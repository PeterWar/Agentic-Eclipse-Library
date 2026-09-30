"""t3 (V99 banda, tancament de Codex) · Injecció completa per a la transferència: (1) TANGENCIAL, les dues freqüències als MATEIXOS sectors
(PA 60–130°): 1 + ε·[cos(2π·s/8) + cos(2π·s/24)], ε = 0,02; (2) RADIAL a PA 200–250°: 1 + 0,03·cos(2π·d/6). A tota la distància −2…60 px.
Ús: t3_injecta_complet.py <franja.npz> <sortida.npz>"""
import sys
import numpy as np
Q = dict(np.load(sys.argv[1])); by0, by1, bx0, bx1 = [int(v) for v in Q['box']]; cx, cy, R = [float(v) for v in Q['centre']]
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360; s = np.radians(th) * R
P = np.zeros_like(d); z = (th >= 60) & (th < 130) & (d >= -2) & (d < 60); P[z] = 0.02 * (np.cos(2 * np.pi * s[z] / 8) + np.cos(2 * np.pi * s[z] / 24))
z2 = (th >= 200) & (th < 250) & (d >= -2) & (d < 60); P[z2] = 0.03 * np.cos(2 * np.pi * d[z2] / 6)
f = (1 + P).astype(np.float32); Q['G'] = Q['G'] * f; Q['V'] = Q['V'] * f; Q['F'] = Q['F'] * f[..., None]; np.savez_compressed(sys.argv[2], **Q); print('injectat', sys.argv[2])
