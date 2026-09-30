"""P04: observed linear intensity; preserve V104 spectral/display colour.
L=(R+2G+B)/4 is a defined intensity, not CIE Y. Unit conversions are constants.
F is the old RGB reference; E_observed is untouched physical post-matrix data.
"""
from pathlib import Path
import numpy as np,json
O=Path('/private/tmp/v105_root_pilots_20260926');R=Path('/Users/USUARI/Desktop/Eclipse 2026')
p=O/'P04';assert not p.exists();p.mkdir()
z=np.load(O/'P03/Q_OBSERVED.npz');q={k:z[k]for k in z.files}
old=np.load(R/'4-RESULTATS/v103_banda_20260926/E/lineal_v103_franja/A3C_franja_silueta.npz')
y0,y1,x0,x1=map(int,q['box']);yy,xx=np.mgrid[y0:y1,x0:x1];cx,cy,rad=q['centre'];d=np.hypot(xx-cx,yy-cy)-rad
E=q['E_observed'];L=(E[...,0]+2*E[...,1]+E[...,2])/4
good=q['observed']&np.isfinite(L)&(L>0)
F=old['F'];oldL=(F[...,0]+2*F[...,1]+F[...,2])/4
targets={'G':old['G'],'V':old['V'],'L_scalar':oldL}
th=(np.degrees(np.arctan2(-(yy-cy),xx-cx))%360//30).astype(int)
fit=good&(d>=25)&(d<100)&old['domini']
t=np.clip((d-12)/13,0,1);weight=(1-t*t*(3-2*t))*good
scales={};heldout={}
for name,arr in targets.items():
    mask=fit&np.isfinite(arr)&(arr>0);gain=float(np.median(arr[mask]/L[mask]));scales[name]=gain
    q[name]=np.where(weight>0,arr*(1-weight)+L*gain*weight,arr).astype(np.float32)
    heldout[name]={}
    for fold in [0,1]:
        train=mask&(th%2==fold);test=mask&(th%2!=fold);g=float(np.median(arr[train]/L[train]));row={'gain':g,'sectors':{}}
        for k in range(12):
            m=test&(th==k)
            if m.any():row['sectors'][str(k*30)]=np.percentile((g*L[m]/arr[m]-1)*100,[16,50,84]).tolist()
        heldout[name][str(fold)]=row
    assert np.array_equal(q[name][d>=25],arr[d>=25],equal_nan=True)
q['F']=F # F remains the original RGB reference; E3 uses explicit L_scalar.
geo=q['domini_E'];q['domini']=np.where(d<25,geo&good,old['domini']);q['scalar_observed']=L;q['scalar_valid']=good
q['beta']=np.where(d<25,q['domini'].astype(np.float32),old['beta']);q['dins_franja']=q['beta']>0
np.savez_compressed(p/'Q_OBSERVED.npz',**q)
rep={'representation':'Observed linear L=(R+2G+B)/4, not CIE Y. No spectral colour replacement in output; constant conversion to historic scalar filter units only.',
    'unit_scales':scales,'fit_region':[25,100],'join_px':[12,25],'heldout_constants':heldout,
    'new_filter_pixels':int((q['domini']&~old['domini']&(d<25)).sum()),'lost_filter_pixels':int((~q['domini']&old['domini']&(d<25)).sum()),
    'E_observed_unchanged':bool(np.array_equal(q['E_observed'],z['E_observed'],equal_nan=True)),
    'F_legacy_unchanged':bool(np.array_equal(q['F'],F,equal_nan=True)),
    'warning':'Do not call F the new physical RGB: it is the unchanged legacy reference. New physical RGB is E_observed; L_scalar is the explicit E3 intensity input.'}
(p/'SCALAR.json').write_text(json.dumps(rep,indent=2));print(json.dumps({k:v for k,v in rep.items()if k!='heldout_constants'},indent=2))
