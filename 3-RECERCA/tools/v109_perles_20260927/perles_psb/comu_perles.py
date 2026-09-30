"""Mòdul comú (V109 · perles_psb): geometria, lectura de la pila VISIBLE d'un PSB a una caixa (ràster, alfa, màscara, opacitat i mode reals,
tal com són desats), compositor (jutge_comu.comp, sense les capes d'ajust 239–244), mètriques de trets compactes. Només lectura dels PSB."""
import sys, struct, json
from pathlib import Path
import numpy as np, cv2
R0 = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v73_marques_v71_20260917')); sys.path.insert(0, str(R0 / '3-RECERCA/tools/v97_refundacio_20260924'))
from psb69 import PSB                      # noqa: E402
from jutge_comu import comp                # noqa: E402
OUT = R0 / '4-RESULTATS/v109_perles_20260927/perles_psb'
V107 = R0 / '1-PHOTOSHOP/V107.psb'; V108 = R0 / '1-PHOTOSHOP/V108.psb'
LLUNA = (5375.786804312011, 3775.9774911631); RL = 452.9785129274736
SOL = (5361.768, 3775.748); RSOL = 440.603
CAIXA = (4840, 3240, 5912, 4312)            # tota la Lluna + 60 px
CANVIADES = [3, 54, 41, 42, 47, 49, 51, 45, 46, 55, 56]   # les visibles de les 17 que la V108 regenera (48, 50, 52, 53, 43, 44 són ocultes)
AJUST = {239, 240, 241, 242, 243, 244}


def geom(box):
    x0, y0, x1, y1 = box; yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL
    th = (np.degrees(np.arctan2(-(yy - LLUNA[1]), xx - LLUNA[0])) % 360).astype(np.float32)
    return d, th


def fusionat(p, box):
    """Compost fusionat (Image Data) retallat, 0–1 float32 (h, w, 3)."""
    with open(p, 'rb') as f:
        hdr = f.read(26); nch = struct.unpack('>H', hdr[12:14])[0]; h, w = struct.unpack('>II', hdr[14:22])
        n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>Q', f.read(8))[0]; f.seek(n, 1)
        pos = f.tell(); assert struct.unpack('>H', f.read(2))[0] == 0
    mm = np.memmap(p, dtype='>u2', mode='r', offset=pos + 2, shape=(nch, h, w)); x0, y0, x1, y1 = box
    return np.stack([np.asarray(mm[c, y0:y1, x0:x1], np.float32) / 65535 for c in range(3)], -1)


def capa(P, lid, box):
    """(mode, rgb 0–1 (h,w,3), alfa del ràster, màscara, opacitat 0–1) d'una capa a la caixa, amb la geometria desada."""
    L = P.layer(lid); x0, y0, x1, y1 = box; h, w = y1 - y0, x1 - x0
    rgb = np.stack([P.channel_box(lid, c, box, 0).astype(np.float32) / 65535 for c in (0, 1, 2)], -1)
    a = P.channel_box(lid, -1, box, 0)
    alfa = np.zeros((h, w), np.float32) if a is None else a.astype(np.float32) / 65535
    if a is None:   # sense canal d'alfa: opaca dins del marc de la capa
        alfa[max(L['top'], y0) - y0:min(L['bottom'], y1) - y0, max(L['left'], x0) - x0:min(L['right'], x1) - x0] = 1
    m = L['mask']; masc = np.ones((h, w), np.float32)
    if m is not None and not m['disabled'] and -2 in L['chans']:
        masc = P.channel_box(lid, -2, box, 0).astype(np.float32) / 65535
        # fora del marc de la màscara val el color de fons
        inside = np.zeros((h, w), bool)
        inside[max(m['top'], y0) - y0:max(min(m['bottom'], y1) - y0, 0), max(m['left'], x0) - x0:max(min(m['right'], x1) - x0, 0)] = True
        masc = np.where(inside, masc, m['background'] / 255.0).astype(np.float32)
    return dict(id=lid, nom=L['name'], mode=L['blend'], rgb=rgb, alfa=alfa, masc=masc, op=L['opacity'] / 255.0)


def pila(P, box):
    """Capes visibles (sense les d'ajust), de baix a dalt."""
    return [capa(P, L['id'], box) for L in P.layers if L['visible'] and L['id'] not in AJUST and (L['right'] > L['left'])]


def compon(capes):
    h, w = capes[0]['alfa'].shape
    C, a = comp([(c['mode'], c['rgb'], c['alfa'] * c['masc'] * c['op']) for c in capes], h, w)
    return C


def lum(C):
    return (C[..., 0] + 2 * C[..., 1] + C[..., 2]) / 4


def desa(path, d):
    Path(path).write_text(json.dumps(d, ensure_ascii=False, indent=1, default=lambda x: x.item() if isinstance(x, np.generic) else (x.tolist() if isinstance(x, np.ndarray) else str(x))) + '\n')
