import numpy as np
from skyfield.api import load
from skyfield.data import hipparcos
L=1.7516
with load.open(hipparcos.URL) as f: df=hipparcos.load_dataframe(f)
df=df[df['magnitude'].notnull()]
ra=df['ra_degrees'].values; dec=df['dec_degrees'].values; mag=df['magnitude'].values
sra,sdec=131.9672,17.8642; Rs=945.6/3600.
r1,d1=np.radians(sra),np.radians(sdec); r2,d2=np.radians(ra),np.radians(dec)
den=np.sin(d1)*np.sin(d2)+np.cos(d1)*np.cos(d2)*np.cos(r2-r1)
xi=np.degrees(np.cos(d2)*np.sin(r2-r1)/den)/Rs
eta=np.degrees((np.cos(d1)*np.sin(d2)-np.sin(d1)*np.cos(d2)*np.cos(r2-r1))/den)/Rs
rr=np.hypot(xi,eta)

def bias_eps(x,y,pattern,amp_at_edge,order_fit=1):
    """how much of a smooth radial distortion residual leaks into epsilon"""
    r=np.hypot(x,y); rmax=r.max(); n=len(r)
    ur,vr=x/r,y/r
    if pattern=="r3": g=(r/rmax)**3
    elif pattern=="r5": g=(r/rmax)**5
    elif pattern=="r2": g=(r/rmax)**2
    dx=amp_at_edge*g*ur; dy=amp_at_edge*g*vr        # the systematic displacement field
    tx=L*ur/r; ty=L*vr/r                            # deflection template
    base=[(np.ones(n),0),(x,0),(y,0),(np.ones(n),1),(x,1),(y,1)]
    if order_fit>=2:
        for p in (x*x,x*y,y*y): base+=[(p,0),(p,1)]
    if order_fit>=3:
        r2_=x*x+y*y
        for p in (x*r2_,y*r2_,x**3,y**3,x*x*y,x*y*y): base+=[(p,0),(p,1)]
    A=np.zeros((2*n,1+len(base))); A[:n,0]=tx; A[n:,0]=ty
    for j,(v,ax) in enumerate(base):
        if ax==0: A[:n,1+j]=v
        else: A[n:,1+j]=v
    d=np.concatenate([dx,dy])
    sol=np.linalg.lstsq(A,d,rcond=None)[0]
    return sol[0]

for hf,lab in [(1.4,"1.4 deg half-field (VSD90SS-class)"),(2.6,"2.6 deg"),(3.5,"3.5 deg")]:
    hr=hf/Rs
    m=(rr>=1.6)&(rr<=hr)&(mag<=10)
    x,y=xi[m],eta[m]
    print(f"\n{lab}: {m.sum()} stars, r = {np.hypot(x,y).min():.1f}-{np.hypot(x,y).max():.1f} Rsun")
    for pat in ("r2","r3","r5"):
        for of in (1,2,3):
            b=bias_eps(x,y,pat,1.0,of)     # per 1 arcsec of residual at the field edge
            print(f"   {pat} radial residual, plate model order {of}: "
                  f"d(eps) = {b:+.4f} per arcsec at edge  -> "
                  f"20 mas residual gives {abs(b)*0.020*100:.2f}% ; 100 mas gives {abs(b)*0.100*100:.1f}%")
