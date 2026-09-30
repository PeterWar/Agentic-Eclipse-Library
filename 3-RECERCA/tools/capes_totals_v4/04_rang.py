"""04 — Rang vàlid per anell solar (0,02 R☉, fins a 12 R☉) per a les 12 capes, VERSIÓ V4:
els píxels saturats (plateau del sensor, `sat_i`) queden EXCLUSOS de les estadístiques i es
reporta `sat_frac` per anell. Criteri V4 de validesa: sat_frac≤0,5 i SNR≥5 (re-calibratge V4,
proposta §4.2: els revelats normalitzats són lineals —p50/p95 del codificat mesuraven la
compressió de la corba ACR, que ja no existeix— i el plateau seu a nivell scale_i, que el
criteri antic no detectava). p50/p95 es conserven com a diagnòstic.
SNR = mediana G / σ del residu passa-alt (sobre no saturats)."""
import numpy as np
from scipy import ndimage as ndi
from v4_lib import *

ell = ell_all()
xx, yy = canvas_grid()
rs = r_sun(xx, yy)
core3 = np.load(V4W / 'masks/core3.npy')
core4 = np.load(V4W / 'masks/core4.npy')
bins = np.arange(0.98, 12.0, 0.02)
out = {}
for i in ORDER:
    mx, _ = layer_maxmin_canvas(i)
    g = layer_channel_canvas(i, 1)
    sat = np.load(V4W / 'npy' / f'sat_{i}.npy', mmap_mode='r')
    d = d_moon(ell[str(i)], xx, yy)
    base = frame_sel(i) & (d > R_eq(ell[str(i)]) + 3) & ~core3 & ~core4
    ok = base & ~sat
    hp = g - ndi.gaussian_filter(g, 2.5)
    idx = np.digitize(rs, bins) - 1
    rows = []
    for k in range(len(bins) - 1):
        s = (idx == k) & ok
        sb = (idx == k) & base
        if sb.sum() < 500:
            continue
        sf = float(1.0 - s.sum() / sb.sum())
        if s.sum() < 500:
            rows.append(dict(r=round(float(0.5 * (bins[k] + bins[k + 1])), 3), sat_frac=round(sf, 3)))
            continue
        p50, p95 = np.percentile(mx[s], [50, 95])
        mg = np.median(g[s])
        sg = 1.4826 * np.median(np.abs(hp[s]))
        rows.append(dict(r=round(float(0.5 * (bins[k] + bins[k + 1])), 3), p50=round(float(p50), 4),
                         p95=round(float(p95), 4), medG=round(float(mg), 5),
                         snr=round(float(mg / max(sg, 1e-6)), 1), sat_frac=round(sf, 3)))
    out[str(i)] = rows
    valid = [r['r'] for r in rows if r.get('sat_frac', 1) <= 0.5 and r.get('snr', 0) >= 5]
    plateau = [r['r'] for r in rows if r.get('sat_frac', 0) >= 0.5]
    print(f'== ID{i} ({LAYER_PREFIX[i]}): 1r anell vàlid {min(valid) if valid else None}; '
          f'plateau des de {min(plateau) if plateau else "mai"}; '
          f'SNR≥5 fins {max([r["r"] for r in rows if r.get("snr", 0) >= 5] or [None])}', flush=True)
    del mx, g, hp
jdump(out, V4W / 'rang.json')
