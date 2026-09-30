"""Rang vàlid per anell solar (0,02 R☉) per a ID3,4,5,7 al llenç: p50 i p95 del canal màxim (research/84 §5: p50≤0,46,
p95≤0,66), mediana G, SNR (mediana / σ del residu passa-alt). Exclou el disc lunar propi (R+3) i els nuclis P3/P4."""
import numpy as np
from scipy import ndimage as ndi
from v3c_lib import *
ell = json.load(open(f'{SCR}/lluna_ellipse_llenc.json'))
xx, yy = canvas_grid(); rs = r_sun(xx, yy)
core3 = np.load(f'{SCR}/masks/core3.npy'); core4 = np.load(f'{SCR}/masks/core4.npy')
bins = np.arange(0.98, 4.6, 0.02)
out = {}
for i in (3, 4, 5, 7):
    mx, _ = layer_maxmin_canvas(i); g = layer_channel_canvas(i, 1)
    d = d_moon(ell[str(i)], xx, yy)
    ok = frame_sel(i) & (d > R_eq(ell[str(i)])+3) & ~core3 & ~core4
    hp = g - ndi.gaussian_filter(g, 2.5)
    idx = np.digitize(rs, bins)-1
    rows = []
    for k in range(len(bins)-1):
        s = (idx == k) & ok
        if s.sum() < 500: continue
        p50, p95 = np.percentile(mx[s], [50, 95]); mg = np.median(g[s]); sg = 1.4826*np.median(np.abs(hp[s]))
        rows.append(dict(r=round(float(0.5*(bins[k]+bins[k+1])), 3), p50=round(float(p50), 4), p95=round(float(p95), 4), medG=round(float(mg), 5), snr=round(float(mg/max(sg, 1e-6)), 1)))
    out[str(i)] = rows
    valid = [r['r'] for r in rows if r['p50'] <= 0.46 and r['p95'] <= 0.66]
    print(f'== ID{i}: 1r anell vàlid {min(valid) if valid else None}; últim amb SNR≥10: {max([r["r"] for r in rows if r["snr"] >= 10] or [None])}; SNR≥5: {max([r["r"] for r in rows if r["snr"] >= 5] or [None])}')
    for r in rows[:12] + rows[12:60:4]:
        print(f"   r={r['r']:.2f}: p50={r['p50']:.3f} p95={r['p95']:.3f} medG={r['medG']:.5f} SNR={r['snr']}")
    del mx, g, hp
jdump(out, f'{SCR}/rang.json')
