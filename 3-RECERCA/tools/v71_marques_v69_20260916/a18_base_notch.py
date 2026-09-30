"""A18: el clot (notch) de la base al costat del forat lunar: mesura per sector i per canal; correcció multiplicativa coherent en azimut (σθ 6°) a d ∈ [−1, 8] px (taper 6→8) respecte de l'extrapolació lineal de d 8–20; control nul a +170 px."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
import compo; from compo import *
from scipy.ndimage import map_coordinates, gaussian_filter1d
v=np.load(SP+'/a9_vores.npz'); TH=v['TH']; CX,CY=998.88,998.41
r=v['alfa_base_(forat)'].copy(); ok=np.isfinite(r); r[~ok]=np.interp(np.nonzero(~ok)[0],np.nonzero(ok)[0],r[ok]); R_hole=gaussian_filter1d(r,8,mode='wrap')
yy,xx=np.mgrid[0:2000,0:2000]; rr=np.hypot(xx-CX,yy-CY); az=np.rad2deg(np.arctan2(-(yy-CY),xx-CX))%360; ia=np.clip((az/0.25).astype(int),0,len(TH)-1)
D=np.arange(-3,25,0.5); SIG=24
d3=np.load(SP+'/roi_L3.npz'); rgb=np.dstack([d3['c0'],d3['c1'],d3['c2']]).astype(np.float32)/65535; A=d3['c-1'].astype(np.float32)/65535; Mk=np.load(SP+'/roi_L3_v70.npz')['c-2'].astype(np.float32)/65535
sup=(A*Mk)
def polar(img,Redge):
    xs=CX+(Redge[:,None]+D[None,:])*np.cos(TH[:,None]); ys=CY-(Redge[:,None]+D[None,:])*np.sin(TH[:,None])
    return map_coordinates(img,[ys.ravel(),xs.ravel()],order=1).reshape(len(TH),len(D))
def smooth_th(P):
    val=np.nan_to_num(P); wgt=np.isfinite(P).astype(float); S=gaussian_filter1d(val,SIG,axis=0,mode='wrap')/np.maximum(gaussian_filter1d(wgt,SIG,axis=0,mode='wrap'),1e-6); S[gaussian_filter1d(wgt,SIG,axis=0,mode='wrap')<0.3]=np.nan; return S
def guany(L,Redge):
    P=polar(L,Redge); Sp=polar(sup,Redge); P=np.where(Sp>=0.5,np.log(np.maximum(P,1e-4)),np.nan); S=smooth_th(P)
    kref=(D>=8)&(D<=20); g=np.zeros_like(S)
    for i in range(len(TH)):
        s=S[i]; okk=np.isfinite(s)&kref
        if okk.sum()<10: continue
        a,b=np.polyfit(D[okk],s[okk],1); ref=a*D+b; g[i]=ref-s   # ln(ref/S): >0 on hi ha dèficit
    g=np.nan_to_num(g); w=np.where(D<=6,1.0,np.where(D>=8,0.0,0.5*(1+np.cos(np.pi*(D-6)/2))))*(D>=-1)
    return np.clip(g,0,None)*w[None,:], S   # només omplir dèficits
L=rgb.mean(-1); G,S=guany(L,R_hole); G0,_=guany(L,R_hole+170)
print('dèficit màxim (ln) a la vora del forat: %.3f (%.0f %%); control nul (+170 px): %.3f (%.1f %%)'%(G.max(),100*(np.exp(G.max())-1),G0.max(),100*(np.exp(G0.max())-1)))
sect=np.arange(0,360,10); print('sector: dèficit màx (%) a d ≤ 6 · per canal R,G,B (a la mateixa posició)')
for s in sect:
    k=(np.rad2deg(TH)>=s)&(np.rad2deg(TH)<s+10); gm=np.exp(G[k].max())-1
    if gm>0.03:
        i=np.nonzero(k)[0][np.argmax(G[k].max(1))]; j=np.argmax(G[i]); ch=[]
        for c in range(3):
            Pc=polar(rgb[...,c],R_hole); Sc=smooth_th(np.where(polar(sup,R_hole)>=0.5,np.log(np.maximum(Pc,1e-4)),np.nan)); okk=np.isfinite(Sc[i])&(D>=8)&(D<=20); a,b=np.polyfit(D[okk],Sc[i][okk],1); ch.append(100*(np.exp(a*D[j]+b-Sc[i][j])-1))
        print(f'  az {s:3d}–{s+10:3d}: {100*gm:5.1f} % a d={D[j]:.1f}  R {ch[0]:5.1f} G {ch[1]:5.1f} B {ch[2]:5.1f}')
# aplica el guany (exp(G)) als tres canals, només al suport
d=rr-R_hole[ia]; inb=(d>=-3)&(d<=24); Gp=np.zeros_like(rr,dtype=np.float32); Gp[inb]=map_coordinates(G,[az[inb]/0.25,(d[inb]+3)/0.5],order=1,mode='nearest'); gain=np.exp(Gp)
out={k:d3[k] for k in d3.files}; out['c-2']=np.load(SP+'/roi_L3_v70.npz')['c-2']
for c,key in enumerate(('c0','c1','c2')): out[key]=(np.clip(rgb[...,c]*gain,0,1)*65535+.5).astype(np.uint16)
np.savez_compressed(SP+'/roi_L3_v70.npz',**out); np.save(SP+'/guany_base.npy',gain.astype(np.float32))
print('base: píxels amb guany > 1,005: %d; guany màxim %.3f'%(int((gain>1.005).sum()),gain.max()))
# verificació: tornar a mesurar
L2=np.dstack([out['c0'],out['c1'],out['c2']]).astype(np.float32).mean(-1)/65535; G2,_=guany(L2,R_hole); print('dèficit residual màxim després: %.1f %%'%(100*(np.exp(G2.max())-1)))
json.dump(dict(deficit_max_ln=float(G.max()),control_nul_max_ln=float(G0.max()),residual_max_ln=float(G2.max()),pixels=int((gain>1.005).sum()),gain_max=float(gain.max())),open(SP+'/a18_base.json','w'),indent=1)
