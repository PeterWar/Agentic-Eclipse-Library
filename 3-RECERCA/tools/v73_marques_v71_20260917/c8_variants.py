"""C8: variants de la capa lunar per a V73 amb POWAAAH3 (57) OCULTA: A = contrast k=2,5 sense vora fosca; B = idem + vora fosca suau (0,35 a la vora, 4 px). Transició de color al limbe i panell ×4 saturat V72 | A | B."""
import sys, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; S3='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
sys.path.insert(0,NEW)
import compo71; from compo71 import *
from scipy.ndimage import gaussian_filter1d, map_coordinates
from PIL import Image, ImageCms, ImageDraw, ImageFont
CX,CY,RS=998.88,998.41,456.0; Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY); az=np.rad2deg(np.arctan2(-(Y-CY),X-CX))%360
d30=np.load(NEW+'/roi72_L30.npz'); rgb=np.dstack([d30['c0'],d30['c1'],d30['c2']]).astype(np.float64)/65535; cov=(d30['c-1'].astype(np.float64)/65535)*(d30['c-2'].astype(np.float64)/65535)
TH=np.deg2rad(np.arange(0,360,0.25)); RR=np.arange(430,480,0.25); xs=CX+RR[None,:]*np.cos(TH[:,None]); ys=CY-RR[None,:]*np.sin(TH[:,None])
P=map_coordinates(cov,[ys.ravel(),xs.ravel()],order=1).reshape(len(TH),len(RR)); Redge=np.full(len(TH),np.nan)
for i in range(len(TH)):
    j=np.nonzero(np.diff(np.sign(P[i]-0.5))!=0)[0]
    if len(j): k=j[-1]; Redge[i]=RR[k]+(0.5-P[i][k])/(P[i][k+1]-P[i][k]+1e-9)*0.25
ok=np.isfinite(Redge); Redge[~ok]=np.interp(np.nonzero(~ok)[0],np.nonzero(ok)[0],Redge[ok]); Redge=gaussian_filter1d(Redge,4,mode='wrap'); ia=np.clip((az/0.25).astype(int),0,len(TH)-1); din=Redge[ia]-rr
L=rgb.mean(-1); disc=rr<RS-6; rad=np.arange(0,470,1.0); prof=np.array([L[disc&(rr>=k)&(rr<k+2)].mean() if (disc&(rr>=k)&(rr<k+2)).sum()>10 else np.nan for k in rad]); okp=np.isfinite(prof); prof[~okp]=np.interp(rad[~okp],rad[okp],prof[okp]); prof=gaussian_filter1d(prof,6); m_pix=np.interp(rr,rad,prof)
kt=1+(2.5-1)*np.clip((440-rr)/40,0,1); gain=np.clip(np.where(L>1e-4,(m_pix+kt*(L-m_pix))/np.maximum(L,1e-4),1.0),0.05,6.0)
def capa(rim_min,rim_w):
    if rim_w>0: t=np.clip(din/rim_w,0,1); fosc=rim_min+(1-rim_min)*t*t*(3-2*t)
    else: fosc=np.ones_like(rr)
    new=np.clip(rgb*gain[...,None]*fosc[...,None],0,1); o={kk:d30[kk] for kk in d30.files}
    for c,key in enumerate(('c0','c1','c2')): o[key]=(new[...,c]*65535+.5).astype(np.uint16)
    return o
np.savez_compressed(S3+'/roi73A_L30.npz',**capa(1.0,0)); np.savez_compressed(S3+'/roi73B_L30.npz',**capa(0.35,4))
D=np.arange(-3,6,1.0)
def polar_d(F): xs2=CX+(Redge[:,None]+D[None,:])*np.cos(TH[:,None]); ys2=CY-(Redge[:,None]+D[None,:])*np.sin(TH[:,None]); return map_coordinates(F,[ys2.ravel(),xs2.ravel()],order=1).reshape(len(TH),len(D))
src=ImageCms.ImageCmsProfile(NEW+'/AdobeRGB.icc'); lab=ImageCms.createProfile('LAB'); srgbp=ImageCms.createProfile('sRGB')
def srgb(arr): return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)),src,srgbp,outputMode='RGB')
def satur(pil,k=3.0):
    l=ImageCms.profileToProfile(pil,srgbp,lab,outputMode='LAB'); Lc,A,B=l.split(); A=np.asarray(A).astype(np.float32)-128; B=np.asarray(B).astype(np.float32)-128; ma,mb=np.median(A),np.median(B)
    out=Image.merge('LAB',(Lc,Image.fromarray(np.uint8(np.clip(ma+(A-ma)*k+128,0,255))),Image.fromarray(np.uint8(np.clip(mb+(B-mb)*k+128,0,255))))); return ImageCms.profileToProfile(out,lab,srgbp,outputMode='RGB')
sb=lambda C,a: C*a[...,None]+(1-a[...,None])
comps={}
for nom,f30,ex in (('V72',NEW+'/roi72_L30.npz',(219,220,41,42,47,49,51,53,45,46,55,56)),('A: 57 oculta',S3+'/roi73A_L30.npz',(219,220,57,41,42,47,49,51,53,45,46,55,56)),('B: 57 oculta + vora',S3+'/roi73B_L30.npz',(219,220,57,41,42,47,49,51,53,45,46,55,56))):
    compo71.OVERRIDE.clear()
    for lid in (3,55,56,76,96,204): compo71.OVERRIDE[lid]=NEW+f'/roi72_L{lid}.npz'
    compo71.OVERRIDE[30]=f30; C,a=recompon(exclou=ex); comps[nom]=(C,a)
    bg=polar_d(C[...,2]/np.maximum(C[...,1],1e-4)); Lc=polar_d(C.mean(-1)); print(f'{nom:22s} B/G (d −3…+5): '+' '.join(f'{x:4.2f}' for x in np.median(bg,0))+' · L: '+' '.join(f'{x:4.2f}' for x in np.median(Lc,0)))
try: f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',16)
except Exception: f=ImageFont.load_default()
azs=(10,90,200,270); W=80; Z=4; pan=Image.new('RGB',(6*(W*Z+8)+8,len(azs)*(W*Z+26)+8),(20,20,22)); d=ImageDraw.Draw(pan)
for j,a0 in enumerate(azs):
    cx=CX+458*np.cos(np.deg2rad(a0)); cy=CY-458*np.sin(np.deg2rad(a0)); x0=int(cx-W//2); y0=int(cy-W//2); k=0
    for nom,(C,a) in comps.items():
        im=srgb(sb(C,a)[y0:y0+W,x0:x0+W]); pan.paste(im.resize((W*Z,W*Z),Image.Resampling.NEAREST),(8+k*(W*Z+8),8+j*(W*Z+26))); k+=1; pan.paste(satur(im).resize((W*Z,W*Z),Image.Resampling.NEAREST),(8+k*(W*Z+8),8+j*(W*Z+26))); k+=1
    d.text((8,8+j*(W*Z+26)+W*Z+4),f'az {a0}° · sense filtres: V72 | sat×3 | A (57 oculta) | sat×3 | B (57 oculta + vora fosca) | sat×3',fill=(230,230,225),font=f)
pan.save(S3+'/v_C8_variants_x4.png'); print('fet')
