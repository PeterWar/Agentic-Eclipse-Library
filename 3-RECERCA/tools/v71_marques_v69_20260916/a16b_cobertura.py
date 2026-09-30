"""A16b: cobertura afinada: (1) capa lunar: màscara 1 dins; cobertura retallada a silueta+0,5 (50 %); (2) base opaca des d'1,5 px DINS de la vora lunar (50 %) cap enfora → cap píxel transparent;
(3) NRGF/RHEF: omplir el 'taló' de les màscares (0,9→1 en 14 px) fora del forat sense tocar les seleccions de Pere (sectors on la màscara a d 2–6 és < 0,7 del nivell)."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
import compo; from compo import *
from scipy.ndimage import map_coordinates, gaussian_filter1d
CX,CY,RS=998.88,998.41,456.0
yy,xx=np.mgrid[0:2000,0:2000]; rr=np.hypot(xx-CX,yy-CY); az=np.rad2deg(np.arctan2(-(yy-CY),xx-CX))%360
TH=np.deg2rad(np.arange(0,360,0.25)); ia=np.clip((az/0.25).astype(int),0,len(TH)-1)
def ss(x,w=2.0): return np.clip(0.5+x/w,0,1)
def vora50(cov):
    RR=np.arange(430,480,0.25); xs=CX+RR[None,:]*np.cos(TH[:,None]); ys=CY-RR[None,:]*np.sin(TH[:,None])
    P=map_coordinates(cov,[ys.ravel(),xs.ravel()],order=1).reshape(len(TH),len(RR)); out=np.full(len(TH),np.nan)
    for i in range(len(TH)):
        j=np.nonzero(np.diff(np.sign(P[i]-0.5))!=0)[0]
        if len(j): k=j[-1] if P[i][0]>0.5 else j[0]; out[i]=RR[k]+(0.5-P[i][k])/(P[i][k+1]-P[i][k]+1e-9)*0.25
    ok=np.isfinite(out); out[~ok]=np.interp(np.nonzero(~ok)[0],np.nonzero(ok)[0],out[ok]); return out
# (1) capa lunar
d30=np.load(SP+'/roi_L30.npz'); A30=d30['c-1'].astype(np.float32)/65535; M30=d30['c-2'].astype(np.float32)/65535
M30n=np.where((A30>=0.999)&(rr<RS-3),1.0,M30); M30n=M30n*(1-ss(rr-(RS+0.5)))
cov=A30*M30n; Redge=vora50(cov); Redge_s=gaussian_filter1d(Redge,4,mode='wrap')
print('vora lunar 50 %% nova: mín %.1f màx %.1f (mediana %.1f)'%(Redge.min(),Redge.max(),np.median(Redge)))
out={k:d30[k] for k in d30.files}; out['c-2']=(np.clip(M30n,0,1)*65535+.5).astype(np.uint16); np.savez_compressed(SP+'/roi_L30_v70.npz',**out)
print('capa 30: màscara canviada en %d px'%int((np.abs(M30n-M30)>1/65535).sum()))
# (2) base opaca des de la vora lunar −1,5 px cap enfora (rampa 2 px: 0 a −3,5, 1 a −1,5)
d3=np.load(SP+'/roi_L3.npz'); M3=d3['c-2'].astype(np.float32)/65535; dl=rr-Redge_s[ia]; M3n=np.maximum(M3,ss(dl+2.5))
out={k:d3[k] for k in d3.files}; out['c-2']=(np.clip(M3n,0,1)*65535+.5).astype(np.uint16); np.savez_compressed(SP+'/roi_L3_v70.npz',**out)
print('base 3: màscara pujada en %d px (màx +%.3f); píxels amb r > vora lunar+2 encara < 0,999: %d'%(int((M3n-M3>1/65535).sum()),float((M3n-M3).max()),int(((dl>2)&(M3n<0.999)).sum())))
# (3) taló de les màscares NRGF/RHEF
v=np.load(SP+'/a9_vores.npz'); r=v['alfa_base_(forat)'].copy(); ok=np.isfinite(r); r[~ok]=np.interp(np.nonzero(~ok)[0],np.nonzero(ok)[0],r[ok]); R_hole=gaussian_filter1d(r,8,mode='wrap'); dh=rr-R_hole[ia]
for lid in (41,42,45,46):
    dd=np.load(SP+f'/roi_L{lid}.npz'); M=dd['c-2'].astype(np.float32)/65535
    # nivell de referència per θ: mediana de la màscara a d 14–24; sectors de selecció (màscara a d 2–6 < 0,7·ref) queden intactes
    D=np.arange(0,25,0.5); xs=CX+(R_hole[:,None]+D[None,:])*np.cos(TH[:,None]); ys=CY-(R_hole[:,None]+D[None,:])*np.sin(TH[:,None])
    P=map_coordinates(M,[ys.ravel(),xs.ravel()],order=1).reshape(len(TH),len(D)); ref=np.median(P[:,(D>=14)&(D<=24)],1); prop=np.median(P[:,(D>=2)&(D<=6)],1)
    talo=(prop>=0.7*ref)&(prop<0.995*ref); talo_s=gaussian_filter1d(talo.astype(float),4,mode='wrap')>0.5
    ref_pix=ref[ia]; ok_pix=talo_s[ia]&(dh>=0)&(dh<=24)
    Mn=M.copy(); Mn[ok_pix]=np.maximum(M[ok_pix],ref_pix[ok_pix]*ss(dh[ok_pix]-1.5))
    print(f'capa {lid}: sectors amb taló (graus): {round(float(talo_s.mean()*360))}°; píxels pujats {int((Mn-M>1/65535).sum())}, màx +{float((Mn-M).max()):.3f}')
    out={k:dd[k] for k in dd.files}; out['c-2']=(np.clip(Mn,0,1)*65535+.5).astype(np.uint16); np.savez_compressed(SP+f'/roi_L{lid}_v70.npz',**out)
# compost
def compon(v70):
    compo.OVERRIDE.clear()
    if v70:
        for lid in (47,49,51,53,55,56,30,3,41,42,45,46): compo.OVERRIDE[lid]=SP+f'/roi_L{lid}_v70.npz'
    return recompon()
Cb,ab=compon(False); Ca,aa=compon(True)
print('transparència (alfa<0,998) ROI: abans %d → després %d; alfa mín %.4f → %.4f'%(int((ab<0.998).sum()),int((aa<0.998).sum()),ab.min(),aa.min()))
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
print('índex de vora ABANS  :',idx(Cb)); print('índex de vora DESPRÉS:',idx(Ca))
dif=np.abs(Ca-Cb).max(-1)*65535; far=(rr<400)|(rr>520); print('canvi màxim fora de r 400–520: %.1f DN16'%dif[far].max())
np.savez_compressed(SP+'/roi_compost_v70.npz',C=(np.clip(Ca,0,1)*65535+.5).astype(np.uint16),a=(np.clip(aa,0,1)*65535+.5).astype(np.uint16))
# perfils m8 i m1: compost abans/després vs base
for kk in ('m8 SSW','m1 dalt','m3-4 W'):
    a0,a1=sectors[kk]; pb=perfil(Cb.mean(-1),a0,a1); pa=perfil(Ca.mean(-1),a0,a1); compo.OVERRIDE.clear(); B,_=recompon(ids=[3]); pB=perfil(B.mean(-1),a0,a1)
    print(kk,' r: '+' '.join(f'{x:5.0f}' for x in RR[::8]))
    print('   abans  : '+' '.join(f'{x:5.3f}' for x in pb[::8])); print('   després: '+' '.join(f'{x:5.3f}' for x in pa[::8])); print('   base   : '+' '.join(f'{x:5.3f}' for x in pB[::8]))
