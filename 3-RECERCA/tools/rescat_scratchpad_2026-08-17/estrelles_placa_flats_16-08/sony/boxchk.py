import numpy as np, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
from common import planes
from esf import limb_circle
def auto_c0(P):
    g=P['G1']; h,w=g.shape
    d=g[:h//8*8,:w//8*8].reshape(h//8,8,w//8,8).mean(axis=(1,3))
    thr=np.percentile(d,99.9)*0.05
    ys,xs=np.nonzero(d>thr); return (np.average(xs,weights=d[ys,xs])*8,np.average(ys,weights=d[ys,xs])*8)
for nm in ["DSC06979.ARW","DSC06981.ARW","DSC07000.ARW","DSC07002.ARW"]:
    P=planes(nm); c0=auto_c0(P)
    cx,cy,R,_,_=limb_circle(P['G1'],'G1',c0,146,159)
    print(nm,"R=%.2f"%R, "globalmax=%.0f"%P['G1'].max())
    for rr,adeg,lab in [(1.05,70,"prom70"),(1.05,90,"prom90"),(1.05,222,"prom222"),(1.35,285,"cor285"),(1.20,180,"cor180"),(0.55,0,"inside")]:
        a=np.radians(adeg); px=cx+rr*R*np.cos(a); py=cy+rr*R*np.sin(a)
        n=64; x0=int(px)-n//2; y0=int(py)-n//2
        for ch in ['G1','R']:
            b=P[ch][y0:y0+n,x0:x0+n]
            print("   %-8s %-2s max=%8.0f mean=%8.1f"%(lab,ch,b.max(),b.mean()))
