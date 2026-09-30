"""Pipeline complet sobre el domini ESTÈS (llenç de Pere + marges on la Sony encara té dades):
  marges: dalt 550, baix 250, esquerra 600, dreta 300  → 5353 × 7648.

1. Sony estesa (RGB) → estrelles arrodonides (arregla_estrelles.py, ja fet a part).
2. Encaix: LUT per canal (quantils, zona vàlida dins el llenç), residu D per convolució normalitzada
   (σ 80 px) estimat només dins el llenç i a més de VORA px de les seves vores; extrapolat cap enfora.
   Dins la zona cremada, la Vixen. Dues variants: VORA=0 (segueix la Vixen fins a les vores) i VORA=300 (vores netes).
3. Detall exterior: bandes angulars sobre la luminància ESTESA i detrendada radialment (així el DoG no
   veu ni el perfil radial ni les vores del llenç), coring, component d'anell restada, rampa radial.
4. Lliurables retallats al llenç 6748×4553 i, a part, els estesos 7648×5353.
"""
import os, sys, json
import numpy as np
from scipy import ndimage as ndi
import tifffile
from PIL import Image

OUTDIR = os.path.expanduser('~/Downloads/Encaixada_2026-08-18')
os.makedirs(OUTDIR, exist_ok=True)
ICC = open('perfil.icc', 'rb').read()
SCALE = 2.1495
T, B, Lm, Rm = 550, 250, 600, 300            # marges
H0, W0 = 4553, 6748
H, W = H0 + T + B, W0 + Lm + Rm
SX, SY = 3563.891 - 143 + Lm, 2274.66 - 87 + T
RSOL = 446.15
sl = (slice(T, T + H0), slice(Lm, Lm + W0))     # el llenç dins l'estès

sony = np.load('sony_ext_estrelles.npy')       # H×W×3
vix0 = np.load('vixen_canvas_rgb.npy')
vix = np.zeros((H, W, 3), np.float32); vix[sl] = vix0
inside = np.zeros((H, W), bool); inside[sl] = True
yy, xx = np.mgrid[0:H, 0:W]
r = (np.hypot(xx - SX, yy - SY) / RSOL).astype(np.float32)
th = np.degrees(np.arctan2(-(yy - SY), xx - SX)).astype(np.float32)
dist_in = np.minimum(np.minimum(yy - T, T + H0 - 1 - yy), np.minimum(xx - Lm, Lm + W0 - 1 - xx))  # distància a la vora del llenç (negativa a fora)

# --- validesa de la Sony ------------------------------------------------------------
valid_px = (sony < 0.70).all(-1) & (r > 3.0)
valid_px = ndi.binary_dilation(ndi.binary_erosion(valid_px, iterations=2, border_value=1), iterations=2)  # obertura sense tocar la vora del domini
valid_er = ndi.binary_erosion(valid_px, iterations=50, border_value=1)
dist = ndi.distance_transform_edt(np.pad(valid_er, 1, constant_values=True))[1:-1, 1:-1]
t = np.clip(dist / 120.0, 0, 1); w = (t * t * (3 - 2 * t)).astype(np.float32)
# fora del llenç no hi ha Vixen: w hi ha de ser 1 (la Sony sola). Dins la zona cremada (w<1) sempre som dins el llenç.
assert (w[~inside] > 0.999).all(), 'zona cremada fora del llenç?'
print('vàlid: fracció', valid_px.mean(), ' r mínim (erosionat)', r[valid_er].min())

# --- LUT ---------------------------------------------------------------------------
O = valid_er & inside & (r >= 3.6) & (dist_in >= 30)
qs = np.linspace(0, 1, 4001)
lut = []
for c in range(3):
    lut.append((np.quantile(sony[..., c][O], qs), np.quantile(vix[..., c][O], qs)))
g = np.empty_like(sony)
for c in range(3):
    xs, ys = lut[c]
    g[..., c] = np.interp(sony[..., c], xs, ys)
    over = sony[..., c] > xs[-1]
    slope = (ys[-1] - ys[-50]) / max(xs[-1] - xs[-50], 1e-6)
    g[..., c][over] = ys[-1] + slope * (sony[..., c][over] - xs[-1])
np.savez('lut_ext.npz', **{f'{"RGB"[c]}_s': lut[c][0] for c in range(3)}, **{f'{"RGB"[c]}_v': lut[c][1] for c in range(3)})

def residu(vora):
    m = (valid_er & inside & (dist_in >= vora)).astype(np.float32)
    den = ndi.gaussian_filter(m, 80.0, mode='constant', cval=0.0)
    D = np.empty_like(g)
    for c in range(3):
        num = ndi.gaussian_filter((g[..., c] - vix[..., c]) * m, 80.0, mode='constant', cval=0.0)
        Dc = np.where(den > 0.05, num / np.maximum(den, 1e-6), np.nan)
        idx = ndi.distance_transform_edt(np.isnan(Dc), return_distances=False, return_indices=True)
        D[..., c] = Dc[tuple(idx)]
    return D

