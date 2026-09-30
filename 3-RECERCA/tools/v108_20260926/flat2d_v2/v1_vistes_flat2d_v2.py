"""v1 (V108, flat2d_v2) · VISTES DEL LLENÇ SENCER (i del sensor sencer) per a Pere. Només llegeix; escriu PNG a 4-RESULTATS/v108_20260926/flat2d_v2/.
  VISTA_1_C_al_sensor.png            la correcció C − 1 al sensor sencer (canal G1), pilot (ronda 1) i v2, Vixen i Sony, a ±1,5 %: al pilot hi ha el
                                     disc del centre (Sony +49 %, saturat); a la v2 no, i C s'esvaeix a les vores.
  VISTA_2_base_despres_sobre_abans   base_G (flat2d_v2 / control − 1) a ±0,3 %, llenç sencer a 1/2.
  VISTA_3_compost_despres_sobre_abans  compost amb les màscares de la V107 (flat2d_v2 / control − 1) a ±1 %, llenç sencer a 1/2, amb T1–T6.
  VISTA_4_base_v2_sobre_pilot        què han canviat la correcció del disc i la fusió congelada respecte del pilot (base_G v2 / pilot − 1, ±0,3 %).
  VISTA_5_compost_contrast_fi_abans_despres  contrast fi (σ4/σ40 − 1, ±3 %) del compost, abans (dalt) i després (baix), llenç sencer a 1/4, amb T1–T6."""
import json
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[4]; OUT = ARREL / '4-RESULTATS/v108_20260926/flat2d_v2'
W, H = 10551, 7506; CAD = ARREL / '4-RESULTATS/v108_20260926/cadena'; PI = ARREL / '4-RESULTATS/v108_20260926/marrons/pilot'
C5 = json.loads((ARREL / '4-RESULTATS/v93_20260924/C5_PERFILS.json').read_text())['tracos']
def diverg(u):   # u en [−1, 1] → blau (negatiu) / blanc / vermell (positiu)
    u = np.clip(np.nan_to_num(u, nan=0.0), -1, 1); r = np.where(u > 0, 1.0, 1.0 + u); b = np.where(u < 0, 1.0, 1.0 - u); g = 1.0 - np.abs(u)
    return (np.stack([b, g, r], -1) * 255).astype(np.uint8)   # BGR per a cv2
def marca(img, esc, gruix=2):
    for k, t in enumerate(C5):
        c = np.array(t['info']['centre'], float); d = np.array(t['info']['direccio'], float); d /= np.linalg.norm(d); L = float(t['info']['llarg'])
        p1 = tuple(int(v) for v in (c + d * L / 2) * esc); p2 = tuple(int(v) for v in (c - d * L / 2) * esc); n = np.array([-d[1], d[0]]) * 60 * esc
        for s in (1, -1):
            cv2.line(img, tuple(int(v) for v in np.array(p1) + s * n), tuple(int(v) for v in np.array(p2) + s * n), (0, 160, 0), gruix)
        cv2.putText(img, f'T{k+1}', tuple(int(v) for v in np.array(p1) + n * 1.8), cv2.FONT_HERSHEY_SIMPLEX, 1.4 * esc * 2, (0, 120, 0), 3)
    return img
