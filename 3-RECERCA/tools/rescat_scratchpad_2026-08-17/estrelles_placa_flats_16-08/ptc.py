"""Corba de transferencia de fotons per parelles de fotogrames, en espai cru."""
import numpy as np, rawpy, sys, json, itertools

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


def est_shift(a, b, maxs=64):
    """Desplacament enter (dy,dx) en pixels de pla que porta b sobre a.
    Correlacio de fase sobre la imatge sencera, en log per no dependre del pic."""
    A = np.log1p(np.clip(a - np.median(a), 0, None))
    B = np.log1p(np.clip(b - np.median(b), 0, None))
    win = np.hanning(A.shape[0])[:, None] * np.hanning(A.shape[1])[None, :]
    FA = np.fft.rfft2(A * win)
    FB = np.fft.rfft2(B * win)
    R = FA * np.conj(FB)
    R /= np.abs(R) + 1e-12
    c = np.fft.irfft2(R, s=A.shape)
    idx = np.unravel_index(np.argmax(c), c.shape)
    dy = idx[0] if idx[0] <= A.shape[0] // 2 else idx[0] - A.shape[0]
    dx = idx[1] if idx[1] <= A.shape[1] // 2 else idx[1] - A.shape[1]
    return int(dy), int(dx), float(c.max())


def patch_stats(a, b, ped, box=24, order=2, sat=WHITE - 300, gradfrac=0.10):
    """Retorna llista de (senyal_ADU, var_per_fotograma_ADU2, ndof, gradient_rel)."""
    H, W = a.shape
    ny, nx = H // box, W // box
    a = a[:ny * box, :nx * box]
    b = b[:ny * box, :nx * box]
    # base polinomica
    y, x = np.mgrid[0:box, 0:box].astype(np.float64)
    y = (y - box / 2) / box
    x = (x - box / 2) / box
    terms = [np.ones_like(x), x, y]
    if order >= 2:
        terms += [x * x, x * y, y * y]
    M = np.stack([t.ravel() for t in terms], axis=1)
    Q, _ = np.linalg.qr(M)
    npar = M.shape[1]

    A = a.reshape(ny, box, nx, box).transpose(0, 2, 1, 3).reshape(-1, box * box)
    B = b.reshape(ny, box, nx, box).transpose(0, 2, 1, 3).reshape(-1, box * box)
    D = A - B
    S = (A + B) / 2.0 - ped

    ok = (A.max(1) < sat) & (B.max(1) < sat) & (A.min(1) > 0) & (B.min(1) > 0)
    # residu despres de treure el polinomi
    coef = D @ Q
    R = D - coef @ Q.T
    n = box * box - npar
    var = (R * R).sum(1) / n
    # estimador robust (MAD) per detectar valors atipics dins el pegat
    mad = np.median(np.abs(R - np.median(R, axis=1, keepdims=True)), axis=1) * 1.4826
    varr = mad ** 2
    clean = var < 1.6 * varr + 1e-9
    smean = S.mean(1)
    # gradient relatiu tipic del pegat (per diagnostic)
    gy = np.abs(np.diff(A.reshape(-1, box, box), axis=1)).mean((1, 2))
    grad = gy / np.maximum(smean, 1.0)
    ok &= clean & (smean > -50)
    return smean[ok], var[ok] / 2.0, np.full(ok.sum(), n), grad[ok]


def fit_ptc(S, V, w=None):
    """Ajust ponderat var = S/g + RN^2. Retorna g (e/ADU), RN (ADU) i incerteses."""
    S = np.asarray(S, float); V = np.asarray(V, float)
    if w is None:
        w = np.ones_like(S)
    X = np.stack([S, np.ones_like(S)], 1)
    Wm = np.diag(w)
    cov = np.linalg.inv(X.T @ Wm @ X)
    beta = cov @ (X.T @ (w * V))
    resid = V - X @ beta
    chi2 = float((w * resid ** 2).sum() / max(len(S) - 2, 1))
    cov = cov * chi2
    slope, inter = beta
    g = 1.0 / slope
    dg = abs(g) * np.sqrt(cov[0, 0]) / abs(slope)
    rn = np.sqrt(max(inter, 0.0))
    drn = np.sqrt(cov[1, 1]) / (2 * max(rn, 1e-6))
    return dict(g=g, dg=dg, rn=rn, drn=drn, slope=slope, inter=inter, chi2=chi2)
