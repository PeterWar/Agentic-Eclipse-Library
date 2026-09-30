import numpy as np, sys
sys.path.insert(0, '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/604fa71e-4fd9-4d66-a0e5-157c6621ceb3/scratchpad')
from model import *
from final2 import budget, VSD, MU

print("=== FOCAL-LENGTH OPTIMUM, with distortion residual growing as the cube of the")
print("    field angle (40 mas at 2.51 deg half-diagonal, the Bruns-class calibration).")
print("    Full-frame mono 36x24, 3.76 um, Sloan r', FWHM 3.5\", 200 s, 90 mm aperture.\n")
print(f"{'F(mm)':>6s} {'as/px':>6s} {'px/FWHM':>8s} {'half-diag':>10s} {'r_corner':>9s} "
      f"{'N*':>5s} {'random':>7s} {'distort':>8s} {'TOTAL 3rd':>10s} {'TOTAL 5th':>10s}")
best = (1e9, None)
for F in (200, 250, 300, 350, 390, 440, 494, 550, 620, 700, 800, 950, 1200):
    w, h = np.rad2deg(36/F), np.rad2deg(24/F); Rd = np.hypot(w, h)/2
    dres = 40.0*(Rd/2.51)**3
    out = {}
    for o in (3, 5):
        b = budget(F=F, D=89.8, pix=3.76, sw=36, sh=24, eta=ETA_MONO_R, fwhm=3.5,
                   aext=0.12, csys=0.020, order=o, distres_mas=dres, coronares_mas=8)
        out[o] = b
    b3 = out[3]
    tot = min(out[3]['tot'], out[5]['tot'])
    if tot < best[0]:
        best = (tot, F)
    print(f"{F:6d} {b3['p']:6.2f} {3.5/b3['p']:8.2f} {Rd:9.2f}d {Rd/RSUN_DEG:8.1f}R "
          f"{b3['N']:5d} {b3['rnd']*100:6.2f}% {b3['bd']*100:7.2f}% "
          f"{out[3]['tot']*100:9.2f}% {out[5]['tot']*100:9.2f}%")
print(f"\n  -> optimum at F ~ {best[1]} mm, sigma(eps) = {best[0]*100:.2f}%"
      f"   (VSD90SS is 494 mm)")

print("\n=== SAME, but with calibration fields (plate scale determined externally) ===")
print(f"{'F(mm)':>6s} {'N*':>5s} {'random':>7s} {'distort':>8s} {'scale':>7s} {'TOTAL':>8s}")
for F in (250, 300, 390, 494, 620, 800):
    w, h = np.rad2deg(36/F), np.rad2deg(24/F); Rd = np.hypot(w, h)/2
    b = budget(F=F, D=89.8, pix=3.76, sw=36, sh=24, eta=ETA_MONO_R, fwhm=3.5,
               aext=0.12, csys=0.020, order=3, distres_mas=40.0*(Rd/2.51)**3,
               coronares_mas=8, extcal=True, dS=5e-7)
    print(f"{F:6d} {b['N']:5d} {b['rnd']*100:6.2f}% {b['bd']*100:7.2f}% "
          f"{b['bs']*100:6.2f}% {b['tot']*100:7.2f}%")

print("\n=== WHEN IS A 5th-ORDER PLATE MODEL WORTH ITS VARIANCE? (494 mm, FF mono) ===")
print(f"{'distortion residual (mas)':>26s} {'3rd order':>10s} {'5th order':>10s} {'winner':>8s}")
for d in (20, 40, 80, 150, 300, 600, 1200):
    t = []
    for o in (3, 5):
        b = budget(**VSD, pix=3.76, eta=ETA_MONO_R, fwhm=3.5, aext=0.12, csys=0.020,
                   order=o, distres_mas=d, coronares_mas=8)
        t.append(b['tot'])
    print(f"{d:26d} {t[0]*100:9.2f}% {t[1]*100:9.2f}% {'3rd' if t[0]<t[1] else '5th':>8s}")

print("\n=== FRAMING M44 / VENUS / delta Cnc (all at PA 291-314 deg) ===")
for F, sw, sh, nm in ((494, 36, 24, 'VSD90SS + full frame'),
                      (494, 23.5, 15.7, 'VSD90SS + APS-C'),
                      (300, 36, 24, 'Sony 300 + full frame')):
    w, h = np.rad2deg(sw/F), np.rad2deg(sh/F)
    print(f"   {nm:24s} {w:4.2f}x{h:4.2f} deg  half-short {h/2:4.2f} ({h/2/RSUN_DEG:4.1f}R)"
          f"  half-long {w/2:4.2f} ({w/2/RSUN_DEG:4.1f}R)  half-diag {np.hypot(w,h)/2:4.2f}"
          f" ({np.hypot(w,h)/2/RSUN_DEG:4.1f}R)")
print("   targets: delta Cnc 0.815 deg (3.10R) | M44 2.530 deg (9.63R) | Venus 2.840 deg (10.81R)")
for off in (0.0, 0.3, 0.55, 0.8):
    b = budget(**VSD, pix=3.76, eta=ETA_MONO_R, fwhm=3.5, aext=0.12, csys=0.020,
               order=3, distres_mas=40, coronares_mas=8, extcal=True, dS=5e-7, offset=off)
    w, h = np.rad2deg(36/494), np.rad2deg(24/494)
    reach = off + np.hypot(w, h)/2
    print(f"   offset {off:4.2f} deg toward PA 314 -> reaches {reach/RSUN_DEG:5.1f} Rsun that way,"
          f" {(np.hypot(w,h)/2-off)/RSUN_DEG:5.1f} Rsun opposite;  N={b['N']:4d}"
          f"  sigma(eps)={b['tot']*100:5.2f}%")
