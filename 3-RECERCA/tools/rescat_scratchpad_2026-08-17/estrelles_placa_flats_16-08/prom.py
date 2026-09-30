"""Analisi de les protuberancies: electrons, soroll mesurat contra Poisson,
i escala espacial on el senyal supera el soroll."""
import numpy as np, ptc2, limb
from scipy.ndimage import map_coordinates, shift as ndshift

V = '/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/'
S = '/Users/USUARI/Desktop/Eclipse 2026/300mm/'


def reg_int(a, ref, ped=512.0):
    sh, _ = ptc2.measure_shift(ref, a, ped)
    dy, dx = int(round(sh[0])), int(round(sh[1]))
    return np.roll(np.roll(a, dy, 0), dx, 1), sh


def boxes_from_peaks(cy, cx, R, azdeg, dr0=-6, dr1=26, halfaz=9.0):
    """Retall rectangular que conte el sector de protuberancia."""
    out = []
    for A in azdeg:
        a0, a1 = np.radians(A - halfaz), np.radians(A + halfaz)
        aa = np.linspace(a0, a1, 60)
        rr = np.array([R + dr0, R + dr1])
        ys = np.concatenate([cy + r * np.sin(aa) for r in rr])
        xs = np.concatenate([cx + r * np.cos(aa) for r in rr])
        out.append((int(ys.min()) - 2, int(ys.max()) + 3, int(xs.min()) - 2, int(xs.max()) + 3))
    return out


def radial_mask(shape, y0, x0, cy, cx, R, r0, r1, azdeg, halfaz):
    yy, xx = np.mgrid[y0:y0 + shape[0], x0:x0 + shape[1]]
    r = np.hypot(yy - cy, xx - cx)
    a = np.degrees(np.arctan2(yy - cy, xx - cx)) % 360
    d = np.abs((a - azdeg + 180) % 360 - 180)
    return (r > R + r0) & (r < R + r1) & (d < halfaz)


def powerspec(img, nbin=40):
    """Espectre de potencia radial 1D (per pixel^2 per mode)."""
    n = min(img.shape)
    im = img[:n, :n]
    w = np.hanning(n)[:, None] * np.hanning(n)[None, :]
    wn = np.mean(w ** 2)
    F = np.fft.fftshift(np.fft.fft2((im - im.mean()) * w))
    P = np.abs(F) ** 2 / (n * n) / wn
    fy = np.fft.fftshift(np.fft.fftfreq(n))
    F2 = np.hypot(*np.meshgrid(fy, fy, indexing='ij'))
    ed = np.linspace(0, 0.5, nbin + 1)
    idx = np.digitize(F2.ravel(), ed) - 1
    out = []
    Pr = P.ravel()
    for i in range(nbin):
        m = idx == i
        if m.sum() < 8:
            continue
        out.append((0.5 * (ed[i] + ed[i + 1]), float(Pr[m].mean()), int(m.sum())))
    return np.array(out)
