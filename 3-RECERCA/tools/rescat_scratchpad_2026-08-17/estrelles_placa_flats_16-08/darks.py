import numpy as np, ptc2, os, sys, json, subprocess, collections

def inventory(d, ext):
    out = subprocess.run(['exiftool', '-T', '-FileName', '-ExposureTime', '-ISO'] +
                         [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith(ext)],
                         capture_output=True, text=True).stdout
    g = collections.defaultdict(list)
    for l in out.strip().split('\n'):
        p = l.split('\t')
        if len(p) < 3: continue
        g[p[1]].append(os.path.join(d, p[0]))
    return g

def secs(e):
    if '/' in e:
        a, b = e.split('/'); return float(a) / float(b)
    return float(e)

def stats(a, b, ped, box=32):
    """Mitjana, variancia per fotograma i autocorrelacio de la diferencia."""
    H, W = a.shape
    a = a[100:H - 100, 100:W - 100]; b = b[100:H - 100, 100:W - 100]
    d = a - b
    # retall robust de pixels calents / raigs cosmics
    med = np.median(d); mad = np.median(np.abs(d - med)) * 1.4826
    m = np.abs(d - med) < 6 * mad
    v = np.var(d[m]) / 2.0
    mean = float(np.median((a + b) / 2.0) - ped)
    meanmean = float(np.mean(np.clip((a + b) / 2.0, 0, np.percentile((a + b) / 2, 99.9))) - ped)
    # autocorrelacio a lag 1 i 2 (horitzontal i vertical) sobre la diferencia
    dd = np.where(m, d - med, 0.0)
    n0 = np.mean(dd * dd)
    ac = {}
    for name, sl in [('h1', (slice(None), slice(1, None))), ('h2', (slice(None), slice(2, None))),
                     ('v1', (slice(1, None), slice(None))), ('v2', (slice(2, None), slice(None)))]:
        k = 1 if name.endswith('1') else 2
        if name[0] == 'h':
            ac[name] = float(np.mean(dd[:, :-k] * dd[:, k:]) / n0)
        else:
            ac[name] = float(np.mean(dd[:-k, :] * dd[k:, :]) / n0)
    # soroll de fila/columna (bandes)
    rows = dd.mean(1); cols = dd.mean(0)
    ac['rowvar'] = float(np.var(rows) * dd.shape[1] / 2.0)
    ac['colvar'] = float(np.var(cols) * dd.shape[0] / 2.0)
    return mean, meanmean, v, ac
