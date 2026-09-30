import numpy as np, sys, json
sys.path.insert(0,"/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/sony")
from common import planes, SCALE
from esf import limb_circle, annulus_samples
from viaA2 import esf_build
from scipy.optimize import least_squares

FINE=np.arange(-60,60,0.005)

def lsf_moffat(x,a,b):
    return (1.0+(x/a)**2)**(-(b-0.5))

def forward(p,x,pixel=0.5,psf='moffat'):
    A,L1,f2,L2,a,b,B=p
    dx=FINE[1]-FINE[0]
    step=np.where(FINE>0,A*((1-f2)*np.exp(-FINE/max(L1,1e-3))+f2*np.exp(-FINE/max(L2,1e-3))),0.0)
    t=np.arange(-2000,2001)*dx
    k=lsf_moffat(t,a,b) if psf=='moffat' else np.exp(-0.5*(t/a)**2)
    k/=k.sum()
    conv=np.convolve(step,k,mode='same')
    nb=max(1,int(round(pixel/dx))); conv=np.convolve(conv,np.ones(nb)/nb,mode='same')
    return np.interp(x,FINE,conv)+B

def fit(ctr,prof,fitrange=10.0,psf='moffat'):
    m=np.isfinite(prof)&(np.abs(ctr)<fitrange)
    x=ctr[m]; y=prof[m]
    if psf=='moffat':
        p0=[1.0,16.,0.3,4.,0.45,2.5,0.0]
        lo=[0.2,3.,0.,0.5,0.05,0.7,-0.05]; hi=[3.,300.,0.95,300.,3.,25.,0.05]
    else:
        p0=[1.0,16.,0.3,4.,0.6,2.0,0.0]
        lo=[0.2,3.,0.,0.5,0.05,1.9,-0.05]; hi=[3.,300.,0.95,300.,3.,2.1,0.05]
    r=least_squares(lambda p:(forward(p,x,psf=psf)-y),p0,bounds=(lo,hi),xtol=1e-13,ftol=1e-13,max_nfev=20000)
    return r,x,y

def moffat_fwhm2d(a,b): return 2*a*np.sqrt(2**(1.0/b)-1)
def moffat_fwhm_lsf(a,b): return 2*a*np.sqrt(2**(1.0/(b-0.5))-1)

def run(nm,ch,c0=None,sector_mask=None,tag="",quiet=False):
    P=planes(nm); img=P[ch]
    if c0 is None:
        g=P['G1']; h,w=g.shape
        dsn=g[:h//8*8,:w//8*8].reshape(h//8,8,w//8,8).mean(axis=(1,3))
        thr=np.percentile(dsn,99.9)*0.05
        ys,xs=np.nonzero(dsn>thr); c0=(np.average(xs,weights=dsn[ys,xs])*8,np.average(ys,weights=dsn[ys,xs])*8)
    cx,cy,R,rms,n=limb_circle(img,ch,c0,80,320)
    d,az,v=annulus_samples(img,ch,cx,cy,R)
    ctr,prof,cnt,ok,tot,diag=esf_build(d,az,v,sector_mask=sector_mask)
    if len(ok)<5: return None
    r,x,y=fit(ctr,prof)
    a,b=r.x[4],r.x[5]
    f2d=moffat_fwhm2d(a,b); flsf=moffat_fwhm_lsf(a,b)
    ftot=np.sqrt(flsf**2+0.5**2)  # + single-photosite aperture (0.5 half-res px)
    resid=np.sqrt(np.mean(r.fun**2))
    o=dict(frame=nm,ch=ch,tag=tag,nsec=len(ok),R=R,a=a,b=b,
           fwhm2d_as=f2d*2*SCALE, fwhmlsf_as=flsf*2*SCALE, fwhmtot_as=ftot*2*SCALE, resid=resid)
    if not quiet:
        print("%-14s %-3s %-9s sec=%2d  a=%.3f b=%.2f  FWHM_2D=%.2f\"  FWHM_LSF=%.2f\"  +pix=%.2f\"  resid=%.4f"%(
            nm,ch,tag,len(ok),a,b,o['fwhm2d_as'],o['fwhmlsf_as'],o['fwhmtot_as'],resid))
    return o,ctr,prof,r

if __name__=="__main__":
    for nm in ["DSC06983.ARW","DSC06995.ARW","DSC06998.ARW"]:
        for ch in ['R','G1','G2','B']:
            run(nm,ch)
