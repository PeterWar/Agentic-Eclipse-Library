"""Isolated S8 audit. Default exactly reproduces historical S8. No side effects.

centered=True corrects the angular coordinate of sector-bin medians. This is an
algorithmic candidate, not a validated optical background or delivered image.
"""
import numpy as np
from scipy.ndimage import gaussian_filter1d,map_coordinates,median

def s8_eval(G,edge,centered=False):
    y,x=np.mgrid[:1400,:1400]
    rad=np.hypot(x-699.568111973117,y-699.6475341408573)
    ang=np.arctan2(y-699.6475341408573,x-699.568111973117)%(2*np.pi)
    f=gaussian_filter1d(edge,3,mode='wrap')
    d=rad-np.interp(ang,np.linspace(0,2*np.pi,1441),np.r_[f,f[0]])
    sec=(ang*72/(2*np.pi)).astype(int)
    dc=np.arange(-299,3,2.)
    ib=np.floor((d+300)/2).astype(int)
    valid=(ib>=0)&(ib<len(dc))
    labels=sec[valid]*len(dc)+ib[valid]
    counts=np.bincount(labels,minlength=72*len(dc)).reshape(72,-1)
    P=median(G[valid],labels=labels,index=np.arange(72*len(dc))).reshape(72,-1)
    P[counts<12]=np.nan
    for k in range(72):
        ok=np.isfinite(P[k]);P[k]=np.interp(dc,dc[ok],P[k,ok])
    base=np.median(P[:,(dc>=-260)&(dc<=-200)],axis=1)
    E=np.maximum(P-base[:,None],0)
    E=gaussian_filter1d(gaussian_filter1d(E,1.5,axis=1),2,axis=0,mode='wrap')
    W=np.maximum.accumulate(np.where(dc>=-260,E,0),axis=1)*np.clip((dc+260)/60,0,1)
    si=ang*72/(2*np.pi)
    if centered:si=(si-.5)%72
    wf=map_coordinates(np.r_[W,W[:1]],[si,np.interp(d,dc,np.arange(len(dc)))],order=1,mode='nearest')
    wf[d<-300]=0
    Ln=np.clip(G-wf,0,65535)
    dc1=np.arange(-69.5,1,1.);ib1=np.floor(d+70).astype(int);v=(ib1>=0)&(ib1<len(dc1))
    labels1=sec[v]*len(dc1)+ib1[v];counts1=np.bincount(labels1,minlength=72*len(dc1)).reshape(72,-1)
    rr=median(Ln[v],labels=labels1,index=np.arange(72*len(dc1))).reshape(72,-1)-base[:,None]
    rr[counts1<6]=0;rr=gaussian_filter1d(gaussian_filter1d(rr,1,axis=0,mode='wrap'),1,axis=1)
    tap=np.clip((dc1+70)/30,0,1);rr*=tap*tap*(3-2*tap)
    rf=map_coordinates(np.r_[rr,rr[:1]],[si,np.interp(d,dc1,np.arange(len(dc1)))],order=1,mode='nearest')
    rf[(d<-70)|(d>1)]=0;wf=np.maximum(wf+rf,0)
    return np.clip(G-wf,0,65535),wf
