"""Diagnostic optical counterfactual relative to the SAME physical source input.
Preserve actual V49 source residual detail and chroma. Remove one global affine
Camera Raw response change, fitted only in r<350, before differencing corrected
and uncorrected optical source. A separate view tests measured Vixen support;
this is NOT a validated geometry or authorized promotion of that probe mask.
"""
from common50 import *
from scipy.optimize import isotonic_regression
from scipy.interpolate import PchipInterpolator
from PIL import Image
Y,X=np.mgrid[:N,:N];r=np.hypot(X-CX,Y-CY);sec=(np.arctan2(Y-CY,X-CX)%(2*np.pi)*24/(2*np.pi)).astype(int);deep=r<350
pere=np.load(V49/'A0_Pere_moon_RGB16.npy').astype(float);target=pere.mean(-1);mask=np.load(V49/'A0_inherited_mask_roi.npy').astype(float)/65535;bg=np.load(V49/'A2_sense_font_lunar_RGB16.npy').astype(float)
a=np.load(OUT/'E1_physical_RGB16.npy').mean(-1);b=np.load(OUT/'E1_pupil_RGB16.npy').mean(-1)
train=deep&(sec%2==0);test=deep&(sec%2==1);cf=np.linalg.lstsq(np.c_[b[train],np.ones(train.sum())],a[train],rcond=None)[0];bc=np.clip(cf[0]*b+cf[1],0,65535)
knots=[];train=(r<458)&(mask>.8)&(sec%2==0)
for lo in np.arange(0,65535,300):
 w=train&(a>=lo)&(a<lo+300)
 if w.sum()>=100:knots.append([float(a[w].mean()),float(np.median(target[w])),int(w.sum())])
k=np.array(knots);yy=isotonic_regression(k[:,1],weights=k[:,2]).x;f=PchipInterpolator(np.r_[0,k[:,0],65535],np.r_[0,yy,65535]);delta=f(bc)-f(a);rgb=np.rint(np.clip(pere+delta[...,None],0,65535)).astype(np.uint16);np.save(OUT/'E3_counterfactual_RGB16.npy',rgb)
M=np.load(OUT/'B2_joint_inputs.npz')['mask'];newmask=mask*M
for name,m in [('inherited',mask),('support',newmask)]:
 comp=np.rint(bg*(1-m[...,None])+rgb*m[...,None]).astype(np.uint16);np.save(OUT/f'E3_{name}_composite.npy',comp);Image.fromarray((comp>>8).astype('uint8')).save(OUT/f'E3_{name}_moon.png')
 rep={f'{lo}_{hi}':np.percentile((rgb.astype(float)-pere)[(r>=lo)&(r<hi)],[5,50,95]).tolist() for lo,hi in [(0,350),(415,435),(435,449),(449,454)]}
 np.save(OUT/'E3_support_mask_roi.npy',np.rint(newmask*65535).astype(np.uint16))
save('E3_probe.json',dict(method=__doc__,global_native_affine=cf.tolist(),affine_deep_heldout_error=np.percentile(abs(bc[test]-a[test]),[50,95,99]).tolist(),delta=rep,fit_knots=knots,fit_y=yy.tolist(),publication=False));print(rep,flush=True)
