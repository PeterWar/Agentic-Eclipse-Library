from pathlib import Path
import json,numpy as np
from scipy.ndimage import gaussian_filter,map_coordinates
from scipy.optimize import minimize
R=Path.cwd();O=R/'output/v62_prominencies_20260913';A=O/'arrays';CX,CY=5361.768111973117,3775.747534140857
base=np.load(A/'V61_L02_C1.npy').astype('float64')/65535;src=np.load(A/'V61_L19_C1.npy').astype('float64')/65535
S=gaussian_filter(src,1)-gaussian_filter(src,5);B=gaussian_filter(base,1)-gaussian_filter(base,5)
spec=[('west_fit',4890,3755,40,False),('SE_fit',5793,3956,30,False),('top_reserved',5277,3318,25,True),('west_lower_check',4895,3820,40,True),('NW_check',5000,3500,30,True)]
patches=[]
for name,x,y,h,res in spec:
 gy,gx=np.mgrid[y-h:y+h,x-h:x+h];lr=np.hypot(gx-5376.5681,gy-3776.6475);ok=(lr>466)&(lr<510)&(src[gy-2777,gx-4377]>.008)&(base[gy-2777,gx-4377]>.01)
 patches.append((name,gx[ok].astype(float),gy[ok].astype(float),S[gy[ok]-2777,gx[ok]-4377],res))
def score(p,it):
 _,x,y,v,_=it;th=np.deg2rad(p[2]);sc=p[3];xx=CX+sc*(np.cos(th)*(x-CX)-np.sin(th)*(y-CY))+p[0];yy=CY+sc*(np.sin(th)*(x-CX)+np.cos(th)*(y-CY))+p[1]
 return float(np.corrcoef(v,map_coordinates(B,[yy-2777,xx-4377],order=1))[0,1])
fit=[q for q in patches if not q[-1]]
def loss(p):return -np.mean([score(p,q) for q in fit])
opts=[]
for sc in [.988,1,1.012]:
 opt=minimize(loss,[0,0,0,sc],method='Nelder-Mead',bounds=[(-6,6),(-6,6),(-.3,.3),(.98,1.02)],options={'maxiter':1500,'xatol':1e-5});opts.append(opt)
best=min(opts,key=lambda o:o.fun).x
rows=[]
for it in patches:
 local=minimize(lambda p:-score([p[0],p[1],0,1],it),[0,0],method='Nelder-Mead',bounds=[(-8,8),(-8,8)])
 rows.append(dict(name=it[0],reserved=it[-1],n=len(it[1]),current=score([0,0,0,1],it),candidate=score(best,it),forced_shrink_1pct=score([0,0,0,.99],it),local_dxdy=local.x.tolist(),local_ncc=-float(local.fun)))
out=dict(candidate_relative_to_V61=best.tolist(),rows=rows,decision='diagnostic only; no geometry promoted');print(json.dumps(out,indent=2));(O/'B0_geometry.json').write_text(json.dumps(out,indent=2))
