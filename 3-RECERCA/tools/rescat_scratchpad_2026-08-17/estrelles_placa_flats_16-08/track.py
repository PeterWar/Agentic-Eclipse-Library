import tifffile, numpy as np, sys, json, os
from scipy.signal import fftconvolve
def moon_center(g, R, ds=4):
    gd = np.log1p(np.clip(g[::ds, ::ds].astype(np.float32),0,None))
    Rd=R/ds; k=int(np.ceil(Rd+16))
    yy,xx=np.mgrid[-k:k+1,-k:k+1]; rr=np.hypot(yy,xx)
    K=np.zeros_like(rr,np.float32)
    ring=(rr>=Rd+1)&(rr<=Rd+6); disk=(rr<=Rd-6)
    K[ring]=1/ring.sum(); K[disk]=-1/disk.sum()
    sc=fftconvolve(gd,K[::-1,::-1],mode='same')
    m=np.zeros_like(sc,bool); b=int(Rd)+4; m[b:-b,b:-b]=True
    sc=np.where(m,sc,-1e9)
    iy,ix=np.unravel_index(np.argmax(sc),sc.shape)
    p=lambda a,b,c: 0.0 if (a-2*b+c)==0 else 0.5*(a-c)/(a-2*b+c)
    dy=p(sc[iy-1,ix],sc[iy,ix],sc[iy+1,ix]); dx=p(sc[iy,ix-1],sc[iy,ix],sc[iy,ix+1])
    return (ix+dx)*ds,(iy+dy)*ds,float(sc[iy,ix])
R=float(sys.argv[1]); out=[]
for p in sys.argv[2:]:
    g=tifffile.imread(p)[...,1]
    cx,cy,s=moon_center(g,R)
    out.append([os.path.basename(p),round(cx,2),round(cy,2),round(s,3)])
print(json.dumps(out))
