"""Independent linear-input layers and Photoshop-style display composition.

Sources are immutable arrays owned by a job. Two source identities (fast/native)
are retained, with one cached result per filter/ACHF variant. Pixel/geometry edits
invalidate the affected signatures; visibility, opacity and display never do.
"""
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextvars import copy_context
from threading import Event, RLock
import time
import numpy as np

from .cancellation import check_cancelled, cancellation_check, cancellation_scope
from .parallelism import CPU_CORES, filter_budget, layer_workers
from .image_data import observed_image
from .result_cache import parameter_signature
from .presentation import normalized_base

ORDER = ('nrgf', 'fnrgf', 'rhef', 'mgn', 'wow', 'tangential', 'larson_sekanina')
VARIANTS = ('adaptive', 'ael_iso_01', 'ael_iso_04', 'ael_angular_4')
LABELS = dict(adaptive='ACHF_ADAPTIVE', ael_iso_01='ACHF_AEL_ISO_01',
              ael_iso_04='ACHF_AEL_ISO_04', ael_angular_4='ACHF_AEL_ANGULAR')


def requests(params):
    """Ordered active layers; the family checkbox gates ACHF inclusion flags."""
    result=[]
    for name in ORDER:
        if params.get(name+'_enabled', False):
            result.append((name, None, params, True))
    for variant in VARIANTS:
        settings = dict(params.get('achf_variants', {}).get(variant, {}))
        enabled = params.get('achf_enabled', False) and settings.get('enabled', variant == 'adaptive')
        if not enabled:
            continue
        p=dict(params,achf_variant=variant,achf_enabled=True)
        if variant == 'adaptive':
            p['achf_str']=params.get('achf_adaptive_strength',params.get('achf_str',10))
        else:
            from .ael_achf import AEL_PRESETS
            preset=dict(AEL_PRESETS[variant]); preset.update(settings)
            p.update(achf_str=preset['strength'],achf_ael_parameters=preset)
        p['achf_opacity']=settings.get('opacity',params.get('achf_opacity',50))
        result.append(('achf',variant,p,enabled))
    return result


def opacity(name, params, enabled=True):
    value=float(params.get(name+'_opacity',40 if name == 'nrgf' else 50)) / 100
    if not np.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('Layer opacity must be between 0 and 100 percent')
    return round(value*255)/255 if enabled and params.get(name+'_str',100) != 0 else 0.


def blend(base, image, alpha, mode, amount):
    from .layer_export import overlay, linear_light
    if mode == 'Multiply':
        weight=alpha*amount
        return base*(1-weight)+(base*image)*weight
    return (linear_light if mode == 'Linear Light' else overlay)(base,image,alpha,amount)


def display_base(source, params, display):
    from .layer_export import to_u16
    valid=params.get('valid_mask')
    observed=source if valid is None else np.where(valid,source,np.nan)
    if display.get('mode') == 'ael_presentation':
        from .presentation import ael_tone_map
        return to_u16(ael_tone_map(observed,np.isfinite(observed),display))
    return to_u16(normalized_base(observed,display))


def colour_display(rgb, source, display):
    """Quantized RGB Color samples for the explicitly supplied base recipe."""
    from .colour import colour_layer
    from .layer_export import to_u16
    if display.get('mode') == 'ael_presentation':
        from .presentation import ael_tone_map
        return to_u16(ael_tone_map(rgb,np.isfinite(source) & np.isfinite(rgb).all(axis=-1),display)).astype(float)/65535.
    return to_u16(colour_layer(rgb,source,display)).astype(float)/65535.


