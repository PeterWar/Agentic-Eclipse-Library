"""d40 (V101 detall) · Dues correccions de la verificació de Codex sobre la capa (ja amb k): (1) MITJANA LOCAL ZERO per construcció: a cada radi,
es resta al contingut k·δ la seva mitjana local al llarg de l'arc ponderada per l'alfa (gaussiana σ 20 px d'arc), de manera que la capa no pot moure
el nivell (Codex: −1,31 % a 210–240°); (2) el factor de correcció de k per PA de la prova 3 (D39_CORRECCIO_K2.json). Ús: d40_mitjana_zero_i_k2.py <capa_K.npz> <sortida.npz>"""
import sys, json
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
ARREL = Path(__file__).resolve().parents[3]; O = ARREL / '4-RESULTATS/v100_detall_20260925'
Z = np.load(O / sys.argv[1]); by0, by1, bx0, bx1 = [int(v) for v in Z['box']]; LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736
f = json.loads((O / 'D39_CORRECCIO_K2.json').read_text())['factor_per_PA']; a_ = np.array(sorted(int(k) for k in f)); fv = np.array([f[str(k)] for k in a_])
yy, xx = np.mgrid[by0:by1, bx0:bx1]; th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
F = np.interp(th, np.concatenate([a_ - 360, a_, a_ + 360]), np.concatenate([fv, fv, fv])); c = Z['delta'] * F; al = Z['alfa']
DR_, DS_ = 0.25, 0.5; rr = np.arange(-1.0, 20.0, DR_); nth = int(round(2 * np.pi * RL / DS_)); tt = np.arange(nth) * 2 * np.pi / nth
R_, T_ = np.meshgrid(RL + rr, tt, indexing='ij'); mx = (LX + R_ * np.cos(T_) - bx0).astype(np.float32); my = (LY - R_ * np.sin(T_) - by0).astype(np.float32)
cp = cv2.remap((c * al).astype(np.float32), mx, my, cv2.INTER_LINEAR); ap = cv2.remap(al.astype(np.float32), mx, my, cv2.INTER_LINEAR)
m = gaussian_filter1d(cp, 20 / DS_, axis=1, mode='wrap') / np.maximum(gaussian_filter1d(ap, 20 / DS_, axis=1, mode='wrap'), 1e-6)   # mitjana local de k·δ (ponderada per alfa)
r_ = np.hypot(xx - LX, yy - LY); t_ = np.arctan2(-(yy - LY), xx - LX) % (2 * np.pi)
mC = cv2.remap(m.astype(np.float32), (t_ / (2 * np.pi) * nth).astype(np.float32), ((r_ - RL - rr[0]) / DR_).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
out = np.where(al > 0, c - mC, 0).astype(np.float32)
np.savez_compressed(O / sys.argv[2], box=Z['box'], delta=out, alfa=al)
d = r_ - RL
for a0, a1 in ((60, 105), (105, 140), (205, 240), (240, 270)):
    sec = (th >= a0) & (th < a1); print(a0, a1, ' '.join(f'd{lo}-{lo+1}: mitj {np.mean((out*al)[sec & (d >= lo) & (d < lo + 1) & (al > 0.05)]):+.4f} (abans {np.mean((c*al)[sec & (d >= lo) & (d < lo + 1) & (al > 0.05)]):+.4f})' for lo in range(2, 6) if (sec & (d >= lo) & (d < lo + 1) & (al > 0.05)).sum() > 50))
g = 0.5 + out * (al > 0); print('retallats', int(((g < 0) | (g > 1)).sum()))
