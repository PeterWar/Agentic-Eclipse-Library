import numpy as np, sys
sys.path.insert(0,"/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/sony")
from common import planes
from esf import limb_circle, annulus_samples
from viaA import build_esf
nm="DSC06983.ARW"; P=planes(nm); ch='G1'
img=P[ch]
cx,cy,R,rms,n=limb_circle(img,ch,(1834.6,1741.2),80,320)
d,az,v=annulus_samples(img,ch,cx,cy,R)
ctr,prof,cnt,ks,info,shift,dd,norm,ok,sec=build_esf(d,az,v)
print("shifts: min %.3f max %.3f rms %.3f"%(shift[ks].min(),shift[ks].max(),shift[ks].std()))
cs=[info[s][1] for s in ks]
print("contrast per sector: median %.0f min %.0f max %.0f"%(np.median(cs),min(cs),max(cs)))
print("counts per bin median",np.median(cnt))
for i in range(0,len(ctr),4):
    if -8<=ctr[i]<=8:
        print("%7.2f %9.4f %5d"%(ctr[i],prof[i],cnt[i]))
