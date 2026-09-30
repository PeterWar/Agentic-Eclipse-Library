from pathlib import Path
import numpy as np,tifffile as tf,json,ast
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';A=O/'arrays';V=O/'vistes';mks=json.loads((O/'A3_marks.json').read_text());icc=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));srgb=ImageCms.createProfile('sRGB')
def view(a):return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)),icc,srgb,outputMode='RGB')
raw={id:np.stack([np.load(A/f'L{id}_C{c}.npy') for c in range(3)],-1)/65535 for id in [3,30,76,96]};alphas={id:np.load(A/f'L{id}_C-1.npy')/65535*np.load(A/f'L{id}_C-2.npy')/65535 for id in [3,30,76,96]};m=mks[1];x0,y0,x1,y1=5255,3295,5310,3360;sl=np.s_[y0-2777:y1-2777,x0-4377:x1-4377];panel=Image.new('RGB',(55*8*4,65*8+24));draw=ImageDraw.Draw(panel)
for j,id in enumerate(raw):
 a=raw[id][sl];panel.paste(view(a).resize((55*8,65*8),Image.Resampling.NEAREST),(j*55*8,24));draw.text((j*55*8+4,4),f'RGB without masks L{id}',fill='white')
panel.save(V/'B2_orange_unmasked.png')
rows=[]
for m in mks:
 x0,y0,x1,y1=m['bbox'];sl=np.s_[y0-2777:y1-2777,x0-4377:x1-4377];q=dict(mark=m['index'],layers={})
 for id in raw:
  a=raw[id][sl];al=alphas[id][sl];q['layers'][id]=dict(RGB_median=np.median(a,axis=(0,1)).tolist(),alpha_quantiles=np.percentile(al,[0,25,50,75,100]).tolist(),R_clip_fraction=float(np.mean(a[...,0]>=.999)))
 rows.append(q)
(O/'B2_causal_values.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
