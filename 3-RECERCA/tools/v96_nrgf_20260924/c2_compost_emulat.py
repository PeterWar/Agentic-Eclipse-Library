"""c2 (V96) · Compost EMULAT (sense capes d'ajust) a la caixa de la Lluna: V95 tal com és contra V95 amb la 41 nova (NRGF V96: ràster i alfa de domini).
La 41 és en Multiplicar: on és transparent no enfosqueix. Mesura el canvi de lluminància per distància al limbe i sector (sobretot al buit sense dada, d 0–2),
i làmina 6:1. Només lectura."""
import sys, json
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v96_nrgf_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v86_neta_20260923')); sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v90_marques_pere_20260923'))
from psb69 import PSB
from v86_compost import capa_box
from vm_compost import comp
cx, cy, R = 5375.787, 3775.977, 452.979; B = 560; box = (int(cx) - B, int(cy) - B, int(cx) + B, int(cy) + B); x0, y0, x1, y1 = box
p = PSB(str(ARREL / '1-PHOTOSHOP/V95.psb')); u = np.load(SORT / 'P01_NRGF_u16.npy', mmap_mode='r'); al = np.load(SORT / 'P01_NRGF_alfa_u16.npy', mmap_mode='r')
capes = [L for L in p.layers if L['visible'] and L['right'] > L['left']]
print('capes emulades:', [(L['id'], str(L['blend'])) for L in capes])
def fer(nova):
    ll = []
    for L in capes:
        mode, F, a = capa_box(p, L['id'], box)
        if nova and L['id'] == 41:
            F = np.repeat((np.asarray(u[y0:y1, x0:x1]).astype(np.float32) / 65535)[..., None], 3, -1)
            msk = p.channel_box(41, -2, box, fill=65535 if L['mask']['background'] == 255 else 0).astype(np.float32) / 65535 if L['mask'] is not None else 1
            a = (np.asarray(al[y0:y1, x0:x1]).astype(np.float32) / 65535) * msk * (L['opacity'] / 255.0)
        ll.append((str(mode).split('.')[-1].upper(), F, a))
    return comp(ll, y1 - y0, x1 - x0)[0]
C5, C6 = fer(False), fer(True); np.save(SORT / 'c2_compost_V95.npy', C5); np.save(SORT / 'c2_compost_V96.npy', C6)
lum = lambda C: 0.2126 * C[..., 0] + 0.7152 * C[..., 1] + 0.0722 * C[..., 2]; L5, L6 = lum(C5), lum(C6); rat = L6 / np.maximum(L5, 1e-4) - 1
yy, xx = np.mgrid[y0:y1, x0:x1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
DD = [-2, -1, 0, 0.5, 1, 1.5, 2, 3, 4, 6, 8, 10, 12, 15, 20, 30]
for a0, a1 in ((0, 360), (195, 295), (52, 108), (300, 360), (130, 190)):
    s = (th >= a0) & (th < a1); print(f'{a0}-{a1}° V96/V95 − 1 (%) per d:', [round(float(np.mean(rat[s & (np.abs(d - dd) < 0.25)])) * 100, 2) for dd in DD])
print('d:', DD)
LLOCS = [(245, 6), (85, 6), (60, 6), (330, 4), (20, 4), (215, 6)]; w, zf = 60, 6; F_ = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15)
out = Image.new('RGB', (2 * (w * zf + 8), len(LLOCS) * (w * zf + 24) + 36), 'white'); dr = ImageDraw.Draw(out); dr.text((6, 8), 'Compost EMULAT (sense capes d ajust) 6:1 · esquerra V95 · dreta V95 amb la NRGF V96 · mateix contrast', fill='black', font=F_)
for j, (az, dd) in enumerate(LLOCS):
    px = int(cx + (R + dd) * np.cos(np.radians(az))) - x0; py = int(cy - (R + dd) * np.sin(np.radians(az))) - y0
    ref = C5[py - w // 2:py + w // 2, px - w // 2:px + w // 2]; lo, hi = np.percentile(ref, (1, 99.5))
    for i, C in enumerate((C5, C6)):
        c = np.clip((C[py - w // 2:py + w // 2, px - w // 2:px + w // 2] - lo) / max(hi - lo, 1e-6), 0, 1); im = cv2.resize(np.uint8(c * 255), (w * zf, w * zf), interpolation=cv2.INTER_NEAREST)
        out.paste(Image.fromarray(im), (i * (w * zf + 8), 36 + j * (w * zf + 24) + 20)); dr.text((i * (w * zf + 8) + 4, 36 + j * (w * zf + 24) + 2), f'{az}° · {("V95", "V96")[i]}', fill='black', font=F_)
out.save(SORT / 'C2_COMPOST_EMULAT_6a1.png'); print('fet')
