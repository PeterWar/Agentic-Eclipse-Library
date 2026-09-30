"""Identify the Earthshine09 raster against all original interior layer subsets.
No fitting of radii or tone: exact registered RGB, original alpha and user masks.
Enumerate layer order/blending on deterministic coarse samples, then verify
the winning hypothesis at native resolution and export diagnostic views.
"""
from common50 import *
from itertools import permutations
from PIL import Image
layers={k:dict(np.load(OUT/f'L4_original_{k}.npz')) for k in ['12','11','10','09']};target=np.load(OUT/'L0_09_RGB16.npy').astype(float)
yy,xx=np.mgrid[:N,:N];r=np.hypot(xx-CX,yy-CY);sample=(slice(None,None,7),slice(None,None,7));t=target[sample];rr=r[sample];valid=(rr>430)&(rr<650)
def compose(order,mode,mask,full=False):
 size=(N,N) if full else t.shape[:2];col=np.zeros((*size,3));aa=np.zeros(size)
 for k in order:
  z=layers[k];rgb=z['rgb'].astype(float);w=z['alpha'].astype(float)/65535
  if mask:w*=z['mask'].astype(float)/65535
  if not full:rgb=rgb[sample];w=w[sample]
  v=rgb if mode=='normal' else np.maximum(col,rgb);col=col*(1-w[...,None])+v*w[...,None];aa=aa*(1-w)+w
 return col,aa
rows=[]
for count in range(1,5):
 for order in permutations(layers,count):
  for mode in ['normal','lighten']:
   for mask in [True,False]:
    col,aa=compose(order,mode,mask)
    for assoc in [True,False]:
     pred=col if assoc else col/np.maximum(aa[...,None],1/65535);delta=abs(pred-t)[valid]
     rows.append(dict(order=list(order),mode=mode,mask=mask,associated=assoc,mae=float(delta.mean()),p95=float(np.percentile(delta,95)),max=float(delta.max())))
rows.sort(key=lambda z:z['mae']);best=rows[0];pred,a=compose(best['order'],best['mode'],best['mask'],True)
if not best['associated']:pred/=np.maximum(a[...,None],1/65535)
np.save(OUT/'L5_best_composite.npy',np.rint(pred).astype(np.uint16));regions=[]
for lo,hi in [(0,350),(435,449),(449,454),(454,460),(460,480),(480,650)]:
 k=(r>=lo)&(r<hi);d=abs(pred-target)[k];regions.append(dict(radius=[lo,hi],mae=float(d.mean()),p95=float(np.percentile(d,95)),max=float(d.max()),current_median=np.median(target[k],axis=0).tolist(),pred_median=np.median(pred[k],axis=0).tolist()))
save('L5_composite_identification.json',dict(method=__doc__,best=best,regions=regions,top20=rows[:20]));print(json.dumps(dict(best=best,regions=regions,top10=rows[:10]),indent=2),flush=True)
ims=[Image.fromarray((np.clip(z,0,65535).astype(np.uint16)>>8).astype('uint8')) for z in [target,pred,layers['10']['rgb'],layers['09']['rgb']]]
for name,box in {'right':(1040,430,1220,940),'top':(370,170,990,365),'full':(0,0,N,N)}.items():
 crops=[im.crop(box) for im in ims];out=Image.new('RGB',(crops[0].width*len(crops),crops[0].height))
 for i,im in enumerate(crops):out.paste(im,(i*im.width,0))
 out.save(OUT/f'L5_{name}.png')
