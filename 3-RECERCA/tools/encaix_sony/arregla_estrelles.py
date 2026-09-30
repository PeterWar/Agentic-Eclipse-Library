"""Arregla les estrelles mogudes (traces curtes) de la capa Sony.

Per a cada font compacta i allargada: ajust d'una gaussiana el·líptica + fons local sobre la
luminància, i, si passa els criteris de forma (allargament, angle coherent amb la deriva,
mida), es resta el model el·líptic per canal i s'hi posa una gaussiana rodona amb el mateix
flux i el mateix centroide (σ = σ menor mesurada). Els plomalls (estrets però llargs) i les
crestes queden fora pels criteris de mida i de residu de l'ajust.

Ús: arregla_estrelles.py entrada.npy sortida.npy [mask_valid.npy]
"""
import sys, json
import numpy as np
from scipy import ndimage as ndi
from scipy.optimize import least_squares

SRC, OUT = sys.argv[1], sys.argv[2]
img = np.load(SRC)                        # H×W×3 float32 0–1
H, W = img.shape[:2]
L = img.mean(-1)
# on hi ha llenç vàlid per buscar (per defecte tot, menys on la Sony està cremada)
if len(sys.argv) > 3:
    ok = np.load(sys.argv[3]) > 0.5
else:
    ok = (img < 0.85).all(-1)
ok = ndi.binary_erosion(ok, iterations=25, border_value=1)

# --- detecció ---------------------------------------------------------------
bg = ndi.gaussian_filter(L, 12)
hp = L - bg
sm = ndi.gaussian_filter(hp, 1.2)
noise = 1.4826 * np.median(np.abs(sm[ok] - np.median(sm[ok])))
pk = (sm == ndi.maximum_filter(sm, size=11)) & (sm > 6 * noise) & ok
pk[:20, :] = pk[-20:, :] = False; pk[:, :20] = pk[:, -20:] = False
ys, xs = np.nonzero(pk)
print('soroll', noise, ' candidats:', len(ys))

def model(p, yy, xx):
    A, y0, x0, sa, sb, th, c = p
    ct, st = np.cos(th), np.sin(th)
    u = (xx - x0) * ct + (yy - y0) * st
    v = -(xx - x0) * st + (yy - y0) * ct
    return A * np.exp(-0.5 * (u / sa) ** 2 - 0.5 * (v / sb) ** 2) + c

R = 12
yy, xx = np.mgrid[-R:R + 1, -R:R + 1]
fits = []
for y, x in zip(ys, xs):
    cut = hp[y - R:y + R + 1, x - R:x + R + 1]
    if cut.shape != (2 * R + 1, 2 * R + 1):
        continue
    A0 = cut[R, R]
    p0 = [A0, 0.0, 0.0, 3.0, 1.5, np.radians(50), 0.0]
    try:
        res = least_squares(lambda p: (model(p, yy, xx) - cut).ravel(), p0,
                            bounds=([0, -4, -4, 0.7, 0.7, -np.pi, -1], [2, 4, 4, 12, 12, np.pi, 1]), max_nfev=200)
    except Exception:
        continue
    A, y0, x0, sa, sb, th, c = res.x
    if sa < sb:
        sa, sb, th = sb, sa, th + np.pi / 2
    th = (th + np.pi / 2) % np.pi - np.pi / 2
    resid = res.fun.reshape(cut.shape)
    chi = np.std(resid[R - 6:R + 7, R - 6:R + 7]) / noise
    fits.append(dict(y=float(y + y0), x=float(x + x0), A=float(A), sa=float(sa), sb=float(sb),
                     th=float(np.degrees(th)), c=float(c), chi=float(chi), snr=float(A / noise)))
print('ajustats:', len(fits))
fits = [f for f in fits if f['snr'] > 6]
# angle global de la traça: dels ben allargats i brillants (pes = snr), mòdul 180°
good = [f for f in fits if 1.4 < f['sa'] / f['sb'] < 4 and 1.1 < f['sb'] < 3.0 and f['sa'] < 7 and f['snr'] > 12]
good = sorted(good, key=lambda f: -f['snr'])[:8]
wts = np.array([f['snr'] for f in good]); angles = np.radians([f['th'] for f in good])
ang_g = np.degrees(0.5 * np.arctan2(np.sum(wts * np.sin(2 * angles)), np.sum(wts * np.cos(2 * angles))))
sa_g = float(np.median([f['sa'] for f in good])); sb_g = float(np.median([f['sb'] for f in good]))
print('estrelles brillants allargades:', len(good), ' angle global de la traça:', round(ang_g, 1), '°',
      ' σ major mediana', round(sa_g, 2), ' σ menor mediana', round(sb_g, 2))

def dang(a, b):
    d = (a - b + 90) % 180 - 90
    return abs(d)

# criteris finals: mateixa direcció de traça (±12°), mida de traça compatible, prou senyal,
# i ajust acceptable (el llindar de residu creix amb la brillantor: el model gaussià és aproximat)
stars = []
for f in fits:
    elong = f['sa'] / f['sb']
    if not (1.15 < elong < 4.5): continue
    if not (1.2 < f['sb'] < 2.4): continue
    if not (2.2 <= f['sa'] <= 5.5): continue
    if dang(f['th'], ang_g) > 12: continue
    if f['snr'] < 8: continue
    if f['chi'] > max(3.5, 0.15 * f['snr']): continue
    stars.append(f)
print('estrelles acceptades:', len(stars))
json.dump(dict(angle_global=ang_g, noise=float(noise), stars=stars), open(OUT.replace('.npy', '_estrelles.json'), 'w'), indent=1)

# --- substitució per canal ---------------------------------------------------------
out = img.copy()
RR = 14
yy2, xx2 = np.mgrid[-RR:RR + 1, -RR:RR + 1]
n_done = 0
for f in stars:
    yi, xi = int(round(f['y'])), int(round(f['x']))
    if yi - RR < 0 or xi - RR < 0 or yi + RR + 1 > H or xi + RR + 1 > W: continue
    dy, dx = f['y'] - yi, f['x'] - xi
    th = np.radians(f['th'])
    ct, st = np.cos(th), np.sin(th)
    u = (xx2 - dx) * ct + (yy2 - dy) * st
    v = -(xx2 - dx) * st + (yy2 - dy) * ct
    shape_el = np.exp(-0.5 * (u / f['sa']) ** 2 - 0.5 * (v / f['sb']) ** 2)
    s_round = float(np.clip(f['sb'], 1.2, 2.2))
    shape_ro = np.exp(-0.5 * ((xx2 - dx) ** 2 + (yy2 - dy) ** 2) / s_round ** 2)
    flux_el = 2 * np.pi * f['sa'] * f['sb']
    flux_ro = 2 * np.pi * s_round ** 2
    for c in range(3):
        cut = out[yi - RR:yi + RR + 1, xi - RR:xi + RR + 1, c]
        # fons local per canal (mediana de l'anell 9–14 px) i amplitud per canal per mínims quadrats
        ring = (np.hypot(xx2 - dx, yy2 - dy) > 9)
        bgc = np.median(cut[ring])
        d = cut - bgc
        A_c = max(float(np.sum(d * shape_el) / np.sum(shape_el ** 2)), 0.0)
        # resta el·líptica, afegeix rodona amb el mateix flux
        newcut = cut - A_c * shape_el + (A_c * flux_el / flux_ro) * shape_ro
        out[yi - RR:yi + RR + 1, xi - RR:xi + RR + 1, c] = np.clip(newcut, 0, 1)
    n_done += 1
print('substituïdes:', n_done)
np.save(OUT, out.astype(np.float32))
