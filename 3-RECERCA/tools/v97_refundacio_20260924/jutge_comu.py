"""Mòdul comú del jutge V97: geometria, lectura d'un «estat» (carpeta amb L{id}_G/RGB/alfa/mascara.npy + CAPES.json),
compositor com el de Photoshop (sense capes d'ajust) i mostreig polar al voltant de la Lluna o del Sol.
Un estat és el que el jutge compara: v96_ref (extret de la V96 per r2) o estat_v97 (el que construeix la V97)."""
import json
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]
RES = ARREL / '4-RESULTATS/v97_refundacio_20260924'
W, H = 10551, 7506
SOL = (5361.768, 3775.748); RSOL = 440.603                      # graella V23 (geometria_v27)
LLUNA = (5375.786804312011, 3775.9774911631); RLLUNA = 452.9785129274736   # Lluna de presentació (V86 A2), instant t = 18,4 s
MARC = (1325, 1142, 9348, 6263)                                  # enquadrament final (V78-FINAL)

def comp(layers, h, w):
    """layers: (mode, rgb[h,w,3] 0–1, alfa efectiva[h,w]) de baix a dalt → (color, cobertura). Com Photoshop per a aquests modes."""
    Cb = np.zeros((h, w, 3), np.float32); ab = np.zeros((h, w), np.float32)
    for mode, F, a in layers:
        if F.ndim == 2: F = F[..., None]
        if mode == 'NORMAL': B = np.broadcast_to(F, Cb.shape)
        elif mode == 'MULTIPLY': B = Cb * F
        elif mode == 'OVERLAY': B = np.where(Cb < 0.5, 2 * Cb * F, 1 - 2 * (1 - Cb) * (1 - F))
        elif mode == 'LINEAR_DODGE': B = np.clip(Cb + F, 0, 1)
        elif mode == 'DIFFERENCE': B = np.abs(Cb - F)
        elif mode == 'LIGHTEN': B = np.maximum(Cb, F)
        else: raise ValueError(mode)
        Cs = (1 - ab[..., None]) * np.broadcast_to(F, Cb.shape) + ab[..., None] * B; ao = a + ab * (1 - a)
        num = a[..., None] * Cs + (1 - a[..., None]) * ab[..., None] * Cb
        Cb = np.where(ao[..., None] > 0, num / np.maximum(ao[..., None], 1e-9), 0).astype(np.float32); ab = ao.astype(np.float32)
    return Cb, ab

