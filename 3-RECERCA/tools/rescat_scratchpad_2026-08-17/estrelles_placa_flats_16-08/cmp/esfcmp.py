"""Mesura identica del FWHM del sistema als dos trens, a partir del tall de
ganivet del limbe lunar. Nomes lectura. Tot en arcsec."""
import numpy as np, rawpy, math
from scipy.optimize import least_squares
from scipy.special import erf
from scipy.ndimage import uniform_filter1d

SQ2 = math.sqrt(2.0)


def Phi(z):
    return 0.5 * (1.0 + erf(z / SQ2))


def load(path, pedestal=512.0):
    with rawpy.imread(path) as raw:
        v = raw.raw_image_visible.astype(np.float64) - pedestal
        c = raw.raw_colors_visible.copy()
        white = int(raw.white_level)
    return v, c, white


def pick(v, c, which):
    """which: 'G' -> colors 1 i 3 (quincunx), 'R' -> 0, 'B' -> 2."""
    if which == 'G':
        m = (c == 1) | (c == 3)
    elif which == 'G1':
        m = (c == 1)
    elif which == 'G2':
        m = (c == 3)
    elif which == 'R':
        m = (c == 0)
    else:
        m = (c == 2)
    ys, xs = np.nonzero(m)
    return xs.astype(np.float64), ys.astype(np.float64), v[ys, xs]


