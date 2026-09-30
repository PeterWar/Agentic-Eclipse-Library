"""a3d · Prova C de la vora esquerra (23-09-2026, vespre): l'entrada de la prova B (a3c, sense la pujada) i, a més, el domini dels filtres comença on
acaba la Lluna de Pere. Per a cada azimut (0,25°): radi on l'alfa de la seva Lluna (258) creua 0,5 per última vegada (des de fora), menys 1 px;
suavitzat com DMIN (màxim mòbil i gaussiana d'1°); DMIN_C = màx(DMIN, aquest radi). Així la fosa d'a4 (DMIN_C+1 → DMIN_C+4) cau dins de la vora
suau de la seva Lluna, i els filtres no responen a la corona de 18,4 s que queda a sota. A dalt i a baix (la seva alfa hi és per dins) no canvia res.
Sortida: 4-RESULTATS/v89_proves_20260923/C/A3A_franja_un_instant.npz i A3D_DOMINI_LLUNA.json."""
from v89c_comu import *
from psb69 import PSB
from scipy.ndimage import maximum_filter1d, gaussian_filter1d
claim()
Q = dict(np.load(SORT.parent / 'A3A_franja_un_instant.npz')); by0, by1, bx0, bx1 = [int(v) for v in Q['box']]; cx, cy, R = [float(v) for v in Q['centre']]
DMIN = Q['DMIN'].astype(np.float64); NBZ = len(DMIN)
p = PSB(str(ARREL / '1-PHOTOSHOP/V88.psb')); a, (ox, oy) = p.channel(258, -1); a = a.astype(np.float32) / 65535
yl, xl = np.mgrid[oy:oy + a.shape[0], ox:ox + a.shape[1]]; dl = np.hypot(xl - cx, yl - cy) - R; tl = (np.degrees(np.arctan2(-(yl - cy), xl - cx)) + 360) % 360
ibl = (tl / 360 * NBZ).astype(int) % NBZ; sel = (dl > -15) & (dl < 15) & (a >= 0.5)
crua = np.full(NBZ, -15.0); np.maximum.at(crua, ibl[sel], dl[sel])          # radi més exterior amb alfa ≥ 0,5, per azimut
vora = np.maximum(gaussian_filter1d(maximum_filter1d(crua, 5, mode='wrap'), 4, mode='wrap'), maximum_filter1d(crua, 3, mode='wrap')) - 1.0
DMIN_C = np.maximum(DMIN, vora)
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360; ib = (th / 360 * NBZ).astype(int) % NBZ
dom = Q['domini'] & (d >= DMIN_C[ib]); tret = int((Q['domini'] & ~dom).sum())
Q['DMIN'] = DMIN_C; Q['domini'] = dom; Q['DMIN_V88'] = DMIN; Q['VORA_LLUNA_PERE'] = vora
np.savez_compressed(SORT / 'A3A_franja_un_instant.npz', **Q)
def resum(a0, a1):
    s = slice(int(a0 / 360 * NBZ), int(a1 / 360 * NBZ)); return dict(dmin_V88=round(float(np.mean(DMIN[s])), 2), dmin_C=round(float(np.mean(DMIN_C[s])), 2), max_C=round(float(np.max(DMIN_C[s])), 2))
rep = dict(font_entrada='4-RESULTATS/v89_proves_20260923/A3A_franja_un_instant.npz (prova B: a3c)', alfa_lluna='1-PHOTOSHOP/V88.psb capa 258 (Pere)', llindar_alfa=0.5, marge_px=-1.0,
           px_trets_del_domini=tret, sectors={f'{a0}-{a1}': resum(a0, a1) for a0, a1 in [(0, 35), (35, 100), (100, 120), (120, 152), (152, 170), (170, 190), (190, 205), (205, 230), (230, 300), (300, 360)]})
desa_json('A3D_DOMINI_LLUNA.json', rep); log(json.dumps(rep['sectors'], ensure_ascii=False)); log(f'px trets del domini {tret}')
