"""t6 · Làmina a 4:1: V94 (56 tal com és a WOW.psb, ràster × alfa sobre gris 0,5) contra la prova t4 (parells simètrics, sense cap correcció
posterior), amb les marques de Pere perfilades. Finestres de 90 px centrades a les marques vermelles, liles i verdes. Contrast estirat ×4
al voltant de 0,5 perquè les diferències de nivell de ±0,02–0,08 es vegin igual que en Superposar."""
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; S = ARREL / '4-RESULTATS/v95_20260924'
Q = np.load(ARREL / '4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz'); cx, cy, R = [float(v) for v in Q['centre']]; B = 1200; bx0, by0 = int(cx) - B, int(cy) - B
t4 = np.load(S / 't9_display.npy'); m = np.isfinite(np.load(S / 't9_q.npy'))
v94 = np.load(ARREL / '4-RESULTATS/v94_20260924/wow/P05_WOW_bilateral_u16.npy', mmap_mode='r')[by0:by0 + 2 * B, bx0:bx0 + 2 * B].astype(np.float32) / 65535
al = np.load(ARREL / '4-RESULTATS/v94_20260924/wow/P05_WOW_bilateral_alfa_u16.npy', mmap_mode='r')[by0:by0 + 2 * B, bx0:bx0 + 2 * B].astype(np.float32) / 65535
V94 = 0.5 + al * (v94 - 0.5); T4 = np.where(m, t4, 0.5)
Z = np.load(ARREL / '4-RESULTATS/wow_marques_pere_20260924/marques.npz'); x0, y0 = Z['272_origen']
def marca(nom):
    mm = Z[f'272_{nom}']; out = np.zeros((2 * B, 2 * B), bool); ys, xs = slice(max(0, y0 - by0), min(2 * B, y0 - by0 + mm.shape[0])), slice(max(0, x0 - bx0), min(2 * B, x0 - bx0 + mm.shape[1]))
    out[ys, xs] = mm[ys.start - (y0 - by0):ys.stop - (y0 - by0), xs.start - (x0 - bx0):xs.stop - (x0 - bx0)]; return out
COL = {'to_350_360': (255, 0, 40), 'to_280_290': (190, 0, 255), 'to_100_110': (60, 230, 20), 'to_120_130': (20, 200, 60)}
MK = {k: marca(k) for k in COL}
LLOCS = [('vermella 0°', 0, 4), ('vermella 300°', 300, 4), ('vermella 211°', 211, 8), ('vermella 181°', 181, 8), ('lila 352°', 352, 106), ('lila 282°', 282, 105),
         ('lila 118°', 118, 34), ('lila 63°', 63, 19), ('verda 215°', 215, 45), ('verda 155°', 155, 21), ('verda 59°', 59, 50), ('verda 250°', 250, 22)]
W, Z4 = 90, 4; tiles = []
for nom, az, dd in LLOCS:
    px = cx + (R + dd) * np.cos(np.radians(az)) - bx0; py = cy - (R + dd) * np.sin(np.radians(az)) - by0; xa, ya = int(px) - W // 2, int(py) - W // 2
    row = []
    for X in (V94, T4):
        c = np.clip(0.5 + 4 * (X[ya:ya + W, xa:xa + W] - 0.5), 0, 1); im = np.stack([np.uint8(c * 255)] * 3, -1); im = cv2.resize(im, (W * Z4, W * Z4), interpolation=cv2.INTER_NEAREST)
        for k, col in COL.items():
            mb = cv2.resize(MK[k][ya:ya + W, xa:xa + W].astype(np.uint8), (W * Z4, W * Z4), interpolation=cv2.INTER_NEAREST); v = cv2.dilate(mb, np.ones((3, 3), np.uint8)) - mb; im[v > 0] = col
        row.append(im)
    t = np.concatenate([row[0], np.full((W * Z4, 8, 3), 255, np.uint8), row[1]], 1); tiles.append((nom, t))
cols = 2; th = W * Z4 + 30; tw = 2 * W * Z4 + 8; out = Image.new('RGB', (cols * tw + (cols - 1) * 20, (len(tiles) + 1) // 2 * th), 'white'); dr = ImageDraw.Draw(out)
try: F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 20)
except Exception: F = None
for i, (nom, t) in enumerate(tiles):
    X0, Y0 = (i % cols) * (tw + 20), (i // cols) * th; dr.text((X0 + 4, Y0 + 4), f'{nom} · esquerra V94 · dreta V95 prova t9', fill='black', font=F); out.paste(Image.fromarray(t), (X0, Y0 + 30))
out.save(S / 'LAMINA_T9_marques_V94_contra_V95.png'); print(out.size)
