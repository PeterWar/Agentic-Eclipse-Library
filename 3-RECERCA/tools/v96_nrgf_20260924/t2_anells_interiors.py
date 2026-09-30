"""t2 (V96) · NRGF amb els ANELLS INTERIORS PARCIALS completats (el mètode que la V36 ja fa servir als anells exteriors: complete_from_partial,
amb el patró azimutal P dels 40 anells complets de sobre, r_in..r_in+40). Sense cap farcit de píxels. Comparació amb la V88 pura (inner = []):
continuïtat del nivell a r_in (el cercle centrat al Sol), nivell per d i sector, i làmina 5:1."""
import sys, json
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v96_nrgf_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v86_neta_20260923')); from v86_operadors import ring_stats, complete_from_partial, NB
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
CX, CY = 5361.768111973117, 3775.747534140857; FONTS = ARREL / '4-RESULTATS/v85_regeneracio_20260922/d4_baseline/products/sources'
Q = np.load(ARREL / '4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; cx, cy, R = [float(v) for v in Q['centre']]
Bh = 760; by0, bx0 = int(CY) - Bh, int(CX) - Bh; sl = (slice(by0, by0 + 2 * Bh), slice(bx0, bx0 + 2 * Bh))
a = np.asarray(np.load(FONTS / 'base_G.npy', mmap_mode='r')[sl], np.float32).copy(); m = (np.asarray(np.load(FONTS / 'support.npy', mmap_mode='r')[sl]) & np.isfinite(a) & (a > 0))
a[qy0 - by0:qy1 - by0, qx0 - bx0:qx1 - bx0] = Q['G']; m[qy0 - by0:qy1 - by0, qx0 - bx0:qx1 - bx0] = Q['domini'] & (Q['G'] > 0); a = np.nan_to_num(a)
yy, xx = np.mgrid[by0:by0 + 2 * Bh, bx0:bx0 + 2 * Bh]; r = np.hypot(xx - CX, yy - CY).astype(np.float32); t = np.arctan2(yy - CY, xx - CX).astype(np.float32)
d = (np.hypot(xx - cx, yy - cy) - R).astype(np.float32); th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
dins = m & (r < 700); ri = np.floor(r).astype('int32'); nr = 702; ids = ri[dins]; v = a[dins].astype('float64'); tb = np.floor((t[dins] + np.pi) / (2 * np.pi) * NB).astype('int32') % NB
count, mean, std = ring_stats(v, ids, nr); nodes = np.arange(nr) + .5; comp = count / (2 * np.pi * nodes); r_in = 469
print('anells parcials interiors: de', int(np.flatnonzero(count > 0)[0]), 'a', r_in - 1, '· completesa a r 450/460/465/468/469/470:', [round(float(comp[k]), 3) for k in (450, 460, 465, 468, 469, 470)])
inner = [i for i in range(r_in) if count[i] > 0]
mean_u, std_u, ok_i, P, varP = complete_from_partial(mean, std, ids, tb, v, inner, list(range(r_in, r_in + 40)))
res = {}
for nom, (mu_, sd_, ok_) in {'V88 (inner=[])': (mean, std, count > 0), 'V96 anells interiors completats': (mean_u, std_u, (count > 0) & ok_i)}.items():
    mu = np.interp(r, nodes[ok_], mu_[ok_]).astype(np.float32); sd = np.interp(r, nodes[ok_], sd_[ok_]).astype(np.float32); z = np.where(dins, (a - mu) / np.maximum(sd, 1e-12), np.nan)
    lo, hi = -2.3811454010009765, 3.09986613345147; X = np.clip((z - lo) / (hi - lo), 0, 1); res[nom] = X
    # continuïtat a r_in per sector (salt del nivell entre r 463-468 i 470-475, a cada sector)
    salts = {}
    for a0, a1 in ((60, 120), (240, 300), (150, 210), (330, 390)):
        s = dins & (((th >= a0) & (th < a1)) | ((th + 360 >= a0) & (th + 360 < a1)))
        salts[f'{a0}-{a1}'] = round(float(np.nanmean(X[s & (r >= 470) & (r < 476)]) - np.nanmean(X[s & (r >= 462) & (r < 468)])), 4)
    print(nom, '| salt de nivell a r_in (470–476 menys 462–468) per sector:', salts)
    print('   nivell per d:', {f'{a0}-{a1}': [round(float(np.nanmean(X[dins & (th >= a0) & (th < a1) & (np.abs(d - dd) < 0.5)])), 3) for dd in (2, 4, 6, 8, 10, 12, 15, 20, 30, 50)] for a0, a1 in ((195, 295), (52, 108), (300, 360), (130, 190))})
np.save(SORT / 't2_display.npy', np.where(dins, res['V96 anells interiors completats'], np.nan).astype(np.float32))
Z = np.load(ARREL / '4-RESULTATS/artefactes_v95_pere_20260924/marques.npz'); mk = np.zeros((7506, 10551), bool)
for k in Z.files:
    if k.startswith('277_') and not k.endswith('origen'): g = Z[k]; ox, oy = Z['277_origen']; mk[oy:oy + g.shape[0], ox:ox + g.shape[1]] |= g
mk = mk[sl]; X95 = PSB(str(ARREL / '1-PHOTOSHOP/V95.psb')).channel(41, 0)[0][sl].astype(np.float32) / 65535
LLOCS = [(245, 8), (270, 8), (85, 8), (60, 8), (215, 8), (160, 8), (330, 6), (20, 6)]; w, zf = 64, 5; rows = []
circ = np.abs(r - r_in) < 0.7
for az, dd in LLOCS:
    px = int(cx + (R + dd) * np.cos(np.radians(az))) - bx0; py = int(cy - (R + dd) * np.sin(np.radians(az))) - by0; row = []
    for X in (X95, res['V88 (inner=[])'], res['V96 anells interiors completats']):
        c = X[py - w // 2:py + w // 2, px - w // 2:px + w // 2]; lo_, hi_ = np.nanpercentile(res['V88 (inner=[])'][py - w // 2:py + w // 2, px - w // 2:px + w // 2], (2, 98))
        im = np.nan_to_num(np.clip((c - lo_) / max(hi_ - lo_, 1e-6), 0, 1), nan=0.5); im = cv2.resize(np.stack([np.uint8(im * 255)] * 3, -1), (w * zf, w * zf), interpolation=cv2.INTER_NEAREST)
        for Mm, col in ((d >= 0, (255, 0, 0)), (circ, (0, 200, 255)), (mk, (255, 120, 0))):
            s = cv2.resize(Mm[py - w // 2:py + w // 2, px - w // 2:px + w // 2].astype(np.uint8), (w * zf, w * zf), interpolation=cv2.INTER_NEAREST)
            v_ = (cv2.dilate(s, np.ones((3, 3), np.uint8)) - cv2.erode(s, np.ones((3, 3), np.uint8))) if Mm is not circ else s
            im[v_ > 0] = col
        row.append(im)
    rows.append((az, row))
Wt = w * zf; F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15); out = Image.new('RGB', (3 * (Wt + 8), len(rows) * (Wt + 24) + 36), 'white'); dr = ImageDraw.Draw(out)
dr.text((6, 8), 'P01 NRGF 5:1 · V95 · V88 pura · V96 (anells interiors completats) · vermell: limbe · blau: cercle r_in=469 del Sol · taronja: marques de Pere', fill='black', font=F)
for j, (az, row) in enumerate(rows):
    for i, im in enumerate(row): out.paste(Image.fromarray(im), (i * (Wt + 8), 36 + j * (Wt + 24) + 20)); dr.text((i * (Wt + 8) + 4, 36 + j * (Wt + 24) + 2), f'{az}° · {("V95", "V88 pura", "V96")[i]}', fill='black', font=F)
out.save(SORT / 'T2_NRGF_5a1.png'); print('fet')
