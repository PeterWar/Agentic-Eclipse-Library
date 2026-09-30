"""d35 (V100 detall) · LA CAPA DE DETALL REAL DE LA BANDA (pla de Codex: detall de la dada calibrada, en una capa a part).
Dada: D29_banda_15_30.npz (tots els fotogrames Vixen amb D_real ≥ 1,5 px del seu limbe REAL, dividits per la seva transmissió mesurada;
meitats independents parells/senars). Senyal: lluminància post-matriu L = (c0·R' + 2·c1·G' + c2·B')/4 (l'entrada dels ACHF, amb els factors de l'a3c).
Detall TANGENCIAL (al llarg de l'arc, a cada radi): ln L remostrejat en polar al voltant del centre de presentació (dr 0,25 px, ds 0,5 px), bandes
de diferència de gaussianes al llarg de l'arc (σ 1, 2, 4, 8 px; convolució normalitzada pels vàlids). La mitjana de cada banda al llarg de l'arc
és zero per construcció: la capa NO pot fer cap anell concèntric. Cada banda es pondera pel seu SENYAL CORROBORAT entre les dues meitats
(Wiener local: g = S/(S+N), S = ⟨b₁·b₂⟩, N = ⟨((b₁−b₂)/2)²⟩, finestra gaussiana σ 20 px d'arc × 0,75 px radials). Cap suavitzat de la textura.
Zona: on la dada és vàlida (NF ≥ 3; rampa d'1 px des de la vora interior) fins a la vora de dada de la V99 + 2 px (fosa d'1,5 px cap enfora,
on la textura dels filtres de la V99 pren el relleu); a l'esquerra (135–210°) també, però allà hi manen les capes d'interiors de Pere.
Sortida: CAPA_DETALL_BANDA.npz (delta, alfa, box) i vistes PNG. El contrast (k) es fixa després contra el compost natiu (d36)."""
import json, os
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d, gaussian_filter
ARREL = Path(__file__).resolve().parents[3]; O = ARREL / '4-RESULTATS/v100_detall_20260925'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925/B'
Z = np.load(O / os.environ.get('D35_FONT', 'D29_banda_15_30.npz')); by0, by1, bx0, bx1 = [int(v) for v in Z['box']]; LX, LY, RL = [float(v) for v in Z['centre']]
esc = json.loads((R9 / 'lineal_v99_franja/A3C_FRANJA_SILUETA.json').read_text())['escales']; cF = [esc[f'c_F{c}'][0] for c in range(3)]
Q9 = np.load(R9 / 'lineal_v99_franja/A3C_franja_silueta.npz'); DMIN9 = Q9['DMIN']; NBZ = DMIN9.size
def lum(P): return (cF[0] * P[..., 0] + 2 * cF[1] * P[..., 1] + cF[2] * P[..., 2]) / 4
L, L1, L2 = lum(Z['RGB']), lum(Z['RGB_parells']), lum(Z['RGB_senars']); NF = Z['NF']
valid = (NF >= 3) & (L > 0) & (L1 > 0) & (L2 > 0)
DR_, DS_ = 0.25, 0.5; rr = np.arange(-1.0, 16.0, DR_); nth = int(round(2 * np.pi * RL / DS_)); tt = np.arange(nth) * 2 * np.pi / nth
R_, T_ = np.meshgrid(RL + rr, tt, indexing='ij'); mx = (LX + R_ * np.cos(T_) - bx0).astype(np.float32); my = (LY - R_ * np.sin(T_) - by0).astype(np.float32)
def polar(img, v):
    a = cv2.remap(np.where(v, img, 0).astype(np.float32), mx, my, cv2.INTER_LINEAR); w = cv2.remap(v.astype(np.float32), mx, my, cv2.INTER_LINEAR)
    return np.where(w > 0.999, a / np.maximum(w, 1e-6), np.nan)
def lnp(P): return np.where(np.isfinite(P) & (P > 0), np.log(np.maximum(P, 1e-30)), np.nan)
X, X1, X2 = lnp(polar(L, valid)), lnp(polar(L1, valid)), lnp(polar(L2, valid)); OK = np.isfinite(X) & np.isfinite(X1) & np.isfinite(X2)
def gtang(x, ok, s):   # gaussiana al llarg de l'arc, normalitzada pels vàlids (σ en px d'arc)
    w = ok.astype(np.float64); return gaussian_filter1d(np.where(ok, x, 0) * w, s / DS_, axis=1, mode='wrap') / np.maximum(gaussian_filter1d(w, s / DS_, axis=1, mode='wrap'), 1e-6)
