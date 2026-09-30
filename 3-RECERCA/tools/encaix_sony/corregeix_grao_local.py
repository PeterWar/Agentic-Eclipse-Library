"""Correcció LOCAL del graó de la fusió HDR (contorn de saturació del 10,3 s) al sector que Pere marca.
Coordenades: d = distància amb signe al contorn exterior de la zona cremada del 10,3 s (fora > 0),
θ = azimut. Al sector θ ∈ [TH0, TH1] (rampes de 12°), perfil per canal P_c(d) = mediana de
L_c / G25(L_c) − 1 en bins de 2 px de d, per −120 < d < 120; L'_c = L_c / (1 + P_c(d)·w(θ)).
Es verifica al lloc de Pere i s'aplica a tots els TIFF d'APILAT (no PASSALT) amb APPLY=1."""
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
sat10 = np.load(os.path.join(SP, 'sat10_canvas.npy'))
TH0, TH1, RAMP = float(os.environ.get('TH0', -160)), float(os.environ.get('TH1', -78)), 12.0
DMAX = 120

fill = ndi.binary_fill_holes(sat10 | (r < 1.05))
fill = ndi.binary_opening(fill, iterations=3)
d = ndi.distance_transform_edt(~fill) - ndi.distance_transform_edt(fill)     # fora > 0
def ss(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
wth = ss((th - TH0) / RAMP) * ss((TH1 - th) / RAMP)
zone = (np.abs(d) < DMAX) & (wth > 0) & (r > 1.15) & (r < 3.0)
print('zona: %d px; contorn dins del sector: r mediana %.2f (%.2f–%.2f)' % (zone.sum(), np.median(r[zone & (np.abs(d) < 1.5)]), r[zone & (np.abs(d) < 1.5)].min(), r[zone & (np.abs(d) < 1.5)].max()))
K = np.ones(vix.shape, np.float32)
bins = np.arange(-DMAX, DMAX + 1, 2)
prof = {}
for c in range(3):
    Lc = vix[..., c]; G = ndi.gaussian_filter(Lc, 25)
    rho = Lc / np.maximum(G, 1e-6) - 1
    P = np.zeros(len(bins) - 1)
    for i in range(len(bins) - 1):
        m = zone & (d >= bins[i]) & (d < bins[i + 1]) & (wth > 0.5)
        if m.sum() > 100:
            P[i] = np.median(rho[m])
    # base lineal entre els extrems i rampes de 8 bins
    k = np.arange(len(P)); base = P[:6].mean() + (P[-6:].mean() - P[:6].mean()) * (k - 2.5) / (len(P) - 6)
    Pn = P - base
    tap = np.ones(len(P)); tap[:8] = np.linspace(0, 1, 8); tap[-8:] = np.linspace(1, 0, 8); Pn *= tap
    Pn = ndi.gaussian_filter1d(Pn, 1.0)
    prof[c] = Pn
    di = np.clip(((d + DMAX) / 2).astype(int), 0, len(P) - 1)
    Kc = 1.0 / (1.0 + Pn[di] * wth)
    K[..., c] = np.where(zone, Kc, 1.0)
    print(f'canal {"RGB"[c]}: perfil P(d) ×100 cada 10 px de d=−80..+60:', ' '.join(f'{100*Pn[(dd+DMAX)//2]:+.2f}' for dd in range(-80, 61, 10)))
K = np.stack([ndi.gaussian_filter(K[..., c], 1.5) for c in range(3)], -1).astype(np.float32)
np.save(os.path.join(SP, 'K_grao_local.npy'), K)
print('K: min %.4f max %.4f' % (K.min(), K.max()))

# verificació al lloc de Pere
Ap_ = np.array([2735.0, 2714.0]); Bp_ = np.array([3440.0, 3006.0])
ang = np.degrees(np.arctan2(Bp_[1] - Ap_[1], Bp_[0] - Ap_[0])); C = 0.5 * (Ap_ + Bp_)
def rot_crop(img, cx, cy, ang_deg, w=1600, h=700):
    yy, xx = np.mgrid[-h // 2:h // 2, -w // 2:w // 2].astype(np.float64); a = np.radians(ang_deg)
    X = cx + xx * np.cos(a) - yy * np.sin(a); Y = cy + xx * np.sin(a) + yy * np.cos(a)
    return ndi.map_coordinates(img, [Y, X], order=1, mode='nearest')
L = vix.mean(-1); L2 = (vix * K).mean(-1)
y = np.arange(-350, 350); rows = []
for nom, img in (('abans', L), ('després', L2)):
    rc = rot_crop(img, C[0], C[1], ang)
    for x0, x1 in ((500, 1100), (200, 700), (900, 1400)):
        p = rc[:, x0:x1].mean(1); pn = p / np.median(p); hpp = pn - ndi.gaussian_filter1d(pn, 25)
        j = np.argmax(np.abs(hpp[280:420])) + 280
        print(f'  {nom:8s} x {x0-800:+5d}..{x1-800:+5d}: passa-alt màx a |y|<70: {100*hpp[j]:+.2f} % a y={y[j]}')
    hp = rc - ndi.gaussian_filter(rc, 20); sd = 1.4826 * np.median(np.abs(hp - np.median(hp)))
    rows.append((np.clip(0.5 + hp / (8 * sd), 0, 1) * 255).astype(np.uint8))
Image.fromarray(np.concatenate(rows, 0)).save(OUT + 'zoom_artefacte_girat_abans_despres.png')
# retall tal qual (gamma) abans/després
def g_(a): return (np.clip(a, 0, 1) ** 0.5 * 255).astype(np.uint8)
y0, y1, x0, x1 = 2350, 3300, 2300, 3800
Image.fromarray(np.concatenate([g_(vix[y0:y1, x0:x1]), np.full((y1 - y0, 8, 3), 255, np.uint8), g_((vix * K)[y0:y1, x0:x1])], 1)).save(OUT + 'zoom_artefacte_abans_despres.jpg', quality=93)

if os.environ.get('APPLY') != '1':
    raise SystemExit('només anàlisi (APPLY=1 per aplicar)')
Kext = np.ones((H0 + T + B, W0 + Lm + Rm, 3), np.float32); Kext[sl] = K
ICC = open(os.path.join(SP, 'perfil.icc'), 'rb').read()
for f in sorted(glob.glob(OUT + 'APILAT_*.tif')):
    if 'PASSALT' in f:
        continue
    with tifffile.TiffFile(f) as tf:
        desc = tf.pages[0].description or ''
        a = tf.asarray()
    if a.ndim != 3 or a.shape[2] != 3 or 'grao HDR' in desc:
        print('salto', os.path.basename(f)); continue
    Kx = K if a.shape[:2] == (H0, W0) else Kext
    if a.shape[:2] not in ((H0, W0), Kext.shape[:2]):
        print('mida inesperada, salto', f, a.shape); continue
    b = np.clip(a.astype(np.float32) * Kx, 0, 65535).round().astype(np.uint16)
    tifffile.imwrite(f, b, photometric='rgb', compression='zlib', extratags=[(34675, 'B', len(ICC), ICC, False)],
                     description=(desc + ' | grao HDR del contorn 10,3 s corregit al sector de Pere (v4b)')[:1000], resolution=(300, 300), metadata=None)
    print('corregit', os.path.basename(f))
print('fet')
