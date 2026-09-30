from pathlib import Path
import numpy as np,json,tifffile as tf
from PIL import Image,ImageCms,ImageDraw
R=Path.cwd();O=R/'output/v64_geometria_20260914';A=O/'arrays';V=O/'vistes'
def rd(n):return tf.imread(O/(n+'.tif')).astype(float)/65535
so=rd('A0_interiors_unmasked');background=rd('A0_no_interiors')[...,:3];extra=rd('A0_extra12_masked');clean=rd('A0_clean')[...,:3];mask=np.load(A/'L76_C-2.npy')/65535
alpha=so[...,3];rgb=so[...,:3]/np.maximum(alpha[...,None],1e-8);new=np.clip(np.maximum(alpha,np.load(A/'B3_alpha_probe.npy')),0,1);new[alpha<=0]=0
def compose(a):
    a=a*mask;out=rgb*a[...,None]+background*(1-a[...,None]);return extra[...,:3]+out*(1-extra[...,3:])
cand=rd('D1_candidate_with83')[...,:3]
icc=ImageCms.ImageCmsProfile(str(O/'AdobeRGB.icc'));srgb=ImageCms.createProfile('sRGB')
def view(a):return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)),icc,srgb,outputMode='RGB')
for q in json.loads((O/'A2_green_marks.json').read_text()):
    x0,y0,x1,y1=q['bbox'];x0-=16;y0-=18;x1+=16;y1+=18;k=6;w=(x1-x0)*k;h=(y1-y0)*k;can=Image.new('RGB',(w*2,h+24));dr=ImageDraw.Draw(can)
    for j,(name,b) in enumerate([('V63 Pere',clean),('Native V64 candidate',cand)]):can.paste(view(b[y0-2777:y1-2777,x0-4377:x1-4377]).resize((w,h),Image.Resampling.NEAREST),(j*w,24));dr.text((j*w+3,5),name,fill='white')
    can.save(V/f'D2_mark_{q["index"]:02d}.png')
