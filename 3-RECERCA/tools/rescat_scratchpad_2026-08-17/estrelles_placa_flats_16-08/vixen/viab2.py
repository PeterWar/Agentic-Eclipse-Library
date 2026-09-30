import numpy as np, lib
from scipy.ndimage import fourier_shift, gaussian_filter
from skimage.registration import phase_cross_correlation

SQ2 = np.sqrt(2.0)
STEP = SQ2*lib.SCALE                    # 3,052 arcsec entre mostres verdes
F_NYQ_PLA = 0.5*STEP/(2*lib.SCALE)      # Nyquist del pla de Bayer, en c/mostra quincunx


def quincunx(img, y0, y1, x0, x1):
    y = np.arange(y0, y1)[:, None]; x = np.arange(x0, x1)[None, :]
    g = ((y % 2 == 0) & (x % 2 == 1)) | ((y % 2 == 1) & (x % 2 == 0))
    Y, X = np.broadcast_arrays(y, x)
    uu = ((X+Y-1)//2)[g]; vv = ((X-Y+1)//2)[g]; val = img[y0:y1, x0:x1][g]
    uu = uu-uu.min(); vv = vv-vv.min()
    out = np.zeros((uu.max()+1, vv.max()+1)); cnt = np.zeros_like(out)
    out[uu, vv] = val; cnt[uu, vv] = 1
    n0 = out.shape[0] - out.shape[0] % 2; n1 = out.shape[1] - out.shape[1] % 2
    return out[:n0, :n1], cnt[:n0, :n1]


def register(a, b):
    ha = a - gaussian_filter(a, 6); hb = b - gaussian_filter(b, 6)
    w = np.hanning(a.shape[0])[:, None]*np.hanning(a.shape[1])[None, :]
    sh, _, _ = phase_cross_correlation(ha*w, hb*w, upsample_factor=200, normalization='phase')
    return sh


def spectra(a, b, nb=48):
    sh = register(a, b)
    b2 = np.real(np.fft.ifft2(fourier_shift(np.fft.fft2(b), sh)))
    S = 0.5*(a+b2); Dd = 0.5*(a-b2)
    n0, n1 = a.shape
    w = np.hanning(n0)[:, None]*np.hanning(n1)[None, :]
    nrm = np.sum(w**2)
    PS = np.abs(np.fft.fftshift(np.fft.fft2(S*w)))**2/nrm
    PD = np.abs(np.fft.fftshift(np.fft.fft2(Dd*w)))**2/nrm
    fy = np.fft.fftshift(np.fft.fftfreq(n0))[:, None]
    fx = np.fft.fftshift(np.fft.fftfreq(n1))[None, :]
    f = np.hypot(fy, fx).ravel()
    PS = PS.ravel(); PD = PD.ravel()
    edges = np.linspace(0, 0.5, nb+1)
    idx = np.digitize(f, edges)-1
    F, SIG, NOI = [], [], []
    for i in range(nb):
        k = idx == i
        if k.sum() < 10:
            continue
        F.append(f[k].mean()); SIG.append(PS[k].mean()-PD[k].mean()); NOI.append(PD[k].mean())
    return np.array(F), np.array(SIG), np.array(NOI), sh


def crossing(F, SIG, NOI, fmin=0.08):
    r = SIG/NOI
    ok = F > fmin
    Fo, ro = F[ok], r[ok]
    bel = np.where(ro < 1)[0]
    if not len(bel):
        return None, ro[-1]
    i = bel[0]
    if i == 0:
        return Fo[0], ro[-1]
    x0, x1 = np.log(max(ro[i-1], 1e-6)), np.log(max(ro[i], 1e-6))
    fc = Fo[i-1] + (0-x0)/(x1-x0)*(Fo[i]-Fo[i-1])
    return fc, ro[-1]


def run(nameA, nameB, cy, cx, half, label):
    A = lib.load(nameA); B = lib.load(nameB)
    a, _ = quincunx(A, cy-half, cy+half, cx-half, cx+half)
    b, _ = quincunx(B, cy-half, cy+half, cx-half, cx+half)
    n0 = min(a.shape[0], b.shape[0]) // 2*2; n1 = min(a.shape[1], b.shape[1])//2*2
    a = a[:n0, :n1]; b = b[:n0, :n1]
    F, SIG, NOI, sh = spectra(a, b)
    fc, rn = crossing(F, SIG, NOI)
    # soroll pla?
    hi = NOI[F > 0.3]
    flat = hi.std()/hi.mean() if len(hi) else np.nan
    if fc is None:
        txt = "senyal > soroll fins a Nyquist"
        per = STEP/(2*0.5)
    else:
        txt = "tall a %.3f c/mostra" % fc
        per = STEP/(2*fc)
    # senyal/soroll al Nyquist del pla de Bayer
    rpla = np.interp(F_NYQ_PLA, F, SIG/NOI)
    print("%-46s  caixa %3dx%3d  desp=(%+.2f,%+.2f)  %-28s  resolucio=%5.2f\"   "
          "S/N a Nyq_pla(8,63\")=%6.1f  S/N a Nyq_quinc(6,10\")=%5.2f" %
          (label, n0, n1, sh[0], sh[1], txt, 2*per, rpla, rn))
    return F, SIG, NOI
