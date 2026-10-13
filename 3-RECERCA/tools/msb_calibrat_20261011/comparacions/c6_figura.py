"""c6 · Comparació E: figura per a l'article (rètols en anglès, fons blanc, estil del whitepaper: Avenir Next, tinta #0b0b0b/#52514e,
blau #2a78d6, taronja #eb6834, ambre #a9691b). 166 mm d'amplada, PNG a 300 ppp + SVG + PDF. Encàrrec «comparacions», 11-10-2026.

Corbes (totes medianes azimutals; les dels instruments, sobre les caselles d'1° aparellades amb la nostra dada vàlida):
  - nostra MSB total (mapa/perfils/perfil_azimutal.csv), amb el rang 10–90 % dels sectors de 10° i la banda sistemàtica (± SIGMA_SYS);
  - K-Cor: pB/p + F (mitjana dels 7 fotogrames de la totalitat); línia = Baumbach–Allen + van de Hulst 1950; banda = els 3 models de p ×
    els 2 models de F; només fins a 1,7 R☉ (més enllà, el pB L2 d'aquell dia té un residu negatiu del cel; vegeu KCOR.json);
  - LASCO C2 (mitjana de 18:24:31 i 18:36:15), els dos calibratges;
  - el cel (model adoptat, verd de càmera, sense corregir l'extinció);
  - la franja del moviment lunar, ombrejada: «no single-instant data».
Escriu comparacions/fig_msb_profile.{png,svg,pdf} i FIGURA.json (les dades de cada corba)."""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cmp_comu as cc   # noqa: E402

mc = cc.mc
T0 = time.time()
N = np.load(cc.RES / 'caselles_nostra.npz')
C2 = np.load(cc.RES / 'lasco/c2_caselles.npz')
FIGR = [tuple(a) for a in N['fig_anells']]
rmid = np.array([0.5 * (a + b) for a, b in FIGR])
use = N['fig_usable']

# ---------------------------------------------------------------- nostra
AZ = pd.read_csv(mc.MAPA / 'perfils/perfil_azimutal.csv')
SEC = pd.read_csv(mc.MAPA / 'perfils/perfil_sectors_10graus.csv')
AZ = AZ[(AZ.sectors_10deg_covered >= 30) & np.isfinite(AZ.MSB_median) & (AZ.r_mid <= 6.0)]
r_n = AZ.r_mid.values; m_n = AZ.MSB_median.values; s_n = AZ.sigma_sys_median.values
p10, p90 = [], []
for _, row in AZ.iterrows():
    s = SEC[(SEC.r_in == row.r_in) & (SEC.n_px >= 20)].MSB_median.values
    s = s[np.isfinite(s)]
    p10.append(np.percentile(s, 10)); p90.append(np.percentile(s, 90))
p10 = np.array(p10); p90 = np.array(p90)
sky_n = AZ.sky_Bsun_median.values

# ---------------------------------------------------------------- K-Cor pB/p + F als anells fins (r < 1,7)
ref = np.mean([cc.carrega_kcor(s)[0] for s in cc.KCOR_TOT], axis=0)
g = cc.carrega_kcor(cc.KCOR_TOT[0])[1]
yy, xx = np.mgrid[0:ref.shape[0], 0:ref.shape[1]].astype(np.float64)
rK, paK = g.polar(xx, yy)
dins = (rK > 1.04) & (rK < 2.6)
FK = {'vdH1950': cc.f_vdh1950(rK), 'KL1985': np.full_like(rK, np.nan)}
FK['KL1985'][dins] = cc.f_kl1985(rK[dins], paK[dins])
k_sel = [i for i, (a, b) in enumerate(FIGR) if b <= 1.72 and a >= 1.15]
AK = [FIGR[i] for i in k_sel]
kc = {}
for nomp in cc.MODELS_DENSITAT:
    p = cc.p_de_r(rK, nomp)
    for nomf, F in FK.items():
        _, q, _ = cc.caselles_imatge(ref / p + F, g, AK)
        kc[(nomp, nomf)] = np.array([np.nanmedian(np.where(use[i], q[50][j], np.nan)) if use[i].sum() >= 60 else np.nan
                                     for j, i in enumerate(k_sel)])
