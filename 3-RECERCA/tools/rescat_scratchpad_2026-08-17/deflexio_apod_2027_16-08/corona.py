import numpy as np
np.random.seed(5)
RSUN=945.6
ZP_e=10**(14.21/2.5)*5.08          # e-/s for V=0, Leon ZP (train B)
EXT=10**(0.4*0.20*(6.02-1.011))    # Luxor vs Leon extinction gain
PIX=2.15                            # arcsec/px
FWHM=3.5; SG=FWHM/2.3548
FULLWELL=16383*5.08                 # e- (ISO100 R6 III)

def mu(r):
    rg=np.array([1.2,1.5,2,3,5,8,10,15,20]); mg=np.array([4.6,5.6,6.9,8.4,10.4,11.8,12.5,13.7,14.4])
    return np.interp(r,rg,mg)
def Bsurf(r):  return ZP_e*10**(-0.4*mu(r))*EXT      # e-/s/arcsec^2
def Fstar(V):  return ZP_e*10**(-0.4*V)*EXT          # e-/s

print("="*76)
print("SATURATION LADDER — the corona, not the stars, sets the frame time")
print("="*76)
print(f"{'r/Rsun':>7} {'mu':>7} {'e-/s/px':>10} {'t_sat(75%FW)':>13} {'frames in 263s':>15}")
for r in [1.2,1.5,1.75,2,2.5,3,4,6,8,12]:
    epx=Bsurf(r)*PIX**2
    ts=0.75*FULLWELL/epx
    print(f"{r:7.2f} {mu(r):7.2f} {epx:10.0f} {ts:13.2f} {263/min(ts,10.3):15.0f}")
print("  a V=3.94 star (delta Cnc) peak pixel:",
      f"{Fstar(3.94)/(2*np.pi*(SG/PIX)**2):,.0f} e-/s -> saturates in {0.75*FULLWELL/(Fstar(3.94)/(2*np.pi*(SG/PIX)**2)):.2f} s")

print()
print("="*76)
print("READ NOISE IS IRRELEVANT: stacking many short frames costs ~nothing")
print("="*76)
Aeff=4*np.pi*SG**2; npx=Aeff/PIX**2
for r,t,rn in [(1.5,0.5,2.72*5.08),(2.0,1.5,1.05*5.08),(3.0,4.0,1.05*5.08),(8.0,10.3,1.05*5.08)]:
    n=263/t
    var_rd=n*rn**2*npx
    var_sky=Bsurf(r)*Aeff*263
    print(f"  r={r:4.1f}  t={t:4.1f}s  n={n:5.0f}  read-noise var {var_rd:12.3e}"
          f"  sky-shot var {var_sky:12.3e}  ratio {var_rd/var_sky:8.2e}")

print()
print("="*76)
print("CORONAL-GRADIENT CENTROID BIAS — simulated, four methods")
print("="*76)
def sim(r0, V, method, T=263.0, tframe=None, ntrial=400):
    """one star on the real coronal gradient; returns bias & scatter in arcsec"""
    half=12                                   # px half-window
    yy,xx=np.mgrid[-half:half+1,-half:half+1]
    B0=Bsurf(r0)*PIX**2*T                     # e- per px from corona at r0
    # local log-gradient of the corona
    d=1e-3; n_idx=(mu(r0+d)-mu(r0-d))/(2*d)   # mag per Rsun
    glog=-0.921*n_idx/RSUN                    # d ln B / d arcsec  (radial)
    F=Fstar(V)*T
    sgpx=SG/PIX
    out=[]
    for _ in range(ntrial):
        dx,dy=np.random.uniform(-.5,.5,2)
        star=F/(2*np.pi*sgpx**2)*np.exp(-((xx-dx)**2+(yy-dy)**2)/(2*sgpx**2))
        # corona: exponential in the radial direction (+x), exact not linearised
        bg=B0*np.exp(glog*PIX*xx)
        img=np.random.poisson(np.maximum(star+bg,0)).astype(float)
        if method=='const':            # subtract an annulus median, plain 1st moment
            ann=(np.hypot(xx,yy)>8)&(np.hypot(xx,yy)<12)
            im=img-np.median(img[ann]); ap=np.hypot(xx,yy)<=3.5*sgpx
        elif method=='plane':          # fit a local PLANE in the annulus, then 1st moment
            ann=(np.hypot(xx,yy)>8)&(np.hypot(xx,yy)<12)
            A=np.c_[np.ones(ann.sum()),xx[ann],yy[ann]]
            c=np.linalg.lstsq(A,img[ann],rcond=None)[0]
            im=img-(c[0]+c[1]*xx+c[2]*yy); ap=np.hypot(xx,yy)<=3.5*sgpx
        elif method=='model':          # subtract a smooth coronal model (exact form), 1st moment
            im=img-bg; ap=np.hypot(xx,yy)<=3.5*sgpx
        elif method=='psf_plane':      # simultaneous PSF + local plane fit (gaussian-weighted)
            ann=(np.hypot(xx,yy)>8)&(np.hypot(xx,yy)<12)
            A=np.c_[np.ones(ann.sum()),xx[ann],yy[ann]]
            c=np.linalg.lstsq(A,img[ann],rcond=None)[0]
            im=img-(c[0]+c[1]*xx+c[2]*yy)
            w=np.exp(-(xx**2+yy**2)/(2*(1.5*sgpx)**2)); im=im*w; ap=np.hypot(xx,yy)<=6
        s=im[ap].sum()
        cx=(im[ap]*xx[ap]).sum()/s; cy=(im[ap]*yy[ap]).sum()/s
        out.append(((cx-dx)*PIX,(cy-dy)*PIX))
    o=np.array(out)
    return o[:,0].mean(), o[:,0].std()/np.sqrt(len(o)), o[:,0].std()

print(f"{'r':>5} {'V':>4} {'method':>10} {'bias_radial(\")':>15} {'+-':>7} {'scatter(\")':>11}")
for r0 in [2.0,3.0,5.0]:
    for V in [9.0]:
        for meth in ['const','plane','model','psf_plane']:
            b,e,s=sim(r0,V,meth)
            print(f"{r0:5.1f} {V:4.1f} {meth:>10} {b:15.4f} {e:7.4f} {s:11.4f}")
