import numpy as np, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
from core import prep, build, fwhm_of
for nm,ch in [("DSC06986.ARW",'B'),("DSC06989.ARW",'B'),("DSC06992.ARW",'B'),("DSC06983.ARW",'B')]:
    pr=prep(nm,ch)
    c,p,n=build(pr)
    try: f,f2,rr,r=fwhm_of(c,p)
    except Exception: f=np.nan
    print("%-14s %s  global FWHM_LSF=%.2f\"  sect=%d"%(nm,ch,f,len(pr['ok_sec'])))
    az=pr['az']; vals=[]
    for k in range(6):
        a0=-np.pi+k*np.pi/3; a1=a0+np.pi/3
        m=(az>=a0)&(az<a1)
        c2,p2,_=build(pr,m)
        try:
            f2b,_,_,_=fwhm_of(c2,p2); vals.append((int(np.degrees(a0)),f2b))
        except Exception: vals.append((int(np.degrees(a0)),np.nan))
    print("     ", "  ".join("%d:%.1f"%v for v in vals))
