"""cv4_5 (12-10, de cv3_5): mida real d'impressió (142 × 118 mm, el text surt 1:1), llegenda amb fons blanc i rètols planers (verificador de normes del paper). Abans, cv3_5: banda del quocient corregida [1/(1+σ_hi), 1/(1−σ_lo)] · Figura v2 per a l'article (12-10-2026): fig_msb_profile_v2.{png,svg,pdf}, 166 mm a 300 ppp, fons blanc, rètols en anglès.

Panell de dalt (log-log): la nostra mediana azimutal v2 (tots els angles vàlids; perfil_azimutal_v2.csv, des d'1,155 R☉, sense anells
parcials) amb la banda sistemàtica 1σ asimètrica (SIGMA_SYS_LO/HI; NO porta la llum difusa, el calibratge de la segona càmera ni el
biaix del cel d'un sol sentit) i el rang 10–90 % dels sectors de 10°; el K-Cor (pB/p + F) NOMÉS fins a 1,7 R☉, amb la banda de
3 densitats × 2 models de F × F de 0,5 a 1,5; el C2 amb els dos calibratges (sense preferència); el cel. Per a cada instrument, la
NOSTRA mediana sobre les MATEIXES caselles d'1° (línia discontínua fina). Franja lunar ombrejada en dos tons (a tots els angles /
només a alguns).
Panell de baix: quocient de medianes sobre les caselles aparellades per anell fi, amb la nostra sistemàtica al voltant d'1.
Escriu v2/comparacions/fig_msb_profile_v2.{png,svg,pdf} i FIGURA_v2.json."""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv2_comu as cv   # noqa: E402

mc, m2, cc1 = cv.mc, cv.m2, cv.cc1
T0 = time.time()
N = np.load(cv.RES2 / 'caselles_v2.npz')
C2 = np.load(cv.RES2 / 'lasco' / 'c2_caselles_v2.npz')
FIGR = [tuple(a) for a in N['fig_anells']]
rmid = np.array([0.5 * (a + b) for a, b in FIGR])
use = N['fig_usable']
ours_bins = N['fig_msb']

# ---------------------------------------------------------------- nostra (tots els angles)
AZ = pd.read_csv(m2.MAPA2 / 'perfils' / 'perfil_azimutal_v2.csv')
FR = json.load(open(m2.MAPA2 / 'perfils' / 'perfils_msb_v2.json'))['franja_lunar']
R_BAND_ALL, R_BAND_SOME = float(FR['r_vora_min_mesurat_Rsol']), float(FR['r_vora_max_mesurat_Rsol'])
AZ = AZ[(AZ.r_in >= R_BAND_SOME - 1e-9) & ~AZ.partial_ring_lunar_band.astype(bool) & np.isfinite(AZ.MSB_median) & (AZ.r_mid <= 6.0)
        & (AZ.sectors_10deg_covered >= 30)]
r_n = AZ.r_mid.values; m_n = AZ.MSB_median.values
lo_n = m_n - AZ.sigma_sys_lo_median.values; hi_n = m_n + AZ.sigma_sys_hi_median.values
SEC = pd.read_csv(m2.MAPA2 / 'perfils' / 'perfil_sectors_10graus_v2.csv')
p10, p90 = [], []
for _, row in AZ.iterrows():
    s = SEC[(np.isclose(SEC.r_in, row.r_in)) & (SEC.n_px >= 20)].MSB_median.values
    s = s[np.isfinite(s)]
    p10.append(np.percentile(s, 10)); p90.append(np.percentile(s, 90))
p10 = np.array(p10); p90 = np.array(p90)
sky_n = AZ.sky_Bsun_median.values
rel_lo = AZ.sigma_sys_lo_median.values / m_n; rel_hi = AZ.sigma_sys_hi_median.values / m_n

