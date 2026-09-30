"""E3f · TRANSLACIÓ de les capes 06–12 de Pere respecte de la base V42, per força bruta (Pearson dins del solapament, sense màscara comuna): ln G passa-banda 4–16 px
a l'anell 1,25–1,6 R☉ per sectors de 45°, només on la capa té contingut vàlid (0,02 < G < 0,98) i la base també; escombrada ±20 px (pas 2) + refinament ±2 (pas 1).
D = desplaçament de la capa respecte de la base (positiu = la capa és més a l'oest/avall). CONTROL: la base contra ella mateixa desplaçada +10 px en x → D = (+10, 0).
Mètode de l'escèptic de la verificació del 10-09 (s8_brut_net.py), adoptat. ⛔ L'E3 (correlació de fase amb la MATEIXA màscara als dos costats) quedava clavada a zero
(control de 10 px → 0,1 px): research/125 ja ho deia («la finestra ha de ser lliure a TOTES DUES imatges»). Les finestres quadrades a 1,4 R☉ tampoc no valen (hi entra el forat)."""
import json, numpy as np
from scipy.ndimage import gaussian_filter, shift as scishift
from psd_tools import PSDImage
from comu42 import *
import c4_projecte_v42 as C4
C = C4.C; R0, R1 = 1.25, 1.6; S1, S2 = 4, 16
bG = np.asarray(np.load(CAU42 / 'base_corba_total_v42_u16.npy', mmap_mode='r')[..., 1]).astype(np.float32) / 65535; lb = np.log(np.maximum(bG, 1e-4))
def bp(z): return gaussian_filter(z, S1) - gaussian_filter(z, S2)
yy, xx = np.mgrid[0:H, 0:W]; r = np.hypot(xx - CX, yy - CY); th = (np.degrees(np.arctan2(yy - CY, xx - CX)) + 360) % 360
def brut(a, b, m):
    ys, xs = np.nonzero(m); y0, y1, x0, x1 = ys.min() - 25, ys.max() + 26, xs.min() - 25, xs.max() + 26; a = a[y0:y1, x0:x1]; b = b[y0:y1, x0:x1]; mm = m[y0:y1, x0:x1]
    def c(dx, dy):
        m2 = mm & np.roll(np.roll(mm, dy, 0), dx, 1); u = np.roll(np.roll(a, dy, 0), dx, 1)[m2]; v = b[m2]; return float(np.corrcoef(u, v)[0, 1])
    best = max(((c(dx, dy), dx, dy) for dy in range(-20, 21, 2) for dx in range(-20, 21, 2))); best = max(((c(dx, dy), dx, dy) for dy in range(best[2] - 2, best[2] + 3) for dx in range(best[1] - 2, best[1] + 3)))
    return best, c(0, 0)
def mesura(a, b, gm, lab):
    out = []
    for a0 in range(0, 360, 45):
        m = (r > R0 * RS) & (r < R1 * RS) & (th >= a0) & (th < a0 + 45) & (bG > 0.02)
        if gm is not None: m &= (gm > 0.02) & (gm < 0.98)
        if m.sum() < 5000: out.append([a0, None, None, None, None]); continue
        (cb, dx, dy), c0 = brut(a, b, m); out.append([a0, -dx, -dy, cb, c0])
    ok = [o for o in out if o[1] is not None]; med = [float(np.median([o[1] for o in ok])), float(np.median([o[2] for o in ok]))] if ok else None
    print(f'{lab:26s}: D mediana ' + (f'({med[0]:+.0f}, {med[1]:+.0f}) px' if med else 'n/d (sense contingut vàlid a l\'anell)') + ' · per sector ' + ' '.join(f"{o[0]}°:({o[1]:+d},{o[2]:+d}) r{o[3]:.2f}/{o[4]:.2f}" for o in ok)); return {'per_sector_[az,Dx,Dy,r,r0]': out, 'mediana_px': med}
B = bp(lb); rep = {'metode': 'Pearson força bruta, ln G passa-banda 4–16, anell 1,25–1,6 R☉, sectors 45°, màscara de contingut vàlid; D = desplaçament capa − base'}
rep['control_base_+10x'] = mesura(bp(scishift(lb, (0, 10), order=1, mode='nearest')), B, None, 'CONTROL base +10 px en x')
s39 = PSDImage.open(C4.F39); n = {l.name: l for l in s39}
for nom in ['12 1/3200 perles', '11 1/500 limbe', '10 1/125', '09 1/60 x2', '08 1/30 x4 quar', '07 1/15 x2 quar', '06 1/8 x4 quar']:
    l = n[nom]; x0, y0, x1, y1 = l.bbox; g = np.zeros((H, W), np.float32); g[y0:y1, x0:x1] = C.channel(l, 1).astype(np.float32) / 65535
    rep[nom] = mesura(bp(np.log(np.maximum(g, 1e-4))), B, g, nom)
(REB42 / 'E3f_translacio_sectors.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False)); print('E3f fet')
