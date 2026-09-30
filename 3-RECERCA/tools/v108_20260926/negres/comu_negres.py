"""Comú de la tasca «zones negres» (V108, 26-09-2026). Emula la pila ràster de la V107 per sota de la 239 (sense capes d'ajust) amb
jutge_comu.comp (el compositor com el Photoshop), i permet: amagar capes, canviar opacitats i SUBSTITUIR el ràster d'un filtre per un
ràster candidat (npy uint16 del llenç sencer, com els de f3). Les màscares i els modes són els de la V107 (llegits del PSB per n0).

Variant = dict lid → 'oculta' | {'F': ruta_npy_u16 (opcional), 'o': opacitat 0–1 (opcional), 'alfa': ruta_npy_u16 (opcional)}.
Composició per franges de files (memòria acotada). Sortida: L = (R + 2G + B)/4 (0–1) i, si cal, el RGB en float16."""
import sys, os, json
from pathlib import Path
import numpy as np, cv2
R0 = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v97_refundacio_20260924'))
from jutge_comu import Estat, comp, W, H, SOL, RSOL, LLUNA, RLLUNA, MARC  # noqa: F401
cv2.setNumThreads(6)
EST7 = R0 / '4-RESULTATS/v108_20260926/negres/estat_v107'
EST5 = R0 / '4-RESULTATS/v105_limbe_20260926/claude/estat_v105'          # Brno 230–233 i estrelles 202 (només per excloure-les de les mètriques)
OUT = R0 / '4-RESULTATS/v108_20260926/negres'
E = Estat(EST7); E5 = Estat(EST5)
FILTRES = (54, 41, 42, 47, 49, 51, 45, 46, 55, 56)                      # visibles a la V107, en l'ordre de la pila
DALT = (305, 306, 258, 76, 224, 267)                                     # ràsters visibles per sobre dels filtres, fins a la 239 exclosa
assert [l for l in E.ordre if l in FILTRES] == list(FILTRES), [l for l in E.ordre if l in FILTRES]
assert all(E.capes[l]['visible'] for l in FILTRES + DALT + (3,))


def lum(C): return (C[..., 0] + 2 * C[..., 1] + C[..., 2]) / 4


def _box_pas(box, pas):
    x0, y0, x1, y1 = box; return x0, y0, x1, y1, len(range(y0, y1, pas)), len(range(x0, x1, pas))


def llegeix_u16(path, box, pas):
    a = np.load(path, mmap_mode='r'); x0, y0, x1, y1 = box
    return np.asarray(a[y0:y1:pas, x0:x1:pas])


class Pila:
    """Tot el que cal per compondre una finestra (box, pas): base, filtres (F en uint16, alfa efectiva en float32), capes de sobre (disperses)."""
    def __init__(self, box=(0, 0, W, H), pas=1):
        self.box, self.pas = box, pas
        self.base = (np.asarray(E.rgb(3, box, pas) * 65535 + 0.5, np.uint16), E.alfa_efectiva(3, box, pas).astype(np.float32))
        self.fil = {}
        for lid in FILTRES:
            c = E.capes[lid]; g = E._llegeix(lid, 'G', box)[::pas, ::pas]
            dada = E.dada(lid, box, pas); m = E._llegeix(lid, 'mascara', box, fill=65535 if (c.get('mascara') or {}).get('background') == 255 else 0)
            m = np.ones_like(dada) if m is None else np.asarray(m[::pas, ::pas], np.float32) / 65535
            self.fil[lid] = dict(mode=c['mode'], F=np.ascontiguousarray(g), am=(dada * m).astype(np.float32), dada=None, o=c['opacitat'] / 255.0); del dada, m
        self.dalt = []
        for lid in DALT:
            a = E.alfa_efectiva(lid, box, pas); idx = np.nonzero(a > 0)
            if len(idx[0]) == 0: continue
            F = E.rgb(lid, box, pas)
            if F.ndim == 2: F = np.repeat(F[..., None], 3, 2)
            self.dalt.append((lid, E.capes[lid]['mode'], idx, F[idx].astype(np.float32), a[idx].astype(np.float32)))

    def capes(self, esp, y0, y1):
        """Llista (mode, F float32, alfa) per a les files y0:y1 (en píxels de la finestra), amb la variant `esp` aplicada."""
        C, a0 = self.base; out = [('NORMAL', C[y0:y1].astype(np.float32) / 65535, a0[y0:y1])]
        for lid in FILTRES:
            e = esp.get(lid)
            if e == 'oculta': continue
            f = self.fil[lid]; e = e or {}
            if 'F' in e:
                F = e['_F'][y0:y1].astype(np.float32) / 65535
            else: F = f['F'][y0:y1].astype(np.float32) / 65535
            o = e.get('o', f['o'])
            if 'alfa' in e: raise NotImplementedError('alfa candidata: cal la màscara separada')
            out.append((f['mode'], F, f['am'][y0:y1] * o))
        return out

    def prepara(self, esp):
        """Carrega (una vegada) els ràsters candidats de la variant."""
        for lid, e in esp.items():
            if isinstance(e, dict):
                if 'F' in e and '_F' not in e: e['_F'] = llegeix_u16(e['F'], self.box, self.pas)
                if 'alfa' in e and '_alfa' not in e: e['_alfa'] = llegeix_u16(e['alfa'], self.box, self.pas)
        return esp

    def compon(self, esp=None, rgb=False, franja=768):
        esp = self.prepara(esp or {}); h, w = self.base[1].shape
        L = np.empty((h, w), np.float32); RGB = np.empty((h, w, 3), np.float16) if rgb else None
        for y0 in range(0, h, franja):
            y1 = min(h, y0 + franja); Cb, ab = comp(self.capes(esp, y0, y1), y1 - y0, w)
            L[y0:y1] = lum(Cb)
            if rgb: RGB[y0:y1] = Cb
        if self.dalt:   # capes disperses de sobre (puntuals): recomposició exacta de la franja de files on n'hi ha, en ordre
            ys = np.unique(np.concatenate([idx[0] for _, _, idx, _, _ in self.dalt]))
            yset = np.zeros(h, bool); yset[ys] = True
            rows = np.flatnonzero(yset); r0, r1 = rows.min(), rows.max() + 1
            Cb, ab = comp(self.capes(esp, r0, r1), r1 - r0, w)
            for lid, mode, idx, Fs, As in self.dalt:
                ii = (idx[0] - r0, idx[1]); n = len(ii[0])
                sub, asub = comp([('NORMAL', Cb[ii].reshape(n, 1, 3), ab[ii].reshape(n, 1)), (mode, Fs.reshape(n, 1, 3), As.reshape(n, 1))], n, 1)
                Cb[ii] = sub.reshape(n, 3); ab[ii] = asub.reshape(n)
            L[r0:r1] = lum(Cb)
            if rgb: RGB[r0:r1] = Cb
        return (L, RGB) if rgb else L


