import numpy as np
from skyfield.api import load
from skyfield.data import hipparcos
L=1.7516; S=2.3548
with load.open(hipparcos.URL) as f: df=hipparcos.load_dataframe(f)
df=df[df['magnitude'].notnull()]
ra=df['ra_degrees'].values; dec=df['dec_degrees'].values; mag=df['magnitude'].values
sra,sdec=131.9672,17.8642; Rs=945.6/3600.
r1,d1=np.radians(sra),np.radians(sdec); r2,d2=np.radians(ra),np.radians(dec)
xi=np.cos(d2)*np.sin(r2-r1)/(np.sin(d1)*np.sin(d2)+np.cos(d1)*np.cos(d2)*np.cos(r2-r1))
eta=(np.cos(d1)*np.sin(d2)-np.sin(d1)*np.cos(d2)*np.cos(r2-r1))/(np.sin(d1)*np.sin(d2)+np.cos(d1)*np.cos(d2)*np.cos(r2-r1))
xi=np.degrees(xi)/Rs; eta=np.degrees(eta)/Rs; rr=np.hypot(xi,eta)

# ---- SNR model anchored on the 2026 measurement -------------------------------
# anchor: D=90mm, T=10.3s, FWHM=5.8", sky=9.15 mag/as^2, V=5.73 -> SNR=121, airmass 6.26 (ext 1.56 mag)
def snr(V,D_mm,T_s,fwhm,sky,ext_mag,thr=1.0):
    return 121.0*(D_mm/90.)**2*(T_s/10.3)**0.5*(5.8/fwhm)*10**(-0.4*(V-5.73))\
           *10**(0.4*(sky-9.15)/2)*10**(-0.4*(ext_mag-1.56))*thr
def sig_star(V,D_mm,T_s,fwhm,sky,ext,floor,thr=1.0):
    s=snr(V,D_mm,T_s,fwhm,sky,ext,thr)
    return np.hypot(0.601*fwhm/s, floor), s

def sigma_eps(x,y,sig,extra_terms=0):
    r=np.hypot(x,y); n=len(r); w=1/sig**2
    dxi=L*(x/r)/r; deta=L*(y/r)/r
    base=[(np.ones(n),0),(x,0),(y,0),(np.ones(n),1),(x,1),(y,1)]
    if extra_terms:
        r2=x*x+y*y
        for p in (x*x,x*y,y*y,x*r2,y*r2):
            base+=[(p,0),(p,1)]
    A=np.zeros((2*n,1+len(base))); A[:n,0]=dxi; A[n:,0]=deta
    for j,(v,ax) in enumerate(base):
        if ax==0: A[:n,1+j]=v
        else: A[n:,1+j]=v
    W=np.concatenate([w,w]); F=A.T@(A*W[:,None])
    return np.sqrt(np.linalg.pinv(F)[0,0])

configs=[
 # name                          D    T    FWHM  sky   ext  floor  halffield(deg) snrmin
 ("0. 2026 León, as flown (B)",  90, 30.9, 5.8,  9.15, 1.56, 0.50, 1.39, 5),
 ("1. same gear, Luxor 2027",    90, 300., 5.8, 12.20, 0.25, 0.50, 1.39, 8),
 ("1b. same gear + red filter + Gaia + distortion cal", 90,300.,5.8,12.20,0.25,0.08,1.39,8),
 ("2. 100mm apo, mono, r', 3.0\" FWHM, good focus",100,300.,3.0,12.20,0.25,0.05,1.90,8),
 ("3. 130mm apo, mono, r', 2.5\" FWHM, 3.0 deg fld",130,300.,2.5,12.20,0.25,0.03,2.60,8),
 ("4. 150mm apo, mono, r', 2.5\" FWHM, 3.5 deg fld",150,320.,2.5,12.20,0.25,0.02,3.50,8),
 ("5. as 4 but sloppy: 5\" FWHM, no filter, Tycho-2, cubic-only distortion",
                                150,320., 5.0,12.20,0.25,0.35, 3.50, 8),
]
print(f"{'configuration':62s} {'Nstars':>6s} {'sig(eps)':>9s} {'GR sigma':>9s} {'E-vs-N':>7s}  median sig*")
for nm,D,T,fw,sky,ext,floor,hf,smin in configs:
    hr=hf/Rs
    m=(rr>=1.6)&(rr<=hr)&(np.abs(xi)<=hr*1.5)&(np.abs(eta)<=hr)
    V=mag[m]; x=xi[m]; y=eta[m]
    sg,sn=sig_star(V,D,T,fw,sky,ext,floor)
    keep=sn>=smin
    if keep.sum()<6: print(f"{nm:62s}  too few"); continue
    se=sigma_eps(x[keep],y[keep],sg[keep])
    print(f"{nm:62s} {keep.sum():6d} {se:9.3f} {1/se:8.1f}s {0.5/se:6.1f}s   {np.median(sg[keep]):.3f}\"")
print("\n(Hipparcos only: real counts to V=11 are ~4-6x larger, improving sigma(eps) by ~2-2.5x)")
