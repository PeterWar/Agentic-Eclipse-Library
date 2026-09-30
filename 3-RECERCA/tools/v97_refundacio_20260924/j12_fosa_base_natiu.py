"""j12 (V97) · La fosa de la base (V96 a < 150 px del limbe → nova a > 250 px) al RENDER NATIU del Photoshop (amb les capes d'ajust de Pere):
perfil per distància al limbe (calaixos de 4 px, d 60–330) del quocient V97/V96 per canal i de la seva derivada, per sectors de 45°.
Una costura hi sortiria com un salt o un pic de derivada a 150–250 px que no hi és a fora. Ús: j12_fosa_base_natiu.py <sortida.json>"""
import sys, json
from pathlib import Path
import numpy as np, tifffile
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jutge_comu import *
a = tifffile.imread(ARREL / '4-RESULTATS/v96_nrgf_20260924/vistes/V96_lluna.tif').astype(np.float64); b = tifffile.imread(RES / 'vistes/V97_lluna.tif').astype(np.float64)
x0, y0 = 4600, 3000; yy, xx = np.mgrid[y0:y0 + a.shape[0], x0:x0 + a.shape[1]]; d = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RLLUNA
th = (np.degrees(np.arctan2(-(yy - LLUNA[1]), xx - LLUNA[0])) + 360) % 360; out = {}
for s0 in range(0, 360, 45):
    P = []
    for d0 in range(60, 330, 4):
        m = (d >= d0) & (d < d0 + 4) & (th >= s0) & (th < s0 + 45)
        if m.sum() < 50: P.append(None); continue
        P.append([float(np.median(b[..., c][m]) / max(np.median(a[..., c][m]), 1e-9)) for c in range(3)])
    ok = [p for p in P if p is not None]
    if len(ok) < 10: continue
    Q = np.array([p if p is not None else [np.nan] * 3 for p in P]); dQ = np.abs(np.diff(Q, axis=0)); dd = np.arange(60, 330, 4)[:-1]
    dins = (dd >= 140) & (dd <= 260); fora = ~dins
    out[s0] = dict(quocient_mitja_dins_fosa=np.nanmean(Q[(np.arange(60, 330, 4) >= 150) & (np.arange(60, 330, 4) <= 250)], 0).tolist(), derivada_max_dins=np.nanmax(dQ[dins], 0).tolist(), derivada_max_fora=np.nanmax(dQ[fora], 0).tolist())
desa(sys.argv[1], dict(definicio=__doc__.split('\n')[1], sectors=out))
for k, v in out.items(): print(k, 'derivada màx dins la fosa', [round(x, 4) for x in v['derivada_max_dins']], 'fora', [round(x, 4) for x in v['derivada_max_fora']])
