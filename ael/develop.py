"""Linear stack -> filter layers, preview and optional verified 16-bit PSB."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from . import io, photoshop
from .filterbank import DEFAULTS,NAMES,make_filter
from .geometry import EclipseGeometry


def layer_alpha(base_alpha,observed,mode):
    """Multiply must use exactly the base's limb ramp; never an earlier fade."""
    alpha=np.asarray(base_alpha,np.float32)
    if alpha.shape!=observed.shape or not np.isfinite(alpha).all() or (alpha<0).any() or (alpha>1).any():
        raise ValueError('alpha must be finite [0,1] and match the canvas')
    return np.where(observed,alpha,0).astype(np.float32)


def filters_from_config(config_path,out_dir,*,progress=print):
    path=Path(config_path).resolve(); root=path.parent
    cfg=json.loads(path.read_text())
    allowed={'input','geometry','valid','exclude','coverage','min_coverage','alpha','white_balance',
             'camera_to_linear_rgb','moon_margin_px','filters','display','photoshop','opacities','visible','icc','note'}
    if set(cfg)-allowed: raise ValueError(f'unknown recipe keys: {sorted(set(cfg)-allowed)}')
    def resolve(v):
        p=Path(v).expanduser(); return p if p.is_absolute() else root/p
    def load(key): return np.asarray(io.load_array(resolve(cfg[key])))
    a=load('input').astype(np.float32)
    if a.ndim==2: a=np.repeat(a[...,None],3,axis=-1)
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
    if not isinstance(names,list) or not names or len(set(names))!=len(names) or any(n not in NAMES for n in names):
        raise ValueError(f'filters must be a nonempty unique list from {NAMES}, or "all"')
    visible_names=cfg.get('visible',[n for n in DEFAULTS if n in names])
    if not isinstance(visible_names,list) or set(visible_names)-set(names):
        raise ValueError('visible must be a subset of filters')
    if set(cfg.get('opacities',{}))-set(names): raise ValueError('opacities must name selected filters')
    if any(not np.isfinite(v) or not 0<=v<=1 for v in cfg.get('opacities',{}).values()):
        raise ValueError('opacities must be finite in [0,1]')
    stretch=cfg['display']
    if set(stretch)-{'scale','asinh'}: raise ValueError('unknown display parameter')
    scale=float(stretch['scale']); strength=float(stretch.get('asinh',10))
    if not np.isfinite(scale*strength) or scale<=0 or strength<=0: raise ValueError('display scale and asinh must be positive')
    base=np.clip(np.arcsinh(np.maximum(rgb,0)/scale*strength)/np.arcsinh(strength),0,1)
    base=np.where(valid[...,None],base,0).astype(np.float32)
    out=Path(out_dir).resolve(); out.mkdir(parents=True,exist_ok=False)
    outputs={}; params=[]; expected=[]
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
    # The actual HDR values remain in the float TIFF/NPY, not a clipped 16-bit layer.
    add('Linear reference / declared scale',np.nan_to_num(rgb)/scale,alpha,visible=False)
    add('Display base',base,alpha)
    domain_checks=[]
    for i,name in enumerate(names):
        progress(f'filter {i+1}/{len(names)}: {name}')
        image,mode,info=make_filter(name,lum,valid,geo)
        observed=valid & np.isfinite(image)
        al=layer_alpha(alpha,observed,mode)
        opacity=float(cfg.get('opacities',{}).get(name,{'nrgf':.39,'wow_bilateral':.37,'achf_iso_04':.08}.get(name,1)))
        if not np.isfinite(opacity) or not 0<=opacity<=1: raise ValueError('opacity must be in [0,1]')
        visible=name in visible_names
        image=np.where(observed,image,np.nan)
        domain_checks.append(bool(np.isnan(image[~valid]).all() and (al[~valid]==0).all()))
        for suffix,arr in (('layer',image),('alpha',al)):
            p=out/f'{name}_{suffix}.npy'; np.save(p,arr); outputs[f'{name}_{suffix}']=p
        add(name,image,al,mode,opacity,visible)
        params.append(dict(name=name,mode=mode,opacity=opacity,visible=visible,parameters=info,
                           observed_pixels=int(observed.sum()),alpha='same as display base on observed domain'))
    outputs['preview']=io.save_png(out/'preview.png',np.round(np.clip(comp,0,1)*255).astype(np.uint8))
    outputs['display']=io.save_tiff(out/'display.tif',photoshop.to_u16(comp),description='Display only; not linear photometry')
    gates={'nothing_outside_data':all(domain_checks),'photoshop_native':'not checked (no application is opened)'}
    if doc is not None:
        icc=resolve(cfg['icc']).read_bytes() if 'icc' in cfg else None
        outputs['psb']=photoshop.save(doc,out/'corona.psb',photoshop.to_u16(comp),icc=icc)
        gates['photoshop_roundtrip']=photoshop.verify(outputs['psb'],expected)
        if not gates['photoshop_roundtrip']['ok']: raise RuntimeError('Photoshop roundtrip failed')
    inputs={key:resolve(cfg[key]) for key in ('input','geometry','valid','exclude','coverage','alpha','icc') if key in cfg}
    inputs['config']=path
    receipt=io.write_receipt(out/'receipt.json',product='corona filter layers',inputs=inputs,outputs=outputs,
        parameters=dict(recipe=cfg,layers=params),gates=gates,
        notes='Generalised operators, not an exact replay of historical project recipes. No reconstructed saturation, '
        'stars or lunar texture. NRGF-log is a measured-data variant, not historical inward extrapolation. '
        'Linear reference layer is scaled/clipped; original HDR input is authoritative. '
        'No scientific or native Photoshop validation implied by file roundtrip.')
    return dict(files={k:str(v) for k,v in outputs.items()},receipt=str(receipt))
