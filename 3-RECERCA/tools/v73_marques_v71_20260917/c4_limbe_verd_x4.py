"""C4: el limbe a ×4 al compost SENSE filtres (V71 de Pere i V72) a E, NE, N, S, SE, amb la saturació ×3 (Lab a*,b* ×3) perquè qualsevol tint verd/cian salti; i la mateixa finestra amb el compost complet."""
import sys, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; S3='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
sys.path.insert(0,NEW)
import compo71; from compo71 import *
from PIL import Image, ImageCms, ImageDraw, ImageFont
CX,CY,RS=998.88,998.41,456.0
src=ImageCms.ImageCmsProfile(NEW+'/AdobeRGB.icc'); dst=ImageCms.createProfile('sRGB'); lab=ImageCms.createProfile('LAB')
def srgb(arr): return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)),src,dst,outputMode='RGB')
def satur(pil,k=3.0):
    l=ImageCms.profileToProfile(pil,ImageCms.createProfile('sRGB'),lab,outputMode='LAB'); L,A,B=l.split(); A=np.asarray(A).astype(np.float32)-128; B=np.asarray(B).astype(np.float32)-128
    med_a,med_b=np.median(A),np.median(B); A=np.clip(med_a+(A-med_a)*k+128,0,255); B=np.clip(med_b+(B-med_b)*k+128,0,255)
    out=Image.merge('LAB',(L,Image.fromarray(np.uint8(A)),Image.fromarray(np.uint8(B)))); return ImageCms.profileToProfile(out,lab,ImageCms.createProfile('sRGB'),outputMode='RGB')
sb=lambda C,a: C*a[...,None]+(1-a[...,None])
variants={}
compo71.OVERRIDE.clear(); variants['V71 sense filtres']=recompon(exclou=(219,220,41,42,47,49,51,53,45,46,55,56))
for lid in (3,30,55,56,76,96,204): compo71.OVERRIDE[lid]=NEW+f'/roi72_L{lid}.npz'
variants['V72 sense filtres']=recompon(exclou=(219,220,41,42,47,49,51,53,45,46,55,56))
try: f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',16)
except Exception: f=ImageFont.load_default()
azs=(10,50,90,270,320); W=100; Z=4
pan=Image.new('RGB',(4*(W*Z+8)+8,len(azs)*(W*Z+26)+8),(20,20,22)); d=ImageDraw.Draw(pan)
for j,a0 in enumerate(azs):
    cx=CX+458*np.cos(np.deg2rad(a0)); cy=CY-458*np.sin(np.deg2rad(a0)); x0=int(cx-W//2); y0=int(cy-W//2); k=0
    for nom,(C,a) in variants.items():
        im=srgb(sb(C,a)[y0:y0+W,x0:x0+W]); pan.paste(im.resize((W*Z,W*Z),Image.Resampling.NEAREST),(8+k*(W*Z+8),8+j*(W*Z+26))); k+=1
        pan.paste(satur(im).resize((W*Z,W*Z),Image.Resampling.NEAREST),(8+k*(W*Z+8),8+j*(W*Z+26))); k+=1
    d.text((8,8+j*(W*Z+26)+W*Z+4),f'az {a0}° · V71 sense filtres | idem saturació ×3 | V72 sense filtres | idem saturació ×3',fill=(230,230,225),font=f)
pan.save(S3+'/v_C4_limbe_verd_x4.png'); print('fet')