k_mid = kc[('Baumbach-Allen', 'vdH1950')]
k_lo = np.nanmin(np.vstack(list(kc.values())), axis=0); k_hi = np.nanmax(np.vstack(list(kc.values())), axis=0)
r_k = rmid[k_sel]

# ---------------------------------------------------------------- C2
c2u = C2['fig_usable']
c2 = {}
for nc in ('SSW_c2_calfactor', 'Colaninno_Howard_2015_eq8'):
    v = C2[f'fig_{nc}']
    c2[nc] = np.array([np.nanmedian(np.where(c2u[i], v[i], np.nan)) if (FIGR[i][0] >= 2.40 and c2u[i].sum() >= 60) else np.nan for i in range(len(FIGR))])

# ---------------------------------------------------------------- figura
import matplotlib   # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt   # noqa: E402
from matplotlib.ticker import FixedLocator, NullFormatter, NullLocator   # noqa: E402
plt.rcParams.update({'font.family': 'Avenir Next', 'svg.fonttype': 'path', 'pdf.fonttype': 42, 'font.size': 8.0, 'axes.edgecolor': '#9a9994',
                     'axes.linewidth': 0.6, 'xtick.color': '#52514e', 'ytick.color': '#52514e', 'axes.labelcolor': '#52514e', 'text.color': '#0b0b0b'})
BLUE, ORANGE, AMBRE, AMBRE_CLAR, INK, INK2, GRIS = '#2a78d6', '#eb6834', '#a9691b', '#f4ead9', '#0b0b0b', '#52514e', '#9a9994'
W_MM, H_MM = 166.0, 100.0
fig, ax = plt.subplots(figsize=(W_MM / 25.4, H_MM / 25.4))
for s_ in ('top', 'right'):
    ax.spines[s_].set_visible(False)
ax.set_xscale('log'); ax.set_yscale('log')
ax.set_xlim(1.0, 6.2); ax.set_ylim(1.5e-10, 4e-6)
ax.grid(axis='y', which='major', color='#e4e3df', lw=0.6); ax.set_axisbelow(True)
# franja lunar
r_band_lo = (mc.R_BANDA_PX - 40 - np.hypot(mc.LLUNA_XY[0] - mc.SOL_XY[0], mc.LLUNA_XY[1] - mc.SOL_XY[1])) / mc.RSOL_PX
r_band_hi = (mc.R_BANDA_PX + np.hypot(mc.LLUNA_XY[0] - mc.SOL_XY[0], mc.LLUNA_XY[1] - mc.SOL_XY[1])) / mc.RSOL_PX
ax.axvspan(1.0, r_band_hi, color='#ecebe6', lw=0, zorder=0)
ax.text(0.5 * (1.0 + r_band_hi) - 0.004, 2.4e-8, 'Moon and lunar-motion band: no single-instant data', fontsize=6.4, color=INK2,
        rotation=90, va='center', ha='center')