# ---------------------------------------------------------------- K-Cor als anells fins (1,15–1,72)
ref = np.mean([cc1.carrega_kcor(s)[0] for s in cc1.KCOR_TOT], axis=0)
g = cc1.carrega_kcor(cc1.KCOR_TOT[0])[1]
yy, xx = np.mgrid[0:ref.shape[0], 0:ref.shape[1]].astype(np.float64)
rK, paK = g.polar(xx, yy)
dins = (rK > 1.04) & (rK < 2.6)
FK = {'vdH1950': cc1.f_vdh1950(rK), 'KL1985': np.full_like(rK, np.nan)}
FK['KL1985'][dins] = cc1.f_kl1985(rK[dins], paK[dins])
k_sel = [i for i, (a, b) in enumerate(FIGR) if b <= 1.72 and a >= R_BAND_SOME - 1e-9]
AK = [FIGR[i] for i in k_sel]
kc_med, kc_q = {}, {}
our_k = np.full(len(k_sel), np.nan)
for nomp in cc1.MODELS_DENSITAT:
    p = cc1.p_de_r(rK, nomp)
    for nomf, F in FK.items():
        for s in (0.5, 1.0, 1.5):
            _, q, _ = cc1.caselles_imatge(ref / p + s * F, g, AK)
            med, qq = [], []
            for j, i in enumerate(k_sel):
                ok = use[i] & np.isfinite(q[50][j]) & np.isfinite(ours_bins[i])
                if ok.sum() < 60:
                    med.append(np.nan); qq.append(np.nan); continue
                med.append(np.median(q[50][j][ok])); qq.append(np.median(ours_bins[i][ok]) / np.median(q[50][j][ok]))
                if (nomp, nomf, s) == ('Baumbach-Allen', 'vdH1950', 1.0):
                    our_k[j] = np.median(ours_bins[i][ok])
            kc_med[(nomp, nomf, s)] = np.array(med); kc_q[(nomp, nomf, s)] = np.array(qq)
k_mid = kc_med[('Baumbach-Allen', 'vdH1950', 1.0)]
k_lo = np.nanmin(np.vstack(list(kc_med.values())), axis=0); k_hi = np.nanmax(np.vstack(list(kc_med.values())), axis=0)
kq_mid = kc_q[('Baumbach-Allen', 'vdH1950', 1.0)]
kq_lo = np.nanmin(np.vstack(list(kc_q.values())), axis=0); kq_hi = np.nanmax(np.vstack(list(kc_q.values())), axis=0)
r_k = rmid[k_sel]

# ---------------------------------------------------------------- C2 als anells fins (≥ 2,4 R☉)
c2u = C2['fig_usable']
c2, c2q, our_c2 = {}, {}, np.full(len(FIGR), np.nan)
for nc in ('SolarSoft_c2_calfactor', 'Colaninno_Howard_2015_eq8'):
    v = C2[f'fig_{nc}']
    med, qq = [], []
    for i in range(len(FIGR)):
        ok = c2u[i] & np.isfinite(v[i]) & np.isfinite(ours_bins[i]) & (v[i] > 0)
        if FIGR[i][0] < 2.40 or ok.sum() < 60:
            med.append(np.nan); qq.append(np.nan); continue
        med.append(np.median(v[i][ok])); qq.append(np.median(ours_bins[i][ok]) / np.median(v[i][ok]))
        our_c2[i] = np.median(ours_bins[i][ok])
    c2[nc] = np.array(med); c2q[nc] = np.array(qq)

# nostra mediana sobre les caselles de cada instrument contra la nostra mediana sobre totes les caselles usables del mateix anell fi
tots = np.array([np.median(ours_bins[i][use[i] & np.isfinite(ours_bins[i])]) if (use[i] & np.isfinite(ours_bins[i])).sum() >= 60 else np.nan
                 for i in range(len(FIGR))])
dif_k = our_k / tots[k_sel] - 1; dif_c2 = our_c2 / tots - 1
print('caselles K-Cor contra totes: màx |dif|', np.nanmax(np.abs(dif_k)), '; C2:', np.nanmax(np.abs(dif_c2)), flush=True)

# ---------------------------------------------------------------- figura
import matplotlib   # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt   # noqa: E402
from matplotlib.ticker import FixedLocator, NullFormatter, NullLocator   # noqa: E402
from matplotlib.lines import Line2D   # noqa: E402
from matplotlib.patches import Patch   # noqa: E402
plt.rcParams.update({'font.family': 'Avenir Next', 'svg.fonttype': 'path', 'pdf.fonttype': 42, 'font.size': 7.6, 'axes.edgecolor': '#9a9994',
                     'axes.linewidth': 0.6, 'xtick.color': '#52514e', 'ytick.color': '#52514e', 'axes.labelcolor': '#52514e', 'text.color': '#0b0b0b'})
