"""v1_vistes_flat2d_v5 (V108, flat2d_v5) · VISTES DEL LLENÇ SENCER (a 1/4, mai retalls) del que canvia la v5.
VISTA_1: el compost, ln(v4/v3) a l'esquerra i ln(v5/v3) a la dreta (σ 3 px, ±2 %, vermell = més clar), amb les 5 petjades de pols moguda
         encerclades (groc) i la protuberància (cian). Si la v5 fa el que diu, a la dreta les 5 petjades gairebé no es veuen.
VISTA_2: el compost, ln(v5/v4) (σ 3 px, ±2 %): només hi ha d'haver les 5 petjades i la protuberància (i l'escampada dels filtres al voltant).
VISTA_3: l'apilat de la Vixen, ln(v5/v4) (σ 3 px, ±0,3 %): el canvi de la C, al llenç.
Sortida: 4-RESULTATS/v108_20260926/flat2d_v5/VISTA_*.png"""
import json
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/flat2d_v5'
F3 = A / '4-RESULTATS/v108_20260926/flat2d_v3'; F4 = A / '4-RESULTATS/v108_20260926/flat2d_v4'
G1 = json.loads((F4 / 'flat2d/G1_PORTA_V4_VIXEN.json').read_text())['grups']['vixen']['decisions']
POLS = {k: tuple(int(v) for v in G1[str(k)]['centre_llenc']) for k in (73, 2, 32, 66, 57)}; PROT = (4902, 3782)
def lnr(pa, pb, canal=None):
    a = np.load(pa, mmap_mode='r'); b = np.load(pb, mmap_mode='r')
    a = np.asarray(a if canal is None else a[..., canal], np.float32); b = np.asarray(b if canal is None else b[..., canal], np.float32)
    ok = np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0); return cv2.GaussianBlur(np.where(ok, np.log(np.maximum(a, 1e-12) / np.maximum(b, 1e-12)), 0).astype(np.float32), (0, 0), 3), ok
def pinta(d, ok, esc):
    t = np.clip(d / esc, -1, 1); img = np.full(d.shape + (3,), 255, np.uint8)
    img[..., 2] = np.where(t > 0, 255, 255 * (1 + t)).astype(np.uint8); img[..., 1] = (255 * (1 - np.abs(t))).astype(np.uint8); img[..., 0] = np.where(t < 0, 255, 255 * (1 - t)).astype(np.uint8)
    img[~ok] = 215
    for k, c in POLS.items(): cv2.circle(img, c, 150, (0, 200, 230), 10); cv2.putText(img, str(k), (c[0] + 160, c[1]), cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 150, 180), 8, cv2.LINE_AA)
    cv2.circle(img, PROT, 120, (230, 200, 0), 10)
    return cv2.resize(img, (img.shape[1] // 4, img.shape[0] // 4), interpolation=cv2.INTER_AREA)
def peu(text, w):
    cap = np.full((60, w, 3), 255, np.uint8); cv2.putText(cap, text, (10, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 1, cv2.LINE_AA); return cap
d1, o1 = lnr(F4 / 'compost_flat2d_v4.npy', F3 / 'compost_flat2d_v3.npy'); d2, o2 = lnr(OUT / 'compost_flat2d_v5.npy', F3 / 'compost_flat2d_v3.npy')
a, b = pinta(d1, o1, 0.02), pinta(d2, o2, 0.02); sep = np.full((a.shape[0], 12, 3), 0, np.uint8); im = np.hstack([a, sep, b])
cv2.imwrite(str(OUT / 'VISTA_1_compost_v4_i_v5_sobre_v3.png'), np.vstack([peu('compost: esquerra ln(v4/v3), dreta ln(v5/v3); sigma 3 px, +-2 % (vermell = mes clar); groc = les 5 petjades de pols moguda, cian = protuberancia', im.shape[1]), im]))
del d1, o1
d3, o3 = lnr(OUT / 'compost_flat2d_v5.npy', F4 / 'compost_flat2d_v4.npy'); im = pinta(d3, o3, 0.02)
cv2.imwrite(str(OUT / 'VISTA_2_compost_v5_sobre_v4.png'), np.vstack([peu('compost ln(v5/v4), sigma 3 px, +-2 %: nomes hi ha d haver les 5 petjades (groc) i la protuberancia (cian)', im.shape[1]), im]))
d4, o4 = lnr(OUT / 'apilats/vixen_total.npy', F4 / 'apilats/vixen_total.npy', canal=1); im = pinta(d4, o4, 0.003)
cv2.imwrite(str(OUT / 'VISTA_3_apilat_vixen_v5_sobre_v4.png'), np.vstack([peu('apilat de la Vixen (G) ln(v5/v4), sigma 3 px, +-0,3 %: el canvi de la C al llenc', im.shape[1]), im]))
print('FET')
