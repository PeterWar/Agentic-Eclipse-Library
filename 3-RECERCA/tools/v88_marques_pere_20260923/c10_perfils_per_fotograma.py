"""c10 · La vall arran del limbe de l'esquerra: és a cada fotograma o la fa la combinació? Perfil radial del verd de cada fotograma primerenc
(num/pes, sense rampa ni llindars), normalitzat a 10–14 px del limbe de presentació, als sectors de les marques (130–170° i 190–225°) i de control
(75–105° dalt, 255–285° baix, 345–15° dreta); i el de E (la combinació de la V88). Amb el limbe propi de cada fotograma (D_obs = 0) marcat.
Sortida: PERFILS_PER_FOTOGRAMA.json i LAMINA_M10_perfils_per_fotograma.png."""
from vm_comu import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
claim()
V85D = ARREL / '4-RESULTATS/v85_regeneracio_20260922'
meta = json.loads((V85D / 'limb_frames/METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
num = np.load(V85D / 'limb_frames/numerator.npy', mmap_mode='r'); wt = np.load(V85D / 'limb_frames/weight.npy', mmap_mode='r'); Dm = np.load(V85D / 'limb_frames/distance_model.npy', mmap_mode='r')
cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']; DR = float(meta['radius_model']) - R
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
Q = np.load(V88D / 'A3A_franja_un_instant.npz'); assert list(Q['box']) == [by0, by1, bx0, bx1]
early = [i for i, f in enumerate(fr) if f['time'] <= 22.3]
SECT = {'esquerra-dalt 130–170° (marques)': (130, 170), 'esquerra-baix 190–225° (marques)': (190, 225), 'dalt 75–105°': (75, 105), 'baix 255–285°': (255, 285), 'dreta 345–15°': (345, 15)}
xs = np.arange(-4, 20.01, 0.5); kb = np.round(d * 2) / 2; out = {}
fig, axs = plt.subplots(1, len(SECT), figsize=(5.2 * len(SECT), 5), sharey=True)
for ax, (nom, (a0, a1)) in zip(axs, SECT.items()):
    sel = ((th >= a0) & (th <= a1)) if a0 < a1 else ((th >= a0) | (th <= a1)); out[nom] = {}
    cmap = plt.get_cmap('viridis')
    for j, i in enumerate(early):
        n_ = np.asarray(num[i, :, :, 1], np.float32); w_ = np.asarray(wt[i, :, :, 1], np.float32); g_ = np.where(w_ > 0, n_ / np.maximum(w_, 1e-30), np.nan)
        Do = np.asarray(Dm[i]) + DR
        ys = np.array([np.nanmedian(g_[sel & (kb == v)]) if np.isfinite(g_[sel & (kb == v)]).sum() > 5 else np.nan for v in xs])
        ref = np.nanmedian(ys[(xs >= 10) & (xs <= 14)]); ys = ys / ref if np.isfinite(ref) and ref > 0 else ys * np.nan
        limb = float(np.median(d[sel & (np.abs(Do) < 0.5)])) if (sel & (np.abs(Do) < 0.5)).sum() > 5 else np.nan
        out[nom][fr[i]['name']] = dict(t=fr[i]['time'], exposicio=fr[i]['exposure'], limbe_propi_d=limb, perfil=np.round(ys, 4).tolist())
        ax.plot(xs, ys, color=cmap(j / max(len(early) - 1, 1)), lw=1, label=f"t {fr[i]['time']:.1f} s · {fr[i]['exposure']*1000:.2f} ms")
        if np.isfinite(limb): ax.axvline(limb, color=cmap(j / max(len(early) - 1, 1)), lw=0.6, ls=':')
    e = Q['E'][..., 1]; ok = Q['domini']
    ys = np.array([np.median(e[sel & ok & (kb == v)]) if (sel & ok & (kb == v)).sum() > 5 else np.nan for v in xs]); ys = ys / np.nanmedian(ys[(xs >= 10) & (xs <= 14)])
    out[nom]['E_combinacio_V88'] = np.round(ys, 4).tolist(); ax.plot(xs, ys, 'r', lw=2.5, label='E (combinació V88)')
    ax.set_title(nom, fontsize=10); ax.set_xlabel('distància al limbe de presentació (px)'); ax.grid(alpha=0.3); ax.set_ylim(0, 3)
axs[0].set_ylabel('verd / valor a 10–14 px'); axs[0].legend(fontsize=6)
fig.tight_layout(); fig.savefig(SORT / 'LAMINA_M10_perfils_per_fotograma.png', dpi=100); plt.close(fig)
out['d'] = xs.tolist(); desa_json('PERFILS_PER_FOTOGRAMA.json', out); log('fet')
