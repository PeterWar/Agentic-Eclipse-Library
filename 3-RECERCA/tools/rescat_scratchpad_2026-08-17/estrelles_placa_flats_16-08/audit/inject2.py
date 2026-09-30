"""Igual que abans pero comptant el difuminat REALMENT injectat (variancia del
nucli discret), no el nominal. Nucli aplicat a la subreixa de pas 2 px."""
import sys, numpy as np, math
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/cmp')
from esfcmp import *
from run import TRAINS
from scipy.ndimage import gaussian_filter1d

def kern_var(sig):
    d=np.zeros(41); d[20]=1.0
    k=gaussian_filter1d(d,sig,mode='constant',truncate=8.0)
    xx=np.arange(41)-20.0
    k=k/k.sum()
    return float((k*xx*xx).sum())

def blur_green(v,c,sig_sub):
    out=v.copy()
    for k in (1,3):
        ys,xs=np.nonzero(c==k); r0,c0=ys[0]%2,xs[0]%2
        sub=v[r0::2,c0::2]
        sub=gaussian_filter1d(sub,sig_sub,axis=0,mode='nearest',truncate=8.)
        sub=gaussian_filter1d(sub,sig_sub,axis=1,mode='nearest',truncate=8.)
        out[r0::2,c0::2]=sub
    return out

def meas(train,name,sig_sub=0.0):
    t=TRAINS[train]
    v,c,white=load(t['dirp']+name+t['ext'])
    vb=blur_green(v,c,sig_sub) if sig_sub>0 else v
    x,y,val=pick(vb,c,'G'); xr,yr,vr=pick(v,c,'G')
    cx,cy,R=centroid(v)
    for w in (60.,25.): cx,cy,R,sd,ng=fit_circle(xr,yr,vr,cx,cy,R,win=w)
    fits=sector_fits(x,y,val,cx,cy,R,30.0/t['scale'],240,(white-512)*0.93)
    if len(fits)<20: return None
    xc,ym,e,cnt=stack_esf(fits,align=True,xlim=20.0/t['scale'],bw=0.05)
    return fit_esf(xc,ym,e,boxw=1.0)['fwhm_tot']*t['scale']

print("injectat_real = FWHM equivalent del nucli discret, en arcsec")
for train,names,sigs in [('vixen',['572A2987','572A2974'],[0.8,1.2,1.8,2.5]),
                         ('sony',['DSC06981','DSC06979'],[0.8,1.2,1.8,2.5])]:
    t=TRAINS[train]
    for n in names:
        F0=meas(train,n,0.0)
        line=f"{train:5s} {n} F(0)={F0:5.2f}\""
        for s in sigs:
            var=kern_var(s)                    # px de subreixa^2
            b=2.3548*math.sqrt(var)*2.0*t['scale']   # arcsec
            F=meas(train,n,s)
            rec=math.sqrt(max(F*F-F0*F0,0))
            line+=f" | inj={b:5.2f} rec={rec:5.2f} ({rec/b*100:3.0f}%)"
        print(line,flush=True)
