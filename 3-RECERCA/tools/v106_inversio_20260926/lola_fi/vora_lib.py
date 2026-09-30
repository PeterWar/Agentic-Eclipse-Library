"""vora_lib (V106, «LOLA fi», Claude, 26-09-2026) · Funcions comunes: lectura dels 67 fotogrames del limbe (sense llindar), centre del model,
silueta d'ordre 2 (D21), mostreig polar al voltant del centre de cada fotograma i ajust de la vora per calaixos d'angle.
Model de la vora a cada calaix (u = r − r_vora): V(u) = B0 + B1·s + A·Σ_k w_k·exp(b·u + b²σ_k²/2)·Φ((u + b·σ_k²)/σ_k)
= la PSF (doble gaussiana, pesos 1−f i f) aplicada a una corona exponencial exp(b·u) tallada per la Lluna a u = 0 (forma tancada exacta),
més un fons lineal (llum difusa i earthshine). La posició r_vora és la del graó abans de la PSF (sense biaix pel pendent de la corona)."""
import json, os, numpy as np, cv2
from pathlib import Path
from scipy.special import ndtr
R0 = Path.home() / 'Desktop/Eclipse 2026'
LF = Path(os.environ.get('V105_LF', str(R0 / '4-RESULTATS/v106_inversio_20260926/limb_frames_sense_llindar')))
meta = json.loads((LF / 'METADATA.json').read_text()); FR = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
NUM = np.load(LF / 'numerator.npy', mmap_mode='r'); WT = np.load(LF / 'weight.npy', mmap_mode='r'); DM = np.load(LF / 'distance_model.npy', mmap_mode='r')
Rm = float(meta['radius_model']); hb, wb = by1 - by0, bx1 - bx0; nF = len(FR)
geo = json.loads((R0 / '4-RESULTATS/v97_refundacio_20260924/lineal_v97_franja/A2_GEOMETRIA.json').read_text())['lluna_presentacio']
CX, CY, R = geo['cx'], geo['cy'], geo['R']
sil = np.load(R0 / '4-RESULTATS/v99_banda_20260925/D21_silueta_o2.npz'); SPA = np.asarray(sil['pa'], float); SE = np.asarray(sil['e'], float); SCOEF = np.asarray(sil['coef'], float)
def e_o2(a): return np.interp(np.asarray(a) % 360, SPA, SE, period=360)
TIMES = np.array([f['time'] for f in FR]); EXPO = np.array([f['exposure'] for f in FR])
def centre_model(j):
    D = np.asarray(DM[j], np.float64); gy, gx = np.gradient(D); iy, ix = hb // 2, wb - 100
    return ix + bx0 - (D[iy, ix] + Rm) * gx[iy, ix], iy + by0 - (D[iy, ix] + Rm) * gy[iy, ix]

DTH = 0.05                       # pas fi d'angle per al mostreig (graus)
NSUB = 5                         # 5 × 0,05° = calaix de 0,25°
S = np.arange(-8.0, 10.0001, 0.25)   # distància radial a la vora prevista (R + e_o2), px

