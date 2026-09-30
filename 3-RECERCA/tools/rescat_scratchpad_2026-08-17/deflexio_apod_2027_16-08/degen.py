import numpy as np
np.random.seed(7)
RSUN = 945.6      # arcsec, 2027-08-02
L    = 1.7516     # arcsec at 1 Rsun

# ---------------------------------------------------------------
# 1. ANALYTIC DEGENERACY: deflection ~ 1/r  vs  plate scale ~ r
#    both purely radial.  rho = 1/sqrt(<r^-2><r^2>)  (equal weights)
# ---------------------------------------------------------------
def rho_scale(r, w=None):
    w = np.ones_like(r) if w is None else w
    W = w.sum()
    a = (w*r**-2).sum()/W
    b = (w*r**2).sum()/W
    return 1.0/np.sqrt(a*b)

def vif(rho):  return 1.0/np.sqrt(1.0-rho**2)

print("="*74)
print("DEGENERACY  deflection(1/r) vs plate-scale(r), pure radial, equal weight")
print("  rho = 1/sqrt(<r^-2><r^2>) ;  VIF = 1/sqrt(1-rho^2)")
print("="*74)
print(f"{'radial coverage':>22} {'rho':>8} {'VIF':>7}   surface-density-weighted sample")
cases = [("Bruns 2017  2.43-4.82",2.43,4.82),
         ("2026 train B 2.16-9.5",2.16,9.5),
         ("2026 train A 2.16-13.7",2.16,13.7),
         ("2027  2.0-5",2.0,5.0),
         ("2027  2.0-8",2.0,8.0),
         ("2027  2.0-11",2.0,11.0),
         ("2027  2.0-15",2.0,15.0),
         ("2027  1.5-15",1.5,15.0),
         ("2027  2.0-20",2.0,20.0),
         ("2027  3.0-15",3.0,15.0)]
for lab,a,b in cases:
    r = np.sqrt(np.random.uniform(a**2,b**2,200000))   # uniform surface density
    rr = rho_scale(r)
    print(f"{lab:>22} {rr:8.4f} {vif(rr):7.3f}")

# optimum outer radius for fixed inner radius, EQUAL weight per star, uniform density
print()
print("Outer-radius scan (inner 2.0 Rsun, uniform surface density, equal weights):")
print(f"{'r_out':>7} {'N rel':>7} {'rho':>8} {'VIF':>7} {'sig(eps) rel':>13}")
best=None
for rout in [3,4,5,6,7,8,9,10,12,15,18,20,25]:
    r = np.sqrt(np.random.uniform(2.0**2,rout**2,400000))
    rr = rho_scale(r); v=vif(rr)
    # information without degeneracy ~ N*<1/r^2>; N ~ (rout^2-4)
    N = rout**2-4.0
    info = N*np.mean(r**-2)
    sig = v/np.sqrt(info)
    if best is None or sig<best[1]: best=(rout,sig)
    print(f"{rout:7.1f} {N/ (15**2-4):7.3f} {rr:8.4f} {v:7.3f} {sig:13.4f}")
print(f"  --> minimum at r_out ~ {best[0]} Rsun")
