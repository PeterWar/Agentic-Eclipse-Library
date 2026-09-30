"""Segona passada, estrictament local: al marc girat de la línia de Pere (x al llarg, y a través),
la resta del graó es modela com a funció de dy = y − y_sat(x) (y_sat = contorn de saturació del 10,3 s
per columna), perfil per canal = mediana sobre x ∈ [250, 1350] (del retall de 1600) de L/G25(L) − 1
després de la primera correcció (K_grao_local.npy), amb rampa en x. Es combina amb K1 → K_grao_total.npy
i, amb APPLY=1, s'aplica a tots els TIFF d'APILAT (no PASSALT)."""
import os, glob, numpy as np, tifffile
from scipy import ndimage as ndi
from PIL import Image

SP = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.expanduser('~/Downloads/Encaixada_2026-08-18/APILAT/')
T, B, Lm, Rm = 550, 250, 600, 300
H0, W0 = 4553, 6748
sl = (slice(T, T + H0), slice(Lm, Lm + W0))
vix = np.load(os.path.join(SP, 'vixen_canvas_rgb.npy'))
r = np.load(os.path.join(SP, 'r_rsol.npy'))
sat10 = np.load(os.path.join(SP, 'sat10_canvas.npy'))
K1 = np.load(os.path.join(SP, 'K_grao_local.npy'))
V1 = vix * K1
fill = ndi.binary_fill_holes(sat10 | (r < 1.05)); fill = ndi.binary_opening(fill, iterations=3)

