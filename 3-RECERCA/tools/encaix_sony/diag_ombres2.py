"""Ombres: quocient a baixa freqüència capa/Vixen, cobertura de l'apilat i el perfil de la vora
superior de la Vixen. Només lectura."""
import os, numpy as np, tifffile
import scipy.ndimage as ndi
from PIL import Image

SP = os.path.dirname(os.path.abspath(__file__))
D = os.path.expanduser('~/Downloads/Encaixada_2026-08-18/APILAT')
suau = tifffile.imread(os.path.join(D, '_anteriors_DoG', 'APILAT_Capa_Sony_encaixada_VORESNETES_REALCADA_SUAU_6748x4553.tif')).astype(np.float32)
base = tifffile.imread(os.path.join(D, 'APILAT_Capa_Sony_encaixada_VORESNETES_6748x4553.tif')).astype(np.float32)
vix = np.load(os.path.join(SP, 'vixen_canvas_rgb.npy')).astype(np.float32) * 65535
r = np.load(os.path.join(SP, 'r_rsol.npy'))
H, W = r.shape
T, B, Lm, Rm = 550, 250, 600, 300
cov = np.load(os.path.join(SP, 'sony_stack_ext_cov.npy'))[T:T + H, Lm:Lm + W]
old = np.load(os.path.join(SP, 'fit_ext_VORESNETES.npy'))[T:T + H, Lm:Lm + W] * 65535   # capa anterior encaixada (reserva)

def lum(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]

def low(a, s=20):
    return ndi.gaussian_filter(a, s)

Lv = low(lum(vix)); Ls = low(lum(suau)); Lb = low(lum(base)); Lo = low(lum(old))
def stretch(q, lo=0.6, hi=1.4):
    v = np.clip((q - lo) / (hi - lo), 0, 1); v[r < 3.2] = 0.5
    return (v[::4, ::4] * 255).astype(np.uint8)
qs = Ls / np.maximum(Lv, 1); qb = Lb / np.maximum(Lv, 1); qo = Lo / np.maximum(Lv, 1)
row1 = np.concatenate([stretch(qs), stretch(qb)], 1)
covp = (cov[::4, ::4] * 200 + 55).astype(np.uint8)
row2 = np.concatenate([stretch(qo), covp], 1)
Image.fromarray(np.concatenate([row1, row2], 0)).save(os.path.join(SP, 'ombres_quocient.png'))
print('SUAU_v1/Vixen | BASE_v2/Vixen ; capa_anterior/Vixen | cobertura apilat   (estirat 0,6–1,4)')

# perfils del quocient a les vores
for nom, q in (('SUAU_v1', qs), ('BASE_v2', qb), ('capa_ant', qo)):
    print('==', nom)
    print('  fila superior (y=0..600 cada 50), mediana x∈[2500,4500]:', [round(float(np.median(q[y, 2500:4500])), 3) for y in range(0, 601, 50)])
    print('  fila inferior (y=H-1..H-600), x∈[2500,4500]:', [round(float(np.median(q[H - 1 - y, 2500:4500])), 3) for y in range(0, 601, 50)])
    print('  columna esq (x=0..600), y∈[1500,3000]:', [round(float(np.median(q[1500:3000, x])), 3) for x in range(0, 601, 50)])
    print('  columna dreta (x=W-1..W-600), y∈[1500,3000]:', [round(float(np.median(q[1500:3000, W - 1 - x])), 3) for x in range(0, 601, 50)])
    for cx, cy, tag in ((100, 100, 'dalt-esq'), (W - 100, 100, 'dalt-dreta'), (100, H - 100, 'baix-esq'), (W - 100, H - 100, 'baix-dreta')):
        print(f'  canto {tag}: q={float(np.median(q[cy-80:cy+80, cx-80:cx+80])):.3f}  cov={cov[cy-80:cy+80, cx-80:cx+80].mean():.2f}')

# Vixen: perfil de files a dalt (luminància absoluta) per veure l'enfosquiment
print('Vixen L mediana per fila (y=0..800 cada 25), x∈[1000,6000]:')
print([int(np.median(Lv[y, 1000:6000])) for y in range(0, 801, 25)])
print('Vixen L mediana per fila baix (y=H-1-...):', [int(np.median(Lv[H - 1 - y, 1000:6000])) for y in range(0, 401, 50)])
print('Vixen L columna esq (x=0..400 cada 50), y∈[1000,3500]:', [int(np.median(Lv[1000:3500, x])) for x in range(0, 401, 50)])
print('Vixen L columna dreta:', [int(np.median(Lv[1000:3500, W - 1 - x])) for x in range(0, 401, 50)])
# ombra a la punta del raig: retall 900×700 al voltant de (1840, 220) de SUAU_v1, base i Vixen, estirat local
def crop(a, cx=1840, cy=260, hw=450, hh=260):
    x0, x1 = max(0, cx - hw), min(W, cx + hw); y0, y1 = max(0, cy - hh), min(H, cy + hh)
    c = low(lum(a), 6)[y0:y1, x0:x1]
    lo, hi = np.percentile(c, [1, 99]); return (np.clip((c - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)
Image.fromarray(np.concatenate([crop(suau), crop(base), crop(vix)], 1)).save(os.path.join(SP, 'ombres_punta_raig.png'))
print('punta del raig: SUAU_v1 | BASE_v2 | Vixen (retall (1390..2290, 0..520), estirat local p1–p99)')
