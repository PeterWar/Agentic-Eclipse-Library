import numpy as np, sys
sys.path.insert(0,"/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/sony")
from common import plane
from scipy.ndimage import map_coordinates

def radial_sample(img, cx, cy, ang, r):
    x=cx+np.outer(np.cos(ang),r); y=cy+np.outer(np.sin(ang),r)
    return map_coordinates(img,[y,x],order=1,mode='constant',cval=np.nan)

def fit_limb(img, cx, cy, rmin, rmax, nang=720, refine=3):
    ang=np.linspace(0,2*np.pi,nang,endpoint=False)
    for it in range(refine):
        r=np.arange(rmin,rmax,0.25)
        prof=radial_sample(img,cx,cy,ang,r)
        # gradient along r
        g=np.gradient(prof,axis=1)
        idx=np.nanargmax(g,axis=1)
        redge=r[idx]
        good=np.isfinite(redge)
        # robust circle fit: x = cx + redge cos, etc  -> algebraic
        for _ in range(5):
            X=cx+redge*np.cos(ang); Y=cy+redge*np.sin(ang)
            A=np.c_[2*X[good],2*Y[good],np.ones(good.sum())]
            b=(X[good]**2+Y[good]**2)
            sol,*_=np.linalg.lstsq(A,b,rcond=None)
            ncx,ncy=sol[0],sol[1]; nR=np.sqrt(sol[2]+ncx**2+ncy**2)
            res=np.hypot(X-ncx,Y-ncy)-nR
            s=np.nanstd(res[good])
            good=good&(np.abs(res)<2.5*s)
        cx,cy=ncx,ncy
        rmin=nR-40; rmax=nR+40
    return cx,cy,nR,res,good,ang,redge

if __name__=="__main__":
    for nm,c0 in [("DSC06983.ARW",(1817,1696)),("DSC06995.ARW",(1944,1369)),("DSC06998.ARW",None)]:
        g=plane(nm)
        if c0 is None:
            h,w=g.shape
            d=g[:h//8*8,:w//8*8].reshape(h//8,8,w//8,8).mean(axis=(1,3))
            thr=np.percentile(d,99.9)*0.05
            ys,xs=np.nonzero(d>thr); c0=(np.average(xs,weights=d[ys,xs])*8,np.average(ys,weights=d[ys,xs])*8)
        cx,cy,R,res,good,ang,redge=fit_limb(g,c0[0],c0[1],80,320)
        print(nm,"center=(%.2f,%.2f) R=%.3f px(half) rms=%.3f  used=%d/%d"%(cx,cy,R,np.nanstd(res[good]),good.sum(),len(ang)))
