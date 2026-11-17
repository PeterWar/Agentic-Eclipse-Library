"""Linear stack -> filter layers, preview and optional verified 16-bit PSB."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from . import io, photoshop
from . import gates as G
from .filterbank import ALIASES,DEFAULTS,EDGES,EXTRA,LARSON_SEKANINA,NAMES,level_through_zones,make_filter,red_excess_mask
from .zones import inner_zones,zones_preview
from .geometry import EclipseGeometry

# Starting opacities of the default layers, from the author's 2026 image, where the Overlay layer was the edge-aware WOW
# at 0.37. The plain WOW (`wow`, the default in 1.3.4) keeps 0.37 for recipes that list it (docs/VALIDATION_1.3.4.md).
# Since 1.4.2 the author's 2026 test layers give three more: NAFE at 0.79 (where it adds, at 1.3–3 R☉, the contrast of
# his edge-aware WOW at 0.37) and both Larson–Sekanina layers at 0.20. SWAP is a whole view in Normal: 1.
DEFAULT_OPACITY={'nrgf':.39,'wow_edge_aware':.37,'achf_iso_04':.08,'wow':.37,'nafe':.79,'larson_sekanina_1':.2,
                 'larson_sekanina_0.4':.2,'swap':1.}

# Photoshop layer names (since 1.3.5), the scheme of the author's own files: the number is the family, in the order
# of his stack (00 display base, 01 NRGF, 02 RHEF, 03 MGN, 04 ACHF, 05 WOW, 09 NAFE); a letter tells the variants of
# one family apart from the bottom up; then the filter and the parameter that distinguishes it. The receipt keeps the
# code names.
LAYER_LABELS={'nrgf':('01','NRGF'),'nrgf_log':('01','NRGF log'),'rhef':('02','RHEF'),
              'rhef_upsilon':('02','RHEF Upsilon'),'rhef_local60':('02','RHEF local 60°'),
              'rhef_local30':('02','RHEF local 30°'),'mgn':('03','MGN'),'achf_angular':('04','ACHF angular'),
              'achf_angular4':('04','ACHF angular smoothed 4 px'),'achf_angular8':('04','ACHF angular smoothed 8 px'),
              'achf_iso_01':('04','ACHF iso 2–32 px'),'achf_iso_04':('04','ACHF iso 1–16 px'),
              'achf_iso_05':('04','ACHF iso 2–48 px'),'achf_iso_06':('04','ACHF iso 4–64 px'),
              'wow':('05','WOW'),'wow_edge_aware':('05','WOW edge-aware'),
              # structure-aware detail (after 1.4.0): one family each, after the agentic layers 06–07 of the author's files
              'hessian_ridge':('10','Hessian ridge'),'steerable_g2':('11','Steerable G2'),'mmt':('12','Median transform'),
              'noise_gate':('13','Noise gating'),'coherence_diffusion':('14','Coherence diffusion'),
              # since 1.4.2: NAFE keeps the number of the author's 2026 test layer; then one family each
              'fnrgf':('01','FNRGF'),          # since 1.5.0: next to the NRGF, as in the author's files
              'nafe':('09','NAFE'),'larson_sekanina_1':('15','Larson-Sekanina 1°'),
              'larson_sekanina_0.4':('15','Larson-Sekanina 0.4°'),'swap':('16','SWAP filter')}


def layer_names(names):
    """Photoshop layer names of the filters ``names``, listed from the bottom up: ``['01 NRGF', '05 WOW edge-aware',
    '04 ACHF iso 1–16 px']`` for the defaults, ``'05a WOW'`` and ``'05b WOW edge-aware'`` when both WOW layers are listed."""
    names=[ALIASES.get(n,n) for n in names]
    families=[LAYER_LABELS[n][0] for n in names]
    out=[]
    for i,(n,family) in enumerate(zip(names,families)):
        letter='abcdefghijklmnop'[families[:i].count(family)] if families.count(family)>1 else ''
        out.append(f'{family}{letter} {LAYER_LABELS[n][1]}')
    return out


def layer_alpha(base_alpha,observed,mode):
    """Multiply must use exactly the base's limb ramp; never an earlier fade."""
    alpha=np.asarray(base_alpha,np.float32)
    if alpha.shape!=observed.shape or not np.isfinite(alpha).all() or (alpha<0).any() or (alpha>1).any():
        raise ValueError('alpha must be finite [0,1] and match the canvas')
    return np.where(observed,alpha,0).astype(np.float32)


