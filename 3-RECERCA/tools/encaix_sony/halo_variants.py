"""Halo concèntric de 2,7–4 R☉ (és de la capa Vixen: el SUAU hi coincideix a ≤ 0,1 %).

El perfil de luminància azimutal és llis (a ≤ 1,5 % d'una Hermite log-log): el que es veu és
el CREUAMENT de color —corona càlida (R−B)/L = +0,36 a 2,5 R☉, gris a 3,3, cel blau −0,30 a
4,5— sobre la meseta on la corona i el cel s'igualen. Tractament: dues funcions suaus i
monòtones del radi (rampa smoothstep 2,6 → 4,5 R☉, constant més enllà; cap anell possible):
  croma × CM   (1 → CM)   i   luminància × G  (1 → G).
  A: CM 0,35, G 0,95 (recomanada)   B: CM 0,20, G 0,90 (més fort, cel més fosc)   C: CM 0,50, G 1,00 (toc lleu)
"""
import os
import numpy as np
import tifffile
from PIL import Image

OUTDIR = os.path.expanduser('~/Downloads/Encaixada_2026-08-18')
ICC = open('perfil.icc', 'rb').read()
T, B, Lm, Rm = 550, 250, 600, 300
H0, W0 = 4553, 6748
H, W = H0 + T + B, W0 + Lm + Rm
SX, SY = 3563.891 - 143 + Lm, 2274.66 - 87 + T
yy, xx = np.mgrid[0:H, 0:W]
r = (np.hypot(xx - SX, yy - SY) / 446.15).astype(np.float32)
sl = (slice(T, T + H0), slice(Lm, Lm + W0))
R1, R2 = 2.6, 4.5
t = np.clip((r - R1) / (R2 - R1), 0, 1); t = (t * t * (3 - 2 * t))[..., None]
VARS = {'A': (0.35, 0.95), 'B': (0.20, 0.90), 'C': (0.50, 1.00)}

def apply(img, cm_ext, g_ext):
    cm = 1 - t * (1 - cm_ext); g = 1 - t * (1 - g_ext)
    Lq = img.mean(-1, keepdims=True)
    return np.clip((Lq + (img - Lq) * cm) * g, 0, 1).astype(np.float32)

def save16(name, arr, desc):
    a16 = np.round(np.clip(arr, 0, 1) * 65535).astype(np.uint16)
    tifffile.imwrite(os.path.join(OUTDIR, name), a16, photometric='rgb', compression='zlib',
                     extratags=[(34675, 'B', len(ICC), ICC, False)], description=desc, resolution=(300, 300), metadata=None)
    print('desat', name)
def to8(a, s=4): return (np.clip(a[::s, ::s], 0, 1) * 255).astype(np.uint8)

# neteja de la prova anterior (només luminància isotònica, efecte < 0,5 %)
for f in os.listdir(OUTDIR):
    if 'SENSEHALO' in f and '_A_' not in f and '_B_' not in f and '_C_' not in f:
        os.remove(os.path.join(OUTDIR, f))

for src, tag in (('enh_ext_SUAU.npy', 'REALCADA_SUAU_'), ('enh_ext_FORT.npy', 'REALCADA_FORT_'), ('fit_ext_VORESNETES.npy', '')):
    img = np.load(src)
    for v, (cm, g) in VARS.items():
        if tag != 'REALCADA_SUAU_' and v != 'A':
            continue
        out = apply(img, cm, g)
        save16(f'Capa_Sony_encaixada_VORESNETES_{tag}SENSEHALO_{v}_6748x4553.tif', out[sl],
               f'SENSEHALO {v}: croma x{cm} i luminancia x{g} de 2,6 a 4,5 Rsol (smoothstep) i mes enlla; sobre {src}')
        if tag == 'REALCADA_SUAU_':
            save16(f'ESTESA_7648x5353_encaixada_VORESNETES_REALCADA_SUAU_SENSEHALO_{v}.tif', out, f'SENSEHALO {v}, domini estes')
            Image.fromarray(to8(out[sl])).save(os.path.join(OUTDIR, f'despres_SUAU_SENSEHALO_{v}.jpg'), quality=92)
            np.save(f'suau_sensehalo_{v}.npy', out)
# comparació 2×2 al voltant del Sol: SUAU, A, B, C
cx, cy = 3421 + Lm, 2188 + T
base = np.load('enh_ext_SUAU.npy')
tiles = [to8(base[cy - 2000:cy + 2000, cx - 2000:cx + 2000], 5)]
for v in 'ABC':
    o = np.load(f'suau_sensehalo_{v}.npy'); tiles.append(to8(o[cy - 2000:cy + 2000, cx - 2000:cx + 2000], 5))
top = np.concatenate(tiles[:2], 1); bot = np.concatenate(tiles[2:], 1)
Image.fromarray(np.concatenate([top, bot], 0)).save(os.path.join(OUTDIR, 'comparacio_halo_SUAU_A_B_C.jpg'), quality=90)
print('fet')
