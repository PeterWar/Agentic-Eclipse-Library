from pathlib import Path
import numpy as np,json,tifffile as tf,cv2
from scipy.ndimage import map_coordinates
R=Path.cwd();O=R/'output/v64_geometria_20260914';P=R/'output/v61_interiors_limbe_20260913';A=O/'arrays'
meta=json.loads((P/'A0_sources.json').read_text())['V57']['layers'];W=np.zeros((2000,2000),float);S=np.zeros((2000,2000,3),float)
for i in range(7):
    l=meta[i]
    if not l['visible']:continue
    alpha=np.load(P/'arrays'/f'V57_L{i:02d}_C-1.npy').astype(float)/65535
    if not l['mask_flags']['mask_disabled']:alpha*=np.load(P/'arrays'/f'V57_L{i:02d}_C-2.npy').astype(float)/65535
    alpha*=l['opacity']/255
    rgb=np.stack([np.load(P/'arrays'/f'V57_L{i:02d}_C{c}.npy') for c in range(3)],-1).astype(float)/65535
    # psd-tools indices are bottom-to-top: retain previous recomposition order.
    S+=alpha[...,None]*(rgb-S);W+=alpha*(1-W)
native=tf.imread(P/'V61_interiors_only.tif')[...,:3].astype(float)/65535
delta=abs(S-native)*65535
N=native/np.maximum(W[...,None],1e-8);N[W==0]=0
M=np.array(json.loads((P/'C3_rigid_controls.json').read_text())['matrix_global']);M[:,2]+=M[:,:2]@np.array([4377,2777])-np.array([4377,2777])
def warp(a):return cv2.warpAffine(a,M,(2000,2000),flags=cv2.INTER_CUBIC)
w=warp(W);n=warp(N);np.save(A/'B2_photo_weight.npy',w);np.save(A/'B2_normalized_photo.npy',n);np.save(A/'B2_original_weight.npy',W)
marks=json.loads((O/'A2_green_marks.json').read_text());rep=[]
for q in marks:
    x,y=q['centre'];cx,cy=5376.568111973117,3776.647534140857;theta=np.arctan2(y-cy,x-cx);rr=np.arange(445,468,.25);xx=cx+np.cos(theta)*rr;yy=cy+np.sin(theta)*rr
    out={'mark':q['index']}
    for name,field in [('weight',w),('old_G',warp(native[...,1])),('normalized_G',n[...,1])]:out[name]=np.round(map_coordinates(field,[yy-2777,xx-4377],order=1)[::4],6).tolist()
    rep.append(out)
(O/'B2_weight_coverage.json').write_text(json.dumps(dict(original_reconstruction_DN16_quantiles=np.quantile(delta,[.5,.99,.999,1]).tolist(),profile_radii=list(range(445,468)),marks=rep,method='Diagnostic normalization by aggregate photographic layer weight. No output promoted; original weights are not physical alpha.'),indent=2)+'\n')
print('RECON',np.quantile(delta,[.5,.99,.999,1]));print(json.dumps(rep),flush=True)
