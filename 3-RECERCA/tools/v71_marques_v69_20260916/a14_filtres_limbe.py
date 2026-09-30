"""A14: correcció del biaix de contorn dels filtres isotròpics (ACHF 47/49/51/53, WOW 55/56) contra el forat lunar:
component radial coherent en azimut (σθ 6°) a la banda d ∈ [−2, 22] px (taper fins a 32) respecte del nivell a d 32–48, restat; control nul a una vora falsa (+170 px)."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
import compo; from compo import *
from scipy.ndimage import map_coordinates, gaussian_filter1d
v=np.load(SP+'/a9_vores.npz'); TH=v['TH']; CX,CY=998.88,998.41
r=v['alfa_base_(forat)'].copy(); ok=np.isfinite(r); r[~ok]=np.interp(np.nonzero(~ok)[0],np.nonzero(ok)[0],r[ok]); k=np.exp(-0.5*(np.arange(-40,41)/8)**2); k/=k.sum(); R_hole=np.convolve(np.r_[r[-40:],r,r[:40]],k,'valid')
yy,xx=np.mgrid[0:2000,0:2000]; rr=np.hypot(xx-CX,yy-CY); az=np.rad2deg(np.arctan2(-(yy-CY),xx-CX))%360; ia=np.clip((az/0.25).astype(int),0,len(TH)-1)
D=np.arange(-6,49,0.5); SIG=24  # 6° en mostres de 0,25°
def w_taper(d): return np.where(d<=22,1.0,np.where(d>=32,0.0,0.5*(1+np.cos(np.pi*(d-22)/10))))*(d>=-2)
def mesura(F,aeff,Redge):
    xs=CX+(Redge[:,None]+D[None,:])*np.cos(TH[:,None]); ys=CY-(Redge[:,None]+D[None,:])*np.sin(TH[:,None])
    P=map_coordinates(F,[ys.ravel(),xs.ravel()],order=1).reshape(len(TH),len(D)); Am=map_coordinates(aeff,[ys.ravel(),xs.ravel()],order=1).reshape(len(TH),len(D))
    P=np.where(Am>=0.5,P,np.nan)
    # suavitzat circular en θ amb normalització (nan-aware)
    val=np.nan_to_num(P); wgt=np.isfinite(P).astype(float)
    S=gaussian_filter1d(val,SIG,axis=0,mode='wrap')/np.maximum(gaussian_filter1d(wgt,SIG,axis=0,mode='wrap'),1e-6); S[wgt==0]=np.nan
    ref=np.nanmean(S[:,(D>=32)&(D<=48)],1); B=(S-ref[:,None])*w_taper(D)[None,:]; B=np.nan_to_num(B)
    return P,S,B,ref
def a_pixel(B,Redge):
    d=rr-Redge[ia]; inb=(d>=-6)&(d<=48)
    Bp=np.zeros_like(rr,dtype=np.float32); Bp[inb]=map_coordinates(B,[az[inb]/0.25,(d[inb]+6)/0.5],order=1,mode='nearest'); return Bp
res={}
for lid in (47,49,51,53,55,56):
    dd=np.load(SP+f'/roi_L{lid}.npz'); rgb,a=carrega(lid); op=LAYERS[lid]['opacity']/255.0; aeff=a/op; F=rgb.mean(-1)
    gris=float(np.abs(rgb[...,0]-rgb[...,2]).max()); P,S,B,ref=mesura(F,aeff,R_hole)
    # control nul: vora falsa 170 px més enfora
    P0,S0,B0,ref0=mesura(F,aeff,R_hole+170)
    Bp=a_pixel(B,R_hole); F2=np.clip(F-Bp,0,1)
    # verificació: tornar a mesurar sobre F2
    P2,S2,B2,ref2=mesura(F2,aeff,R_hole)
    def rms_band(Bm,d0,d1): return float(np.sqrt(np.nanmean(Bm[:,(D>=d0)&(D<=d1)]**2)))
    r_=dict(nom=LAYERS[lid]['name'][:34],gris_max_dif=gris,
        biaix_rms_d0_8=rms_band(B,0,8),biaix_rms_d8_22=rms_band(B,8,22),biaix_max=float(np.nanmax(np.abs(B))),
        control_nul_rms_d0_8=rms_band(B0,0,8),control_nul_rms_d8_22=rms_band(B0,8,22),control_nul_max=float(np.nanmax(np.abs(B0))),
        despres_rms_d0_8=rms_band(B2,0,8),despres_rms_d8_22=rms_band(B2,8,22),
        pixels_canviats=int((np.abs(F2-F)>1/65535).sum()),canvi_max_DN16=float(np.abs(F2-F).max()*65535))
    res[lid]=r_; print(lid,json.dumps(r_,ensure_ascii=False))
    # desa la variant: mateixa delta als tres canals (la capa és grisa: gris_max_dif petit)
    out={key:dd[key] for key in dd.files}
    for c in ('c0','c1','c2'):
        ch=dd[c].astype(np.float32)/65535; out[c]=(np.clip(ch-Bp,0,1)*65535+.5).astype(np.uint16)
    np.savez_compressed(SP+f'/roi_L{lid}_v70.npz',**out); np.save(SP+f'/biaix_L{lid}.npy',Bp.astype(np.float32))
json.dump(res,open(SP+'/a14_filtres.json','w'),indent=1,ensure_ascii=False)
# índex de vora per sector amb els filtres corregits
for lid in (47,49,51,53,55,56): compo.OVERRIDE[lid]=SP+f'/roi_L{lid}_v70.npz'
RR=np.arange(440,480,0.25)
def perfil(img,az0,az1):
    th=np.deg2rad(np.arange(az0,az1,0.25)); xs=CX+RR[None,:]*np.cos(th[:,None]); ys=CY-RR[None,:]*np.sin(th[:,None])
    return np.median(map_coordinates(img,[ys.ravel(),xs.ravel()],order=1,mode='nearest').reshape(len(th),len(RR)),0)
sectors={'m1 dalt':(76,100),'m2 NW':(148,158),'m3-4 W':(163,173),'m5 Weq':(177,181),'m6 WSW':(189,199),'m8 SSW':(240,254),'ctrl E':(-10,10),'ctrl S':(260,280),'ctrl NE':(40,60)}
def idx(C,a):
    L=C.mean(-1); out={}
    for kk,(a0,a1) in sectors.items():
        p=perfil(L,a0,a1); out[kk]=round(float(p[(RR>=452)&(RR<=456)].max()/p[(RR>=462)&(RR<=468)].mean()-1),3)
    return out
compo.OVERRIDE.clear(); C,a=recompon(ids=[3,41,42,47,49,51,53,45,46,55,56]); print('índex de vora base+filtres ABANS  :',idx(C,a))
for lid in (47,49,51,53,55,56): compo.OVERRIDE[lid]=SP+f'/roi_L{lid}_v70.npz'
C,a=recompon(ids=[3,41,42,47,49,51,53,45,46,55,56]); print('índex de vora base+filtres DESPRÉS:',idx(C,a))
C,a=recompon(ids=[3]); print('índex de vora base sola           :',idx(C,a))
np.savez_compressed(SP+'/roi_recomp_v70_filtres.npz',C=(np.clip(C,0,1)*65535+.5).astype(np.uint16),a=(np.clip(a,0,1)*65535+.5).astype(np.uint16))
