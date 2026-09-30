"""Native short-frame identifiability pilot; no corrected pixels or mask output.
Physical 90mm Airy OTF plus seeing, positive peaked/decaying solar exterior,
curved radial coordinate and native square-pixel quadrature. Lunar deep plane
frozen from native observations; an equal linear deep gauge projects every
solar basis. Green parities and inner band are held out. Likelihood here is
conditional on existing variance/calibration and not a physical confidence claim.
"""
from common50 import *
from scipy.fft import rfft,irfft,rfftfreq
from scipy.optimize import nnls
from numpy.polynomial.legendre import leggauss
import time
from PIL import Image
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
SRC=ROOT/'output/earthshine_native_psf_20260911'
scale=2.1494813525884373;step=1/32;coord=np.arange(-64,64+step,step)
fc=.09*scale*np.pi/(180*3600)/(550e-9)
fn,fw=leggauss(1024);freq=(fn+1)*fc/2;fw=fw*fc/2;nu=freq/fc
OTF=2/np.pi*(np.arccos(nu)-nu*np.sqrt(1-nu*nu));lambdas=[.5,1,2,4,8,16,32,64]
sigmas=np.arange(.5,1.81,.1);deltas=np.arange(-1.5,1.501,.1)
phase=2*np.pi*coord[:,None]*freq[None,:];SIN=np.sin(phase);COS=np.cos(phase);profiles={}
for sigma in sigmas:
 h=OTF*np.exp(-2*np.pi**2*sigma*sigma*freq*freq)*fw
 cols=[.5+SIN@(h/(np.pi*freq))]
 for lam in lambdas:
  a=1/lam;den=a*a+(2*np.pi*freq)**2
  cols.append(COS@(2*h*a/den)+SIN@(2*h*(2*np.pi*freq)/den))
 profiles[round(float(sigma),3)]=np.stack(cols,-1)
