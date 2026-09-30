"""Recomposició Photoshop (W3C amb transparència del fons) de la ROI lunar a partir de les capes extretes."""
import json, numpy as np
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
IDX=json.load(open(SP+'/v74pere_index_psb69.json')); LAYERS={l['id']:l for l in IDX['layers']}
ROI=(4377,2777,6377,4777)
def carrega(lid):
    d=np.load(SP+f'/roi74p_L{lid}.npz'); L=LAYERS[lid]
    rgb=np.dstack([d['c0'],d['c1'],d['c2']]).astype(np.float32)/65535
    a=d['c-1'].astype(np.float32)/65535
    if 'c-2' in d and L['mask'] and not L['mask']['disabled']: a=a*(d['c-2'].astype(np.float32)/65535)
    a=a*(L['opacity']/255.0)
    return rgb,a
def B(mode,cb,cs):
    if mode=='NORMAL': return cs
    if mode=='MULTIPLY': return cb*cs
    if mode=='OVERLAY': return np.where(cb<=0.5,2*cb*cs,1-2*(1-cb)*(1-cs))
    if mode=='HARD_LIGHT': return np.where(cs<=0.5,2*cs*cb,1-2*(1-cs)*(1-cb))
    if mode=='LINEAR_DODGE': return np.minimum(1,cb+cs)
    if mode=='DIFFERENCE': return np.abs(cb-cs)
    if mode=='SOFT_LIGHT':
        D=np.where(cb<=0.25,((16*cb-12)*cb+4)*cb,np.sqrt(cb)); return np.where(cs<=0.5,cb-(1-2*cs)*cb*(1-cb),cb+(2*cs-1)*(D-cb))
    if mode=='SUBTRACT': return np.clip(cb-cs,0,1)
    raise ValueError(mode)
def recompon(ids=None,exclou=(218,),ordre=None,retorna_passos=False):
    """Compon de baix a dalt les capes visibles (o `ids`), amb la fórmula Co·ao = (1−as)·ab·Cb + as·(1−ab)·Cs + as·ab·B(Cb,Cs)."""
    seq=[l for l in IDX['layers'] if (l['visible'] if ids is None else l['id'] in ids) and l['id'] not in exclou]
    if ordre: seq=sorted(seq,key=lambda l: ordre.index(l['id']))
    Cb=np.zeros((2000,2000,3),np.float32); ab=np.zeros((2000,2000),np.float32); passos={}
    for l in seq:
        cs,as_=carrega(l['id']); a3=as_[...,None]; ab3=ab[...,None]
        num=(1-a3)*ab3*Cb+a3*(1-ab3)*cs+a3*ab3*B(l['blend'],Cb,cs); ao=as_+ab*(1-as_)
        Cb=np.where(ao[...,None]>0,num/np.maximum(ao[...,None],1e-9),0); ab=ao
        if retorna_passos: passos[l['id']]=(Cb.copy(),ab.copy())
    return (Cb,ab,passos) if retorna_passos else (Cb,ab)

# --- variants corregides (V70): OVERRIDE[lid] = ruta a un npz amb els mateixos canals ---
OVERRIDE={}
_carrega_orig=carrega
def carrega(lid):
    if lid in OVERRIDE:
        d=np.load(OVERRIDE[lid]); L=LAYERS[lid]
        rgb=np.dstack([d['c0'],d['c1'],d['c2']]).astype(np.float32)/65535; a=d['c-1'].astype(np.float32)/65535
        if 'c-2' in d and L['mask'] and not L['mask']['disabled']: a=a*(d['c-2'].astype(np.float32)/65535)
        return rgb,a*(L['opacity']/255.0)
    return _carrega_orig(lid)
