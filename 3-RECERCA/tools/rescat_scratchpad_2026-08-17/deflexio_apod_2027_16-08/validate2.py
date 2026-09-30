import numpy as np
from fisher import *
rng = np.random.default_rng(7)
R26 = 950.0

def rect_field(n, halfw_deg, halfh_deg, rmin_rho, rng, rsun=R26):
    """Uniform surface density inside the rectangular sensor footprint,
    excluding the inner rmin (Moon + inner corona)."""
    hw = halfw_deg*3600.; hh = halfh_deg*3600.
    xs=[];ys=[]
    while len(xs)<n:
        x = rng.uniform(-hw,hw); y = rng.uniform(-hh,hh)
        if np.hypot(x,y) >= rmin_rho*rsun:
            xs.append(x); ys.append(y)
    return np.array(xs), np.array(ys)

def run(n, hw, hh, sig, trials=600, order=1, rsun=R26, rmin=2.16):
    o=[];f=[];nv=[]
    for _ in range(trials):
        x,y = rect_field(n,hw,hh,rmin,rng,rsun)
        o.append(sigma_eps(x,y,sig,order=order,rsun_arcsec=rsun))
        f.append(sigma_eps(x,y,sig,order=order,rsun_arcsec=rsun,fix_scale=True))
        nv.append(sigma_eps_naive(np.hypot(x,y)/rsun,sig))
    return np.median(o),np.median(f),np.median(nv)

print("=== 2026 with the REAL rectangular footprints ===")
a=run(38, 7.14/2, 4.77/2, 1.61)
print(f"train A 38 stars @1.61: full={a[0]:.3f} (reported 1.39)  scale-fixed={a[1]:.3f}  naive={a[2]:.3f}  D={a[0]/a[2]:.2f}")
b=run(22, 4.17/2, 2.78/2, 0.64)
print(f"train B 22 stars @0.64: full={b[0]:.3f} (reported 0.57)  scale-fixed={b[1]:.3f}  naive={b[2]:.3f}  D={b[0]/b[2]:.2f}")
c=1/np.sqrt(1/a[0]**2+1/b[0]**2)
print(f"combined = {c:.3f} (reported 0.53) -> model/report = {c/0.53:.3f}")
