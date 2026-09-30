"""Reprodueix el defecte (ABANS): màscara actual de la 1/125 (Corretgint2 → V3b) per sectors de 5° al voltant del centre
lunar, i compost 12+11+10 amb les màscares actuals; PNG del limbe+protuberància."""
import numpy as np
from v3c_lib import *
xx, yy = canvas_grid()
# centre lunar d'ID5 de Corretgint2 desplaçat (−1,−1) (es re-mesura a 02_lluna.py)
cx, cy, R = 4037.03-1, 2738.18-1, 451.71
d = np.hypot(xx-cx, yy-cy); az = np.degrees(np.arctan2(-(yy-cy), xx-cx)) % 360
m5 = old_mask_canvas(5).astype(np.float32)/65535.
sel = frame_sel(5)
out = {}
for (r0, r1) in ((452, 470), (470, 500), (500, 530)):
    rows = {}
    for s0 in range(0, 360, 5):
        z = sel & (d >= r0) & (d < r1) & (az >= s0) & (az < s0+5)
        rows[s0] = round(float(m5[z].mean()), 3)
    out[f'{r0}-{r1}'] = rows
    print(f'màscara ID5, anell {r0}-{r1} px (mitjana per sector de 5°):')
    print('  ', {k: v for k, v in rows.items() if k % 15 == 0})
# anells
ring = {}
for r0 in range(452, 560, 10):
    z = sel & (d >= r0) & (d < r0+10); ring[r0] = round(float(m5[z].mean()), 3)
print('per anells:', ring); out['anells'] = ring
# compost 12+11+10 amb les màscares actuals
base = layer_rgb_canvas(3)
c4 = compose_over(base, 4, old_mask_canvas(4)); c5 = compose_over(c4, 5, old_mask_canvas(5))
np.save(f'{SCR}/states/abans_12_11_10_u16.npy', quantize(c5))
L5 = lum(c5); L4 = lum(c4)
sec = {}
for (r0, r1) in ((455, 470), (470, 500)):
    rows = {}
    for s0 in range(0, 360, 5):
        z = sel & (d >= r0) & (d < r1) & (az >= s0) & (az < s0+5)
        rows[s0] = [round(float(np.median(L5[z])*65535)), round(float(np.median(L4[z])*65535))]
    sec[f'{r0}-{r1}'] = rows
    print(f'compost 12+11+10 vs 12+11, mediana DN anell {r0}-{r1}:', {k: v for k, v in rows.items() if k % 15 == 0})
out['compost_sectors_DN_[12+11+10, 12+11]'] = sec
jdump(out, f'{SCR}/QA/ABANS_mascara_ID5_sectors.json')
# PNG ABANS: retall 1024 a (3578,2653): 12+11 | 12+11+10 | màscara ID5 | log2 ratio
x0, y0 = 3578-512, 2653-512
A = c4[y0:y0+1024, x0:x0+1024]; D = c5[y0:y0+1024, x0:x0+1024]; M = m5[y0:y0+1024, x0:x0+1024]
lo, hi = np.percentile(lum(A), [0.5, 99.5])
ev = np.log2(np.maximum(lum(D), 1e-4)/np.maximum(lum(A), 1e-4)); dv = np.clip(ev/3+0.5, 0, 1)
panel = np.concatenate([stretch(A, lo, hi), stretch(D, lo, hi), np.repeat(M[..., None], 3, 2), np.repeat(dv[..., None], 3, 2)], axis=1)
save_png(panel, f'{SCR}/QA/ABANS_limbe_protuberancia_12_11_vs_12_11_10.png')
print('estirament', lo, hi)
