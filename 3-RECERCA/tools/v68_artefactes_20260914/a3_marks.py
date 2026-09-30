from pathlib import Path
import json,numpy as np,tifffile as tf
from scipy.ndimage import label,binary_dilation
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v68_artefactes_20260914';A=O/'arrays';V=O/'vistes';info=json.loads((O/'A1_layers.json').read_text());l=info['layers'][-1];x0,y0=l['bbox'][:2]
rgb=np.stack([np.load(A/f'A1_L205_C{c}.npy') for c in range(3)],-1);alpha=np.load(A/'A1_L205_C-1.npy');valid=alpha>10000
lab,n=label(binary_dilation(valid,iterations=4));rows=[]
for i in range(1,n+1):
 k=(lab==i)&valid
 if k.sum()<10:continue
 y,x=np.where(k);rows.append(dict(index=len(rows)+1,pixels=int(k.sum()),bbox=[int(x.min()+x0),int(y.min()+y0),int(x.max()+x0+1),int(y.max()+y0+1)],centre=[float(x.mean()+x0),float(y.mean()+y0)],median_RGB16=np.median(rgb[k],axis=0).tolist()))
(O/'A3_marks.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows),flush=True)
src=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));dst=ImageCms.createProfile('sRGB')
def view(a):
 a=a.astype(float)/65535
 if a.shape[-1]==4:a=a[...,:3]+.1*(1-a[...,3:])
 return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)),src,dst,outputMode='RGB')
for tag,scale in [('A2_marked_full',6),('A2_marked_ROI',1),('A2_clean_full',6),('A2_clean_ROI',1)]:
 f=O/(tag+'.tif')
 if not f.exists():continue
 a=tf.imread(f);im=view(a[::scale,::scale]);im.save(V/(tag+'.png'))
 if 'ROI' in tag:
  im=view(a);dr=ImageDraw.Draw(im)
  for r in rows:
   x1,y1,x2,y2=r['bbox'];b=[x1-4377-8,y1-2777-8,x2-4377+8,y2-2777+8];dr.rectangle(b,outline='cyan',width=2);dr.text((b[0],b[1]-15),str(r['index']),fill='cyan')
  im.save(V/(tag+'_numbered.png'))
