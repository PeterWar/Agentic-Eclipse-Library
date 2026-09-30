from pathlib import Path
import json,numpy as np,cv2
R=Path.cwd();O=R/'output/v64_geometria_20260914';P=R/'output/v61_interiors_limbe_20260913';A=O/'arrays'
yy,xx=np.ogrid[2777:4777,4377:6377];r=np.hypot(xx-5376.568111973117,yy-3776.647534140857);inner=(r>410)&(r<430)
conf=[];rows=[]
for i in [0,1,2]:
    g=np.load(P/'arrays'/f'V57_L{i:02d}_C1.npy').astype(float)/65535
    med=np.median(g[inner]);sig=np.median(abs(g[inner]-med))*1.4826
    sig=max(sig,1/65535);c=np.clip((g-med-3*sig)/(3*sig),0,1);conf.append(c)
    rows.append(dict(layer=12-i,black_background=med,robust_sigma=sig,method='Measured black interior; smooth 3-to-6 sigma support. Only gates new opacity increase, never removes old foreground.'))
# Require corroborating signal in at least two of the three shortest photos.
c=np.sort(conf,axis=0)[1]
M=np.array(json.loads((P/'C3_rigid_controls.json').read_text())['matrix_global']);M[:,2]+=M[:,:2]@np.array([4377,2777])-np.array([4377,2777]);c=cv2.warpAffine(c,M,(2000,2000),flags=cv2.INTER_LINEAR)
np.save(A/'B5_support.npy',c);(O/'B5_support.json').write_text(json.dumps(dict(photos=rows,scope='Support for a diagnostic opacity increase only; no original pixels or alpha removed'),indent=2)+'\n');print(rows,flush=True)
