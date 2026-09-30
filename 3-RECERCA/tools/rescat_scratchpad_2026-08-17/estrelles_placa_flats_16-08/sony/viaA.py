import numpy as np, sys, json
sys.path.insert(0,"/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/sony")
from common import planes, SCALE
from esf import limb_circle, annulus_samples

SAT=16383.0-512.0

def build_esf(d,az,v, nsec=72, half=14.0, binw=0.05, inner=(-12,-4), outer=(4,12),
              min_contrast=50.0, align_iters=3, sat=SAT*0.95):
    sec=((az+np.pi)/(2*np.pi)*nsec).astype(int)%nsec
    keep_sec=[]; norm=np.full(len(v),np.nan); shift=np.zeros(nsec)
    info={}
    for s in range(nsec):
        m=sec==s
        ds=d[m]; vs=v[m]
        if vs.max()>=sat:   # saturated (prominence/bead/photosphere)
            info[s]='sat'; continue
        mi=(ds>inner[0])&(ds<inner[1]); mo=(ds>outer[0])&(ds<outer[1])
        if mi.sum()<20 or mo.sum()<20: info[s]='few'; continue
        pi=np.polyfit(ds[mi],vs[mi],1); po=np.polyfit(ds[mo],vs[mo],1)
        Iin=pi[1]; Iout=po[1]
        c=Iout-Iin
        if c<min_contrast: info[s]='lowc'; continue
        norm[m]=(vs-np.polyval(pi,ds))/c
        keep_sec.append(s); info[s]=('ok',c,Iin,Iout,pi[0]/c,po[0]/c)
    ok=np.isfinite(norm)
    # iterative per-sector alignment against the global ESF
    edges=np.arange(-half,half+binw,binw); ctr=0.5*(edges[:-1]+edges[1:])
    dd=d.copy()
    for it in range(align_iters):
        cnt,_=np.histogram(dd[ok],edges); ssum,_=np.histogram(dd[ok],edges,weights=norm[ok])
        prof=np.where(cnt>0,ssum/np.maximum(cnt,1),np.nan)
        if it==align_iters-1: break
        # local shift per sector: minimise |sector profile - global| over -1..1 px
        gi=np.interp
        lags=np.arange(-1.5,1.5001,0.02)
        for s in keep_sec:
            m=(sec==s)&ok
            ds=dd[m]; ns=norm[m]
            w=(np.abs(ds)<4)
            if w.sum()<10: continue
            best=None;bl=0
            for L in lags:
                pv=np.interp(ds[w]-L,ctr,prof,left=np.nan,right=np.nan)
                e=np.nanmean((ns[w]-pv)**2)
                if best is None or e<best: best=e;bl=L
            dd[m]=ds-bl; shift[s]=bl
    return ctr,prof,cnt,keep_sec,info,shift,dd,norm,ok,sec

def lsf_fwhm(ctr,prof,fit_half=6.0):
    m=np.isfinite(prof)
    c=ctr[m]; p=prof[m]
    # smooth lightly then derivative
    from scipy.ndimage import uniform_filter1d
    ps=uniform_filter1d(p,5)
    ls=np.gradient(ps,c)
    # baseline: slopes far in / far out of the ESF
    bi=np.median(ls[(c>-12)&(c<-6)]); bo=np.median(ls[(c>6)&(c<12)])
    base=bi+(bo-bi)*np.clip(np.interp(c,c,ps),0,1)
    y=ls-base
    sel=np.abs(c)<fit_half
    cs=c[sel]; ys=y[sel]
    pk=ys.max(); i0=np.argmax(ys)
    hm=pk/2.0
    # left crossing
    def cross(idx,step):
        i=idx
        while 0<=i+step<len(ys) and ys[i]>hm: i+=step
        if not (0<=i<len(ys)) or ys[i]>hm: return np.nan
        x1,x2=cs[i],cs[i-step]; y1,y2=ys[i],ys[i-step]
        return x1+(hm-y1)*(x2-x1)/(y2-y1)
    xl=cross(i0,-1); xr=cross(i0,+1)
    return xl,xr,xr-xl,pk,cs,ys

if __name__=="__main__":
    nm=sys.argv[1] if len(sys.argv)>1 else "DSC06983.ARW"
    P=planes(nm)
    c0=(1834.6,1741.2) if nm=="DSC06983.ARW" else None
    if c0 is None:
        g=P['G1']; h,w=g.shape
        dsn=g[:h//8*8,:w//8*8].reshape(h//8,8,w//8,8).mean(axis=(1,3))
        thr=np.percentile(dsn,99.9)*0.05
        ys,xs=np.nonzero(dsn>thr); c0=(np.average(xs,weights=dsn[ys,xs])*8,np.average(ys,weights=dsn[ys,xs])*8)
    for ch in ['R','G1','G2','B']:
        img=P[ch]
        cx,cy,R,rms,n=limb_circle(img,ch,c0,80,320)
        d,az,v=annulus_samples(img,ch,cx,cy,R)
        ctr,prof,cnt,ks,info,shift,dd,norm,ok,sec=build_esf(d,az,v)
        xl,xr,f,pk,cs,ys=lsf_fwhm(ctr,prof)
        print("%s %s R=%.3f rms=%.3f sect=%d/72  FWHM=%.3f half-px = %.3f fullpx = %.2f arcsec  (L=%.2f R=%.2f)"%(
            nm,ch,R,rms,len(ks),f,f*2,f*2*SCALE,xl,xr))