def tone_map(rgb, valid, *, scale, strength=10., highlight_ceiling=.9):
    """Per-channel asinh followed by one shared, continuous highlight shoulder.

    No positive hard clipping. The shared factor preserves asinh RGB ratios;
    the original linear data and its physical support are unchanged.
    """
    if not np.isfinite([scale, strength, highlight_ceiling]).all():
        raise ValueError('display parameters must be finite')
    if scale <= 0 or strength <= 0 or not 0 < highlight_ceiling <= 1-1/65535:
        raise ValueError('scale/asinh must be positive; highlight_ceiling must leave one 16-bit DN below 1')
    a = np.asarray(rgb, np.float64)
    m = np.asarray(valid, bool)
    if a.shape != (*m.shape, 3) or not np.isfinite(a[m]).all():
        raise ValueError('RGB must be finite on a matching valid domain')
    a = np.where(m[...,None], a, 0)
    with np.errstate(over='ignore', invalid='ignore'):
        u = np.arcsinh(np.maximum(a, 0)/scale*strength)/np.arcsinh(strength)
    if not np.isfinite(u).all():
        raise ValueError('display scale/asinh overflow; choose a usable scale')
    peak = np.max(u, axis=-1)
    shoulder = highlight_ceiling*(-np.expm1(-peak/highlight_ceiling))
    factor = np.divide(shoulder, peak, out=np.zeros_like(peak), where=peak>0)
    return (u*factor[...,None]).astype(np.float32)