def titol(img, txt):
    cv2.rectangle(img, (0, 0), (img.shape[1], 56), (255, 255, 255), -1); cv2.putText(img, txt, (12, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 2); return img
def carrega(p, ch=None):
    a = np.load(p, mmap_mode='r'); return np.asarray(a if ch is None else a[..., ch], np.float32)
def ratio(A, B):
    ok = np.isfinite(A) & np.isfinite(B) & (A > 0) & (B > 0); return np.where(ok, B / np.where(ok, A, 1) - 1, np.nan).astype(np.float32)
def redueix(x, f): return cv2.resize(np.nan_to_num(x, nan=0.0), (W // f, H // f), interpolation=cv2.INTER_AREA)
# 1 · C al sensor
pan = []
for tren in ('VIXEN', 'SONYTOT'):
    fila = []
    for nom, p in (('pilot (ronda 1)', ARREL / f'4-RESULTATS/v108_20260926/marrons/flat2d/{tren}_flat2d.npz'), ('v2', OUT / f'flat2d/{tren}_flat2d_v2.npz')):
        C = np.load(p)['C'][0::2, 1::2] - 1; C = cv2.resize(C, (C.shape[1] // 2, C.shape[0] // 2), interpolation=cv2.INTER_AREA)
        im = diverg(C / 0.015); titol(im, f'{tren} · C - 1 {nom} · +-1,5 % · G1, sensor sencer'); fila.append(im)
    hh = max(x.shape[0] for x in fila); fila = [cv2.copyMakeBorder(x, 0, hh - x.shape[0], 0, 8, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for x in fila]; pan.append(np.hstack(fila))
ww = max(x.shape[1] for x in pan); pan = [cv2.copyMakeBorder(x, 0, 8, 0, ww - x.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for x in pan]
cv2.imwrite(str(OUT / 'VISTA_1_C_al_sensor.png'), np.vstack(pan)); print('VISTA_1', flush=True)
# 2 · base
bA = carrega(CAD / 'control/lineal/base_G.npy'); bB = carrega(CAD / 'flat2d_v2/lineal/base_G.npy'); D = ratio(bA, bB)
im = diverg(redueix(D, 2) / 0.003); titol(im, 'base_G · flat2d_v2 / control - 1 · +-0,3 % · llenc sencer a 1/2'); cv2.imwrite(str(OUT / 'VISTA_2_base_despres_sobre_abans.png'), im); print('VISTA_2', flush=True)
# 4 · v2 contra el pilot
bP = carrega(PI / 'lineal_v108/base_G.npy'); D = ratio(bP, bB)
im = diverg(redueix(D, 2) / 0.003); titol(im, 'base_G · flat2d_v2 / pilot (ronda 1) - 1 · +-0,3 % · llenc sencer a 1/2'); cv2.imwrite(str(OUT / 'VISTA_4_base_v2_sobre_pilot.png'), im); del bA, bB, bP, D; print('VISTA_4', flush=True)
# 3 · compost
cA = carrega(OUT / 'compost_control.npy'); cB = carrega(OUT / 'compost_flat2d_v2.npy'); D = ratio(cA, cB)
im = marca(diverg(redueix(D, 2) / 0.01), 0.5); titol(im, 'compost amb les mascares de la V107 · flat2d_v2 / control - 1 · +-1 % · llenc sencer a 1/2 · T1-T6 en verd')
cv2.imwrite(str(OUT / 'VISTA_3_compost_despres_sobre_abans.png'), im); print('VISTA_3', flush=True)
# 5 · contrast fi abans / després
def fi(X):
    m = (X > 0).astype(np.float32); g4 = cv2.GaussianBlur(X * m, (0, 0), 4) / np.maximum(cv2.GaussianBlur(m, (0, 0), 4), 1e-6); g40 = cv2.GaussianBlur(X * m, (0, 0), 40) / np.maximum(cv2.GaussianBlur(m, (0, 0), 40), 1e-6)
    return np.where(m > 0, g4 / np.maximum(g40, 1e-6) - 1, 0)
ims = []
for nom, X in (('abans (control = V107)', cA), ('despres (flat2d_v2)', cB)):
    u = redueix(fi(X), 4) / 0.03; g = ((np.clip(u, -1, 1) + 1) / 2 * 255).astype(np.uint8); im = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR); marca(im, 0.25, 1); titol(im, f'compost · contrast fi s4/s40 - 1 · +-3 % · {nom}'); ims.append(im)
cv2.imwrite(str(OUT / 'VISTA_5_compost_contrast_fi_abans_despres.png'), np.vstack(ims)); print('VISTA_5 FET', flush=True)
