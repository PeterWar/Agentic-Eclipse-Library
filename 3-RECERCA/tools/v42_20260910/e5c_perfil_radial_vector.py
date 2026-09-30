"""E5c · el vector capa − base EN FUNCIÓ DEL RADI a la protuberància de l'est (sector 160–200°) i, per comparar, a l'oest (340–20°) i al nord (250–290°), per a les capes
12, 10 i 07 de Pere: bandes radials fines des del Sol. Si el vector canvia amb el radi, la base (un compost) no és rígida respecte de les capes (fotogrames sols)."""
import json, numpy as np
from scipy.ndimage import gaussian_filter
from psd_tools import PSDImage
from comu42 import *
import c4_projecte_v42 as C4
C = C4.C; MC = (CX + 14.8, CY + 0.9); RMAX = 20
bG = np.asarray(np.load(CAU42 / 'base_corba_total_v42_u16.npy', mmap_mode='r')[..., 1]).astype(np.float32) / 65535; lb = np.log(np.maximum(bG, 1e-4))
def bp(z): return gaussian_filter(z, 2) - gaussian_filter(z, 12)
yy, xx = np.mgrid[0:H, 0:W]; r = np.hypot(xx - CX, yy - CY) / RS; th = (np.degrees(np.arctan2(yy - CY, xx - CX)) + 360) % 360; rh = np.hypot(xx - MC[0], yy - MC[1])
BASEOK = (rh > 460) & (bG > 0.02) & (bG < 0.999); B = bp(lb)
def brut(a, b, m):
    ys, xs = np.nonzero(m); Y0, Y1, X0, X1 = ys.min() - RMAX - 1, ys.max() + RMAX + 2, xs.min() - RMAX - 1, xs.max() + RMAX + 2
    a = a[Y0:Y1, X0:X1]; b = b[Y0:Y1, X0:X1]; mm = m[Y0:Y1, X0:X1]; cc = np.full((2 * RMAX + 1, 2 * RMAX + 1), np.nan)
    for dy in range(-RMAX, RMAX + 1):
        for dx in range(-RMAX, RMAX + 1):
            m2 = mm & np.roll(np.roll(mm, dy, 0), dx, 1)
            if m2.sum() < 800: continue
            cc[dy + RMAX, dx + RMAX] = float(np.corrcoef(np.roll(np.roll(a, dy, 0), dx, 1)[m2], b[m2])[0, 1])
    if np.all(np.isnan(cc)): return None
    k = np.nanargmax(cc); iy, ix = np.unravel_index(k, cc.shape); return [-(int(ix) - RMAX), -(int(iy) - RMAX), round(float(cc[iy, ix]), 3), int(m.sum())]
s39 = PSDImage.open(C4.F39); n = {l.name: l for l in s39}; rep = {}
SECT = {'est (protuberància) 160–200°': (160, 200), 'oest 340–20°': (340, 20), 'nord 250–290°': (250, 290)}
BANDS = [(1.0, 1.04), (1.04, 1.08), (1.08, 1.13), (1.13, 1.2), (1.2, 1.3), (1.3, 1.45), (1.45, 1.6)]
for nom in ['12 1/3200 perles', '10 1/125', '07 1/15 x2 quar']:
    o = n[nom]; rgb, alpha, mask, box, bg = C.source_arrays(o); x0, y0, x1, y1 = o.bbox; g = np.zeros((H, W), np.float32); g[y0:y1, x0:x1] = rgb[..., 1].astype(np.float32) / 65535
    ok = np.zeros((H, W), bool); ok[y0:y1, x0:x1] = (alpha > 0) if alpha is not None else True; ok &= (g > 0.02) & (g < 0.98); A = bp(np.log(np.maximum(g, 1e-4))); rep[nom] = {}
    for sn, (a0, a1) in SECT.items():
        sm = ((th >= a0) & (th <= a1)) if a0 < a1 else ((th >= a0) | (th <= a1)); row = []
        for r0, r1 in BANDS:
            m = BASEOK & ok & sm & (r >= r0) & (r < r1); res = brut(A, B, m) if m.sum() > 1500 else None; row.append([r0, r1, res])
        rep[nom][sn] = row; print(f'{nom[:2]} {sn:28s}: ' + ' '.join(f"{r0:.2f}–{r1:.2f}:({res[0]:+d},{res[1]:+d})r{res[2]:.2f}" if res else f"{r0:.2f}–{r1:.2f}:n/d" for r0, r1, res in row))
    del rgb, alpha, mask
(REB42 / 'E5c_perfil_radial_vector.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False)); print('E5c fet')
