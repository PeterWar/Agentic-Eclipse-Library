import numpy as np, sys
sys.path.insert(0,"/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/sony")
from common import planes, SCALE
from esf import limb_circle, annulus_samples
from viaA3 import fit, moffat_fwhm2d, moffat_fwhm_lsf
SAT=(16383.0-512.0)*0.97

def prep(nm,ch,c0=None,nsec=72,half=14.0,inner=(-12,-4),outer=(4,12),min_contrast=200.0,
         align_iters=3,binw=0.05):
    P=planes(nm); img=P[ch]
    if c0 is None:
        g=P['G1']; h,w=g.shape
        dsn=g[:h//8*8,:w//8*8].reshape(h//8,8,w//8,8).mean(axis=(1,3))
        thr=np.percentile(dsn,99.9)*0.05
        ys,xs=np.nonzero(dsn>thr); c0=(np.average(xs,weights=dsn[ys,xs])*8,np.average(ys,weights=dsn[ys,xs])*8)
    cx,cy,R,rms,n=limb_circle(img,ch,c0,80,320)
    d,az,v=annulus_samples(img,ch,cx,cy,R,half=half)
    sec=((az+np.pi)/(2*np.pi)*nsec).astype(int)%nsec
    norm=np.full(len(v),np.nan); ok_sec=[]; contrast=np.full(nsec,np.nan)
    for s in range(nsec):
        m=sec==s; ds=d[m]; vs=v[m]
        if len(vs)<40 or vs.max()>=SAT: continue
        mi=(ds>inner[0])&(ds<inner[1]); mo=(ds>outer[0])&(ds<outer[1])
        if mi.sum()<15 or mo.sum()<15: continue
        pi=np.polyfit(ds[mi],vs[mi],1); po=np.polyfit(ds[mo],vs[mo],1)
        c=po[1]-pi[1]
        if c<min_contrast: continue
        norm[m]=(vs-np.polyval(pi,ds))/c; ok_sec.append(s); contrast[s]=c
    okm=np.isfinite(norm); dd=d.copy()
    edges=np.arange(-half,half+binw,binw); ctr=0.5*(edges[:-1]+edges[1:])
    lags=np.arange(-1.2,1.2001,0.02); tot=np.zeros(nsec)
    for it in range(align_iters):
        cnt,_=np.histogram(dd[okm],edges); ssum,_=np.histogram(dd[okm],edges,weights=norm[okm])
        prof=np.where(cnt>0,ssum/np.maximum(cnt,1),np.nan)
        if it==align_iters-1: break
        for s in ok_sec:
            m=(sec==s)&okm; ds=dd[m]; ns=norm[m]; w=np.abs(ds)<3.0
            if w.sum()<8: continue
            Q=ds[w][:,None]-lags[None,:]
            PV=np.interp(Q.ravel(),ctr,prof,left=np.nan,right=np.nan).reshape(Q.shape)
            e=np.nanmean((ns[w][:,None]-PV)**2,axis=0)
            bl=lags[int(np.nanargmin(e))]; dd[m]=ds-bl; tot[s]+=bl
    return dict(cx=cx,cy=cy,R=R,d=dd,az=az,v=v,norm=norm,ok=okm,sec=sec,ctr=ctr,prof=prof,
                ok_sec=ok_sec,contrast=contrast,shift=tot,binw=binw,half=half)

def build(pr,mask=None):
    okm=pr['ok'] if mask is None else (pr['ok']&mask)
    edges=np.arange(-pr['half'],pr['half']+pr['binw'],pr['binw'])
    ctr=0.5*(edges[:-1]+edges[1:])
    cnt,_=np.histogram(pr['d'][okm],edges); ssum,_=np.histogram(pr['d'][okm],edges,weights=pr['norm'][okm])
    prof=np.where(cnt>=3,ssum/np.maximum(cnt,1),np.nan)
    return ctr,prof,cnt

def fwhm_of(ctr,prof):
    r,x,y=fit(ctr,prof)
    a,b=r.x[4],r.x[5]
    return moffat_fwhm_lsf(a,b)*2*SCALE, moffat_fwhm2d(a,b)*2*SCALE, np.sqrt(np.mean(r.fun**2)), r

def esf_widths(ctr,prof):
    """model-free 10-90 and 25-75 widths of the ESF, in arcsec"""
    m=np.isfinite(prof)&(np.abs(ctr)<3.0)
    c=ctr[m]; p=prof[m]
    out={}
    for lo,hi in [(0.1,0.9),(0.25,0.75),(0.05,0.5),(0.5,0.95)]:
        try:
            xl=np.interp(lo,p,c); xh=np.interp(hi,p,c)
            out["%g-%g"%(lo,hi)]=(xh-xl)*2*SCALE
        except Exception: out["%g-%g"%(lo,hi)]=np.nan
    return out
