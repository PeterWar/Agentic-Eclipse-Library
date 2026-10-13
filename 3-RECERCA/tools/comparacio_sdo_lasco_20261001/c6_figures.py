"""c6 · Figures de la comparació:
  FA  desplegat polar alineat per angle: final (NRGF), K-Cor (NRGF del HAO) i LASCO C2 (vista sense harmònics baixos);
  FB  correlació del detall d'angle (< 12°) entre la final i cada instrument, per radi, amb la banda del control nul (±2σ)
      i la referència entre dos instruments professionals (K-Cor ↔ AIA 211 Å);
  i SERIES_CORRELACIO.json per a la pàgina interactiva."""
import json, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from comu_comp import *
from lasco_vista import VistaLasco
import os
CA = os.environ.get('LANG_FIG') == 'ca'; SUF = '_ca' if CA else ''

# ---------------------------------------------------------------- FA: desplegat polar alineat
z = np.load(RES / 'C2_desplegats.npz'); pa, r = z['pa'], z['r']
v2 = VistaLasco('24038985.fts', 2.25, 6.4, mmax=3, suau_r=1.0)
RR, PP = np.meshgrid(r, pa, indexing='ij'); c2v = v2.mostra(RR, PP); c2v[:, (pa >= 290) & (pa <= 352)] = np.nan
franges = [('Eclipsi (Pere Guerra) · 18:28:46 UT' if CA else 'Eclipse (Pere Guerra) · 18:28:46 UT', z['nrgf_final'], (1.08, 6.0), (-2.2, 2.8)),
           ('K-Cor (Mauna Loa) · llum blanca polaritzada · 18:29:32 UT' if CA else 'K-Cor (Mauna Loa) · polarized white light · 18:29:32 UT', z['nrgf_kcor'], (1.08, 2.0), (-2.0, 3.0)),
           ('SOHO/LASCO C2 · 18:24:31 UT', c2v, (2.3, 6.0), (-1.3, 3.8))]
fig, axs = plt.subplots(3, 1, figsize=(14, 9.2), gridspec_kw=dict(height_ratios=[1.0, 0.36, 0.55], hspace=0.32), facecolor='#0d0d0d')
for ax, (tit, A, (r1, r2), (lo, hi)) in zip(axs, franges):
    sel = (r >= r1) & (r <= r2)
    ax.imshow(np.clip((A[sel] - lo) / (hi - lo), 0, 1), origin='lower', aspect='auto', cmap='gray', interpolation='bilinear',
              extent=[0, 360, np.log10(r[sel][0]), np.log10(r[sel][-1])])
    ax.set_facecolor('#000000')
    ticks = [t for t in [1.1, 1.25, 1.5, 2, 2.5, 3, 4, 5, 6] if r1 <= t <= r2]
    ax.set_yticks(np.log10(ticks)); ax.set_yticklabels([f'{t:g}' for t in ticks], color='#c3c2b7', fontsize=9)
    ax.set_xticks(np.arange(0, 361, 30)); ax.set_xticklabels([({0: '0° N', 90: '90° E', 180: '180° S', 270: '270° O', 360: '360° N'} if CA else {0: '0° N', 90: '90° E', 180: '180° S', 270: '270° W', 360: '360° N'}).get(t, f'{t}°') for t in range(0, 361, 30)], color='#c3c2b7', fontsize=9)
    for t in (0, 90, 180, 270):
        ax.axvline(t, color='#3a3a38', lw=0.6)
    ax.set_title(tit, color='#ffffff', fontsize=11, loc='left', pad=6)
    ax.set_ylabel('r (R☉)', color='#c3c2b7', fontsize=9)
    for s in ax.spines.values(): s.set_color('#383835')
    ax.tick_params(colors='#898781')
axs[2].text(321, np.log10(4.2), 'braç de\nl’ocultador' if CA else 'occulter\npylon', color='#898781', ha='center', va='center', fontsize=9)
axs[2].set_xlabel('angle des del nord solar, cap a l’est (est = 90°)' if CA else 'position angle from solar north, counter-clockwise (east = 90°)', color='#c3c2b7', fontsize=10)
fig.savefig(VISTES / f'FA_desplegat_final_KCor_LASCO_C2{SUF}.png', dpi=110, facecolor=fig.get_facecolor(), bbox_inches='tight')
plt.close(fig)

# ---------------------------------------------------------------- FB: correlació per radi
c2r = json.load(open(RES / 'C2_PERFILS.json'))['resultats']; c3r = json.load(open(RES / 'C3_PERFILS_EUV.json'))['resultats']
def pt(res, key, r1, r2, detall=True):
    d = res[key]; dd = d['passa_alt'] if 'passa_alt' in d else d.get('detall_12')
    if detall:
        rho = dd['rho_0'] if 'rho_0' in dd else dd['pearson']; nul = (dd['nul_mitjana'], dd['nul_sd']) if 'nul_mitjana' in dd else (dd['nul'][0], dd['nul'][1])
    else:
        rho = d['rho_0'] if 'rho_0' in d else d['pearson']; nul = (d['nul_mitjana'], d['nul_sd']) if 'nul_mitjana' in d else (d['nul'][0], d['nul'][1])
    return dict(r=float(np.sqrt(r1 * r2)), r1=r1, r2=r2, rho=float(rho), nul_m=float(nul[0]), nul_sd=float(nul[1]))