fits = {}
for nom, vora in (('SEGUEIX_VIXEN', 0), ('VORESNETES', 300)):
    D = residu(vora)
    fit = np.clip((g - D) * w[..., None] + vix * (1 - w[..., None]), 0, 1).astype(np.float32)
    fits[nom] = fit
    np.save(f'fit_ext_{nom}.npy', fit)
    print(nom, 'D rang', [(round(float(D[..., c][valid_er].min()), 4), round(float(D[..., c][valid_er].max()), 4)) for c in range(3)])

# --- detall exterior sobre la variant VORESNETES, domini estès -----------------------------
fit = fits['VORESNETES']
L = fit.mean(-1)
# detrend radial: mitjana per anell de 0,02 R☉ (sobre tot el domini estès), suavitzada
rb = np.clip(((r - 0.9) / 0.02).astype(int), 0, 599)
cnt = np.bincount(rb.ravel(), minlength=600).astype(float)
prof = ndi.gaussian_filter1d(np.where(cnt > 0, np.bincount(rb.ravel(), weights=L.ravel(), minlength=600) / np.maximum(cnt, 1), 0), 2, mode='nearest')
Ld = L - prof[rb]
BANDS = [(12, 35), (35, 100), (100, 280), (280, 600)]
PRESETS = {'SUAU': [1.5, 3.0, 2.5, 0.0], 'FORT': [3.0, 6.0, 5.0, 2.0]}
R_IN, R_OUT = 3.2, 4.4
tt = np.clip((r - R_IN) / (R_OUT - R_IN), 0, 1); ramp = tt * tt * (3 - 2 * tt)
stars = json.load(open('sony_ext_estrelles_estrelles.json'))['stars']
star_m = np.ones((H, W), np.float32)
sy, sx = np.mgrid[-16:17, -16:17]
for s in stars:
    yi, xi = int(round(s['y'])), int(round(s['x']))
    if 16 <= yi < H - 16 and 16 <= xi < W - 16:
        star_m[yi - 16:yi + 17, xi - 16:xi + 17] *= np.clip((np.hypot(sy, sx) - 6) / 8, 0, 1)
sky = (r > 5.5) & (w > 0.99)
# vora del domini estès: rampa de 120 px (el DoG amb reflexió hi és menys net)
dist_ext = np.minimum(np.minimum(yy, H - 1 - yy), np.minimum(xx, W - 1 - xx)).astype(np.float32)
te = np.clip(dist_ext / 120.0, 0, 1); border_ramp = te * te * (3 - 2 * te)
bands_c = []
info = []
for (a, b) in BANDS:
    band = ndi.gaussian_filter(Ld, a) - ndi.gaussian_filter(Ld, b)
    sig = 1.4826 * np.median(np.abs(band[sky] - np.median(band[sky])))
    k = 1 - np.exp(-(band / (1.5 * sig)) ** 2)
    bands_c.append(band * k)
    info.append(dict(banda_px=(a, b), banda_arcmin=(round(a * SCALE / 60, 2), round(b * SCALE / 60, 2)), sigma_soroll=float(sig),
                     std_4_5Rsol=float(band[(r > 4) & (r < 5) & (w > 0.99)].std())))
print(json.dumps(info))

def save16(name, arr, desc):
    a16 = np.round(np.clip(arr, 0, 1) * 65535).astype(np.uint16)
    tifffile.imwrite(os.path.join(OUTDIR, name), a16, photometric='rgb', compression='zlib',
                     extratags=[(34675, 'B', len(ICC), ICC, False)], description=desc, resolution=(300, 300), metadata=None)
    print('desat', name, a16.shape)

def to8(a, s=4): return (np.clip(a[::s, ::s], 0, 1) * 255).astype(np.uint8)

