import numpy as np, rawpy, ptc2

def rgb_planes(path):
    """Plans de Bayer amb el mateix mostreig (mitja resolucio)."""
    return {c: ptc2.plane(path, c) for c in ('R', 'G1', 'G2', 'B')}

def find_disc(g, ped=512.0):
    """Centre i radi del disc lunar (fosc) envoltat de corona, sobre el pla de Bayer."""
    s = g - ped
    # llindar: entre el disc fosc i la corona interior
    hi = np.percentile(s, 99.9)
    thr = hi * 0.02
    from scipy import ndimage
    m = s > thr
    m = ndimage.binary_closing(m, np.ones((5, 5)))
    fill = ndimage.binary_fill_holes(m)
    hole = fill & ~m
    lab, n = ndimage.label(hole)
    if n == 0:
        return None
    sizes = ndimage.sum(hole, lab, range(1, n + 1))
    k = int(np.argmax(sizes)) + 1
    ys, xs = np.where(lab == k)
    cy, cx = ys.mean(), xs.mean()
    r = np.sqrt(sizes[k - 1] / np.pi)
    return float(cy), float(cx), float(r)

def refine_disc(g, cy, cx, r, ped=512.0, naz=720):
    """Refina el limbe buscant el maxim de gradient radial en cada azimut."""
    az = np.linspace(0, 2 * np.pi, naz, endpoint=False)
    rr = np.arange(r - 25, r + 25, 0.25)
    R, A = np.meshgrid(rr, az)
    Y = cy + R * np.sin(A); X = cx + R * np.cos(A)
    from scipy.ndimage import map_coordinates
    prof = map_coordinates(g - ped, [Y.ravel(), X.ravel()], order=1).reshape(A.shape)
    d = np.gradient(np.log1p(np.clip(prof, 0.5, None)), axis=1)
    k = np.argmax(d, axis=1)
    redge = rr[k]
    good = np.abs(redge - np.median(redge)) < 4
    # ajust de cercle
    x = cx + redge * np.cos(az); y = cy + redge * np.sin(az)
    x, y = x[good], y[good]
    Amat = np.stack([x, y, np.ones_like(x)], 1)
    b = x ** 2 + y ** 2
    sol, *_ = np.linalg.lstsq(Amat, b, rcond=None)
    ncx, ncy = sol[0] / 2, sol[1] / 2
    nr = np.sqrt(sol[2] + ncx ** 2 + ncy ** 2)
    return float(ncy), float(ncx), float(nr), int(good.sum())

def polar(img, cy, cx, r0, r1, nr=200, naz=1440, ped=512.0):
    from scipy.ndimage import map_coordinates
    rr = np.linspace(r0, r1, nr)
    az = np.linspace(0, 2 * np.pi, naz, endpoint=False)
    R, A = np.meshgrid(rr, az)
    Y = cy + R * np.sin(A); X = cx + R * np.cos(A)
    P = map_coordinates(img - ped, [Y.ravel(), X.ravel()], order=1, mode='nearest').reshape(A.shape)
    return rr, az, P
