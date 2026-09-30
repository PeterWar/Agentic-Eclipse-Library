import numpy as np, lib
from scipy.signal import savgol_filter

for key in ('R', 'G1', 'G2', 'B'):
    c, med, cnt = np.load(f"stack_{key}.npy")
    ok = np.isfinite(med) & (np.abs(c) < 20)
    x = c[ok]; y = savgol_filter(med[ok], 41, 3)
    d = savgol_filter(np.gradient(y, x), 41, 3)
    d = d - np.median(np.concatenate([d[:100], d[-100:]]))
    d = np.clip(d, 0, None)
    d /= d.sum()*(x[1]-x[0])
    # centrat
    xc = (d*x).sum()*(x[1]-x[0])
    # MTF
    f = np.linspace(0, 0.6, 601)                      # cicles per pixel raw
    M = np.abs(np.trapezoid(d*np.exp(-2j*np.pi*f[:, None]*(x-xc)), x, axis=1))
    M /= M[0]
    def at(fq): return np.interp(fq, f, M)
    def fat(v):
        i = np.where(M < v)[0]
        return np.interp(v, [M[i[0]], M[i[0]-1]], [f[i[0]], f[i[0]-1]]) if len(i) else np.nan
    print("%3s  MTF50 a %.4f c/px = %.4f c/arcsec  (periode %.2f\")   MTF10 a %.4f c/px (%.2f\")" % (
        key, fat(0.5), fat(0.5)/lib.SCALE, lib.SCALE/fat(0.5), fat(0.1), lib.SCALE/fat(0.1)))
    print("     MTF a Nyquist del pla de Bayer (0,25 c/px) = %.3f ;  a Nyquist de la reixa raw (0,50 c/px) = %.4f" % (
        at(0.25), at(0.50)))
    # variancia i cua
    var = (d*(x-xc)**2).sum()*(x[1]-x[0])
    print("     sigma equivalent (2n moment, |u|<20px) = %.3f px = %.2f\"  ; FWHM gaussiana equiv %.2f\"" % (
        np.sqrt(var), np.sqrt(var)*lib.SCALE, 2.3548*np.sqrt(var)*lib.SCALE))
    # energia encerclada de la LSF
    cum = np.cumsum(d)*(x[1]-x[0])
    for frac, lab in [(0.5,'50 %'), (0.8,'80 %'), (0.9,'90 %'), (0.95,'95 %')]:
        lo = np.interp(0.5-frac/2, cum, x); hi = np.interp(0.5+frac/2, cum, x)
        print("       amplada que conte el %s de la LSF: %.2f px = %.2f\"" % (lab, hi-lo, (hi-lo)*lib.SCALE))
