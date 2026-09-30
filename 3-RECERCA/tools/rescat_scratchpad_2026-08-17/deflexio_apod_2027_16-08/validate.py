import numpy as np, sys
sys.path.insert(0, '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/604fa71e-4fd9-4d66-a0e5-157c6621ceb3/scratchpad')
from model import *

rng = np.random.default_rng(7)

def uniform_in_box(n, w, h, rmin, rmax, rng):
    out = []
    while len(out) < n:
        x = rng.uniform(-w/2, w/2); y = rng.uniform(-h/2, h/2)
        r = np.hypot(x, y)/RSUN_DEG
        if rmin <= r <= rmax:
            out.append((x, y))
    return np.array(out)

print("=== VALIDATION 1: the 2026 Leon campaign (reported 1.39 / 0.57 / 0.53) ===")
for name, n, w, h, rmax, s in [("train A (300GM+A7R3A)", 38, 7.14, 4.77, 13.7, 1.61),
                               ("train B (VSD90SS+R6)",  22, 4.17, 2.78,  9.5, 0.64)]:
    vals = []
    for k in range(400):
        p = uniform_in_box(n, w, h, 2.16, rmax, np.random.default_rng(k))
        se, N = sigma_eps(p[:,0], p[:,1], np.full(n, s), order=1, rmin=2.0)
        vals.append(se)
    print(f"  {name:24s} N={n:3d} sigma*={s:.2f}\"  ->  sigma(eps) = {np.median(vals):.3f}")

print()
print("=== VALIDATION 2: Bruns 2017 (reported 3.4% total; 3.1% star-fit term) ===")
# 18 stars 2.433-4.817 Rsun in a 1.9x1.4 deg field + 2 stars at 1.513/1.603 opposite each other
for s in (0.065, 0.075):
    vals = []
    for k in range(400):
        rr = np.random.default_rng(k)
        p = uniform_in_box(18, 1.9, 1.4, 2.433, 4.817, rr)
        # the two close-in stars, nearly opposite
        th = rr.uniform(0, 2*np.pi)
        extra = np.array([[1.513*RSUN_DEG*np.cos(th), 1.513*RSUN_DEG*np.sin(th)],
                          [1.603*RSUN_DEG*np.cos(th+np.pi), 1.603*RSUN_DEG*np.sin(th+np.pi)]])
        p = np.vstack([p, extra])
        se_free, _ = sigma_eps(p[:,0], p[:,1], np.full(20, s), order=1, rmin=1.4)
        se_fix,  _ = sigma_eps(p[:,0], p[:,1], np.full(20, s), order=1, rmin=1.4, fix_scale=True)
        vals.append((se_free, se_fix))
    v = np.median(np.array(vals), axis=0)
    print(f"  per-star {s:.3f}\": eclipse-field-only scale = {v[0]*100:5.2f}% ;"
          f"  external scale = {v[1]*100:5.2f}%   (Bruns: ~4% and 3.1%)")