series = {
    'final_kcor': [pt(c3r, f'final~kcor_{a:.2f}-{b:.2f}', a, b) for a, b in [(1.10, 1.16), (1.16, 1.22), (1.22, 1.28)]] +
                  [pt(c2r, f'kcor_{a:.2f}-{b:.2f}', a, b) for a, b in [(1.30, 1.50), (1.50, 1.75), (1.75, 1.98)]],
    'final_c2': [pt(c2r, f'c2_1824_{a:.2f}-{b:.2f}', a, b) for a, b in [(2.4, 2.8), (2.8, 3.3), (3.3, 4.0), (4.0, 5.0), (5.0, 6.0)]],
    'final_aia211': [pt(c3r, f'final~aia0211_{a:.2f}-{b:.2f}', a, b) for a, b in [(1.10, 1.16), (1.16, 1.22), (1.22, 1.28)]],
    'kcor_aia211': [pt(c3r, f'kcor~aia0211_{a:.2f}-{b:.2f}', a, b) for a, b in [(1.10, 1.16), (1.16, 1.22), (1.22, 1.28)]],
}
series_tot = {
    'final_kcor': [pt(c3r, f'final~kcor_{a:.2f}-{b:.2f}', a, b, False) for a, b in [(1.10, 1.16), (1.16, 1.22), (1.22, 1.28)]] +
                  [pt(c2r, f'kcor_{a:.2f}-{b:.2f}', a, b, False) for a, b in [(1.30, 1.50), (1.50, 1.75), (1.75, 1.98)]],
    'final_c2': [pt(c2r, f'c2_1824_{a:.2f}-{b:.2f}', a, b, False) for a, b in [(2.4, 2.8), (2.8, 3.3), (3.3, 4.0), (4.0, 5.0), (5.0, 6.0)]],
    'final_aia211': [pt(c3r, f'final~aia0211_{a:.2f}-{b:.2f}', a, b, False) for a, b in [(1.10, 1.16), (1.16, 1.22), (1.22, 1.28)]],
    'kcor_aia211': [pt(c3r, f'kcor~aia0211_{a:.2f}-{b:.2f}', a, b, False) for a, b in [(1.10, 1.16), (1.16, 1.22), (1.22, 1.28)]],
}
json.dump(dict(detall_12=series, perfil_sencer=series_tot), open(RES / 'SERIES_CORRELACIO.json', 'w'), indent=1)

COL = {'final_kcor': '#2a78d6', 'final_c2': '#eb6834', 'final_aia211': '#1baf7a', 'kcor_aia211': '#898781'}
NOM = ({'final_kcor': 'fotografia ↔ K-Cor', 'final_c2': 'fotografia ↔ LASCO C2', 'final_aia211': 'fotografia ↔ SDO/AIA 211 Å', 'kcor_aia211': 'referència: K-Cor ↔ SDO/AIA 211 Å'} if CA else
       {'final_kcor': 'eclipse ↔ K-Cor', 'final_c2': 'eclipse ↔ LASCO C2', 'final_aia211': 'eclipse ↔ SDO/AIA 211 Å', 'kcor_aia211': 'reference: K-Cor ↔ SDO/AIA 211 Å'})
fig, ax = plt.subplots(figsize=(9.5, 5.2), facecolor='#fcfcfb'); ax.set_facecolor('#fcfcfb')
alln = [p for s in series.values() for p in s]
rs = np.array([p['r'] for p in alln]); o = np.argsort(rs)
nm = np.array([p['nul_m'] for p in alln])[o]; ns = np.array([p['nul_sd'] for p in alln])[o]
ax.fill_between(rs[o], nm - 2 * ns, nm + 2 * ns, color='#e1e0d9', lw=0, label='control nul (151 girs regulars de 30° a 330°, ±2σ)' if CA else 'null control (151 regular rotations, 30°–330°, ±2σ)')
for k, s in series.items():
    x = [p['r'] for p in s]; y = [p['rho'] for p in s]
    if k == 'kcor_aia211':
        ax.plot(x, y, color=COL[k], lw=2, marker='o', ms=8, mfc='#fcfcfb', mec=COL[k], mew=2, label=NOM[k], zorder=3)
    else:
        ax.plot(x, y, color=COL[k], lw=2, marker='o', ms=8, mec='#fcfcfb', mew=2, label=NOM[k], zorder=4)
ax.set_xscale('log'); ax.set_xticks([1.1, 1.25, 1.5, 2, 3, 4, 5, 6]); ax.set_xticklabels(['1,1', '1,25', '1,5', '2', '3', '4', '5', '6'] if CA else ['1.1', '1.25', '1.5', '2', '3', '4', '5', '6'])
from matplotlib.ticker import NullFormatter, FuncFormatter
ax.xaxis.set_minor_formatter(NullFormatter())
if CA: ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:.1f}'.replace('.', ',').replace('-', '−')))
ax.set_xlim(1.07, 6.4); ax.set_ylim(-0.45, 1.0)
ax.set_xlabel('distància al centre del Sol (radis solars)' if CA else 'distance from the Sun’s centre (solar radii)', color='#52514e'); ax.set_ylabel('correlació del detall d’angle (passa-alt σ 12°)' if CA else 'correlation of angular detail (high-pass σ 12°)', color='#52514e')
ax.grid(True, color='#e1e0d9', lw=1); ax.set_axisbelow(True)
for s_ in ax.spines.values(): s_.set_color('#c3c2b7')
ax.tick_params(colors='#52514e')
ax.legend(loc='lower left', frameon=False, fontsize=9)
ax.set_title('La fotografia mostra les mateixes estructures que els coronògrafs?' if CA else 'Does the eclipse image show the same structures as the space and ground coronagraphs?', color='#0b0b0b', fontsize=11, loc='left')
fig.savefig(VISTES / f'FB_correlacio_per_radi{SUF}.png', dpi=130, bbox_inches='tight', facecolor=fig.get_facecolor())
print(json.dumps({k: [(round(p['r'], 2), round(p['rho'], 3)) for p in v] for k, v in series.items()}))
