from pathlib import Path
import numpy as np,cv2,tifffile as tf,json
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';A=O/'arrays';P=R/'output/v61_interiors_limbe_20260913';native=tf.imread(P/'V61_interiors_only.tif').astype('float32')/65535;cur=np.stack([np.load(A/f'L96_C{c}.npy') for c in range(3)],-1).astype('float32')/65535
if native.shape[2]==4:native=np.divide(native[...,:3],native[...,3:],out=np.zeros_like(native[...,:3]),where=native[...,3:]>.01)
y,x=np.mgrid[:2000,:2000];rad=np.hypot(x-1000,y-1000);mask=((rad>448)&(rad<540)).astype('uint8');mask[450:670,820:1000]=0
# Use gradient of log green to remove exposure/render amplitude, masked held-out upper prominence.
def signal(a):
 v=np.log(np.maximum(a[...,1],.001));return cv2.GaussianBlur(v,(0,0),1)-cv2.GaussianBlur(v,(0,0),8)
a=signal(native);b=signal(cur);M=np.eye(2,3,dtype=np.float32)
cc,M=cv2.findTransformECC(b,a,M,cv2.MOTION_EUCLIDEAN,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,200,1e-7),mask,3)
w=cv2.warpAffine(a,M,(2000,2000),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP);sel=np.s_[500:580,850:950];rep=dict(correlation=float(cc),current_to_original_ROI=M.tolist(),train_rms_before=float(np.sqrt(np.mean((a[mask>0]-b[mask>0])**2))),train_rms_after=float(np.sqrt(np.mean((w[mask>0]-b[mask>0])**2))),held_top_correlation_before=float(np.corrcoef(a[sel].ravel(),b[sel].ravel())[0,1]),held_top_correlation_after=float(np.corrcoef(w[sel].ravel(),b[sel].ravel())[0,1]),claim='Diagnostic mapping only. No existing project transform.')
(O/'B8_colour_mapping.json').write_text(json.dumps(rep,indent=2));print(rep)
