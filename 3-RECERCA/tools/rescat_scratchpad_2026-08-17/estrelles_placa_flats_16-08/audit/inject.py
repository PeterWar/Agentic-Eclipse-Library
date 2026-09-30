"""Prova empirica sobre dades REALS: hi afegim un difuminat CONEGUT i mirem si
l'estimador el recupera. Si es imparcial, F(b)^2 - F(0)^2 = b^2."""
import sys, numpy as np, math
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/cmp')
from esfcmp import *
from run import TRAINS
from scipy.ndimage import gaussian_filter

def blur_green(v,c,fwhm_px):
    if fwhm_px<=0: return v
    sig=fwhm_px/2.3548/2.0   # sublattice de pas 2 px
    out=v.copy()
    for k in (1,3):
        ys,xs=np.nonzero(c==k)
        r0,c0=ys[0]%2,xs[0]%2
        sub=v[r0::2,c0::2]
        out[r0::2,c0::2]=gaussian_filter(sub,sig,mode='nearest')
    return out

def meas(train,name,fwhm_add_as=0.0):
    t=TRAINS[train]
    v,c,white=load(t['dirp']+name+t['ext'])
    vb=blur_green(v,c,fwhm_add_as/t['scale'])
    x,y,val=pick(vb,c,'G')
    xr,yr,vr=pick(v,c,'G')
    cx,cy,R=centroid(v)
    for w in (60.,25.): cx,cy,R,sd,ng=fit_circle(xr,yr,vr,cx,cy,R,win=w)
    fits=sector_fits(x,y,val,cx,cy,R,30.0/t['scale'],240,(white-512)*0.93)
    if len(fits)<20: return None
    xc,ym,e,cnt=stack_esf(fits,align=True,xlim=20.0/t['scale'],bw=0.05)
    f=fit_esf(xc,ym,e,boxw=1.0)
    return f['fwhm_tot']*t['scale'],len(fits)

for train,names in [('vixen',['572A2987','572A2999','572A2974']),
                    ('sony',['DSC06981','DSC06995','DSC06979'])]:
    for n in names:
        base=meas(train,n,0.0)[0]
        line=f"{train:5s} {n} F(0)={base:5.2f}\""
        for b in (4.0,6.0,8.0):
            fb,nk=meas(train,n,b)
            q=fb*fb-base*base
            line+=f" | +{b:.0f}\": F={fb:5.2f} sqrt(dF2)={math.sqrt(max(q,0)):5.2f}"
        print(line,flush=True)
