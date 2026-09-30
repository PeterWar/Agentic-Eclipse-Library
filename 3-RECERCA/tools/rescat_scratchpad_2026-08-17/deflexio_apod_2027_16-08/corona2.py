import numpy as np
from scipy.ndimage import gaussian_filter
np.random.seed(9)
RSUN=945.6; ZP_e=10**(14.21/2.5)*5.08; EXT=10**(0.4*0.20*(6.02-1.011))
PIX=2.15; FWHM=3.5; SG=FWHM/2.3548; SGP=SG/PIX
def mu(r):
    rg=np.array([1.2,1.5,2,3,5,8,10,15,20]); mg=np.array([4.6,5.6,6.9,8.4,10.4,11.8,12.5,13.7,14.4])
    return np.interp(r,rg,mg)
def Bs(r): return ZP_e*10**(-0.4*mu(r))*EXT
def Fs(V): return ZP_e*10**(-0.4*V)*EXT

def run(r0,V,method,T=263.,ap_fac=2.5,ntr=600,streamer=False):
    half=14; yy,xx=np.mgrid[-half:half+1,-half:half+1]
    d=1e-3; nidx=(mu(r0+d)-mu(r0-d))/(2*d); glog=-0.921*nidx/RSUN
    B0=Bs(r0)*PIX**2*T; F=Fs(V)*T; out=[]
    for _ in range(ntr):
        dx,dy=np.random.uniform(-.5,.5,2)
        star=F/(2*np.pi*SGP**2)*np.exp(-((xx-dx)**2+(yy-dy)**2)/(2*SGP**2))
        bg=B0*np.exp(glog*PIX*xx)
        if streamer: bg=bg*(1+0.35*np.tanh((yy-3)/4.0))     # streamer edge crossing
        img=np.random.poisson(np.maximum(star+bg,0)).astype(float)
        R=np.hypot(xx,yy); ann=(R>9)&(R<13); ap=R<=ap_fac*SGP
        if method=='const':
            im=img-np.median(img[ann])
        elif method=='plane':
            A=np.c_[np.ones(ann.sum()),xx[ann],yy[ann]]
            c=np.linalg.lstsq(A,img[ann],rcond=None)[0]; im=img-(c[0]+c[1]*xx+c[2]*yy)
        elif method=='quad':
            A=np.c_[np.ones(ann.sum()),xx[ann],yy[ann],xx[ann]**2,xx[ann]*yy[ann],yy[ann]**2]
            c=np.linalg.lstsq(A,img[ann],rcond=None)[0]
            im=img-(c[0]+c[1]*xx+c[2]*yy+c[3]*xx**2+c[4]*xx*yy+c[5]*yy**2)
        elif method=='bruns':                # blur the frame, subtract  (Bruns 2017 §2.6)
            im=img-gaussian_filter(img,10.0)
        elif method=='bruns+plane':
            t=img-gaussian_filter(img,10.0)
            A=np.c_[np.ones(ann.sum()),xx[ann],yy[ann]]
            c=np.linalg.lstsq(A,t[ann],rcond=None)[0]; im=t-(c[0]+c[1]*xx+c[2]*yy)
        s=im[ap].sum()
        out.append(((im[ap]*xx[ap]).sum()/s-dx, (im[ap]*yy[ap]).sum()/s-dy))
    o=np.array(out)*PIX
    return o[:,0].mean(), o[:,0].std()/np.sqrt(ntr), o[:,0].std()

print("="*90)
print("BACKGROUND MODELS: radial centroid bias (arcsec). aperture = 2.5 sigma_PSF")
print("="*90)
print(f"{'r/Rsun':>7} {'method':>13} {'bias':>10} {'+-':>7} {'scatter':>9}   [V=9, 263 s]")
for r0 in [1.5,2.0,3.0,5.0,8.0]:
    for m in ['const','plane','quad','bruns','bruns+plane']:
        b,e,s=run(r0,9.0,m)
        print(f"{r0:7.1f} {m:>13} {b:10.4f} {e:7.4f} {s:9.4f}")
    print()

print("="*90); print("APERTURE SIZE: bias ~ R^4 for a plain moment on a gradient (r=2.5 Rsun, V=9)")
print("="*90)
for af in [1.5,2.0,2.5,3.0,4.0]:
    bc,_,sc=run(2.5,9.0,'const',ap_fac=af); bp,_,sp=run(2.5,9.0,'plane',ap_fac=af)
    print(f"  aperture {af:4.1f} sigma ({af*SG:4.1f}\") : const {bc:9.4f}\"  plane {bp:8.4f}\"  scatter(plane) {sp:.4f}\"")

print()
print("="*90); print("STREAMER EDGE (35% azimuthal step across the window), r=3 Rsun, V=9")
print("="*90)
for m in ['const','plane','quad']:
    b,e,s=run(3.0,9.0,m,streamer=True)
    print(f"  {m:>6}: radial bias {b:8.4f} +- {e:.4f}  scatter {s:.4f}")

# ---- leakage of a radial bias pattern b(r) into epsilon ----
print()
print("="*90); print("LEAKAGE INTO EPSILON of a radial systematic b(r) = A*(r/2)^-p, 2-15 Rsun")
print("="*90)
LDEF=1.7516
r=np.sqrt(np.random.uniform(2**2,15**2,60000)); th=np.random.uniform(0,2*np.pi,len(r))
x,y=r*np.cos(th),r*np.sin(th)
def leak(p,order=1):
    b=(r/2.0)**(-p)                                 # radial bias, unit amplitude at r=2
    # project onto epsilon after marginalising the plate model of given order
    Rn=r.max(); cols=[np.ones_like(x)]
    X,Y=x/Rn,y/Rn
    for o in range(1,order+1):
        for i in range(o+1): cols.append(X**(o-i)*Y**i)
    M=np.array(cols).T; n,m=M.shape; Z=np.zeros((n,m))
    Jx=np.hstack([M,Z]); Jy=np.hstack([Z,M])
    de_x=LDEF/r*(x/r); de_y=LDEF/r*(y/r)
    Jx=np.hstack([Jx,de_x[:,None]]); Jy=np.hstack([Jy,de_y[:,None]])
    dxb=b*(x/r); dyb=b*(y/r)
    J=np.vstack([Jx,Jy]); d=np.concatenate([dxb,dyb])
    sol=np.linalg.lstsq(J,d,rcond=None)[0]
    return sol[-1]
print(f"{'p':>5} {'shape':>22} {'d eps / (1\" at 2Rsun)':>24} {'3rd-order model':>17}")
for p,lab in [(1.0,'1/r  (= deflection)'),(2.0,'1/r^2'),(3.0,'1/r^3'),(4.65,'1/r^4.65 (measured)'),(0.0,'constant inward'),(-1.0,'r (= plate scale)')]:
    print(f"{p:5.2f} {lab:>22} {leak(p,1):24.4f} {leak(p,3):17.4f}")
