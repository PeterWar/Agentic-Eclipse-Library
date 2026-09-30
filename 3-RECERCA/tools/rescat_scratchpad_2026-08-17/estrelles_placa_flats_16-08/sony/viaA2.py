import numpy as np, sys, json
sys.path.insert(0,"/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/sony")
from common import planes, SCALE
from esf import limb_circle, annulus_samples
from scipy.optimize import least_squares

SAT=(16383.0-512.0)*0.97

def esf_build(d,az,v,nsec=72,half=14.0,binw=0.05,inner=(-12,-4),outer=(4,12),
              min_contrast=200.0,align_iters=4,sector_mask=None):
    sec=((az+np.pi)/(2*np.pi)*nsec).astype(int)%nsec
    norm=np.full(len(v),np.nan); tot=np.zeros(nsec); ok_sec=[]
    diag={}
    for s in range(nsec):
        if sector_mask is not None and not sector_mask[s]: continue
        m=sec==s
        ds=d[m]; vs=v[m]
        if vs.max()>=SAT: diag[s]='sat'; continue
        mi=(ds>inner[0])&(ds<inner[1]); mo=(ds>outer[0])&(ds<outer[1])
        if mi.sum()<20 or mo.sum()<20: diag[s]='few'; continue
        pi=np.polyfit(ds[mi],vs[mi],1); po=np.polyfit(ds[mo],vs[mo],1)
        c=po[1]-pi[1]
        if c<min_contrast: diag[s]='lowc'; continue
        norm[m]=(vs-np.polyval(pi,ds))/c
        ok_sec.append(s); diag[s]=c
    okm=np.isfinite(norm)
    edges=np.arange(-half,half+binw,binw); ctr=0.5*(edges[:-1]+edges[1:])
    dd=d.copy()
    lags=np.arange(-1.0,1.0001,0.01)
    for it in range(align_iters):
        cnt,_=np.histogram(dd[okm],edges); ssum,_=np.histogram(dd[okm],edges,weights=norm[okm])
        prof=np.where(cnt>0,ssum/np.maximum(cnt,1),np.nan)
        if it==align_iters-1: break
        for s in ok_sec:
            m=(sec==s)&okm
            ds=dd[m]; ns=norm[m]; w=np.abs(ds)<3.0
            if w.sum()<10: continue
            e=[np.nanmean((ns[w]-np.interp(ds[w]-L,ctr,prof,left=np.nan,right=np.nan))**2) for L in lags]
            bl=lags[int(np.nanargmin(e))]
            dd[m]=ds-bl; tot[s]+=bl
    return ctr,prof,cnt,ok_sec,tot,diag

def model(p,x,fine,ker_pix):
    """p = [A, L1, f2, L2, s_sigma, B]; edge model: corona = A*(f1*exp(-t/L1)+f2*exp(-t/L2)) for t>0"""
    A,L1,f2,L2,sg,B=p
    dx=fine[1]-fine[0]
    step=np.where(fine>0,A*((1-f2)*np.exp(-fine/max(L1,1e-3))+f2*np.exp(-fine/max(L2,1e-3))),0.0)
    n=int(np.ceil(6*abs(sg)/dx))+1
    t=np.arange(-n,n+1)*dx
    g=np.exp(-0.5*(t/max(abs(sg),1e-4))**2); g/=g.sum()
    conv=np.convolve(step,g,mode='same')
    # pixel aperture (1 full-res px = 0.5 half-res px)
    k=max(1,int(round(ker_pix/dx)))
    box=np.ones(k)/k
    conv=np.convolve(conv,box,mode='same')
    return np.interp(x,fine,conv)+B

def fit_psf(ctr,prof,fitrange=9.0,pixel=0.5):
    m=np.isfinite(prof)&(np.abs(ctr)<fitrange)
    x=ctr[m]; y=prof[m]
    fine=np.arange(-40,40,0.01)
    p0=[1.0,16.0,0.3,4.0,0.5,0.0]
    lo=[0.2,3.0,0.0,0.5,0.05,-0.05]; hi=[3.0,200.0,0.95,200.0,3.0,0.05]
    r=least_squares(lambda p:(model(p,x,fine,pixel)-y),p0,bounds=(lo,hi),xtol=1e-12,ftol=1e-12)
    return r

def gauss_fwhm(sigma): return 2.3548*sigma

def analyse(nm,ch,c0=None,sector_mask=None,verbose=True,tag=""):
    P=planes(nm); img=P[ch]
    if c0 is None:
        g=P['G1']; h,w=g.shape
        dsn=g[:h//8*8,:w//8*8].reshape(h//8,8,w//8,8).mean(axis=(1,3))
        thr=np.percentile(dsn,99.9)*0.05
        ys,xs=np.nonzero(dsn>thr); c0=(np.average(xs,weights=dsn[ys,xs])*8,np.average(ys,weights=dsn[ys,xs])*8)
    cx,cy,R,rms,n=limb_circle(img,ch,c0,80,320)
    d,az,v=annulus_samples(img,ch,cx,cy,R)
    ctr,prof,cnt,ok,tot,diag=esf_build(d,az,v,sector_mask=sector_mask)
    if len(ok)<6: return None
    r=fit_psf(ctr,prof)
    sg=abs(r.x[4]); fw_h=gauss_fwhm(sg)             # atmos+optics only, half-res px
    fw_tot_h=np.sqrt(fw_h**2+ (0.5*1.0)**2)          # + pixel box FWHM (=0.5 half-res px)
    res=r.fun; rmsr=np.sqrt(np.mean(res**2))
    out=dict(frame=nm,ch=ch,R=R,cx=cx,cy=cy,nsec=len(ok),shift_rms=float(np.std(tot[ok])),
             sigma=sg,fwhm_psf_arcsec=fw_h*2*SCALE,fwhm_tot_arcsec=fw_tot_h*2*SCALE,
             L1=r.x[1],f2=r.x[2],L2=r.x[3],A=r.x[0],B=r.x[5],resid=rmsr)
    if verbose:
        print("%-14s %-3s %-10s R=%.2f sec=%2d shrms=%.3f  sigma=%.4f  FWHM(atm+opt)=%.2f\"  FWHM(total)=%.2f\"  resid=%.4f"%(
            nm,ch,tag,R,len(ok),np.std(tot[ok]),sg,out['fwhm_psf_arcsec'],out['fwhm_tot_arcsec'],rmsr))
    return out,ctr,prof,cnt

if __name__=="__main__":
    frames=["DSC06983.ARW","DSC06995.ARW","DSC06998.ARW"]
    for nm in frames:
        for ch in ['R','G1','G2','B']:
            analyse(nm,ch)
