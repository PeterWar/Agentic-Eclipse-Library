"""w0 (V108 · verifica2_negres) · Compositor PROPI (no fa servir jutge_comu.comp ni comu_negres.Pila) de la pila ràster de la V107 per sota de
les capes d'ajust: base (3) + filtres 54, 41, 42, 47, 49, 51, 45, 46, 55, 56 + capes de sobre 305, 306, 258, 76, 224, 267, amb les fórmules
del Photoshop (C ← C + a·(B(C, F) − C), a = opacitat·alfa·màscara). Llegeix l'estat de la V107 (negres/estat_v107, extret del PSB; només lectura).
Un candidat de la 41/42 entra com a «ràster de la V107 + (candidat − ràster de la cadena)» (la mateixa hipòtesi que r3: dins del disc, igual).
Geometria pròpia (centre del Sol, radi solar, Lluna i marc presos de les constants del projecte)."""
import json
from pathlib import Path
import numpy as np, cv2
R0 = Path(__file__).resolve().parents[4]
EST = R0 / '4-RESULTATS/v108_20260926/negres/estat_v107'
STD = R0 / '4-RESULTATS/v108_20260926/cadena/control/filtres_std/filtres'
OUT = R0 / '4-RESULTATS/v108_20260926/verifica2_negres'
W, H = 10551, 7506
SOL = (5361.768, 3775.748); RSOL = 440.603
LLUNA = (5375.786804312011, 3775.9774911631); RLLUNA = 452.9785129274736
MARC = (1325, 1142, 9348, 6263)
META = json.loads((EST / 'CAPES_V107.json').read_text()); CAPES = {int(k): v for k, v in META['capes'].items()}
FILTRES = (54, 41, 42, 47, 49, 51, 45, 46, 55, 56); DALT = (305, 306, 258, 76, 224, 267)
TAG = {41: 'P01_NRGF', 42: 'P01_NRGF_extrap'}
cv2.setNumThreads(6)


def _llegeix(lid, suf, box, pas, fill=0):
    p = EST / f'L{lid}_{suf}.npy'
    if not p.exists(): return None
    a = np.load(p, mmap_mode='r'); c = CAPES[lid].get('caixa_desada') or (0, 0, W, H); x0, y0, x1, y1 = box
    ys = np.arange(y0, y1, pas); xs = np.arange(x0, x1, pas)
    out = np.full((len(ys), len(xs)) + a.shape[2:], fill, a.dtype)
    ky = (ys >= c[1]) & (ys < c[3]); kx = (xs >= c[0]) & (xs < c[2])
    if ky.any() and kx.any():
        yy = ys[ky] - c[1]; xx = xs[kx] - c[0]
        sub = np.asarray(a[yy[0]:yy[-1] + 1:pas, xx[0]:xx[-1] + 1:pas])
        out[np.ix_(np.flatnonzero(ky), np.flatnonzero(kx))] = sub
    return out


def alfa(lid, box, pas):
    c = CAPES[lid]; a = _llegeix(lid, 'alfa', box, pas)
    a = np.ones((len(range(box[1], box[3], pas)), len(range(box[0], box[2], pas))), np.float32) if a is None else a.astype(np.float32) / 65535
    mk = c.get('mascara'); m = _llegeix(lid, 'mascara', box, pas, fill=65535 if (mk or {}).get('background') == 255 else 0)
    if m is not None and not (mk or {}).get('disabled'): a *= m.astype(np.float32) / 65535
    return a * (c['opacitat'] / 255.0)


def ras(lid, box, pas):
    g = _llegeix(lid, 'G', box, pas)
    if g is None: g = _llegeix(lid, 'RGB', box, pas)
    return g.astype(np.float32) / 65535


def barreja(mode, C, F):
    if mode == 'MULTIPLY': return C * F
    if mode == 'OVERLAY': return np.where(C < 0.5, 2 * C * F, 1 - 2 * (1 - C) * (1 - F))
    if mode == 'LIGHTEN': return np.maximum(C, F)
    if mode == 'LINEAR_DODGE': return np.minimum(C + F, 1)
    if mode == 'NORMAL': return np.broadcast_to(F, C.shape)
    raise ValueError(mode)


def compon(box=(0, 0, W, H), pas=2, cand=None, franja=640, sense=()):
    """L = (R + 2G + B)/4 de la pila. cand = carpeta amb P01_NRGF[_extrap]_u16.npy (o None = V107)."""
    x0, y0, x1, y1 = box; ys = list(range(y0, y1, pas)); h = len(ys); w = len(range(x0, x1, pas)); L = np.empty((h, w), np.float32)
    for i0 in range(0, h, franja):
        i1 = min(h, i0 + franja); bb = (x0, y0 + i0 * pas, x1, y0 + i1 * pas)
        C = ras(3, bb, pas)
        for lid in FILTRES + DALT:
            if lid in sense: continue
            a = alfa(lid, bb, pas)
            if not (a > 0).any(): continue
            F = ras(lid, bb, pas)
            if cand is not None and lid in TAG:
                c = np.load(Path(cand) / f'{TAG[lid]}_u16.npy', mmap_mode='r'); s = np.load(STD / f'{TAG[lid]}_u16.npy', mmap_mode='r')
                sl = (slice(bb[1], bb[3], pas), slice(bb[0], bb[2], pas))
                F = np.clip(F + (np.asarray(c[sl], np.float32) - np.asarray(s[sl], np.float32)) / 65535, 0, 1)
            if F.ndim == 2: F = F[..., None]
            B = barreja(CAPES[lid]['mode'], C, F); C = C + a[..., None] * (B - C); del B, F, a
        L[i0:i1] = (C[..., 0] + 2 * C[..., 1] + C[..., 2]) / 4
    return L


def geo(box=(0, 0, W, H), pas=2):
    x0, y0, x1, y1 = box; yy, xx = np.mgrid[y0:y1:pas, x0:x1:pas].astype(np.float32)
    r = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; th = (np.degrees(np.arctan2(-(yy - SOL[1]), xx - SOL[0])) + 360) % 360
    dl = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RLLUNA
    marc = (xx >= MARC[0]) & (xx < MARC[2]) & (yy >= MARC[1]) & (yy < MARC[3])
    base_ok = alfa(3, box, pas) > 0.5
    k = max(3, int(150 / pas)) | 1
    base_ok = cv2.erode(base_ok.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) > 0
    return dict(r=r, th=th, dl=dl, marc=marc, ok=base_ok & (dl > 3))
