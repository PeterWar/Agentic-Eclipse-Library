"""Treu el «halo» concèntric de 2,7–4 R☉: és de la capa Vixen (el SUAU hi coincideix a ≤ 0,1 %).

Dues coses, totes dues funcions suaus del radi (cap anell nou possible: només es re-grada el gradient):
1. Luminància: el perfil azimutal té una espatlla a 3,2–3,9 R☉ (el pendent log-log torna a
   fer-se més pronunciat després d'aplanar-se). Es força que el pendent sigui monòton (només pot
   aplanar-se cap enfora: regressió isotònica del pendent) i s'aplica el factor target/actual a
   R, G i B (rampa d'entrada 2,0→2,4 R☉, sortida 6,0→6,5).
2. Croma (opcional): la corona és càlida i el cel blau; on es creuen (3,3 R☉) queda una banda
   grisa. Un multiplicador de croma que baixa suau de 1 (2,6 R☉) a CROMA_EXT (≥ 4,5 R☉) fa el
   cel menys blau i el creuament menys visible.

Ús: halo_fix.py CROMA_EXT   (1.0 = només luminància)
"""
import sys, os
import numpy as np
from scipy import ndimage as ndi
from sklearn.isotonic import IsotonicRegression
import tifffile
from PIL import Image

CROMA_EXT = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
SUF = 'SENSEHALO' if CROMA_EXT >= 0.999 else f'SENSEHALO_CEL{int(round(CROMA_EXT*100))}'
OUTDIR = os.path.expanduser('~/Downloads/Encaixada_2026-08-18')
ICC = open('perfil.icc', 'rb').read()
T, B, Lm, Rm = 550, 250, 600, 300
H0, W0 = 4553, 6748
H, W = H0 + T + B, W0 + Lm + Rm
SX, SY = 3563.891 - 143 + Lm, 2274.66 - 87 + T
yy, xx = np.mgrid[0:H, 0:W]
r = (np.hypot(xx - SX, yy - SY) / 446.15).astype(np.float32)
sl = (slice(T, T + H0), slice(Lm, Lm + W0))

# perfil de luminància del SUAU (anells de 0,02 R☉, tots els píxels del domini estès)
base = np.load('enh_ext_SUAU.npy')
L = base.mean(-1)
DR = 0.02
rb = np.clip((r / DR).astype(int), 0, 599)
cnt = np.bincount(rb.ravel(), minlength=600).astype(float)
prof = np.where(cnt > 0, np.bincount(rb.ravel(), weights=L.ravel(), minlength=600) / np.maximum(cnt, 1), np.nan)
rr = (np.arange(600) + 0.5) * DR
ok = np.isfinite(prof) & (rr >= 1.8) & (rr <= 6.5)
x = np.log(rr[ok]); y = np.log(prof[ok])
# pendent local (diferència finita) i regressió isotònica creixent (el pendent només s'aplana cap enfora)
xm = 0.5 * (x[1:] + x[:-1]); slope = np.diff(y) / np.diff(x)
ir = IsotonicRegression(increasing=True).fit(xm, slope)
slope_t = ir.predict(xm)
# integra: mateix punt de partida (r = 1,8), i reancora perquè a 6,5 coincideixi (repartint la diferència linealment)
y_t = np.concatenate([[y[0]], y[0] + np.cumsum(slope_t * np.diff(x))])
y_t = y_t - (y_t[-1] - y[-1]) * (x - x[0]) / (x[-1] - x[0])
f = np.exp(y_t - y)                     # factor target/actual sobre la mostra
# rampa: 1 dins de 2,0→2,4 i fora 6,0→6,5
rrk = rr[ok]
ramp_in = np.clip((rrk - 2.0) / 0.4, 0, 1); ramp_in = ramp_in * ramp_in * (3 - 2 * ramp_in)
ramp_out = np.clip((6.5 - rrk) / 0.5, 0, 1); ramp_out = ramp_out * ramp_out * (3 - 2 * ramp_out)
f = 1 + (f - 1) * ramp_in * ramp_out
f = np.clip(f, 0.88, 1.06)
f = ndi.gaussian_filter1d(f, 1.5, mode='nearest')
print('factor de luminància: mín %.4f a r=%.2f, màx %.4f a r=%.2f' % (f.min(), rrk[np.argmin(f)], f.max(), rrk[np.argmax(f)]))
for a in (2.6, 2.9, 3.1, 3.3, 3.5, 3.7, 3.9, 4.1, 4.4, 4.8, 5.2, 5.6):
    i = np.argmin(np.abs(rrk - a)); print(f'  r={a}: f={f[i]:.4f}')
