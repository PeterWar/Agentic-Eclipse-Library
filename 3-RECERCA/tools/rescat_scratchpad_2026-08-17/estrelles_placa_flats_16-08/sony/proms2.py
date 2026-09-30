import numpy as np, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
from common import planes, SCALE
from esf import limb_circle, OFF
from scipy.ndimage import map_coordinates
def auto_c0(P):
    g=P['G1']; h,w=g.shape
    d=g[:h//8*8,:w//8*8].reshape(h//8,8,w//8,8).mean(axis=(1,3))
    thr=np.percentile(d,99.9)*0.05
    ys,xs=np.nonzero(d>thr); return (np.average(xs,weights=d[ys,xs])*8,np.average(ys,weights=d[ys,xs])*8)
for nm in sys.argv[1:]:
    P=planes(nm); c0=auto_c0(P)
    cx,cy,R,rms,n=limb_circle(P['G1'],'G1',c0,135,172)
    ang=np.linspace(0,2*np.pi,360,endpoint=False)
    r=np.arange(R+0.7,R+4.0,0.2)
    o={}
    for ch in ['R','G1','B']:
        dx,dy=OFF[ch]
        px=cx+np.outer(np.cos(ang),r)-dx; py=cy+np.outer(np.sin(ang),r)-dy
        o[ch]=map_coordinates(P[ch],[py,px],order=1,mode='constant',cval=np.nan).mean(axis=1)
    rg=o['R']/np.maximum(o['G1'],1)
    k=np.ones(5)/5
    rgs=np.convolve(np.r_[rg[-5:],rg,rg[:5]],k,'same')[5:-5]
    med=np.median(rgs)
    print("%s R=%.2f rms=%.3f  medR/G=%.3f  max=%d"%(nm,R,rms,med,P['G1'].max()))
    hot=np.nonzero(rgs>med*1.35)[0]
    # group
    groups=[]
    if len(hot):
        cur=[hot[0]]
        for i in hot[1:]:
            if i-cur[-1]<=3: cur.append(i)
            else: groups.append(cur); cur=[i]
        groups.append(cur)
    for g in groups:
        if len(g)<2: continue
        a0,a1=g[0],g[-1]
        print("   PROM az %4d..%4d deg  R/G peak %.2f  Rflux %.0f"%(a0,a1,rgs[g].max(),o['R'][g].max()))
