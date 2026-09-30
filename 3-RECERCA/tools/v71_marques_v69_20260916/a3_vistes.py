"""A3: vistes de les marques de Pere sobre el compost V69 (ROI lunar), amb i sense la capa de marques (des-fusió on alfa<1)."""
import sys, json, numpy as np
from PIL import Image, ImageCms, ImageDraw, ImageFont
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
ROI=(4377,2777,6377,4777); x0,y0,x1,y1=ROI
C=np.load(SP+'/roi_compost.npz')['C'].astype(np.float32)/65535  # (2000,2000,4) RGB + alfa
m=np.load(SP+'/marques_218.npz'); A=m['A'].astype(np.float32)/65535; R=m['R'].astype(np.float32)/65535; G=m['G'].astype(np.float32)/65535; B=m['B'].astype(np.float32)/65535
mx,my=int(m['x0'])-x0,int(m['y0'])-y0
Afull=np.zeros((2000,2000),np.float32); Mfull=np.zeros((2000,2000,3),np.float32)
Afull[my:my+A.shape[0],mx:mx+A.shape[1]]=A; Mfull[my:my+A.shape[0],mx:mx+A.shape[1]]=np.dstack([R,G,B])
rgb=C[...,:3].copy()
# des-fusió NORMAL: C = a·M + (1−a)·U → U = (C − a·M)/(1−a) (on a<0,98)
a=Afull[...,None]; U=np.where(a<0.98,(rgb-a*Mfull)/np.clip(1-a,0.02,1),rgb); U=np.clip(U,0,1)
np.savez_compressed(SP+'/roi_compost_net.npz',U=(U*65535+.5).astype(np.uint16))
print('alfa max marques',Afull.max(),'píxels a>=0,98:',int((Afull>=0.98).sum()))
src=ImageCms.ImageCmsProfile(SP+'/AdobeRGB.icc'); dst=ImageCms.createProfile('sRGB')
def to_srgb(arr):
    return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)),src,dst,outputMode='RGB')
marques=json.load(open(SP+'/a1_marques.json'))
try: f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',28); f2=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18)
except Exception: f=f2=ImageFont.load_default()
# 1) ROI sencera amb marques i requadres numerats (a 1:1 → 2000 px)
im=to_srgb(rgb); d=ImageDraw.Draw(im)
for r in marques:
    bx0,by0,bx1,by1=r['bbox']; d.rectangle([bx0-x0-6,by0-y0-6,bx1-x0+6,by1-y0+6],outline=(0,255,255),width=2); d.text((bx0-x0-6,by0-y0-34),str(r['id']),fill=(0,255,255),font=f)
im.save(SP+'/v_A3_roi_marques.png')
to_srgb(U).save(SP+'/v_A3_roi_net.png')
# 2) zoom ×4 per marca: [compost amb marques | compost net | compost net amb estirament local ×3 al voltant del nivell]
S=160
pan=Image.new('RGB',(3*S*4+40,len(marques)*(S*4+44)+10),(20,20,22)); d=ImageDraw.Draw(pan)
for j,r in enumerate(marques):
    cx,cy=r['centre']; hx=max(S//2,(r['bbox'][2]-r['bbox'][0])//2+24); hy=max(S//2,(r['bbox'][3]-r['bbox'][1])//2+24); h=max(hx,hy); h=min(h,400)
    ax=int(np.clip(cx-x0-h,0,2000-2*h)); ay=int(np.clip(cy-y0-h,0,2000-2*h))
    crops=[rgb[ay:ay+2*h,ax:ax+2*h],U[ay:ay+2*h,ax:ax+2*h]]
    u=U[ay:ay+2*h,ax:ax+2*h]; lo=np.percentile(u,2); hi=np.percentile(u,98); crops.append(np.clip((u-lo)/(hi-lo+1e-6),0,1))
    for k,c in enumerate(crops):
        im=to_srgb(c).resize((S*4,S*4),Image.Resampling.LANCZOS); pan.paste(im,(10+k*(S*4+10),10+j*(S*4+44)))
    d.text((10,10+j*(S*4+44)+S*4+4),f"marca {r['id']} rgb8={r['rgb8']} n={r['n']} centre=({cx:.0f},{cy:.0f}) finestra {2*h}px · esq: amb marques · mig: net · dreta: net estirat p2–p98",fill=(230,230,225),font=f2)
pan.save(SP+'/v_A3_marques_zoom.png'); print('vistes fetes')
