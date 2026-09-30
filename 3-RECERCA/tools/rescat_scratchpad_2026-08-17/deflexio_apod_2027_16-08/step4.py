import numpy as np, eb_core as E
rng=np.random.default_rng(9); RS=E.RSUN27

# ---------------------------------------------------------------- leakage
print("="*80)
print("LEAKAGE OF A COHERENT *RADIAL* SYSTEMATIC INTO epsilon")
print("  displacement d(r) = A * (r/r_edge)^n , radial, amplitude A at the field edge")
print("  (the deflection template itself is n = -1)")
print("="*80)
def leak(hw,hh,Vlim,n,order,trials=40,rmin=2.0):
    out=[]
    for _ in range(trials):
        x,y,V=E.sample_rect(hw,hh,Vlim,rng,rmin_rho=rmin)
        r=np.hypot(x,y); redge=r.max(); ux,uy=x/r,y/r
        prof=(r/redge)**n
        b=E.bias_eps(x,y,1.0,(prof*ux,prof*uy),order=order)
        out.append(b)
    return np.median(out)
hdr=f"{'pattern':16s}"+"".join(f"{s:>16s}" for s in ["A: 1st order","A: 3rd order","B: 1st order","B: 3rd order"])
print(hdr)
for n,name in [(-2,'r^-2'),(-1,'r^-1 (=signal)'),(0,'constant'),(1,'r (=scale)'),
               (2,'r^2'),(3,'r^3 (cubic)'),(5,'r^5')]:
    row=f"{name:16s}"
    for hw,hh in [(7.14/2,4.77/2),(4.17/2,2.78/2)]:
        for o in [1,3]:
            row+=f"{leak(hw,hh,11.0,n,o):16.3f}"
    print(row)
print("\n  read as: Delta(epsilon) = (coefficient) x A[arcsec].  'r^1' is the plate scale")
print("  itself, so it is absorbed exactly (coefficient 0) whenever scale is a free")
print("  parameter -- but NOT if you import a scale from a calibration frame.")

# ------------------------------------------------- coronal-gradient bias
print("\n"+"="*80)
print("CORONAL BACKGROUND GRADIENT -> CENTROID BIAS (numerical PSF fit)")
print("="*80)
from scipy.optimize import least_squares
def coronal_bias(rho, fwhm, V, area, t, thru, msky, model='plane', box=None):
    sg=fwhm/2.3548
    if box is None: box=int(np.ceil(4*sg))
    K=E.K_ANCHOR*(area/E.A0)*(t/E.T0)*thru
    F=K*10**(-0.4*V)
    # local background surface brightness and its radial log-gradient
    r_as=rho*RS
    def Bsb(rr): return K*10**(-0.4*E.m_bg(rr/RS, msky))       # e- per arcsec^2
    n=2*box+1
    gx=np.arange(n)-box                      # arcsec grid, 1 arcsec sampling
    X,Y=np.meshgrid(gx,gx)                   # X points AWAY from the Sun
    Rr=r_as+X                                # distance from Sun centre
    bg=Bsb(Rr)
    star=F/(2*np.pi*sg**2)*np.exp(-((X)**2+(Y)**2)/(2*sg**2))
    img=star+bg
    def resid(p):
        x0,y0,f,b0,bx,by=p
        m=f/(2*np.pi*sg**2)*np.exp(-((X-x0)**2+(Y-y0)**2)/(2*sg**2))+b0
        if model=='plane': m=m+bx*X+by*Y
        return (img-m).ravel()
    p0=[0,0,F,bg.mean(),0,0]
    s=least_squares(resid,p0,method='lm',xtol=1e-14,ftol=1e-14)
    return s.x[0]      # positive = pushed AWAY from the Sun
thru=10**(0.4*(0.37*6.03-0.20*1.011))*1.30
print(f"{'r(Rsun)':>8} {'V':>5} {'const bkg':>12} {'fitted plane':>14}   (arcsec, + = outward)")
for rho in [2.0,2.5,3.0,4.0,6.0,8.0]:
    for V in [9.0,11.0]:
        b1=coronal_bias(rho,3.8,V,63.3,240,thru,12.0,'const')
        b2=coronal_bias(rho,3.8,V,63.3,240,thru,12.0,'plane')
        print(f"{rho:8.1f} {V:5.1f} {b1:12.4f} {b2:14.5f}")
