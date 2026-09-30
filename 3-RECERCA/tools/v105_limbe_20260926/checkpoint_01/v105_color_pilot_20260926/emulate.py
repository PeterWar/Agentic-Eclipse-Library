"""Comparison-only composition, using existing read-only Estat arrays.
No adjustment-layer emulation and no PSB output. All writes stay in this folder.
"""
import sys,json
from pathlib import Path
import numpy as np
ROOT=Path('/Users/USUARI/Desktop/Eclipse 2026')
OUT=Path('/private/tmp/v105_color_pilot_20260926')
sys.path.insert(0,str(ROOT/'3-RECERCA/tools/v97_refundacio_20260924'))
from jutge_comu import Estat,comp
sys.path.insert(0,str(OUT))
from color_pilot import make_panel

def smoothstep(x,lo,hi):
    t=np.clip((x-lo)/(hi-lo),0,1)
    return t*t*(3-2*t)

S=Estat(ROOT/'4-RESULTATS/v103_banda_20260926/E/estat_v103')
box=(4677,3077,6077,4477)
P=S.pila(box=box)
oldbase=next(f for lid,mode,f,a in P if lid==3)
oldcomp,coverage=comp([(mode,f,a) for lid,mode,f,a in P],1400,1400)
coords={'top':(650,860,210,295),'upper_left':(310,520,275,360),'left':(210,330,600,750)}
report={}
for name in ['572A2969','572A2975']:
    source=np.load('/private/tmp/v105_base_sources_20260926/'+name+'.npz')
    d=source['d_presentation_circle']
    for variant in ['fixed_slope022','free_slope']:
        q=np.load(OUT/f'{name}_{variant}.npz')
        new=np.asarray(q['RGB'],np.float32)
        eligible=np.asarray(q['valid'],bool)&(q['dreal']>=0)&(d>=0)
        weight=eligible.astype(np.float32)*(1-smoothstep(d,50,150))
        safe_new=np.where(eligible[...,None],new,oldbase)
        replacement=(1-weight[...,None])*oldbase+weight[...,None]*safe_new
        mixed,cov=comp([(mode,replacement if lid==3 else f,a) for lid,mode,f,a in P],1400,1400)
        # Ready arrays have no product alpha decision embedded. Root can choose
        # its final blending, but must never read outside maskwhereupdate.
        np.savez_compressed(OUT/f'{name}_{variant}_ready.npz',RGB=np.where(eligible[...,None],new,0),
            maskwhereupdate=eligible,valid_source=np.asarray(q['valid'],bool),
            dreal=q['dreal'],d_presentation_circle=d,box=q['box'],
            params=q['params'],Lref=q['Lref'])
        np.savez_compressed(OUT/f'{name}_{variant}_emulated.npz',RGB=mixed,
            coverage=cov,provisional_weight=weight,box=q['box'])
        r={}
        for region,(x0,x1,y0,y1) in coords.items():
            z=np.s_[y0:y1,x0:x1]
            items=[('Current base L3',oldbase[z],np.ones(d[z].shape,bool)),
                ('Photographic source carrier',replacement[z],np.ones(d[z].shape,bool)),
                ('Current old-filter composite',oldcomp[z],np.ones(d[z].shape,bool)),
                ('Carrier + old-filter composite',mixed[z],np.ones(d[z].shape,bool))]
            make_panel(items,OUT/f'{name}_{variant}_{region}_EMULATED.png',
                'DIAGNOSTIC ONLY: before adjustment layers; temporary 50-150 px blend; no source warp',zoom=True)
            zz=eligible[z]&(d[z]>=0)&(d[z]<15)
            if zz.any():
                r[region]={'n':int(zz.sum()),'comp_R_median_old':float(np.median(oldcomp[z][zz,0])),
                    'comp_R_median_new':float(np.median(mixed[z][zz,0])),
                    'comp_delta_RGB_median':np.median((mixed-oldcomp)[z][zz],axis=0).tolist()}
        report[f'{name}_{variant}']=r
report['limits']='Existing Estat blend modes/masks/opacities only; no Photoshop adjustment layers. Source geometry unchanged; final mask undecided.'
(OUT/'EMULATED.json').write_text(json.dumps(report,indent=2)+'\n')
print('READY',list(report))
