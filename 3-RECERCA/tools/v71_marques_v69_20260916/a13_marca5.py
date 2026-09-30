"""A13: la marca 5 (línia lila vertical a x 4913–4915, y 3770–3800) capa per capa a ×8."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
from PIL import Image, ImageDraw, ImageFont, ImageCms
Rr=np.load(SP+'/roi_recomp.npz'); Cr=Rr['C'].astype(np.float32)/65535; ar=Rr['a'].astype(np.float32)/65535
m=np.load(SP+'/marques_218.npz'); M=np.zeros((2000,2000),np.float32); mx,my=int(m['x0'])-4377,int(m['y0'])-2777; M[my:my+m['A'].shape[0],mx:mx+m['A'].shape[1]]=m['A']/65535
x0,y0,w,h=4885-4377,3750-2777,60,70; Z=8
src=ImageCms.ImageCmsProfile(SP+'/AdobeRGB.icc'); dst=ImageCms.createProfile('sRGB')
def srgb(arr): return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)),src,dst,outputMode='RGB')
def grey(arr): return Image.fromarray(np.uint8(np.clip(arr,0,1)*255)).convert('RGB')
pans=[('compost (sobre blanc)',srgb((Cr*ar[...,None]+(1-ar[...,None]))[y0:y0+h,x0:x0+w])),('marca 5 (alfa)',grey(M[y0:y0+h,x0:x0+w]*2))]
for lid,nom in [(3,'base'),(30,'earthshine'),(76,'interiors 76'),(96,'perles 96'),(204,'perles 204'),(202,'estrelles 202'),(41,'NRGF 41'),(51,'ACHF 51'),(56,'WOW 56')]:
    rgb,a=carrega(lid); pans.append((nom+' RGB',srgb(rgb[y0:y0+h,x0:x0+w]))); pans.append((nom+' alfa·màsc·op',grey(a[y0:y0+h,x0:x0+w])))
try: f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',14)
except Exception: f=ImageFont.load_default()
cols=5; rows=(len(pans)+cols-1)//cols; pan=Image.new('RGB',(cols*(w*Z+8)+8,rows*(h*Z+30)+8),(20,20,22)); d=ImageDraw.Draw(pan)
for j,(nom,im) in enumerate(pans):
    X=8+(j%cols)*(w*Z+8); Y=8+(j//cols)*(h*Z+30); pan.paste(im.resize((w*Z,h*Z),Image.Resampling.NEAREST),(X,Y)); d.text((X,Y+h*Z+6),nom,fill=(230,230,225),font=f)
    # contorn de la marca 5 en lila
    yy,xx=np.nonzero(M[y0:y0+h,x0:x0+w]>0.02)
    for yq,xq in zip(yy,xx): d.rectangle([X+xq*Z,Y+yq*Z,X+xq*Z+Z-1,Y+yq*Z+Z-1],outline=(255,0,255))
pan.save(SP+'/v_A13_marca5_capes.png'); print('fet',len(pans))
