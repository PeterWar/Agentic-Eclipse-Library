"""A16: cures de cobertura (màscara lunar opaca dins del disc; base opaca fora de la silueta; alfa lunar retallada a silueta+1,5) + filtres corregits → compost V70 de la ROI; verificació i vistes abans/després."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
import compo; from compo import *
from scipy.ndimage import map_coordinates
from PIL import Image, ImageDraw, ImageFont, ImageCms
CX,CY,RS=998.88,998.41,456.0   # silueta fotogràfica (perles 96)
yy,xx=np.mgrid[0:2000,0:2000]; rr=np.hypot(xx-CX,yy-CY)
def ss(x,w=2.0): return np.clip(0.5+x/w,0,1)   # rampa lineal d'amplada w centrada a 0
# 1) capa lunar (30): màscara := 1 dins (r < RS−3) on l'alfa geomètrica ja és 1; cobertura retallada a RS+1,5 (rampa 2 px) via la màscara
d30=np.load(SP+'/roi_L30.npz'); A30=d30['c-1'].astype(np.float32)/65535; M30=d30['c-2'].astype(np.float32)/65535
M30n=np.where((A30>=0.999)&(rr<RS-3),np.maximum(M30,1.0),M30); M30n=M30n*(1-ss(rr-(RS+0.5)))
out={k:d30[k] for k in d30.files}; out['c-2']=(np.clip(M30n,0,1)*65535+.5).astype(np.uint16); np.savez_compressed(SP+'/roi_L30_v70.npz',**out)
print('capa 30: màscara canviada en %d px (dins: %d, retall exterior: %d)'%(int((np.abs(M30n-M30)>1/65535).sum()),int(((M30n>M30)&(np.abs(M30n-M30)>1/65535)).sum()),int(((M30n<M30)&(np.abs(M30n-M30)>1/65535)).sum())))
# 2) base (3): màscara := max(màscara, opaca fora de RS+1) (rampa 2 px)
d3=np.load(SP+'/roi_L3.npz'); M3=d3['c-2'].astype(np.float32)/65535; M3n=np.maximum(M3,ss(rr-(RS+1)))
out={k:d3[k] for k in d3.files}; out['c-2']=(np.clip(M3n,0,1)*65535+.5).astype(np.uint16); np.savez_compressed(SP+'/roi_L3_v70.npz',**out)
print('base 3: màscara pujada en %d px (màx +%.3f)'%(int((M3n-M3>1/65535).sum()),float((M3n-M3).max())))
# 3) compost abans / després
def compon(v70):
    compo.OVERRIDE.clear()
    if v70:
        for lid in (47,49,51,53,55,56,30,3): compo.OVERRIDE[lid]=SP+f'/roi_L{lid}_v70.npz'
    return recompon()
Cb,ab=compon(False); Ca,aa=compon(True)
print('transparència (alfa<0,998) ROI: abans %d, després %d; alfa mín %.4f → %.4f'%(int((ab<0.998).sum()),int((aa<0.998).sum()),ab.min(),aa.min()))
RR=np.arange(440,480,0.25)
def perfil(img,az0,az1):
    th=np.deg2rad(np.arange(az0,az1,0.25)); xs=CX+RR[None,:]*np.cos(th[:,None]); ys=CY-RR[None,:]*np.sin(th[:,None])
    return np.median(map_coordinates(img,[ys.ravel(),xs.ravel()],order=1,mode='nearest').reshape(len(th),len(RR)),0)
sectors={'m1 dalt':(76,100),'m2 NW':(148,158),'m3-4 W':(163,173),'m5 Weq':(177,181),'m6 WSW':(189,199),'m8 SSW':(240,254),'ctrl E':(-10,10),'ctrl S':(260,280),'ctrl NE':(40,60)}
def idx(C):
    L=C.mean(-1); out={}
    for kk,(a0,a1) in sectors.items():
        p=perfil(L,a0,a1); out[kk]=round(float(p[(RR>=452)&(RR<=458)].max()/p[(RR>=464)&(RR<=470)].mean()-1),3)
    return out
print('índex de vora (pic 452–458 / 464–470 − 1) compost complet ABANS  :',idx(Cb)); print('índex de vora compost complet DESPRÉS:',idx(Ca))
# diferència fora de la banda del limbe: ha de ser 0
dif=np.abs(Ca-Cb).max(-1)*65535; far=(rr<400)|(rr>520); print('canvi màxim fora de r 400–520: %.1f DN16; dins la banda: p50 %.1f p99 %.0f màx %.0f'%(dif[far].max(),np.median(dif[~far]),np.percentile(dif[~far],99),dif[~far].max()))
np.savez_compressed(SP+'/roi_compost_v70.npz',C=(np.clip(Ca,0,1)*65535+.5).astype(np.uint16),a=(np.clip(aa,0,1)*65535+.5).astype(np.uint16))
# vistes abans/després (sobre blanc) per marca
src=ImageCms.ImageCmsProfile(SP+'/AdobeRGB.icc'); dst=ImageCms.createProfile('sRGB')
def srgb(arr): return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)),src,dst,outputMode='RGB')
marques=json.load(open(SP+'/a1_marques.json'))
try: f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18)
except Exception: f=ImageFont.load_default()
S=180; Z=3; pan=Image.new('RGB',(3*(S*Z+8)+8,7*(S*Z+30)+8),(20,20,22)); d=ImageDraw.Draw(pan); j=0
for q in marques:
    if q['id']==7: continue
    cx,cy=q['centre']; ax=int(np.clip(cx-4377-S//2,0,2000-S)); ay=int(np.clip(cy-2777-S//2,0,2000-S))
    for k,(C,a) in enumerate([(Cb,ab),(Ca,aa)]):
        crop=C[ay:ay+S,ax:ax+S]*a[ay:ay+S,ax:ax+S,None]+(1-a[ay:ay+S,ax:ax+S,None]); pan.paste(srgb(crop).resize((S*Z,S*Z),Image.Resampling.NEAREST),(8+k*(S*Z+8),8+j*(S*Z+30)))
    u=Ca[ay:ay+S,ax:ax+S]; lo,hi=np.percentile(u,2),np.percentile(u,98); pan.paste(srgb(np.clip((u-lo)/(hi-lo+1e-6),0,1)).resize((S*Z,S*Z),Image.Resampling.NEAREST),(8+2*(S*Z+8),8+j*(S*Z+30)))
    d.text((8,8+j*(S*Z+30)+S*Z+6),f"marca {q['id']} · esq: V69 · mig: V70 (cobertura + filtres) · dreta: V70 estirat",fill=(230,230,225),font=f); j+=1
pan.save(SP+'/v_A16_abans_despres.png'); print('fet')
