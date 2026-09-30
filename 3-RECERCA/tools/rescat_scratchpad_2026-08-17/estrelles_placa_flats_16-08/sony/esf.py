import numpy as np, sys
sys.path.insert(0,"/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/sony")
from common import planes, SCALE

OFF={'R':(0.0,0.0),'G1':(0.5,0.0),'G2':(0.0,0.5),'B':(0.5,0.5)}  # (dx,dy) in half-res px

def coords(img,ch):
    h,w=img.shape
    dx,dy=OFF[ch]
    x=np.arange(w)+dx; y=np.arange(h)+dy
    return x,y

def fit_circle_pts(X,Y):
    A=np.c_[2*X,2*Y,np.ones(len(X))]; b=X**2+Y**2
    sol,*_=np.linalg.lstsq(A,b,rcond=None)
    cx,cy=sol[0],sol[1]; R=np.sqrt(sol[2]+cx**2+cy**2)
    return cx,cy,R

def limb_circle(img,ch,c0,rmin,rmax,nang=1440,iters=4):
    from scipy.ndimage import map_coordinates
    x,y=coords(img,ch); dx,dy=OFF[ch]
    cx,cy=c0
    ang=np.linspace(0,2*np.pi,nang,endpoint=False)
    for it in range(iters):
        r=np.arange(rmin,rmax,0.2)
        px=(cx+np.outer(np.cos(ang),r)-dx); py=(cy+np.outer(np.sin(ang),r)-dy)
        prof=map_coordinates(img,[py,px],order=1,mode='constant',cval=np.nan)
        g=np.gradient(prof,axis=1)
        idx=np.nanargmax(g,axis=1); redge=r[idx]
        good=np.isfinite(redge)
        for _ in range(6):
            X=cx+redge*np.cos(ang); Y=cy+redge*np.sin(ang)
            ncx,ncy,nR=fit_circle_pts(X[good],Y[good])
            res=np.hypot(X-ncx,Y-ncy)-nR
            s=np.std(res[good]); good=good&(np.abs(res)<2.5*s)
        cx,cy=ncx,ncy; rmin=nR-25; rmax=nR+25
    return cx,cy,nR,np.std(res[good]),good.sum()

def annulus_samples(img,ch,cx,cy,R,half=14.0):
    x,y=coords(img,ch)
    X,Y=np.meshgrid(x,y)
    d=np.hypot(X-cx,Y-cy)-R
    m=np.abs(d)<half
    az=np.arctan2(Y[m]-cy,X[m]-cx)
    return d[m],az,img[m]
