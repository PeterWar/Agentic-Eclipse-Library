"""A32: compost provisional V71 de la ROI: filtres v70 + talons v70 + base v70 + capa 30 (màscara v70, RGB v71 vel) + interiors 76 de V69 (sense clau); vistes de la Lluna (×1) V69 | V71 sobre blanc."""
import sys, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
import compo; from compo import *
from PIL import Image, ImageCms, ImageDraw, ImageFont
compo.OVERRIDE.clear(); Cb,ab=recompon()
for lid in (47,49,51,53,55,56,3,41,42,45,46): compo.OVERRIDE[lid]=SP+f'/roi_L{lid}_v70.npz'
compo.OVERRIDE[30]=SP+'/roi_L30_v71.npz'; Ca,aa=recompon()
np.savez_compressed(SP+'/roi_compost_v71_prov.npz',C=(np.clip(Ca,0,1)*65535+.5).astype(np.uint16),a=(np.clip(aa,0,1)*65535+.5).astype(np.uint16))
src=ImageCms.ImageCmsProfile(SP+'/AdobeRGB.icc'); dst=ImageCms.createProfile('sRGB')
def srgb(arr): return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)),src,dst,outputMode='RGB')
def sobre_blanc(C,a): return C*a[...,None]+(1-a[...,None])
# Lluna 1100×1100 centrada, V69 | V71, més una versió aclarida ×3 (com faria Pere en pujar la Lluna) de les dues
x0,y0=int(998.88)-550,int(998.41)-550
try: f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',22)
except Exception: f=ImageFont.load_default()
pan=Image.new('RGB',(2*1110+10,2*1140+10),(20,20,22)); d=ImageDraw.Draw(pan)
for j,(C,a,nom) in enumerate([(Cb,ab,'V69'),(Ca,aa,'V71 provisional')]):
    im=srgb(sobre_blanc(C,a)[y0:y0+1100,x0:x0+1100]); pan.paste(im,(10+j*1110,10)); d.text((10+j*1110,1115),nom,fill=(230,230,225),font=f)
    im2=srgb(np.clip(sobre_blanc(C,a)[y0:y0+1100,x0:x0+1100]*3,0,1)); pan.paste(im2,(10+j*1110,1150)); d.text((10+j*1110,2255),nom+' · ×3 (Lluna aclarida)',fill=(230,230,225),font=f)
pan.save(SP+'/v_A32_lluna_v69_v71.png'); print('transparència ROI V71 prov: %d'%int((aa<0.998).sum())); print('fet')