BLUE, ORANGE, AMBRE, AMBRE_CLAR, INK, INK2, GRIS = '#2a78d6', '#eb6834', '#a9691b', '#f4ead9', '#0b0b0b', '#52514e', '#9a9994'
W_MM, H_MM = 142.0, 134.0
fig, (ax, bx) = plt.subplots(2, 1, figsize=(W_MM / 25.4, H_MM / 25.4), sharex=True, gridspec_kw=dict(height_ratios=[2.35, 1.0], hspace=0.06))
for a_ in (ax, bx):
    for s_ in ('top', 'right'):
        a_.spines[s_].set_visible(False)
    a_.set_xscale('log')
    a_.axvspan(1.0, R_BAND_ALL, color='#dedcd6', lw=0, zorder=0)
    a_.axvspan(R_BAND_ALL, R_BAND_SOME, color='#eeede9', lw=0, zorder=0)
ax.set_yscale('log'); ax.set_xlim(1.0, 6.2); ax.set_ylim(1.5e-10, 4e-6)
ax.grid(axis='y', which='major', color='#e4e3df', lw=0.6); ax.set_axisbelow(True)
ax.text(0.5 * (1.0 + R_BAND_SOME) - 0.003, 1.2e-8, 'Moon and lunar-motion band: no single-instant data', fontsize=6.2, color=INK2,
        rotation=90, va='center', ha='center')
# nostra
ax.fill_between(r_n, np.clip(lo_n, 1e-12, None), hi_n, color=AMBRE_CLAR, lw=0, zorder=1)
ax.plot(r_n, np.clip(p10, 1e-12, None), color=AMBRE, lw=0.5, alpha=0.85, zorder=2)
ax.plot(r_n, p90, color=AMBRE, lw=0.5, alpha=0.85, zorder=2)
ax.plot(r_n, m_n, color=AMBRE, lw=1.8, solid_capstyle='round', zorder=5)
ax.plot(r_k, our_k, color=AMBRE, lw=0.9, ls=(0, (2.5, 1.5)), zorder=7)
ax.plot(rmid, our_c2, color=AMBRE, lw=0.9, ls=(0, (2.5, 1.5)), zorder=7)
# K-Cor
ax.fill_between(r_k, k_lo, k_hi, color=BLUE, alpha=0.20, lw=0, zorder=3)
ax.plot(r_k, k_mid, color=BLUE, lw=1.3, zorder=6)
# C2
ax.plot(rmid, c2['Colaninno_Howard_2015_eq8'], color=ORANGE, lw=1.3, zorder=6)
ax.plot(rmid, c2['SolarSoft_c2_calfactor'], color=ORANGE, lw=1.1, ls=(0, (4, 2)), zorder=6)
# cel
ax.plot(r_n, sky_n, color=GRIS, lw=1.0, ls=(0, (1, 2)), zorder=4)
ax.set_ylabel('Brightness (mean solar brightness, B/B$_\\odot$)')
ax.yaxis.set_minor_formatter(NullFormatter())
H = [Line2D([], [], color=AMBRE, lw=1.8), Patch(color=AMBRE_CLAR, lw=0), Line2D([], [], color=AMBRE, lw=0.5),
     Line2D([], [], color=AMBRE, lw=0.9, ls=(0, (2.5, 1.5))),
     (Patch(color=BLUE, alpha=0.20, lw=0), Line2D([], [], color=BLUE, lw=1.3)),
     Line2D([], [], color=ORANGE, lw=1.3), Line2D([], [], color=ORANGE, lw=1.1, ls=(0, (4, 2))),
     Line2D([], [], color=GRIS, lw=1.0, ls=(0, (1, 2)))]
L = ['This work: median total brightness (K+F)',
     'This work: 1σ systematic (see caption)',
     'This work: 10–90 % range of 10° sectors',
     'This work: median over the bins of each instrument',
     'K-Cor as total brightness (band: models)',
     'LASCO C2, Colaninno & Howard (2015)',
     'LASCO C2, SolarSoft calibration',
     'Sky during totality (subtracted)']
