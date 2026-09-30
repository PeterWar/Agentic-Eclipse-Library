from pathlib import Path
import numpy as np,cv2,json
from scipy.ndimage import gaussian_filter
O=Path('/private/tmp/v105_root_pilots_20260926');S=Path('/private/tmp/v105_base_sources_20260926');D=Path('/private/tmp/eclipse_v104_diagnosi_20260926')
q=np.load(S/'572A2975.npz');raw=q['E'];by,ey,bx,ex=q['box'];A=np.load(D/'L303.npz');ref=np.stack([A['c'+str(c)] for c in range(3)],-1)[by-3000:ey-3000,bx-4600:ex-4600].astype(np.float32)/65535
N=raw[...,1];G=ref[...,1];yy,xx=np.mgrid[by:ey,bx:ex];r=np.hypot(xx-5375.7868,yy-3775.9775)-452.9785
z=(r>20)&(r<145)&q['valid_rgb']&(N>0)&(G>.02)&(G<.85)
# Normalize local log contrast; tone differences are removed only for registration.
def texture(x):
 l=np.log(np.maximum(x,1e-6));h=gaussian_filter(l,1.2)-gaussian_filter(l,12);return np.clip(h,-.2,.2).astype(np.float32)
tar=texture(N);inp=texture(G);z=cv2.erode(z.astype(np.uint8),np.ones((9,9),np.uint8));basecorr=float(np.corrcoef(tar[z>0],inp[z>0])[0,1]);results=[]
for motion in [cv2.MOTION_TRANSLATION,cv2.MOTION_EUCLIDEAN,cv2.MOTION_AFFINE]:
 mat=np.eye(2,3,dtype=np.float32)
 try:
  cc,mat=cv2.findTransformECC(tar,inp,mat,motion,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,300,1e-7),z,3)
  warped=cv2.warpAffine(inp,mat,(1400,1400),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)
  out=cv2.warpAffine(ref,mat,(1400,1400),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)
  result={'motion':motion,'cc':float(cc),'matrix_template_to_input_local':mat.tolist(),'corr_original':basecorr,'corr_warped':float(np.corrcoef(tar[z>0],warped[z>0])[0,1])}
  for a,b in [(0,90),(90,180),(180,270),(270,360)]:
   th=np.degrees(np.arctan2(-(yy-3775.9775),xx-5375.7868))%360;m=(z>0)&(th>=a)&(th<b);result[f'sector{a}']=[float(np.corrcoef(tar[m],inp[m])[0,1]),float(np.corrcoef(tar[m],warped[m])[0,1])]
  results.append(result);np.save(O/f'ref09_registered_motion{motion}.npy',out);print(result,flush=True)
 except cv2.error as e:print(motion,str(e),flush=True)
(O/'registration09.json').write_text(json.dumps(results,indent=2))
