"""E5d · vista 1:1 per triar el vector: el que Pere veu (base corba amb el forat V38 a sobre de la capa seva) a la PROTUBERÀNCIA DE L'EST i a la vora OEST del forat,
per a les capes 12, 06 (visibles) i 10, amb la capa moguda (0,0), (+5,+1), (+8,+1) i (+12,+1). Cercles: cian = vora del forat V38 (R 457,5)."""
import numpy as np, cv2
from psd_tools import PSDImage
from comu42 import *
import c4_projecte_v42 as C4
C = C4.C; MC = (CX + 14.8, CY + 0.9); W2 = 250; CANDS = [(0, 0), (5, 1), (8, 1), (12, 1)]
REG = {'EST protuberancia': (4880, 3770), 'OEST vora forat': (5836, 3777)}
base = np.load(CAU42 / 'base_corba_total_v42_u16.npy', mmap_mode='r'); mk = C.mascara_lluna_inici().astype(np.float32) / 65535
s39 = PSDImage.open(C4.F39); n = {l.name: l for l in s39}
def crop(img, cx, cy): return np.asarray(img[int(cy) - W2:int(cy) + W2, int(cx) - W2:int(cx) + W2])
rows = []
for nom in ['12 1/3200 perles', '06 1/8 x4 quar', '10 1/125']:
    o = n[nom]; rgb, alpha, mask, box, bg = C.source_arrays(o); x0, y0, x1, y1 = o.bbox
    lay = np.zeros((H, W, 3), np.float32); lay[y0:y1, x0:x1] = rgb.astype(np.float32) / 65535; la = np.zeros((H, W), np.float32); la[y0:y1, x0:x1] = 1.0 if alpha is None else alpha.astype(np.float32) / 65535
    lm = mask.astype(np.float32) / 65535 if mask is not None else np.ones((H, W), np.float32)   # màscara d'usuari (llenç sencer)
    for reg, (cx, cy) in REG.items():
        b = crop(base, cx, cy).astype(np.float32) / 65535; m = crop(mk, cx, cy)[..., None]; tiles = []
        for dx, dy in CANDS:
            l = crop(lay, cx - dx, cy - dy) * (crop(la, cx - dx, cy - dy) * crop(lm, cx - dx, cy - dy))[..., None]   # la capa moguda (+dx,+dy) = mostrejar-la a (x−dx, y−dy)
            comp = b * m + l * (1 - m); t = cv2.cvtColor((np.clip(comp, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
            cv2.circle(t, (int(round((MC[0] - (cx - W2)) * 16)), int(round((MC[1] - (cy - W2)) * 16))), int(round(457.5 * 16)), (255, 255, 0), 1, lineType=cv2.LINE_AA, shift=4)
            cv2.putText(t, f'{nom[:2]} {reg} moguda ({dx:+d},{dy:+d})', (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2); tiles.append(t)
        row = tiles[0]
        for t in tiles[1:]: row = np.concatenate([row, np.full((2 * W2, 6, 3), 40, np.uint8), t], axis=1)
        rows.append(row)
    del rgb, alpha, mask, lay, la, lm
can = rows[0]
for r_ in rows[1:]: can = np.concatenate([can, np.full((6, r_.shape[1], 3), 40, np.uint8), r_], axis=0)
cv2.imwrite(str(VIS42 / 'E5d_candidats_moure_capes_1a1.png'), can); print('E5d fet', can.shape)
