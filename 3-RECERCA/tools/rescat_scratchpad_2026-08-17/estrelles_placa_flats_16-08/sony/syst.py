import numpy as np, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
from common import SCALE
from core import prep, build
from viaA3 import fit, moffat_fwhm_lsf, moffat_fwhm2d, forward
out=[]
for nm,ch in [("DSC06983.ARW",'G1'),("DSC06981.ARW",'R'),("DSC07002.ARW",'G2')]:
    base=None
    for kw,lab in [ (dict(),"base"),
                    (dict(nsec=36),"nsec=36"), (dict(nsec=240),"nsec=240"),
                    (dict(inner=(-10,-3),outer=(3,10)),"finestres 3-10"),
                    (dict(inner=(-14,-6),outer=(6,14),half=16),"finestres 6-14"),
                    (dict(align_iters=1),"sense alineacio"),
                    (dict(binw=0.10),"bins 0,10 px")]:
        pr=prep(nm,ch,**kw); c,p,n=build(pr)
        for fr in ([9.0] if lab!="base" else [6.0,8.0,9.0,11.0]):
            r,x,y=fit(c,p,fitrange=fr)
            a,b=r.x[4],r.x[5]
            f=moffat_fwhm_lsf(a,b)*2*SCALE; f2=moffat_fwhm2d(a,b)*2*SCALE
            print("%-13s %-3s %-18s fit|d|<%4.1f  FWHM_LSF=%.2f\" FWHM_2D=%.2f\" b=%.1f resid=%.4f"%(nm,ch,lab,fr,f,f2,b,np.sqrt(np.mean(r.fun**2))))
