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

OUTDIR = '.'
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
    # intermedis per al PSB de capes (UnintCapes4): Sony encaixada sola, pes de barreja i reserva
    np.save('v4_sony_gD.npy', (g - D).astype(np.float32)); np.save('v4_w.npy', w.astype(np.float32))
    np.save('v4_fbk.npy', fbk); np.save('v4_fbk_in.npy', fbk_in); np.save('v4_valid_px.npy', valid_px); np.save('v4_vref.npy', vref)
    del vsm, fbk_in
    fit = np.clip((g - D) * w[..., None] + fbk * (1 - w[..., None]), 0, 1).astype(np.float32)
    print(nom, 'nivell dels cantons: desplaçaments', [round(float(np.median((g[..., c] - D[..., c])[band] - np.nan_to_num(fallback_old)[..., c][band])), 4) for c in range(3)] if band.sum() > 1000 else 'cap banda')
    fits[nom] = fit
    np.save(f'v4_fit_check.npy', fit)
    print(nom, 'D rang', [(round(float(D[..., c][valid_er].min()), 4), round(float(D[..., c][valid_er].max()), 4)) for c in range(3)])
    # comprovació de les ombres: luminància de la capa als cantons i costats del llenç, i quocient amb la referència
    Lf = fit.mean(-1); Lr = vref.mean(-1)
    for tag, (y_, x_) in (('dalt-esq', (150, 150)), ('dalt-dreta', (150, W0 - 150)), ('baix-esq', (H0 - 150, 150)), ('baix-dreta', (H0 - 150, W0 - 150)),
                          ('dalt', (150, W0 // 2)), ('baix', (H0 - 150, W0 // 2)), ('esq', (H0 // 2, 150)), ('dreta', (H0 // 2, W0 - 150)), ('punta raig', (200, 1840))):
        bx = (slice(T + y_ - 100, T + y_ + 100), slice(Lm + x_ - 100, Lm + x_ + 100))
        print(f'   {tag:11s} L capa = {65535 * np.median(Lf[bx]):7.0f}   L ref = {65535 * np.median(Lr[bx]):7.0f}   capa/ref = {np.median(Lf[bx]) / max(np.median(Lr[bx]), 1e-6):.3f}')


print('intermedis desats')
