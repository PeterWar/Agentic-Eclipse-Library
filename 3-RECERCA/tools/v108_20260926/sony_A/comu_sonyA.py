"""Mòdul comú de la tasca «residu de T1 i T2 a l'apuntament A de la Sony» (V108, ronda 2, carpeta sony_A/).
Només lectura de tot el que hi ha fora de 3-RECERCA/tools/v108_20260926/sony_A/ i 4-RESULTATS/v108_20260926/sony_A/.
Geometria dels traços: la de M3 (ronda 1, marrons), que és la de la capa 269 de Pere afinada al ràster de la WOW.
Mesura del traç: residu relatiu rel = img / mitjana_normalitzada(img, σ 40 px) − 1 (la màscara de dada compta), perfil perpendicular
promitjat al llarg del traç; profunditat D(t0) = mitjana(|t − t0| ≤ 3) − mitjana(12 ≤ |t − t0| ≤ 60). El nul són les rectes paral·leles
del mateix perfil (|t0| ≥ 60) i les rectes girades ±3°…±9° (mateixa imatge, mateixa mesura)."""
import json, os, sys, hashlib
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[4]
OUT = ARREL / '4-RESULTATS/v108_20260926/sony_A'
W, H = 10551, 7506
SOL = (5361.768, 3775.748); RSOL = 440.603
R97 = ARREL / '4-RESULTATS/v97_refundacio_20260924'; CR = R97 / 'cadena_raw'
PIL = ARREL / '4-RESULTATS/v108_20260926/marrons/pilot'
V98 = ARREL / '4-RESULTATS/v98_20260925/cadena_v98'
_g = json.loads((ARREL / '4-RESULTATS/v108_20260926/marrons/M3_GEOMETRIA.json').read_text())
TRACOS = {}
for k in ('1', '2'):
    z = _g[k]; d = np.array(z['direccio'], float); d /= np.linalg.norm(d)
    TRACOS[int(k)] = dict(k=int(k), nom=z['nom'], centre=np.array(z['centre'], float), d=d, n=np.array([-d[1], d[0]]), llarg=float(z['llarg']), extrems=np.array(z['extrems'], float))

FONTS = {   # nom → (fitxer, canal o None)
    'A_ctrl': (CR / 'b2_sony_A/cau/sony_A_total_v36.npy', 1),
    'A_f2d': (PIL / 'flat2d/sony_A_total.npy', 1),
    'B_ctrl': (CR / 'b2_sony_B/cau/sony_B_total_v42.npy', 1),
    'B_f2d': (PIL / 'flat2d/cau/sony_B_total_v42.npy', 1),
    'SonyAB_ctrl': (V98 / 'b3/cau/sony_corrected_total_v42.npy', 1),
    'SonyAB_f2d': (PIL / 'cadena_v108/b3/cau/sony_corrected_total_v42.npy', 1),
    'base_ctrl': (V98 / 'd4/products/sources/base_G.npy', None),
    'base_f2d': (PIL / 'cadena_v108/d4/products/sources/base_G.npy', None),
    'compost_ctrl': (PIL / 'compost_v107mascares_abans.npy', None),
    'compost_f2d': (PIL / 'compost_v107mascares_despres.npy', None),
}

def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def desa(path, d):
    Path(path).write_text(json.dumps(d, ensure_ascii=False, indent=1, default=lambda x: x.item() if isinstance(x, np.generic) else (x.tolist() if isinstance(x, np.ndarray) else str(x))) + '\n')

def obre(nom_o_cami, canal=None):
    if nom_o_cami in FONTS: p, canal = FONTS[nom_o_cami]
    else: p = Path(nom_o_cami)
    a = np.load(p, mmap_mode='r')
    if a.ndim == 3 and canal is None: canal = 1 if a.shape[2] == 3 else 0
    return a, canal

def retall(a, canal, box):
    x0, y0, x1, y1 = box
    return np.asarray(a[y0:y1, x0:x1] if canal is None or a.ndim == 2 else a[y0:y1, x0:x1, canal], np.float32)

def caixa_tr(tr, marge=700):
    e = tr['extrems']; x0 = int(max(0, e[:, 0].min() - marge)); x1 = int(min(W, e[:, 0].max() + marge)); y0 = int(max(0, e[:, 1].min() - marge)); y1 = int(min(H, e[:, 1].max() + marge))
    return x0, y0, x1, y1

