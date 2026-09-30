"""a6 · On tenen els filtres (V88, sense suavitzat) una estructura PARAL·LELA al limbe (coherent al llarg de l'azimut) als primers 14 px.
Per què: el suavitzat radial cura les línies (detall radial fals coherent al llarg del limbe), però on no n'hi ha només esborrona la textura
real (la «lent» de la V90). Mesura: en polars (0,05° × 0,25 px), el detall radial fi del ràster (perfil − perfil suavitzat σ 4 px en el radi)
a d 1–12 px, (a) mitjanat en finestres de 3° d'azimut (el coherent: les línies sobreviuen, la textura aleatòria es cancel·la) i (b) sense
mitjanar (la textura). Índex = rms(a) / rms(b) per azimut. Sortida: A6_COHERENT.json i LAMINA_A6_coherent.png."""
from v91_comu import *
import cv2
from scipy.ndimage import uniform_filter1d, gaussian_filter1d
claim(); GEO = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
FIN = ARREL / '4-RESULTATS/v88_20260923/filtres_finals'; NT = 7200; DR = 0.25; DS = np.arange(-4, 20.001, DR); TS = np.radians((np.arange(NT) + 0.5) * 360 / NT)
TT, DD = np.meshgrid(TS, DS); MX = (cx + (R + DD) * np.cos(TT)).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT)).astype(np.float32)
sel = (DS >= 1) & (DS <= 12); rep = dict(capes={}); TSd = np.degrees(TS); acc = []
for tag in ['P01_NRGF', 'P01_NRGF_extrap', 'P02_RHEF', 'P02c_RHEF_local60_native', '04', '05', 'P04_WOW', 'P05_WOW_bilateral']:
    u = np.load(FIN / f'{tag}_u16.npy', mmap_mode='r'); x0, x1, y0, y1 = int(MX.min()) - 2, int(MX.max()) + 3, int(MY.min()) - 2, int(MY.max()) + 3
    X = np.asarray(u[y0:y1, x0:x1], np.float32) / 65535; P = cv2.remap(X, MX - x0, MY - y0, cv2.INTER_LINEAR)
    HP = P - gaussian_filter1d(P, 4 / DR, axis=0)                     # detall radial fi
    coh = uniform_filter1d(HP, int(3 / 0.05), axis=1, mode='wrap')      # mitjana en 3° d'azimut
    a = np.sqrt((coh[sel] ** 2).mean(0)); b = np.sqrt((HP[sel] ** 2).mean(0)); idx = uniform_filter1d(a, 20, mode='wrap') / np.maximum(uniform_filter1d(b, 20, mode='wrap'), 1e-6)
    acc.append(idx); rep['capes'][tag] = {f'{s}-{s + 10}': round(float(idx[(TSd >= s) & (TSd < s + 10)].mean()), 3) for s in range(0, 360, 10)}
    log(tag + ' fet')
I = np.mean(acc, 0); rep['index_mitja_per_10_graus'] = {f'{s}-{s + 10}': round(float(I[(TSd >= s) & (TSd < s + 10)].mean()), 3) for s in range(0, 360, 10)}
np.save(SORT / 'A6_index_coherent.npy', I); desa_json('A6_COHERENT.json', rep)
from PIL import Image, ImageDraw, ImageFont
Wd, Hd = 1800, 520; S = Image.new('RGB', (Wd, Hd), 'white'); d = ImageDraw.Draw(S); F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15)
X0, Y0, XW, YH = 60, 40, Wd - 90, Hd - 110; top = max(0.6, float(I.max()) * 1.05)
for a0, a1, col, et in ((104, 119, (170, 220, 255), 'línies V88 (blau)'), (121, 152, (220, 190, 250), 'línies V88 (lila)'), (205, 229, (220, 190, 250), 'línies V88 (lila)'),
                        (0, 32, (255, 200, 230), 'lent V90'), (340, 360, (255, 200, 230), ''), (44.8, 98.4, (255, 200, 230), 'lent V90'), (230.5, 305, (255, 200, 230), 'lent V90')):
    d.rectangle((X0 + a0 / 360 * XW, Y0, X0 + a1 / 360 * XW, Y0 + YH), fill=col); d.text((X0 + a0 / 360 * XW + 2, Y0 + 2), et, fill='black', font=F)
pts = [(X0 + t / 360 * XW, Y0 + YH - min(v / top, 1) * YH) for t, v in zip(TSd[::4], I[::4])]; d.line(pts, fill='black', width=2)
for t in range(0, 361, 30): d.text((X0 + t / 360 * XW - 10, Y0 + YH + 6), f'{t}°', fill='black', font=F)
for v in np.arange(0, top, 0.1): d.text((10, Y0 + YH - v / top * YH - 8), f'{v:.1f}', fill='black', font=F)
d.text((X0, Hd - 40), "Índex d'estructura paral·lela al limbe (detall radial fi mitjanat en 3° d'azimut / sense mitjanar), d 1–12 px, 8 filtres de la V88", fill='black', font=F)
S.save(SORT / 'LAMINA_A6_coherent.png'); log(json.dumps(rep['index_mitja_per_10_graus']))
