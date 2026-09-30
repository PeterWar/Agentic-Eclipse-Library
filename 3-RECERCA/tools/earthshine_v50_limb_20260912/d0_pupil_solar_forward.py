"""Optical-source ablation: fixed 90mm Airy pupil, measured plate scale.
This REPLACES A1 Gaussian-wing mixture. No extra empirical wing is added.
Positive solar inversion uses the actual 2D exterior and original physical
mask; no linear radial exterior approximation. Stack/core/crop approximations
remain unqualified, including finite Airy-tail exterior. Diagnostic only.
"""
from common50 import *
from scipy.fft import rfft2,irfft2
from PIL import Image
import time
scale=2.1494813525884373;seeing=.97;lam=550.;Y,X=np.mgrid[:N,:N];r=np.hypot(X-CX,Y-CY);M=np.load(OUT/'B2_joint_inputs.npz')['mask'];O=1-M;deep=r<350;xx=(X-CX)/455;yy=(Y-CY)/455;A=np.c_[np.ones(deep.sum()),xx[deep],yy[deep]]
kx=np.fft.rfftfreq(N)[None,:];ky=np.fft.fftfreq(N)[:,None];f2=kx*kx+ky*ky;nu=np.minimum(np.sqrt(f2)*lam*1e-9/(.09*scale*np.pi/(180*3600)),1)
T=2/np.pi*(np.arccos(nu)-nu*np.sqrt(1-nu*nu));T*=np.exp(-2*np.pi**2*(seeing*seeing+1/3+1/12)*f2)
def blur(a):return irfft2(rfft2(a,workers=2)*T,s=(N,N),workers=2)
save('D0_plan.json',dict(method=__doc__,aperture_m=.09,wavelength_nm=lam,seeing_sigma=seeing,scale=scale,iterations=300))
for group in ['all','early','late']:
 G=np.load(ROOT/f'output/earthshine_native_psf_20260911/B0_new_{group}.npz')['candidate'];cf=np.linalg.lstsq(A,G[deep],rcond=None)[0];B=cf[0]+cf[1]*xx+cf[2]*yy;S=np.maximum(G-B,0)*O;start=time.time()
 for it in range(300):
  spill=blur(O*S);S*=np.maximum(blur(np.maximum(G,0)/np.maximum(B+spill,1)),0)
 spill=blur(O*S);C=G-spill;np.savez_compressed(OUT/f'D0_pupil_{group}.npz',solar=S,spill=spill,corrected=C,background=B,mask=M,transfer=T)
 u=np.clip(.13+.07*np.arcsinh((C-528)/20),0,1);Image.fromarray((u*255).astype('uint8')).save(OUT/f'D0_pupil_{group}.png')
 stats={f'{lo}_{hi}':np.percentile(C[(r>=lo)&(r<hi)],[5,50,95]).tolist() for lo,hi in [(0,350),(415,435),(435,449),(449,454),(454,460)]};save(f'D0_pupil_{group}.json',dict(profiles=stats,seconds=time.time()-start));print(group,stats,flush=True)