fig.legend(H, L, loc='lower center', ncol=2, frameon=False, fontsize=6.6, handlelength=2.2, columnspacing=1.6, labelspacing=0.45, bbox_to_anchor=(0.54, 0.0), labelcolor=INK2)  # fora dels eixos: no tapa cap dada
# v3: sense títol intern; el peu de l'article fa de títol
# panell de baix: quocients sobre caselles aparellades
bx.fill_between(r_n, 1 / (1 + rel_hi), np.where(rel_lo < 0.99, 1 / np.clip(1 - rel_lo, 0.01, None), 10.0), color=AMBRE_CLAR, lw=0, zorder=1)  # v3: compatibilitat d'un quocient nostra/instrument a 1σ = [1/(1+σ_hi), 1/(1−σ_lo)] (re-verificador, 12-10)
bx.axhline(1.0, color=GRIS, lw=0.6, zorder=2)
bx.fill_between(r_k, kq_lo, kq_hi, color=BLUE, alpha=0.20, lw=0, zorder=3)
bx.plot(r_k, kq_mid, color=BLUE, lw=1.3, zorder=6)
bx.plot(rmid, c2q['Colaninno_Howard_2015_eq8'], color=ORANGE, lw=1.3, zorder=6)
bx.plot(rmid, c2q['SolarSoft_c2_calfactor'], color=ORANGE, lw=1.1, ls=(0, (4, 2)), zorder=6)
bx.set_ylim(0.4, 2.0)
bx.set_ylabel('This work / instrument\n(same 1° bins)')
bx.set_xlabel('Distance from the Sun’s centre (solar radii)')
bx.xaxis.set_major_locator(FixedLocator([1, 1.5, 2, 3, 4, 5, 6])); bx.xaxis.set_minor_locator(NullLocator())
bx.set_xticklabels(['1', '1.5', '2', '3', '4', '5', '6'])
bx.yaxis.set_major_locator(FixedLocator([0.5, 1.0, 1.5, 2.0]))
for a_ in (ax, bx):
    a_.tick_params(length=2.5, width=0.6, which='both')
fig.subplots_adjust(left=0.105, right=0.985, top=0.975, bottom=0.235)
OUTF = cv.RES2 / 'fig_msb_profile_v4'
fig.savefig(str(OUTF) + '.png', dpi=300, facecolor='white')
fig.savefig(str(OUTF) + '.svg', facecolor='white')
fig.savefig(str(OUTF) + '.pdf', facecolor='white')
plt.close(fig)
from PIL import Image   # noqa: E402
im = Image.open(str(OUTF) + '.png')
cv.json_dump(dict(guio=cv.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'), mida_px=im.size, mida_mm=[W_MM, H_MM], dpi=300,
                  nostra=dict(r=r_n, mediana=m_n, sigma_sys_lo=AZ.sigma_sys_lo_median.values, sigma_sys_hi=AZ.sigma_sys_hi_median.values,
                              p10_sectors=p10, p90_sectors=p90, cel=sky_n),
                  nostra_caselles_kcor=dict(r=r_k, mediana=our_k, dif_rel_contra_totes_les_caselles=dif_k),
                  nostra_caselles_c2=dict(r=rmid, mediana=our_c2, dif_rel_contra_totes_les_caselles=dif_c2),
                  nostra_totes_les_caselles_anells_fins=dict(r=rmid, mediana=tots),
                  kcor=dict(r=r_k, baumbach_allen_vdH=k_mid, min=k_lo, max=k_hi, quocient=kq_mid, quocient_min=kq_lo, quocient_max=kq_hi),
                  c2=dict(r=rmid, **{k: v for k, v in c2.items()}, **{f'quocient_{k}': v for k, v in c2q.items()}),
                  franja_lunar_R_sol=dict(a_tots_els_angles=[1.0, R_BAND_ALL], a_alguns_angles=[R_BAND_ALL, R_BAND_SOME]),
                  entrades_sha256={cv.rel(p): cv.sha256(p) for p in (m2.MAPA2 / 'perfils' / 'perfil_azimutal_v2.csv',
                                                                     m2.MAPA2 / 'perfils' / 'perfil_sectors_10graus_v2.csv',
                                                                     m2.MAPA2 / 'perfils' / 'perfils_msb_v2.json',
                                                                     cv.RES2 / 'caselles_v2.npz', cv.RES2 / 'lasco' / 'c2_caselles_v2.npz')}),
             cv.RES2 / 'FIGURA_v4.json')
print('mida', im.size, f'fet ({time.time() - T0:.0f} s)')
