"""One global affine display calibration to the user's chosen lunar aesthetic.
Fit brightness/contrast on alternating lunar sectors, verify on the other half.
Apply exactly the same gain and offset to the entire rectangle. This changes
photographic display only; it does not invent CameraRaw sliders or spatial
retouch. Source texture and the CameraRaw rendering precede this calibration.
"""
from validation_common import *
a=np.load(OUT/'E2_candidate_rgb.npy').astype(float);old=np.load(PREV/'A0_live_layer21_rgb.npy').astype(float);x=a.mean(-1);target=old.mean(-1)
yy,xx=np.mgrid[:N,:N];r=np.hypot(xx-CX,yy-CY);theta=np.arctan2(yy-CY,xx-CX)%(2*np.pi);train=((theta//(np.pi/8)).astype(int)%2==0)&(r<430);test=(~train)&(r<430)
A=np.stack([np.ones(train.sum()),x[train]],1);intercept,gain=np.linalg.lstsq(A,target[train],rcond=None)[0];assert gain>0
mapped=intercept+gain*x;delta=np.rint(mapped-target).astype(np.int32);new=old.astype(np.int32)+delta[...,None];assert new.min()>=0 and new.max()<=65535
np.save(OUT/'E3a_candidate_rgb.npy',new.astype(np.uint16))
err=mapped-target
save('E3a_global_aesthetic.json',dict(method=__doc__,offset_DN16=float(intercept),gain=float(gain),fit_pixels=int(train.sum()),holdout_pixels=int(test.sum()),holdout_signed_q=np.percentile(err[test],[0,5,50,95,100]).tolist(),holdout_rms_DN16=float(np.sqrt(np.mean(err[test]**2))),no_spatial_tone_mask=True,old_chroma_exact=True,clipped_pixels=0,scope='Approximate photographic style preservation; exact historical CameraRaw replay not established.'))
print(json.loads((OUT/'E3a_global_aesthetic.json').read_text()),flush=True)
