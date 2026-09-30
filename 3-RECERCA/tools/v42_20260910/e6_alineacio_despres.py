"""E6 · després de moure les capes 06–12 de Pere (+12, +2): re-mesura sobre el V42.psb PUBLICAT.
(1) D = capa − base a l'anell 1,25–1,6 R☉ per vuit sectors (mètode E3f, control exacte) → ha de quedar a ±1 px; (2) cercle de la Lluna (vora fosca del contingut, 720 raigs)
de les capes 12/11/10 contra el forat V38; (3) vistes 1:1: limbe est/oest amb cercles i la protuberància de l'est (base | capa moguda | escaquer)."""
import json, numpy as np, cv2
from scipy.ndimage import gaussian_filter, shift as scishift, map_coordinates
from psd_tools import PSDImage
from comu42 import *
import c4_projecte_v42 as C4
C = C4.C; MC = (CX + 14.8, CY + 0.9); RMAX = 16; PSB = C4.FINAL; MV = C4.MOVIMENTS
bG = np.asarray(np.load(CAU42 / 'base_corba_total_v42_u16.npy', mmap_mode='r')[..., 1]).astype(np.float32) / 65535; lb = np.log(np.maximum(bG, 1e-4))
def bp(z): return gaussian_filter(z, 4) - gaussian_filter(z, 16)
yy, xx = np.mgrid[0:H, 0:W]; r = np.hypot(xx - CX, yy - CY); th = (np.degrees(np.arctan2(yy - CY, xx - CX)) + 360) % 360
def brut(a, b, m):
    ys, xs = np.nonzero(m); y0, y1, x0, x1 = ys.min() - RMAX - 1, ys.max() + RMAX + 2, xs.min() - RMAX - 1, xs.max() + RMAX + 2; a = a[y0:y1, x0:x1]; b = b[y0:y1, x0:x1]; mm = m[y0:y1, x0:x1]
    def c(dx, dy):
        m2 = mm & np.roll(np.roll(mm, dy, 0), dx, 1); return float(np.corrcoef(np.roll(np.roll(a, dy, 0), dx, 1)[m2], b[m2])[0, 1]) if m2.sum() > 1500 else -2
    best = max(((c(dx, dy), dx, dy) for dy in range(-RMAX, RMAX + 1, 2) for dx in range(-RMAX, RMAX + 1, 2))); best = max(((c(dx, dy), dx, dy) for dy in range(best[2] - 2, best[2] + 3) for dx in range(best[1] - 2, best[1] + 3)))
    return [-best[1], -best[2], round(best[0], 3)]
B = bp(lb); rep = {'psb': str(PSB), 'sha256': sha(PSB)}
s = PSDImage.open(PSB); n = {l.name: l for l in s}; capes = {}
for nom in ['12 1/3200 perles', '11 1/500 limbe', '10 1/125', '09 1/60 x2', '08 1/30 x4 quar', '07 1/15 x2 quar', '06 1/8 x4 quar']:
    l = n[nom]; x0, y0, x1, y1 = l.bbox; g = np.zeros((H, W), np.float32); g[y0:y1, x0:x1] = C.channel(l, 1).astype(np.float32) / 65535; al = C.channel(l, -1); a_ = np.zeros((H, W), np.float32); a_[y0:y1, x0:x1] = 1.0 if al is None else al.astype(np.float32) / 65535
    capes[nom] = (g, a_, l.bbox); ok = (a_ > 0) & (g > 0.02) & (g < 0.98); A = bp(np.log(np.maximum(g, 1e-4))); sec = {}
    for a0 in range(0, 360, 45):
        m = (r > 1.25 * RS) & (r < 1.6 * RS) & (th >= a0) & (th < a0 + 45) & (bG > 0.02) & ok; sec[a0] = brut(A, B, m) if m.sum() > 5000 else None
    ok_ = [v for v in sec.values() if v]; med = [float(np.median([v[0] for v in ok_])), float(np.median([v[1] for v in ok_]))] if ok_ else None
    rep[nom] = {'bbox': list(l.bbox), 'D_sectors': sec, 'D_mediana_px': med}
    print(f"{nom:18s} bbox {l.bbox} · D després = " + (f"({med[0]:+.1f}, {med[1]:+.1f}) px" if med else 'n/d') + ' · ' + ' '.join(f"{a}°:({v[0]:+d},{v[1]:+d})" for a, v in sec.items() if v))
# (2) cercle de la Lluna: vora fosca (G·alfa < 0,02) des del centre aproximat (Sol + moviment), 720 raigs, radi entre 420 i 490
def cercle(g, a_, c0):
    ang = np.linspace(0, 2 * np.pi, 720, endpoint=False); rs = np.arange(420, 490, 0.5); pts = []
    for t in ang:
        v = map_coordinates(g * a_, [c0[1] + rs * np.sin(t), c0[0] + rs * np.cos(t)], order=1); k = np.nonzero(v > 0.02)[0]
        if len(k) and 0 < k[0] < len(rs) - 1: pts.append((c0[0] + rs[k[0]] * np.cos(t), c0[1] + rs[k[0]] * np.sin(t)))
    P = np.array(pts); Amat = np.c_[2 * P[:, 0], 2 * P[:, 1], np.ones(len(P))]; bvec = (P ** 2).sum(1); cx, cy, cc = np.linalg.lstsq(Amat, bvec, rcond=None)[0]; R = np.sqrt(cc + cx * cx + cy * cy)
    res = np.hypot(P[:, 0] - cx, P[:, 1] - cy) - R; return {'cx': float(cx), 'cy': float(cy), 'R': float(R), 'rms_px': float(np.std(res)), 'n': int(len(P))}
