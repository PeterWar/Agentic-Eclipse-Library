"""a3c · Proves de la vora esquerra (V89, 23-09-2026, vespre): els filtres NO veuen la pujada dels primers px de la corona arran del limbe.
Diagnosi (4-RESULTATS/v88_marques_pere_20260923/DIAGNOSI.md): a la dada d'un instant, la corona puja durant els primers 6–7 px a l'esquerra
(3,5 px a baix, ~5 a la dreta, gens a dalt) i tots els filtres la dibuixen com una línia fosca i una de clara a 2–10 px (marques de Pere a la
V88). Aquesta pujada és la vora de la Lluna difuminada sobre la corona més pendent (a l'esquerra el limbe lunar és gairebé sobre el solar):
no és detall resoluble de la corona.
Què es fa, a cada azimut (0,25°), a les tres entrades lineals dels filtres de la franja (G de la fusió amb la franja, F RGB, V verd Vixen):
  1. perfil radial de G (mitjana normalitzada al domini, suavitzat 1° en azimut); d_pic = el màxim entre DMIN i 9 px. Només si des de DMIN+0,5
     fins al màxim puja més d'un 3 %; si no, d_pic = DMIN i res no canvia (a dalt, per exemple);
  2. d_pic suavitzat com DMIN (màxim mòbil i gaussiana d'1°) i pendent s del ln del perfil a d_pic..d_pic+6 px (la corona decreix cap enfora);
  3. per sota de d_pic, cada entrada es continua radialment cap endins des del seu propi valor a d_pic (el detall azimutal hi queda com a raigs),
     creixent amb el mateix pendent: X·exp(s·(d_pic − d)); fosa smoothstep d'1,5 px a d_pic. Fora del domini (d < DMIN) res no canvia.
El domini, DMIN i la resta del npz d'a3a de la V88 queden igual; així a3 i a4 (còpies de la V88) funcionen sense cap altre canvi.
Sortida: 4-RESULTATS/v89_proves_20260923/A3A_franja_un_instant.npz (amb G, F i V nous) i A3C_SENSE_PUJADA.json."""
from v89_comu import *
from v86_operadors import smoothstep
from scipy.ndimage import maximum_filter1d, gaussian_filter1d
import cv2
claim()
V88D = ARREL / '4-RESULTATS/v88_20260923'
Q = dict(np.load(V88D / 'A3A_franja_un_instant.npz')); by0, by1, bx0, bx1 = [int(v) for v in Q['box']]; cx, cy, R = [float(v) for v in Q['centre']]
DMIN = Q['DMIN'].astype(np.float64); NBZ = len(DMIN); dom = Q['domini']
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = (np.hypot(xx - cx, yy - cy) - R).astype(np.float32); th = ((np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360).astype(np.float32)
ib = (th / 360 * NBZ).astype(int) % NBZ
# 1. perfil polar de G al domini (mitjana normalitzada), θ 0,25° × d 0,25 px de −2 a 16 px
DS = np.arange(-2.0, 16.01, 0.25); TS = (np.arange(NBZ) + 0.5) * 360 / NBZ; TT, DD = np.meshgrid(np.radians(TS), DS)
MX = (cx + (R + DD) * np.cos(TT) - bx0).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT) - by0).astype(np.float32)
G = Q['G'].astype(np.float32); m = dom.astype(np.float32)
num = cv2.remap(G * m, MX, MY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0); den = cv2.remap(m, MX, MY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
P = np.where(den > 0.5, num / np.maximum(den, 1e-6), np.nan)                 # (len(DS), NBZ)
Ps = np.full_like(P, np.nan)
for i in range(len(DS)):
    row = P[i]; ok = np.isfinite(row)
    if ok.sum() < NBZ // 4: continue
    w = gaussian_filter1d(ok.astype(np.float64), 4, mode='wrap'); v = gaussian_filter1d(np.where(ok, row, 0), 4, mode='wrap'); Ps[i] = np.where(w > 0.2, v / np.maximum(w, 1e-9), np.nan)
# 2. d_pic i pendent per azimut
dpic = DMIN.copy(); puja = np.zeros(NBZ); pend = np.zeros(NBZ)
for k in range(NBZ):
    col = Ps[:, k]; sel = (DS >= DMIN[k] + 0.25) & (DS <= 9.0) & np.isfinite(col)
    if sel.sum() < 4: continue
    j = np.flatnonzero(sel); jm = j[np.nanargmax(col[j])]; v0 = col[j[0] + 1] if j.size > 1 else col[j[0]]
    puja[k] = col[jm] / v0 - 1
    if puja[k] > 0.03: dpic[k] = DS[jm]
dpic = gaussian_filter1d(maximum_filter1d(dpic, 5, mode='wrap'), 4, mode='wrap'); dpic = np.maximum(dpic, DMIN)
for k in range(NBZ):
    col = Ps[:, k]; sel = (DS >= dpic[k]) & (DS <= dpic[k] + 6) & np.isfinite(col) & (col > 0)
    if sel.sum() >= 6: pend[k] = -np.polyfit(DS[sel], np.log(col[sel]), 1)[0]
pend = np.clip(gaussian_filter1d(pend, 4, mode='wrap'), 0, 0.08)
canvi = dpic > DMIN + 0.3
# 3. continuació de les entrades per sota de d_pic
dp = dpic[ib].astype(np.float32); sp = pend[ib].astype(np.float32); ang = np.radians(th)
RX = (cx + (R + dp) * np.cos(ang) - bx0).astype(np.float32); RY = (cy - (R + dp) * np.sin(ang) - by0).astype(np.float32)
zona = dom & (d < dp) & canvi[ib]; w = smoothstep(d, dp - 1.5, dp).astype(np.float32)
def continua(X):
    ref = cv2.remap(X.astype(np.float32), RX, RY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    cont = ref * np.exp(sp * (dp - d)); return np.where(zona, w * X + (1 - w) * cont, X).astype(np.float32)
out = dict(Q); out['G'] = continua(Q['G']); out['V'] = continua(Q['V']); F = Q['F'].copy()
for c in range(3): F[..., c] = continua(Q['F'][..., c])
out['F'] = F; out['D_PUJADA'] = dpic; out['S_PUJADA'] = pend
np.savez_compressed(SORT / 'A3A_franja_un_instant.npz', **out)
def resum(a0, a1):
    s = slice(int(a0 / 360 * NBZ), int(a1 / 360 * NBZ)); return dict(d_pic_mitja=round(float(np.mean(dpic[s])), 2), dmin_mitja=round(float(np.mean(DMIN[s])), 2), pujada_mitjana=round(float(np.mean(puja[s])), 3), pendent=round(float(np.mean(pend[s])), 4), fraccio_amb_canvi=round(float(np.mean(canvi[s])), 2))
rep = dict(font='4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz (V88)', llindar_pujada=0.03, d_pic_max_px=9.0, fosa_px=1.5,
           px_canviats=int(zona.sum()), canvi_relatiu_G_mediana_a_la_zona=float(np.median(out['G'][zona] / np.maximum(Q['G'][zona], 1e-9))) if zona.any() else None,
           sectors={f'{a0}-{a1}': resum(a0, a1) for a0, a1 in [(0, 30), (30, 60), (60, 100), (100, 120), (120, 152), (152, 170), (170, 190), (190, 205), (205, 230), (230, 260), (260, 300), (300, 330), (330, 360)]})
desa_json('A3C_SENSE_PUJADA.json', rep); log(json.dumps(rep['sectors'], ensure_ascii=False)); log('px canviats %d' % rep['px_canviats'])
