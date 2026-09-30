"""A24: la foto d'interiors (76) només contribueix on aporta senyal (protuberàncies, perles, cromosfera): clau K a partir de l'excés de lluminància o de vermell respecte del compost de sota; alfa := alfa × K fora del disc. RGB de la foto intacte."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
import compo; from compo import *
from scipy.ndimage import gaussian_filter, map_coordinates
from PIL import Image, ImageDraw, ImageFont, ImageCms
CX,CY,RS=998.88,998.41,456.0; yy,xx=np.mgrid[0:2000,0:2000]; rr=np.hypot(xx-CX,yy-CY)
for lid in (47,49,51,53,55,56,30,3,41,42,45,46): compo.OVERRIDE[lid]=SP+f'/roi_L{lid}_v70.npz'
Cs,as_=recompon(exclou=(218,76,96,204,206,202))          # compost de sota de la 76
rgb76,a76=carrega(76); d76=np.load(SP+'/roi_L76.npz'); A=d76['c-1'].astype(np.float32)/65535; M=d76['c-2'].astype(np.float32)/65535
Ls=Cs.mean(-1); L76=rgb76.mean(-1)
E_lum=(gaussian_filter(L76,1.5)-gaussian_filter(Ls,1.5))/np.maximum(gaussian_filter(Ls,1.5),0.02)
rg76=gaussian_filter(rgb76[...,0],1.5)/np.maximum(gaussian_filter(rgb76[...,1],1.5),1e-3); rgs=gaussian_filter(Cs[...,0],1.5)/np.maximum(gaussian_filter(Cs[...,1],1.5),1e-3); E_red=rg76-rgs
def sst(x,a,b): t=np.clip((x-a)/(b-a),0,1); return t*t*(3-2*t)
K=np.maximum(sst(E_lum,-0.04,0.08),sst(E_red,0.05,0.20)); K=gaussian_filter(K,3.0); K=np.where(rr<RS-2,1.0,K)   # dins del disc: intacte
Mn=M*K   # apliquem la clau a la màscara (la selecció de Pere és el sostre)
out={k:d76[k] for k in d76.files}; out['c-2']=(np.clip(Mn,0,1)*65535+.5).astype(np.uint16); np.savez_compressed(SP+'/roi_L76_v70.npz',**out)
ch=(np.abs(Mn-M)>1/65535)&(A*M>0.02); print('capa 76: màscara reduïda en %d px (mitjana de K on hi ha alfa: %.3f); píxels amb alfa efectiva > 0,1 abans %d → després %d'%(int(ch.sum()),float(K[A*M>0.02].mean()),int((A*M*(227/255)>0.1).sum()),int((A*Mn*(227/255)>0.1).sum())))
compo.OVERRIDE[76]=SP+'/roi_L76_v70.npz'; Ca,aa=recompon()
RR=np.arange(440,520,0.25)
def perfil(img,az0,az1):
    th=np.deg2rad(np.arange(az0,az1,0.25)); xs=CX+RR[None,:]*np.cos(th[:,None]); ys=CY-RR[None,:]*np.sin(th[:,None])
    return np.median(map_coordinates(img,[ys.ravel(),xs.ravel()],order=1,mode='nearest').reshape(len(th),len(RR)),0)
Cs2,_=recompon(exclou=(218,76,96,204,206))
for kk,(a0,a1) in {'m2 NW':(148,158),'m3-4 W':(163,173),'m5 Weq':(177,181),'m6 WSW':(189,199)}.items():
    q=perfil(Ca.mean(-1),a0,a1)/np.maximum(perfil(Cs2.mean(-1),a0,a1),1e-6); print(f'{kk}: quocient amb/sense fotos (V70) a r 455..490 pas 5: '+' '.join(f'{x:5.3f}' for x in q[(RR>=455)&(RR<=490)][::20]))
print('transparència ROI (alfa<0,998): %d'%int((aa<0.998).sum()))
np.savez_compressed(SP+'/roi_compost_v70.npz',C=(np.clip(Ca,0,1)*65535+.5).astype(np.uint16),a=(np.clip(aa,0,1)*65535+.5).astype(np.uint16))
# panell: V69 | V70 (tot) per marques 2–6 a ×3 i el mapa K
compo.OVERRIDE.clear(); Cb,ab=recompon()
src=ImageCms.ImageCmsProfile(SP+'/AdobeRGB.icc'); dst=ImageCms.createProfile('sRGB')
def srgb(arr): return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)),src,dst,outputMode='RGB')
marques=json.load(open(SP+'/a1_marques.json'))
try: f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18)
except Exception: f=ImageFont.load_default()
S=180; Z=3; sel=[q for q in marques if q['id']!=7]; pan=Image.new('RGB',(4*(S*Z+8)+8,len(sel)*(S*Z+30)+8),(20,20,22)); d=ImageDraw.Draw(pan)
for j,q in enumerate(sel):
    cx,cy=q['centre']; ax=int(np.clip(cx-4377-S//2,0,2000-S)); ay=int(np.clip(cy-2777-S//2,0,2000-S))
    for k,(C,a) in enumerate([(Cb,ab),(Ca,aa)]):
        crop=C[ay:ay+S,ax:ax+S]*a[ay:ay+S,ax:ax+S,None]+(1-a[ay:ay+S,ax:ax+S,None]); pan.paste(srgb(crop).resize((S*Z,S*Z),Image.Resampling.NEAREST),(8+k*(S*Z+8),8+j*(S*Z+30)))
    u=Ca[ay:ay+S,ax:ax+S]; lo,hi=np.percentile(u,2),np.percentile(u,98); pan.paste(srgb(np.clip((u-lo)/(hi-lo+1e-6),0,1)).resize((S*Z,S*Z),Image.Resampling.NEAREST),(8+2*(S*Z+8),8+j*(S*Z+30)))
    pan.paste(Image.fromarray(np.uint8((A*Mn)[ay:ay+S,ax:ax+S]*255)).convert('RGB').resize((S*Z,S*Z),Image.Resampling.NEAREST),(8+3*(S*Z+8),8+j*(S*Z+30)))
    d.text((8,8+j*(S*Z+30)+S*Z+6),f"marca {q['id']} · V69 · V70 · V70 estirat · alfa 76 nova",fill=(230,230,225),font=f)
pan.save(SP+'/v_A24_abans_despres.png'); print('fet')
