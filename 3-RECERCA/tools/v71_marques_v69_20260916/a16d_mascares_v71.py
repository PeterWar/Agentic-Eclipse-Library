"""A16d (V71): màscares sense tocar la vora de Pere. Capa 30: només el pinzell al 99 % de l'interior (píxels amb 0,98<M<1 i mínim 7×7 > 0,95, r<440) → 1; cap retall exterior.
Base 3: opaca des d'1,5 px dins de la vora lunar de V69 (50 %) cap enfora. Compost provisional V71 i índex de dentat (std del passa-alt azimutal de la vora) V69 vs V71."""
import sys, json, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
import compo; from compo import *
from scipy.ndimage import minimum_filter, map_coordinates, gaussian_filter1d
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
CX,CY,RS=998.88,998.41,456.0; Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY); az=np.rad2deg(np.arctan2(-(Y-CY),X-CX))%360
TH=np.deg2rad(np.arange(0,360,0.25)); ia=np.clip((az/0.25).astype(int),0,len(TH)-1)
def ss(x,w=2.0): return np.clip(0.5+x/w,0,1)
# capa 30
d30=np.load(SP+'/roi_L30.npz'); A30=d30['c-1'].astype(np.float32)/65535; M30=d30['c-2'].astype(np.float32)/65535
interior=(M30>0.98)&(M30<1.0)&(minimum_filter(M30,7)>0.95)&(rr<440)
M30n=M30.copy(); M30n[interior]=1.0
print('capa 30: píxels de màscara pujats a 1 (interior, lluny de la vora): %d; cap altre canvi; màx r afectat %.0f'%(int(interior.sum()),rr[interior].max() if interior.any() else 0))
v71=np.load(SP+'/roi_L30_v71.npz'); out={k:v71[k] for k in v71.files}; out['c-2']=(np.clip(M30n,0,1)*65535+.5).astype(np.uint16); np.savez_compressed(SP+'/roi_L30_v71.npz',**out)
# vora lunar de V69 (50 % de la cobertura alfa×màscara) per θ
cov=A30*M30
RR=np.arange(430,480,0.25); xs=CX+RR[None,:]*np.cos(TH[:,None]); ys=CY-RR[None,:]*np.sin(TH[:,None]); P=map_coordinates(cov,[ys.ravel(),xs.ravel()],order=1).reshape(len(TH),len(RR)); Redge=np.full(len(TH),np.nan)
for i in range(len(TH)):
    j=np.nonzero(np.diff(np.sign(P[i]-0.5))!=0)[0]
    if len(j): k=j[-1]; Redge[i]=RR[k]+(0.5-P[i][k])/(P[i][k+1]-P[i][k]+1e-9)*0.25
