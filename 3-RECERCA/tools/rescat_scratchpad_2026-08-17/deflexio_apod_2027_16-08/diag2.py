import numpy as np, sys
sys.path.insert(0, '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/604fa71e-4fd9-4d66-a0e5-157c6621ceb3/scratchpad')
from model import *
import final2
from final2 import budget, VSD, MU, YIELD, MARGIN

BASE = dict(**VSD, pix=3.76, eta=ETA_MONO_R, fwhm=3.5, aext=0.12, csys=0.020,
            order=3, distres_mas=40, coronares_mas=8, extcal=True, dS=5e-7)

print("=== M44, controlled test (identical smooth field, cluster added or removed) ===")
xi, eta_, V = make_field(seed=3)
pa = np.deg2rad(314.3); cx, cy = 2.530*np.sin(pa), 2.530*np.cos(pa)
inM44 = np.hypot(xi-cx, eta_-cy) < 1.0
# cluster members are the excess over the smooth density in that circle
n_smooth_here = int(np.pi*1.0**2 * (len(xi)/(np.pi*(30*RSUN_DEG)**2)))
keep = ~inM44 | (np.arange(len(xi)) % 7 == 0)     # thin the M44 circle back to field density
for lbl, msk in (('field WITH M44 as it really is', np.ones(len(xi), bool)),
                 ('same field, M44 thinned to background', keep)):
    old = (final2.xi, final2.eta_, final2.V)
    final2.xi, final2.eta_, final2.V = xi[msk], eta_[msk], V[msk]
    b = budget(**BASE); b3 = budget(**dict(BASE, extcal=False, dS=0.0))
    final2.xi, final2.eta_, final2.V = old
    print(f"   {lbl:40s} N={b['N']:4d}  with cal {b['tot']*100:5.2f}%"
          f"   in-frame scale {b3['tot']*100:5.2f}%")
print("   -> M44 sits at 9.6 Rsun where the deflection weight is (1/9.6)^2 of a star at")
print("      1 Rsun.  It is a nice photograph and a plate-model constraint, not a signal.")

print("\n=== THERMAL PLATE-SCALE DRIFT between the calibration field and the eclipse field ===")
print("   defocus-magnification: dS/S = (dL/L) with L the back-focus; 24 ppm/K for an")
print("   aluminium tube+focuser at F=494 mm, ~1 ppm/K for carbon fibre (research 3).")
print(f"   leakage into eps for the 4.18x2.78 deg field: 0.0092 per 1e-6 of dS/S\n")
print(f"   {'tube / procedure':52s} {'dT (K)':>8s} {'dS/S':>10s} {'d eps':>8s}")
for lbl, cte, dT in (("aluminium, night calibration hours earlier", 24, 5.0),
                     ("aluminium, calibration 10 min before totality", 24, 0.5),
                     ("aluminium, RIGHT-ECLIPSE-LEFT inside totality", 24, 0.05),
                     ("aluminium, bracketed R/L (linear drift cancels)", 24, 0.010),
                     ("carbon fibre, bracketed R/L", 1, 0.010)):
    dS = cte*dT*1e-6
    print(f"   {lbl:52s} {dT:8.3f} {dS:10.2e} {dS*1e6*0.0092*100:7.2f}%")

print("\n=== FINAL ERROR BUDGET, recommended configuration ===")
b = budget(**BASE)
terms = [("random (688 stars, photon + per-star floor)", b['rnd']),
         ("optical distortion residual 40 mas, 3rd-order fit", b['bd']),
         ("radial/coronal centroid residual 8 mas", b['bc']),
         ("plate scale from calibration fields, dS/S=5e-7", b['bs']),
         ("thermal scale drift, bracketed calibration", 0.0092*0.24),
         ("Gaia DR3 catalogue + parallax + proper motion", 0.0005),
         ("differential refraction after a 3rd-order fit", 0.0002),
         ("atmospheric dispersion through r', Gaia colours applied", 0.0010)]
tot = 0
for n, v in terms:
    tot += v**2
    print(f"   {n:56s} {v*100:6.2f}%")
tot = np.sqrt(tot)
print(f"   {'QUADRATURE TOTAL':56s} {tot*100:6.2f}%")
print(f"\n   -> L = 1.7516 +/- {1.7516*tot:.4f} arcsec")
print(f"   -> GR confirmed at {1/tot:.0f} sigma; Einstein vs Newton at {0.5/tot:.0f} sigma")
print(f"   -> gamma to +/- {2*tot*100:.1f} %")
print(f"   -> Bruns 2017 record: 3.4%.  This configuration: {tot*100:.1f}%")

print("\n=== WHAT WOULD IT TAKE TO REACH 1%? ===")
for lbl, kw, extra in (
        ("as recommended", {}, 0),
        ("+ per-star floor halved (0.010 x FWHM)", dict(csys=0.010), 0),
        ("+ 2x the aperture (180 mm at 494 mm = f/2.7)", dict(D=180), 0),
        ("+ distortion 10 mas and corona 3 mas", dict(distres_mas=10, coronares_mas=3), 0),
        ("+ all three together", dict(csys=0.010, D=180, distres_mas=10, coronares_mas=3), 0)):
    a = dict(BASE); a.update(kw); bb = budget(**a)
    t = np.sqrt(bb['tot']**2 + (0.0092*0.24)**2 + 0.0005**2 + 0.001**2)
    print(f"   {lbl:46s} {t*100:6.2f}%")
