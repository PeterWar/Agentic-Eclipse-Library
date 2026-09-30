"""El «artefacte tangencial» de Pere a 1,7–1,9 R☉: és el graó de la fusió HDR de la capa Vixen al
contorn on l'apilat de 10,3 s satura (13995 ADU). L'apilat de 10,3 s de l'HDR4 és un ~2 % més fosc que
el de 2 s (10,3/(2×5,15) = 0,977–0,987 a 1,5–3,3 R☉; 2 s/1 s = 1,001–1,008), i on la fusió passa del
10,3 s al 2 s hi ha un graó del 2 % en lineal → +0,7 % passa-alt a la capa de Pere, i on el contorn
és recte es veu com una ratlla tangencial.

Correcció empírica sobre la capa (la meva capa és la de Pere a r < 3): coordenada s = valor de
l'apilat de 10,3 s (fora del cremat) o distància cap endins del contorn (dins); perfil A(s) =
mediana de L / G60(L) per bins de s a tot el contorn (totes les azimuts); base lineal entre els dos
extrems i rampes; K = 1/A(s). S'aplica K a tots els TIFF d'APILAT/ (base, REALCADA, TANGENCIAL,
EXTENSIO, CELPLA, ESTESA); no als PASSALT."""
import os, glob, numpy as np, tifffile
from scipy import ndimage as ndi
from PIL import Image

SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.expanduser('~/Downloads/Encaixada_2026-08-18/APILAT/')
T, B, Lm, Rm = 550, 250, 600, 300
H0, W0 = 4553, 6748
sl = (slice(T, T + H0), slice(Lm, Lm + W0))
vix = np.load(os.path.join(SP, 'vixen_canvas_rgb.npy'))
r = np.load(os.path.join(SP, 'r_rsol.npy')); th = np.load(os.path.join(SP, 'theta_deg.npy'))
g10 = np.load(os.path.join(SP, 'g10_canvas.npy'))       # 10,3 s, verd, −512
sat10 = np.load(os.path.join(SP, 'sat10_canvas.npy'))
WHITE = 13995 - 512
L = 0.2126 * vix[..., 0] + 0.7152 * vix[..., 1] + 0.0722 * vix[..., 2]
L60 = ndi.gaussian_filter(L, 60)
rho = L / np.maximum(L60, 1e-6)

# regió cremada del 10,3 s + disc lunar → el contorn exterior és el que compta
fill = ndi.binary_fill_holes(sat10 | (r < 1.05))
fill = ndi.binary_opening(fill, iterations=3)
d_in = ndi.distance_transform_edt(fill)          # px cap endins des del contorn exterior (0 fora)
g10s = ndi.gaussian_filter(g10, 2.0)
# coordenada unificada: fora, per valor del 10,3 s (ADU sobre negre); dins, per distància
S_LO, S_HI, DS = 10500.0, WHITE, 50.0            # 60 bins fora
D_HI, DD = 140.0, 4.0                            # 35 bins dins
nb_out = int((S_HI - S_LO) / DS); nb_in = int(D_HI / DD)
idx = np.full(r.shape, -1, np.int32)
outm = (~fill) & (g10s >= S_LO) & (g10s < S_HI) & (r > 1.2) & (r < 3.0)
idx[outm] = ((g10s[outm] - S_LO) / DS).astype(np.int32)
inm = fill & (d_in > 0) & (d_in < D_HI) & (r > 1.1)
idx[inm] = nb_out + (d_in[inm] / DD).astype(np.int32)
NB = nb_out + nb_in
A = np.ones(NB); n = np.zeros(NB, int)
for k in range(NB):
    m = idx == k
    n[k] = m.sum()
    if n[k] > 200:
        A[k] = np.median(rho[m])
# base lineal entre els extrems (5 bins a cada costat) i rampes de 6 bins
k = np.arange(NB)
a0 = A[:5].mean(); a1 = A[-5:].mean()
base = a0 + (a1 - a0) * (k - 2) / (NB - 5)
An = A / base
taper = np.ones(NB); taper[:6] = np.linspace(0, 1, 6); taper[-6:] = np.linspace(1, 0, 6)
An = 1 + (An - 1) * taper
print('perfil A(s) (fora: bins de 50 ADU de 10500 a 13483; dins: bins de 4 px):')
for kk in range(0, NB, 3):
    tag = f'{S_LO + kk * DS:6.0f} ADU' if kk < nb_out else f'{(kk - nb_out) * DD:4.0f} px dins'
    print(f'   bin {kk:3d} {tag:12s} n={n[kk]:8d}  A={A[kk]:.4f}  A_norm={An[kk]:.4f}')