class LayerEngine:
    def __init__(self):
        self.sources=OrderedDict()
        self._lock=RLock()

    def clear(self):
        with self._lock:
            self.sources.clear()

    def snapshot(self, source, copied_source):
        """Share immutable layer arrays with an isolated export-worker cache."""
        result=LayerEngine()
        with self._lock:
            cached=self.sources.get(id(source))
            if cached is not None:
                result.sources[id(copied_source)]=(copied_source,dict(cached[1]))
        return result

    def absorb(self, snapshot, copied_source, original_source):
        """Retain completed export layers for the unchanged source on the GUI thread."""
        with snapshot._lock:
            cached=snapshot.sources.get(id(copied_source))
            additions=dict(cached[1]) if cached is not None else {}
        if additions:
            with self._lock:
                self._entries(original_source).update(additions)

    def _entries(self, source):
        with self._lock:
            identity=id(source)
            if identity not in self.sources:
                self.sources[identity]=(source,{})
                while len(self.sources)>2:
                    self.sources.popitem(last=False)
            self.sources.move_to_end(identity)
            return self.sources[identity][1]

    def edge_alpha(self, source, params):
        """Cache display-only edge coverage independently of filter and colour edits."""
        from .presentation_edges import black_edge_alpha
        scale=params.get('nrgf_scale',1.)
        signature=parameter_signature(dict(valid=params.get('valid_mask'),scale=scale,
                                            geometry={k:params.get(k) for k in ('sx','sy','sr')}))
        entries=self._entries(source)
        slot=('display_edge',None)
        with self._lock:
            cached=entries.get(slot)
        if cached is not None and cached[0]==signature:
            return cached[1]
        alpha=black_edge_alpha(source,params.get('valid_mask'),scale,params)
        check_cancelled()
        with self._lock:
            entries[slot]=(signature,alpha)
        return alpha

    def layer(self, worker, source, params, name, variant=None, calculate=True):
        # A key contains only this filter's controls and shared spatial/support data.
        shared=('sx','sy','sr','spatial_scale','valid_mask','statistics_mask')
        controls={k:v for k,v in params.items() if
                  k in shared or k.startswith('statistics_') or
                  (k.startswith(name+'_') and not k.endswith(('_enabled','_opacity')))}
        for key in ('achf_variants','achf_adaptive_strength','achf_variant'):
            controls.pop(key,None)
        if name == 'achf':
            if variant == 'adaptive':
                controls.pop('achf_ael_parameters',None)
            controls['variant']=variant
            if variant != 'adaptive':
                settings=dict(params.get('achf_ael_parameters',{}))
                settings.pop('opacity',None); settings.pop('enabled',None)
                controls={'settings':settings, 'strength':params['achf_str'],
                          **{k:v for k,v in controls.items() if not k.startswith('achf_')}}
                controls['achf_ael_scale']=params.get('achf_ael_scale',1.)
        signature=parameter_signature(controls)
        entries=self._entries(source)
        slot=(name,variant)
        with self._lock:
            cached=entries.get(slot)
        if cached is not None and cached[0] == signature:
            return cached[1]
        if not calculate:
            return None
        started=time.perf_counter()
        value=self._calculate(worker,source,params,name,variant)
        check_cancelled()
        with self._lock:
            entries[slot]=(signature,value)
        timing=value.get('timings',{})
        detail=(f" (filter {timing['filter']:.3f}s, encoding {timing['encoding']:.3f}s)" if timing else '')
        print(f'[FILTER: {LABELS.get(variant,name.upper())}] Calculated in {time.perf_counter()-started:.3f}s{detail}')
        return value

    def _calculate(self, worker, source, params, name, variant):
        from .pipeline import apply_filter
        from .statistics_support import statistics_support
        from .layer_export import branch_domain, neutral_layer, linear_detail_layer, to_u16
        prepared,valid=observed_image(source,params.get('valid_mask'))
        prepared=prepared.astype(np.float32)
        statistics=statistics_support(prepared,params,valid)
        p=dict(params,valid_mask=valid)
        if not statistics.all():
            p["statistics_mask"]=statistics
        else:
            p.pop("statistics_mask",None)
        for family in (*ORDER,'achf'):
            p[family+'_enabled']=family == name
        p[name+'_str']=100
        p['fnrgf_apply_mask']=0
        filter_start=time.perf_counter()
        ael=name == 'achf' and variant != 'adaptive'
        ael_wow=name == 'wow' and p.get('wow_mode') == 'ael_bilateral'
        if name == 'nrgf':
            from .nrgf import nrgf_layer
            values, mapping = nrgf_layer(prepared, p, valid & statistics)
        elif ael_wow:
            from .ael_wow import ael_wow_layer
            values, mapping = ael_wow_layer(prepared, p, valid & statistics)
        elif ael:
            from .ael_achf import ael_achf_layer
            values,mapping=ael_achf_layer(prepared,p['sx'],p['sy'],p['sr'],valid & statistics,
                p.get('achf_ael_scale',1.),variant,p.get('achf_ael_parameters'))
        elif name == 'larson_sekanina':
            from .filters import larson_sekanina_residual
            values=larson_sekanina_residual(prepared,p['sx'],p['sy'],p['sr'],
                p.get('larson_sekanina_radial',0.),p.get('larson_sekanina_angular',3.),valid & statistics)
        else:
            filtered=apply_filter(worker,prepared,p,process_label='INDEPENDENT '+name.upper(),verbose=False)
            values=(filtered-prepared if name == 'tangential' else
                    filtered-float(p.get('achf_background',10))/100*prepared if name == 'achf' else filtered)
        filter_seconds=time.perf_counter()-filter_start
        encoding_start=time.perf_counter()
        domain=branch_domain(source.shape,p,name) & valid & statistics
        if name == 'nrgf':
            domain &= np.isfinite(values)
        if ael or ael_wow or (name == 'rhef' and p.get('rhef_mode') == 'continuous'):
            domain &= (prepared>0) & np.isfinite(values)
        mode='Multiply' if name in ('nrgf', 'fnrgf') else 'Linear Light' if name == 'larson_sekanina' else 'Overlay'
        if name == 'nrgf':
            image=np.where(domain, values, 1.)
        elif ael or ael_wow:
            image=np.where(domain,values,.5)
        elif name == 'larson_sekanina':
            image,mapping=linear_detail_layer(values,domain,np.ptp(prepared[valid]))
        else:
            image,mapping=neutral_layer(values,domain)
        if mode == 'Multiply' and mapping.get('constant',False):
            image=np.ones_like(image)
        strength=float(params.get(name+'_str',100))/100
        maximum=2 if name == 'larson_sekanina' else 1
        if not np.isfinite(strength) or not 0 <= strength <= maximum:
            raise ValueError(f'Filter gain/strength must be between 0 and {100*maximum} percent')
        # Strength changes encoded contrast, opacity independently controls blending.
        image=(1+(image-1)*strength if mode == 'Multiply' else .5+(image-.5)*strength)
        alpha=domain.astype(float)
        if name == 'fnrgf' and params.get('fnrgf_apply_mask',0):
            yy,xx=np.ogrid[:source.shape[0],:source.shape[1]]
            r=np.hypot(xx-params['sx'],yy-params['sy'])/params['sr']
            alpha*=1-float(params['fnrgf_apply_mask'])/100*np.clip(1-np.abs(r-1)/.05,0,1)
        result=dict(image=to_u16(image),alpha=to_u16(alpha),mode=mode,mapping=mapping)
        result['image'].setflags(write=False)
        result['alpha'].setflags(write=False)
        result["timings"]=dict(filter=filter_seconds,encoding=time.perf_counter()-encoding_start)
        return result

    def prepare(self, worker, source, params):
        """Calculate only cache misses concurrently; never blend in finish order."""
        check_cancelled()
        pending=[(name,variant,p) for name,variant,p,_ in requests(params)
                 if self.layer(worker,source,p,name,variant,calculate=False) is None]
        if not pending:
            return 0
        workers=layer_workers(source,len(pending))
        budget=max(1,CPU_CORES//workers)
        started=time.perf_counter()
        print(f'[FILTERS] Calculating {len(pending)} layers at {source.shape[1]}×{source.shape[0]}; up to {workers} in parallel')
        if workers == 1:
            with filter_budget(budget):
                for name,variant,p in pending:
                    check_cancelled()
                    self.layer(worker,source,p,name,variant)
        else:
            stopped=Event()
            parent_check=cancellation_check()
            class BatchToken:
                def is_set(self):
                    parent_check()
                    return stopped.is_set()
            token=BatchToken()
            def run(name,variant,p):
                with cancellation_scope(token), filter_budget(budget):
                    return self.layer(worker,source,p,name,variant)
            executor=ThreadPoolExecutor(max_workers=workers,thread_name_prefix='corona-layer')
            futures=[]
            try:
                for name,variant,p in pending:
                    context=copy_context()
                    futures.append(executor.submit(context.run,run,name,variant,p))
                for future in as_completed(futures):
                    check_cancelled()
                    future.result()
            except BaseException:
                stopped.set()
                raise
            finally:
                executor.shutdown(wait=True,cancel_futures=True)
        check_cancelled()
        print(f'[FILTERS] Calculation finished in {time.perf_counter()-started:.3f}s (wall time)')
        return len(pending)

    def render(self, worker, source, params, display, calculate=True, base=None):
        if calculate:
            computed=self.prepare(worker,source,params)
            if not computed and requests(params):
                print('[FUSION] Reusing calculated layers; no filters recalculated')
        if base is None:
            base=display_base(source,params,display).astype(float)/65535
        result=base.copy()
        reveal=float(display.get('blend',1.))
        if not np.isfinite(reveal) or not 0 <= reveal <= 1:
            raise ValueError('Reveal must be between zero and one')
        for name,variant,p,enabled in requests(params):
            check_cancelled()
            amount=round(opacity(name,p,enabled)*reveal*255)/255
            # Enabled layers are calculated even at zero opacity, so raising it
            # later only blends. Cached-only display need not read an invisible layer.
            if not amount and not calculate:
                continue
            layer=self.layer(worker,source,p,name,variant,calculate)
            if layer is None:
                return None
            if amount:
                result=blend(result,layer['image'].astype(float)/65535,
                             layer['alpha'].astype(float)/65535,layer['mode'],amount)
        return result.astype(np.float32)


def engine_for(worker):
    engine=getattr(worker,'layer_engine',None)
    if not isinstance(engine,LayerEngine):
        engine=LayerEngine()
        worker.layer_engine=engine
    return engine
