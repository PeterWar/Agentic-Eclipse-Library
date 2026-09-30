import numpy as np, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
from common import planes, SCALE
from esf import limb_circle
def auto_c0(P):
    g=P['G1']; h,w=g.shape
    d=g[:h//8*8,:w//8*8].reshape(h//8,8,w//8,8).mean(axis=(1,3))
    thr=np.percentile(d,99.9)*0.05
    ys,xs=np.nonzero(d>thr); return (np.average(xs,weights=d[ys,xs])*8,np.average(ys,weights=d[ys,xs])*8)
print("frame          ch    cx        cy        R        | dx vs R   dy vs R  (full-res px)   (arcsec)")
for nm in ["DSC06983.ARW","DSC06995.ARW","DSC06998.ARW","DSC06981.ARW","DSC07002.ARW","DSC07005.ARW","DSC06975.ARW","DSC06978.ARW","DSC06986.ARW","DSC06992.ARW"]:
    P=planes(nm); c0=auto_c0(P); ref=None
    for ch in ['R','G1','G2','B']:
        cx,cy,R,rms,n=limb_circle(P[ch],ch,c0,146,159)
        if ref is None: ref=(cx,cy); d=(0,0)
        else: d=(cx-ref[0],cy-ref[1])
        print("%-13s %-3s %9.3f %9.3f %8.3f | %+7.3f %+7.3f      %+6.2f %+6.2f"%(
            nm,ch,cx,cy,R,d[0]*2,d[1]*2,d[0]*2*SCALE,d[1]*2*SCALE))