Ap_ = np.array([2735.0, 2714.0]); Bp_ = np.array([3440.0, 3006.0])
ang = np.degrees(np.arctan2(Bp_[1] - Ap_[1], Bp_[0] - Ap_[0])); C = 0.5 * (Ap_ + Bp_)
a = np.radians(ang); ca, sa = np.cos(a), np.sin(a)
Wc, Hc = 1600, 700
def rot_crop(img, order=1):
    yy, xx = np.mgrid[-Hc // 2:Hc // 2, -Wc // 2:Wc // 2].astype(np.float64)
    X = C[0] + xx * ca - yy * sa; Y = C[1] + xx * sa + yy * ca
    return ndi.map_coordinates(img, [Y, X], order=order, mode='nearest')
# perfil coherent a y fix (files del marc girat), per canal: mitjana en x ∈ [X0+100, X1−100] del passa-alt
# relatiu 2-D (σ 25) → c(y); base lineal entre y = ±YM i rampes; K3 = 1/(1 + c(y)·wx(x))
yy, xx = np.mgrid[0:Hc, 0:Wc]
X0, X1, XR = 350, 1250, 100
wx = np.clip((xx - X0) / XR, 0, 1) * np.clip((X1 - xx) / XR, 0, 1); wx = wx * wx * (3 - 2 * wx)
YM = 100; y0r = Hc // 2
Krot = np.ones((Hc, Wc, 3), np.float32)
yv = np.arange(-YM, YM + 1)
for c in range(3):
    Lc = rot_crop(V1[..., c]); G = ndi.gaussian_filter(Lc, 25); rho = Lc / np.maximum(G, 1e-6) - 1
    cy = rho[y0r - YM:y0r + YM + 1, X0 + 100:X1 - 100].mean(1)
    base = cy[:8].mean() + (cy[-8:].mean() - cy[:8].mean()) * (np.arange(len(cy)) - 3.5) / (len(cy) - 8)
    cn = cy - base
    tap = np.ones(len(cn)); tap[:20] = np.linspace(0, 1, 20); tap[-20:] = np.linspace(1, 0, 20); cn *= tap
    cn = ndi.gaussian_filter1d(cn, 1.5)
    prof2 = np.zeros(Hc); prof2[y0r - YM:y0r + YM + 1] = cn
    Krot[..., c] = 1.0 / (1.0 + prof2[:, None] * wx)
    print(f'canal {"RGB"[c]}: c(y) ×100 cada 12 px de y=−60..+60:', ' '.join(f'{100*cn[YM+dd]:+.2f}' for dd in range(-60, 61, 12)))
# porta Krot al llenç: per a cada píxel del llenç, coordenades girades
K2 = np.ones(vix.shape, np.float32)
y0, y1 = int(C[1]) - 700, int(C[1]) + 700; x0, x1 = int(C[0]) - 1000, int(C[0]) + 1000
Yc, Xc = np.mgrid[y0:y1, x0:x1].astype(np.float64)
u = (Xc - C[0]) * ca + (Yc - C[1]) * sa + Wc / 2; v = -(Xc - C[0]) * sa + (Yc - C[1]) * ca + Hc / 2
for c in range(3):
    K2[y0:y1, x0:x1, c] = ndi.map_coordinates(Krot[..., c], [v, u], order=1, mode='constant', cval=1.0)
K = (K1 * K2).astype(np.float32)
np.save(os.path.join(SP, 'K_grao_total.npy'), K)
print('K total: min %.4f max %.4f' % (K.min(), K.max()))
# verificació
L = vix.mean(-1); L2 = (vix * K).mean(-1); y = np.arange(-350, 350); rows = []
for nom, img in (('abans', L), ('després', L2)):
    rc = rot_crop(img)
    for xa, xb in ((500, 1100), (250, 750), (900, 1400)):
        p = rc[:, xa:xb].mean(1); pn = p / np.median(p); hpp = pn - ndi.gaussian_filter1d(pn, 25)
        j = np.argmax(np.abs(hpp[280:420])) + 280
        print(f'  {nom:8s} x {xa-800:+5d}..{xb-800:+5d}: passa-alt màx a |y|<70: {100*hpp[j]:+.2f} % a y={y[j]}')
    hp = rc - ndi.gaussian_filter(rc, 20); sd = 1.4826 * np.median(np.abs(hp - np.median(hp)))
    rows.append((np.clip(0.5 + hp / (8 * sd), 0, 1) * 255).astype(np.uint8))
Image.fromarray(np.concatenate(rows, 0)).save(OUT + 'zoom_artefacte_girat_abans_despres.png')
def g_(a_): return (np.clip(a_, 0, 1) ** 0.5 * 255).astype(np.uint8)
yA, yB, xA, xB = 2350, 3300, 2300, 3800
Image.fromarray(np.concatenate([g_(vix[yA:yB, xA:xB]), np.full((yB - yA, 8, 3), 255, np.uint8), g_((vix * K)[yA:yB, xA:xB])], 1)).save(OUT + 'zoom_artefacte_abans_despres.jpg', quality=93)

if os.environ.get('APPLY') != '1':
    raise SystemExit('només anàlisi (APPLY=1 per aplicar)')
Kext = np.ones((H0 + T + B, W0 + Lm + Rm, 3), np.float32); Kext[sl] = K
ICC = open(os.path.join(SP, 'perfil.icc'), 'rb').read()
for f in sorted(glob.glob(OUT + 'APILAT_*.tif')):
    if 'PASSALT' in f:
        continue
    with tifffile.TiffFile(f) as tf:
        desc = tf.pages[0].description or ''
        a_ = tf.asarray()
    if a_.ndim != 3 or a_.shape[2] != 3 or 'grao HDR' in desc:
        print('salto', os.path.basename(f)); continue
    Kx = K if a_.shape[:2] == (H0, W0) else Kext
    if a_.shape[:2] not in ((H0, W0), Kext.shape[:2]):
        print('mida inesperada, salto', f, a_.shape); continue
    b = np.clip(a_.astype(np.float32) * Kx, 0, 65535).round().astype(np.uint16)
    tifffile.imwrite(f, b, photometric='rgb', compression='zlib', extratags=[(34675, 'B', len(ICC), ICC, False)],
                     description=(desc + ' | grao HDR del contorn 10,3 s corregit al sector de Pere (v4b)')[:1000], resolution=(300, 300), metadata=None)
    print('corregit', os.path.basename(f))
print('fet')