ok=np.isfinite(Redge); Redge[~ok]=np.interp(np.nonzero(~ok)[0],np.nonzero(ok)[0],Redge[ok]); Redge_s=gaussian_filter1d(Redge,4,mode='wrap')
d3=np.load(SP+'/roi_L3.npz'); M3=d3['c-2'].astype(np.float32)/65535; dl=rr-Redge_s[ia]; M3n=np.maximum(M3,ss(dl+2.5))
out3={k:d3[k] for k in d3.files}; out3['c-2']=(np.clip(M3n,0,1)*65535+.5).astype(np.uint16); np.savez_compressed(SP+'/roi_L3_v71.npz',**out3)
print('base 3: màscara pujada en %d px (vora lunar de V69: mín %.1f màx %.1f)'%(int((M3n-M3>1/65535).sum()),Redge.min(),Redge.max()))
# compost V69 i V71 provisional
compo.OVERRIDE.clear(); Cb,ab=recompon()
for lid in (47,49,51,53,55,56,41,42,45,46): compo.OVERRIDE[lid]=SP+f'/roi_L{lid}_v70.npz'
compo.OVERRIDE[3]=SP+'/roi_L3_v71.npz'; compo.OVERRIDE[30]=SP+'/roi_L30_v71.npz'; Ca,aa=recompon()
print('transparència (alfa<0,998) ROI: V69 %d → V71 %d; alfa mín %.4f → %.4f'%(int((ab<0.998).sum()),int((aa<0.998).sum()),ab.min(),aa.min()))
np.savez_compressed(SP+'/roi_compost_v71.npz',C=(np.clip(Ca,0,1)*65535+.5).astype(np.uint16),a=(np.clip(aa,0,1)*65535+.5).astype(np.uint16))
# índex de dentat (mètode de l'agent): vora 50 % de la lluminància de C·a, passa-alt azimutal σ 1° (4 mostres), std per sector
def vora(C,a):
    L=(C*a[...,None]).mean(-1); P=map_coordinates(L,[ys.ravel(),xs.ravel()],order=1).reshape(len(TH),len(RR)); lo=np.median(P[:,RR<440],1); hi=np.median(P[:,RR>470],1); mid=(lo+hi)/2; out=np.full(len(TH),np.nan)
    for i in range(len(TH)):
        j=np.nonzero(np.diff(np.sign(P[i]-mid[i]))!=0)[0]
        if len(j): k=j[0]; out[i]=RR[k]+(mid[i]-P[i][k])/(P[i][k+1]-P[i][k]+1e-9)*0.25
    ok=np.isfinite(out); out[~ok]=np.interp(np.nonzero(~ok)[0],np.nonzero(ok)[0],out[ok]); return out
v70=np.load(SP+'/roi_compost_v70.npz')
res={}
for nom,(C,a) in (('V69',(Cb,ab)),('V70',(v70['C'].astype(np.float32)/65535,v70['a'].astype(np.float32)/65535)),('V71',(Ca,aa))):
    e=vora(C,a); hp=e-gaussian_filter1d(e,4,mode='wrap'); sec=(np.rad2deg(TH)//10).astype(int); res[nom]=[float(np.std(hp[sec==s])) for s in range(36)]
    print(f'{nom}: dentat global {np.std(hp):.3f} px · sectors 60–120: {np.mean(res[nom][6:12]):.3f} · 270–300: {np.mean(res[nom][27:30]):.3f} · 150–210: {np.mean(res[nom][15:21]):.3f}')
json.dump(res,open(SP+'/a16d_dentat.json','w'),indent=1)
# vistes ×8 a 90°, 250°, 300°, 170°: V69 | V70 | V71
from PIL import Image, ImageCms, ImageDraw, ImageFont
src=ImageCms.ImageCmsProfile(SP+'/AdobeRGB.icc'); dst=ImageCms.createProfile('sRGB')
def srgb(arr): return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)),src,dst,outputMode='RGB')
try: f=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',16)
except Exception: f=ImageFont.load_default()
W=80; Z=8; azs=(90,170,250,300); pan=Image.new('RGB',(3*(W*Z+8)+8,len(azs)*(W*Z+28)+8),(20,20,22)); d=ImageDraw.Draw(pan)
for j,a0 in enumerate(azs):
    cx=CX+454.5*np.cos(np.deg2rad(a0)); cy=CY-454.5*np.sin(np.deg2rad(a0)); x0=int(cx-W//2); y0=int(cy-W//2)
    for k,(C,a) in enumerate([(Cb,ab),(v70['C'].astype(np.float32)/65535,v70['a'].astype(np.float32)/65535),(Ca,aa)]):
        crop=(C*a[...,None]+(1-a[...,None]))[y0:y0+W,x0:x0+W]; pan.paste(srgb(crop).resize((W*Z,W*Z),Image.Resampling.NEAREST),(8+k*(W*Z+8),8+j*(W*Z+28)))
    d.text((8,8+j*(W*Z+28)+W*Z+4),f'az {a0}° · V69 | V70 | V71',fill=(230,230,225),font=f)
pan.save(SP+'/v_A16d_dentat_v69_v70_v71.png'); print('fet')
