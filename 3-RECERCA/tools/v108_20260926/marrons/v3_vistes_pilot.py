"""v3 · Vistes del LLENÇ SENCER per a Pere (traços marrons i pilot del flat 2D). Totes amb les marques de Pere (capa 269) dibuixades com a contorn fi
i els noms dels traços. Realç declarat a cada vista (el que cal per veure un 1 % o menys).
  VISTA_1  compost fusionat de la V107: contrast relatiu gauss σ8 / σ160 − 1 a ±3 %.
  VISTA_2  la correcció del pilot a la base_G (després / abans − 1), passa alt σ1,5/σ40, a ±0,2 %: les línies del flat que el radial no treia.
  VISTA_3  base_G abans | després: contrast fi σ4/σ60 − 1 a ±0,3 % (dalt abans, baix després).
  VISTA_4  P04 WOW abans | després (el ràster de la capa 55 recalculat), σ3/σ60 a ±12 %.
  VISTA_5  P05 WOW bilateral abans | després (capa 56), σ3/σ60 a ±8 %.
  VISTA_6  el compost amb les màscares de la V107 (m21), abans | després, σ8/σ160 a ±3 % (com la VISTA_1).
Ús: v3_vistes_pilot.py [1,2,3,4,5]"""
import sys, json, struct
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
QUINES = [int(x) for x in (sys.argv[1] if len(sys.argv) > 1 else '1,2,3,4,5').split(',')]
PD = OUT / 'pilot'; LA = ARREL / '4-RESULTATS/v103_banda_20260926/E/lineal_v103'; LD = PD / 'lineal_v108'; PAS = 5
sig = json.loads((OUT / 'M11_SIGNIFICACIO.json').read_text())['tracos']
def marques(rgb, pas=PAS):
    """Els sis traços com a rectangle fi de ±70 px al voltant de la recta de la marca de Pere (capa 269 / C5 de la V93)."""
    for tr in TRACOS:
        c, d, n, L = tr['centre'], tr['d'], tr['n'], tr['llarg']
        q = [c + d * L / 2 + n * 70, c - d * L / 2 + n * 70, c - d * L / 2 - n * 70, c + d * L / 2 - n * 70]
        cv2.polylines(rgb, [np.array([[int(x / pas), int(y / pas)] for x, y in q], np.int32)], True, (40, 110, 230), 1)
        p = c + n * 130; cv2.putText(rgb, f"T{tr['k']}", (int(p[0] / pas), int(p[1] / pas)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (40, 110, 230), 2)
    return rgb
def rel(img, valid, sa, sb):
    w = valid.astype(np.float32); img = np.where(valid, img, 0).astype(np.float32)
    ng = lambda x, s: cv2.GaussianBlur(x * w, (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-6)
    return np.where(valid, ng(img, sa) / np.maximum(ng(img, sb), 1e-12) - 1, 0)
def pinta(r, lim, titol, pas=PAS):
    sm = cv2.resize(r.astype(np.float32), (W // pas, H // pas), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(np.clip(128 + 127 * sm / lim, 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR); rgb = marques(rgb, pas)
    cv2.putText(rgb, titol, (16, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 215, 255), 2); return rgb
def compost_v107():
    psb = ARREL / '1-PHOTOSHOP/V107.psb'
    with open(psb, 'rb') as fh:
        hdr = fh.read(26); nch = struct.unpack('>H', hdr[12:14])[0]
        n = struct.unpack('>I', fh.read(4))[0]; fh.seek(n, 1); n = struct.unpack('>I', fh.read(4))[0]; fh.seek(n, 1); n = struct.unpack('>Q', fh.read(8))[0]; fh.seek(n, 1); pos = fh.tell()
    mm = np.memmap(psb, dtype='>u2', mode='r', offset=pos + 2, shape=(nch, H, W)); return sum(np.asarray(mm[c], np.float32) for c in range(3)) / 3
if 1 in QUINES:
    C = compost_v107(); r = rel(C, C > 0, 8, 160)
    t = 'V107 compost fusionat: contrast relatiu g8/g160 - 1 a +-3 % | ' + ' '.join(f"T{k} p={v['V107_compost']['p']:.3f}" for k, v in sig.items() if 'V107_compost' in v)
    cv2.imwrite(str(OUT / 'VISTA_1_V107_tracos_marrons.png'), pinta(r, 0.03, t)); del C, r
if 2 in QUINES or 3 in QUINES:
    A = np.load(LA / 'base_G.npy').astype(np.float32); D = np.load(LD / 'base_G.npy').astype(np.float32); v = np.isfinite(A) & np.isfinite(D) & (A > 0) & (D > 0)
    if 2 in QUINES:
        q = np.where(v, D / np.where(v, A, 1) - 1, 0).astype(np.float32); w = v.astype(np.float32)
        ng = lambda x, s: cv2.GaussianBlur(x * w, (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-6)
        cv2.imwrite(str(OUT / 'VISTA_2_correccio_flat2d_a_la_base.png'), pinta(np.where(v, ng(q, 1.5) - ng(q, 40), 0), 0.002, 'PILOT flat 2D: base_G despres/abans - 1 (passa alt s1.5/s40) a +-0,2 % = la part no radial del flat que la cadena no treia'))
    if 3 in QUINES:
        ra = pinta(rel(A, v, 4, 60), 0.003, 'base_G ABANS (linealitzada E, V104-V107): contrast fi g4/g60 - 1 a +-0,3 %')
        rd = pinta(rel(D, v, 4, 60), 0.003, 'base_G DESPRES (pilot flat 2D): contrast fi g4/g60 - 1 a +-0,3 %')
        cv2.imwrite(str(OUT / 'VISTA_3_base_abans_despres.png'), np.vstack([ra, np.full((8, ra.shape[1], 3), 60, np.uint8), rd]))
    del A, D, v
for num, tag, lim in ((4, 'P04', 0.12), (5, 'P05', 0.08)):
    if num in QUINES and (PD / f'wow_{tag}_despres_u16.npy').exists():
        im = {et: np.load(PD / f'wow_{tag}_{et}_u16.npy').astype(np.float32) / 65535 for et in ('abans', 'despres')}; v = (im['abans'] != 0.5) | (im['despres'] != 0.5)
        ra = pinta(rel(im['abans'], v, 3, 60), lim, f'{tag} WOW ABANS (base E) : contrast g3/g60 - 1 a +-{lim*100:g} %')
        rd = pinta(rel(im['despres'], v, 3, 60), lim, f'{tag} WOW DESPRES (base amb flat 2D): contrast g3/g60 - 1 a +-{lim*100:g} %')
        cv2.imwrite(str(OUT / f'VISTA_{num}_{tag}_WOW_abans_despres.png'), np.vstack([ra, np.full((8, ra.shape[1], 3), 60, np.uint8), rd])); del im
if 6 in QUINES:
    im = {et: np.load(PD / f'compost_v107mascares_{et}.npy', mmap_mode='r') for et in ('abans', 'despres')}
    ra = pinta(rel(np.asarray(im['abans']), np.asarray(im['abans']) > 0, 8, 160), 0.03, 'Compost amb les mascares de la V107, ABANS (estat E): g8/g160 - 1 a +-3 %')
    rd = pinta(rel(np.asarray(im['despres']), np.asarray(im['despres']) > 0, 8, 160), 0.03, 'Compost amb les mascares de la V107, DESPRES (pilot flat 2D): g8/g160 - 1 a +-3 %')
    cv2.imwrite(str(OUT / 'VISTA_6_compost_mascares_V107_abans_despres.png'), np.vstack([ra, np.full((8, ra.shape[1], 3), 60, np.uint8), rd]))
print('vistes fetes', QUINES)
