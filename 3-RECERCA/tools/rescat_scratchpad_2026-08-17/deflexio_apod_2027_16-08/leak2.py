import numpy as np, sys
sys.path.insert(0, '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/604fa71e-4fd9-4d66-a0e5-157c6621ceb3/scratchpad')
from model import *
from leak import leak

xi, eta_, V = make_field(seed=3)
sig_all = np.full(len(V), 0.12)
w, h = 4.18, 2.78
inx = (np.abs(xi) < w/2) & (np.abs(eta_) < h/2)
x, y, s = xi[inx], eta_[inx], sig_all[inx]
R = np.hypot(w, h)/2

print("Recommended field 4.18 x 2.78 deg (VSD90SS + full-frame), %d stars\n" % inx.sum())
print("A. HIGH-ORDER OPTICAL DISTORTION, unit amplitude at the field edge")
print(f"{'pattern':>10s} {'linear':>10s} {'3rd order':>10s} {'5th order':>10s} {'7th order':>10s}")
for n in (2, 3, 4, 5, 6, 7):
    pat = lambda rho, n=n: (rho/R)**n
    v = [leak(x, y, s, pat, order=o) for o in (1, 3, 5, 7)]
    print(f"{'r^%d'%n:>10s} {v[0]:10.4f} {v[1]:10.4f} {v[2]:10.4f} {v[3]:10.4f}")

print("\nB. CORONAL-GRADIENT CENTROID BIAS: radial patterns that FALL with radius.")
print("   Unit amplitude quoted AT 2 Rsun.  These are NOT removable by a")
print("   polynomial plate model - they look like the signal.")
r2 = 2 * RSUN_DEG
print(f"{'pattern':>12s} {'linear':>10s} {'3rd order':>10s} {'5th order':>10s} {'note':>28s}")
for n, note in ((1, 'identical to the signal'), (2, ''), (3, ''), (4, '')):
    pat = lambda rho, n=n: (r2/rho)**n
    v = [leak(x, y, s, pat, order=o) for o in (1, 3, 5)]
    print(f"{'(2Rsun/r)^%d'%n:>12s} {v[0]:10.3f} {v[1]:10.3f} {v[2]:10.3f} {note:>28s}")

print("\nC. VARIANCE COST of plate-model order, and of an inner-radius cut")
for rmin in (1.8, 2.0, 2.5, 3.0, 4.0):
    row = []
    for o in (1, 3, 5, 7):
        se, N = sigma_eps(x, y, s, order=o, rmin=rmin)
        row.append(se)
    se, N = sigma_eps(x, y, s, order=3, rmin=rmin)
    print(f"  rmin={rmin:.1f} Rsun  N={N:5d}   1st {row[0]*100:5.2f}%  3rd {row[1]*100:5.2f}%"
          f"  5th {row[2]*100:5.2f}%  7th {row[3]*100:5.2f}%")

print("\nD. WHERE THE INFORMATION IS: sigma(eps) using only stars inside r_max")
for rmax in (3, 4, 5, 6, 8, 10, 12, 15, 25):
    m = np.hypot(x, y)/RSUN_DEG < rmax
    if m.sum() < 60:
        print(f"  r<{rmax:2d} Rsun  N={m.sum():5d}   (too few for a 3rd-order fit)")
        continue
    se3, N = sigma_eps(x[m], y[m], s[m], order=3, rmin=1.8)
    se1, _ = sigma_eps(x[m], y[m], s[m], order=1, rmin=1.8)
    print(f"  r<{rmax:2d} Rsun  N={N:5d}   1st {se1*100:6.2f}%   3rd {se3*100:6.2f}%")
