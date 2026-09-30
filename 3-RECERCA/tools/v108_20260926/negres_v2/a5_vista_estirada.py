"""a5 (V108 · negres_v2) · Làmina de diagnòstic del LLENÇ SENCER amb un estirament fort (ln L entre ln 0,12 i ln 0,30) per veure el cel i la corona
feble: V107 | CEL sol | genoll AMB PES de corona (vora = halo a ~5 R☉ al sud) | RECOMANADA (genoll continu), i a sota la diferència del genoll sol
respecte del CEL sol (±5 %), amb el marc final i cercles a 3 / 4,5 / 5,5 / 7 R☉. Llegeix pas2/L_<nom>.npy (de a1_avalua). Sortida: vistes/ESTIRADA_*.jpg"""
from pathlib import Path
import numpy as np, cv2
OUT = Path(__file__).resolve().parents[4] / '4-RESULTATS/v108_20260926/negres_v2'
MARC = (1325, 1142, 9348, 6263); SX, SY, RS = 5361.768, 3775.748, 440.603
NOMS = [('V107', 'V107'), ('CEL_v2', 'CEL sol'), ('v4_CEL_G_MAX_T_e20', 'genoll AMB PES (halo)'), ('v4_CEL_G_MAX_T_e30_W_H0', 'RECOMANADA: genoll continu')]
Lc = np.load(OUT / 'pas2/L_CEL_v2.npy'); H2, W2 = Lc.shape
def rotul(im, t): cv2.rectangle(im, (0, 0), (im.shape[1], 44), (0, 0, 0), -1); cv2.putText(im, t, (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA); return im
def marques(im, f):
    cv2.rectangle(im, (int(MARC[0] / f), int(MARC[1] / f)), (int(MARC[2] / f), int(MARC[3] / f)), (0, 200, 255), 2)
    for rs in (3, 4.5, 5.5, 7): cv2.circle(im, (int(SX / f), int(SY / f)), int(rs * RS / f), (0, 160, 0), 1)
    return im
dalt, baix = [], []
for nom, et in NOMS:
    L = np.load(OUT / f'pas2/L_{nom}.npy'); v = np.clip((np.log(np.maximum(L, 1e-3)) - np.log(0.12)) / (np.log(0.30) - np.log(0.12)), 0, 1)
    im = cv2.cvtColor(cv2.resize((v * 255).astype(np.uint8), (W2 // 2, H2 // 2), interpolation=cv2.INTER_AREA), cv2.COLOR_GRAY2BGR); dalt.append(rotul(im, et))
    dl = np.log(np.maximum(L, 1e-3)) - np.log(np.maximum(Lc, 1e-3)); t = np.clip(dl / 0.05, -1, 1); d = np.zeros(dl.shape + (3,), np.uint8)
    d[..., 2] = np.where(t > 0, 255, 255 * (1 + t)); d[..., 0] = np.where(t < 0, 255, 255 * (1 - t)); d[..., 1] = 255 * (1 - np.abs(t))
    d = marques(cv2.resize(d, (W2 // 2, H2 // 2), interpolation=cv2.INTER_AREA), 4); baix.append(rotul(d, f'{et}: ln(/CEL sol), +-5 %'))
img = np.concatenate([np.concatenate(dalt[:2], 1), np.concatenate(dalt[2:], 1), np.concatenate(baix[2:], 1)], 0)
cv2.imwrite(str(OUT / 'vistes/ESTIRADA_V107_CEL_ambpes_recomanada.jpg'), img, [cv2.IMWRITE_JPEG_QUALITY, 90]); print('FET')
