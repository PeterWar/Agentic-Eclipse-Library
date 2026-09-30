"""c1 · Comprovació de l'entrada nova dels filtres (a3c): perfil radial de G (mediana al domini) abans (V88) i després, als sectors de les marques
i als de control. Sortida: LAMINA_P1_entrada.png."""
from v89_comu import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
claim()
A = np.load(ARREL / '4-RESULTATS/v88_20260923/A3A_franja_un_instant.npz'); B = np.load(SORT / 'A3A_franja_un_instant.npz')
by0, by1, bx0, bx1 = [int(v) for v in A['box']]; cx, cy, R = [float(v) for v in A['centre']]
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360; dom = A['domini']
SECT = {'blau cel 104–119°': (104, 119), 'lila 121–152°': (121, 152), 'lila 152–170°': (152, 170), 'lila 190–205°': (190, 205), 'lila 205–229°': (205, 229), 'dreta 0–30°': (0, 30), 'dalt 70–100° (control)': (70, 100), 'baix 255–285° (control)': (255, 285)}
xs = np.arange(0.5, 20.01, 0.5); kb = np.round(d * 2) / 2
fig, axs = plt.subplots(2, 4, figsize=(18, 8)); axs = axs.ravel()
for ax, (nom, (a0, a1)) in zip(axs, SECT.items()):
    sel = dom & (th >= a0) & (th <= a1)
    for Q, et, st in [(A, 'V88', 'k-'), (B, 'prova (sense pujada)', 'r--')]:
        ys = np.array([np.median(Q['G'][sel & (kb == v)]) if (sel & (kb == v)).sum() > 5 else np.nan for v in xs]); ax.plot(xs, ys / np.nanmedian(ys[(xs >= 10) & (xs <= 14)]), st, lw=2, label=et)
    ax.set_title(nom, fontsize=10); ax.grid(alpha=0.3); ax.set_xlabel('distància al limbe (px)')
axs[0].legend(); fig.suptitle("Entrada dels filtres (G lineal): V88 contra la prova. On la corona pujava des del limbe, ara continua cap endins des del màxim", fontsize=11)
fig.tight_layout(); fig.savefig(SORT / 'LAMINA_P1_entrada.png', dpi=95); plt.close(fig); log('fet')
