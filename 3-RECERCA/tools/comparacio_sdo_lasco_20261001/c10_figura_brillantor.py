"""c10 · Figura de la brillantor absoluta (de C9_BRILLANTOR.json):
  esquerra: perfil radial (mediana de cada anell, B/B☉): nostra − cel, LASCO C2 (K+F), K-Cor pB i pB/p (p teòric de Baumbach–Allen),
            els punts de research/76 i el nivell del cel de l'eclipsi;
  dreta: el quocient nostra / instrument per anells (pendent de la regressió i quocient de medianes), amb la banda de ±10 % del
         nostre calibratge."""
import json, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from comu_comp import *
d = json.load(open(RES / 'brillantor/C9_BRILLANTOR.json'))
m = d['perfils_mitjans']; r = np.array(m['r'])
nos_tot = np.array(m['nostra_menys_cel'], float)
apc2 = np.array([np.nan if v is None else v for v in m['nostra_aparellada_c2']], float)
appb = np.array([np.nan if v is None else v for v in m['nostra_aparellada_pB']], float)
# revisió 2 de Codex: on hi ha instrument, la nostra corba és la mediana sobre les MATEIXES caselles d'angle que la seva
nos = np.where(np.isfinite(appb), appb, np.where(np.isfinite(apc2), apc2, nos_tot))
c2 = np.array([np.nan if v is None else v for v in m['c2']], float)
pb = np.array([np.nan if v is None else v for v in m['pB']], float)
pt = d['p_teoric_u056']['Baumbach–Allen']; rp = np.array([float(k) for k in pt]); pp = np.array(list(pt.values()))
p_r = np.interp(r, rp, pp)
cel = d['cel_BBsol_al_centre']
r76 = (np.array([1.10, 1.50, 2.00, 3.00, 5.00]) + 0.01) * 959.0 / GEO['R_sol_arcsec']   # research/76 feia servir R☉ = 959″
b76 = np.array([47766, 4937, 809, 175, 37]) * 2.772e-11
INK, INK2, MUTED, GRID, AX, SURF = '#0b0b0b', '#52514e', '#898781', '#e1e0d9', '#c3c2b7', '#fcfcfb'
C_NOS, C_C2, C_KC = '#a86c12', '#eb6834', '#2a78d6'
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.2), facecolor=SURF, gridspec_kw=dict(width_ratios=[1.25, 1], wspace=0.28))
for ax in (a1, a2):
    ax.set_facecolor(SURF); ax.grid(True, color=GRID, lw=1); ax.set_axisbelow(True)
    for s_ in ax.spines.values(): s_.set_color(AX)
    ax.tick_params(colors=INK2)
a1.axhline(cel, color=MUTED, lw=1.2); a1.text(5.6, cel * 1.12, 'cel de l’eclipsi', color=MUTED, ha='right', fontsize=9)
a1.plot(r, nos, color=C_NOS, lw=2.2, label='fotografia − cel (calibratge propi; mateixos angles que l’instrument)')
a1.plot(r, c2, color=C_C2, lw=2, marker='o', ms=5, mec=SURF, label='SOHO/LASCO C2 (K + F)')
a1.plot(r, pb / p_r, color=C_KC, lw=2, marker='o', ms=5, mec=SURF, label='K-Cor pB / p teòric (corona K)')
a1.plot(r, pb, color=C_KC, lw=1.2, alpha=0.55, label='K-Cor pB tal qual')
a1.plot(r76, b76, ls='none', marker='s', ms=6, mfc=SURF, mec=INK2, mew=1.5, label='perfil de referència del 16-08 (anells)')
a1.set_xscale('log'); a1.set_yscale('log'); a1.set_xlim(1.07, 6.0); a1.set_ylim(3e-10, 3e-6)
a1.set_xticks([1.1, 1.25, 1.5, 2, 3, 4, 5]); a1.set_xticklabels(['1,1', '1,25', '1,5', '2', '3', '4', '5'])
a1.set_xlabel('distància al centre del Sol (radis solars)', color=INK2); a1.set_ylabel('brillantor (B/B☉, mediana de l’anell)', color=INK2)
a1.legend(frameon=False, fontsize=8.5, loc='lower left')
a1.set_title('Brillantor de la corona', color=INK, fontsize=11, loc='left')
# quocients
kc = d['anells_kcor']; cc = d['anells_c2']
def mid(k): a, b = map(float, k.split('-')); return np.sqrt(a * b)
rk = np.array([mid(k) for k in kc]); gk = np.array([v['f'] for v in kc.values()]); ek = np.array([v['f_err'] for v in kc.values()])
pk = np.interp(rk, rp, pp)
qk_med = np.array([v['mediana_nostra_menys_cel'] / (v['mediana_pB'] / np.interp(mid(k), rp, pp)) for k, v in kc.items()])
rc = np.array([mid(k) for k in cc]); fc = np.array([v['f'] for v in cc.values()]); ec = np.array([v['f_err'] for v in cc.values()])
qc_med = np.array([v['mediana_nostra_menys_cel'] / v['mediana_C2'] for v in cc.values()])
a2.axhspan(0.9, 1.1, color=GRID, lw=0, label='±10 % (el nostre calibratge)')
a2.axhline(1.0, color=AX, lw=1)
a2.errorbar(rk, gk * pk, yerr=ek * pk, fmt='o', color=C_KC, ms=7, mec=SURF, capsize=0, lw=1.5, label='K-Cor: pendent × p teòric')
a2.plot(rk, qk_med, ls='none', marker='o', ms=7, mfc=SURF, mec=C_KC, mew=2, label='K-Cor: quocient de medianes')
a2.errorbar(rc, fc, yerr=ec, fmt='o', color=C_C2, ms=7, mec=SURF, capsize=0, lw=1.5, label='LASCO C2: pendent de la regressió')
a2.plot(rc, qc_med, ls='none', marker='o', ms=7, mfc=SURF, mec=C_C2, mew=2, label='LASCO C2: quocient de medianes')
a2.set_xscale('log'); a2.set_xlim(1.07, 6.0); a2.set_ylim(0.0, 3.5)
a2.set_xticks([1.1, 1.25, 1.5, 2, 3, 4, 5]); a2.set_xticklabels(['1,1', '1,25', '1,5', '2', '3', '4', '5'])
a2.set_xlabel('distància al centre del Sol (radis solars)', color=INK2); a2.set_ylabel('fotografia / instrument', color=INK2)
a2.legend(frameon=False, fontsize=8.5, loc='upper left')
a2.set_title('Quocient', color=INK, fontsize=11, loc='left')
for ax in (a1, a2): ax.xaxis.set_minor_formatter(NullFormatter())
fig.savefig(VISTES / 'FC_brillantor_absoluta.png', dpi=130, bbox_inches='tight', facecolor=SURF)
print('K-Cor g·p:', np.round(gk * pk, 3), ' medianes:', np.round(qk_med, 3))
print('C2 f:', np.round(fc, 3), ' medianes:', np.round(qc_med, 3))