for nom in ['12 1/3200 perles', '11 1/500 limbe', '10 1/125']:
    g, a_, bb = capes[nom]; cf = cercle(g, a_, (CX + 12, CY + 2)); cf['vs_forat_px'] = [cf['cx'] - MC[0], cf['cy'] - MC[1]]; rep[nom]['lluna'] = cf
    print(f"{nom:18s} Lluna: ({cf['cx']:.1f}, {cf['cy']:.1f}) R {cf['R']:.1f} rms {cf['rms_px']:.2f} n {cf['n']} → respecte del forat ({cf['vs_forat_px'][0]:+.1f}, {cf['vs_forat_px'][1]:+.1f}) px")
(REB42 / 'E6_alineacio_despres.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False))
# (3) vistes
base = np.load(CAU42 / 'base_corba_total_v42_u16.npy', mmap_mode='r'); mk = C.mascara_lluna_inici().astype(np.float32) / 65535; W2 = 300
def crop(img, cx, cy): return np.asarray(img[int(cy) - W2:int(cy) + W2, int(cx) - W2:int(cx) + W2])
def rgb_capa(nom):
    l = n[nom]; x0, y0, x1, y1 = l.bbox; f = np.zeros((H, W, 3), np.float32)
    for c in range(3): f[y0:y1, x0:x1, c] = C.channel(l, c).astype(np.float32) / 65535
    return f * capes[nom][1][..., None]
rows = []
for lab, cx in (('EST', MC[0] - 453.5), ('OEST', MC[0] + 453.5)):
    cy = MC[1]; tiles = []
    for nom in ('12 1/3200 perles', '10 1/125'):
        t = (np.clip(crop(rgb_capa(nom), cx, cy), 0, 1) * 255).astype(np.uint8); t = cv2.cvtColor(t, cv2.COLOR_RGB2BGR); ox, oy = int(cx) - W2, int(cy) - W2
        cv2.circle(t, (int(round((MC[0] - ox) * 16)), int(round((MC[1] - oy) * 16))), int(round(457.5 * 16)), (255, 255, 0), 1, lineType=cv2.LINE_AA, shift=4)
        cf = rep[nom]['lluna']; cv2.circle(t, (int(round((cf['cx'] - ox) * 16)), int(round((cf['cy'] - oy) * 16))), int(round(cf['R'] * 16)), (0, 255, 255), 1, lineType=cv2.LINE_AA, shift=4)
        cv2.putText(t, f'{lab} · capa {nom} MOGUDA ({MV[nom][0]:+d},{MV[nom][1]:+d}) · cian forat · groc la seva Lluna', (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2); tiles.append(t)
    b = crop(base, cx, cy).astype(np.float32) / 65535 * crop(mk, cx, cy)[..., None]; l12 = crop(rgb_capa('12 1/3200 perles'), cx, cy); comp = b + l12 * (1 - crop(mk, cx, cy)[..., None])
    t = cv2.cvtColor((np.clip(comp, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2BGR); cv2.putText(t, f'{lab} · base (forat) sobre la capa 12 moguda', (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2); tiles.append(t)
    row = tiles[0]
    for t in tiles[1:]: row = np.concatenate([row, np.full((2 * W2, 6, 3), 40, np.uint8), t], axis=1)
    rows.append(row)
can = np.concatenate([rows[0], np.full((6, rows[0].shape[1], 3), 40, np.uint8), rows[1]], axis=0); cv2.imwrite(str(VIS42 / 'E6_limbe_est_oest_despres_1a1.png'), can)
# protuberància: base | capa | escaquer (×2)
cx, cy = 4880, 3770; W2 = 200; sq = 25; yy2, xx2 = np.mgrid[0:2 * W2, 0:2 * W2]; chk = (((yy2 // sq) + (xx2 // sq)) % 2 == 0)[..., None]
rows = []
for nom in ('12 1/3200 perles', '10 1/125', '06 1/8 x4 quar'):
    b = crop(base, cx, cy).astype(np.float32) / 65535; l = crop(rgb_capa(nom), cx, cy); e = np.where(chk, b, l); tiles = []
    for im, lab in ((b, 'base corba (sense forat)'), (l, f'capa {nom} moguda'), (e, 'escaquer base/capa (25 px)')):
        t = cv2.resize((np.clip(im, 0, 1) * 255).astype(np.uint8), None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST); t = cv2.cvtColor(t, cv2.COLOR_RGB2BGR); cv2.putText(t, lab, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2); tiles.append(t)
    row = tiles[0]
    for t in tiles[1:]: row = np.concatenate([row, np.full((4 * W2, 6, 3), 40, np.uint8), t], axis=1)
    rows.append(row)
can = rows[0]
for r_ in rows[1:]: can = np.concatenate([can, np.full((6, r_.shape[1], 3), 40, np.uint8), r_], axis=0)
cv2.imwrite(str(VIS42 / 'E6_protuberancia_est_escaquer_x2.png'), can); print('E6 fet')
