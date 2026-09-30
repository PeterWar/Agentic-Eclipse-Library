from pathlib import Path
import numpy as np,pandas as pd,json
from scipy.special import erf
from scipy.optimize import least_squares
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';W=Path('/Users/USUARI/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/Work_2026-08-17');S=W/'sony';X=W/'xmatch'
cat=pd.read_csv(R/'output/v58_correccions_20260913/catalog_projected.csv');plate=json.loads((X/'final_solution.json').read_text())['sony_radial'];u=cat.xh_as.to_numpy();v=cat.yh_as.to_numpy();Q=np.c_[u*0+1,u,v,u*(u*u+v*v),v*(u*u+v*v)];Cpos=Q@np.array([plate['px'],plate['py']]).T
M=np.load(S/'warpM.npy');T=np.load(S/'warpT.npy');C=np.load(S/'warpC.npy');imgs={g:np.load(S/f'IMG{g}.npy',mmap_mode='r') for g in ['A','C']};psf=pd.read_csv(O/'S1_psf_stacks.csv');pars={}
for g in ['A','C']:
 d=psf[(psf.group==g)&(~psf.reserved)&(psf.snr_peak>10)&(psf.relative_residual<.3)];cov=[]
 for r in d.itertuples():
  c,s=np.cos(r.theta),np.sin(r.theta);rot=np.array([[c,-s],[s,c]]);cov.append(rot@np.diag([r.sigma1**2,r.sigma2**2])@rot.T)
 pars[g]=np.median(cov,axis=0)
Y,Xg=np.mgrid[-12:13,-12:13];B=np.c_[np.ones(625),Xg.ravel(),Y.ravel(),Xg.ravel()**2,Y.ravel()**2,(Xg*Y).ravel()];Bi=np.linalg.pinv(B);ann=np.hypot(Xg,Y)>8
# fixed template per native stack; 1px grid search +/-3; both dithers independently fit, then cross-checked

def template(dx,dy,g):
 xy=np.stack([Xg-dx,Y-dy],-1);I=np.linalg.inv(pars[g]);z=np.exp(-.5*np.einsum('...i,ij,...j->...',xy,I,xy));return z/z.sum()
def detect(im,x,y,g):
 xi,yi=int(round(x)),int(round(y));z=np.array(im[yi-12:yi+13,xi-12:xi+13],float)
 if z.shape!=(25,25) or not np.isfinite(z).all() or np.count_nonzero(z)==0:return None
 flat=z.ravel();z0=flat-B@(Bi@flat);bgplane=np.linalg.lstsq(B[ann.ravel()],flat[ann.ravel()],rcond=None)[0];noise=max(1.4826*np.median(abs((flat-B@bgplane)[ann.ravel()])),.025)
 def calc(dx,dy):
  t=template(dx,dy,g).ravel();t-=B@(Bi@t);den=t@t;flux=(t@z0)/den;sn=flux*np.sqrt(den)/noise;return sn,flux
 best=(-np.inf,0,0,0)
 for dy in np.arange(-3,4)+y-yi:
  for dx in np.arange(-3,4)+x-xi:
   sn,f=calc(dx,dy)
   if sn>best[0]:best=(sn,f,dx,dy)
 sn,f,dx,dy=best
 if sn>3:
  from scipy.optimize import minimize
  opt=minimize(lambda p:-calc(*p)[0],[dx,dy],method='Nelder-Mead',options=dict(maxiter=35,xatol=.03,fatol=.02));dx,dy=opt.x;sn,f=calc(dx,dy)
  if abs(dx-(x-xi))>3.6 or abs(dy-(y-yi))>3.6:return None
 return dict(x=float(xi+dx),y=float(yi+dy),snr=float(sn),flux=float(f),noise=float(noise),expected_distance=float(np.hypot(xi+dx-x,yi+dy-y)))
rows=[]
for kind in ['catalog','rotated_null']:
 pos=Cpos.copy()
 if kind=='rotated_null':pos=2*np.array([plate['sun_x'],plate['sun_y']])-pos
 for i,c in enumerate(pos):
  a=(c-C-T)@np.linalg.inv(M).T+C
  if not(50<c[0]<7918 and 50<c[1]<5270 and 50<a[0]<7918 and 50<a[1]<5270):continue
  if np.linalg.norm(c-[plate['sun_x'],plate['sun_y']])<310:continue
  # same native radius and full support for null and catalog
  fA=detect(imgs['A'],*a,'A');fC=detect(imgs['C'],*c,'C')
  if not fA or not fC:continue
  ac=(np.array([fA['x'],fA['y']])-C)@M.T+T+C;dist=np.linalg.norm(ac-[fC['x'],fC['y']]);total=np.hypot(fA['snr'],fC['snr']);accept=min(fA['snr'],fC['snr'])>=4 and total>=8 and dist<=2.5
  row=dict(kind=kind,catalog_index=int(i),HIP=cat.iloc[i].HIP,TYC=cat.iloc[i].TYC,V=float(cat.iloc[i].Vuse),x_final=float(cat.iloc[i].x_pred),y_final=float(cat.iloc[i].y_pred),native_C_pred=c.tolist(),native_A_pred=a.tolist(),A=fA,C=fC,separation=float(dist),total_snr=float(total),accepted=bool(accept));rows.append(row)
  if len(rows)%100==0:print(kind,len(rows),'accepted',sum(r['accepted'] and r['kind']==kind for r in rows),flush=True)
(O/'S2_detection.json').write_text(json.dumps(dict(thresholds=dict(each_min=4,total_min=8,independent_centres_max=2.5,search=3,inner_sony_radius=310),covariance={g:pars[g].tolist() for g in pars},rows=rows),indent=2))
for kind in ['catalog','rotated_null']:print(kind,sum(r['kind']==kind for r in rows),sum(r['kind']==kind and r['accepted'] for r in rows),flush=True)