fmap = np.interp(r, rrk, f, left=1.0, right=1.0).astype(np.float32)

# croma
if CROMA_EXT < 0.999:
    tc = np.clip((r - 2.6) / (4.5 - 2.6), 0, 1); tc = tc * tc * (3 - 2 * tc)
    cm = (1 - tc * (1 - CROMA_EXT)).astype(np.float32)
else:
    cm = None

def apply(img):
    out = img * fmap[..., None]
    if cm is not None:
        Lo = out.mean(-1, keepdims=True)
        out = Lo + (out - Lo) * cm[..., None]
    return np.clip(out, 0, 1).astype(np.float32)

def save16(name, arr, desc):
    a16 = np.round(np.clip(arr, 0, 1) * 65535).astype(np.uint16)
    tifffile.imwrite(os.path.join(OUTDIR, name), a16, photometric='rgb', compression='zlib',
                     extratags=[(34675, 'B', len(ICC), ICC, False)], description=desc, resolution=(300, 300), metadata=None)
    print('desat', name, a16.shape)
def to8(a, s=4): return (np.clip(a[::s, ::s], 0, 1) * 255).astype(np.uint8)
def sat(img, k):
    Lq = img.mean(-1, keepdims=True); return np.clip(Lq + (img - Lq) * k, 0, 1)

for nom, src in (('SUAU', 'enh_ext_SUAU.npy'), ('FORT', 'enh_ext_FORT.npy'), ('', 'fit_ext_VORESNETES.npy')):
    img = np.load(src)
    out = apply(img)
    tag = f'REALCADA_{nom}_' if nom else ''
    save16(f'Capa_Sony_encaixada_VORESNETES_{tag}{SUF}_6748x4553.tif', out[sl], f'{SUF}: espatlla de luminancia 3,2-3,9 Rsol treta (pendent log-log monoton), croma exterior x{CROMA_EXT}')
    if nom == 'SUAU':
        save16(f'ESTESA_7648x5353_encaixada_VORESNETES_REALCADA_SUAU_{SUF}.tif', out, f'{SUF}, domini estes')
        Image.fromarray(to8(out[sl])).save(os.path.join(OUTDIR, f'despres_SUAU_{SUF}.jpg'), quality=92)
        Image.fromarray(np.concatenate([to8(sat(img[sl], 5)), np.full((to8(img[sl]).shape[0], 12, 3), 255, np.uint8), to8(sat(out[sl], 5))], 1)).save(os.path.join(OUTDIR, f'comparacio_halo_saturacio_x5_{SUF}.jpg'), quality=90)
        np.save(f'out_{SUF}_SUAU.npy', out)
        # perfil després
        L2 = out.mean(-1)
        prof2 = np.where(cnt > 0, np.bincount(rb.ravel(), weights=L2.ravel(), minlength=600) / np.maximum(cnt, 1), np.nan)
        print('pendent log-log abans/després:')
        for a in (2.5, 2.9, 3.1, 3.3, 3.5, 3.7, 3.9, 4.1, 4.5, 5.0):
            i = int(a / DR); j = i + 10
            s1 = (np.log(prof[j]) - np.log(prof[i])) / (np.log(rr[j]) - np.log(rr[i])); s2 = (np.log(prof2[j]) - np.log(prof2[i])) / (np.log(rr[j]) - np.log(rr[i]))
            print(f'  {a:.1f}–{a+0.2:.1f}: {s1:+.3f} → {s2:+.3f}')
print('fet', SUF)