def centroid(v):
    """Detecta el disc lunar fosc: llindar + emplenat de forats sobre una
    imatge de blocs 8x8. Torna centre i radi aproximats en px crus."""
    from scipy.ndimage import binary_fill_holes, label, binary_closing
    s = np.clip(v, 0, None)
    k = 8
    h, w = s.shape
    sb = s[:h // k * k, :w // k * k].reshape(h // k, k, w // k, k).mean(axis=(1, 3))
    thr = 0.10 * np.percentile(sb, 99.9)
    m = binary_closing(sb > thr, np.ones((3, 3)))
    holes = binary_fill_holes(m) & ~m
    lab, n = label(holes)
    if n == 0:
        raise RuntimeError('no s\'ha trobat el disc lunar')
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    i = sizes.argmax()
    ys, xs = np.nonzero(lab == i)
    R = math.sqrt(sizes[i] / math.pi) * k
    return (xs.mean() + 0.5) * k, (ys.mean() + 0.5) * k, R


def fit_circle(x, y, val, cx, cy, R0, nazim=720, win=40.0):
    """Ajust robust del limbe: creuament al 50% per azimut + cercle."""
    for it in range(4):
        dx = x - cx
        dy = y - cy
        r = np.hypot(dx, dy)
        sel = np.abs(r - R0) < win
        rr = r[sel]
        th = np.arctan2(dy[sel], dx[sel])
        vv = val[sel]
        ib = ((th + np.pi) / (2 * np.pi) * nazim).astype(int) % nazim
        rs, ts = [], []
        # perfil radial per azimut, bins d'1 px
        nb = int(2 * win)
        rid = np.clip(((rr - (R0 - win))).astype(int), 0, nb - 1)
        key = ib * nb + rid
        cnt = np.bincount(key, minlength=nazim * nb).reshape(nazim, nb)
        ssum = np.bincount(key, weights=vv, minlength=nazim * nb).reshape(nazim, nb)
        prof = np.where(cnt > 0, ssum / np.maximum(cnt, 1), np.nan)
        rax = R0 - win + np.arange(nb) + 0.5
        inner = np.nanmedian(prof[:, (rax < R0 - 0.35 * win) & (rax > R0 - 0.95 * win)], axis=1)
        outer = np.nanmedian(prof[:, (rax > R0 + 0.35 * win) & (rax < R0 + 0.95 * win)], axis=1)
        mid = 0.5 * (inner + outer)
        sm = np.where(np.isnan(prof), 0.0, prof)
        sm = uniform_filter1d(sm, 3, axis=1)
        for a in range(nazim):
            if not np.isfinite(mid[a]) or (outer[a] - inner[a]) < 20:
                continue
            p = sm[a]
            above = p > mid[a]
            idx = np.nonzero(above[1:] & ~above[:-1])[0]
            if idx.size == 0:
                continue
            j = idx[np.argmin(np.abs(rax[idx] - R0))]
            f = (mid[a] - p[j]) / max(p[j + 1] - p[j], 1e-9)
            rs.append(rax[j] + f)
            ts.append(-np.pi + (a + 0.5) * 2 * np.pi / nazim)
        rs = np.array(rs); ts = np.array(ts)
        good = np.ones(rs.size, bool)
        for k in range(4):
            A = np.stack([np.ones(good.sum()), np.cos(ts[good]), np.sin(ts[good])], 1)
            sol, *_ = np.linalg.lstsq(A, rs[good], rcond=None)
            res = rs - (sol[0] + sol[1] * np.cos(ts) + sol[2] * np.sin(ts))
            sd = 1.4826 * np.median(np.abs(res[good] - np.median(res[good])))
            good = np.abs(res) < 3 * sd
        cx += sol[1] * 1.0
        cy += sol[2] * 1.0
        R0 = sol[0]
    return cx, cy, R0, sd, good.sum()


def sector_fits(x, y, val, cx, cy, R, halfwin_px, nsec, satlevel):
    dx = x - cx; dy = y - cy
    r = np.hypot(dx, dy)
    sel = np.abs(r - R) < halfwin_px
    u = r[sel] - R
    th = np.arctan2(dy[sel], dx[sel])
    vv = val[sel]
    ib = ((th + np.pi) / (2 * np.pi) * nsec).astype(int) % nsec
    order = np.argsort(ib, kind='stable')
    u = u[order]; vv = vv[order]; ib = ib[order]
    bounds = np.searchsorted(ib, np.arange(nsec + 1))
    out = []
    for a in range(nsec):
        i0, i1 = bounds[a], bounds[a + 1]
        if i1 - i0 < 18:
            continue
        us = u[i0:i1]; vs = vv[i0:i1]
        if np.max(vs) > satlevel:
            continue
        P0 = np.median(vs[us < -0.5 * halfwin_px])
        O0 = np.median(vs[us > 0.5 * halfwin_px])
        if not np.isfinite(P0) or not np.isfinite(O0) or (O0 - P0) < 30:
            continue

        def res(p):
            P, c0, c1, u0, s = p
            return P + (c0 + c1 * us) * Phi((us - u0) / s) - vs
        try:
            sol = least_squares(res, [P0, O0 - P0, 0.0, 0.0, 1.0],
                                bounds=([-np.inf, 1e-3, -np.inf, -4.0, 0.15],
                                        [np.inf, np.inf, np.inf, 4.0, 8.0]),
                                max_nfev=400)
        except Exception:
            continue
        if not sol.success:
            continue
        P, c0, c1, u0, s = sol.x
        rms = math.sqrt(np.mean(sol.fun ** 2))
        if abs(u0) > 3.0 or c0 <= 0:
            continue
        denom = c0 + c1 * us
        ok = denom > 0.3 * c0
        out.append(dict(a=a, u=us[ok], y=(vs[ok] - P) / denom[ok], u0=u0, s=s,
                        c0=c0, rms=rms, snr=c0 / max(rms, 1e-6), n=int(ok.sum())))
    return out


def stack_esf(fits, align=True, xlim=8.0, bw=0.05, mincnt=6):
    xs, ys = [], []
    for f in fits:
        xs.append(f['u'] - (f['u0'] if align else 0.0))
        ys.append(f['y'])
    x = np.concatenate(xs); y = np.concatenate(ys)
    m = np.abs(x) < xlim
    x, y = x[m], y[m]
    nb = int(2 * xlim / bw)
    idx = np.clip(((x + xlim) / bw).astype(int), 0, nb - 1)
    cnt = np.bincount(idx, minlength=nb)
    s1 = np.bincount(idx, weights=y, minlength=nb)
    s2 = np.bincount(idx, weights=y * y, minlength=nb)
    ok = cnt > mincnt
    xc = (-xlim + (np.arange(nb) + 0.5) * bw)[ok]
    ym = (s1[ok] / cnt[ok])
    sd = np.sqrt(np.maximum(s2[ok] / cnt[ok] - ym ** 2, 0)) / np.sqrt(cnt[ok])
    return xc, ym, np.maximum(sd, 1e-4), cnt[ok]


def esf_model(x, a, s1, s2, boxw, A, B, x0):
    """ESF = A * [(a*G(s1)+(1-a)*G(s2)) (x) boxcar(boxw)] integrada + B."""
    g = np.linspace(-40, 40, 8001)
    d = g[1] - g[0]
    lsf = a * np.exp(-0.5 * (g / s1) ** 2) / s1 + (1 - a) * np.exp(-0.5 * (g / s2) ** 2) / s2
    nb = max(int(round(boxw / d)), 1)
    box = np.ones(nb) / nb
    lsf = np.convolve(lsf, box, mode='same')
    lsf /= lsf.sum() * d
    esf = np.cumsum(lsf) * d
    return A * np.interp(x - x0, g, esf) + B


def fwhm_of(a, s1, s2, boxw=0.0):
    g = np.linspace(-40, 40, 16001)
    d = g[1] - g[0]
    lsf = a * np.exp(-0.5 * (g / s1) ** 2) / s1 + (1 - a) * np.exp(-0.5 * (g / s2) ** 2) / s2
    if boxw > 0:
        nb = max(int(round(boxw / d)), 1)
        lsf = np.convolve(lsf, np.ones(nb) / nb, mode='same')
    lsf = lsf / lsf.max()
    i = np.nonzero(lsf > 0.5)[0]
    lo = np.interp(0.5, [lsf[i[0] - 1], lsf[i[0]]], [g[i[0] - 1], g[i[0]]])
    hi = np.interp(0.5, [lsf[i[-1] + 1], lsf[i[-1]]], [g[i[-1] + 1], g[i[-1]]])
    return hi - lo


def fit_esf(xc, ym, sd, boxw=1.0):
    def res(p):
        a, s1, s2, A, B, x0 = p
        return (esf_model(xc, a, s1, s2, boxw, A, B, x0) - ym) / sd
    best = None
    for s1i, s2i in [(0.6, 1.6), (0.4, 1.2), (1.0, 2.5)]:
        try:
            sol = least_squares(res, [0.7, s1i, s2i, 1.0, 0.0, 0.0],
                                bounds=([0.0, 0.10, 0.10, 0.5, -0.5, -1.0],
                                        [1.0, 6.0, 12.0, 1.5, 0.5, 1.0]), max_nfev=600)
            if best is None or sol.cost < best.cost:
                best = sol
        except Exception:
            pass
    a, s1, s2, A, B, x0 = best.x
    return dict(a=a, s1=s1, s2=s2, A=A, B=B, x0=x0,
                fwhm_int=fwhm_of(a, s1, s2, 0.0),
                fwhm_tot=fwhm_of(a, s1, s2, boxw),
                chi2=float(np.mean(best.fun ** 2)))
