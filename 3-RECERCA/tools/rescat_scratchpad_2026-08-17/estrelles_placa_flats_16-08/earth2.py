"""Igual que earth.py pero (a) reixa angular comuna, (b) nomes r<0.70 per
excloure la pujada del limbe, (c) cerca de rotacio per a la comparacio
entre cossos."""
import tifffile, numpy as np, json, sys
from scipy.ndimage import map_coordinates, rotate

N = 320          # reixa comuna: 320x320 sobre +-1.05 Rm
HALF = 1.05

def grid_patch(path, cx, cy, R):
    a = tifffile.imread(path)[..., 1].astype(np.float32)
    u = (np.arange(N) - (N-1)/2.0) * (2*HALF/N)     # en radis lunars
    yy, xx = np.meshgrid(u, u, indexing='ij')
    ys = cy + yy*R; xs = cx + xx*R
    p = map_coordinates(a, [ys, xs], order=1, mode='nearest')
    r = np.hypot(yy, xx)
    return p, r

def detrend(p, r, rmax):
    m = r < rmax
    yy, xx = np.meshgrid(np.linspace(-HALF,HALF,N), np.linspace(-HALF,HALF,N), indexing='ij')
    terms = [xx**i * yy**j for i in range(4) for j in range(4) if i+j <= 3]
    A = np.stack([t[m] for t in terms], 1)
    c, *_ = np.linalg.lstsq(A, p[m], rcond=None)
    res = p - sum(k*t for k,t in zip(c, terms))
    res = np.where(m, res - res[m].mean(), 0.0)
    return res, m, float(np.median(p[m]))

def corr(a, b, m):
    return float((a[m]*b[m]).sum()/np.sqrt((a[m]**2).sum()*(b[m]**2).sum()))

cfg = json.loads(sys.argv[1]); P=[]
for c in cfg:
    p, r = grid_patch(c["path"], c["cx"], c["cy"], c["R"])
    res, m, med = detrend(p, r, 0.70)
    sd = float(np.std(res[m]))
    print(f"{c['tag']:24s} nivell={med:8.0f} sd(r<0.70)={sd:7.1f} ({100*sd/med:.3f}%)")
    P.append((c["tag"], res, m, med, sd))

print("\ncorrelacio de residus dins r<0.70, reixa angular comuna:")
for i in range(len(P)):
    for j in range(i+1, len(P)):
        best = max(((corr(P[i][1], rotate(P[j][1], ang, reshape=False, order=1), P[i][2]), ang)
                    for ang in range(-180, 180, 5)))
        print(f"  {P[i][0]:22s} x {P[j][0]:22s}  rho(0 deg)={corr(P[i][1],P[j][1],P[i][2]):+.3f}   "
              f"millor rho={best[0]:+.3f} a {best[1]:+d} deg")