wgt = (border_ramp > 0.99).astype(np.float64)   # el detall s'aplica a tot arreu (també on la capa és Vixen): la component d'anell es treu sobre tots els píxels
cntw = np.bincount(rb.ravel(), weights=wgt.ravel(), minlength=600)
Lmean = fit.mean(-1)
results = {}
for preset, gains in PRESETS.items():
    D = sum(G * bc for G, bc in zip(gains, bands_c)).astype(np.float32) * star_m
    prof_D = ndi.gaussian_filter1d(np.where(cntw > 100, np.bincount(rb.ravel(), weights=(D * wgt).ravel(), minlength=600) / np.maximum(cntw, 1), 0.0), 3, mode='nearest')
    D = np.clip((D - prof_D[rb]) * border_ramp * ramp, -0.06, 0.06).astype(np.float32)
    # test d'anell (dins el llenç, zona plena)
    for a, b in ((4.6, 5.4), (5.5, 7.0)):
        ann = (r >= a) & (r < b) & (w > 0.99) & (border_ramp > 0.99) & inside
        means = []
        for t0 in range(-180, 180, 15):
            sel = ann & (th >= t0) & (th < t0 + 15)
            if sel.sum() > 2000: means.append(D[sel].mean() / Lmean[sel].mean())
        print(f"{preset}: anell {a}–{b}: component d'anell {100*D[ann].mean()/Lmean[ann].mean():+.3f} % (llindar 0,15); sectors 15°: {100*min(means):+.2f} … {100*max(means):+.2f} %")
    # component d'anell del detall: mitjana de D/L per anells de 0,05 R☉ COMPLETS dins el domini estès (r < 5,8), tots els píxels
    mx, mx_in = 0, 0
    for a in np.arange(3.0, 5.8, 0.05):
        ann = (r >= a) & (r < a + 0.05) & (border_ramp > 0.99)
        if ann.sum() > 5000: mx = max(mx, abs(D[ann].mean() / Lmean[ann].mean()))
        ann2 = ann & inside
        if ann2.sum() > 5000: mx_in = max(mx_in, abs(D[ann2].mean() / Lmean[ann2].mean()))
    print(f"{preset}: component d'anell del detall, màxim sobre anells de 0,05 R☉ (3,0–5,8): {100*mx:.3f} % (domini estès complet), {100*mx_in:.3f} % (només dins el llenç, on l'anell és incomplet a partir de 4,9)")
    # vores del llenç: mediana de D per files de dalt del llenç
    print(f"{preset}: mediana de D a les files 0/100/200/400 del llenç:", [round(float(np.median(D[T + y, Lm + 1000:Lm + 5700])), 5) for y in (0, 100, 200, 400)])
    enh = np.clip(fit + D[..., None], 0, 1)
    passalt = np.clip(0.5 + D / 2, 0, 1)
    results[preset] = (D, enh, passalt)
    np.save(f'D_ext_{preset}.npy', D)
    save16(f'Capa_Sony_encaixada_VORESNETES_REALCADA_{preset}_6748x4553.tif', enh[sl], f'Encaixada (vores netes) + detall exterior {preset}: bandes {BANDS} px, guanys {gains}, rampa {R_IN}-{R_OUT} Rsol')
    save16(f'Detall_exterior_PASSALT_{preset}_6748x4553.tif', np.repeat(passalt[sl][..., None], 3, -1), f'Gris 50% + D/2 ({preset}): en Linear Light al 100% afegeix D; opacitat = dosi')
    save16(f'ESTESA_7648x5353_encaixada_VORESNETES_REALCADA_{preset}.tif', enh, f'Domini estes (marges dalt 550, baix 250, esq 600, dreta 300 px): {preset}')
    Image.fromarray(to8(enh[sl])).save(os.path.join(OUTDIR, f'despres_encaixada_realcada_{preset}.jpg'), quality=92)
    Image.fromarray(to8(enh)).save(os.path.join(OUTDIR, f'ESTESA_despres_encaixada_realcada_{preset}.jpg'), quality=92)

save16('Capa_Sony_encaixada_6748x4553.tif', fits['SEGUEIX_VIXEN'][sl], 'Sony 300 mm encaixada a la Vixen (LUT per canal + residu de baixa frequencia restat, tambe a les vores); Vixen dins de la zona cremada; estrelles arrodonides')
save16('Capa_Sony_encaixada_VORESNETES_6748x4553.tif', fits['VORESNETES'][sl], 'Com l\'anterior, pero a les vores del llenc la Sony continua el seu cel natural en lloc de copiar l\'enfosquiment de vora de la capa Vixen')
save16('ESTESA_7648x5353_encaixada_VORESNETES.tif', fits['VORESNETES'], 'Domini estes (marges dalt 550, baix 250, esq 600, dreta 300 px), sense detall')
Image.fromarray(to8(fits['VORESNETES'][sl])).save(os.path.join(OUTDIR, 'despres_encaixada.jpg'), quality=92)
comp_before = np.load('composite_u16.npy').astype(np.float32) / 65535.
Image.fromarray(to8(comp_before)).save(os.path.join(OUTDIR, 'abans_compost_de_Pere.jpg'), quality=92)
enh_f = results['FORT'][1][sl]
Image.fromarray(np.concatenate([to8(comp_before), np.full((to8(comp_before).shape[0], 12, 3), 255, np.uint8), to8(enh_f)], 1)).save(os.path.join(OUTDIR, 'comparacio_abans_despres_FORT.jpg'), quality=92)
y0, y1, x0, x1 = 2200, 4200, 200, 2600
crop = np.concatenate([np.clip(comp_before[y0:y1, x0:x1], 0, 1), np.ones((y1 - y0, 10, 3)), np.clip(enh_f[y0:y1, x0:x1], 0, 1)], 1)
Image.fromarray((crop[::2, ::2] * 255).astype(np.uint8)).save(os.path.join(OUTDIR, 'retall_exterior_abans_despres_FORT.jpg'), quality=92)
np.save('enh_ext_FORT.npy', results['FORT'][1]); np.save('enh_ext_SUAU.npy', results['SUAU'][1])
print('fet')