class Estat:
    """Carpeta amb els ràsters d'una versió. CAPES.json (o CAPES_V96.json): props per capa (mode, opacitat, visible, caixa_desada)."""
    def __init__(self, carpeta):
        self.dir = Path(carpeta); j = next(self.dir.glob('CAPES*.json')); self.meta = json.loads(j.read_text())
        self.capes = {int(k): v for k, v in self.meta['capes'].items()}; self.ordre = self.meta['ordre_de_baix_a_dalt']
    def te(self, lid): return any(self.dir.glob(f'L{lid}_*.npy'))
    def caixa(self, lid): return tuple(self.capes[lid].get('caixa_desada') or (0, 0, W, H))
    def _llegeix(self, lid, sufix, box, fill=0):
        p = self.dir / f'L{lid}_{sufix}.npy'
        if not p.exists(): return None
        a = np.load(p, mmap_mode='r'); cx0, cy0, cx1, cy1 = self.caixa(lid); x0, y0, x1, y1 = box
        shape = (y1 - y0, x1 - x0) + a.shape[2:]; out = np.full(shape, fill, a.dtype)
        xa, ya, xb, yb = max(x0, cx0), max(y0, cy0), min(x1, cx1), min(y1, cy1)
        if xb > xa and yb > ya: out[ya - y0:yb - y0, xa - x0:xb - x0] = a[ya - cy0:yb - cy0, xa - cx0:xb - cx0]
        return out
    def rgb(self, lid, box=(0, 0, W, H), pas=1):
        """(h,w,3) o (h,w) 0–1."""
        g = self._llegeix(lid, 'G', box)
        if g is None: g = self._llegeix(lid, 'RGB', box)
        return (np.asarray(g[::pas, ::pas], np.float32) / 65535)
    def alfa_efectiva(self, lid, box=(0, 0, W, H), pas=1, amb_opacitat=True):
        c = self.capes[lid]; a = self._llegeix(lid, 'alfa', box)
        a = np.ones((box[3] - box[1], box[2] - box[0]), np.float32) if a is None else np.asarray(a, np.float32) / 65535
        m = self._llegeix(lid, 'mascara', box, fill=65535 if (c.get('mascara') or {}).get('background') == 255 else 0)
        if m is not None: a = a * (np.asarray(m, np.float32) / 65535)
        a = a[::pas, ::pas]
        return a * (c['opacitat'] / 255.0) if amb_opacitat else a
    def dada(self, lid, box=(0, 0, W, H), pas=1):
        """Alfa del ràster sol (sense màscara ni opacitat): on el filtre diu que hi ha dada."""
        a = self._llegeix(lid, 'alfa', box)
        return (np.ones((box[3] - box[1], box[2] - box[0]), np.float32) if a is None else np.asarray(a, np.float32) / 65535)[::pas, ::pas]
    def pila(self, fins_a=234, sense=(), amb=(), pas=1, box=(0, 0, W, H)):
        """Capes visibles (o forçades amb `amb`) per sota de `fins_a`, amb ràster, de baix a dalt."""
        out = []
        for lid in self.ordre:
            if lid == fins_a: break
            c = self.capes.get(lid)
            if c is None or lid in sense or not self.te(lid): continue
            if not (c['visible'] or lid in amb): continue
            out.append((lid, c['mode'], self.rgb(lid, box, pas), self.alfa_efectiva(lid, box, pas)))
        return out
    def compost(self, pas=1, box=(0, 0, W, H), **kw):
        P = self.pila(pas=pas, box=box, **kw); h, w = P[0][2].shape[:2]
        return comp([(m, F, a) for _, m, F, a in P], h, w)

def polar(img, centre=LLUNA, r0=RLLUNA - 12, r1=RLLUNA + 320, dr=0.5, nth=5760, interp=cv2.INTER_LINEAR, border=np.nan):
    """Mostreig polar: files = radi (r0…r1 amb pas dr), columnes = azimut θ (0° = +x, 90° = −y, «amunt» a la imatge).
    Retorna (P, r, θ graus)."""
    r = np.arange(r0, r1, dr, dtype=np.float32); th = np.linspace(0, 2 * np.pi, nth, endpoint=False, dtype=np.float32)
    X = (centre[0] + np.cos(th)[None, :] * r[:, None]).astype(np.float32); Y = (centre[1] - np.sin(th)[None, :] * r[:, None]).astype(np.float32)
    src = np.ascontiguousarray(img, np.float32)
    P = cv2.remap(src, X, Y, interp, borderMode=cv2.BORDER_CONSTANT, borderValue=float(border) if np.isfinite(border) else 0.0)
    if not np.isfinite(border):
        out = (X < 0) | (Y < 0) | (X > img.shape[1] - 1) | (Y > img.shape[0] - 1); P[out] = np.nan
    return P, r, np.degrees(th)

def dist_limbe(box=(0, 0, W, H), pas=1):
    x0, y0, x1, y1 = box; yy, xx = np.mgrid[y0:y1:pas, x0:x1:pas].astype(np.float32)
    return np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RLLUNA

def radi_sol(box=(0, 0, W, H), pas=1):
    x0, y0, x1, y1 = box; yy, xx = np.mgrid[y0:y1:pas, x0:x1:pas].astype(np.float32)
    return np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL

def dog(a, s1, s2):
    return cv2.GaussianBlur(a, (0, 0), s1) - cv2.GaussianBlur(a, (0, 0), s2)

def corr(a, b, m):
    a = a[m].astype(np.float64); b = b[m].astype(np.float64); a -= a.mean(); b -= b.mean()
    return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum() + 1e-30))

def desa(path, d):
    Path(path).write_text(json.dumps(d, ensure_ascii=False, indent=1, default=lambda x: x.item() if isinstance(x, np.generic) else (x.tolist() if isinstance(x, np.ndarray) else str(x))) + '\n')
