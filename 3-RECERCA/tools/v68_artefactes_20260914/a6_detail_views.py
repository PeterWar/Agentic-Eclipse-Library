from pathlib import Path
import json,numpy as np,tifffile as tf
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v68_artefactes_20260914';A=O/'arrays';V=O/'vistes';src=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));dst=ImageCms.createProfile('sRGB')
def view(a):return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)),src,dst,outputMode='RGB')
for k,bb in {'top':(5305,3275,5520,3370),'inside':(5170,3910,5470,4170),'SW':(4940,3980,5070,4100)}.items():
 for lid in [3,45,56,30,76,96]:
  ar=np.load(A/f'A5_c{lid}.npy');x0,y0,x1,y1=bb;q=ar[y0-2777:y1-2777,x0-4377:x1-4377,:3]
  if k=='inside':q*=4
  im=view(q);im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST).save(V/f'A6_{k}_c{lid}.png')
# independent annotation specks retained in inventory
from scipy.ndimage import label,binary_dilation
alpha=np.load(A/'A1_L205_C-1.npy');lab,n=label(binary_dilation(alpha>10000,iterations=4));rows=[]
for i in range(1,n+1):
 y,x=np.where((lab==i)&(alpha>10000));rows.append([i,len(y),[int(x.min()+4983),int(y.min()+3312),int(x.max()+4984),int(y.max()+3313)]])
print(rows)