def polar(j, chan=1, centre=None, s=S, dth=DTH):
    """Perfils radials del fotograma j (valor = numerador/pes) al voltant del centre donat (per defecte el del model), mostreig bilineal.
    Retorna V (ns, nθ), W (ns, nθ), θ (graus, llenç: 0 = dreta, 90 = amunt), r (ns, nθ)."""
    cx, cy = centre if centre is not None else centre_model(j)
    th = np.arange(0, 360, dth) + dth / 2
    r = R + e_o2(th)[None, :] + s[:, None]
    X = (cx + r * np.cos(np.radians(th))[None, :] - bx0).astype(np.float32); Y = (cy - r * np.sin(np.radians(th))[None, :] - by0).astype(np.float32)
    W = np.ascontiguousarray(WT[j, :, :, chan], np.float32); N = np.ascontiguousarray(NUM[j, :, :, chan], np.float32)
    Wp = cv2.remap(W, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    Np = cv2.remap(N, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    # zeros de pes dins la finestra bilineal: marca el punt com a invàlid si qualsevol veí té pes 0
    Wmin = cv2.remap(cv2.erode(W, np.ones((2, 2), np.uint8), anchor=(0, 0)), X, Y, cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    V = np.where(Wp > 0, Np / np.maximum(Wp, 1e-30), np.nan)
    V[Wmin <= 0] = np.nan
    return V, Wp, th, r

def bins(V, nsub=NSUB):
    """Mitjana de nsub subangles → calaixos (ns, nθ/nsub); NaN si algun subangle és NaN."""
    ns, nt = V.shape
    return V.reshape(ns, nt // nsub, nsub).mean(-1)

def model(p, s, psf):
    """p: (nb, 5) = lnA, b, B0, B1, u0 ; s: (ns,) ; psf = (s1, f, s2). Retorna (nb, ns)."""
    lnA, b, B0, B1, u0 = [p[:, k:k + 1] for k in range(5)]
    u = s[None, :] - u0
    s1, f, s2 = psf; out = 0.0
    for wk, sk in ((1 - f, s1), (f, s2)):
        if wk <= 0: continue
        out = out + wk * np.exp(np.clip(b * u + 0.5 * b * b * sk * sk, -50, 50)) * ndtr((u + b * sk * sk) / sk)
    return B0 + B1 * s[None, :] + np.exp(lnA) * out

def ajusta(P, s, psf, p0=None, iters=30, robust=True, bmax=0.6):
    """LM vectoritzat sobre calaixos. P: (nb, ns) amb NaN on no hi ha dada. Retorna p (nb, 5), err_u0 (nb,), chi2 (nb,), n (nb,)."""
    nb, ns = P.shape; ok = np.isfinite(P); Y = np.where(ok, P, 0.0)
    if p0 is None:
        hi = np.nanpercentile(np.where(s[None, :] > 3, P, np.nan), 50, axis=1); lo = np.nanpercentile(np.where(s[None, :] < -4, P, np.nan), 50, axis=1)
        hi = np.where(np.isfinite(hi) & (hi > 0), hi, 1.0); lo = np.where(np.isfinite(lo), lo, 0.0)
        p = np.stack([np.log(np.maximum(hi - lo, 1e-3 * hi)), np.full(nb, -0.02), lo, np.zeros(nb), np.zeros(nb)], 1)
    else:
        p = p0.copy()
    lam = np.full(nb, 1e-2); wr = ok.astype(float)
    scale = np.maximum(np.nanmedian(np.where(s[None, :] > 3, P, np.nan), axis=1), 1e-6); scale = np.where(np.isfinite(scale), scale, 1.0)
    def resid(pp): return (np.where(ok, Y - model(pp, s, psf), 0.0)) / scale[:, None]
    eps = np.array([1e-4, 1e-4, 1e-4, 1e-5, 1e-4])
    for it in range(iters):
        r = resid(p)
        if robust and it >= 3:
            mad = np.nanmedian(np.where(ok, np.abs(r), np.nan), axis=1)
            c = 4.685 * np.maximum(mad / 0.6745, 1e-6)[:, None]
            wr = np.where(ok, np.clip(1 - (r / c) ** 2, 0, None) ** 2, 0.0)
        J = np.empty((nb, ns, 5))
        for k in range(5):
            dp = np.zeros_like(p); dp[:, k] = eps[k]
            if k == 2: dp[:, k] = 1e-4 * np.exp(p[:, 0])
            if k == 3: dp[:, k] = 1e-5 * np.exp(p[:, 0])
            J[:, :, k] = -(resid(p + dp) - r) / dp[:, k:k + 1]      # derivada del model (escalat)
        Jw = J * wr[:, :, None]
        H = np.einsum('bik,bil->bkl', Jw, J); g = np.einsum('bik,bi->bk', Jw, r)
        Hd = H + lam[:, None, None] * np.einsum('bkk->bk', H)[:, :, None] * np.eye(5)[None]
        try:
            dpar = np.linalg.solve(Hd + 1e-12 * np.eye(5)[None], g[:, :, None])[:, :, 0]
        except np.linalg.LinAlgError:
            dpar = np.zeros_like(p)
        pn = p + dpar; pn[:, 1] = np.clip(pn[:, 1], -bmax, bmax); pn[:, 4] = np.clip(pn[:, 4], -6, 6)
        c_old = np.sum(wr * r * r, 1); rn = resid(pn); c_new = np.sum(wr * rn * rn, 1)
        better = c_new < c_old
        p = np.where(better[:, None], pn, p); lam = np.where(better, lam * 0.3, lam * 10)
    r = resid(p); wtot = wr
    # error formal de u0 (escala amb la dispersió dels residus)
    J = np.empty((nb, ns, 5))
    for k in range(5):
        dp = np.zeros_like(p); dp[:, k] = 1e-4 if k != 2 else 1e-4 * np.exp(p[:, 0])
        J[:, :, k] = (resid(p + dp) - r) / dp[:, k:k + 1]
    Jw = J * wtot[:, :, None]; H = np.einsum('bik,bil->bkl', Jw, J)
    n = wtot.sum(1); dof = np.maximum(n - 5, 1); s2 = np.sum(wtot * r * r, 1) / dof
    try:
        Hi = np.linalg.inv(H + 1e-12 * np.eye(5)[None]); err = np.sqrt(np.maximum(Hi[:, 4, 4] * s2, 0))
    except np.linalg.LinAlgError:
        err = np.full(nb, np.nan)
    return p, err, s2, n
