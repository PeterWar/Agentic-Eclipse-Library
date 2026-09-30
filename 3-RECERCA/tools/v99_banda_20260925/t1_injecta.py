"""t1 (V99 banda, prova de transferència demanada per Codex) · Injecta a la franja lineal de la V99 (A3C_franja_silueta.npz: G, F, V) una
modulació multiplicativa coneguda al llarg de l'arc, 1 + ε·cos(2π·s/λ) amb s = longitud d'arc sobre el cercle de presentació, a tota la
distància 0–60 px: λ = 8 px a PA 60–95° i λ = 24 px a PA 95–130°; ε = 0,03. La resta de la franja, igual. Només per a proves (sortida a
4-RESULTATS/v99_banda_20260925/transferencia/). Ús: t1_injecta.py <franja.npz> <sortida.npz>"""
import sys
import numpy as np
Q = dict(np.load(sys.argv[1])); by0, by1, bx0, bx1 = [int(v) for v in Q['box']]; cx, cy, R = [float(v) for v in Q['centre']]
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
s = np.radians(th) * R; EPS = 0.03; P = np.zeros_like(d)
for (a0, a1, lam) in ((60, 95, 8.0), (95, 130, 24.0)):
    z = (th >= a0) & (th < a1) & (d >= -2) & (d < 60); P[z] = np.cos(2 * np.pi * s[z] / lam)
f = (1 + EPS * P).astype(np.float32)
Q['G'] = Q['G'] * f; Q['V'] = Q['V'] * f; Q['F'] = Q['F'] * f[..., None]
np.savez_compressed(sys.argv[2], **Q); print('injectat', sys.argv[2])