SIGS = [float(v) for v in os.environ.get('D35_SIGS', '0,1,2,4,8').split(',')]   # V100 final: 1,2,4,8,16 (sense la banda més fina: el gra fi hi és soroll)
def bandes(x):
    g = [np.where(OK, x, np.nan) if s == 0 else gtang(x, OK, s) for s in SIGS]; return [np.where(OK, g[i] - g[i + 1], 0.0) for i in range(len(SIGS) - 1)]
B, B1, B2 = bandes(X), bandes(X1), bandes(X2)
def finestra(q): return gaussian_filter(np.where(OK, q, 0), (0.75 / DR_, 20 / DS_), mode=('nearest', 'wrap')) / np.maximum(gaussian_filter(OK.astype(float), (0.75 / DR_, 20 / DS_), mode=('nearest', 'wrap')), 1e-6)
delta = np.zeros_like(X); guanys = []
for b, b1, b2 in zip(B, B1, B2):
    S = np.maximum(finestra(b1 * b2), 0); Nn = finestra(((b1 - b2) / 2) ** 2); g = S / np.maximum(S + Nn, 1e-12); delta += g * b; guanys.append(g)
delta = np.where(OK, delta, 0.0)
# de polar a cartesià
yy, xx = np.mgrid[by0:by1, bx0:bx1]; r_ = np.hypot(xx - LX, yy - LY); t_ = np.arctan2(-(yy - LY), xx - LX) % (2 * np.pi)
ri = ((r_ - RL - rr[0]) / DR_).astype(np.float32); ti = (t_ / (2 * np.pi) * nth).astype(np.float32)
dC = cv2.remap(delta.astype(np.float32), ti, ri, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
okC = cv2.remap(OK.astype(np.float32), ti, ri, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0) > 0.999
d = r_ - RL; th = np.degrees(t_); dm9 = np.maximum(DMIN9, 0)[(th / 360 * NBZ).astype(int) % NBZ]
def ss(x, a, b): u = np.clip((x - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)
dist_int = cv2.distanceTransform(okC.astype(np.uint8), cv2.DIST_L2, 5)          # distància a la vora interior de la dada vàlida
alfa = (ss(dist_int, 0.0, 1.0) * (1 - ss(d - dm9, 0.5, 2.0)) * okC * (d < 15)).astype(np.float32)
SORT35 = os.environ.get('D35_SORTIDA', 'CAPA_DETALL_BANDA')
np.savez_compressed(O / f'{SORT35}.npz', box=np.array([by0, by1, bx0, bx1]), delta=dC.astype(np.float32), alfa=alfa, sigmes=np.array(SIGS))
# resum per sector: guany mitjà de cada banda i amplitud del detall a la zona útil (alfa > 0,5)
rep = {}
thp = np.degrees(tt)
for a0, a1 in ((75, 105), (105, 135), (135, 165), (165, 210), (210, 235), (235, 255)):
    sel = ((thp - a0) % 360) < ((a1 - a0) % 360); r = {}
    for lo, hi in ((1.5, 2.5), (2.5, 3.5), (3.5, 5.0), (5.0, 8.0)):
        rows = (rr >= lo) & (rr < hi); m = OK[rows][:, sel]
        if m.sum() < 50: continue
        r[f'{lo}-{hi}'] = dict(guany_per_banda=[round(float(np.mean(g[rows][:, sel][m])), 3) for g in guanys], rms_delta=round(float(np.std(delta[rows][:, sel][m])), 4),
                               rms_cru=round(float(np.std(sum(B)[rows][:, sel][m])), 4))
    rep[f'{a0}-{a1}'] = r; print(a0, a1, {k: (v['guany_per_banda'], v['rms_delta'], v['rms_cru']) for k, v in r.items()})
(O / f'{SORT35}.json').write_text(json.dumps(dict(sigmes_arc_px=SIGS, finestra_wiener=dict(arc_px=20, radial_px=0.75), factors_cF=cF, sectors=rep), ensure_ascii=False, indent=1))
v = np.clip(0.5 + 8 * dC * alfa, 0, 1); cv2.imwrite(str(O / f'{SORT35}_x8.png'), (v[150:1250, 150:1250] * 255).astype(np.uint8))
print('fet')
