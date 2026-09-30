"""Rigidesa del terme lunar: Λ_obs,j = δ_j − C_conegut (C dels fotogrames 0–18 que veuen el píxel a D ≥ 8), a coordenades lunars,
comparat entre grups de fotogrames tardans (26–36, 38–49, 50–66) al costat d'avanç (130–240°)."""
import numpy as np, pickle
from inversio import Inversio
sig = dict(np.load('SIG.npz'))
I = Inversio(sig_tab=sig, verbose=False); S = I.S
fr = [j for j in range(67) if sig['sig'][j].min() < 0.5]
I.prepara(fr)
# C conegut: fotogrames 0–18 amb D ≥ 8
sw = np.zeros((len(S.dg), S.nth)); sy = np.zeros_like(sw)
for j in [j for j in fr if j <= 18]:
    c = I.cache[j]; m = c['ok'] & (c['D'] >= 8); w = (1 / I.sigma(j) ** 2)[:, None] * m
    sw += w; sy += w * c['d']
Ck = np.where(sw > 0, sy / np.maximum(sw, 1e-30), np.nan)
dphi = 0.125; nphi = int(360 / dphi); Dg = np.arange(0.5, 6.01, 0.5); nDb = len(Dg) - 1
grups = {'G26-36': [j for j in fr if 26 <= j <= 36], 'G38-49': [j for j in fr if 38 <= j <= 49], 'G50-58': [j for j in fr if 50 <= j <= 58], 'G59-66': [j for j in fr if 59 <= j <= 66]}
LAM = {}
for g, js in grups.items():
    SW = np.zeros((nDb, nphi)); SY = np.zeros_like(SW)
    for j in js:
        c = I.cache[j]; m = c['ok'] & np.isfinite(Ck) & (c['D'] >= Dg[0]) & (c['D'] < Dg[-1]) & (c['a'] >= 130) & (c['a'] < 240)
        ia = (c['a'][m] / dphi).astype(int) % nphi; kd = np.digitize(c['D'][m], Dg) - 1
        w = (1 / I.sigma(j) ** 2)[:, None] * np.ones((1, S.nth)); w = w[m]
        np.add.at(SW, (kd, ia), w); np.add.at(SY, (kd, ia), w * (c['d'][m] - Ck[m]))
    LAM[g] = (np.where(SW > 0, SY / np.maximum(SW, 1e-30), np.nan), SW)
from itertools import combinations
from scipy.ndimage import gaussian_filter1d
def hp(x):  # pas alt al llarg de φ (treu la part suau > ~4°) per comparar estructura fina
    v = np.isfinite(x); xx = np.where(v, x, 0); s = gaussian_filter1d(xx, 16, mode='wrap') / np.maximum(gaussian_filter1d(v.astype(float), 16, mode='wrap'), 1e-6)
    return np.where(v, x - s, np.nan)
for k in range(nDb):
    txt = []
    for g1, g2 in combinations(grups, 2):
        a = hp(LAM[g1][0][k]); b = hp(LAM[g2][0][k]); m = np.isfinite(a) & np.isfinite(b)
        if m.sum() > 100: txt.append(f'{g1}×{g2}: ρ {np.corrcoef(a[m], b[m])[0, 1]:+.2f} (n {m.sum()}, rms {np.std(a[m]):.3f}/{np.std(b[m]):.3f})')
    print(f'D {Dg[k]:.1f}-{Dg[k+1]:.1f}: ' + ' | '.join(txt))
