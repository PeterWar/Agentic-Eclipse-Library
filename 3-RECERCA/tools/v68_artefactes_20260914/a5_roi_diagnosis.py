from pathlib import Path
import numpy as np,json,tifffile as tf
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v68_artefactes_20260914';A=O/'arrays';V=O/'vistes';info=json.loads((O/'A1_layers.json').read_text());src=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));dst=ImageCms.createProfile('sRGB')
def view(a):
 if a.shape[-1]==4:a=a[...,:3]+.1*(1-a[...,3:])
 return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)),src,dst,outputMode='RGB')
regs={'top':(5305,3275,5520,3370),'inside':(5170,3910,5470,4170),'SW':(4940,3980,5070,4100),'east':(5760,3910,5840,4000)}
c=np.zeros((2000,2000,3),np.float32);aa=np.zeros((2000,2000,1),np.float32);records=[]
for l in info['layers']:
 id=l['id']
 if not l['visible'] or id in [202,205]:continue
 rgb=np.stack([np.load(A/f'L{id}_C{ch}.npy') for ch in range(3)],-1).astype(np.float32)/65535;al=np.load(A/f'L{id}_C-1.npy').astype(np.float32)[...,None]/65535
 if l.get('mask') and not l['mask']['disabled']:al*=np.load(A/f'L{id}_C-2.npy').astype(np.float32)[...,None]/65535
 al*=l['opacity']/255;blend=l['blend'].split('.')[-1]
 if blend=='NORMAL':b=rgb
 elif blend=='MULTIPLY':b=c*rgb
 elif blend=='HARD_LIGHT':b=np.where(rgb<=.5,2*c*rgb,1-2*(1-c)*(1-rgb))
 elif blend=='OVERLAY':b=np.where(c<=.5,2*c*rgb,1-2*(1-c)*(1-rgb))
 else:raise ValueError(blend)
 ao=al+aa*(1-al);c=np.divide(al*((1-aa)*rgb+aa*b)+(1-al)*aa*c,ao,out=np.zeros_like(c),where=ao>0);aa=ao
 if id in [3,45,56,30,76,96]:
  q=np.concatenate([c,aa],-1);np.save(A/f'A5_c{id}.npy',q)
  for k,(x0,y0,x1,y1) in regs.items():
   v=view(q[y0-2777:y1-2777,x0-4377:x1-4377]);v.resize((v.width*3,v.height*3),Image.Resampling.NEAREST).save(V/f'A5_{k}_c{id}.png')
 if id in [3,30,76,96]:
  for k,(x0,y0,x1,y1) in regs.items():
   sy=slice(y0-2777,y1-2777);sx=slice(x0-4377,x1-4377);ar=al[sy,sx];rr=rgb[sy,sx]
   records.append(dict(id=id,region=k,alpha_percentiles=np.percentile(ar,[0,10,50,90,100]).tolist()))
   im=view(rr);im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST).save(V/f'A5_{k}_L{id}_RGB.png');Image.fromarray(np.uint8(ar[...,0]*255+.5)).resize((im.width*3,im.height*3),Image.Resampling.NEAREST).save(V/f'A5_{k}_L{id}_alpha.png')
(O/'A5_alpha.json').write_text(json.dumps(records,indent=2)+'\n');print(records)
