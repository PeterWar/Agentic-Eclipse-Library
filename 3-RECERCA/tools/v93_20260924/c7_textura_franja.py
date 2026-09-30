"""c7 · On falta textura a les marques verdes (193–227°, d ≤ 14 px): energia del detall fi isotròpic (LoG σ 1 px, relativa al nivell local)
per distància al limbe i per sector, a la base (capa 3), al compost natiu (render V0) i als ràsters de la V92, dins i fora de la franja d'un instant.
Sortida: C7_TEXTURA.json."""
from v93_comu import *
from psb69 import PSB
import cv2, tifffile
claim(); BX = (4600, 3000, 6150, 4550); cx, cy, R = GEO['cx'] - BX[0], GEO['cy'] - BX[1], GEO['R']
yy, xx = np.mgrid[:BX[3] - BX[1], :BX[2] - BX[0]]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
p = PSB(str(PSB_PERE)); base = np.stack([p.channel_box(3, c, BX) for c in range(3)], -1).astype(np.float32) / 65535
V0 = tifffile.imread(SORT / 'renders/V0_tal_com_esta_lluna.tif')[..., :3].astype(np.float32) / 65535
lum = lambda C: 0.2126 * C[..., 0] + 0.7152 * C[..., 1] + 0.0722 * C[..., 2]
fonts = {'base': lum(base), 'compost_V92': lum(V0)}
for tag in ('P05_WOW_bilateral', 'P01_NRGF', '04'): fonts['filtre_' + tag] = np.load(ARREL / f'4-RESULTATS/v92_20260924/filtres_v92/{tag}_u16.npy', mmap_mode='r')[BX[1]:BX[3], BX[0]:BX[2]].astype(np.float32) / 65535
SECT = {'verd_193_227': (193, 227), 'esquerra_150_190': (150, 190), 'dalt_60_100': (60, 100), 'baix_250_290': (250, 290), 'dreta_330_20': (330, 380)}
BINS = [(2, 5), (5, 9), (9, 14), (14, 25), (25, 40), (40, 70)]
rep = {}
for nm, Y in fonts.items():
    log_ = cv2.GaussianBlur(Y, (0, 0), 1.0); lap = cv2.Laplacian(log_, cv2.CV_32F); niv = cv2.GaussianBlur(Y, (0, 0), 6) + 1e-4; e = (lap / niv) ** 2 if not nm.startswith('filtre') else lap ** 2
    rep[nm] = {}
    for s, (a, b) in SECT.items():
        az = ((th - a) % 360) < ((b - a) % 360 if b - a != 360 else 360); row = []
        for d0, d1 in BINS:
            m = az & (d >= d0) & (d < d1); row.append(float(np.sqrt(e[m].mean())))
        ref = row[-1]; rep[nm][s] = [round(v / ref, 2) for v in row]
    print(nm, json.dumps(rep[nm]), flush=True)
rep['bins_px'] = BINS; desa_json('C7_TEXTURA.json', rep)
