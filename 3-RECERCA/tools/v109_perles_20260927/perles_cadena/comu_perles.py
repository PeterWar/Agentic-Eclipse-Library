"""Comú de la diagnosi «perles a la cadena» (V109, 27-09-2026, Claude). Només lectura de tot el que no és 4-RESULTATS/v109_perles_20260927/perles_cadena/.

- fusionat(psb, box): el compost fusionat que desa el Photoshop (secció Image Data, sense compressió), RGB 0–1, d'una finestra.
- q(v): la quantització del Photoshop a 16 bits (15 bits reals), la de b2/v1.
- Geometria: la de jutge_comu (Lluna de presentació, Sol, llenç 10551 × 7506).
"""
import sys, struct
from pathlib import Path
import numpy as np, cv2
R0 = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v97_refundacio_20260924'))
from jutge_comu import comp, W, H, SOL, RSOL, LLUNA, RLLUNA  # noqa: E402,F401
OUT = R0 / '4-RESULTATS/v109_perles_20260927/perles_cadena'
V8 = R0 / '4-RESULTATS/v108_20260926'
CTL = V8 / 'cadena/control'; V108 = V8 / 'cadena/v108'
PSB7 = R0 / '1-PHOTOSHOP/V107.psb'; PSB8 = R0 / '1-PHOTOSHOP/V108.psb'


def _pos_image_data(p):
    with open(p, 'rb') as f:
        hdr = f.read(26); nch = struct.unpack('>H', hdr[12:14])[0]; h, w = struct.unpack('>II', hdr[14:22])
        n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1)
        n = struct.unpack('>Q', f.read(8))[0]; f.seek(n, 1); pos = f.tell(); assert struct.unpack('>H', f.read(2))[0] == 0
    return pos + 2, nch, h, w


def fusionat(p, box):
    pos, nch, h, w = _pos_image_data(p); assert (h, w) == (H, W), (h, w)
    mm = np.memmap(p, dtype='>u2', mode='r', offset=pos, shape=(nch, h, w)); x0, y0, x1, y1 = box
    return np.stack([np.asarray(mm[c, y0:y1, x0:x1], np.float32) / 65535 for c in range(3)], -1)


def q(v):
    v = np.asarray(v).astype(np.int64)
    return (np.round(np.round(v * 32768 / 65535) * 65535 / 32768)).astype(np.uint16)


def lum(C): return (C[..., 0] + 2 * C[..., 1] + C[..., 2]) / 4


def dist_limbe(box):
    x0, y0, x1, y1 = box; yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    return np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RLLUNA


def pa_lluna(box):
    """Angle de posició al voltant de la Lluna, en graus: 0° = dreta (+x), 90° = amunt (−y), 180° = esquerra (les 9 h)."""
    x0, y0, x1, y1 = box; yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    return np.degrees(np.arctan2(-(yy - LLUNA[1]), xx - LLUNA[0])) % 360


def crop(path, box, key=None):
    """Retall d'un .npy del llenç sencer (mmap) o d'una clau d'un .npz."""
    x0, y0, x1, y1 = box
    if key is None: a = np.load(path, mmap_mode='r')
    else: a = np.load(path)[key]
    return np.asarray(a[y0:y1, x0:x1])


def png(path, img, esc=4, lo=None, hi=None, gamma=1.0):
    a = np.asarray(img, np.float32)
    lo = np.nanpercentile(a, 0.5) if lo is None else lo; hi = np.nanpercentile(a, 99.8) if hi is None else hi
    a = np.clip((a - lo) / max(hi - lo, 1e-12), 0, 1) ** gamma
    a = (np.nan_to_num(a) * 255 + 0.5).astype(np.uint8)
    if esc > 1: a = cv2.resize(a, None, fx=esc, fy=esc, interpolation=cv2.INTER_NEAREST)
    if a.ndim == 3: a = a[..., ::-1]
    cv2.imwrite(str(path), a)