del SIN,COS,phase
GL,W=leggauss(5);GL=GL/2;W=W/2;u,v=np.meshgrid(GL,GL);quad=np.c_[u.ravel(),v.ravel()];qw=(W[:,None]*W[None,:]).ravel()
plan=dict(method=__doc__,stems=['572A2973','572A2991'],angles_deg=[0,270],tangent_half_width_px=4,normal_range_px=[-35,25],frozen_lunar_plane_range=[-35,-20],heldout_inner_band=[-15,-3],parity_swap=True,sigma_grid=sigmas.tolist(),delta_grid=deltas.tolist(),exterior_decay_lengths=lambdas,acceptance='No promotion on this pilot alone. Reject if parity/inner prediction fails or equally adequate fits imply Moon-side uncertainty comparable to lunar structure. No radius or PSF applied.',finite_domain='Infinite half-plane and positive exponential transforms integrated over Airy finite frequency cutoff by1024-point GL; profile grid1/32px. Local Airy curvature still approximated by straight optical convolution at curved pixel coordinates; no promotion.')
save('C1_plan.json',plan);rows=[]
for stem in plan['stems']:
 z=np.load(SRC/f'A0_native_samples_{stem}.npz');x=z['x'];y=z['y'];rad=np.hypot(x-CX,y-CY);theta=np.arctan2(y-CY,x-CX);edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
 for angle in plan['angles_deg']:
  t=time.time();th=np.deg2rad(angle);er=float(np.interp(th%(2*np.pi),np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi));tang=-(x-CX)*np.sin(th)+(y-CY)*np.cos(th);d=rad-er
  sel=z['valid']&(z['q']>.99)&np.isfinite(z['g'])&(abs(tang)<4)&(d>=-35)&(d<=25)&((x-CX)*np.cos(th)+(y-CY)*np.sin(th)>0)
  xx=x[sel];yy=y[sel];dd=d[sel];tt=tang[sel];g=z['g'][sel];var=z['variance'][sel];par=z['green_plane'][sel];J=z['native_to_world'];dxdy=quad@J.T
  dq=np.hypot(xx[:,None]+dxdy[None,:,0]-CX,yy[:,None]+dxdy[None,:,1]-CY)-er
  deep=(dd>=-35)&(dd<=-20);A=np.c_[np.ones(len(g)),dd/30,tt/4];iv=1/np.maximum(var,1);P=np.linalg.pinv(A[deep].T@(iv[deep,None]*A[deep]))@(A[deep].T*iv[deep]);coeff=P@g[deep];B=A@coeff;target=g-B
  # Each basis is centred on precisely the same deep-only linear estimator.
  target_noise=np.sqrt(np.maximum(var,1));grids=[]
  for parity in [0,1]:
   # Native green labels are inspected, never assumed 0/1 below.
   label=np.unique(par)[parity];train=(par==label)&~((dd>=-15)&(dd<=-3));train&=~deep
   reserve=(par!=label)&~deep;inside=(dd>=-15)&(dd<=-3)
   if train.sum()<15:raise RuntimeError(('few samples',stem,angle,train.sum(),np.unique(par)))
   fits=[]
   for sigma,prof in profiles.items():
    for delta in deltas:
     Q=np.stack([np.interp((dq-delta).ravel(),coord,prof[:,j]).reshape(dq.shape)@qw for j in range(prof.shape[1])],-1)
     Q=Q-A@(P@Q[deep]);scale_cols=np.maximum(np.sqrt(np.mean(Q[train]**2,axis=0)),1e-8)
     H=Q/scale_cols;beta,_=nnls(H[train]/target_noise[train,None],target[train]/target_noise[train],maxiter=500)
     pred=H@beta;train_chi=float(np.mean(((target-pred)[train]/target_noise[train])**2));fits.append((train_chi,sigma,float(delta),beta/scale_cols,pred))
   fits.sort(key=lambda a:a[0]);best=fits[0];minchi=best[0];near=[a for a in fits if a[0]<=minchi+max(.1,2/np.sqrt(train.sum()))];sp=np.stack([a[4] for a in near]);spread=np.ptp(sp,axis=0);last=(dd>=-6)&(dd<=-.5)
   metrics=dict(stem=stem,angle=angle,train_label=int(label),n_samples=len(g),n_train=int(train.sum()),n_reserve=int(reserve.sum()),frozen_plane=coeff.tolist(),best_sigma=best[1],best_delta=best[2],best_coeff=best[3].tolist(),train_chi2=minchi,reserve_chi2=float(np.mean(((target-best[4])[reserve]/target_noise[reserve])**2)),inner_chi2=float(np.mean(((target-best[4])[inside]/target_noise[inside])**2)),near_models=len(near),near_delta_range=[min(a[2] for a in near),max(a[2] for a in near)],near_sigma_range=[min(a[1] for a in near),max(a[1] for a in near)],inner_spill_spread_G=np.percentile(spread[inside],[50,95]).tolist(),last_spill_spread_G=np.percentile(spread[last],[50,95]).tolist(),last_corrected_G=np.percentile((g-best[4])[last],[5,50,95]).tolist(),boundary=best[1] in [min(profiles),max(profiles)] or abs(best[2])>1.49)
   rows.append(metrics);tag=f'{stem}_{angle}_p{int(label)}';np.savez_compressed(OUT/f'C1_{tag}.npz',distance=dd,tangent=tt,observed=g,variance=var,frozen_lunar=B,predicted_spill=best[4],spread=spread,train=train,reserve=reserve,inner=inside,parity=par)
   save('C1_results.json',dict(plan=plan,rows=rows));print(json.dumps(metrics),flush=True)
   fig,axs=plt.subplots(2,1,figsize=(8,6),layout='constrained');idx=np.argsort(dd)
   axs[0].scatter(dd,g,s=6,label='Native green');axs[0].plot(dd[idx],(B+best[4])[idx],lw=1,label='Solar forward + frozen deep plane');axs[0].set_yscale('symlog',linthresh=1000);axs[0].legend(fontsize=7);axs[0].set_title(tag)
   axs[1].scatter(dd,g-best[4],s=6,label='Observed minus predicted solar');axs[1].plot(dd[idx],B[idx],label='Deep-only reference');axs[1].fill_between(dd[idx],B[idx]-spread[idx]/2,B[idx]+spread[idx]/2,alpha=.2,label='Near-fit spill range');axs[1].set_ylim(-1000,5000);axs[1].legend(fontsize=7);fig.savefig(OUT/f'C1_{tag}.png',dpi=120);plt.close(fig)
  print('PATCH_DONE',stem,angle,time.time()-t,flush=True)
