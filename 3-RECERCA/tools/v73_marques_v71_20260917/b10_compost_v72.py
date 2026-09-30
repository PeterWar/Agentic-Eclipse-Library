"""B10: compost V72 de la ROI (V71 de Pere + capes 3/30/55/56/76/96/204 corregides, marques ocultes): dentat, anell de color, taca, ploma de les fotos, transparència; vistes abans/després."""
import sys, json, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
sys.path.insert(0,NEW)
import compo71; from compo71 import *
from scipy.ndimage import map_coordinates, gaussian_filter1d, gaussian_filter
from PIL import Image, ImageCms, ImageDraw, ImageFont
CX,CY,RS=998.88,998.41,456.0; Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY); az=np.rad2deg(np.arctan2(-(Y-CY),X-CX))%360
TH=np.deg2rad(np.arange(0,360,0.25)); RR=np.arange(430,480,0.25); xs=CX+RR[None,:]*np.cos(TH[:,None]); ys=CY-RR[None,:]*np.sin(TH[:,None])
compo71.OVERRIDE.clear(); Cb,ab=recompon(exclou=(219,220)); Sb,_=recompon(exclou=(219,220,41,42,47,49,51,53,45,46,55,56))
for lid in (3,30,55,56,76,96,204): compo71.OVERRIDE[lid]=NEW+f'/roi72_L{lid}.npz'
Ca,aa=recompon(exclou=(219,220)); Sa,_=recompon(exclou=(219,220,41,42,47,49,51,53,45,46,55,56))
np.savez_compressed(NEW+'/roi72_compost.npz',C=(np.clip(Ca,0,1)*65535+.5).astype(np.uint16),a=(np.clip(aa,0,1)*65535+.5).astype(np.uint16))
def vora(C,a):
    L=(C*a[...,None]).mean(-1); P=map_coordinates(L,[ys.ravel(),xs.ravel()],order=1).reshape(len(TH),len(RR)); lo=np.median(P[:,RR<440],1); hi=np.median(P[:,RR>470],1); mid=(lo+hi)/2; out=np.full(len(TH),np.nan)
    for i in range(len(TH)):
        j=np.nonzero(np.diff(np.sign(P[i]-mid[i]))!=0)[0]
        if len(j): k=j[0]; out[i]=RR[k]+(mid[i]-P[i][k])/(P[i][k+1]-P[i][k]+1e-9)*0.25
    ok=np.isfinite(out); out[~ok]=np.interp(np.nonzero(~ok)[0],np.nonzero(ok)[0],out[ok]); return out
