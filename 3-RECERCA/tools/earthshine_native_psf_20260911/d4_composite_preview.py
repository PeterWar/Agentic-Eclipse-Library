"""Expected same-mask V48 composite with the source interpolation delta.
No modified layer, mask, source registration or visible alternative state.
Uses an actual native V48 export; publication still requires Photoshop readback.
"""
from full_delta_common import *
from PIL import Image
new=np.load(OUT/'C3_candidate_rgb.npy').astype(int);old=np.load(SRC/'C3_candidate_rgb.npy').astype(int);baseline=np.load(PREV/'C1_native_composition_roi.npz')['baseline'].astype(float)
mask=np.load(SRC/'C4_inherited_mask_roi.npy').astype(float)/65535
candidate=baseline+(new-old)*mask[...,None]
assert candidate.min()>=0 and candidate.max()<=65535
candidate=np.rint(candidate).astype(np.uint16);np.save(OUT/'C4_expected_moon.npy',candidate)
vis=OUT/'vistes';vis.mkdir(exist_ok=True);Image.fromarray((candidate>>8).astype(np.uint8)).save(vis/'C4_candidate_composite.png')
for title,box in [('top',(550,200,850,350)),('right',(1075,540,1220,855)),('bottom_right',(935,935,1105,1105))]:
    x1,y1,x2,y2=box;pair=np.concatenate([baseline[y1:y2,x1:x2].astype(np.uint16),candidate[y1:y2,x1:x2]],axis=0 if title!='right' else 1);im=Image.fromarray((pair>>8).astype(np.uint8));im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST).save(vis/f'C4_{title}_before_after_x3.png')
yy,xx=np.mgrid[:N,:N];r=np.hypot(xx-CX,yy-CY);d=candidate.astype(int)-baseline.astype(int);ch=(d-d[...,1,None]);rows=[]
for lo,hi in [(0,350),(350,420),(420,435),(435,449),(449,454),(454,460),(460,480)]:
    w=(r>=lo)&(r<hi);rows.append(dict(radius=[lo,hi],median_delta_DN16=float(np.median(d[w])),percentiles_delta_DN16=np.percentile(d[w],[0,1,5,50,95,99,100]).tolist(),median_luminance_ratio=float(np.median(candidate[w].mean(-1)/np.maximum(baseline[w].mean(-1),1)))))
prom=(baseline[...,0]-baseline[...,1])>1000
save('C4_composite_preview.json',dict(method=__doc__,regions=rows,chroma_max_DN16=int(abs(ch).max()),prominence_chroma_max_DN16=int(abs(ch[prom]).max()),zero_mask_max_DN16=int(abs(d[mask==0]).max()),photo_status='Expected composition only, not native Photoshop gate'))
print(json.dumps(rows),flush=True)
