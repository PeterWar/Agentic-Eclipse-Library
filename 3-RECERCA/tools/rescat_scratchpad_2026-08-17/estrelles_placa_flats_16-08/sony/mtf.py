import numpy as np, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
from common import SCALE
from core import prep, build
from scipy.optimize import least_squares
from scipy.ndimage import uniform_filter1d

def lsf_from_prof(ctr,prof,smooth=3):
    m=np.isfinite(prof)
    c=ctr[m]; p=uniform_filter1d(prof[m],smooth)
    l=np.gradient(p,c)
    return c,l

def mtf_from_lsf(c,l,fmax=0.6,nf=200):
    # remove the corona-gradient pedestal: subtract a smooth baseline fitted on |d|>4
    base=np.polyval(np.polyfit(c[np.abs(c)>4],l[np.abs(c)>4],2),c)
    y=l-base
    y=np.clip(y,0,None)
    y/= np.trapezoid(y,c)
    f=np.linspace(0,fmax,nf)
    M=np.array([np.abs(np.trapezoid(y*np.exp(-2j*np.pi*ff*c),c)) for ff in f])
    return f,M,y

def wing_fit(ctr,prof):
    """fit Moffat LSF cumulative to the INWARD side (pure PSF, no source behind)"""
    m=np.isfinite(prof)&(ctr<-0.3)&(ctr>-9)&(prof>1e-5)
    x=-ctr[m]; y=prof[m]
    def mod(p):
        a,b,A=p
        u=np.linspace(0,60,20000)
        # LSF(t) ~ (1+(t/a)^2)^-(b-0.5); tail integral from x to inf
        t=np.linspace(0,80,40000)
        k=(1+(t/a)**2)**(-(b-0.5))
        norm=2*np.trapezoid(k,t)
        cum=np.concatenate([[0],np.cumsum((k[1:]+k[:-1])/2*np.diff(t))])
        tail=(norm/2-cum)/norm
        return A*np.interp(x,t,tail)
    r=least_squares(lambda p: np.log(np.maximum(mod(p),1e-12))-np.log(y),[0.5,2.5,1.0],
                    bounds=([0.05,1.2,0.3],[5.0,12.0,3.0]),xtol=1e-12)
    a,b,A=r.x
    fw2d=2*a*np.sqrt(2**(1/b)-1)*2*SCALE
    fwlsf=2*a*np.sqrt(2**(1/(b-0.5))-1)*2*SCALE
    return a,b,A,fw2d,fwlsf,np.sqrt(np.mean(r.fun**2))

if __name__=="__main__":
    for nm in ["DSC06983.ARW","DSC06995.ARW","DSC06998.ARW"]:
        for ch in ['R','G1','B']:
            pr=prep(nm,ch); ctr,prof,cnt=build(pr)
            c,l=lsf_from_prof(ctr,prof)
            f,M,y=mtf_from_lsf(c,l)
            def at(lam_as):  # frequency for a given wavelength in arcsec
                fp=2*SCALE/lam_as
                return np.interp(fp,f,M)
            f50=np.interp(0.5,M[::-1],f[::-1]); f10=np.interp(0.1,M[::-1],f[::-1])
            a,b,A,fw2d,fwlsf,rr=wing_fit(ctr,prof)
            print("%s %-3s  MTF50 @ %.2f\"  MTF10 @ %.2f\"  MTF(12.9\")=%.3f MTF(6.47\")=%.4f | wings: b=%.2f a=%.3f FWHM2D=%.2f\" res=%.3f"%(
                nm,ch, 2*SCALE/f50, 2*SCALE/f10, at(12.936), at(6.468), b,a,fw2d,rr))
