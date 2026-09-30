import numpy as np, sys
sys.path.insert(0,"/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/sony")
from common import planes, SCALE
from esf import limb_circle, annulus_samples
from viaA2 import esf_build
from viaA3 import fit, moffat_fwhm2d, moffat_fwhm_lsf
nm="DSC06983.ARW"; ch='G1'
P=planes(nm); img=P[ch]
cx,cy,R,rms,n=limb_circle(img,ch,(1834.6,1741.2),80,320)
d,az,v=annulus_samples(img,ch,cx,cy,R)
print("circle-fit residual rms (half-px) =",round(rms,3))
for nsec in [1,12,36,72,144,240,360]:
    ctr,prof,cnt,ok,tot,diag=esf_build(d,az,v,nsec=nsec)
    r,x,y=fit(ctr,prof)
    a,b=r.x[4],r.x[5]
    f=moffat_fwhm_lsf(a,b)
    print("nsec=%3d  arc=%.1f px  sec_used=%3d  shift_rms=%.3f  FWHM_LSF=%.2f\"  resid=%.4f"%(
        nsec, 2*np.pi*R/nsec, len(ok), np.std(tot[ok]) if len(ok) else 0, f*2*SCALE, np.sqrt(np.mean(r.fun**2))))