def filters_from_config(config_path,out_dir,*,progress=print):
    """Linear stack → filter layers over a display base, a preview and (``"photoshop": true``) a verified 16-bit PSB.

    Since 1.5.0 two recipe keys decide how the layers treat what is not corona and the edges of the data:

    - ``"inner_limit"``: ``"auto"`` (default), ``true`` or ``false``. With the Moon in the geometry, the single map of
      the inner limit (:func:`ael.zones.inner_zones`) is measured on the image; no filter sees the core (limb,
      chromosphere, prominences, beads), the hydrogen light is taken out of the filters' input, an Overlay layer is
      transparent in the core and a Multiply layer carries only its level through it. The map is written next to the
      layers (``inner_limit_map.png``: look at it) and the receipt says what each criterion found. ``"auto"`` goes on
      without the map, and says so, when the geometry has no Moon or the map cannot be measured; ``true`` stops.
    - ``"edges"``: ``"unbiased"`` (default) or ``"classic"`` (:data:`ael.filterbank.EDGES`).

    With the map, every Overlay and Multiply layer goes through gate L (:func:`ael.gates.inner_limit`): it starts
    where the map says, like the others, and carries no detail inside the core. **A layer that fails is written
    switched off** and stays out of the preview (``"gates": "report"`` in the recipe only reports, and the receipt says
    the gate was not enforced). The returned dictionary and the receipt carry ``gates["verdict"]``: ``PASS``, ``WARN``
    (look where it says), ``FAIL`` (``gates["failed"]`` names the layers; those that were visible are switched off
    and listed in ``switched_off_by_a_gate``; with no layer named, the layers do not start at the same place) or
    ``NOT JUDGED`` (no map).

    Gate D (:func:`ael.gates.gramophone`, fine concentric rings) is not run here: without a control it cannot tell the
    rings a step adds from those the data carry (the exposure transitions of an HDR stack are concentric). Run it
    yourself, with the plain layer as ``control``, whenever a layer is shown with a yardstick measured on another
    layer, or made from a base that went through a new step."""
    path=Path(config_path).resolve(); root=path.parent
    cfg=json.loads(path.read_text())
    allowed={'input','geometry','valid','exclude','coverage','min_coverage','alpha','white_balance',
             'camera_to_linear_rgb','moon_margin_px','filters','display','photoshop','opacities','visible','icc','note',
             'achf_display','inner_limit','edges','gates'}
    if set(cfg)-allowed: raise ValueError(f'unknown recipe keys: {sorted(set(cfg)-allowed)}')
    def resolve(v):
        p=Path(v).expanduser(); return p if p.is_absolute() else root/p
    def load(key): return np.asarray(io.load_array(resolve(cfg[key])))
    a=load('input').astype(np.float32)
    mono_input=a.ndim==2
    if mono_input: a=np.repeat(a[...,None],3,axis=-1)
    if a.ndim!=3 or a.shape[-1]!=3: raise ValueError('input must be a linear HxW or HxWx3 array')
    geo=EclipseGeometry.from_json(resolve(cfg['geometry']))
    if tuple(a.shape[:2])!=tuple(geo.shape): raise ValueError('geometry does not match input canvas')
    if not np.isfinite(geo.sun_radius_px) or geo.sun_radius_px<=0 or not np.isfinite(geo.sun_xy).all():
        raise ValueError('solar geometry must be finite with a positive radius')
    valid=np.isfinite(a).all(axis=-1)
    for key in ('valid','exclude'):
        if key in cfg:
            mask=load(key)
            if mask.shape!=valid.shape: raise ValueError(f'{key} does not match input canvas')
            if not np.isfinite(mask).all(): raise ValueError(f'{key} must be finite')
            valid &= mask.astype(bool) if key=='valid' else ~mask.astype(bool)
    # Coverage is explicitly geometric, never a count of unsaturated full-weight frames.
    if 'coverage' in cfg:
        cov=load('coverage')
        if cov.shape!=valid.shape or not np.isfinite(cov).all(): raise ValueError('invalid geometric coverage')
        minimum=float(cfg.get('min_coverage',.5))
        if not np.isfinite(minimum) or minimum<0: raise ValueError('min_coverage must be finite and nonnegative')
        valid &= cov>=minimum
    balance=np.asarray(cfg.get('white_balance',[1,1,1]),np.float32)
    if balance.shape!=(3,) or not np.isfinite(balance).all() or (balance<=0).any():
        raise ValueError('white_balance must contain three positive linear ratios')
    rgb=a*balance
    colour_matrix=np.asarray(cfg.get('camera_to_linear_rgb',np.eye(3)),np.float32)
    if colour_matrix.shape!=(3,3) or not np.isfinite(colour_matrix).all():
        raise ValueError('camera_to_linear_rgb must be finite 3x3')
    rgb=rgb@colour_matrix.T
    lum=(rgb[...,0]+2*rgb[...,1]+rgb[...,2])/4
    valid &= lum>0
    if geo.moon_xy is not None and geo.moon_radius_px is not None:
        valid &= ~geo.moon_mask(float(cfg.get('moon_margin_px',2)))
    if not valid.any(): raise ValueError('no positive observed corona pixels')
    alpha=layer_alpha(load('alpha') if 'alpha' in cfg else valid.astype(np.float32),valid,'normal')
    names=cfg.get('filters',list(DEFAULTS))
    if names=='all': names=list(NAMES)
    if isinstance(names,list): names=[ALIASES.get(n,n) for n in names]          # 'wow_bilateral' up to 1.3.4
    if not isinstance(names,list) or not names or len(set(names))!=len(names) or any(n not in NAMES+EXTRA for n in names):
        raise ValueError(f'filters must be a nonempty unique list from {NAMES + EXTRA}, or "all"')
    # The plain WOW was the default in 1.3.4: a recipe that lists it without the edge-aware WOW keeps it visible
    visible_names=cfg.get('visible',[n for n in names if n in DEFAULTS or (n=='wow' and 'wow_edge_aware' not in names)])
    if isinstance(visible_names,list): visible_names=[ALIASES.get(n,n) for n in visible_names]
    if not isinstance(visible_names,list) or set(visible_names)-set(names):
        raise ValueError('visible must be a subset of filters')
    opacities={ALIASES.get(k,k):v for k,v in cfg.get('opacities',{}).items()}
    if set(opacities)-set(names): raise ValueError('opacities must name selected filters')
    if any(not np.isfinite(v) or not 0<=v<=1 for v in opacities.values()):
        raise ValueError('opacities must be finite in [0,1]')
    achf_display=cfg.get('achf_display','rings')
    if achf_display not in ('rings','global'): raise ValueError("achf_display is 'rings' or 'global'")
    edges=cfg.get('edges','unbiased')
    if edges not in EDGES: raise ValueError(f'edges is one of {EDGES}')
    inner=cfg.get('inner_limit','auto')
    if not (isinstance(inner,bool) or inner=='auto'): raise ValueError('inner_limit is "auto", true or false')
    enforce=cfg.get('gates','enforce')
    if enforce not in ('enforce','report'): raise ValueError('gates is "enforce" or "report"')
    has_moon=geo.moon_xy is not None and geo.moon_radius_px is not None
    if inner is True and not has_moon: raise ValueError('inner_limit needs the Moon in the geometry (run `ael geometry`)')
    stretch=cfg['display']
    if set(stretch)-{'scale','asinh','highlight_ceiling'}: raise ValueError('unknown display parameter')
    scale=float(stretch['scale']); strength=float(stretch.get('asinh',10))
    ceiling=float(stretch.get('highlight_ceiling',.9))
    base=tone_map(rgb,valid,scale=scale,strength=strength,highlight_ceiling=ceiling)
    # A reference is independently scaled, so positive observed HDR is not clipped
    # merely because the display stretch uses a lower scale.
    reference_scale=float(np.max(rgb[valid]))/.98
    reference=np.where(valid[...,None],rgb.astype(np.float64)/reference_scale,0)
    display_info=dict(scale=scale,asinh=strength,highlight_ceiling=ceiling,
                      method='asinh RGB with shared exponential highlight shoulder',
                      positive_base_clip_pixels=int(np.count_nonzero((photoshop.to_u16(base[valid])==65535).any(axis=-1))),
                      negative_rgb_samples=int(np.count_nonzero(rgb[valid]<0)),
                      linear_reference_scale=reference_scale,
                      linear_reference_peak=.98)
    out=Path(out_dir).resolve(); out.mkdir(parents=True,exist_ok=False)
    outputs={}; params=[]; expected=[]
    # The inner limit (since 1.5.0): one map for every layer, measured on the image
    zones=None; lum_f,valid_f=lum,valid; inner_info=dict(used=False)
    if inner is False: inner_info['why_not']='switched off in the recipe ("inner_limit": false)'
    elif not has_moon: inner_info['why_not']='the geometry has no Moon: no map could be made; filters act on every observed pixel'
    else:
        progress('inner limit: measuring the map (limb, chromosphere, prominences, beads)')
        try:
            zones=inner_zones(lum if mono_input else rgb,valid,geo)
        except ValueError as exc:
            if inner is True: raise
            inner_info['why_not']=f'the map could not be measured ({exc}); filters act on every observed pixel'
        if zones is not None:
            lum_f=(zones.clean[...,0]+2*zones.clean[...,1]+zones.clean[...,2])/4
            valid_f=valid & ~zones.core & np.isfinite(lum_f) & (lum_f>0)
            np.save(out/'inner_limit_core.npy',zones.core); outputs['inner_limit_core']=out/'inner_limit_core.npy'
            np.save(out/'inner_limit_classes.npy',zones.classes); outputs['inner_limit_classes']=out/'inner_limit_classes.npy'
            outputs['inner_limit_map']=io.save_png(out/'inner_limit_map.png',zones_preview(zones,lum))
            inner_info=dict(used=True,**zones.info,
                            read_me='inner_limit_map.png: corona grey, limb white, chromosphere pink, prominences red, beads '
                                    'cyan, corona whose input was cleaned brown. Check it by eye, enlarged: every red or '
                                    'pink pixel must be emission and no corona must be coloured.')
            for w in zones.info['warnings']: progress(f'inner limit: warning: {w}')
    core_weight=None if zones is None else zones.core.astype(np.float32)
    layer_gates={}; starts=[]; hidden=[]
    export=bool(cfg.get('photoshop',False))
    doc=photoshop.new_document(geo.shape[1],geo.shape[0]) if export else None
    comp=np.zeros_like(base)
    def add(name,image,al,mode='normal',opacity=1,visible=True):
        nonlocal comp
        u=photoshop.to_u16(image); aa=photoshop.to_u16(al)
        if doc is not None:
            photoshop.add_layer(doc,name,u,aa,mode=mode,opacity=opacity,visible=visible)
            expected.append(dict(name=name,rgb16=u,alpha16=aa,mode=mode,opacity=opacity,visible=visible))
        if visible:
            x=u.astype(np.float32)/65535
            if x.ndim==2: x=np.repeat(x[...,None],3,axis=-1)
            blend=x if mode=='normal' else comp*x if mode=='multiply' else np.where(comp<=.5,2*comp*x,1-2*(1-comp)*(1-x))
            weight=aa.astype(np.float32)[...,None]/65535*(round(opacity*255)/255)
            comp=comp*(1-weight)+blend*weight
    add('Background',np.zeros_like(base),np.ones(valid.shape))
    # Signed floating input remains authoritative; 16-bit reference retains positive range.
    add('Linear reference / receipt scale',reference,alpha,visible=False)
    add('00 Display base',base,alpha)
    domain_checks=[]
    # The Larson–Sekanina layers copy a prominence at ±Δθ: it leaves their input, found by its red (since 1.4.2)
    prominences=red_excess_mask(rgb,valid,geo) if set(names)&set(LARSON_SEKANINA) else None
    for i,(name,label) in enumerate(zip(names,layer_names(names))):
        progress(f'filter {i+1}/{len(names)}: {name}')
        kw=dict(exclude=prominences) if name in LARSON_SEKANINA else {}
        image,mode,info=make_filter(name,lum_f,valid_f,geo,achf_display=achf_display,edges=edges,**kw)
        if name in LARSON_SEKANINA: info=dict(info,excluded='prominences: red_excess_mask (R/G above 1.12 times its annulus)')
        observed=valid_f & np.isfinite(image)
        image=np.where(observed,image,np.nan)
        if zones is not None and mode=='multiply':
            # a Multiply layer carries its level, and nothing else, through the core (an Overlay layer is transparent there)
            image,_=level_through_zones(image,observed,core_weight)
            observed=valid & np.isfinite(image)
        al=layer_alpha(alpha,observed,mode)
        opacity=float(opacities.get(name,DEFAULT_OPACITY.get(name,1)))
        if not np.isfinite(opacity) or not 0<=opacity<=1: raise ValueError('opacity must be in [0,1]')
        visible=name in visible_names
        image=np.where(observed,image,np.nan)
        domain_checks.append(bool(np.isnan(image[~valid]).all() and (al[~valid]==0).all()))
        verdicts={}
        if mode not in ('overlay','multiply'):
            verdicts['note']='a whole view in Normal mode, not a detail layer: gate L does not apply'
        elif zones is not None:
            li=G.inner_limit({name:(image,al)},zones.core,geo,valid=valid)['layers'][name]
            fails=list(li['failures']); notes=[w for w in li['warnings'] if w.startswith('a streak')]
            warns=[w for w in li['warnings'] if not w.startswith('a streak')]
            if mode=='multiply':
                # In the core this layer IS its level (level_through_zones): L1 reads the slope of that level across a
                # core a few pixels wide as fine detail. Reported, not enforced (the author accepted by eye, on his 2026
                # image, a layer that failed L1 this way).
                warns+=[f+' — the level this Multiply layer carries through the core, not filter detail: look at it; '
                        'not enforced' for f in fails if f.startswith('L1')]
                fails=[f for f in fails if not f.startswith('L1')]
            verdicts['inner_limit']=dict(verdict='FAIL' if fails else 'WARN' if warns else 'PASS',failures=fails,
                                         warnings=warns,notes=notes,
                                         start_error_median_px=li['measure']['d50_error_median_px'],
                                         detail_inside_core_levels_8bit=li['measure']['detail_inside_core_levels_8bit'])
            starts.append((name,li['measure']['d50_per_sector']))
        failed=[g for g,v in verdicts.items() if isinstance(v,dict) and v['verdict']=='FAIL']
        if failed and enforce=='enforce':
            if visible: hidden.append(name)
            visible=False
        layer_gates[name]=verdicts
        said=', '.join(f"{g} {v['verdict']}" for g,v in verdicts.items() if isinstance(v,dict))
        if said: progress(f'  gates: {name}: {said}'+(' → written switched off' if failed and enforce=='enforce' else ''))
        for suffix,arr in (('layer',image),('alpha',al)):
            p=out/f'{name}_{suffix}.npy'; np.save(p,arr); outputs[f'{name}_{suffix}']=p
        add(label,image,al,mode,opacity,visible)
        params.append(dict(name=name,layer=label,mode=mode,opacity=opacity,visible=visible,parameters=info,
                           observed_pixels=int(observed.sum()),alpha='same as display base on observed domain',
                           gates=verdicts,switched_off_by_a_gate=bool(failed and enforce=='enforce')))
    outputs['preview']=io.save_png(out/'preview.png',np.round(np.clip(comp,0,1)*255).astype(np.uint8))
    outputs['display']=io.save_tiff(out/'display.tif',photoshop.to_u16(comp),description='Display only; not linear photometry')
    gates={'nothing_outside_data':all(domain_checks),
           'positive_display_base_not_clipped':display_info['positive_base_clip_pixels']==0,
           'photoshop_native':'not checked (no application is opened)'}
    between=G.inner_limit_between(starts) if len(starts)>1 else None
    worst=[v['verdict'] for lg in layer_gates.values() for v in lg.values() if isinstance(v,dict)]
    if between is not None: worst.append(between['verdict'])
    verdict='FAIL' if 'FAIL' in worst else 'WARN' if 'WARN' in worst else 'PASS' if 'PASS' in worst else 'NOT JUDGED'
    failed_layers=[n for n,lg in layer_gates.items() if any(isinstance(v,dict) and v['verdict']=='FAIL' for v in lg.values())]
    if verdict=='NOT JUDGED':
        gates['why_not_judged']=inner_info.get('why_not','the recipe has no Overlay or Multiply layer to check against the map')
    gates.update(layers=layer_gates,inner_limit_between_layers=between,failed=failed_layers,
                 switched_off_by_a_gate=hidden,verdict=verdict,
                 enforced=enforce=='enforce',
                 how_to_read='PASS: use the layers. WARN: look at the layer where the warning says before using it. '
                             'FAIL: a layer failed (gates.failed names it); if it was visible it is in the file '
                             'switched off and out of the preview (switched_off_by_a_gate); do not switch it on without '
                             'finding the cause where it is born (docs/INNER_LIMIT.md). FAIL with no layer named: the '
                             'layers do not start at the same place (inner_limit_between_layers). NOT JUDGED: no map of '
                             'the inner limit was made (the reason is in parameters.inner_limit.why_not), so no layer '
                             'was checked against one. Never change a threshold to pass a layer. "notes" are '
                             'uncalibrated measurements (a streak that follows the limb: the first pixels of every '
                             'operator next to a hole see one side only); they do not change the verdict.')
    if doc is not None:
        icc=resolve(cfg['icc']).read_bytes() if 'icc' in cfg else None
        outputs['psb']=photoshop.save(doc,out/'corona.psb',photoshop.to_u16(comp),icc=icc)
        gates['photoshop_roundtrip']=photoshop.verify(outputs['psb'],expected)
        if not gates['photoshop_roundtrip']['ok']: raise RuntimeError('Photoshop roundtrip failed')
    inputs={key:resolve(cfg[key]) for key in ('input','geometry','valid','exclude','coverage','alpha','icc') if key in cfg}
    inputs['config']=path
    receipt=io.write_receipt(out/'receipt.json',product='corona filter layers',inputs=inputs,outputs=outputs,
        parameters=dict(recipe=cfg,layers=params,display=display_info,edges=edges,inner_limit=inner_info),gates=gates,
        notes='Generalised operators, not an exact replay of historical project recipes. No reconstructed saturation, '
        'stars or lunar texture. NRGF-log is a measured-data variant, not historical inward extrapolation. '
        'Linear reference is scaled to retain positive range; negative RGB is clipped in 16-bit display only. '
        'Original signed floating HDR input is authoritative. '
        'No scientific or native Photoshop validation implied by file roundtrip.')
    summary={n:{g:v['verdict'] for g,v in lg.items() if isinstance(v,dict)} for n,lg in layer_gates.items()}
    return dict(files={k:str(v) for k,v in outputs.items()},receipt=str(receipt),
                gates=dict(verdict=verdict,layers=summary,failed=failed_layers,switched_off_by_a_gate=hidden,
                           between_layers=None if between is None else between['verdict']),
                inner_limit=dict(used=inner_info['used'],**({'why_not':inner_info['why_not']} if not inner_info['used'] else
                                 dict(map=str(outputs['inner_limit_map']),pixels=inner_info['pixels'],
                                      warnings=inner_info['warnings']))))
