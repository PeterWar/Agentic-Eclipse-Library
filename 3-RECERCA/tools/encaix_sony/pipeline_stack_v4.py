"""Pipeline v4 (quarta ronda, 18-08 tarda) sobre el domini ESTÈS (llenç de Pere + marges):
  marges: dalt 550, baix 250, esquerra 600, dreta 300  → 5353 × 7648.

Canvis respecte de pipeline_stack.py (v3):
1. L'apilat Sony va APLANAT amb el flat real del FE 300 mm f/2,8 GM a f/2,8 (flats de cel de l'A7III
   d'abril de 2025, simetritzats i portats a la reixa de l'A7RIIIA: flat_sony300.py, flat_al_llenc.py).
   El vinyetatge del 300 mm és de −1,5 EV als cantons del sensor i de 0,60–0,65 als cantons del llenç;
   comprovat contra l'apilat lineal de 10,3 s de la Vixen (HDR4): el quocient queda a ±3 % de 4 a 8,8 R☉.
2. La referència per a la LUT i el residu D ja no és la capa Vixen de Pere a pèl: la seva capa és una
   corba de to global de la Vixen lineal a ±1 % a tot el camp llunyà, EXCEPTE una rampa d'enfosquiment
   de ~700 px a dalt (×0,61 a la fila 0) i a la dreta (×0,54 a l'última columna). La referència és la
   capa de Pere on és de fiar i LUT(Vixen lineal) («vix_ref», diag_capa_vixen_pere.py) dins de les dues
   bandes, amb una rampa de 200 px. Així el residu D s'estima FINS A LES VORES (VORA = 0) i la Sony ja
   no copia ni el vinyetatge propi ni l'enfosquiment de la capa Vixen.
3. El corredor del raig i el tros sense apilat de dins del llenç (108×70 px al cantó de baix a la dreta)
   fan servir la mateixa referència; fora del llenç, la capa anterior anivellada, com abans.
4. Detall SUAU/FORT (DoG angular) i PASSALT com a la v1 (Pere ha triat REALCADA_SUAU).
"""
import os, sys, json
import numpy as np
from scipy import ndimage as ndi
import tifffile
from PIL import Image

OUTDIR = os.path.expanduser('~/Downloads/Encaixada_2026-08-18/APILAT')
os.makedirs(OUTDIR, exist_ok=True)
ICC = open('perfil.icc', 'rb').read()
SCALE = 2.1495
T, B, Lm, Rm = 550, 250, 600, 300            # marges
H0, W0 = 4553, 6748
H, W = H0 + T + B, W0 + Lm + Rm
SX, SY = 3563.891 - 143 + Lm, 2274.66 - 87 + T
RSOL = 446.15
sl = (slice(T, T + H0), slice(Lm, Lm + W0))     # el llenç dins l'estès

sony = np.load('sony_stack_ext_rgb_FLAT.npy')   # H×W×3, ADU/s (lineal) APLANAT amb el flat del 300 mm, NaN sense dada
cov = np.load('sony_stack_ext_cov.npy') & np.isfinite(sony).all(-1)
sony = np.nan_to_num(sony, nan=0.0).astype(np.float32)
SUFX = '_APILAT'
vix0 = np.load('vixen_canvas_rgb.npy')          # capa Vixen de Pere (0–1)
vref0 = np.load('vix_ref_rgb.npy')              # LUT per canal (Vixen lineal 10,3 s → capa de Pere): la mateixa capa sense l'enfosquiment de dalt/dreta
vix = np.zeros((H, W, 3), np.float32); vix[sl] = vix0
inside = np.zeros((H, W), bool); inside[sl] = True
yy, xx = np.mgrid[0:H, 0:W]
r = (np.hypot(xx - SX, yy - SY) / RSOL).astype(np.float32)
th = np.degrees(np.arctan2(-(yy - SY), xx - SX)).astype(np.float32)
dist_in = np.minimum(np.minimum(yy - T, T + H0 - 1 - yy), np.minimum(xx - Lm, Lm + W0 - 1 - xx))  # distància a la vora del llenç (negativa a fora)
# referència Vixen: capa de Pere on és de fiar; vix_ref dins de la banda de dalt (y < 500 del llenç) i de la dreta
# (x > W0−1−550), amb rampes de 200 px (l'enfosquiment de Pere hi és de ×0,54–0,61 a la vora i < 2 % a partir de ~650 px)
def ss(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)
wt0 = ss((yy[sl] - T - 500) / 200.0) * ss(((Lm + W0 - 1 - xx[sl]) - 550) / 200.0)
vref = np.zeros((H, W, 3), np.float32)
vref[sl] = wt0[..., None] * vix0 + (1 - wt0[..., None]) * vref0
del vref0
print('referència Vixen: fracció del llenç on és la capa de Pere al 100 %%: %.3f; on és vix_ref al 100 %%: %.3f' % ((wt0 > 0.999).mean(), (wt0 < 0.001).mean()))

