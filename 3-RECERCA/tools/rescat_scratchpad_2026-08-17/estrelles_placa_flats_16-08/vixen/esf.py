import numpy as np
from scipy.optimize import least_squares
from scipy.special import erf
import lib

RIN, ROUT = 30.0, 30.0        # finestra d'ajust al voltant del limbe (px raw)


def sector_data(img, key, CY, CX, R, nsec=120, rin=RIN, rout=ROUT):
    p, oy, ox = lib.plane(img, key)
    ny, nx = p.shape
    y0 = int((CY - R - rout - 4)/2); y1 = int((CY + R + rout + 4)/2)+1
    x0 = int((CX - R - rout - 4)/2); x1 = int((CX + R + rout + 4)/2)+1
    y0, x0 = max(y0, 0), max(x0, 0); y1, x1 = min(y1, ny), min(x1, nx)
    ii, jj = np.mgrid[y0:y1, x0:x1]
    Y = 2*ii + oy; X = 2*jj + ox
    dy = Y - CY; dx = X - CX
    r = np.hypot(dy, dx)
    m = (r > R-rin) & (r < R+rout)
    r = r[m]; v = p[y0:y1, x0:x1][m]
    th = np.arctan2(dx[m], dy[m])          # 0 = cap amunt (+y), horari
    sec = ((th + np.pi)/(2*np.pi)*nsec).astype(int) % nsec
    return r, v, th, sec


def model(par, u):
    r0, s, P, c0, c1, c2 = par
    z = (u - r0)/(np.sqrt(2)*s)
    step = 0.5*(1 + erf(z))
    return P + (c0 + c1*(u-r0) + c2*(u-r0)**2)*step


def fit_sector(r, v, R, s0=1.5):
    u = r - R
    if len(u) < 60:
        return None
    inn = np.median(v[u < -12]); out = np.median(v[(u > 4) & (u < 14)])
    if not np.isfinite(inn) or not np.isfinite(out) or (out - inn) <= 0:
        return None
    p0 = [0.0, s0, inn, out-inn, 0.0, 0.0]
    try:
        res = least_squares(lambda p: model(p, u) - v, p0,
                            bounds=([-8, 0.15, -1e5, 0, -1e5, -1e5],
                                    [8, 20, 1e5, 1e9, 1e5, 1e5]),
                            max_nfev=400)
    except Exception:
        return None
    r0, s, P, c0, c1, c2 = res.x
    rms = np.sqrt(np.mean(res.fun**2))
    return dict(r0=r0, sigma=s, P=P, amp=c0, c1=c1, c2=c2, rms=rms,
                contrast=c0/max(abs(P), 1e-3), n=len(u), out=out, inn=inn)


def measure_frame(name, keys=('R', 'G1', 'G2', 'B'), nsec=120, verbose=False,
                  img=None, geo=None):
    if img is None:
        img = lib.load(name)
    if geo is None:
        CY, CX, R, *_ = lib.solve_geometry(img)
    else:
        CY, CX, R = geo
    outp = {}
    for key in keys:
        r, v, th, sec = sector_data(img, key, CY, CX, R, nsec=nsec)
        rows = []
        for k in range(nsec):
            m = sec == k
            f = fit_sector(r[m], v[m], R)
            if f is None:
                continue
            f['sec'] = k
            f['th'] = (k + 0.5)*2*np.pi/nsec - np.pi
            rows.append(f)
        outp[key] = dict(rows=rows, r=r, v=v, th=th, sec=sec)
    return img, (CY, CX, R), outp
