from pathlib import Path
import json,numpy as np
from scipy.ndimage import gaussian_filter,map_coordinates,minimum_filter
from scipy.optimize import minimize
O=Path('/private/tmp/v105_base_sources_20260926');H=np.load(O/'detail_audit_hp_sigma1.npz');Q=np.load(O/'572A2975.npz');d=Q['dreal'];by,ey,bx,ex=Q['box'];yy,xx=np.mgrid[by:ey,bx:ex];th=np.degrees(np.arctan2(-(yy-3775.747534),xx-5361.768112))%360;sec=(th//30).astype(int)
def rho(a,b):return float(np.corrcoef(a,b)[0,1])
out={'scope':'diagnostic of correlation sensitivity, no output pixels/geometries modified','heldout':'fit even30deg sectors; evaluate odd sectors','fixed_domain':'raw2975 distance20..150; all original sigma1 kernels and maximum diagnostic Gaussian2 plus shift3 contained in observed coronal input by additional11px square erosion','variants':[]}
for a,b in [('09','2969'),('2975','2969'),('09','2993')]:
 safe=minimum_filter((H[f'safe_{a}']&H[f'safe_{b}']).astype('uint8'),size=23,mode='constant')>0;z=safe&(d>20)&(d<150)
 fit=z&(sec%2==0);test=z&(sec%2==1);y,x=np.where(fit);stride=max(1,len(y)//35000);y=y[::stride];x=x[::stride];ty,tx=np.where(test);stride=max(1,len(ty)//50000);ty=ty[::stride];tx=tx[::stride]
 for sa in [0,.5,1,2]:
  A=gaussian_filter(H[a],sa,truncate=4) if sa else H[a]
  for sb in [0,.5,1,2]:
   B=gaussian_filter(H[b],sb,truncate=4) if sb else H[b]
   tar=B[y,x]
   def cost(p):return 1-rho(tar,map_coordinates(A,[y+p[1],x+p[0]],order=1,mode='constant',cval=0,prefilter=False))
   opt=minimize(cost,[0.,0.],method='Powell',bounds=[(-3,3),(-3,3)],options={'maxiter':30,'xtol':.01,'ftol':1e-6});p=opt.x
   row={'pair':[a,b],'extra_Gaussian_sigma':[sa,sb],'sampling_translation_dxdy':p.tolist(),'fit_n':len(y),'heldout_n':len(ty),'fit_rho':1-float(opt.fun),'heldout_rho_zero_shift':rho(B[ty,tx],A[ty,tx]),'heldout_rho_fit_shift':rho(B[ty,tx],map_coordinates(A,[ty+p[1],tx+p[0]],order=1,mode='constant',cval=0,prefilter=False))};out['variants'].append(row)
 rows=[r for r in out['variants'] if r['pair']==[a,b]];best=max(rows,key=lambda r:r['fit_rho']);print(a,b,'best training-selected',json.dumps(best),flush=True);print('no extra smoothing',json.dumps(rows[0]),flush=True)
(O/'DETAIL_PSF_PHASE_SENSITIVITY.json').write_text(json.dumps(out,indent=2))