# --- validesa de la Sony ------------------------------------------------------------
valid_px = cov & (r > 3.0)
valid_px = ndi.binary_dilation(ndi.binary_erosion(valid_px, iterations=2, border_value=1), iterations=2)  # obertura sense tocar la vora del domini
valid_er = ndi.binary_erosion(valid_px, iterations=50, border_value=1)
dist = ndi.distance_transform_edt(np.pad(valid_er, 1, constant_values=True))[1:-1, 1:-1]
t = np.clip(dist / 120.0, 0, 1); w = (t * t * (3 - 2 * t)).astype(np.float32)
# corredor del raig recte de dalt a l'esquerra: als 8 s de la Sony el raig porta un sotabanc fosc (el
# filtratge espacial del RAW) i el seu perfil no coincideix amb el de la Vixen → a la costura fa un
# colze. Dins d'un corredor de ±60 px (ploma 40) al voltant del raig, entre 2,8 i 6 R☉, la capa és la Vixen.
RAIG_TH = 129.6   # angle (θ, graus, y cap amunt) del raig des del Sol (mesurat a la Vixen i a l'apilat)
ang = np.radians(RAIG_TH)
ux, uy = np.cos(ang), -np.sin(ang)          # direcció del raig al llenç (y cap avall)
px_, py_ = xx - SX, yy - SY
along = px_ * ux + py_ * uy
perp = np.abs(-px_ * uy + py_ * ux)
corr = np.clip((100.0 - perp) / 40.0, 0, 1) * (along > 0) * np.clip((6.0 - r) / 0.5, 0, 1) * np.clip((r - 2.8) / 0.3, 0, 1)
corr = corr * corr * (3 - 2 * corr)
w = (w * (1 - corr) ).astype(np.float32)
w[~inside] = np.maximum(w[~inside], 1.0 * (valid_er[~inside]))   # fora del llenç no hi ha Vixen: el corredor no s'hi aplica
print('corredor del raig: píxels amb w reduït', int((corr > 0.01).sum()))
# on l'apilat no arriba (dos cantons del camp Sony girat) hi va la capa anterior encaixada (mateixa base Vixen);
# dins del llenç, la Vixen. `fallback` = Vixen dins, capa anterior (VORESNETES) fora.
fallback_old = np.load('fit_ext_VORESNETES.npy')
fallback = np.where(inside[..., None], vix, fallback_old).astype(np.float32)
print('sense cobertura de l\'apilat: fora del llenç %.2f %%, dins %.2f %%' % (100 * (w[~inside] < 0.999).mean(), 100 * (w[inside] < 0.999).mean()))
print('vàlid: fracció', valid_px.mean(), ' r mínim (erosionat)', r[valid_er].min())

# --- LUT ---------------------------------------------------------------------------
O = valid_er & inside & (r >= 3.05) & (dist_in >= 30)
qs = np.linspace(0, 1, 4001)
lut = []
for c in range(3):
    lut.append((np.quantile(sony[..., c][O], qs), np.quantile(vref[..., c][O], qs)))
g = np.empty_like(sony)
for c in range(3):
    xs, ys = lut[c]
    g[..., c] = np.interp(sony[..., c], xs, ys)
    over = sony[..., c] > xs[-1]
    slope = (ys[-1] - ys[-50]) / max(xs[-1] - xs[-50], 1e-6)
    g[..., c][over] = ys[-1] + slope * (sony[..., c][over] - xs[-1])
np.savez('lut_ext_apilat_v4.npz', **{f'{"RGB"[c]}_s': lut[c][0] for c in range(3)}, **{f'{"RGB"[c]}_v': lut[c][1] for c in range(3)})

def residu(vora):
    m = (valid_er & inside & (dist_in >= vora)).astype(np.float32)
    den = ndi.gaussian_filter(m, 80.0, mode='constant', cval=0.0)
    D = np.empty_like(g)
    for c in range(3):
        num = ndi.gaussian_filter((g[..., c] - vref[..., c]) * m, 80.0, mode='constant', cval=0.0)
        Dc = np.where(den > 0.05, num / np.maximum(den, 1e-6), np.nan)
        idx = ndi.distance_transform_edt(np.isnan(Dc), return_distances=False, return_indices=True)
        D[..., c] = Dc[tuple(idx)]
    return D

