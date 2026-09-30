"""Hi ha estructura d'earthshine (mars/altiplans) dins el disc lunar?
Metode: retalla el disc, treu un polinomi 2D d'ordre 3, i correlaciona els
residus de dos fotogrames independents. Si les taques son reals, el pic
de correlacio ha de ser alt i a un desplacament coherent."""
import tifffile, numpy as np, json, sys
from scipy.signal import fftconvolve

def patch(path, cx, cy, R, half=1.05, ds=2):
    a = tifffile.imread(path)[..., 1].astype(np.float32)
    h = int(R*half)
    p = a[int(cy)-h:int(cy)+h, int(cx)-h:int(cx)+h][::ds, ::ds]
    n = p.shape[0]
    yy, xx = (np.mgrid[0:n, 0:n] - n/2.0)/(R/ds)
    r = np.hypot(yy, xx)
    m = r < 0.86
    # polinomi 2D grau 3 dins el disc
    terms = [xx**i * yy**j for i in range(4) for j in range(4) if i+j <= 3]
    A = np.stack([t[m] for t in terms], 1)
    coef, *_ = np.linalg.lstsq(A, p[m], rcond=None)
    model = sum(c*t for c, t in zip(coef, terms))
    res = np.where(m, p-model, 0.0)
    return p, res, m, float(np.median(p[m]))

cfg = json.loads(sys.argv[1])
res = []
for c in cfg:
    p, rr, m, med = patch(c["path"], c["cx"], c["cy"], c["R"])
    sd = float(np.std(rr[m]))
    res.append((c["tag"], rr, m, med, sd, p))
    print(f"{c['tag']:28s} nivell={med:8.0f}  sd_residu={sd:7.1f}  ({100*sd/med:.3f}% del nivell)  "
          f"p1-p99={np.percentile(rr[m],1):.0f}..{np.percentile(rr[m],99):.0f}")

# correlacio creuada entre parells
for i in range(len(res)):
    for j in range(i+1, len(res)):
        a, b = res[i][1], res[j][1]
        n = min(a.shape[0], b.shape[0])
        a = a[:n, :n]; b = b[:n, :n]
        a = a - a.mean(); b = b - b.mean()
        cc = fftconvolve(a, b[::-1, ::-1], mode='same')
        cc /= (np.sqrt((a**2).sum()*(b**2).sum()) + 1e-12)
        k = np.unravel_index(np.argmax(cc), cc.shape)
        off = (k[0]-n//2, k[1]-n//2)
        print(f"corr {res[i][0]} x {res[j][0]}: pic={cc[k]:.3f} a desplacament dy={off[0]} dx={off[1]} px(ds2) "
              f"| corr a 0,0 = {cc[n//2, n//2]:.3f}")