# nostra
lo_sys = np.where(m_n - s_n > 0, m_n - s_n, 1e-12)
ax.fill_between(r_n, lo_sys, m_n + s_n, color=AMBRE_CLAR, lw=0, zorder=1)
ax.plot(r_n, np.clip(p10, 1e-12, None), color=AMBRE, lw=0.55, alpha=0.9, zorder=2, label='This work: 10\u201390 % range of 10° sectors')
ax.plot(r_n, p90, color=AMBRE, lw=0.55, alpha=0.9, zorder=2)
ax.plot(r_n, m_n, color=AMBRE, lw=1.8, solid_capstyle='round', zorder=5, label='This work: total brightness K+F, azimuthal median (camera green, sky subtracted)')
ax.fill_between([], [], [], color=AMBRE_CLAR, lw=0, label='This work: systematic uncertainty (1\u03c3)')
# K-Cor
ax.fill_between(r_k, k_lo, k_hi, color=BLUE, alpha=0.18, lw=0, zorder=3)
ax.plot(r_k, k_mid, color=BLUE, lw=1.4, zorder=6, label='K-Cor pB / p(r) + F-corona model (band: 3 density \u00d7 2 F models)')
# C2
ax.plot(rmid, c2['Colaninno_Howard_2015_eq8'], color=ORANGE, lw=1.4, zorder=6, label='LASCO C2 total brightness, Colaninno & Howard (2015) calibration')
ax.plot(rmid, c2['SSW_c2_calfactor'], color=ORANGE, lw=1.1, ls=(0, (4, 2)), zorder=6, label='LASCO C2 total brightness, SolarSoft calibration')
# cel
ax.plot(r_n, sky_n, color=GRIS, lw=1.0, ls=(0, (1, 2)), zorder=4, label='Sky brightness during totality (camera green)')
ax.set_xlabel('Distance from the Sun’s centre (solar radii)')
ax.set_ylabel('Brightness (mean solar brightness, B/B$_\\odot$)')
ax.xaxis.set_major_locator(FixedLocator([1, 1.5, 2, 3, 4, 5, 6])); ax.xaxis.set_minor_locator(NullLocator())
ax.set_xticklabels(['1', '1.5', '2', '3', '4', '5', '6'])
ax.tick_params(length=2.5, width=0.6, which='both')
ax.yaxis.set_minor_formatter(NullFormatter())
hh, ll = ax.get_legend_handles_labels()
ordre = [1, 0, 2, 3, 4, 5, 6]
leg = ax.legend([hh[i] for i in ordre], [ll[i] for i in ordre], loc='upper right', frameon=False, fontsize=6.9, handlelength=2.2,
                borderaxespad=0.3, labelcolor=INK2)
ax.set_title('The 12 August 2026 corona in mean solar brightness', loc='left', fontsize=9.2, fontweight='demibold', pad=6)
fig.tight_layout(pad=0.4)
OUTF = cc.RES / 'fig_msb_profile'
fig.savefig(str(OUTF) + '.png', dpi=300, facecolor='white')
fig.savefig(str(OUTF) + '.svg', facecolor='white')
fig.savefig(str(OUTF) + '.pdf', facecolor='white')
plt.close(fig)
from PIL import Image   # noqa: E402
im = Image.open(str(OUTF) + '.png')
json.dump(dict(guio=cc.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'), mida_px=im.size, mida_mm=[W_MM, H_MM], dpi=300,
               nostra=dict(r=r_n.tolist(), mediana=m_n.tolist(), sigma_sys=s_n.tolist(), p10_sectors=p10.tolist(), p90_sectors=p90.tolist(), cel=sky_n.tolist()),
               kcor=dict(r=r_k.tolist(), baumbach_allen_vdH=k_mid.tolist(), min=k_lo.tolist(), max=k_hi.tolist()),
               c2=dict(r=rmid.tolist(), **{k: v.tolist() for k, v in c2.items()}),
               franja_lunar_R_sol=[1.0, float(r_band_hi)],
               entrades_sha256={cc.rel(mc.MAPA / 'perfils/perfil_azimutal.csv'): cc.sha256(mc.MAPA / 'perfils/perfil_azimutal.csv'),
                                cc.rel(mc.MAPA / 'perfils/perfil_sectors_10graus.csv'): cc.sha256(mc.MAPA / 'perfils/perfil_sectors_10graus.csv'),
                                cc.rel(cc.RES / 'caselles_nostra.npz'): cc.sha256(cc.RES / 'caselles_nostra.npz'),
                                cc.rel(cc.RES / 'lasco/c2_caselles.npz'): cc.sha256(cc.RES / 'lasco/c2_caselles.npz')}),
          open(cc.RES / 'FIGURA.json', 'w'), indent=1, default=float)
print('mida', im.size, f'fet ({time.time() - T0:.0f} s)')
