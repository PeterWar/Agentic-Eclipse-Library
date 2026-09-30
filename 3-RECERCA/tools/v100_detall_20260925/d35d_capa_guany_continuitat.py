"""d35d (V102 detall; pregunta de Pere del 26-09; 2a versió: entrada per D_real 1→2 px amb ≥ 5 fotogrames i limitador de 3σ local) · La capa de detall real de la banda amb el GUANY PER CONTINUÏTAT RADIAL (d41), fins on arriba
la dada: dada A = D29_primerencs_075_15.npz (primerencs, t < 40 s; D_real ≥ 0,75 px, rampa 0,75→1,5; dividits per T). Detall tangencial (DoG 2→4,
4→8, 8→16 px d'arc; mitjana zero per arc), cada banda × g(banda, fila d, bloc PA) de GUANY_CONTINUITAT.npz (fracció de senyal real fix al cel:
(r/ρ)²; més enllà de 6 px, el guany de veritat de d38 amb guarda 2,75). Zona: dada vàlida (NF ≥ 3) amb 0,5 px de rampa interior; fins a la vora de
dada de la V99 + 2 px; res a 140–205°. Sortida: CAPA_V102.npz (delta, alfa) per a d37b (k) i d40 (mitjana zero i correcció K2)."""
import json
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
ARREL = Path(__file__).resolve().parents[3]; O = ARREL / '4-RESULTATS/v100_detall_20260925'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925/B'
Z = np.load(O / 'D29_primerencs_075_15.npz'); by0, by1, bx0, bx1 = [int(v) for v in Z['box']]; LX, LY, RL = [float(v) for v in Z['centre']]
esc = json.loads((R9 / 'lineal_v99_franja/A3C_FRANJA_SILUETA.json').read_text())['escales']; cF = [esc[f'c_F{c}'][0] for c in range(3)]
Q9 = np.load(R9 / 'lineal_v99_franja/A3C_franja_silueta.npz'); DMIN9 = np.maximum(Q9['DMIN'], 0); NBZ = DMIN9.size
GC = np.load(O / 'GUANY_CONTINUITAT.npz'); gtab, ROWS, BLK = GC['g'], GC['rows'], GC['blocs']
V38 = json.loads((O / 'D38_DETALL_CONTRA_VERITAT_g275.json').read_text()); g_lluny = {b: V38['6.0-9.0'][b]['pendent_B_sobre_A'] for b in ('2-4', '4-8', '8-16')}
P = Z['RGB']; L = (cF[0] * P[..., 0] + 2 * cF[1] * P[..., 1] + cF[2] * P[..., 2]) / 4; ok = (Z['NF'] >= 5) & (L > 0)
DR_, DS_ = 0.25, 0.5; rr = np.arange(-1.0, 16.0, DR_); nth = int(round(2 * np.pi * RL / DS_)); tt = np.arange(nth) * 2 * np.pi / nth; thp = np.degrees(tt)
R_, T_ = np.meshgrid(RL + rr, tt, indexing='ij'); mx = (LX + R_ * np.cos(T_) - bx0).astype(np.float32); my = (LY - R_ * np.sin(T_) - by0).astype(np.float32)
a = cv2.remap(np.where(ok, np.log(np.maximum(L, 1e-30)), 0).astype(np.float32), mx, my, cv2.INTER_LINEAR); w = cv2.remap(ok.astype(np.float32), mx, my, cv2.INTER_LINEAR)
OK = w > 0.999; X = np.where(OK, a / np.maximum(w, 1e-6), 0.0); W = OK.astype(float)
G = {s: gaussian_filter1d(X * W, s / DS_, axis=1, mode='wrap') / np.maximum(gaussian_filter1d(W, s / DS_, axis=1, mode='wrap'), 1e-6) for s in (2, 4, 8, 16)}
B = {'2-4': G[2] - G[4], '4-8': G[4] - G[8], '8-16': G[8] - G[16]}
# guany per (fila, PA): interpolació bilineal de la taula (files 0..6 per 0,5; blocs de 10° centrats a +5°); fora de la taula (d > 6), el de veritat llunyà
fi = np.clip((rr - ROWS[0]) / 0.5, 0, ROWS.size - 1); pi_ = ((thp - 5) % 360) / 10.0
delta = np.zeros_like(X)
for ib, b in enumerate(('2-4', '4-8', '8-16')):
    tab = np.concatenate([gtab[ib], gtab[ib][:, :1]], 1).astype(np.float32)
    gmap = cv2.remap(tab, np.tile(pi_.astype(np.float32), (rr.size, 1)), np.tile(fi.astype(np.float32)[:, None], (1, nth)), cv2.INTER_LINEAR)
    gmap = np.where(rr[:, None] > ROWS[-1] + 0.25, g_lluny[b], gmap); delta += gmap * B[b]
delta = np.where(OK, delta, 0.0)
# limitador: |δ| ≤ 3 × rms local del detall a d 3–6 px del mateix angle (finestra de 20° d'arc); retalla només valors extrems de la vora
rows36 = (rr >= 3) & (rr < 6); rms36 = np.sqrt(gaussian_filter1d(np.nanmean(np.where(OK[rows36], delta[rows36] ** 2, np.nan), axis=0), (20 * np.pi / 180 * RL) / DS_, mode='wrap'))
lim = 3 * np.maximum(np.nan_to_num(rms36, nan=np.nanmedian(rms36)), 1e-4)[None, :]; n_ret = int((np.abs(delta) > lim).sum()); delta = np.clip(delta, -lim, lim); print('valors limitats', n_ret)
yy, xx = np.mgrid[by0:by1, bx0:bx1]; r_ = np.hypot(xx - LX, yy - LY); t_ = np.arctan2(-(yy - LY), xx - LX) % (2 * np.pi); th = np.degrees(t_); d = r_ - RL
dC = cv2.remap(delta.astype(np.float32), (t_ / (2 * np.pi) * nth).astype(np.float32), ((r_ - RL - rr[0]) / DR_).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
def ss(x, a_, b_): u = np.clip((x - a_) / (b_ - a_), 0, 1); return u * u * (3 - 2 * u)
dint = cv2.distanceTransform(ok.astype(np.uint8), cv2.DIST_L2, 5); dd = d - DMIN9[(th / 360 * NBZ).astype(int) % NBZ]
alfa = (ss(Z['DREAL_MAX'], 1.0, 2.0) * ss(dint, 0.0, 0.5) * (1 - ss(dd, 0.5, 2.0)) * ok * (d < 15) * (1 - ss(th, 135, 140) * (1 - ss(th, 205, 210)))).astype(np.float32)
np.savez_compressed(O / 'CAPA_V102.npz', box=Z['box'], delta=dC.astype(np.float32), alfa=alfa)
for a0, a1 in ((75, 95), (95, 125), (225, 255)):
    sel = (th >= a0) & (th < a1); print(a0, a1, ' '.join(f'd{lo}-{lo+1}: alfa {np.mean(alfa[sel & (d >= lo) & (d < lo + 1)]):.2f} rms {np.std((dC * alfa)[sel & (d >= lo) & (d < lo + 1) & (alfa > 0.3)]) if (sel & (d >= lo) & (d < lo + 1) & (alfa > 0.3)).sum() > 20 else 0:.4f}' for lo in range(0, 6)))
