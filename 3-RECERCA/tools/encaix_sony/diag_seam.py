"""Diagnòstic de la costura: perfils radials per canal de la Sony, de la Vixen, de la màscara i del compost."""
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

H, W = 4553, 6748
SX, SY = 3563.891 - 143, 2274.66 - 87     # centre del Sol al llenç de 6748x4553
RSOL = 446.15                              # px (limbe real, 2,1495 "/px)
print('Sol a', SX, SY)

sony = np.load('sony_canvas_rgb.npy')
vix = np.load('vixen_canvas_rgb.npy')
mask = np.load('sony_canvas_mask.npy')
comp = np.load('composite_u16.npy').astype(np.float32) / 65535.

yy, xx = np.mgrid[0:H, 0:W]
r = np.hypot(xx - SX, yy - SY) / RSOL
th = np.degrees(np.arctan2(-(yy - SY), xx - SX))  # angle matemàtic, graus
np.save('r_rsol.npy', r.astype(np.float32)); np.save('theta_deg.npy', th.astype(np.float32))

# vista de la màscara
Image.fromarray((mask[::4, ::4] * 255).astype(np.uint8)).save('mask_canvas_ds4.png')

# perfils radials (mediana per anell) fins on hi ha llenç
edges = np.arange(0.9, 7.6, 0.05)
def prof(img, ch=None):
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        sel = (r >= a) & (r < b)
        if ch is None:
            out.append(np.median(img[sel]) if sel.any() else np.nan)
        else:
            out.append(np.median(img[..., ch][sel]) if sel.any() else np.nan)
    return np.array(out)
rc = 0.5 * (edges[:-1] + edges[1:])
P = {}
for nm, img in (('sony', sony), ('vixen', vix), ('comp', comp)):
    for c in range(3):
        P[(nm, c)] = prof(img, c)
P['mask'] = prof(mask)
np.savez('perfils_radials.npz', rc=rc, **{f'{k[0]}_{k[1]}' if isinstance(k, tuple) else k: v for k, v in P.items()})

fig, axs = plt.subplots(3, 1, figsize=(11, 13), sharex=True)
cols = ['r', 'g', 'b']
for c in range(3):
    axs[0].plot(rc, P[('vixen', c)], cols[c] + '-', label=f'Vixen {"RGB"[c]}')
    axs[0].plot(rc, P[('sony', c)], cols[c] + '--', label=f'Sony {"RGB"[c]}')
    axs[0].plot(rc, P[('comp', c)], cols[c] + ':', lw=2, label=f'Compost {"RGB"[c]}')
axs[0].set_ylabel('valor (0–1), mediana per anell'); axs[0].legend(ncol=3, fontsize=8); axs[0].set_yscale('log')
axs[0].set_title('Perfils radials per canal (mediana per anell de 0,05 R☉)')
axs[1].plot(rc, P['mask'], 'k-'); axs[1].set_ylabel('màscara Sony (0–1)')
for c in range(3):
    axs[2].plot(rc, P[('sony', c)] - P[('vixen', c)], cols[c] + '-', label=f'Sony−Vixen {"RGB"[c]}')
axs[2].axhline(0, color='k', lw=0.5); axs[2].set_ylabel('Sony − Vixen'); axs[2].legend(); axs[2].set_xlabel('R☉')
axs[2].set_ylim(-0.3, 0.6)
for ax in axs: ax.grid(alpha=0.3)
plt.tight_layout(); plt.savefig('diag_perfils.png', dpi=110)

# color: quocients R/G i B/G a cada radi, Sony vs Vixen
fig, ax = plt.subplots(figsize=(11, 5))
for nm, ls in (('vixen', '-'), ('sony', '--'), ('comp', ':')):
    ax.plot(rc, P[(nm, 0)] / P[(nm, 1)], 'r' + ls, label=f'{nm} R/G')
    ax.plot(rc, P[(nm, 2)] / P[(nm, 1)], 'b' + ls, label=f'{nm} B/G')
ax.set_ylim(0.6, 1.6); ax.grid(alpha=0.3); ax.legend(ncol=3); ax.set_xlabel('R☉'); ax.set_title('Quocients de color per anell')
plt.tight_layout(); plt.savefig('diag_color.png', dpi=110)

# on és la màscara: mapa de la màscara amb anells
print('màscara: mediana per radi')
for a in (1.0, 1.2, 1.5, 1.8, 2.0, 2.2, 2.5, 3.0, 3.5, 4.0, 5.0):
    i = np.argmin(np.abs(rc - a)); print(f'  r={rc[i]:.2f}: mask={P["mask"][i]:.3f}  sony RGB={[round(float(P[("sony",c)][i]),3) for c in range(3)]}  vix RGB={[round(float(P[("vixen",c)][i]),3) for c in range(3)]}')
