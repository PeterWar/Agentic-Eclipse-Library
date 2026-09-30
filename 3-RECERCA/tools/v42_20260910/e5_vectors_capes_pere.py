"""E5 · vector ENTER per moure cada capa 06–12 de Pere perquè coincideixi amb la base V42, fixat a la PROTUBERÀNCIA PRINCIPAL DE L'EST (esquerra del llenç), com mana Pere:
Pearson per força bruta (ln G passa-banda 3–16 px) a la finestra de la protuberància (sector 160–200° des del Sol, r 1,0–1,35 R☉; només contingut vàlid de la capa
0,02 < G < 0,98 amb alfa > 0, i base fora del forat: r_forat > 460 px), escombrada ±24 px pas 1, pic parabòlic per informar del subpíxel. Cross-check: la mediana dels
vuit sectors 1,25–1,6 R☉ (E3f) i la Lluna de la capa contra el forat (E4). CONTROL: la base contra ella mateixa desplaçada (+10, +3) a la mateixa finestra.
D = desplaçament capa − base; la capa s'ha de moure −D (enter)."""
import json, numpy as np
from scipy.ndimage import gaussian_filter, shift as scishift
from psd_tools import PSDImage
from comu42 import *
import c4_projecte_v42 as C4
C = C4.C; MC = (CX + 14.8, CY + 0.9); RMAX = 24
bG = np.asarray(np.load(CAU42 / 'base_corba_total_v42_u16.npy', mmap_mode='r')[..., 1]).astype(np.float32) / 65535; lb = np.log(np.maximum(bG, 1e-4))
def bp(z): return gaussian_filter(z, 3) - gaussian_filter(z, 16)
yy, xx = np.mgrid[0:H, 0:W]; r = np.hypot(xx - CX, yy - CY); th = (np.degrees(np.arctan2(yy - CY, xx - CX)) + 360) % 360; rh = np.hypot(xx - MC[0], yy - MC[1])
WIN = (r > 1.0 * RS) & (r < 1.35 * RS) & (th >= 160) & (th <= 200); BASEOK = (rh > 460) & (bG > 0.02) & (bG < 0.999)
ys, xs = np.nonzero(WIN); Y0, Y1, X0, X1 = ys.min() - RMAX - 2, ys.max() + RMAX + 3, xs.min() - RMAX - 2, xs.max() + RMAX + 3
def brut(a, b, m):   # a = capa, b = base, m = màscara conjunta (contingut de la capa vàlid & base vàlida & finestra)
    a = a[Y0:Y1, X0:X1]; b = b[Y0:Y1, X0:X1]; mm = m[Y0:Y1, X0:X1]; cc = np.full((2 * RMAX + 1, 2 * RMAX + 1), np.nan)
    for dy in range(-RMAX, RMAX + 1):
        for dx in range(-RMAX, RMAX + 1):
            m2 = mm & np.roll(np.roll(mm, dy, 0), dx, 1)
            if m2.sum() < 2000: continue
            u = np.roll(np.roll(a, dy, 0), dx, 1)[m2]; v = b[m2]; cc[dy + RMAX, dx + RMAX] = float(np.corrcoef(u, v)[0, 1])
    k = np.nanargmax(cc); iy, ix = np.unravel_index(k, cc.shape); dx, dy = ix - RMAX, iy - RMAX; fx = fy = 0.0
    if 0 < ix < 2 * RMAX and np.all(np.isfinite(cc[iy, ix - 1:ix + 2])): y0, y1, y2 = cc[iy, ix - 1:ix + 2]; fx = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) if (y0 - 2 * y1 + y2) != 0 else 0.0
    if 0 < iy < 2 * RMAX and np.all(np.isfinite(cc[iy - 1:iy + 2, ix])): y0, y1, y2 = cc[iy - 1:iy + 2, ix]; fy = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) if (y0 - 2 * y1 + y2) != 0 else 0.0
    # D = capa − base = −(desplaçament aplicat a la capa per coincidir)
    return {'D_px': [-(dx + fx), -(dy + fy)], 'D_enter_px': [-int(dx), -int(dy)], 'r_pic': float(cc[iy, ix]), 'r_zero': float(cc[RMAX, RMAX]), 'n_px': int(m.sum())}
B = bp(lb); rep = {'finestra': 'sector 160–200° des del Sol, r 1,0–1,35 R☉, base fora del forat (> 460 px del centre del forat)', 'convencio': 'D = capa − base; moure la capa −D'}
ctrl = brut(bp(scishift(lb, (3, 10), order=1, mode='nearest')), B, WIN & BASEOK); rep['control_base_(+10,+3)'] = ctrl; print(f"control base desplaçada (+10, +3): D = ({ctrl['D_px'][0]:+.2f}, {ctrl['D_px'][1]:+.2f}) (pic {ctrl['r_pic']:.3f}, a zero {ctrl['r_zero']:.3f})")
e3f = json.loads((REB42 / 'E3f_translacio_sectors.json').read_text()); e4 = json.loads((REB42 / 'E4_radi_lunar_llenc.json').read_text())
s39 = PSDImage.open(C4.F39); n = {l.name: l for l in s39}
for nom in ['12 1/3200 perles', '11 1/500 limbe', '10 1/125', '09 1/60 x2', '08 1/30 x4 quar', '07 1/15 x2 quar', '06 1/8 x4 quar']:
    o = n[nom]; rgb, alpha, mask, box, bg = C.source_arrays(o); x0, y0, x1, y1 = o.bbox; g = np.zeros((H, W), np.float32); g[y0:y1, x0:x1] = rgb[..., 1].astype(np.float32) / 65535
    ok = np.zeros((H, W), bool); ok[y0:y1, x0:x1] = (alpha > 0) if alpha is not None else True; ok &= (g > 0.02) & (g < 0.98)
    res = brut(bp(np.log(np.maximum(g, 1e-4))), B, WIN & BASEOK & ok)
    sect = e3f.get(nom, {}).get('mediana_px'); lluna = e4.get(nom); dl = [MC[0] - lluna['cx'], MC[1] - lluna['cy']] if lluna else None
    res['sectors_1.25_1.6_mediana_D'] = sect; res['lluna_E4_moure_per_coincidir_amb_forat'] = dl; res['moure_px'] = [-res['D_enter_px'][0], -res['D_enter_px'][1]]
    rep[nom] = res; del rgb, alpha, mask
    print(f"{nom:18s}: protuberància D = ({res['D_px'][0]:+.2f}, {res['D_px'][1]:+.2f}) r {res['r_pic']:.3f} (a zero {res['r_zero']:.3f}, {res['n_px']} px) → MOURE ({res['moure_px'][0]:+d}, {res['moure_px'][1]:+d}) · sectors D {sect} · Lluna: moure ({dl[0]:+.1f}, {dl[1]:+.1f})" if dl else f"{nom:18s}: protuberància D = ({res['D_px'][0]:+.2f}, {res['D_px'][1]:+.2f}) r {res['r_pic']:.3f} (a zero {res['r_zero']:.3f}, {res['n_px']} px) → MOURE ({res['moure_px'][0]:+d}, {res['moure_px'][1]:+d}) · sectors D {sect}")
(REB42 / 'E5_vectors_capes_pere.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False)); print('E5 fet')
