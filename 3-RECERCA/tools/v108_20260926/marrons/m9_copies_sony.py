"""m9 · Si un traç de la Sony és fix al SENSOR, a l'altre apuntament hi ha d'haver una CÒPIA desplaçada pel salt de muntura (el marc de B
és el d'A desplaçat (+482, +1001) px al llenç: vores de M2). Per a cada traç i cada apilat (Sony A, Sony B), es mesura el solc fi (σ 4/40)
a la recta del traç (M3) i a les rectes desplaçades ±(482, 1001), amb una cerca local (±30 px, ±1°) i un control nul (rectes paral·leles
a 120–600 px de cada candidata). Sortida: M9_COPIES_SONY.json."""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
g = json.loads((OUT / 'M3_GEOMETRIA.json').read_text()); CR = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw'
FONTS = {'sony_A': CR / 'b2_sony_A/cau/sony_A_total_v36.npy', 'sony_B': CR / 'b2_sony_B/cau/sony_B_total_v42.npy'}
SALT = np.array([482.0, 1001.0])
TH = np.arange(-1.0, 1.001, 0.1); TT = np.arange(-30, 31, 1.0); NUL = np.concatenate([np.arange(-600, -119, 12), np.arange(120, 601, 12)]).astype(float)
res = {}
for tr0 in TRACOS:
    z = g[str(tr0['k'])]; res[tr0['k']] = {}
    for desp_nom, desp in (('al_seu_lloc', 0.0), ('mes_salt', 1.0), ('menys_salt', -1.0)):
        tr = dict(tr0, centre=np.array(z['centre']) + desp * SALT, d=np.array(z['direccio'])); tr['n'] = np.array([-tr['d'][1], tr['d'][0]])
        box = caixa(tr, 700); x0, y0, x1, y1 = box
        if x1 - x0 < 200 or y1 - y0 < 200: continue
        for nom, p in FONTS.items():
            img = np.asarray(np.load(p, mmap_mode='r')[y0:y1, x0:x1, 1], np.float32); m = np.isfinite(img) & (img > 0); w = m.astype(np.float32); img = np.where(m, img, 0)
            ng = lambda x, s: cv2.GaussianBlur(x * w, (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-6)
            r = np.where(m & (cv2.erode(w, np.ones((81, 81), np.uint8)) > 0), ng(img, 4) / np.maximum(ng(img, 40), 1e-12) - 1, np.nan).astype(np.float32)
            def val(dth, t0):
                s, t, X, Y = graella(tr, tmax=0, dt=1, ds=3, dtheta=dth, dt0=t0); P = mostreja(r, X, Y, (x0, y0))
                return float(np.nanmean(P)) if np.isfinite(P).mean() > 0.7 else np.nan
            M = np.array([[val(a, b) for b in TT] for a in TH])
            if not np.isfinite(M).any(): continue
            i, j = np.unravel_index(np.nanargmin(M), M.shape)
            nul = np.array([val(TH[i], TT[j] + q) for q in NUL]); nul = nul[np.isfinite(nul)]
            if len(nul) < 20: continue
            med = np.median(nul); mad = 1.4826 * np.median(np.abs(nul - med))
            # el mínim d'una cerca local també té biaix: el nul es fa amb la mateixa cerca a cada recta nul·la (21×61) → aproximació: z corregit
            z0 = (M[i, j] - med) / mad
            res[tr0['k']][f'{nom}@{desp_nom}'] = dict(dtheta=float(TH[i]), t=float(TT[j]), valor=float(M[i, j]), z=float(z0), valor_sense_cerca=float(M[len(TH) // 2, len(TT) // 2]), z_sense_cerca=float((M[len(TH) // 2, len(TT) // 2] - med) / mad), cobertura_ok=True)
            print(f"T{tr0['k']} {nom:7s} {desp_nom:12s} cerca dθ {TH[i]:+.1f} t {TT[j]:+3.0f} → {M[i, j]*1e4:+.1f}‱ z {z0:+.1f} | sense cerca {M[len(TH)//2, len(TT)//2]*1e4:+.1f}‱ z {(M[len(TH)//2, len(TT)//2]-med)/mad:+.1f}", flush=True)
desa(OUT / 'M9_COPIES_SONY.json', dict(salt_A_a_B_px=SALT, nota='z de la cerca local té biaix (mínim de 1.281 rectes): un z de −3,5 és el que dona el soroll; z_sense_cerca és l\'avaluació a la recta exacta', tracos=res))
