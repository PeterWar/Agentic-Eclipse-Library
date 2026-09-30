"""c1 (V96) · La P01 NRGF a la vora: la pura de la V88 (E1, només dada) contra la de la V95 (V93: a4v + a5d). Nivell per distància i sector, textura relativa,
i vista a 6:1 a les marques de Pere (capa 277 d'Artefactes_V95). Només lectura."""
import sys, json
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v96_nrgf_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
Q = np.load(ARREL / '4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz'); cx, cy, R = [float(v) for v in Q['centre']]; DMIN = Q['DMIN']; NB = len(DMIN)
B = 700; y0, x0 = int(cy) - B, int(cx) - B; sl = (slice(y0, y0 + 2 * B), slice(x0, x0 + 2 * B))
pura = np.load(ARREL / '4-RESULTATS/v88_20260923/filtres/P01_NRGF_u16.npy', mmap_mode='r')[sl].astype(np.float32) / 65535
v95 = PSB(str(ARREL / '1-PHOTOSHOP/V95.psb')).channel(41, 0)[0][sl].astype(np.float32) / 65535
al = np.load(ARREL / '4-RESULTATS/v94_20260924/wow/P05_WOW_bilateral_alfa_u16.npy', mmap_mode='r')[sl].astype(np.float32) / 65535   # domini de dada (alfa de la V94/V95)
yy, xx = np.mgrid[y0:y0 + 2 * B, x0:x0 + 2 * B]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
dom = al > 0.5; DD = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30, 50]
rep = {}
for nom, X in (('pura_V88', pura), ('V95_capa41', v95)):
    rep[nom] = {f'{a}-{b}': [round(float(X[dom & (th >= a) & (th < b) & (np.abs(d - dd) < 0.5)].mean()), 3) for dd in DD] for a, b in ((195, 295), (52, 108), (300, 360), (130, 190))}
    lap = cv2.Laplacian(cv2.GaussianBlur(X, (0, 0), 1.0), cv2.CV_32F) ** 2
    rep[nom]['textura_1-3_3-6_6-9_9-14_rel_40-70'] = {f'{a}-{b}': [round(float(np.sqrt(lap[dom & (th >= a) & (th < b) & (d >= e0) & (d < e1)].mean() / lap[dom & (th >= a) & (th < b) & (d >= 40) & (d < 70)].mean())), 2) for e0, e1 in ((1, 3), (3, 6), (6, 9), (9, 14))] for a, b in ((195, 295), (52, 108), (300, 360))}
    print(nom, json.dumps(rep[nom]))
print('d:', DD)
(SORT / 'C1_NRGF_VORA.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n')
Z = np.load(ARREL / '4-RESULTATS/artefactes_v95_pere_20260924/marques.npz'); mk = np.zeros((7506, 10551), bool)
for k in Z.files:
    if k.startswith('277_') and not k.endswith('origen'): g = Z[k]; ox, oy = Z['277_origen']; mk[oy:oy + g.shape[0], ox:ox + g.shape[1]] |= g
mk = mk[sl]; dmin = DMIN[(th / 360 * NB).astype(int) % NB]
LLOCS = [(245, 6), (215, 6), (270, 6), (85, 6), (60, 6), (160, 6)]; w, zf = 60, 5; rows = []
for az, dd in LLOCS:
    px = int(cx + (R + dd) * np.cos(np.radians(az))) - x0; py = int(cy - (R + dd) * np.sin(np.radians(az))) - y0; row = []
    for X in (v95, pura):
        c = np.where(dom, X, np.nan)[py - w // 2:py + w // 2, px - w // 2:px + w // 2]; lo, hi = np.nanpercentile(c, (2, 98)); im = np.nan_to_num(np.clip((c - lo) / max(hi - lo, 1e-6), 0, 1), nan=0.5)
        im = cv2.resize(np.stack([np.uint8(im * 255)] * 3, -1), (w * zf, w * zf), interpolation=cv2.INTER_NEAREST)
        for Mm, col in ((d >= 0, (255, 0, 0)), (d >= 9, (0, 255, 255)), (d >= dmin, (255, 230, 0)), (mk, (255, 120, 0))):
            s = cv2.resize(Mm[py - w // 2:py + w // 2, px - w // 2:px + w // 2].astype(np.uint8), (w * zf, w * zf), interpolation=cv2.INTER_NEAREST); v = cv2.dilate(s, np.ones((3, 3), np.uint8)) - cv2.erode(s, np.ones((3, 3), np.uint8)); im[v > 0] = col
        row.append(im)
    rows.append((az, row))
Wt = w * zf; F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15); out = Image.new('RGB', (2 * (Wt + 8), len(rows) * (Wt + 24) + 36), 'white'); dr = ImageDraw.Draw(out)
dr.text((6, 8), 'P01 NRGF a 5:1 · esquerra V95 (V93: a4v + a5d) · dreta NRGF pura V88 (només dada) · vermell d=0, cian d=9, groc DMIN, taronja marques', fill='black', font=F)
for j, (az, row) in enumerate(rows):
    for i, im in enumerate(row): out.paste(Image.fromarray(im), (i * (Wt + 8), 36 + j * (Wt + 24) + 20)); dr.text((i * (Wt + 8) + 4, 36 + j * (Wt + 24) + 2), f'{az}°', fill='black', font=F)
out.save(SORT / 'C1_NRGF_VORA_5a1.png'); print('fet')
