"""Encaixa la capa Sony (300 mm) a la capa Vixen del llenç de Pere.

1. Validesa de la Sony: només on cap canal és a prop de la saturació.
2. LUT monòtona per canal (aparellament de quantils Sony→Vixen a la zona vàlida).
3. Residu de baixa freqüència en polars (anell fi × sector ample), suavitzat, i restat:
   mata qualsevol gradient concèntric i qualsevol vinyetatge/gradient de cel de la Sony,
   i conserva els plomalls (estrets en θ, llargs en r).
4. Dins la zona cremada, la capa passa a ser la Vixen mateixa (ploma suau), o sigui que
   la màscara de Pere ja no pot filtrar res de cremat.

Sortides: sony_fit_rgb.npy (0–1), pes_valid.npy, i diagnòstics PNG.
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SRC = sys.argv[1] if len(sys.argv) > 1 else 'sony_canvas_rgb.npy'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'sony_fit_rgb.npy'
H, W = 4553, 6748
sony = np.load(SRC)
vix = np.load('vixen_canvas_rgb.npy')
r = np.load('r_rsol.npy'); th = np.load('theta_deg.npy')

# 1. validesa -------------------------------------------------------------
SAT_LIM = 0.70
valid_px = (sony < SAT_LIM).all(-1) & (r > 3.0)
# treu forats petits i erosiona 40 px perquè no entri el rim taronja; després ploma
valid_px = ndi.binary_opening(valid_px, iterations=2)
valid_er = ndi.binary_erosion(valid_px, iterations=50, border_value=1)
# pes: 0 a la vora de valid_er i 1 a 120 px cap a dins (smoothstep sobre la distància), sense sortir mai de valid_er
dist = ndi.distance_transform_edt(np.pad(valid_er, 1, constant_values=True))[1:-1, 1:-1]
t = np.clip(dist / 120.0, 0, 1)
w = (t * t * (3 - 2 * t)).astype(np.float32)
np.save('pes_valid.npy', w.astype(np.float32)) if len(sys.argv) <= 4 else None
print('zona vàlida: fracció', valid_px.mean(), ' r mínim vàlid', r[valid_er].min())

# zona d'ajust de la LUT: vàlida i eròsionada, r >= 3.6, sense els 30 px de vora del llenç
O = valid_er & (r >= 3.6)
O[:30, :] = False; O[-30:, :] = False; O[:, :30] = False; O[:, -30:] = False
print('píxels a O:', O.sum())

# 2. LUT per canal --------------------------------------------------------
NQ = 4001
qs = np.linspace(0, 1, NQ)
lut = []
for c in range(3):
    s = sony[..., c][O]; v = vix[..., c][O]
    qs_s = np.quantile(s, qs); qs_v = np.quantile(v, qs)
    # monòtona per construcció; suavitza una mica els extrems (soroll a les cues)
    lut.append((qs_s, qs_v))
    print('RGB'[c], 'sony rang a O', qs_s[0], qs_s[-1], ' → vixen', qs_v[0], qs_v[-1])
np.savez('lut_sony_vixen.npz', **{f'{"RGB"[c]}_s': lut[c][0] for c in range(3)}, **{f'{"RGB"[c]}_v': lut[c][1] for c in range(3)})

g = np.empty_like(sony)
for c in range(3):
    xs, ys = lut[c]
    # extrapolació lineal per sobre del rang (píxels cremats: se substitueixen igualment)
    g[..., c] = np.interp(sony[..., c], xs, ys)
    over = sony[..., c] > xs[-1]
    slope = (ys[-1] - ys[-50]) / max(xs[-1] - xs[-50], 1e-6)
    g[..., c][over] = ys[-1] + slope * (sony[..., c][over] - xs[-1])

# 3. residu de baixa freqüència ------------------------------------------------
# Convolució normalitzada (gaussiana σ = SIGMA_D px) de E = g(sony) − vix sobre la zona vàlida.
# Tot el que difereix a escales més grans que ~2,5·σ (gradients concèntrics, vinyetatge,
# gradients de cel, taques) es resta; el que la Sony aporta és el que queda per sota.
SIGMA_D = float(sys.argv[3]) if len(sys.argv) > 3 else 80.0
E = g - vix
m = valid_er.astype(np.float32)
# variant «vores netes»: el residu s'estima només a l'interior (a més de VORA px de cada vora del
# llenç), i cap a les vores s'extrapola: la Sony hi continua el seu cel natural en lloc de copiar
# l'enfosquiment de vora de la capa Vixen
VORA = int(sys.argv[4]) if len(sys.argv) > 4 else 0
if VORA > 0:
    yy_, xx_ = np.mgrid[0:H, 0:W]
    dist_b = np.minimum(np.minimum(yy_, H - 1 - yy_), np.minimum(xx_, W - 1 - xx_))
    m = m * (dist_b >= VORA)
    print('residu estimat només a més de', VORA, 'px de les vores')
den = ndi.gaussian_filter(m, SIGMA_D, mode='constant', cval=0.0)
D = np.empty_like(g)
for c in range(3):
    num = ndi.gaussian_filter(E[..., c] * m, SIGMA_D, mode='constant', cval=0.0)
    Dc = np.where(den > 0.05, num / np.maximum(den, 1e-6), np.nan)
    # on no hi ha estimació (den petit), agafa el valor vàlid més proper
    if np.isnan(Dc).any():
        idx = ndi.distance_transform_edt(np.isnan(Dc), return_distances=False, return_indices=True)
        Dc = Dc[tuple(idx)]
    D[..., c] = Dc
np.save('D_residu_rgb.npy' if len(sys.argv) <= 4 else 'D_residu_rgb_vores.npy', D.astype(np.float32))
print('residu D: σ =', SIGMA_D, 'px; rang per canal', [(round(float(D[...,c][valid_er].min()),4), round(float(D[...,c][valid_er].max()),4)) for c in range(3)])

fit = g - D
# 4. dins la zona cremada: Vixen -----------------------------------------------
sony_fit = fit * w[..., None] + vix * (1 - w[..., None])
sony_fit = np.clip(sony_fit, 0, 1).astype(np.float32)
np.save(OUT, sony_fit)

# --- diagnòstics -------------------------------------------------------------
comp_pere = vix * (1 - np.load('sony_canvas_mask.npy')[..., None]) + sony_fit * np.load('sony_canvas_mask.npy')[..., None]
comp_new = sony_fit  # amb el pes w ja incorporat, la capa sola ja és el compost «net»
Image.fromarray((np.clip(comp_pere, 0, 1) * 255).astype(np.uint8)[::4, ::4]).save('comp_fit_mascaraPere_ds4.png')
Image.fromarray((np.clip(comp_new, 0, 1) * 255).astype(np.uint8)[::4, ::4]).save('comp_fit_ds4.png')

# perfils radials abans/després
edges = np.arange(0.9, 7.6, 0.05); rc_ = 0.5 * (edges[:-1] + edges[1:])
def prof(img, c):
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        sel = (r >= a) & (r < b)
        out.append(np.median(img[..., c][sel]) if sel.any() else np.nan)
    return np.array(out)
fig, axs = plt.subplots(2, 1, figsize=(11, 9), sharex=True)
cols = 'rgb'
for c in range(3):
    axs[0].plot(rc_, prof(vix, c), cols[c] + '-', label=f'Vixen {"RGB"[c]}')
    axs[0].plot(rc_, prof(sony_fit, c), cols[c] + '--', label=f'Sony encaixada {"RGB"[c]}')
    axs[0].plot(rc_, prof(comp_pere, c), cols[c] + ':', lw=2, label=f'Compost amb màscara de Pere {"RGB"[c]}')
axs[0].set_yscale('log'); axs[0].legend(ncol=3, fontsize=8); axs[0].grid(alpha=0.3); axs[0].set_ylabel('mediana per anell')
for c in range(3):
    axs[1].plot(rc_, prof(sony_fit, c) - prof(vix, c), cols[c] + '-', label=f'encaixada − Vixen {"RGB"[c]}')
    axs[1].plot(rc_, prof(comp_pere, c) - prof(vix, c), cols[c] + ':', label=f'compost Pere − Vixen {"RGB"[c]}')
axs[1].axhline(0, color='k', lw=0.5); axs[1].set_ylim(-0.02, 0.02); axs[1].grid(alpha=0.3); axs[1].legend(ncol=2, fontsize=8)
axs[1].set_xlabel('R☉'); axs[1].set_ylabel('diferència')
plt.tight_layout(); plt.savefig('diag_fit_perfils.png', dpi=110)

# contrast local: banda 15–60 px (escala dels plomalls), pendent i correlació Sony_fit vs Vixen per anell
def band(img, a=15, b=60):
    L = img.mean(-1)
    return ndi.gaussian_filter(L, a) - ndi.gaussian_filter(L, b)
bs, bv = band(sony_fit), band(vix)
print('banda 15–60 px per anell: r, std Sony_fit, std Vixen, pendent (cov/var_v), correlació')
for a in np.arange(3.5, 7.5, 0.5):
    sel = (r >= a) & (r < a + 0.5) & valid_er
    if sel.sum() > 5000:
        x, y = bv[sel] - bv[sel].mean(), bs[sel] - bs[sel].mean()
        print(f'  {a:.1f}–{a+0.5:.1f}: {y.std():.5f} {x.std():.5f} pendent {np.dot(x,y)/np.dot(x,x):.2f} ρ {np.dot(x,y)/np.sqrt(np.dot(x,x)*np.dot(y,y)):.2f}')
print('fet:', OUT)
