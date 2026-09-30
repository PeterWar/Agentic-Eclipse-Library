from pathlib import Path
import numpy as np,json
from scipy.ndimage import gaussian_filter,map_coordinates
from scipy.optimize import minimize
R=Path.cwd();O=R/'output/v68_lroc_revisio_20260914';P=R/'output/v68_artefactes_20260914';photo=np.load(P/'arrays/B10_photo_pilot.npz')['candidate'].mean(-1);lr=np.load(O/'arrays/L62_exact_psb.npz')['rgb'].mean(-1)
y,x=np.mgrid[:1400:4,:1400:4];r=np.hypot(x-699.568,y-699.648);th=np.arctan2(y-699.648,x-699.568)%(2*np.pi);orange=(x>=500)&(x<773)&(y>=852)&(y<1098);valid=(r>80)&(r<400)&~orange;fit=valid&((th//(np.pi/6)).astype(int)%2==0);hold=valid&~fit
def corr(a,b):
 a=a-a.mean();b=b-b.mean();return float(a@b/max(np.linalg.norm(a)*np.linalg.norm(b),1e-30))
def xy(p,sel):
 dx,dy,deg,ds=p;ca=np.cos(np.deg2rad(deg));sa=np.sin(np.deg2rad(deg));xx=x[sel]-699.568-dx;yy=y[sel]-699.648-dy
 return [699.648+(-sa*xx+ca*yy)/(1+ds),699.568+(ca*xx+sa*yy)/(1+ds)]
rows=[]
for mode in ['linear','log']:
 a=np.log(np.maximum(photo,1)) if mode=='log' else photo;b=np.log(np.maximum(lr,1)) if mode=='log' else lr;a=gaussian_filter(a,3)-gaussian_filter(a,16);b=gaussian_filter(b,3)-gaussian_filter(b,16)
 def score(p,sel):return corr(a[y[sel],x[sel]],map_coordinates(b,xy(p,sel),order=1,mode='nearest'))
 res=minimize(lambda p:-score(p,fit),[0.,0.,0.,0.],method='Powell',bounds=[(-8,8),(-8,8),(-1,1),(-.015,.015)],options={'xtol':1e-5,'ftol':1e-7,'maxiter':80})
 rows.append(dict(mode=mode,diagnostic_LROC_to_Moon_dx_dy_deg_scale_delta=res.x.tolist(),fit_before=score([0,0,0,0],fit),fit_after=score(res.x,fit),heldout_before=score([0,0,0,0],hold),heldout_after=score(res.x,hold),success=bool(res.success)))
(O/'A3_registration.json').write_text(json.dumps(dict(rows=rows,scope='Reference-only numerical diagnostic, all PSB geometry unchanged. Mark and 50px guard excluded; alternating sectors held out. No absolute astrometric registration claim.'),indent=2)+'\n');print(rows,flush=True)
