from pathlib import Path
import numpy as np,tifffile as tf,json
from scipy.ndimage import label,binary_dilation
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';A=O/'arrays';V=O/'vistes';src=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));dst=ImageCms.createProfile('sRGB')
def view(a):
 a=a.astype(float)/65535
 if a.shape[-1]==4:a=a[...,:3]+.1*(1-a[...,3:])
 return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)),src,dst,outputMode='RGB')
for tag,scale in [('A2_marked_full',6),('A2_marked_ROI',2)]:
 a=tf.imread(O/(tag+'.tif'));im=view(a[::scale,::scale]);im.save(V/(tag+'.png'))
rgb=np.stack([np.load(A/f'L97_C{c}.npy') for c in range(3)],-1);alpha=np.load(A/'L97_C-1.npy');valid=alpha>10000;cols=np.unique((rgb[valid]//4096),axis=0,return_counts=True);print('COLORS',sorted(zip(cols[0].tolist(),cols[1].tolist()),key=lambda x:-x[1])[:12]);
lab,n=label(binary_dilation(valid,iterations=4));rows=[]
for i in range(1,n+1):
 k=(lab==i)&valid
 if k.sum()<10:continue
 y,x=np.where(k);rows.append(dict(index=len(rows)+1,pixels=int(k.sum()),bbox=[int(x.min()+4377),int(y.min()+2777),int(x.max()+4378),int(y.max()+2778)],centre=[float(x.mean()+4377),float(y.mean()+2777)],median_RGB16=np.median(rgb[k],axis=0).tolist()))
(O/'A3_marks.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows),flush=True)