def radi(box=(0, 0, W, H), pas=1):
    x0, y0, x1, y1 = box; yy, xx = np.mgrid[y0:y1:pas, x0:x1:pas].astype(np.float32)
    return np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL, np.degrees(np.arctan2(-(yy - SOL[1]), xx - SOL[0])) % 360


BANDES = [(1.02, 1.3), (1.3, 2.0), (2.0, 3.0), (3.0, 4.5), (4.5, 7.0), (7.0, 99.0)]
NB = lambda b: f'{b[0]:g}-{b[1]:g}' if b[1] < 50 else f'>{b[0]:g}'


def mascares(box, pas):
    """ok = dins del llenç amb base (erosió 150 px de la vora), fora de les estrelles (202 de la V105 dilatada 8 px, només per excloure residus),
    fora de la cantonada del logo i del disc lunar + 3 px."""
    x0, y0, x1, y1 = box; r, th = radi(box, pas)
    valid = E.alfa_efectiva(3, box, pas) > 0.5; k = max(3, int(150 / pas)) | 1
    valid = cv2.erode(valid.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))) > 0
    a202 = E5.alfa_efectiva(202, box, pas) > 0; ks = int(17 / pas) | 1
    est = cv2.dilate(a202.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ks, ks))) > 0
    ex = est.copy(); bx = (8228, 5187, 9351, 6264)
    ex[max(0, (bx[1] - y0 - 60) // pas):max(0, (bx[3] - y0 + 60) // pas), max(0, (bx[0] - x0 - 60) // pas):max(0, (bx[2] - x0 + 60) // pas)] = True
    yy, xx = np.mgrid[y0:y1:pas, x0:x1:pas].astype(np.float32)
    lluna = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) < RLLUNA + 3
    marc = np.zeros_like(valid)
    marc[max(0, (MARC[1] - y0) // pas):max(0, (MARC[3] - y0) // pas), max(0, (MARC[0] - x0) // pas):max(0, (MARC[2] - x0) // pas)] = True
    return dict(r=r, th=th, ok=valid & ~ex & ~lluna, marc=marc)


def logL(L): return np.log(np.maximum(L, 1e-3)).astype(np.float32)


def dog(a, s1, s2):
    g1 = a if s1 == 0 else cv2.GaussianBlur(a, (0, 0), s1)
    return g1 - cv2.GaussianBlur(a, (0, 0), s2)


def cel_local(L, r, th, ok):
    """Cel del mateix sector de 10° a 6,5–8,5 R☉ (mediana; mediana mòbil de 3 sectors; interpolació lineal en θ)."""
    s = (r >= 6.5) & (r < 8.5) & ok & (L > 1e-3); sec = (th // 10).astype(int) % 36
    v = np.array([np.median(L[s & (sec == i)]) if (s & (sec == i)).sum() > 300 else np.nan for i in range(36)])
    idx = np.arange(36); good = ~np.isnan(v); v = np.interp(idx, idx[good], v[good], period=36)
    vv = np.concatenate([v[-1:], v, v[:1]]); v = np.array([np.median(vv[i:i + 3]) for i in range(36)])
    x = th / 10 - 0.5; i0 = np.floor(x).astype(int) % 36; f = x - np.floor(x)
    return v, ((1 - f) * v[i0] + f * v[(i0 + 1) % 36]).astype(np.float32)


def desa(path, d):
    Path(path).write_text(json.dumps(d, ensure_ascii=False, indent=1, default=lambda x: x.item() if isinstance(x, np.generic) else (x.tolist() if isinstance(x, np.ndarray) else str(x))) + '\n')
