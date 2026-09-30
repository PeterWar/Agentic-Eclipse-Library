"""d3 (V98) · Punt 6 de Pere: anells foscos concèntrics amb la Lluna a 1–9 px del limbe. Perfil per distància al limbe de presentació
(calaixos de 0,5 px, 0–60 px), per sectors de 30°, de: (a) la linealitzada (ln G) i la fusió d4 (ln G) i (b) cada filtre de l'estat donat.
Mesura el «clot»: mínim a 1–9 px menys la mediana a 12–30 px (en unitats del filtre; per ln G, en ln). Estat per defecte: estat_v97."""
import sys, json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v97_refundacio_20260924'))
from jutge_comu import Estat, LLUNA, RLLUNA
est = Path(sys.argv[1]) if len(sys.argv) > 1 else ARREL / '4-RESULTATS/v97_refundacio_20260924/estat_v97'
lin = Path(sys.argv[2]) if len(sys.argv) > 2 else ARREL / '4-RESULTATS/v97_refundacio_20260924/lineal_v97'
out = Path(sys.argv[3]) if len(sys.argv) > 3 else ARREL / '4-RESULTATS/v98_20260925/D3_ANELLS_V97.json'
E = Estat(est); box = (4800, 3200, 5960, 4360); x0, y0, x1, y1 = box
yy, xx = np.mgrid[y0:y1, x0:x1]; d = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RLLUNA; th = (np.degrees(np.arctan2(-(yy - LLUNA[1]), xx - LLUNA[0])) + 360) % 360
nb = np.floor(d / 0.5).astype(int); ok0 = (d >= 0) & (d < 60)
fonts = {'lin_lnG': np.log(np.maximum(np.load(lin / 'base_G.npy', mmap_mode='r')[y0:y1, x0:x1], 1e-6)),
         'd4_lnG': np.log(np.maximum(np.load(ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_v97/d4/products/sources/base_G.npy', mmap_mode='r')[y0:y1, x0:x1], 1e-6))}
rep = dict(estat=str(est), lineal=str(lin), sectors={}, resum={})
def perfil(v, s):
    k = s & ok0; c = np.bincount(nb[k], weights=v[k], minlength=120); n = np.bincount(nb[k], minlength=120)
    return np.where(n > 20, c / np.maximum(n, 1), np.nan)[:120]
capes = [l for l in (41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56) if E.te(l)]
for lid in capes: fonts[f'L{lid}'] = E.rgb(lid, box) if E.rgb(lid, box).ndim == 2 else E.rgb(lid, box)[..., 1]
for nom, v in fonts.items():
    alfa = E.dada(int(nom[1:]), box) if nom.startswith('L') else np.ones(v.shape, np.float32)
    rep['sectors'][nom] = {}; clots = []
    for a0 in range(0, 360, 30):
        s = (((th - a0) % 360) < 30) & (alfa > 0.99)
        p = perfil(v, s); ref = np.nanmedian(p[24:60]); win = p[2:18]
        if np.all(np.isnan(win)): continue
        kmin = int(np.nanargmin(win)) + 2; clot = float(np.nanmin(win) - ref)
        rep['sectors'][nom][f'{a0}-{a0+30}'] = dict(clot=round(clot, 4), d_min=kmin * 0.5 + 0.25, ref=round(float(ref), 4), perfil_0_15px=[None if np.isnan(x) else round(float(x), 4) for x in p[:30]])
        clots.append(clot)
    rep['resum'][nom] = dict(clot_mediana=round(float(np.median(clots)), 4), clot_pitjor=round(float(np.min(clots)), 4))
    print(nom, rep['resum'][nom], {k: (v_['clot'], v_['d_min']) for k, v_ in rep['sectors'][nom].items()}, flush=True)
out.write_text(json.dumps(rep, ensure_ascii=False, indent=1))
