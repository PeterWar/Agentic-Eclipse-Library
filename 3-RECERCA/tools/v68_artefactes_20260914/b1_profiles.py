from pathlib import Path
import numpy as np,json,tifffile as tf
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v68_artefactes_20260914';A=O/'arrays';V=O/'vistes'
ids=[3,41,42,45,47,49,51,52,53,56,30,76,96]
info={x['id']:x for x in json.loads((O/'A1_layers.json').read_text())['layers']}
# Local native cumulative states compared identically, no independent stretch.
regions={'top':(5305,3275,5520,3370),'SW':(4940,3980,5070,4100),'inside':(5170,3910,5470,4170)}
src=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));dst=ImageCms.createProfile('sRGB')
for key,(x0,y0,x1,y1) in regions.items():
 panel=Image.new('RGB',((x1-x0)*3*3,(y1-y0)*3*2+60),'#202020');d=ImageDraw.Draw(panel)
 for k in range(6):
  a=tf.imread(O/f'A2_c0{k}.tif')[y0-2777:y1-2777,x0-4377:x1-4377,:3].astype(float)/65535
  if key=='inside':a*=4
  im=ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)),src,dst,outputMode='RGB').resize(((x1-x0)*3,(y1-y0)*3),Image.Resampling.NEAREST)
  xx=(k%3)*(x1-x0)*3;yy=(k//3)*((y1-y0)*3+30);panel.paste(im,(xx,yy+30));d.text((xx+8,yy+8),['Base','+ NRGF/RHEF','+ ACHF/WOW','+ Earthshine','+ Interiors','+ Perles'][k],fill='white')
 panel.save(V/f'B1_{key}_native_sequence.png')
rows=[]
for y in range(3311,3335):
 x=5410;q={'xy':[x,y]};sx=x-4377;sy=y-2777
 for id in ids:
  alpha=np.load(A/f'L{id}_C-1.npy',mmap_mode='r')[sy,sx]/65535;mask=np.load(A/f'L{id}_C-2.npy',mmap_mode='r')[sy,sx]/65535;g=np.load(A/f'L{id}_C1.npy',mmap_mode='r')[sy,sx]/65535;q[str(id)]=[round(float(alpha*mask*info[id]['opacity']/255),4),round(float(g),4)]
 rows.append(q)
(O/'B1_profiles.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
