"""Exploratory broad source forward models. No PSB modification, no local paint."""
from pathlib import Path
import numpy as np,json
from scipy.ndimage import gaussian_filter
from scipy.interpolate import BSpline
from scipy.stats import spearmanr
R=Path.cwd();O=R/'output/earthshine_broad_lroc_20260914'
S={
 'V49':np.load(R/'output/earthshine_v49_pere_reveal_20260912/A0_Pere_moon_RGB16.npy').mean(-1),
 'V53':np.load(R/'research/tools/earthshine_v50_temporal_20260912/cau/lun_rgb_vel_u16.npy').mean(-1),
 'V68':np.load(R/'output/v68_artefactes_20260914/arrays/B10_photo_pilot.npz')['candidate'].mean(-1),
 'LROC':np.load(R/'output/v68_lroc_revisio_20260914/arrays/L62_exact_psb.npz')['rgb'].mean(-1),
 'preCR':np.load(R/'research/tools/v46_earthshine_20260911/cau/live_lunar_rgb_u16.npy').mean(-1)}
T={'Sony':np.load(R/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference'],
 'Vixen':np.load(R/'output/earthshine_v56_three_routes_20260913/arrays/R5_sources.npz')['Gclean']}
y,x=np.mgrid[:1400:4,:1400:4];r=np.hypot(x-699.568111973117,y-699.6475341408573);th=np.arctan2(y-699.6475341408573,x-699.568111973117)%(2*np.pi)
mark=(x>=550)&(x<723)&(y>=902)&(y<1048);guard=(x>=500)&(x<773)&(y>=852)&(y<1098)
valid=(r>80)&(r<400);sector=(th/(np.pi/6)).astype(int);fit=valid&~guard&(sector%2==0);hold=valid&~guard&(sector%2==1)
SS={k:gaussian_filter(np.nan_to_num(a),8)[::4,::4] for k,a in S.items()};TT={k:gaussian_filter(np.nan_to_num(a),8)[::4,::4] for k,a in T.items()}
# Fixed radial cubic B splines, 100px knot spacing; angular harmonics limited to0,1,2.
knots=np.array([0]*4+[100,200,300]+[450]*4);basis=BSpline.design_matrix(np.clip(r.ravel(),0,450),knots,3).toarray()
rows=[];preds={}
for harmonics in [0,1,2]:
 terms=[basis]
 for m in range(1,harmonics+1):
  for z in [np.cos(m*th),np.sin(m*th)]:terms.append(basis*z.ravel()[:,None])
 B=np.concatenate(terms,axis=1)
 for name,a in SS.items():
  c=np.median(a[fit]);scale=np.std(a[fit]);p=(a.ravel()-c)/scale
  for degree in [1,2]:
   X=np.column_stack([p**j for j in range(1,degree+1)]+[B])
   for train,b in TT.items():
    coeff=np.linalg.lstsq(X[fit.ravel()],b.ravel()[fit.ravel()],rcond=None)[0];pred=(X@coeff).reshape(r.shape);res=b-pred
    rm=lambda mm:float(np.sqrt(np.mean(res[mm]**2)))
    row=dict(photo=name,source=train,harmonics=harmonics,photo_degree=degree,fit_rmse=rm(fit),hold_rmse=rm(hold),mark_rmse=rm(mark),mark_mean_residual=float(res[mark].mean()),mark_range=[float(np.min(res[mark])),float(np.max(res[mark]))],photo_coeff=coeff[:degree].tolist())
    rows.append(row)
    if harmonics==1 and degree==2:preds[name+'_'+train+'_residual']=res.astype('float32')
(O/'A3_forward.json').write_text(json.dumps(rows,indent=2)+'\n');np.savez_compressed(O/'arrays/A3_forward_residuals.npz',**preds)
for q in rows:
 if q['harmonics']==1 and q['photo_degree']==2:print(q,flush=True)