fits = {}
for nom, vora in (('VORESNETES', 0),):
    D = residu(vora)
    print(nom, 'D (residu LUT(Sony aplanada) − referència, σ 80) a les vores del llenç, verd ×1000:')
    print('   files 0/50/100/200/400/800:', [round(float(np.median(D[T + y, Lm + 1000:Lm + 5700, 1])) * 1000, 2) for y in (0, 50, 100, 200, 400, 800)])
    print('   columnes dreta 0/50/100/200/400/800:', [round(float(np.median(D[T + 800:T + 3800, Lm + W0 - 1 - x, 1])) * 1000, 2) for x in (0, 50, 100, 200, 400, 800)])
    print('   columnes esq 0/50/100/200/400/800:', [round(float(np.median(D[T + 800:T + 3800, Lm + x, 1])) * 1000, 2) for x in (0, 50, 100, 200, 400, 800)])
    print('   files baix 0/50/100/200/400/800:', [round(float(np.median(D[T + H0 - 1 - y, Lm + 1000:Lm + 5700, 1])) * 1000, 2) for y in (0, 50, 100, 200, 400, 800)])
    # zona sense apilat fora del llenç: capa anterior (vores netes) anivellada per canal a la banda de 200 px
    # que voreja la zona; dins del llenç, la referència Vixen (r > 3,6: només el tros de 108×70 px de baix a la
    # dreta) i la capa de Pere dins de la corona (r ≤ 3,6)
    Fz = (~valid_er) & (r > 3.6)
    band = ndi.binary_dilation(Fz, iterations=200) & valid_er & (r > 3.6)
    fb = np.nan_to_num(fallback_old, nan=0.0).copy()
    for c in range(3):
        if band.sum() > 1000:
            off_c = float(np.median((g[..., c] - D[..., c])[band] - fb[..., c][band]))
            fb[..., c] += off_c
    fbk_in = np.where((r <= 3.6)[..., None], vix, vref).astype(np.float32)
    fbk = np.where(inside[..., None], fbk_in, fb).astype(np.float32)
    # dins del corredor del raig, la referència suavitzada (σ 1,5); a la banda de dalt és vix_ref, no la capa enfosquida
    vsm = np.stack([ndi.gaussian_filter(fbk_in[..., c], 1.5) for c in range(3)], -1)
    cmask = ((corr > 0.01) & inside)[..., None]
    fbk = np.where(cmask, vsm, fbk).astype(np.float32)
    del vsm, fbk_in
    fit = np.clip((g - D) * w[..., None] + fbk * (1 - w[..., None]), 0, 1).astype(np.float32)
    print(nom, 'nivell dels cantons: desplaçaments', [round(float(np.median((g[..., c] - D[..., c])[band] - np.nan_to_num(fallback_old)[..., c][band])), 4) for c in range(3)] if band.sum() > 1000 else 'cap banda')
    fits[nom] = fit
    np.save(f'fit_ext_{nom}{SUFX}.npy', fit)
    print(nom, 'D rang', [(round(float(D[..., c][valid_er].min()), 4), round(float(D[..., c][valid_er].max()), 4)) for c in range(3)])
    # comprovació de les ombres: luminància de la capa als cantons i costats del llenç, i quocient amb la referència
    Lf = fit.mean(-1); Lr = vref.mean(-1)
    for tag, (y_, x_) in (('dalt-esq', (150, 150)), ('dalt-dreta', (150, W0 - 150)), ('baix-esq', (H0 - 150, 150)), ('baix-dreta', (H0 - 150, W0 - 150)),
                          ('dalt', (150, W0 // 2)), ('baix', (H0 - 150, W0 // 2)), ('esq', (H0 // 2, 150)), ('dreta', (H0 // 2, W0 - 150)), ('punta raig', (200, 1840))):
        bx = (slice(T + y_ - 100, T + y_ + 100), slice(Lm + x_ - 100, Lm + x_ + 100))
        print(f'   {tag:11s} L capa = {65535 * np.median(Lf[bx]):7.0f}   L ref = {65535 * np.median(Lr[bx]):7.0f}   capa/ref = {np.median(Lf[bx]) / max(np.median(Lr[bx]), 1e-6):.3f}')

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
# estrelles de l'apilat (rodones): pics compactes a la luminància, per emmascarar-les del detall
Lg = g.mean(-1)
hpg = Lg - ndi.gaussian_filter(Lg, 8); smg = ndi.gaussian_filter(hpg, 1.0)
okz = valid_er
nz = 1.4826 * np.median(np.abs(smg[valid_er] - np.median(smg[valid_er])))
pkz = (smg == ndi.maximum_filter(smg, 9)) & (smg > 10 * nz) & valid_er
sy_, sx_ = np.nonzero(pkz)
# compacitat: el pic ha de ser > 3× la mitjana de l'anell 4–6 px (una estrella, no una cresta ni textura)
yy5, xx5 = np.mgrid[-6:7, -6:7]; ring5 = (np.hypot(yy5, xx5) >= 4) & (np.hypot(yy5, xx5) <= 6)
stars = []
for y_, x_ in zip(sy_, sx_):
    if 6 <= y_ < H - 6 and 6 <= x_ < W - 6:
        cut = smg[y_ - 6:y_ + 7, x_ - 6:x_ + 7]
        if cut[6, 6] > 3 * max(cut[ring5].mean(), 1e-9):
            stars.append(dict(y=float(y_), x=float(x_)))
print('estrelles detectades a l\'apilat per a la màscara del detall:', len(stars))
star_m = np.ones((H, W), np.float32)
sy, sx = np.mgrid[-16:17, -16:17]
for s_ in stars:
    yi, xi = int(round(s_['y'])), int(round(s_['x']))
    if 16 <= yi < H - 16 and 16 <= xi < W - 16:
        star_m[yi - 16:yi + 17, xi - 16:xi + 17] *= np.clip((np.hypot(sy, sx) - 5) / 7, 0, 1)
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
    np.save(f'D_ext_{preset}{SUFX}.npy', D)
    save16(f'APILAT_Capa_Sony_encaixada_VORESNETES_REALCADA_{preset}_6748x4553.tif', enh[sl], f'Encaixada (vores netes) + detall exterior {preset}: bandes {BANDS} px, guanys {gains}, rampa {R_IN}-{R_OUT} Rsol')
    save16(f'APILAT_Detall_exterior_PASSALT_{preset}_6748x4553.tif', np.repeat(passalt[sl][..., None], 3, -1), f'Gris 50% + D/2 ({preset}): en Linear Light al 100% afegeix D; opacitat = dosi')
    save16(f'APILAT_ESTESA_7648x5353_encaixada_VORESNETES_REALCADA_{preset}.tif', enh, f'Domini estes (marges dalt 550, baix 250, esq 600, dreta 300 px): {preset}')
    Image.fromarray(to8(enh[sl])).save(os.path.join(OUTDIR, f'APILAT_despres_encaixada_realcada_{preset}.jpg'), quality=92)
    Image.fromarray(to8(enh)).save(os.path.join(OUTDIR, f'APILAT_ESTESA_despres_encaixada_realcada_{preset}.jpg'), quality=92)

save16('APILAT_Capa_Sony_encaixada_VORESNETES_6748x4553.tif', fits['VORESNETES'][sl], 'v4: apilat Sony >=1 s APLANAT (flat real del 300 mm f/2,8), LUT per canal + residu sigma 80 fins a les vores contra la Vixen sense l\'enfosquiment de dalt/dreta de la capa de Pere; Vixen dins de la corona (r<=3,6) i al corredor del raig; sense detall')
save16('APILAT_ESTESA_7648x5353_encaixada_VORESNETES.tif', fits['VORESNETES'], 'v4, domini estes (marges dalt 550, baix 250, esq 600, dreta 300 px), sense detall')
Image.fromarray(to8(fits['VORESNETES'][sl])).save(os.path.join(OUTDIR, 'APILAT_despres_encaixada.jpg'), quality=92)
np.save('enh_ext_FORT_APILAT.npy', results['FORT'][1]); np.save('enh_ext_SUAU_APILAT.npy', results['SUAU'][1])
# comprovació de les ombres sobre el REALCAT SUAU: mateixos punts, capa/referència
enh_s = results['SUAU'][1]; Ls = enh_s.mean(-1); Lr = vref.mean(-1)
for tag, (y_, x_) in (('dalt-esq', (150, 150)), ('dalt-dreta', (150, W0 - 150)), ('baix-esq', (H0 - 150, 150)), ('baix-dreta', (H0 - 150, W0 - 150)),
                      ('dalt', (150, W0 // 2)), ('baix', (H0 - 150, W0 // 2)), ('esq', (H0 // 2, 150)), ('dreta', (H0 // 2, W0 - 150)), ('punta raig', (200, 1840))):
    bx = (slice(T + y_ - 100, T + y_ + 100), slice(Lm + x_ - 100, Lm + x_ + 100))
    print(f'   SUAU {tag:11s} L = {65535 * np.median(Ls[bx]):7.0f}   capa/ref = {np.median(Ls[bx]) / max(np.median(Lr[bx]), 1e-6):.3f}')
print('fet')
