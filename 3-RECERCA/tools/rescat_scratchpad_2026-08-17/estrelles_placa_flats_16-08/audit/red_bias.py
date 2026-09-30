import sys, numpy as np, math
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/cmp')
from esfcmp import *
from run import TRAINS
from scipy.ndimage import gaussian_filter1d
def kern_var(sig):
    d=np.zeros(61); d[30]=1.
    k=gaussian_filter1d(d,sig,mode='constant',truncate=10.); k/=k.sum()
    xx=np.arange(61)-30.
    return float((k*xx*xx).sum())
def blur(v,c,cols,sig):
    out=v.copy()
    for k in cols:
        ys,xs=np.nonzero(c==k); r0,c0=ys[0]%2,xs[0]%2
        s=v[r0::2,c0::2]
        s=gaussian_filter1d(s,sig,axis=0,mode='nearest',truncate=10.)
        s=gaussian_filter1d(s,sig,axis=1,mode='nearest',truncate=10.)
        out[r0::2,c0::2]=s
    return out
def meas(train,name,ch,sig=0.0):
    t=TRAINS[train]
    v,c,white=load(t['dirp']+name+t['ext'])
    cols={'R':[0],'G':[1,3],'B':[2]}[ch]
    vb=blur(v,c,cols,sig) if sig>0 else v
    x,y,val=pick(vb,c,ch); xr,yr,vr=pick(v,c,'G')
    cx,cy,R=centroid(v)
    for w in (60.,25.): cx,cy,R,sd,ng=fit_circle(xr,yr,vr,cx,cy,R,win=w)
    f=sector_fits(x,y,val,cx,cy,R,30./t['scale'],240,(white-512)*0.93)
    if len(f)<20: return None
    xc,ym,e,cnt=stack_esf(f,align=True,xlim=20./t['scale'],bw=0.05)
    return fit_esf(xc,ym,e,boxw=1.0)['fwhm_tot']*t['scale']
print("BIAIX AL CANAL VERMELL DEL VIXEN (el que sosté el sostre del seeing)")
for n in ('572A2987','572A2999','572A2974'):
    t=TRAINS['vixen']
    F0=meas('vixen',n,'R')
    line=f" 572A/{n} R  F(0)={F0:5.2f}\""
    Xs=[]
    for s in (0.8,1.2,1.8):
        b=2.3548*math.sqrt(kern_var(s))*2.0*t['scale']
        F=meas('vixen',n,'R',s)
        X=math.sqrt(max(F*F-b*b,0))
        Xs.append(X)
        line+=f" | inj={b:5.2f} F={F:5.2f} -> F0_real={X:5.2f}"
    print(line+f"   >>> biaix={100*(F0/np.mean(Xs)-1):+.1f}%",flush=True)
print()
print("El mateix al VERD del Vixen i al VERD de la Sony, per comparar")
for train,names in [('vixen',['572A2987','572A2974']),('sony',['DSC06981','DSC06979'])]:
    t=TRAINS[train]
    for n in names:
        F0=meas(train,n,'G'); Xs=[]
        line=f" {train:5s} {n} G  F(0)={F0:5.2f}\""
        for s in (0.8,1.2,1.8):
            b=2.3548*math.sqrt(kern_var(s))*2.0*t['scale']
            F=meas(train,n,'G',s); X=math.sqrt(max(F*F-b*b,0)); Xs.append(X)
            line+=f" | inj={b:5.2f} F0_real={X:5.2f}"
        print(line+f"   >>> biaix={100*(F0/np.mean(Xs)-1):+.1f}%",flush=True)
