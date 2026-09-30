"""Variant cosmètica CELPLA: aplana el cel del camp llunyà (r > ~5 R☉) de la capa v4.
El cel real (el que veuen els dos trens) cau un ~20 % dels punts mitjans de les vores als cantons
extrems del llenç (r 9 R☉). Aquí es modela per canal amb una convolució normalitzada (σ 250 px) sobre
r > 5,6 dins del llenç i es porta multiplicativament al nivell de l'anell 5,6–6,2 R☉, amb una rampa
radial 4,8 → 6,2 (0 dins, 1 fora): la corona no es toca. Surt de fit_ext_VORESNETES_APILAT.npy (base v4)
i enh_ext_SUAU_APILAT.npy (REALCADA SUAU v4)."""
import os, numpy as np, tifffile
from scipy import ndimage as ndi
from PIL import Image

SP = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.expanduser('~/Downloads/Encaixada_2026-08-18/APILAT')
ICC = open(os.path.join(SP, 'perfil.icc'), 'rb').read()
T, B, Lm, Rm = 550, 250, 600, 300
H0, W0 = 4553, 6748
H, W = H0 + T + B, W0 + Lm + Rm
sl = (slice(T, T + H0), slice(Lm, Lm + W0))
SX, SY = 3563.891 - 143 + Lm, 2274.66 - 87 + T
RSOL = 446.15
yy, xx = np.mgrid[0:H, 0:W]
r = (np.hypot(xx - SX, yy - SY) / RSOL).astype(np.float32)
inside = np.zeros((H, W), bool); inside[sl] = True
cov = np.load(os.path.join(SP, 'sony_stack_ext_cov.npy'))
fit = np.load(os.path.join(SP, 'fit_ext_VORESNETES_APILAT.npy'))
enh = np.load(os.path.join(SP, 'enh_ext_SUAU_APILAT.npy'))

m = (inside & cov & (r > 5.6)).astype(np.float32)
den = ndi.gaussian_filter(m, 250.0, mode='constant')
def ss(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
ramp = ss((r - 4.8) / 1.4)
# només luminància: un sol factor per píxel per als tres canals (el color del cel —més blau lluny del Sol—
# es conserva; el que s'iguala és la brillantor). Amb un factor per canal el cel llunyà agafava el color
# de 6 R☉ (R ×1,47 contra B ×1,31 al cantó de baix a l'esquerra: un 12 % més vermell del natural).
Lum = 0.2126 * fit[..., 0] + 0.7152 * fit[..., 1] + 0.0722 * fit[..., 2]
num = ndi.gaussian_filter(Lum * m, 250.0, mode='constant')
S = np.where(den > 0.05, num / np.maximum(den, 1e-6), np.nan)
idx = ndi.distance_transform_edt(np.isnan(S), return_distances=False, return_indices=True)
S = S[tuple(idx)]
Tc = float(np.median(S[inside & (r > 5.6) & (r < 6.2)]))
F1 = np.clip((Tc / np.maximum(S, 1e-4)) ** ramp, 0.8, 1.6).astype(np.float32)
print(f'luminància: nivell objectiu {65535*Tc:.0f}; factor als cantons del llenç: '
      f'{F1[sl][100,100]:.3f} {F1[sl][100,-100]:.3f} {F1[sl][-100,100]:.3f} {F1[sl][-100,-100]:.3f}; costats {F1[sl][100,W0//2]:.3f} {F1[sl][-100,W0//2]:.3f} {F1[sl][H0//2,100]:.3f} {F1[sl][H0//2,-100]:.3f}')
F = F1[..., None]
np.save(os.path.join(SP, 'celpla_factor.npy'), F1)

def save16(name, arr, desc):
    a16 = np.round(np.clip(arr, 0, 1) * 65535).astype(np.uint16)
    tifffile.imwrite(os.path.join(OUTDIR, name), a16, photometric='rgb', compression='zlib',
                     extratags=[(34675, 'B', len(ICC), ICC, False)], description=desc, resolution=(300, 300), metadata=None)
    print('desat', name)
def to8(a, s=4): return (np.clip(a[::s, ::s], 0, 1) * 255).astype(np.uint8)

fitp = np.clip(fit * F, 0, 1).astype(np.float32); enhp = np.clip(enh * F, 0, 1).astype(np.float32)
save16('APILAT_Capa_Sony_encaixada_VORESNETES_CELPLA_6748x4553.tif', fitp[sl], 'v4 + cel aplanat (cosmetic): camp llunya r>5,6 portat al nivell de 5,6-6,2 Rsol, rampa 4,8-6,2; la corona no es toca')
save16('APILAT_Capa_Sony_encaixada_VORESNETES_REALCADA_SUAU_CELPLA_6748x4553.tif', enhp[sl], 'v4 REALCADA SUAU + cel aplanat (cosmetic), mateixa rampa')
Image.fromarray(to8(enhp[sl])).save(os.path.join(OUTDIR, 'APILAT_despres_REALCADA_SUAU_CELPLA.jpg'), quality=92)
sep = np.full((to8(enh[sl]).shape[0], 10, 3), 255, np.uint8)
Image.fromarray(np.concatenate([to8(enh[sl]), sep, to8(enhp[sl])], 1)).save(os.path.join(OUTDIR, 'APILAT_comparacio_SUAU_v4_vs_CELPLA.jpg'), quality=92)
L = enhp[sl].mean(-1)
for tag, (y, x) in (('dalt-esq', (150, 150)), ('dalt-dreta', (150, W0 - 150)), ('baix-esq', (H0 - 150, 150)), ('baix-dreta', (H0 - 150, W0 - 150)), ('dalt', (150, W0 // 2)), ('baix', (H0 - 150, W0 // 2)), ('esq', (H0 // 2, 150)), ('dreta', (H0 // 2, W0 - 150))):
    print(f'   CELPLA SUAU {tag:11s} L = {65535*np.median(L[y-100:y+100, x-100:x+100]):7.0f}')
print('fet')
