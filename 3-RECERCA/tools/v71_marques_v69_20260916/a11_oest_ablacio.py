"""A11: ablacions al limbe oest (marques 2–6): què passa si (1) la base torna a ser opaca fora del disc lunar, (2) l'alfa lunar es retalla a la vora del forat +1,5 px, (3) totes dues, (4) sense fotos 76/96/204."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
import compo
from compo import *
from PIL import Image, ImageDraw, ImageFont, ImageCms
v=np.load(SP+'/a9_vores.npz'); TH=v['TH']; CX,CY=998.88,998.41
def per_theta(nom,sig=8):
    r=v[nom].copy(); ok=np.isfinite(r); r[~ok]=np.interp(np.nonzero(~ok)[0],np.nonzero(ok)[0],r[ok])
    k=np.exp(-0.5*(np.arange(-40,41)*0.25/ (sig*0.25))**2); k/=k.sum(); return np.convolve(np.r_[r[-40:],r,r[:40]],k,'valid')
R_hole=per_theta('alfa_base_(forat)'); R_sil=per_theta('silueta_perles_96'); R_esh=per_theta('alfa_earthshine')
yy,xx=np.mgrid[0:2000,0:2000]; rr=np.hypot(xx-CX,yy-CY); az=np.rad2deg(np.arctan2(-(yy-CY),xx-CX))%360; ia=np.clip((az/0.25).astype(int),0,len(TH)-1)
Rh=R_hole[ia]; Rs=R_sil[ia]
def smooth(x,w=2.0): return np.clip(0.5+x/w,0,1)   # rampa lineal de w px centrada
orig=compo.carrega
def variant(mode):
    def carrega_v(lid):
        rgb,a=orig(lid)
        if lid==3 and mode in ('base_opaca','totes'): a=np.maximum(a,smooth(rr-(Rs+2)))            # base opaca fora de la silueta fotogràfica +2 px
        if lid==30 and mode in ('alfa_retallada','totes'): a=a*(1-smooth(rr-(Rh+1.5)))               # alfa lunar acaba a forat+1,5 px (rampa 2 px)
        return rgb,a
    return carrega_v
sortides={}
for mode,ids in [('actual',None),('base_opaca',None),('alfa_retallada',None),('totes',None),('sense_fotos','nofotos')]:
    compo.carrega=variant(mode)
    if ids=='nofotos': C,a=recompon(exclou=(218,76,96,204,206))
    else: C,a=recompon()
    sortides[mode]=(C,a); print(mode,'píxels alfa<0,998 a la ROI:',int((a<0.998).sum()),' mín alfa %.3f'%a.min(),flush=True)
compo.carrega=orig
src=ImageCms.ImageCmsProfile(SP+'/AdobeRGB.icc'); dst=ImageCms.createProfile('sRGB')
def srgb(arr): return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)),src,dst,outputMode='RGB')
try: f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18)
except Exception: f=ImageFont.load_default()
for nomz,(x0,y0,w,h) in {'oest':(4880,3540,200,420),'NW':(4900,3450,200,200),'SSW_m8':(5100,4080,240,200),'dalt_m1':(5280,3240,260,140)}.items():
    Z=3 if h<=200 else 2; pan=Image.new('RGB',(len(sortides)*(w*Z+8)+8,h*Z+34),(20,20,22)); d=ImageDraw.Draw(pan)
    for j,(mode,(C,a)) in enumerate(sortides.items()):
        crop=C[y0-2777:y0-2777+h,x0-4377:x0-4377+w]*a[y0-2777:y0-2777+h,x0-4377:x0-4377+w,None]+(1-a[y0-2777:y0-2777+h,x0-4377:x0-4377+w,None])  # sobre blanc (com l'exportació)
        pan.paste(srgb(crop).resize((w*Z,h*Z),Image.Resampling.NEAREST),(8+j*(w*Z+8),8)); d.text((8+j*(w*Z+8),h*Z+12),mode,fill=(230,230,225),font=f)
    pan.save(SP+f'/v_A11_ablacio_{nomz}.png')
print('fet')
