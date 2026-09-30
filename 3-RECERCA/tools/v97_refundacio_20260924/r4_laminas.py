"""r4 (V97) · Làmines de comparació V96 | V97 | diferència, del compost emulat per sota de la 234 (sense les capes d'ajust de Pere; les vistes
finals les fa el Photoshop). Llocs: el limbe a 1:1 (4 azimuts, 200×200 px ampliats ×3), la franja diagonal de la Sony (pas alt σ 30 i estirament,
perquè es vegi un graó de 2 ‰) i la zona del polígon (una capa ACHF isòtropa sola, la 50, sobre gris).
Ús: r4_laminas.py <estat_v96> <estat_v97> <carpeta_sortida>"""
import sys
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jutge_comu import *
E6, E7, OUT = Estat(sys.argv[1]), Estat(sys.argv[2]), Path(sys.argv[3]); OUT.mkdir(parents=True, exist_ok=True)
def u8(x): return np.clip(np.nan_to_num(x) * 255 + 0.5, 0, 255).astype(np.uint8)
def rotul(img, txt):
    img = img.copy(); cv2.putText(img, txt, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA); return img
def tres(a, b, amp, noms, dif_guany=8):
    d = 0.5 + dif_guany * (b - a); rows = [rotul(u8(x[..., ::-1] if x.ndim == 3 else np.repeat(x[..., None], 3, -1)), n) for x, n in zip((a, b, d), noms)]
    rows = [cv2.resize(r, None, fx=amp, fy=amp, interpolation=cv2.INTER_NEAREST) for r in rows]; return np.concatenate(rows, 1)
# 1 · limbe a 1:1 (×3)
fulls = []
for ang in (0, 90, 160, 270):
    cxp = LLUNA[0] + (RLLUNA + 30) * np.cos(np.radians(ang)); cyp = LLUNA[1] - (RLLUNA + 30) * np.sin(np.radians(ang)); box = (int(cxp - 100), int(cyp - 100), int(cxp + 100), int(cyp + 100))
    a, _ = E6.compost(box=box); b, _ = E7.compost(box=box); fulls.append(tres(a, b, 3, (f'V96 {ang} graus', f'V97 {ang} graus', 'dif x8')))
cv2.imwrite(str(OUT / 'LAMINA_V97_1_limbe_1a1_x3.png'), np.concatenate(fulls, 0))
# 2 · franja diagonal de la Sony (a d ≈ 430 px de la vora del camp A, sector de dalt a l'esquerra)
wA = np.load(RES / 'cadena_raw/sources_v29/sony_A_weights.npy', mmap_mode='r')[::4, ::4, 1] > 0
dA = cv2.distanceTransform(wA.astype(np.uint8), cv2.DIST_L2, 5) * 4; yy, xx = np.nonzero((dA > 420) & (dA < 440))
sel = (xx * 4 < SOL[0] - 2500) & (yy * 4 < SOL[1] - 1200)
if sel.sum() == 0: sel = (xx * 4 < SOL[0]) & (yy * 4 < SOL[1])
cx0, cy0 = int(np.median(xx[sel]) * 4), int(np.median(yy[sel]) * 4); box = (cx0 - 600, cy0 - 600, cx0 + 600, cy0 + 600)
out = []
for E_, n in ((E6, 'V96'), (E7, 'V97')):
    c, _ = E_.compost(box=box); L = (0.25 * c[..., 0] + 0.5 * c[..., 1] + 0.25 * c[..., 2]).astype(np.float32); hp = L - cv2.GaussianBlur(L, (0, 0), 30)
    s = np.percentile(np.abs(hp), 99); out.append(rotul(np.repeat(u8(0.5 + 0.5 * hp / s)[..., None], 3, -1), f'{n} compost, pas alt s30 (centre {cx0},{cy0})'))
cv2.imwrite(str(OUT / 'LAMINA_V97_2_franja_diagonal_sony.png'), np.concatenate(out, 1))
# 3 · zona del polígon: la capa 50 (ACHF 01 isòtrop) sola, 1600² al voltant de la Lluna, reduïda ×2
box = (int(LLUNA[0] - 800), int(LLUNA[1] - 800), int(LLUNA[0] + 800), int(LLUNA[1] + 800)); out = []
for E_, n in ((E6, 'V96 capa 50 (per canal)'), (E7, 'V97 capa 50 (lluminancia)')):
    v = E_.rgb(50, box); v = v if v.ndim == 2 else v[..., 1]; al = E_.dada(50, box); v = np.where(al > 0.5, 0.5 + 4 * (v - 0.5), 0.5)
    out.append(rotul(cv2.resize(np.repeat(u8(v)[..., None], 3, -1), None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA), n))
cv2.imwrite(str(OUT / 'LAMINA_V97_3_poligon_capa50.png'), np.concatenate(out, 1)); print('FET', OUT)
