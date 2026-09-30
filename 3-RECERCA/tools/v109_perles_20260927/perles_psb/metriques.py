"""Mètriques de trets compactes brillants (V109 · perles_psb). Totes sobre la lluminositat L = (R + 2G + B)/4 de la imatge que es mesura,
a les MATEIXES posicions (les de la V107), perquè la comparació sigui punt a punt.
  pic       = màxim de L a r ≤ 2 px
  voltant   = mediana de L a l'anell 5 ≤ r ≤ 9 px
  contrast  = pic − voltant; contrast_rel = pic / voltant
  E_1_4     = Σ DoG(σ1, σ4)² a r ≤ 5 px      (detall fi del gra/perla)
  E_4_16    = Σ DoG(σ4, σ16)² a r ≤ 12 px    (forma i halo)
  amplada   = diàmetre equivalent de l'àrea per sobre de mig contrast, (pic + voltant)/2, a r ≤ 8 px, connectada al centre
  sat       = píxels amb algun canal ≥ 0,998 a r ≤ 6 px"""
import numpy as np, cv2
from scipy import ndimage as ndi


def dog(L, s1, s2):
    return cv2.GaussianBlur(L, (0, 0), s1) - cv2.GaussianBlur(L, (0, 0), s2)


def detecta(L, d, th, dmin=-2, dmax=60, n=None, llindar_mad=6.0, sep=7):
    """Màxims locals de DoG(1,4) a la franja dmin ≤ d < dmax (sobre la imatge de referència). Retorna ys, xs, valor, llindar."""
    D = dog(L, 1, 4); mx = cv2.dilate(D, np.ones((sep, sep), np.uint8)); franja = (d >= dmin) & (d < dmax)
    mad = float(np.median(np.abs(D[franja] - np.median(D[franja])))) * 1.4826
    pk = franja & (D == mx) & (D > llindar_mad * mad)
    ys, xs = np.nonzero(pk); v = D[ys, xs]; o = np.argsort(-v)
    if n: o = o[:n]
    return ys[o], xs[o], v[o], llindar_mad * mad


_K = {}


def _disc(r0, r1):
    k = (r0, r1)
    if k not in _K:
        R = int(np.ceil(r1)); yy, xx = np.mgrid[-R:R + 1, -R:R + 1]; rr = np.hypot(xx, yy); _K[k] = (R, (rr >= r0) & (rr <= r1), rr)
    return _K[k]


def per_tret(C, ys, xs):
    """C (h, w, 3) 0–1. Retorna dict de vectors (una entrada per tret)."""
    L = (C[..., 0] + 2 * C[..., 1] + C[..., 2]) / 4; D14 = dog(L, 1, 4); D416 = dog(L, 4, 16); mxc = C.max(-1)
    out = {k: [] for k in ('pic', 'voltant', 'contrast', 'contrast_rel', 'E_1_4', 'E_4_16', 'amplada', 'sat')}
    H, W = L.shape
    for y, x in zip(ys, xs):
        R, m2, rr = _disc(0, 2); pic = L[max(y - R, 0):y + R + 1, max(x - R, 0):x + R + 1]
        pic = float(pic.max())
        R, ma, rr = _disc(5, 9); win = L[y - R:y + R + 1, x - R:x + R + 1]
        if win.shape != ma.shape: [out[k].append(np.nan) for k in out]; continue
        vol = float(np.median(win[ma]))
        R5, m5, _ = _disc(0, 5); e14 = float((D14[y - R5:y + R5 + 1, x - R5:x + R5 + 1][m5] ** 2).sum())
        R12, m12, _ = _disc(0, 12); w12 = D416[y - R12:y + R12 + 1, x - R12:x + R12 + 1]
        e416 = float((w12[m12] ** 2).sum()) if w12.shape == m12.shape else np.nan
        R8, m8, rr8 = _disc(0, 8); w8 = L[y - R8:y + R8 + 1, x - R8:x + R8 + 1]
        if w8.shape == m8.shape:
            half = (pic + vol) / 2; lab, _ = ndi.label((w8 >= half) & m8); c = lab[R8, R8]
            area = float((lab == c).sum()) if c > 0 else 0.0; amp = 2 * np.sqrt(area / np.pi)
        else: amp = np.nan
        R6, m6, _ = _disc(0, 6); s6 = mxc[y - R6:y + R6 + 1, x - R6:x + R6 + 1]; sat = float((s6[m6] >= 0.998).sum()) if s6.shape == m6.shape else np.nan
        for k, v in zip(out, (pic, vol, pic - vol, pic / max(vol, 1e-6), e14, e416, amp, sat)): out[k].append(v)
    return {k: np.array(v, np.float64) for k, v in out.items()}


def per_zona(C, mask):
    """Energia de detall a una zona: rms de DoG(1,4) i DoG(4,16) de L i de ln L, i nivell mitjà."""
    L = (C[..., 0] + 2 * C[..., 1] + C[..., 2]) / 4; lnL = np.log(np.maximum(L, 1e-4))
    return dict(L_mitj=float(L[mask].mean()), rms_DoG_1_4=float(np.sqrt((dog(L, 1, 4)[mask] ** 2).mean())), rms_DoG_4_16=float(np.sqrt((dog(L, 4, 16)[mask] ** 2).mean())),
                rms_DoGln_1_4=float(np.sqrt((dog(lnL, 1, 4)[mask] ** 2).mean())), rms_DoGln_4_16=float(np.sqrt((dog(lnL, 4, 16)[mask] ** 2).mean())),
                p99_L=float(np.percentile(L[mask], 99)), p1_L=float(np.percentile(L[mask], 1)), sat_frac=float((C.max(-1)[mask] >= 0.998).mean()))
