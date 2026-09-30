import numpy as np, sys
sys.path.insert(0,"/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/sony")
from core import prep, build, fwhm_of, esf_widths
for nm in ["DSC06983.ARW","DSC06995.ARW"]:
  for ch in ['G1','R','B']:
    pr=prep(nm,ch)
    ctr,prof,cnt=build(pr)
    f,f2d,res,r=fwhm_of(ctr,prof)
    w=esf_widths(ctr,prof)
    print("%s %s ALL  FWHM_LSF=%.2f  10-90=%.2f  25-75=%.2f"%(nm,ch,f,w['0.1-0.9'],w['0.25-0.75']))
    az=pr['az']
    for k in range(8):
        a0=-np.pi+k*np.pi/4; a1=a0+np.pi/4
        m=(az>=a0)&(az<a1)
        c2,p2,n2=build(pr,m)
        try:
            f2,_,rr,_=fwhm_of(c2,p2); w2=esf_widths(c2,p2)
            print("    az %4d-%4d deg  FWHM_LSF=%.2f  10-90=%.2f  n=%d"%(np.degrees(a0),np.degrees(a1),f2,w2['0.1-0.9'],m.sum()))
        except Exception as e: print("    az",k,"fail",e)
