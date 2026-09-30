"""c13 · Perfils radials de la combinació d'un instant (E, a3a, sense el suavitzat σ 1,3 ja inclòs: és E tal com entra) en verd matricial G_m,
en lluminància Y anivellada (Y/1,177) i en R/G, als sectors de cada marca i de control. Per veure què canviaria cada via: on la Y omple la vall
(cromosfera) i on no (104–119°, sense cromosfera). Sortida: PERFILS_Y_G.json, LAMINA_M13_perfils_Y_G.png."""
from vm_comu import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
claim()
Q = np.load(V88D / 'A3A_franja_un_instant.npz'); by0, by1, bx0, bx1 = [int(v) for v in Q['box']]; E = Q['E']; dom = Q['domini']
cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']; yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - cx, yy - cy) - R
th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360; ok = dom & (E[..., 1] > 0)
Gm = E[..., 1]; Y = (0.2974 * E[..., 0] + 0.6273 * E[..., 1] + 0.0753 * E[..., 2]) / 1.177
SECT = {'dalt 80–100° (control)': (80, 100), 'blau cel 104–119°': (104, 119), 'lila 121–152°': (121, 152), 'lila 205–229°': (205, 229), 'baix 255–285° (control)': (255, 285), 'dreta 340–20° (control)': (340, 20)}
xs = np.arange(0, 25.01, 0.5); kb = np.round(d * 2) / 2; out = {'d': xs.tolist()}
fig, axs = plt.subplots(1, len(SECT), figsize=(4.4 * len(SECT), 4.6), sharey=True)
for ax, (nom, (a0, a1)) in zip(axs, SECT.items()):
    sel = ok & (((th >= a0) & (th <= a1)) if a0 < a1 else ((th >= a0) | (th <= a1)))
    def pf(A):
        ys = np.array([np.median(A[sel & (kb == v)]) if (sel & (kb == v)).sum() > 5 else np.nan for v in xs]); return ys / np.nanmedian(ys[(xs >= 10) & (xs <= 14)])
    g, y = pf(Gm), pf(Y); rg = np.array([np.median((E[..., 0] / E[..., 1])[sel & (kb == v)]) if (sel & (kb == v)).sum() > 5 else np.nan for v in xs])
    out[nom] = dict(G_m=np.round(g, 3).tolist(), Y=np.round(y, 3).tolist(), R_sobre_G=np.round(rg, 2).tolist())
    ax.plot(xs, g, 'g', lw=2, label='verd matricial (entrada actual)'); ax.plot(xs, y, 'k', lw=2, label='lluminància Y'); ax2 = ax.twinx(); ax2.plot(xs, rg, 'r:', lw=1.2); ax2.set_ylim(0, 6)
    if ax is axs[-1]: ax2.set_ylabel('R/G (vermell puntejat)', color='r')
    ax.set_title(nom, fontsize=10); ax.set_xlabel('distància al limbe (px)'); ax.grid(alpha=0.3); ax.set_ylim(0.4, 2.2)
axs[0].set_ylabel('perfil / valor a 10–14 px'); axs[0].legend(fontsize=7)
fig.tight_layout(); fig.savefig(SORT / 'LAMINA_M13_perfils_Y_G.png', dpi=100); plt.close(fig); desa_json('PERFILS_Y_G.json', out); log('fet')
