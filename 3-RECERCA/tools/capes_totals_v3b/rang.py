"""Rang vàlid per anell solar (bins de 0,02 R☉) per capa: p50 i p95 del canal màxim (llindars research/84 §5: p50 ≤0,46,
p95 ≤0,66), mediana de G, i soroll relatiu (σ del residu passa-alt σ=2,5 px del G / mediana G). S'exclou la Lluna fins a
R+50 px i l'el·lipse de la protuberància (P4)."""
import json, sys, numpy as np
from scipy import ndimage as ndi
from geom import *
def carrega(i):
    if i == 5:
        ch = [np.asarray(np.load(f'{V2B}/src_id5_G.npy', mmap_mode='r')[464:464+H, 458:458+W]) if c == 'G' else
              np.asarray(np.load(f'{V3B}/src_id5_{c}.npy', mmap_mode='r')[464:464+H, 458:458+W]) for c in 'RGB']
    else:
        ch = [np.asarray(np.load(f'{V2B}/src_id{i}_G.npy', mmap_mode='r')) if c == 'G' else np.asarray(np.load(f'{V3B}/src_id{i}_{c}.npy', mmap_mode='r')) for c in 'RGB']
    return ch
xx, yy = grid(); r = r_sun(xx, yy)
# màscara d'exclusió comuna: Lluna (centre d'ID7, R+50) i protuberància (el·lipse 140x160 a local (3578-457, 2653-463))
e7 = ELL['7']; dm = np.hypot(xx-e7['cx'], yy-e7['cy'])
excl = (dm < R_moon(7)+50) | ((((xx-3121)/140.)**2 + ((yy-2190)/160.)**2) < 1)
bins = np.arange(0.98, 4.6, 0.02); idx = np.digitize(r.ravel(), bins)-1
out = {}
for i in [int(s) for s in sys.argv[1:]] or [5, 7, 8, 9, 10]:
    R_, G_, B_ = carrega(i)
    mx = np.maximum(np.maximum(R_, G_), B_).astype(np.float32)/65535.
    g = G_.astype(np.float32)/65535.
    hp = g - ndi.gaussian_filter(g, 2.5)
    ok = ~excl.ravel(); mxf = mx.ravel(); gf = g.ravel(); hpf = hp.ravel()
    rows = []
    for k in range(len(bins)-1):
        s = (idx == k) & ok
        if s.sum() < 500: continue
        p50, p95 = np.percentile(mxf[s], [50, 95]); mg = np.median(gf[s]); sg = 1.4826*np.median(np.abs(hpf[s]))
        rows.append(dict(r=round(float(0.5*(bins[k]+bins[k+1])), 3), p50=round(float(p50), 4), p95=round(float(p95), 4), medG=round(float(mg), 4), snr=round(float(mg/max(sg, 1e-6)), 1)))
    out[i] = rows
    valid = [row['r'] for row in rows if row['p50'] <= 0.46 and row['p95'] <= 0.66]
    print(f'== ID{i}: primer anell vàlid (p50≤0,46 i p95≤0,66): {min(valid) if valid else None} R☉; anells amb SNR<10: {[row["r"] for row in rows if row["snr"] < 10][:3]}…')
    for row in rows[::5]:
        print(f"   r={row['r']:.2f}: p50={row['p50']:.3f} p95={row['p95']:.3f} medG={row['medG']:.4f} SNR={row['snr']}")
    del R_, G_, B_, mx, g, hp
json.dump(out, open('rang.json', 'w'), indent=1)
