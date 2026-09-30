from pathlib import Path
import numpy as np,json,tifffile as tf
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v68_artefactes_20260914';A=O/'arrays';V=O/'vistes';info=json.loads((O/'A1_layers.json').read_text());src=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));dst=ImageCms.createProfile('sRGB');versions={}
for version in ['old','colour','boundary','both']:
 c=np.zeros((2000,2000,3),np.float32);aa=np.zeros((2000,2000,1),np.float32)
 for l in info['layers']:
  id=l['id']
  if not l['visible'] or id in [202,205]:continue
  rgb=np.stack([np.load(A/f'L{id}_C{ch}.npy') for ch in range(3)],-1).astype(np.float32)/65535
  if id==3 and version in ['colour','both']:rgb=np.load(A/'B4_L3_colour.npy').astype('float32')/65535
  if id in [50,51,52,53] and version in ['boundary','both']:
   key={50:'01',51:'04',52:'05',53:'06'}[id];z=np.load(A/f'B5_{key}_candidate.npz');delta=z['delta'];rgb=np.clip(rgb+delta[...,None],0,1)
  al=np.load(A/f'L{id}_C-1.npy').astype(np.float32)[...,None]/65535
  if l.get('mask') and not l['mask']['disabled']:al*=np.load(A/f'L{id}_C-2.npy').astype(np.float32)[...,None]/65535
  al*=l['opacity']/255;blend=l['blend'].split('.')[-1]
  if blend=='NORMAL':b=rgb
  elif blend=='MULTIPLY':b=c*rgb
  elif blend=='HARD_LIGHT':b=np.where(rgb<=.5,2*c*rgb,1-2*(1-c)*(1-rgb))
  elif blend=='OVERLAY':b=np.where(c<=.5,2*c*rgb,1-2*(1-c)*(1-rgb))
  else:raise ValueError(blend)
  ao=al+aa*(1-al);c=np.divide(al*((1-aa)*rgb+aa*b)+(1-al)*aa*c,ao,out=np.zeros_like(c),where=ao>0);aa=ao
 versions[version]=c.copy();np.save(A/f'B7_{version}.npy',c)
for k,(x0,y0,x1,y1) in {'top':(5305,3275,5520,3370),'SW':(4940,3980,5070,4100),'east':(5760,3910,5840,4000),'whole':(4780,3180,5980,4380)}.items():
 scale=1 if k=='whole' else 3;ww=(x1-x0)*scale;hh=(y1-y0)*scale;pan=Image.new('RGB',(ww*2,(hh+30)*2),'#151515');dr=ImageDraw.Draw(pan)
 for j,(name,a) in enumerate(versions.items()):
  q=a[y0-2777:y1-2777,x0-4377:x1-4377];im=ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(q,0,1)*255+.5)),src,dst,outputMode='RGB');xx=(j%2)*ww;yy=(j//2)*(hh+30);pan.paste(im.resize((ww,hh),Image.Resampling.NEAREST),(xx,yy+30));dr.text((xx+7,yy+8),name,fill='white')
 pan.save(V/f'B7_{k}.png')
