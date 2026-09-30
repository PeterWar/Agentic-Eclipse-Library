from pathlib import Path
import json,numpy as np,cv2
O=Path('/private/tmp/v105_base_sources_20260926');D=Path('/private/tmp/eclipse_v104_diagnosi_20260926')
src=np.load(O/'09_original_CapesInteriors_RGB.npy',mmap_mode='r');ox,oy=2764,1475;s=src[oy:oy+1600,ox:ox+1600,1].astype(float)/65535
a=np.load(D/'L303.npz');t=a['c1'][77:1477,77:1477].astype(float)/65535
ys,xs=np.mgrid[:1600,:1600];yt,xt=np.mgrid[:1400,:1400]
ms=((np.hypot(xs-(3563.891-ox),ys-(2274.660-oy))>475)&(np.hypot(xs-(3563.891-ox),ys-(2274.660-oy))<650)).astype('uint8')*255
mt=((np.hypot(xt-(5375.7868-4677),yt-(3775.9775-3077))>478)&(np.hypot(xt-(5375.7868-4677),yt-(3775.9775-3077))<605)).astype('uint8')*255
theta=np.degrees(np.arctan2(-(yt-(3775.7475-3077)),xt-(5361.7681-4677)))%360
mt[(((theta//30).astype(int)%2)!=0)|((theta%30)<5)|((theta%30)>25)]=0
def prep(x):
 l=np.log(np.maximum(x,1e-6));u=np.clip((l+3.5)/3.5*255,0,255).astype('uint8');return cv2.createCLAHE(clipLimit=2,tileGridSize=(20,20)).apply(u)
sift=cv2.SIFT_create(nfeatures=5000,contrastThreshold=.005,edgeThreshold=20)
ks,ds=sift.detectAndCompute(prep(s),ms);kt,dt=sift.detectAndCompute(prep(t),mt)
print('features',len(ks),len(kt),flush=True)
matches=cv2.BFMatcher().knnMatch(ds,dt,k=2);good=[m for m,n in matches if m.distance<.80*n.distance];ss=np.float32([ks[m.queryIdx].pt for m in good]);tt=np.float32([kt[m.trainIdx].pt for m in good]);print('matches',len(good),flush=True)
M,inliers=cv2.estimateAffinePartial2D(ss,tt,method=cv2.RANSAC,ransacReprojThreshold=2,maxIters=10000,confidence=.999);print('M',M,'inliers',sum(inliers),flush=True)
if M is not None:
 H=np.eye(3);H[:2]=M;H[:2,2]+=[4677,3077];HI=np.linalg.inv(H);A=HI[:2,:2];sourcecenter=np.array([3563.891-ox,2274.660-oy]);targetcenter=np.array([5361.768111973117,3775.747534140857]);offset=A@targetcenter+HI[:2,2]-sourcecenter;p=[*offset,np.degrees(np.arctan2(A[1,0],A[0,0])),np.sqrt(np.linalg.det(A))]
 print('p',p,flush=True);(O/'SIFT_seed.json').write_text(json.dumps({'matrix_sourcecrop_to_target_canvas':H.tolist(),'sampling_parameters':p,'n_matches':len(good),'n_inliers':int(sum(inliers)[0]),'matches_source_xy':ss.tolist(),'matches_target_xy':tt.tolist(),'inlier':inliers.flatten().tolist()},indent=2))
