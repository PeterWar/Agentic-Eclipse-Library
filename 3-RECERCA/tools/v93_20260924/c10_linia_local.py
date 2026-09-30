"""c10 · Amplitud de LA LÍNIA a les marques de la V88 (136°, 211°, 219°, 223°, 112°) i textura a les verdes, per a cada variant: perfil radial del compost
EMULAT mitjanat en ±1,5° d'azimut, detall radial (menys gaussiana radial σ 4 px), rms a d 3–12 px; textura LoG de la 56 a 2–14 px a 193–227°."""
from v93_comu import *
from psb69 import PSB
from vm_compost import comp, capa_box
import cv2
from scipy.ndimage import gaussian_filter1d
claim(); BX = (4600, 3000, 6150, 4550); W_, H_ = BX[2] - BX[0], BX[3] - BX[1]; cx, cy, R = GEO['cx'] - BX[0], GEO['cy'] - BX[1], GEO['R']
DT = 0.05; NT = int(360 / DT); DR = 0.25; DS = np.arange(-3, 30.001, DR); TS = np.radians((np.arange(NT) + 0.5) * DT); t = np.arange(NT) * DT
TT, DD = np.meshgrid(TS, DS); MX = (cx + (R + DD) * np.cos(TT)).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT)).astype(np.float32)
VAR = {'V88': ARREL / '4-RESULTATS/v88_20260923/filtres_finals', 'V92': ARREL / '4-RESULTATS/v92_20260924/filtres_v92'}
for s in (6, 8, 12, 24): VAR[f'V93_s{s}'] = SORT / f'prova_v2_s{s}'
p = PSB(str(PSB_PERE)); vis = [L['id'] for L in p.layers if L['visible'] and L['right'] > L['left'] and L['id'] not in (239, 240, 241, 242, 243, 244, 269)]
CAPES = {i: capa_box(p, i, BX) for i in vis}; lum = lambda C: 0.2126 * C[..., 0] + 0.7152 * C[..., 1] + 0.0722 * C[..., 2]
yy, xx = np.mgrid[:H_, :W_]; dpx = np.hypot(xx - cx, yy - cy) - R; thp = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360; rep = {}
for nm, carp in VAR.items():
    capes = []
    for i in vis:
        if i in FILTRES: md, F_, a_ = CAPES[i]; v = np.load(carp / f'{FILTRES[i]}_u16.npy', mmap_mode='r')[BX[1]:BX[3], BX[0]:BX[2]].astype(np.float32) / 65535; capes.append((md, np.repeat(v[..., None], 3, -1), a_))
        else: capes.append(CAPES[i])
    P = cv2.remap(lum(comp(capes, H_, W_)[0]).astype(np.float32), MX, MY, cv2.INTER_LINEAR); r = {}
    for az in (112, 136, 211, 219, 223, 180):
        pr = P[:, (t >= az - 1.5) & (t < az + 1.5)].mean(1); hp = pr - gaussian_filter1d(pr, 4 / DR, mode='nearest'); m = (DS >= 3) & (DS <= 12); r[f'linia_{az}'] = round(float(np.sqrt((hp[m] ** 2).mean()) * 1000), 2)
    v56 = np.load(carp / 'P05_WOW_bilateral_u16.npy', mmap_mode='r')[BX[1]:BX[3], BX[0]:BX[2]].astype(np.float32) / 65535; lap = cv2.Laplacian(cv2.GaussianBlur(v56, (0, 0), 1.0), cv2.CV_32F) ** 2
    verd = (thp >= 193) & (thp < 227); r['textura_56_verd_2_14'] = round(float(np.sqrt(lap[verd & (dpx >= 2) & (dpx < 14)].mean() / lap[verd & (dpx >= 40) & (dpx < 70)].mean())), 3)
    rep[nm] = r; print(nm, json.dumps(r), flush=True)
desa_json('C10_LINIA_LOCAL.json', rep)