for nom,(C,a) in (('V71 Pere',(Cb,ab)),('V72',(Ca,aa))):
    e=vora(C,a); hp=e-gaussian_filter1d(e,4,mode='wrap'); sec=(np.rad2deg(TH)//10).astype(int); s=[float(np.std(hp[sec==k])) for k in range(36)]
    print(f'{nom}: dentat global {np.std(hp):.3f} · 60–120: {np.mean(s[6:12]):.3f} · 270–300: {np.mean(s[27:30]):.3f} · 150–210: {np.mean(s[15:21]):.3f}')
print('transparència ROI: V71 %d → V72 %d'%(int((ab<0.998).sum()),int((aa<0.998).sum())))
# anell de color al compost sense filtres: excés B/G a d 3–30 vs 40–70 per sector (abans/després)
v=np.load(OLD+'/a9_vores.npz'); r=v['alfa_base_(forat)'].copy(); ok=np.isfinite(r); r[~ok]=np.interp(np.nonzero(~ok)[0],np.nonzero(ok)[0],r[ok]); R_hole=gaussian_filter1d(r,8,mode='wrap')
D=np.arange(0,80,1.0)
def polar(F): xs2=CX+(R_hole[:,None]+D[None,:])*np.cos(TH[:,None]); ys2=CY-(R_hole[:,None]+D[None,:])*np.sin(TH[:,None]); return map_coordinates(F,[ys2.ravel(),xs2.ravel()],order=1).reshape(len(TH),len(D))
print('excés B/G (%) del compost sense filtres a d 3–30 respecte de d 40–70, sectors de 30°: abans → després')
for S_,tag in ((Sb,'abans'),(Sa,'després')):
    bg=polar(S_[...,2]/np.maximum(S_[...,1],1e-4)); row=[]
    for s in range(0,360,30):
        k=(np.rad2deg(TH)>=s)&(np.rad2deg(TH)<s+30); m=np.nanmedian(bg[k],0); row.append(100*(np.median(m[(D>=3)&(D<=30)])/np.median(m[(D>=40)&(D<=70)])-1))
    print(f'  {tag:8s}: '+' '.join(f'{x:+5.1f}' for x in row))
# taca 219.7 i ploma de les fotos (219.2–6): quocient amb/sense fotos a r 465–490 al W
m7=np.load(NEW+'/marques_219.npz'); Mk=np.zeros((2000,2000),np.float32); mx,my=int(m7['x0'])-4377,int(m7['y0'])-2777; Mk[my:my+m7['A'].shape[0],mx:mx+m7['A'].shape[1]]=m7['A']/65535
R7=np.zeros((2000,2000),bool); R7[3928-2777:4132-2777,5187-4377:5418-4377]=Mk[3928-2777:4132-2777,5187-4377:5418-4377]>0.03
yb,xb=np.nonzero(R7); rb=np.hypot(xb-CX,yb-CY); anell=(rr>=rb.min()-10)&(rr<=rb.max()+10)&(~R7)&(rr<RS-8)
for nom,C in (('V71 Pere',Cb),('V72',Ca)):
    Lc=C.mean(-1); Ls=gaussian_filter(Lc,8); print(f'taca 219.7 {nom}: mitjana {100*(1-Lc[R7].mean()/Lc[anell].mean()):+.1f} % sota l\'anell · mín σ8 {100*(1-Ls[R7].min()/Lc[anell].mean()):+.1f} %')
Csf,_=recompon(exclou=(219,220,76,96,204,206)); 
def perfil(img,a0,a1):
    th=np.deg2rad(np.arange(a0,a1,0.25)); RR2=np.arange(455,495,5.0); xs3=CX+RR2[None,:]*np.cos(th[:,None]); ys3=CY-RR2[None,:]*np.sin(th[:,None]); return np.median(map_coordinates(img,[ys3.ravel(),xs3.ravel()],order=1,mode='nearest').reshape(len(th),len(RR2)),0)
for kk,(a0,a1) in {'219.2 (az 148–158)':(148,158),'219.4 (az 163–173)':(163,173),'219.6 (az 189–199)':(189,199)}.items():
    print(f'{kk}: quocient amb/sense fotos r 455..490: V72 '+' '.join(f'{x:5.3f}' for x in perfil(Ca.mean(-1),a0,a1)/np.maximum(perfil(Csf.mean(-1),a0,a1),1e-6)))
# vistes: marques 219 (×3) abans/després i anell 220 az 30/90/300; Lluna ×3
src=ImageCms.ImageCmsProfile(NEW+'/AdobeRGB.icc'); dst=ImageCms.createProfile('sRGB')
def srgb(arr): return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)),src,dst,outputMode='RGB')
sb=lambda C,a: C*a[...,None]+(1-a[...,None])
marks=json.load(open(NEW+'/b1_marques.json'))
try: f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',18)
except Exception: f=ImageFont.load_default()
fin=[(f"219.{r['id']}",r['centre'][0]-4377,r['centre'][1]-2777) for r in marks['219']]+[(f'220 az {a0}',CX+475*np.cos(np.deg2rad(a0)),CY-475*np.sin(np.deg2rad(a0))) for a0 in (30,90,300)]
W=200; Z=3; pan=Image.new('RGB',(4*(W*Z+8)+8,len(fin)*(W*Z+30)+8),(20,20,22)); d=ImageDraw.Draw(pan)
for j,(nom,cx,cy) in enumerate(fin):
    x0=int(np.clip(cx-W//2,0,2000-W)); y0=int(np.clip(cy-W//2,0,2000-W))
    ims=[srgb(sb(Cb,ab)[y0:y0+W,x0:x0+W]),srgb(sb(Ca,aa)[y0:y0+W,x0:x0+W]),srgb(sb(Sb,ab)[y0:y0+W,x0:x0+W]),srgb(sb(Sa,aa)[y0:y0+W,x0:x0+W])]
    for k,im in enumerate(ims): pan.paste(im.resize((W*Z,W*Z),Image.Resampling.NEAREST),(8+k*(W*Z+8),8+j*(W*Z+30)))
    d.text((8,8+j*(W*Z+30)+W*Z+4),f'{nom} · V71 Pere | V72 | sense filtres V71 | sense filtres V72',fill=(230,230,225),font=f)
pan.save(NEW+'/v_B10_marques_abans_despres.png')
x0,y0=int(CX)-550,int(CY)-550; pan=Image.new('RGB',(2*1110+10,2*1140+10),(20,20,22)); d=ImageDraw.Draw(pan)
for j,(C,a,nom) in enumerate([(Cb,ab,'V71 Pere'),(Ca,aa,'V72')]):
    pan.paste(srgb(sb(C,a)[y0:y0+1100,x0:x0+1100]),(10+j*1110,10)); d.text((10+j*1110,1115),nom,fill=(230,230,225),font=f)
    pan.paste(srgb(np.clip(sb(C,a)[y0:y0+1100,x0:x0+1100]*3,0,1)),(10+j*1110,1150)); d.text((10+j*1110,2255),nom+' · ×3',fill=(230,230,225),font=f)
pan.save(NEW+'/v_B10_lluna_v71_v72.png'); print('fet')
