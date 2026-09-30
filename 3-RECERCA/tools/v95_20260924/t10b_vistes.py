"""t10b · Vistes de la prova t10 contra la V94: (1) NIVELL (pas baix σ 6 px, contrast ×8 al voltant de 0,5) de 1600×1600 px al voltant de la
Lluna, a 1:2, amb les marques de Pere; (2) làmina a 4:1 a les marques."""
import sys, subprocess
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; S = ARREL / '4-RESULTATS/v95_20260924'
Q = np.load(ARREL / '4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz'); cx, cy, R = [float(v) for v in Q['centre']]; B = 1200; bx0, by0 = int(cx) - B, int(cy) - B
T = np.load(S / 't10_display.npy'); m = np.isfinite(np.load(S / 't10_q.npy'))
v94 = np.load(ARREL / '4-RESULTATS/v94_20260924/wow/P05_WOW_bilateral_u16.npy', mmap_mode='r')[by0:by0 + 2 * B, bx0:bx0 + 2 * B].astype(np.float32) / 65535
Z = np.load(ARREL / '4-RESULTATS/wow_marques_pere_20260924/marques.npz'); x0, y0 = Z['272_origen']
COL = {'to_350_360': (255, 0, 40), 'to_280_290': (190, 0, 255), 'to_100_110': (60, 230, 20), 'to_120_130': (20, 200, 60)}
def marca(nom):
    mm = Z[f'272_{nom}']; out = np.zeros((2 * B, 2 * B), bool); oy, ox = y0 - by0, x0 - bx0
    ys0, xs0 = max(0, oy), max(0, ox); ys1, xs1 = min(2 * B, oy + mm.shape[0]), min(2 * B, ox + mm.shape[1]); out[ys0:ys1, xs0:xs1] = mm[ys0 - oy:ys1 - oy, xs0 - ox:xs1 - ox]; return out
MK = {k: marca(k) for k in COL}
def nivell(X):
    num = cv2.GaussianBlur(np.where(m, X, 0).astype(np.float32), (0, 0), 6); den = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 6); return np.where(m, num / np.maximum(den, 1e-6), 0.5)
H = 800; c0 = B - H; panells = []
for nom, X in (('V94', v94), ('V95 t10', T)):
    L = nivell(X)[c0:c0 + 2 * H, c0:c0 + 2 * H]; im = np.uint8(np.clip(0.5 + 8 * (L - 0.5), 0, 1) * 255); im = np.stack([im] * 3, -1)
    for k, col in COL.items():
        mb = MK[k][c0:c0 + 2 * H, c0:c0 + 2 * H].astype(np.uint8); v = cv2.dilate(mb, np.ones((5, 5), np.uint8)) - mb; im[v > 0] = col
    im = cv2.resize(im, (H, H), interpolation=cv2.INTER_AREA); panells.append((nom, im))
out = Image.new('RGB', (2 * H + 16, H + 34), 'white'); dr = ImageDraw.Draw(out); F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 20)
for i, (nom, im) in enumerate(panells): dr.text((i * (H + 16) + 6, 6), f'{nom} · NIVELL (pas baix σ 6 px, contrast ×8) · 1:2', fill='black', font=F); out.paste(Image.fromarray(im), (i * (H + 16), 34))
out.save(S / 'LAMINA_T10_nivell_V94_contra_V95.png'); print('nivell fet')
