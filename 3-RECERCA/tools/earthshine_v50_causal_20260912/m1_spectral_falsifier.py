"""Minimal two-component spectral falsifier on calibrated camera channels.
Deep planes are nuisance backgrounds, never recovered lunar DC. A lunar colour
direction is learned from interior spatial structure in one long exposure;
solar colour from exterior of the first short. The entire limb, odd sectors,
other epoch and each third camera channel are withheld. No NNLS or clipping.
"""
from common50 import *
from scipy.ndimage import gaussian_filter
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY);sector=(np.arctan2(y-CY,x-CX)%(2*np.pi)*12/np.pi).astype(int);train=(r<330)&(sector%2==0);D=np.stack([np.ones((N,N)),(x-CX)/455,(y-CY)/455],-1);frames={};planes={}
for stem in ['572A2978','572A2996','572A2975','572A2993']:
 z=np.load(OUT/f'M0_camera_{stem}.npz');a=z['camera'].astype(float);p=np.linalg.lstsq(D[train],a[train],rcond=None)[0];planes[stem]=p.tolist();frames[stem]=a-D@p
z=frames['572A2978'];hp=gaussian_filter(np.nan_to_num(z),(6,6,0))-gaussian_filter(np.nan_to_num(z),(30,30,0));cov=np.cov(hp[train].T);val,vec=np.linalg.eigh(cov);m=vec[:,-1];m/=m[1]
outside=(r>470)&(r<485)&(sector%2==0)&np.all(np.isfinite(frames['572A2975']),axis=-1);solar=frames['572A2975'][outside];s=np.median(solar/solar[:,1:2],axis=0);A=np.stack([m,s],axis=1)
rows=[];models=[]
for stem in ['572A2975','572A2993']:
 z=frames[stem]
 # Nonoverlapping six-pixel block means reduce CFA phase sampling differences.
 q=6;h=N//q;a=z[:h*q,:h*q].reshape(h,q,h,q,3).mean((1,3));rr=r[:h*q,:h*q].reshape(h,q,h,q).mean((1,3));ss=sector[:h*q,:h*q].reshape(h,q,h,q)[:,q//2,:,q//2];valid=np.all(np.isfinite(a),axis=-1)
 for hold in range(3):
  fit=[c for c in range(3) if c!=hold];inv=np.linalg.inv(A[fit]);coef=a[...,fit]@inv.T;pred=coef@A[hold];res=a[...,hold]-pred;noise=np.std(res[(rr<330)&(ss%2==1)&valid]);bands=[]
  for lo,hi in [(0,330),(415,435),(435,449),(449,454),(454,460),(470,485)]:
   k=(rr>=lo)&(rr<hi)&(ss%2==1)&valid;bands.append(dict(radius=[lo,hi],n=int(k.sum()),third_channel_residual_percentiles=np.percentile(res[k],[5,50,95]).tolist(),rms_vs_deep=float(np.sqrt(np.mean(res[k]**2))/noise),M_percentiles=np.percentile(coef[...,0][k],[5,50,95]).tolist(),fraction_M_below_minus_3_deep_sd=float(np.mean(coef[...,0][k]<-3*np.std(coef[...,0][(rr<330)&(ss%2==1)&valid])))))
  rows.append(dict(stem=stem,withheld_camera_channel=hold,condition=float(np.linalg.cond(A[fit])),deep_third_channel_noise=float(noise),regions=bands));print(stem,hold,'last',bands[3],flush=True)
save('M1_spectral_falsifier.json',dict(method=__doc__,lunar_direction=m.tolist(),solar_direction=s.tolist(),deep_planes=planes,covariance=cov.tolist(),eigenvalues=val.tolist(),rows=rows,scope='falsifier only, no correction or source pixels promoted'))
