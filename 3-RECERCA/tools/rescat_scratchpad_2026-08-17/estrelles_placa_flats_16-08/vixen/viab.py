import numpy as np, lib
from scipy.ndimage import fourier_shift
from skimage.registration import phase_cross_correlation

SQ2 = np.sqrt(2.0)
STEP = SQ2*lib.SCALE          # 3,052 arcsec: pas de la reixa verda (quincunx)


def green_quincunx(img, y0, y1, x0, x1):
    """reixa verda girada 45 graus: pas sqrt(2) px raw, ortogonal, completa"""
    y = np.arange(y0, y1)[:, None]
    x = np.arange(x0, x1)[None, :]
    g = ((y % 2 == 0) & (x % 2 == 1)) | ((y % 2 == 1) & (x % 2 == 0))
    Y, X = np.broadcast_arrays(y, x)
    uu = (X + Y - 1)//2
    vv = (X - Y + 1)//2
    uu = uu[g]; vv = vv[g]; val = img[y0:y1, x0:x1][g]
    uu -= uu.min(); vv -= vv.min()
    out = np.full((uu.max()+1, vv.max()+1), np.nan)
    out[uu, vv] = val
    return out


def radial_ps(a, b=None, apod=True):
    n0, n1 = a.shape
    w = np.hanning(n0)[:, None]*np.hanning(n1)[None, :] if apod else 1.0
    F = np.fft.fftshift(np.fft.fft2(a*w))
    P = (np.abs(F)**2)/(np.sum(w**2) if apod else a.size)
    fy = np.fft.fftshift(np.fft.fftfreq(n0))[:, None]
    fx = np.fft.fftshift(np.fft.fftfreq(n1))[None, :]
    f = np.hypot(fy, fx)
    return f.ravel(), P.ravel()


def analyse(nameA, nameB, cy, cx, half, label, nb=40):
    A = lib.load(nameA); B = lib.load(nameB)
    y0, y1 = cy-half, cy+half
    x0, x1 = cx-half, cx+half
    ga = green_quincunx(A, y0, y1, x0, x1)
    gb = green_quincunx(B, y0, y1, x0, x1)
    m = np.isfinite(ga) & np.isfinite(gb)
    n0 = min(ga.shape[0], gb.shape[0]); n1 = min(ga.shape[1], gb.shape[1])
    ga = ga[:n0, :n1]; gb = gb[:n0, :n1]
    ga = np.nan_to_num(ga, nan=np.nanmedian(ga)); gb = np.nan_to_num(gb, nan=np.nanmedian(gb))
    # retall parell
    n0 -= n0 % 2; n1 -= n1 % 2
    ga = ga[:n0, :n1]; gb = gb[:n0, :n1]
    sh, err, _ = phase_cross_correlation(ga, gb, upsample_factor=100, normalization=None)
    gb2 = np.real(np.fft.ifft2(fourier_shift(np.fft.fft2(gb), sh)))
    S = 0.5*(ga+gb2); Dd = 0.5*(ga-gb2)
    f, Ps = radial_ps(S)
    _, Pd = radial_ps(Dd)
    edges = np.linspace(0, 0.5, nb+1)
    idx = np.digitize(f, edges)-1
    fs, ps, pd = [], [], []
    for i in range(nb):
        k = idx == i
        if k.sum() < 8:
            continue
        fs.append(f[k].mean()); ps.append(np.mean(Ps[k])); pd.append(np.mean(Pd[k]))
    fs = np.array(fs); ps = np.array(ps); pd = np.array(pd)
    sig = ps - pd
    print("\n--- %s :  %s + %s   caixa %dx%d px de reixa verda   desplacament %.3f,%.3f" %
          (label, nameA, nameB, n0, n1, sh[0], sh[1]))
    print("    f(c/mostra)  f(c/arcsec)  periode(\")   P_senyal      P_soroll     senyal/soroll")
    for i in range(0, len(fs), max(1, len(fs)//14)):
        print("      %.3f        %.4f      %7.2f   %11.4g  %11.4g   %8.2f" %
              (fs[i], fs[i]/STEP, STEP/fs[i] if fs[i] > 0 else np.inf, sig[i], pd[i],
               sig[i]/pd[i] if pd[i] > 0 else np.nan))
    ok = np.isfinite(sig) & (fs > 0.05)
    r = sig[ok]/pd[ok]
    below = np.where(r < 1)[0]
    if len(below):
        i = below[0]
        f1 = np.interp(0.0, [np.log(r[i]), np.log(r[i-1])], [fs[ok][i], fs[ok][i-1]]) if i > 0 else fs[ok][i]
        print("    >> tall senyal=soroll a f=%.3f c/mostra = %.4f c/arcsec  -> 1/(2f) = %.2f arcsec" %
              (f1, f1/STEP, STEP/(2*f1)))
    else:
        print("    >> el senyal supera el soroll fins a Nyquist (0,5 c/mostra = %.4f c/arcsec):"
              " LIMITAT PEL MOSTREIG" % (0.5/STEP))
        print("       rao senyal/soroll a Nyquist = %.2f" % r[-1])
    return fs, sig, pd
