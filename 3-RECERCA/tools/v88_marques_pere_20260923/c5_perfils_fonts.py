"""c5 · On neix la línia paral·lela al limbe que porten tots els filtres a les marques: perfils radials (mediana per calaix de 0,25 px) a cada marca de
l'entrada lineal dels filtres (G de a3a, amb la dada d'un instant a la franja), del nombre de fotogrames, i de cada ràster de filtre abans (filtres/)
i després (filtres_finals/) de la fosa de la vora (a4). Les distàncies, des del limbe de presentació (R 453) i des de la corba llisa DMIN.
Sortida: FONTS_PERFILS.json i LAMINA_M5_perfils_fonts.png."""
from vm_comu import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
claim()
CAPA = {41: 'P01_NRGF', 42: 'P01_NRGF_extrap', 51: '04', 56: 'P05_WOW_bilateral', 55: 'P04_WOW', 47: '03', 49: '07', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native'}
Q = np.load(V88D / 'A3A_franja_un_instant.npz'); by0, by1, bx0, bx1 = [int(v) for v in Q['box']]; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
NBZ = len(Q['DMIN']); dmin = Q['DMIN'][(th / 360 * NBZ).astype(int) % NBZ]
M = json.loads((SORT / 'MARQUES_V88.json').read_text()); llocs = [(g['nom'], cc) for g in M['grups_de_to'] for cc in g['components'] if cc['d_limbe_px'][1] < 10]
series = {'G entrada (a3a)': Q['G'], 'E verd (un instant)': Q['E'][..., 1], 'NF fotogrames': Q['NF'].astype(np.float32), 'beta (pes dada un instant)': Q['beta']}
for lid, tag in CAPA.items():
    series[f'{lid} {tag} abans a4'] = np.load(V88D / f'filtres/{tag}_u16.npy', mmap_mode='r')[by0:by1, bx0:bx1].astype(np.float32) / 65535
    series[f'{lid} {tag} després a4'] = np.load(V88D / f'filtres_finals/{tag}_u16.npy', mmap_mode='r')[by0:by1, bx0:bx1].astype(np.float32) / 65535
xs = np.arange(-3, 25.01, 0.25); out = {}
fig, axs = plt.subplots(len(llocs), 3, figsize=(18, 3.4 * len(llocs)))
for j, (nom, cc) in enumerate(llocs):
    a0, a1 = cc['azimut'][0], cc['azimut'][2]; sel = (th >= a0) & (th <= a1); k = np.round(d * 4) / 4; clau = f"{nom} az {cc['azimut'][1]:.0f}"
    out[clau] = dict(dmin_mitja=float(np.median(dmin[sel & (np.abs(d) < 3)])), marca_d=cc['d_limbe_px'], perfils={})
    for nomS, A in series.items():
        ys = []
        for v in xs:
            s = sel & (k == v); ys.append(float(np.median(A[s])) if s.sum() > 3 else np.nan)
        out[clau]['perfils'][nomS] = ys
    ax = axs[j, 0]; g = np.array(out[clau]['perfils']['G entrada (a3a)']); ax.plot(xs, g / np.nanmax(g), label='G entrada (norm.)', lw=2)
    ax.plot(xs, np.array(out[clau]['perfils']['NF fotogrames']) / 11, label='NF/11'); ax.plot(xs, out[clau]['perfils']['beta (pes dada un instant)'], label='beta')
    ax.set_title(f'{clau}° · entrada · DMIN {out[clau]["dmin_mitja"]:.2f} px', fontsize=9)
    for col, quan in [(1, 'abans a4'), (2, 'després a4')]:
        ax2 = axs[j, col]
        for nomS, ys in out[clau]['perfils'].items():
            if nomS.endswith(quan):
                y = np.array(ys); ref = np.nanmedian(y[(xs >= 10) & (xs <= 20)]); ax2.plot(xs, y - ref, label=nomS.replace(' ' + quan, ''), lw=1)
        ax2.set_title(f'{clau}° · filtres {quan} (menys el nivell a 10–20 px)', fontsize=9); ax2.set_ylim(-0.25, 0.25)
    for a_ in axs[j]:
        a_.axvspan(cc['d_limbe_px'][0], cc['d_limbe_px'][2], color='k', alpha=0.08); a_.axvline(out[clau]['dmin_mitja'], color='k', ls=':', lw=1)
        a_.axvline(out[clau]['dmin_mitja'] + 1, color='r', ls=':', lw=0.8); a_.axvline(out[clau]['dmin_mitja'] + 4, color='r', ls=':', lw=0.8); a_.grid(alpha=0.3)
axs[0, 0].legend(fontsize=7); axs[0, 1].legend(fontsize=6, ncol=2); fig.tight_layout(); fig.savefig(SORT / 'LAMINA_M5_perfils_fonts.png', dpi=100); plt.close(fig)
desa_json('FONTS_PERFILS.json', out); log('fet')
