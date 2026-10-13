"""Figura dels punts zero per canal (etiquetes en anglès): V − m_c corregit de massa d'aire
contra (B−V), amb la recta ajustada, i residus contra (B−V) (el control nul).
Llegeix ZP_CANAL.json i work/canal/zp_canal_per_estrella.csv. Sortida:
resultats/msb_calibrat_20261011/zp_canal/fig_zp_canal.png
"""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI / "original"))
import comu  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RES = comu.ARREL / "3-RECERCA/resultats/msb_calibrat_20261011/zp_canal"


def main():
    z = json.load(open(RES / 'ZP_CANAL.json'))
    d = pd.read_csv(comu.work('canal') / 'zp_canal_per_estrella.csv')
    col = {'R': '#c0392b', 'G': '#2e8b57', 'B': '#2c5aa0'}
    fig, ax = plt.subplots(2, 3, figsize=(13, 7.5), sharex=True)
    bv = np.linspace(-0.2, 1.7, 50)
    for j, ch in enumerate('RGB'):
        C = z['canals'][ch]
        key = f'{ch}_interp'
        y = d.V - d[f'minst_{key}'] + C['k']*d.dX          # corrected to X_sun
        used = d[f'usada_{key}'].astype(bool)
        a = ax[0, j]
        a.plot(d.BV[used], y[used], 'o', color=col[ch], label=f'used (n={used.sum()})')
        a.plot(d.BV[~used], y[~used], 'x', color='0.4', label='clipped / no photometry')
        a.plot(bv, C['ZP'] - C['c']*bv, '-', color='k', lw=1)
        a.axvline(0.653, color='orange', lw=1, ls='--')
        a.plot([0.653], [C['m_sol']], 's', color='orange', ms=7, label='Sun colour (B−V = 0.653)')
        perm = z['controls_nuls'][ch]['permutacio_terme_color']['p_bilateral']
        a.set_title(f"{ch}: ZP={C['ZP']:+.3f}, c={C['c']:+.3f}±{C['ec']:.3f} (perm. p={perm:.2f})\n"
                    f"rms={C['rms']:.3f}, fac={C['fac']:.3e} B/B☉ per ADU/s/px", fontsize=9)
        a.set_ylabel('V − m_inst + k(X − X☉)  [mag]')
        lo, hi = np.nanpercentile(y[used], [0, 100])
        a.set_ylim(lo - 1.0, hi + 1.0)
        a.legend(fontsize=7, loc='lower left')
        b = ax[1, j]
        r = d[f'resid_{key}']
        b.plot(d.BV[used], r[used], 'o', color=col[ch])
        b.plot(d.BV[~used], r[~used], 'x', color='0.4')
        b.axhline(0, color='k', lw=0.8)
        q = z['controls_nuls'][ch]['terme_quadratic_BV2']
        sp = z['controls_nuls'][ch]['spearman_residu_vs_BV']
        b.set_title(f"residuals: (B−V)² term t={q['t']:+.2f}; Spearman ρ={sp['rho']:+.2f}, p={sp['p']:.2f}",
                    fontsize=9)
        b.set_ylim(-1.0, 1.0)
        b.set_xlabel('catalogue B − V  [mag]')
        b.set_ylabel('residual [mag]')
    fig.suptitle('Vixen VSD90SS + Canon R6 III field stars, 12 Aug 2026 (X☉ = 6.02): per-channel zero points '
                 '(same method as the green ZP; clipped points outside ±1 mag not shown)', fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(RES / 'fig_zp_canal.png', dpi=130)
    print(RES / 'fig_zp_canal.png')


if __name__ == '__main__':
    main()
