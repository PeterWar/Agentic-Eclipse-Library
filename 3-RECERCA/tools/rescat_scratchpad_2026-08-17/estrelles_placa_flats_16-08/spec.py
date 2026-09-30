"""Espectre de potencia d'un retall: separa senyal (baixa freq) de soroll (pla)."""
import numpy as np

def pspec(im, nbin=48, detrend=2):
    n0, n1 = im.shape
    n = min(n0, n1)
    im = im[:n, :n].astype(np.float64)
    y, x = np.mgrid[0:n, 0:n] / n - 0.5
    T = [np.ones_like(x)]
    for o in range(1, detrend + 1):
        for k in range(o + 1):
            T.append(x ** (o - k) * y ** k)
    M = np.stack([t.ravel() for t in T], 1)
    c, *_ = np.linalg.lstsq(M, im.ravel(), rcond=None)
    im = im - (M @ c).reshape(n, n)
    w = np.hanning(n)[:, None] * np.hanning(n)[None, :]
    wn = np.mean(w ** 2)
    F = np.fft.fftshift(np.fft.fft2(im * w))
    P = np.abs(F) ** 2 / (n * n) / wn        # normalitzat: sum(P)/n^2 = var
    f = np.fft.fftshift(np.fft.fftfreq(n))
    FY, FX = np.meshgrid(f, f, indexing='ij')
    FR = np.hypot(FY, FX)
    ed = np.linspace(0, 0.5 * np.sqrt(2), nbin + 1)
    idx = np.digitize(FR.ravel(), ed) - 1
    Pr = P.ravel()
    out = []
    for i in range(nbin):
        m = idx == i
        if m.sum() < 6:
            continue
        out.append((0.5 * (ed[i] + ed[i + 1]), float(Pr[m].mean()), int(m.sum())))
    return np.array(out), P, FR
