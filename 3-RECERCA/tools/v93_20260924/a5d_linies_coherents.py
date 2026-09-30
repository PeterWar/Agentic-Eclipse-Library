"""a5d (V93) · Treu les línies paral·leles al limbe de l'esquerra SENSE treure la textura.
Per què: la V90–V92 (a5c) hi suavitzava els filtres al llarg del radi (σ 4 px → 0 a 14 px, 104–228°). Les línies marxaven, però també la
textura: Pere hi va marcar en verd (193–227°, d 0–14 px) «hi falta detall, és com si hagués quedat el color però les textures d'aquella zona no».
Les línies són detall radial fi COHERENT al llarg del limbe (una vall i una cresta que segueixen el limbe graus i graus); la textura és detall
radial fi que canvia d'un píxel a l'altre al llarg de l'arc. Ara: detall radial fi = ràster − gaussiana radial σ 4 px; la seva part coherent =
mitjana al llarg de l'arc (gaussiana d'azimut σ 6 px d'arc ≈ 0,8°; amb 12 i 24 px, a 8:1 hi quedava un rastre de la línia a 219° i 223°, c9b); se'n resta NOMÉS la part coherent, amb el mateix pes que a5c
(1 fins a 4 px del limbe → 0 a 14 px) i la mateixa finestra d'azimut (plena a 104–228°, fosa a 99–104° i 228–232°). Polars 0,05° × 0,25 px,
aplicat com a diferència. Entrada: filtres_nivell/ (a4v). Sortida: filtres_v93/ i A5D.json."""
from v93_comu import *
import cv2
from scipy.ndimage import gaussian_filter1d
from v86_operadors import smoothstep
claim(); FIN = SORT / __import__('os').environ.get('ENTRADA_A5D', 'filtres_nivell'); OUT = SORT / __import__('os').environ.get('SORTIDA_A5D', 'filtres_v93'); OUT.mkdir(exist_ok=True); TAGS = list(dict.fromkeys(FILTRES.values()))
cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']; SIG_R, SIG_ARC, D1, D2 = 4.0, float(__import__('os').environ.get('SIGARC_V93', '6')), 4.0, 14.0; A0, A1, A2, A3 = 99.0, 104.0, 228.0, 232.0
DMIN_P, DMAX_P, DR, NT = -30.0, 30.0, 0.25, 7200; m = int(R + DMAX_P + 4); bx0, bx1, by0, by1 = int(cx) - m, int(cx) + m + 1, int(cy) - m, int(cy) + m + 1
TS = np.radians((np.arange(NT) + 0.5) * 360 / NT); DS = np.arange(DMIN_P, DMAX_P + 1e-6, DR); TT, DD = np.meshgrid(TS, DS); TSg = np.degrees(TS)
WGT = ((smoothstep(TSg, A0, A1) * (1 - smoothstep(TSg, A2, A3)))[None, :] * (1 - smoothstep(DS, D1, D2))[:, None]).astype(np.float32)
MX = (cx + (R + DD) * np.cos(TT) - bx0).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT) - by0).astype(np.float32)
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - cx, yy - cy) - R; tt = (np.arctan2(-(yy - cy), xx - cx) + 2 * np.pi) % (2 * np.pi)
IX = (tt / (2 * np.pi) * NT - 0.5).astype(np.float32); IY = ((d - DS[0]) / DR).astype(np.float32); dins = (d > DMIN_P) & (d < DMAX_P)
sig_th = SIG_ARC / ((R + DS) * np.radians(360 / NT))
def treu(X):
    P = cv2.remap(X, MX, MY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    HP = P - gaussian_filter1d(P, SIG_R / DR, axis=0, mode='nearest')
    COH = np.empty_like(HP)
    for i in range(HP.shape[0]): COH[i] = gaussian_filter1d(HP[i], sig_th[i], mode='wrap')
    back = lambda Z: cv2.remap(Z, np.mod(IX, NT), IY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return np.where(dins, X - back(WGT * COH), X)
rep = dict(sigma_radial_px=SIG_R, sigma_arc_px=SIG_ARC, fosa_radial_px=[D1, D2], finestra_azimut_graus=[A0, A1, A2, A3], capes={})
for tag in TAGS:
    u = np.load(FIN / f'{tag}_u16.npy'); X = u[by0:by1, bx0:bx1].astype(np.float32) / 65535
    out = u.copy(); out[by0:by1, bx0:bx1] = np.round(np.clip(treu(X), 0, 1) * 65535).astype(np.uint16); np.save(OUT / f'{tag}_u16.npy', out)
    rep['capes'][tag] = dict(sha256=sha(OUT / f'{tag}_u16.npy')); log(tag + ' fet')
desa_json('A5D.json', rep); log('A5D fet')
