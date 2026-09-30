"""Trace native Pere solar09 to current raster; fit tone outside reserved limb.
Diagnostic only: a smooth global mapping is not a substitute for the saved
render. The entire lunar boundary and alternate sectors remain held out.
"""
from common50 import *
from scipy.ndimage import map_coordinates
from scipy.optimize import isotonic_regression
from PIL import Image
j=json.loads((OUT/'L2_solar_raster_alignment.json').read_text());p=j['parameters'];sc=j['source_solar_center'];tc=np.array(j['target_solar_center'])+[4062-X0,2476-Y0]
an=np.deg2rad(p['angle_deg']);y,x=np.mgrid[:N,:N];dx=x-tc[0]-p['dx'];dy=y-tc[1]-p['dy'];xx=sc[0]+(np.cos(an)*dx+np.sin(an)*dy)/p['scale'];yy=sc[1]+(-np.sin(an)*dx+np.cos(an)*dy)/p['scale']
raw=np.load(j['source'],mmap_mode='r');source=np.stack([map_coordinates(raw[...,c].astype(float),[yy,xx],order=1,mode='nearest') for c in range(3)],-1)
current=np.load(OUT/'L0_09_RGB16.npy').astype(float);r=np.hypot(x-CX,y-CY);theta=np.arctan2(y-CY,x-CX)%(2*np.pi);sectors=(theta*12/np.pi).astype(int)
train=(r>500)&(r<640)&(sectors%2==0);pred=np.empty_like(source);fits=[]
for c in range(3):
 s=source[...,c][train];t=current[...,c][train];cuts=np.unique(np.quantile(s,np.linspace(0,1,129)));ind=np.digitize(s,cuts[1:-1]);sx=[];tx=[];w=[]
 for i in range(len(cuts)-1):
  k=ind==i
  if k.sum()>10:sx.append(float(np.median(s[k])));tx.append(float(np.median(t[k])));w.append(int(k.sum()))
 iso=isotonic_regression(tx,weights=w).x
 pred[...,c]=np.interp(source[...,c],sx,iso)
 fits.append(dict(source=sx,current=iso.tolist(),weight=w))
rows=[]
for lo,hi in [(0,350),(415,435),(435,449),(449,454),(454,460),(460,480),(480,500),(500,640)]:
 k=(r>=lo)&(r<hi)&(sectors%2==1);rows.append(dict(radius=[lo,hi],native_median=np.median(source[k],axis=0).tolist(),current_median=np.median(current[k],axis=0).tolist(),pred_median=np.median(pred[k],axis=0).tolist(),residual_median=np.median(current[k]-pred[k],axis=0).tolist(),abs_p95=np.percentile(abs(current[k]-pred[k]),95,axis=0).tolist()))
np.save(OUT/'L3_native_Pere09_registered_RGB16.npy',np.rint(source).astype(np.uint16));np.save(OUT/'L3_predicted09_RGB16.npy',np.rint(pred).astype(np.uint16));save('L3_solar_transfer.json',dict(method=__doc__,tone=fits,regions=rows))
def img(a):return Image.fromarray(np.rint(np.clip(a/257,0,255)).astype('uint8'))
a=img(current);b=img(source);c=img(pred)
for label,box in {'top':(370,170,990,365),'right':(1040,430,1220,940),'bottom':(400,1030,970,1230),'left':(165,420,365,960),'full':(0,0,N,N)}.items():
 aa=a.crop(box);bb=b.crop(box);cc=c.crop(box);out=Image.new('RGB',(aa.width*3,aa.height));out.paste(aa,(0,0));out.paste(bb,(aa.width,0));out.paste(cc,(aa.width*2,0));out.save(OUT/f'L3_{label}.png')
print(json.dumps(rows,indent=2),flush=True)
