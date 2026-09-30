"""PTC v2: registre subpixel mesurat (nomes per informar), detrend polinomic per
pegat, i tres estimadors independents de la variancia de soroll."""
import numpy as np, rawpy
from skimage.registration import phase_cross_correlation

WHITE = 16383


def plane(path, chan='G1'):
    with rawpy.imread(path) as r:
        img = r.raw_image_visible.astype(np.float64)
        pat = r.raw_pattern.copy()
    h = img.shape[0] // 2 * 2
    w = img.shape[1] // 2 * 2
    img = img[:h, :w]
    names = {0: 'R', 1: 'G1', 2: 'B', 3: 'G2'}
    for dy in (0, 1):
        for dx in (0, 1):
            if names[int(pat[dy, dx])] == chan:
                return img[dy::2, dx::2]
    raise KeyError(chan)


def measure_shift(a, b, ped, half=512):
    yy, xx = np.indices(a.shape)
    w = np.clip(a - ped - 8, 0, None)
    if w.sum() <= 0:
        return (0.0, 0.0), (a.shape[0] // 2, a.shape[1] // 2)
    cy = int((yy * w).sum() / w.sum()); cx = int((xx * w).sum() / w.sum())
    cy = min(max(cy, half), a.shape[0] - half)
    cx = min(max(cx, half), a.shape[1] - half)
    A = np.log1p(np.clip(a[cy - half:cy + half, cx - half:cx + half] - ped, 0, None))
    B = np.log1p(np.clip(b[cy - half:cy + half, cx - half:cx + half] - ped, 0, None))
    sh, _, _ = phase_cross_correlation(A, B, upsample_factor=20)
    return (float(sh[0]), float(sh[1])), (cy, cx)


def basis(box, order):
    y, x = np.mgrid[0:box, 0:box].astype(np.float64)
    y = (y - (box - 1) / 2) / box
    x = (x - (box - 1) / 2) / box
    T = [np.ones_like(x)]
    for o in range(1, order + 1):
        for k in range(o + 1):
            T.append((x ** (o - k)) * (y ** k))
    M = np.stack([t.ravel() for t in T], 1)
    Q, _ = np.linalg.qr(M)
    return Q, M.shape[1]


def patch_table(a, b, ped, box=24, order=2, sat=WHITE - 300):
    """Per a cada pegat: senyal, variancia per fotograma, estructura de l'escena."""
    H, W = a.shape
    ny, nx = H // box, W // box
    a = a[:ny * box, :nx * box]; b = b[:ny * box, :nx * box]
    Q, npar = basis(box, order)
    A = a.reshape(ny, box, nx, box).transpose(0, 2, 1, 3).reshape(-1, box * box)
    B = b.reshape(ny, box, nx, box).transpose(0, 2, 1, 3).reshape(-1, box * box)
    D = A - B
    Mn = (A + B) / 2.0
    n = box * box - npar
    Rd = D - (D @ Q) @ Q.T
    var = (Rd * Rd).sum(1) / n / 2.0            # variancia per fotograma
    med = np.median(Rd, axis=1, keepdims=True)
    mad = np.median(np.abs(Rd - med), 1) * 1.4826
    varmad = mad ** 2 / 2.0
    Rm = Mn - (Mn @ Q) @ Q.T
    struct = np.sqrt((Rm * Rm).sum(1) / n)      # estructura no polinomica de l'escena
    S = Mn.mean(1) - ped
    ok = (A.max(1) < sat) & (B.max(1) < sat) & (A.min(1) > 0) & (B.min(1) > 0)
    return S[ok], var[ok], varmad[ok], struct[ok]
