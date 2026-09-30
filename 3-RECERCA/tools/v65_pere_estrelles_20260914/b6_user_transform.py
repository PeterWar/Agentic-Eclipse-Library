from pathlib import Path
import numpy as np,cv2,json,tifffile as tf
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';P=R/'output/v64_geometria_20260914';A=O/'arrays'
old=tf.imread(P/'D1_foreground_unmasked.tif').astype('float32')/65535
if old.shape[2]==4:old=np.divide(old[...,:3],old[...,3:],out=np.zeros_like(old[...,:3]),where=old[...,3:]>.05)
cur=np.stack([np.load(A/f'L76_C{c}.npy') for c in range(3)],-1).astype('float32')/65535
# Recover Pere's already-applied sampling for colour-source comparison only. Never move either project layer.
mask=np.zeros((2000,2000),np.uint8);mask[480:650,750:1180]=1;mask[640:1300,440:640]=1;mask[1200:1440,620:950]=1
# Exclude pathological dematting in black core; compare red excess above continuum.
def signal(a):return cv2.GaussianBlur(np.maximum(a[...,0]-1.35*a[...,1],0),(0,0),1)
a=signal(old);b=signal(cur);M=np.eye(2,3,dtype=np.float32)
cc,M=cv2.findTransformECC(b,a,M,cv2.MOTION_AFFINE,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,150,1e-7),mask,3)
# ECC returns destination-to-source mapping for inverse-map warp; output-only matrix must be interpreted explicitly.
warped=cv2.warpAffine(a,M,(2000,2000),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)
rep=dict(correlation=float(cc),current_to_V64_ROI=M.tolist(),claim='Read-only recovery of the manual transform for tracing original photographic colour. No existing pixels, alignment or mask changed.',before_rms=float(np.sqrt(np.mean((a[mask>0]-b[mask>0])**2))),after_rms=float(np.sqrt(np.mean((warped[mask>0]-b[mask>0])**2))))
(O/'B6_user_colour_map.json').write_text(json.dumps(rep,indent=2));print(rep)