def rel_map(img, sgran=40.0, sfi=0.0, erosio=41):
    """residu relatiu fi amb convolució normalitzada per la màscara de dada (img > 0 i finita)."""
    m = np.isfinite(img) & (img > 0); w = m.astype(np.float32); v = np.where(m, img, 0).astype(np.float32)
    ng = lambda x, s: cv2.GaussianBlur(x * w, (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-6)
    num = ng(v, sfi) if sfi > 0 else v
    ok = m & (cv2.erode(w, np.ones((erosio, erosio), np.uint8)) > 0) if erosio > 1 else m
    return np.where(ok, num / np.maximum(ng(v, sgran), 1e-12) - 1, np.nan).astype(np.float32)

def graella(c, d, s, t):
    n = np.array([-d[1], d[0]])
    X = c[0] + s[:, None] * d[0] + t[None, :] * n[0]; Y = c[1] + s[:, None] * d[1] + t[None, :] * n[1]
    return X.astype(np.float32), Y.astype(np.float32)

def mostreja(img, X, Y, org=(0, 0)):
    Xl = X - org[0]; Yl = Y - org[1]
    P = cv2.remap(np.ascontiguousarray(img, np.float32), Xl, Yl, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan)
    P[(Xl < 0) | (Yl < 0) | (Xl > img.shape[1] - 1) | (Yl > img.shape[0] - 1)] = np.nan
    return P

def gira(d, graus):
    a = np.radians(graus); return np.array([d[0] * np.cos(a) - d[1] * np.sin(a), d[0] * np.sin(a) + d[1] * np.cos(a)])

def perfil(r, org, c, d, L, s0=None, s1=None, tmax=600, dt=0.5, ds=2.0, cob_min=0.6):
    s = np.arange(-L / 2 if s0 is None else s0, (L / 2 if s1 is None else s1) + 1e-6, ds); t = np.arange(-tmax, tmax + 1e-6, dt)
    X, Y = graella(c, d, s, t); P = mostreja(r, X, Y, org); cov = np.isfinite(P).mean(0)
    with np.errstate(all='ignore'): pr = np.where(cov >= cob_min, np.nanmean(P, 0), np.nan)
    return t, pr, cov

def profunditat(t, pr, t0=0.0, nucli=3.0, fl=(12.0, 60.0)):
    c = np.abs(t - t0) <= nucli; f = (np.abs(t - t0) >= fl[0]) & (np.abs(t - t0) <= fl[1])
    if np.isfinite(pr[c]).sum() < 3 or np.isfinite(pr[f]).sum() < 20: return np.nan
    return float(np.nanmean(pr[c]) - np.nanmean(pr[f]))

def mesura_amb_nul(r, org, c, d, L, s0=None, s1=None, girs=(-9, -6, -3, 3, 6, 9)):
    """profunditat a t0 = 0 (geometria fixa, SENSE cerca) i nul de rectes paral·leles (|t0| 60…540, pas 6) i girades."""
    t, pr, cov = perfil(r, org, c, d, L, s0, s1)
    D0 = profunditat(t, pr, 0.0)
    nul = [profunditat(t, pr, t0) for t0 in np.concatenate([np.arange(-540, -59, 6), np.arange(60, 541, 6)])]
    for gg in girs:
        tg, pg, _ = perfil(r, org, c, gira(d, gg), L, s0, s1, tmax=300)
        nul += [profunditat(tg, pg, t0) for t0 in np.arange(-240, 241, 12)]
    nul = np.array([x for x in nul if np.isfinite(x)])
    if len(nul) < 30 or not np.isfinite(D0): return dict(D=D0, n_nul=int(len(nul))), t, pr
    med = float(np.median(nul)); mad = float(1.4826 * np.median(np.abs(nul - med)))
    return dict(D=D0, nul_med=med, nul_mad=mad, z=(D0 - med) / mad, p=float((np.sum(nul <= D0) + 1) / (len(nul) + 1)), n_nul=int(len(nul)), cobertura=float(np.nanmean(cov[np.abs(t) <= 60]))), t, pr
