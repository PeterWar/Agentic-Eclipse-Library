"""d14 (V98) · Perfil d'un filtre per distància a la vora de la dada (dv) i sector, per a dues carpetes de filtres (p. ex. normal i retallat 5 px):
d14_perfil_dv.py <tag> <carpetaA> <carpetaB> a0-a1 ..."""
import sys, numpy as np
from pathlib import Path
tag, A, B = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
Q = np.load('4-RESULTATS/v98_20260925/lineal_v98_franja/A3B_franja_neta.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; LX, LY, RL = [float(v) for v in Q['centre']]
yy, xx = np.mgrid[qy0:qy1, qx0:qx1]; d = np.hypot(xx - LX, yy - LY) - RL; th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
DM = np.maximum(Q['DMIN'], 0); dv = d - DM[(th / 360 * len(DM)).astype(int) % len(DM)]
for sec in sys.argv[4:]:
    a0, a1 = map(float, sec.split('-'))
    for nom, c in (('A', A), ('B', B)):
        u = np.load(c / f'{tag}_u16.npy', mmap_mode='r')[qy0:qy1, qx0:qx1] / 65535.; al = np.load(c / f'{tag}_alfa_u16.npy', mmap_mode='r')[qy0:qy1, qx0:qx1] / 65535.
        s = (th >= a0) & (th < a1) & (al > 0.99)
        print(tag, nom, sec, ' '.join(f'{np.median(u[s & (dv >= k) & (dv < k + 1)]):.3f}' if (s & (dv >= k) & (dv < k + 1)).sum() > 20 else '  -  ' for k in range(0, 16)))
