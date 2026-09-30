"""r2 · Prova de sectors: perfil de la vista de banda d'un apilat (sense el perfil radial solar) en funció de la distància a l'eix òptic,
per sectors d'angle al voltant de l'eix. Anells de l'òptica ⇒ el mateix perfil a tots els sectors. Ús: r2_perfil_sectors.py sonyA|sonyB cx cy"""
import sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
R = Path(__file__).resolve().parents[3]; D = R / '4-RESULTATS/v112_claude_20260928/apilats_banda'
nom = sys.argv[1]; cx, cy = float(sys.argv[2]), float(sys.argv[3])
L = np.load(D / f'L_{nom}.npy'); B = 6; h, w = L.shape
yy, xx = np.mgrid[0:h, 0:w]; X = xx * B + 3; Y = yy * B + 3
rsun = np.hypot(X - 5375.8, Y - 3776.0) / 453.0
rho = np.hypot(X - cx, Y - cy); ang = np.degrees(np.arctan2(Y - cy, X - cx)) % 360
ok = np.isfinite(L) & (rsun > 3.2)
bins = np.arange(0, 6000, 30)
fig, ax = plt.subplots(figsize=(12, 4))
for a0 in range(0, 360, 45):
    m = ok & (ang >= a0) & (ang < a0 + 45)
    if m.sum() < 5000: continue
    idx = np.digitize(rho[m], bins); v = L[m]
    prof = np.array([np.median(v[idx == k]) if (idx == k).sum() > 150 else np.nan for k in range(1, len(bins))])
    ax.plot(bins[:-1] + 15, prof * 100, lw=1, label=f'{a0}–{a0+45}°')
for r_ in (1908, 2366, 2832): ax.axvline(r_, color='m', lw=.6, ls='--')
ax.set_xlabel('distància a l\'eix (px de llenç)'); ax.set_ylabel('banda (%)'); ax.set_ylim(-0.4, 0.4); ax.grid(alpha=.3); ax.legend(ncol=8, fontsize=7)
ax.set_title(f'{nom}: perfil al voltant de ({cx:.0f},{cy:.0f}) per sectors (r_sol > 3,2 R)')
fig.tight_layout(); fig.savefig(R / f'4-RESULTATS/v112_claude_20260928/vistes/sectors_{nom}.png', dpi=100)
