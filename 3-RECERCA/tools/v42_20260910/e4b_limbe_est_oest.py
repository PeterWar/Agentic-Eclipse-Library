"""E4b · vista 1:1 del limbe lunar a l'EST (esquerra del llenç: nord amunt, est a l'esquerra; la Lluna es mou cap a l'est i a C2 el seu centre és 14,9 px a l'OEST del Sol)
i a l'OEST: files = capes 12 (1/3200), 11 (1/500) i 10 (1/125) de Pere (byte a byte de la V39/V42) amb els cercles, i la base corba V42
(amb el forat V38) més la capa `Earthshine V42 relleu 12 % · suau σ3` amb la seva màscara. Cercles: CIAN forat V38 (R 457,5 a (5376,6, 3776,6)); GROC limbe mesurat a les
capes 12/11/10 de Pere (R 453,5 a (5361,9, 3774,7)); MAGENTA disc fosc del POWAAAH3 (R 445 al forat); VERD vora de la màscara d'earthshine (R 453,5 al forat)."""
import numpy as np, cv2
from comu42 import *
import c4_projecte_v42 as C4
C = C4.C; MC = (CX + 14.8, CY + 0.9); PL = (5361.9, 3774.7); W2 = 300
s39 = C4.PSDImage.open(C4.F39); n39 = {l.name: l for l in s39}; fulls = {}
for nom in ('12 1/3200 perles', '11 1/500 limbe', '10 1/125'):
    o = n39[nom]; rgb, alpha, mask, box, bg = C.source_arrays(o); x0, y0, x1, y1 = o.bbox; f = np.zeros((H, W, 3), np.float32); f[y0:y1, x0:x1] = rgb.astype(np.float32) / 65535
    if alpha is not None: f[y0:y1, x0:x1] *= (alpha.astype(np.float32) / 65535)[..., None]
    fulls[nom] = f; del rgb, alpha, mask
base = np.load(CAU42 / 'base_corba_total_v42_u16.npy', mmap_mode='r'); es = np.load(CAU42 / 'earthshine_v42_relleu12_suau_u16.npy', mmap_mode='r'); em = np.load(CAU42 / 'earthshine_v42_mascara_u16.npy', mmap_mode='r'); mk = C.mascara_lluna_inici()
def crop(img, cx, cy): return np.asarray(img[int(cy) - W2:int(cy) + W2, int(cx) - W2:int(cx) + W2])
def circles(tile, cx, cy):
    t = (np.clip(tile, 0, 1) * 255).astype(np.uint8); t = cv2.cvtColor(t, cv2.COLOR_RGB2BGR); ox, oy = int(cx) - W2, int(cy) - W2
    for (c, R, col) in ((MC, 457.5, (255, 255, 0)), (PL, 453.5, (0, 255, 255)), (MC, 445.0, (255, 0, 255)), (MC, 453.5, (0, 200, 0))):
        cv2.circle(t, (int(round((c[0] - ox) * 16)), int(round((c[1] - oy) * 16))), int(round(R * 16)), col, 1, lineType=cv2.LINE_AA, shift=4)
    return t
rows = []
for lab, cx in (('EST', MC[0] - 453.5), ('OEST', MC[0] + 453.5)):
    cy = MC[1]; tiles = []
    for nom, f in fulls.items():
        t = circles(crop(f, cx, cy), cx, cy); cv2.putText(t, f'{lab} · capa {nom} (Pere)', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2); tiles.append(t)
    b = crop(base, cx, cy).astype(np.float32) / 65535 * (crop(mk, cx, cy).astype(np.float32) / 65535)[..., None]; e = crop(es, cx, cy).astype(np.float32) / 65535; m = (crop(em, cx, cy).astype(np.float32) / 65535)[..., None]
    tb = circles(b * (1 - m) + e * m, cx, cy); cv2.putText(tb, f'{lab} · base V42 (forat) + earthshine relleu 12 % suau', (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2); tiles.append(tb)
    sep = np.full((2 * W2, 6, 3), 40, np.uint8); row = tiles[0]
    for t in tiles[1:]: row = np.concatenate([row, sep, t], axis=1)
    rows.append(row)
can = np.concatenate([rows[0], np.full((6, rows[0].shape[1], 3), 40, np.uint8), rows[1]], axis=0)
leg = np.full((40, can.shape[1], 3), 25, np.uint8); cv2.putText(leg, 'CIAN forat V38 R457.5 | GROC limbe capes Pere R453.5 (5361.9,3774.7) | MAGENTA disc fosc POWAAAH3 R445 | VERD mascara earthshine R453.5', (8, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
cv2.imwrite(str(VIS42 / 'E4b_limbe_est_oest_1a1.png'), np.concatenate([leg, can], axis=0)); print('E4b fet', VIS42 / 'E4b_limbe_est_oest_1a1.png')
