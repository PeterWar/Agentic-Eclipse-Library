from pathlib import Path
import json,numpy as np,tifffile as tf
from scipy.ndimage import label,find_objects
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v64_geometria_20260914';A=O/'arrays';V=O/'vistes';V.mkdir(exist_ok=True)
icc=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));srgb=ImageCms.createProfile('sRGB')
def view(a):
    a=a.astype('float32')/65535;rgb=a[...,:3]
    if a.shape[-1]==4:rgb=rgb+(1-a[...,3:])*.35
    return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(rgb,0,1)*255+.5)),icc,srgb,outputMode='RGB')
mark=np.stack([np.load(A/f'L87_C{c}.npy') for c in range(3)],-1).astype(float)/65535;alpha=np.load(A/'L87_C-1.npy')/65535
lab,n=label((alpha>.1)&(mark[...,1]>.3)&(mark[...,1]>mark[...,0]*1.4)&(mark[...,1]>mark[...,2]*1.2));marks=[]
for k,sl in enumerate(find_objects(lab),1):
    yy,xx=np.nonzero(lab[sl]==k)
    if len(xx)<4:continue
    xx+=sl[1].start+4377;yy+=sl[0].start+2777
    marks.append(dict(index=len(marks)+1,pixels=len(xx),bbox=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],centre=[float(xx.mean()),float(yy.mean())]))
(O/'A2_green_marks.json').write_text(json.dumps(marks,indent=2)+'\n');print(marks,flush=True)
view(tf.imread(O/'A0_marked.tif')).save(V/'A2_marked.png')
names=['A0_clean','A0_without_extra12','A0_no_interiors','A0_base_moon','A0_base_unmasked','A0_interiors_unmasked','A0_extra12_unmasked']
imgs={n:tf.imread(O/(n+'.tif')) for n in names}
for i,m in enumerate(marks):
    x0,y0,x1,y1=m['bbox'];x0-=16;y0-=18;x1+=16;y1+=18;k=4;w=(x1-x0)*k;h=(y1-y0)*k
    can=Image.new('RGB',(w*4,(h+25)*2));dr=ImageDraw.Draw(can)
    for j,n in enumerate(names):
        im=view(imgs[n][y0-2777:y1-2777,x0-4377:x1-4377]);px=j%4*w;py=j//4*(h+25);can.paste(im.resize((w,h),Image.Resampling.NEAREST),(px,py+25));dr.text((px+3,py+5),n,fill='white')
    can.save(V/f'A2_green_{i+1:02d}.png')
print('VIEWS COMPLETE',flush=True)
