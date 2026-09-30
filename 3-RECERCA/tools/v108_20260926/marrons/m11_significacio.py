"""m11 · SIGNIFICACIÓ NO ESBIAIXADA de cada traç a cada capa: la geometria és la de la MARCA de Pere (capa 269; C5 de la V93), amb només
la tolerància del pinzell (desplaçament ±60 px, angle ±1,5°). El nul són 150 segments a l'atzar de la mateixa llargada, a la mateixa distància
del Sol (±25 %), a qualsevol angle, amb la MATEIXA cerca local. p = fracció de nuls amb un solc igual o més profund. Mesura: mitjana al llarg
del contrast fi relatiu (σ 4/40). Si p ≈ 0, el traç és una recta real d'aquella capa; si p ≈ 0,3–0,5, és el que dona el gra.
Sortida: M11_SIGNIFICACIO.json."""
import sys, json, struct
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
R97 = ARREL / '4-RESULTATS/v97_refundacio_20260924'; CR = R97 / 'cadena_raw'; ES = ARREL / '4-RESULTATS/v105_limbe_20260926/claude/estat_v105'
FONTS = {'V107_compost': 'psb', 'L56_P05_WOW_bil': (ES / 'L56_G.npy', None), 'L55_P04_WOW': (ES / 'L55_G.npy', None), 'L41_P01_NRGF': (ES / 'L41_G.npy', None),
         'base_E': (ARREL / '4-RESULTATS/v103_banda_20260926/E/lineal_v103/base_G.npy', None),
         'sony_A': (CR / 'b2_sony_A/cau/sony_A_total_v36.npy', 1), 'sony_B': (CR / 'b2_sony_B/cau/sony_B_total_v42.npy', 1), 'vixen': (R97 / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', 1)}
psb = ARREL / '1-PHOTOSHOP/V107.psb'
with open(psb, 'rb') as fh:
    hdr = fh.read(26); nch = struct.unpack('>H', hdr[12:14])[0]
    n = struct.unpack('>I', fh.read(4))[0]; fh.seek(n, 1); n = struct.unpack('>I', fh.read(4))[0]; fh.seek(n, 1); n = struct.unpack('>Q', fh.read(8))[0]; fh.seek(n, 1); pos = fh.tell()
MM = np.memmap(psb, dtype='>u2', mode='r', offset=pos + 2, shape=(nch, H, W))
rng = np.random.default_rng(20260926); NNUL = 150
import os
TMAX = float(os.environ.get('M11_TMAX', 60)); AMAX = float(os.environ.get('M11_AMAX', 1.5)); NOMS_T = [int(x) for x in os.environ.get('M11_TRACOS', '1,2,3,4,5,6').split(',')]
FILTRE_FONTS = os.environ.get('M11_FONTS'); SUFIX = os.environ.get('M11_SUFIX', '')
TH = np.arange(-AMAX, AMAX + 1e-3, 0.25); TT = np.arange(-TMAX, TMAX + 1, 2.0)
def mapa_r(nom, box):
    x0, y0, x1, y1 = box; f = FONTS[nom]
    if f == 'psb': img = sum(np.asarray(MM[c, y0:y1, x0:x1], np.float32) for c in range(3)) / 3
    else:
        a = np.load(f[0], mmap_mode='r'); img = np.asarray(a[y0:y1, x0:x1] if f[1] is None else a[y0:y1, x0:x1, f[1]], np.float32)
    m = np.isfinite(img) & (img > 0); w = m.astype(np.float32); img = np.where(m, img, 0)
    ng = lambda x, s: cv2.GaussianBlur(x * w, (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-6)
    ok = cv2.erode(w, np.ones((81, 81), np.uint8)) > 0
    return np.where(ok, ng(img, 4) / np.maximum(ng(img, 40), 1e-12) - 1, np.nan).astype(np.float32)
def cerca(r, org, c, d, L):
    best = np.inf
    n0 = np.array([-d[1], d[0]])
    for dth in TH:
        a = np.radians(dth); dd = np.array([d[0] * np.cos(a) - d[1] * np.sin(a), d[0] * np.sin(a) + d[1] * np.cos(a)]); nn = np.array([-dd[1], dd[0]])
        s = np.arange(-L / 2, L / 2 + 1e-6, 3.0)
        X = (c[0] + s[:, None] * dd[0] + TT[None, :] * nn[0]).astype(np.float32); Y = (c[1] + s[:, None] * dd[1] + TT[None, :] * nn[1]).astype(np.float32)
        P = mostreja(r, X, Y, org)
        cov = np.isfinite(P).mean(0)
        with np.errstate(all='ignore'): v = np.where(cov > 0.8, np.nanmean(P, 0), np.inf)
        best = min(best, float(np.min(v)))
    return best
res = {}
if FILTRE_FONTS: FONTS = {k: v for k, v in FONTS.items() if k in FILTRE_FONTS.split(',')}
for tr in [t_ for t_ in TRACOS if t_['k'] in NOMS_T]:
    c0 = tr['centre']; d0 = tr['d']; L = tr['llarg']; rs = np.hypot(c0[0] - SOL[0], c0[1] - SOL[1])
    # segments nuls: mateixa distància al Sol (±25 %), angle qualsevol, dins del llenç i lluny del traç (> 300 px)
    nuls = []
    while len(nuls) < NNUL:
        rr = rs * rng.uniform(0.75, 1.25); ph = rng.uniform(0, 2 * np.pi); c = np.array([SOL[0] + rr * np.cos(ph), SOL[1] + rr * np.sin(ph)])
        an = rng.uniform(0, np.pi); d = np.array([np.cos(an), np.sin(an)])
        e1 = c + d * (L / 2 + 80); e2 = c - d * (L / 2 + 80)
        if min(e1[0], e2[0]) < 100 or min(e1[1], e2[1]) < 100 or max(e1[0], e2[0]) > W - 100 or max(e1[1], e2[1]) > H - 100: continue
        if np.hypot(*(c - c0)) < 300 + L / 2: continue
        nuls.append((c, d))
    res[tr['k']] = {'nom': tr['nom']}
    for nom in FONTS:
        def val(c, d):
            p = np.array([c + d * (L / 2 + 150), c - d * (L / 2 + 150)])
            box = (int(max(0, p[:, 0].min() - 150)), int(max(0, p[:, 1].min() - 150)), int(min(W, p[:, 0].max() + 150)), int(min(H, p[:, 1].max() + 150)))
            r = mapa_r(nom, box)
            return cerca(r, box[:2], c, d, L)
        v0 = val(c0, d0)
        if not np.isfinite(v0): continue
        vn = np.array([val(c, d) for c, d in nuls]); vn = vn[np.isfinite(vn)]
        p = float((np.sum(vn <= v0) + 1) / (len(vn) + 1)); med = float(np.median(vn)); mad = float(1.4826 * np.median(np.abs(vn - med)))
        res[tr['k']][nom] = dict(solc=v0, nul_mediana=med, nul_mad=mad, z=float((v0 - med) / mad), p=p, n_nul=int(len(vn)))
        print(f"T{tr['k']} {nom:16s} solc {v0*1e4:+8.1f}‱  nul {med*1e4:+8.1f}±{mad*1e4:.1f}‱  z {(v0-med)/mad:+5.1f}  p {p:.3f}", flush=True)
desa(OUT / f'M11_SIGNIFICACIO{SUFIX}.json', dict(geometria=f'marca de Pere (C5 V93 / capa 269), ±{TMAX:g} px, ±{AMAX:g}°', n_nul=NNUL, tracos=res))
