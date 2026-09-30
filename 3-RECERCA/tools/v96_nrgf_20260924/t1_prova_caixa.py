"""t1 (V96) · NRGF V96 a la caixa del Sol (r < 700 sencers): (1) reproducció de la V88 lluny de la Lluna, (2) nivell i textura a la vora, (3) làmina 5:1
a les marques de Pere, contra la V88 pura i la V95. També: fins on tapa l'Earthshine (258) a sobre (la 41 és en Multiplicar: transparent ≠ neutre)."""
import sys, json
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v96_nrgf_20260924'
sys.path.insert(0, str(Path(__file__).parent)); from nrgf_v96 import nrgf_v96
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v95_20260924')); from wow_v95 import desplacament_cresta, dmap_vora
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
CX, CY = 5361.768111973117, 3775.747534140857; FONTS = ARREL / '4-RESULTATS/v85_regeneracio_20260922/d4_baseline/products/sources'
Q = np.load(ARREL / '4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; cx, cy, R = [float(v) for v in Q['centre']]; DMIN = Q['DMIN']; NB = len(DMIN)
Bh = 760; by0, bx0 = int(CY) - Bh, int(CX) - Bh; sl = (slice(by0, by0 + 2 * Bh), slice(bx0, bx0 + 2 * Bh))
a = np.asarray(np.load(FONTS / 'base_G.npy', mmap_mode='r')[sl], np.float32).copy(); m = (np.asarray(np.load(FONTS / 'support.npy', mmap_mode='r')[sl]) & np.isfinite(a) & (a > 0))
a[qy0 - by0:qy1 - by0, qx0 - bx0:qx1 - bx0] = Q['G']; m[qy0 - by0:qy1 - by0, qx0 - bx0:qx1 - bx0] = Q['domini'] & (Q['G'] > 0); a = np.nan_to_num(a)
yy, xx = np.mgrid[by0:by0 + 2 * Bh, bx0:bx0 + 2 * Bh]; r = np.hypot(xx - CX, yy - CY).astype(np.float32)
d = (np.hypot(xx - cx, yy - cy) - R).astype(np.float32); th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
off, _ = desplacament_cresta(Q['G'], Q['domini'] & (Q['G'] > 0), (qy0, qx0), cx, cy, R); dv = dmap_vora(d, xx, yy, cx, cy, off)
z88 = np.load(ARREL / '4-RESULTATS/v88_20260923/filtres/P01_NRGF_float.npy', mmap_mode='r')[sl].astype(np.float32)
res = {}
for D in (12.0,):
    z, info = nrgf_v96(a, m, r, dv, D_NET=D); res[f'D{int(D)}'] = info; print('info', json.dumps(info))
    far = m & (r > 520) & (r < 690); print('reproducció V88 lluny (520<r<690): màx |z−z88|', float(np.nanmax(np.abs(z[far] - z88[far]))))
lo, hi = -2.3811454010009765, 3.09986613345147; disp = lambda Z: np.clip((Z - lo) / (hi - lo), 0, 1)
X96 = np.where(m, disp(z), np.nan); X88 = np.where(m, disp(z88), np.nan); np.save(SORT / 't1_display.npy', X96.astype(np.float32))
v95 = PSB(str(ARREL / '1-PHOTOSHOP/V95.psb')); X95 = v95.channel(41, 0)[0][sl].astype(np.float32) / 65535
DD = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30, 50]
for nom, X in (('V88_pura', X88), ('V95', X95), ('V96', X96)):
    print(nom, {f'{a0}-{a1}': [round(float(np.nanmean(X[m & (th >= a0) & (th < a1) & (np.abs(d - dd) < 0.5)])), 3) for dd in DD] for a0, a1 in ((195, 295), (52, 108), (300, 360), (130, 190), (0, 360))})
print('d:', DD)
# Earthshine 258 per sobre: alfa per d
al258, (ox, oy) = v95.channel(258, -1); A258 = np.zeros((7506, 10551), np.float32); A258[oy:oy + al258.shape[0], ox:ox + al258.shape[1]] = al258.astype(np.float32) / 65535; A258 = A258[sl]
dmin = DMIN[(th / 360 * NB).astype(int) % NB]
print('Earthshine 258 alfa per d (−2..6):', [round(float(A258[np.abs(d - dd) < 0.5].mean()), 3) for dd in (-2, -1, 0, 1, 2, 3, 4, 5, 6)], '| DMIN (px) p5/50/95:', np.percentile(DMIN, (5, 50, 95)).round(2).tolist())
print('Buit sense dada (d entre 0 i DMIN) tapat per la 258 (alfa>0,9):', round(float((A258[(d > 0) & (d < dmin)] > 0.9).mean()), 3))
Z = np.load(ARREL / '4-RESULTATS/artefactes_v95_pere_20260924/marques.npz'); mk = np.zeros((7506, 10551), bool)
for k in Z.files:
    if k.startswith('277_') and not k.endswith('origen'): g = Z[k]; ox, oy = Z['277_origen']; mk[oy:oy + g.shape[0], ox:ox + g.shape[1]] |= g
mk = mk[sl]
LLOCS = [(245, 6), (215, 6), (270, 6), (85, 6), (60, 6), (160, 6), (330, 6), (20, 6)]; w, zf = 60, 5; rows = []
for az, dd in LLOCS:
    px = int(cx + (R + dd) * np.cos(np.radians(az))) - bx0; py = int(cy - (R + dd) * np.sin(np.radians(az))) - by0; row = []
    for X in (X95, X88, X96):
        c = X[py - w // 2:py + w // 2, px - w // 2:px + w // 2]; lo_, hi_ = np.nanpercentile(X88[py - w // 2:py + w // 2, px - w // 2:px + w // 2], (2, 98))
        im = np.nan_to_num(np.clip((c - lo_) / max(hi_ - lo_, 1e-6), 0, 1), nan=0.5); im = cv2.resize(np.stack([np.uint8(im * 255)] * 3, -1), (w * zf, w * zf), interpolation=cv2.INTER_NEAREST)
        for Mm, col in ((d >= 0, (255, 0, 0)), (d >= 9, (0, 255, 255)), (mk, (255, 120, 0))):
            s = cv2.resize(Mm[py - w // 2:py + w // 2, px - w // 2:px + w // 2].astype(np.uint8), (w * zf, w * zf), interpolation=cv2.INTER_NEAREST); v = cv2.dilate(s, np.ones((3, 3), np.uint8)) - cv2.erode(s, np.ones((3, 3), np.uint8)); im[v > 0] = col
        row.append(im)
    rows.append((az, row))
Wt = w * zf; F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15); out = Image.new('RGB', (3 * (Wt + 8), len(rows) * (Wt + 24) + 36), 'white'); dr = ImageDraw.Draw(out)
dr.text((6, 8), 'P01 NRGF 5:1 (mateix contrast a les tres) · V95 (V93) · V88 pura · V96 prova · vermell d=0, cian d=9, taronja marques de Pere', fill='black', font=F)
for j, (az, row) in enumerate(rows):
    for i, im in enumerate(row): out.paste(Image.fromarray(im), (i * (Wt + 8), 36 + j * (Wt + 24) + 20)); dr.text((i * (Wt + 8) + 4, 36 + j * (Wt + 24) + 2), f'{az}° · {("V95", "V88 pura", "V96")[i]}', fill='black', font=F)
out.save(SORT / 'T1_NRGF_5a1.png'); print('fet')
