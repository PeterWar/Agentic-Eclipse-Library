"""c8 · Tria de variants de la vora (compost EMULAT de la V92 de Pere canviant només els 16 filtres): V88 (línies presents), V92 (suavitzat
radial + mirall), V93 VORA 1 σ 12, VORA 2 σ 12, VORA 2 σ 24. Mesures: nivell a d 1–8 respecte de la V92 (vora nova clara/fosca), lent a 1–5
(marques grises), textura LoG de la 56 a 2–14 (marques verdes) i amplitud de LÍNIES (detall radial fi coherent en 1,5° menys el de 15°) a
104–228° d 1–10. Sortida: C8_TRIA.json."""
from v93_comu import *
from psb69 import PSB
from vm_compost import comp, capa_box
import cv2
from scipy.ndimage import gaussian_filter1d, uniform_filter1d
claim(); BX = (4600, 3000, 6150, 4550); W_, H_ = BX[2] - BX[0], BX[3] - BX[1]; cx, cy, R = GEO['cx'] - BX[0], GEO['cy'] - BX[1], GEO['R']
DT = 0.05; NT = int(360 / DT); DR = 0.25; DS = np.arange(-3, 30.001, DR); TS = np.radians((np.arange(NT) + 0.5) * DT)
TT, DD = np.meshgrid(TS, DS); MX = (cx + (R + DD) * np.cos(TT)).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT)).astype(np.float32)
ds_arc = np.radians(DT) * (R + DS)[:, None]; far = (DS >= 16) & (DS <= 30); t = np.arange(NT) * DT
sel = lambda a, b: np.flatnonzero((t >= a) & (t < b)) if a < b else np.flatnonzero((t >= a) | (t < b))
VAR = {'V88': ARREL / '4-RESULTATS/v88_20260923/filtres_finals', 'V92': ARREL / '4-RESULTATS/v92_20260924/filtres_v92', 'V93_vora1_s12': SORT / 'filtres_v93',
       'V93_vora2_s12': SORT / 'prova_v2_s12', 'V93_vora2_s24': SORT / 'prova_v2_s24'}
p = PSB(str(PSB_PERE)); vis = [L['id'] for L in p.layers if L['visible'] and L['right'] > L['left'] and L['id'] not in (239, 240, 241, 242, 243, 244, 269)]
CAPES = {i: capa_box(p, i, BX) for i in vis}; lum = lambda C: 0.2126 * C[..., 0] + 0.7152 * C[..., 1] + 0.0722 * C[..., 2]; rep = {}; PERF = {}
yy, xx = np.mgrid[:H_, :W_]; dpx = np.hypot(xx - cx, yy - cy) - R; thp = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
for nm, carp in VAR.items():
    capes = []
    for i in vis:
        if i in FILTRES: md, F_, a_ = CAPES[i]; v = np.load(carp / f'{FILTRES[i]}_u16.npy', mmap_mode='r')[BX[1]:BX[3], BX[0]:BX[2]].astype(np.float32) / 65535; capes.append((md, np.repeat(v[..., None], 3, -1), a_))
        else: capes.append(CAPES[i])
    Y = lum(comp(capes, H_, W_)[0]); P = cv2.remap(Y.astype(np.float32), MX, MY, cv2.INTER_LINEAR)
    T = P - gaussian_filter1d(P, 3.0 / ds_arc.mean(), axis=1, mode='wrap'); Ed = (np.diff(T, axis=0) / DR) ** 2; Ed = np.vstack([Ed, Ed[-1:]]); Es = (np.diff(T, axis=1, append=T[:, :1]) / ds_arc) ** 2
    f = lambda E, mk: uniform_filter1d(E[mk].mean(0), 100, mode='wrap'); mk = (DS >= 1) & (DS <= 5); L = (f(Ed, far) / f(Es, far)) / (f(Ed, mk) / f(Es, mk))
    HPr = P - gaussian_filter1d(P, 4 / DR, axis=0, mode='nearest'); lin = gaussian_filter1d(HPr, 1.5 / DT, axis=1, mode='wrap') - gaussian_filter1d(HPr, 15 / DT, axis=1, mode='wrap')
    mk10 = (DS >= 1) & (DS <= 10); s_l = sel(104, 228)
    v56 = np.load(carp / 'P05_WOW_bilateral_u16.npy', mmap_mode='r')[BX[1]:BX[3], BX[0]:BX[2]].astype(np.float32) / 65535; lap = cv2.Laplacian(cv2.GaussianBlur(v56, (0, 0), 1.0), cv2.CV_32F) ** 2
    verd = (thp >= 193) & (thp < 227); tex = float(np.sqrt(lap[verd & (dpx >= 2) & (dpx < 14)].mean() / lap[verd & (dpx >= 40) & (dpx < 70)].mean()))
    PERF[nm] = {s: P[:, sel(a, b)].mean(1) for s, (a, b) in {'dalt_60_100': (60, 100), 'baix_240_310': (240, 310), 'dreta_320_20': (320, 20), 'esquerra_104_228': (104, 228)}.items()}
    rep[nm] = dict(lent_1_5={s: round(float(L[sel(a, b)].mean()), 2) for s, (a, b) in {'gris_80_96': (80, 96), 'gris_244_307': (244, 307)}.items()},
                   linies_104_228_rms_x1000=round(float(np.sqrt((lin[mk10][:, s_l] ** 2).mean()) * 1000), 3), textura_56_verd_2_14=round(tex, 3))
for nm in VAR:
    rep[nm]['nivell_menys_V92_d1_8_max'] = {s: round(float(np.max(np.abs((PERF[nm][s] - PERF['V92'][s])[(DS >= 1) & (DS <= 8)]))), 4) for s in PERF[nm]}
    print(nm, json.dumps(rep[nm]), flush=True)
desa_json('C8_TRIA.json', rep)
