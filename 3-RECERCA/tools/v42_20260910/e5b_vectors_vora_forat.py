"""E5b · el mateix vector però a la VORA DEL FORAT (on hi ha la costura visible): anell de 460 a 560 px del centre del forat V38, global i per vuit sectors, per a cada
capa 06–12 de Pere contra la base (ln G passa-banda 3–16, contingut vàlid 0,02 < G < 0,98, base fora del forat). D = capa − base."""
import json, numpy as np
from scipy.ndimage import gaussian_filter, shift as scishift
from psd_tools import PSDImage
from comu42 import *
import c4_projecte_v42 as C4
C = C4.C; MC = (CX + 14.8, CY + 0.9); RMAX = 22
bG = np.asarray(np.load(CAU42 / 'base_corba_total_v42_u16.npy', mmap_mode='r')[..., 1]).astype(np.float32) / 65535; lb = np.log(np.maximum(bG, 1e-4))
def bp(z): return gaussian_filter(z, 3) - gaussian_filter(z, 16)
yy, xx = np.mgrid[0:H, 0:W]; rh = np.hypot(xx - MC[0], yy - MC[1]); th = (np.degrees(np.arctan2(yy - MC[1], xx - MC[0])) + 360) % 360
ANELL = (rh > 460) & (rh < 560) & (bG > 0.02) & (bG < 0.999); ys, xs = np.nonzero(ANELL); Y0, Y1, X0, X1 = ys.min() - RMAX - 2, ys.max() + RMAX + 3, xs.min() - RMAX - 2, xs.max() + RMAX + 3
def brut(a, b, m):
    a = a[Y0:Y1, X0:X1]; b = b[Y0:Y1, X0:X1]; mm = m[Y0:Y1, X0:X1]; cc = np.full((2 * RMAX + 1, 2 * RMAX + 1), np.nan)
    for dy in range(-RMAX, RMAX + 1, 2):
        for dx in range(-RMAX, RMAX + 1, 2):
            m2 = mm & np.roll(np.roll(mm, dy, 0), dx, 1)
            if m2.sum() < 1500: continue
            cc[dy + RMAX, dx + RMAX] = float(np.corrcoef(np.roll(np.roll(a, dy, 0), dx, 1)[m2], b[m2])[0, 1])
    k = np.nanargmax(cc); iy, ix = np.unravel_index(k, cc.shape)
    for dy in range(max(iy - 2, 0), min(iy + 3, 2 * RMAX + 1)):
        for dx in range(max(ix - 2, 0), min(ix + 3, 2 * RMAX + 1)):
            if np.isnan(cc[dy, dx]):
                m2 = mm & np.roll(np.roll(mm, dy - RMAX, 0), dx - RMAX, 1)
                if m2.sum() >= 1500: cc[dy, dx] = float(np.corrcoef(np.roll(np.roll(a, dy - RMAX, 0), dx - RMAX, 1)[m2], b[m2])[0, 1])
    k = np.nanargmax(cc); iy, ix = np.unravel_index(k, cc.shape); return [-(int(ix) - RMAX), -(int(iy) - RMAX), float(cc[iy, ix]), int(m.sum())]
B = bp(lb); rep = {}
c = brut(bp(scishift(lb, (3, 10), order=1, mode='nearest')), B, ANELL); rep['control_(+10,+3)'] = c; print('control (+10,+3):', c[:3])
s39 = PSDImage.open(C4.F39); n = {l.name: l for l in s39}
for nom in ['12 1/3200 perles', '11 1/500 limbe', '10 1/125', '09 1/60 x2', '08 1/30 x4 quar', '07 1/15 x2 quar', '06 1/8 x4 quar']:
    o = n[nom]; rgb, alpha, mask, box, bg = C.source_arrays(o); x0, y0, x1, y1 = o.bbox; g = np.zeros((H, W), np.float32); g[y0:y1, x0:x1] = rgb[..., 1].astype(np.float32) / 65535
    ok = np.zeros((H, W), bool); ok[y0:y1, x0:x1] = (alpha > 0) if alpha is not None else True; ok &= (g > 0.02) & (g < 0.98); A = bp(np.log(np.maximum(g, 1e-4)))
    glob = brut(A, B, ANELL & ok); sec = {}
    for a0 in range(0, 360, 45):
        m = ANELL & ok & (th >= a0) & (th < a0 + 45)
        sec[a0] = brut(A, B, m) if m.sum() > 3000 else None
    rep[nom] = {'global_D': glob, 'sectors_D': sec}
    print(f"{nom:18s}: global D ({glob[0]:+d}, {glob[1]:+d}) r {glob[2]:.2f} n {glob[3]} · sectors " + ' '.join(f"{a}°:({v[0]:+d},{v[1]:+d}) r{v[2]:.2f}" if v else f"{a}°:n/d" for a, v in sec.items()))
    del rgb, alpha, mask
(REB42 / 'E5b_vectors_vora_forat.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False)); print('E5b fet')
