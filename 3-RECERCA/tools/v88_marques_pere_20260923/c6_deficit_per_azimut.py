"""c6 · El dèficit arran del limbe de l'entrada dels filtres, per azimut: perfil radial de G (a3a) normalitzat, per sectors de 5°, i el mateix
per als filtres ja fets (NRGF 41). Mètrica: G(d)/G_ref, amb G_ref = ajust lineal de ln G a 8–16 px extrapolat (el perfil natural de la corona,
que decreix cap enfora). Sortida: DEFICIT_PER_AZIMUT.json, LAMINA_M6_deficit.png (mapa polar azimut × distància del quocient)."""
from vm_comu import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
claim()
Q = np.load(V88D / 'A3A_franja_un_instant.npz'); by0, by1, bx0, bx1 = [int(v) for v in Q['box']]; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
G = Q['G']; E = Q['E']; dom = Q['domini']; NF = Q['NF']
nrgf = np.load(V88D / 'filtres/P01_NRGF_u16.npy', mmap_mode='r')[by0:by1, bx0:bx1].astype(np.float32) / 65535
SEC = 5; ns = 360 // SEC; xs = np.arange(0, 20.01, 0.5); mapa = np.full((ns, len(xs)), np.nan); mapaN = np.full((ns, len(xs)), np.nan); rg = np.full((ns, len(xs)), np.nan)
isec = (th // SEC).astype(int) % ns; kb = np.round(d * 2).astype(int)
for s in range(ns):
    sel = (isec == s) & dom
    prof = np.array([np.median(G[sel & (kb == int(v * 2))]) if (sel & (kb == int(v * 2))).sum() > 5 else np.nan for v in xs])
    profN = np.array([np.median(nrgf[sel & (kb == int(v * 2))]) if (sel & (kb == int(v * 2))).sum() > 5 else np.nan for v in xs])
    profR = np.array([np.median(E[..., 0][sel & (kb == int(v * 2))] / np.maximum(E[..., 1][sel & (kb == int(v * 2))], 1e-6)) if (sel & (kb == int(v * 2))).sum() > 5 else np.nan for v in xs])
    ref = (xs >= 8) & (xs <= 16) & np.isfinite(prof) & (prof > 0)
    if ref.sum() < 5: continue
    a, b = np.polyfit(xs[ref], np.log(prof[ref]), 1); mapa[s] = prof / np.exp(a * xs + b)
    mapaN[s] = profN - np.nanmedian(profN[(xs >= 8) & (xs <= 16)]); rg[s] = profR / np.nanmedian(profR[(xs >= 8) & (xs <= 16)])
out = dict(sector_graus=SEC, d=xs.tolist(), quocient_G_sobre_tendencia=np.round(mapa, 4).tolist(), nrgf_menys_nivell_8_16=np.round(mapaN, 4).tolist(), R_sobre_G_relatiu=np.round(rg, 4).tolist())
# resum: dèficit mitjà a 2–5 px per sector
dd = (xs >= 2) & (xs <= 5); out['deficit_2_5px_per_sector'] = {f'{s * SEC}-{s * SEC + SEC}': (None if not np.isfinite(mapa[s][dd]).any() else round(float(np.nanmean(mapa[s][dd]) - 1), 3)) for s in range(ns)}
desa_json('DEFICIT_PER_AZIMUT.json', out)
fig, axs = plt.subplots(1, 3, figsize=(18, 7))
for ax, M_, t, lim in [(axs[0], mapa - 1, 'G / tendència de 8–16 px − 1 (entrada dels filtres)', 0.3), (axs[1], mapaN, 'NRGF (41, abans a4) − nivell a 8–16 px', 0.3), (axs[2], rg - 1, 'R/G relatiu a 8–16 px − 1 (vermell = cromosfera)', 0.5)]:
    im = ax.imshow(M_, aspect='auto', origin='lower', extent=[xs[0] - 0.25, xs[-1] + 0.25, 0, 360], cmap='RdBu_r', vmin=-lim, vmax=lim)
    ax.set_xlabel('distància al limbe de presentació (px)'); ax.set_ylabel('azimut (°, 0 = dreta, 90 = dalt)'); ax.set_title(t, fontsize=10); plt.colorbar(im, ax=ax, fraction=0.04)
    for a0, a1 in [(104, 119), (120, 152), (171, 178), (210, 212), (215, 229)]: ax.axhspan(a0, a1, xmin=0, xmax=0.02, color='m')
fig.tight_layout(); fig.savefig(SORT / 'LAMINA_M6_deficit.png', dpi=100); plt.close(fig)
for k, v in out['deficit_2_5px_per_sector'].items():
    if v is not None and abs(v) > 0.05: print(k, v)
log('fet')
