import numpy as np
# Refraction: use the standard integral-free Saemundsson/Bennett + a rigorous n(lambda,P,T)
def n_minus_1(lam_um, P_hPa, T_C, RH=0.3):
    # Ciddor-lite / Edlen 1966
    s2 = 1.0/lam_um**2
    n_s = 1e-8*(8342.13 + 2406030/(130-s2) + 15997/(38.9-s2))  # standard air 15C 101325Pa
    # scale to P,T
    T = T_C+273.15
    f = (P_hPa*100/101325.0)*(288.15/T)
    nm1 = n_s*f
    # water vapour correction (small)
    return nm1

def R_arcsec(z_deg, P=1013.25, T=15.0, lam=0.55):
    """refraction using R = k tan z - k' tan^3 z style w/ true n; good to ~z=75.
       For larger z use Saemundsson empirical (which folds in curvature)."""
    nm1 = n_minus_1(lam,P,T)
    k = nm1*206265.0
    z = np.radians(z_deg)
    return k*np.tan(z) - (k*(nm1/2 + ... if False else 0))*0  # placeholder

def R_saem(alt_deg, P=1013.25, T=10.0):
    """Saemundsson refraction in arcmin -> arcsec, valid all altitudes."""
    a = alt_deg
    R = 1.02/np.tan(np.radians(a + 10.3/(a+5.11)))   # arcmin, for 1010 mb, 10C
    R = R*(P/1010.0)*(283.0/(273.0+T))
    return R*60.0

def deriv(f,x,h):
    return (f(x+h)-f(x-h))/(2*h), (f(x+h)-2*f(x)+f(x-h))/h**2, (f(x+2*h)-2*f(x+h)+2*f(x-h)-f(x-2*h))/(2*h**3)

for name, alt, P, T in [("Leon 2026 (798 m)", 9.2, 925.0, 25.0), ("Luxor 2027 (76 m)", 81.73, 1005.0, 38.0)]:
    f = lambda a: R_saem(a,P,T)
    h = 0.05
    d1,d2,d3 = deriv(f, alt, h)   # arcsec per deg, per deg^2, per deg^3
    print(f"\n{name}: alt={alt} deg, R={f(alt):.1f}\"  airmass={1/np.sin(np.radians(alt)):.3f}")
    print(f"  dR/dalt = {d1:+.3f} \"/deg  -> vertical compression = {abs(d1)/3600*100:.4f} %")
    for dfield in (1.0, 2.0, 3.5):
        lin  = abs(d1)*dfield
        quad = abs(d2)/2*dfield**2
        cub  = abs(d3)/6*dfield**3
        print(f"   field radius {dfield:3.1f} deg : linear {lin:9.2f}\"  quadratic {quad:8.3f}\"  cubic {cub:8.4f}\"")
