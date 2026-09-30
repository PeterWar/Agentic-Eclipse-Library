"""Diagnostic positive solar forward fit to complete Vixen stacks.
No Photoshop edit. Fixed stellar core and A1 wings. Solar emission is confined
to the observed optical exterior; a single plane is fit only at r<350. Positive
Poisson iterations avoid the negative intrinsic solar rings of the FFT inverse.
The fit is conditional on the inherited contour and effective stack PSF.
"""
from common50 import *
from scipy.fft import rfft2,irfft2
from PIL import Image
import time
p=np.array(json.loads((OUT/'A1_fit.json').read_text())['p']);core=json.loads((OUT/'B0_native_star_psf.json').read_text())['core_sigma_native_percentiles'][1]
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY);M=np.load(OUT/'B2_joint_inputs.npz')['mask'];O=1-M;deep=r<350;X=(x-CX)/455;Y=(y-CY)/455;A=np.c_[np.ones(deep.sum()),X[deep],Y[deep]]
kx=np.fft.rfftfreq(N)[None,:];ky=np.fft.fftfreq(N)[:,None];f2=kx*kx+ky*ky
T=np.full(f2.shape,1-p.sum())
for a,s in zip(p,SIGMA):T+=a*np.exp(-2*np.pi**2*s*s*f2)
T*=np.exp(-2*np.pi**2*(core*core+1/3+1/12)*f2)
def blur(a):return irfft2(rfft2(a,workers=2)*T,s=(N,N),workers=2)
save('C0_plan.json',dict(method=__doc__,p=p.tolist(),core=core,iterations=300,source='Existing full67 Vixen source ensemble and disjoint early/late halves',qualification='Experimental stack approximation, not publication'))
for group in ['all','early','late']:
 z=np.load(ROOT/f'output/earthshine_native_psf_20260911/B0_new_{group}.npz');G=z['candidate'];cf=np.linalg.lstsq(A,G[deep],rcond=None)[0];B=cf[0]+cf[1]*X+cf[2]*Y
 S=np.maximum(G-B,0)*O;start=time.time();history=[]
 for it in range(300):
  pred=blur(O*S);S*=np.maximum(blur(np.maximum(G,0)/np.maximum(B+pred,1)),0)
  if it%50==0 or it==299:
   C=G-pred;stats={f'{lo}_{hi}':np.percentile(C[(r>=lo)&(r<hi)],[5,50,95]).tolist() for lo,hi in [(0,350),(435,449),(449,454),(454,460)]};history.append(dict(iteration=it,profiles=stats));print(group,it,stats,flush=True)
 spill=blur(O*S);C=G-spill;np.savez_compressed(OUT/f'C0_stack_{group}.npz',solar=S,spill=spill,corrected=C,background=B,mask=M,transfer=T)
 u=np.clip(.13+.07*np.arcsinh((C-528)/20),0,1);Image.fromarray((u*255).astype('uint8')).save(OUT/f'C0_stack_{group}.png')
 save(f'C0_stack_{group}.json',dict(history=history,seconds=time.time()-start))