print(f'màxim de |A_norm − 1|: {100 * np.abs(An - 1).max():.2f} % al bin {np.argmax(np.abs(An - 1))}')
K = np.ones(r.shape, np.float32)
sel = idx >= 0
K[sel] = (1.0 / An[idx[sel]]).astype(np.float32)
K = ndi.gaussian_filter(K, 1.5)      # suavitza els salts de bin
np.save(os.path.join(SP, 'K_grao_hdr.npy'), K)
print('K: min %.4f max %.4f, píxels corregits %d' % (K.min(), K.max(), (np.abs(K - 1) > 1e-4).sum()))

# --- verificació al lloc que Pere marca: perfil perpendicular a la seva línia, abans i després ---
Ap_ = np.array([2735.0, 2714.0]); Bp_ = np.array([3440.0, 3006.0])
ang = np.degrees(np.arctan2(Bp_[1] - Ap_[1], Bp_[0] - Ap_[0])); C = 0.5 * (Ap_ + Bp_)
def rot_crop(img, cx, cy, ang_deg, w=1100, h=700):
    yy, xx = np.mgrid[-h // 2:h // 2, -w // 2:w // 2].astype(np.float64); a = np.radians(ang_deg)
    X = cx + xx * np.cos(a) - yy * np.sin(a); Y = cy + xx * np.sin(a) + yy * np.cos(a)
    return ndi.map_coordinates(img, [Y, X], order=1, mode='nearest')
y = np.arange(-350, 350)
rows = []
for nom, img in (('abans', L), ('després', L * K)):
    rc = rot_crop(img, C[0], C[1], ang); p = rc[:, 250:850].mean(1)
    pn = p / np.median(p); hpp = pn - ndi.gaussian_filter1d(pn, 25)
    j = np.argmax(np.abs(hpp[280:420])) + 280
    print(f'  {nom:8s}: passa-alt màx a |y|<70: {100 * hpp[j]:+.2f} % a y={y[j]};  rang −150..150: {100 * hpp[200:500].min():+.2f}…{100 * hpp[200:500].max():+.2f} %')
    hp = rc - ndi.gaussian_filter(rc, 20); sd = 1.4826 * np.median(np.abs(hp - np.median(hp)))
    rows.append((np.clip(0.5 + hp / (8 * sd), 0, 1) * 255).astype(np.uint8))
Image.fromarray(np.concatenate(rows, 0)).save(OUT + 'zoom_artefacte_girat_abans_despres.png')
# el mateix test a tot el contorn: mitjana de |A| residual per sectors
Kl = L * K; rho2 = Kl / np.maximum(ndi.gaussian_filter(Kl, 60), 1e-6)
print('residu per sectors de 45° (mediana de rho al bin del màxim, abans → després):')
kb = int(np.argmax(np.abs(An - 1)))
for t0 in range(-180, 180, 45):
    m = (idx == kb) & (th >= t0) & (th < t0 + 45)
    if m.sum() > 100:
        print(f'   θ {t0:+4d}: {100 * (np.median(rho[m]) - 1):+.2f} % → {100 * (np.median(rho2[m]) - 1):+.2f} %  (n={m.sum()})')

# --- aplica K a tots els TIFF d'APILAT (no PASSALT) ---
Kext = np.ones((H0 + T + B, W0 + Lm + Rm), np.float32); Kext[sl] = K
ICC = open(os.path.join(SP, 'perfil.icc'), 'rb').read()
if os.environ.get('APPLY') != '1':
    raise SystemExit('només anàlisi (APPLY=1 per aplicar)')
for f in sorted(glob.glob(OUT + 'APILAT_*.tif')):
    if 'PASSALT' in f:
        continue
    with tifffile.TiffFile(f) as tf:
        desc = tf.pages[0].description or ''
        a = tf.asarray()
    if a.ndim != 3 or a.shape[2] != 3:
        print('salto', f); continue
    Kx = K if a.shape[:2] == (H0, W0) else Kext
    if a.shape[:2] not in ((H0, W0), Kext.shape):
        print('mida inesperada, salto', f, a.shape); continue
    b = np.clip(a.astype(np.float32) * Kx[..., None], 0, 65535).round().astype(np.uint16)
    tifffile.imwrite(f, b, photometric='rgb', compression='zlib', extratags=[(34675, 'B', len(ICC), ICC, False)],
                     description=(desc + ' | grao HDR del contorn 10,3 s corregit (v4b)')[:1000], resolution=(300, 300), metadata=None)
    print('corregit', os.path.basename(f))
print('fet')
