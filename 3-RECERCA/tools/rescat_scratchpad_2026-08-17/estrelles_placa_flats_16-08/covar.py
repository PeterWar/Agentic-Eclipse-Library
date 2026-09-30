"""Autocovariancia 2D del soroll (imatge diferencia) sobre la graella crua sencera.
Serveix per veure si el soroll es blanc i per corregir el guany per acoblament
entre pixels (IPC / difusio de carrega), que conserva la suma de covariancies."""
import numpy as np, rawpy


def raw_vis(path):
    with rawpy.imread(path) as r:
        return r.raw_image_visible.astype(np.float64)


def detrend_blocks(D, box=32, order=2):
    H, W = D.shape
    ny, nx = H // box, W // box
    D = D[:ny * box, :nx * box]
    y, x = np.mgrid[0:box, 0:box].astype(np.float64)
    y = (y - (box - 1) / 2) / box; x = (x - (box - 1) / 2) / box
    T = [np.ones_like(x)]
    for o in range(1, order + 1):
        for k in range(o + 1):
            T.append(x ** (o - k) * y ** k)
    M = np.stack([t.ravel() for t in T], 1)
    Q, _ = np.linalg.qr(M)
    A = D.reshape(ny, box, nx, box).transpose(0, 2, 1, 3).reshape(-1, box * box)
    R = A - (A @ Q) @ Q.T
    return R.reshape(ny, nx, box, box).transpose(0, 2, 1, 3).reshape(ny * box, nx * box)


def autocov(R, lag=4):
    R = R - R.mean()
    n0 = float(np.mean(R * R))
    C = np.zeros((2 * lag + 1, 2 * lag + 1))
    for dy in range(-lag, lag + 1):
        for dx in range(-lag, lag + 1):
            a = R[max(0, dy):R.shape[0] + min(0, dy), max(0, dx):R.shape[1] + min(0, dx)]
            b = R[max(0, -dy):R.shape[0] + min(0, -dy), max(0, -dx):R.shape[1] + min(0, -dx)]
            C[dy + lag, dx + lag] = float(np.mean(a * b))
    return C, n0
