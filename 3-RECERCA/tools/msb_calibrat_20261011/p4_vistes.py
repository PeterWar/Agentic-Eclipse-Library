"""p4 · Vistes del mapa MSB per inspeccionar-lo (11-10-2026). Llenç SENCER (la graella 2×2 del FITS, 5276 × 3753), sense retalls.
Escriu mapa/vistes/*.png. Rètols en anglès (poden sortir del projecte amb el sí de Pere)."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits
from matplotlib.colors import ListedColormap, Normalize

sys.path.insert(0, str(Path(__file__).resolve().parent))
import msb_comu as mc

OUT = mc.MAPA / 'vistes'; OUT.mkdir(parents=True, exist_ok=True)
with fits.open(mc.MAPA / 'msb_mapa_2x2.fits') as hl:
    P = {h.name: np.asarray(h.data) for h in hl}
Hb, Wb = P['PRIMARY'].shape
g = mc.geo_llenc()
PAZ = json.load(open(mc.MAPA / 'PROVES_P0.json'))['zenit']['r1']['PA_solar_del_zenit']
STRIP = 420


def a_agrupat(x, y):
    return (np.asarray(x) - 0.5) / 2, (np.asarray(y) - 0.5) / 2


def figura(titol, subtitol):
    fig = plt.figure(figsize=(Wb / 100, (Hb + STRIP) / 100), dpi=100)
    ax = fig.add_axes([0, STRIP / (Hb + STRIP), 1, Hb / (Hb + STRIP)])
    ax.set_xlim(-0.5, Wb - 0.5); ax.set_ylim(Hb - 0.5, -0.5); ax.axis('off')
    fig.text(0.01, (STRIP - 70) / (Hb + STRIP), titol, fontsize=44, weight='bold', va='top')
    fig.text(0.01, (STRIP - 150) / (Hb + STRIP), subtitol, fontsize=28, va='top')
    return fig, ax


def guarnicio(ax, color='w'):
    pa = np.linspace(0, 360, 721)
    for r in (1, 2, 3, 4, 5, 6, 8):
        x, y = a_agrupat(*g.px(np.full_like(pa, r), pa))
        ax.plot(x, y, color=color, lw=1.2, ls='--', alpha=0.6)
        tx, ty = a_agrupat(*g.px(r, 180.0))
        ax.text(tx, ty + 12, f'{r} R$_\\odot$', color=color, fontsize=24, ha='center', va='top', alpha=0.9)
    x0, y0 = a_agrupat(*mc.SOL_XY)
    for pa0, lab, col in ((0.0, 'N', color), (90.0, 'E', color), (PAZ, 'zenith', 'deepskyblue')):
        x1, y1 = a_agrupat(*g.px(7.6 if lab == 'zenith' else 7.2, pa0))
        ax.annotate('', xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle='->', color=col, lw=3))
        ax.text(x1, y1, lab, color=col, fontsize=34, weight='bold', ha='center', va='center')


def barra(fig, cmap, norm, etiqueta, ticks=None):
    cax = fig.add_axes([0.55, 0.22 * STRIP / (Hb + STRIP), 0.42, 0.18 * STRIP / (Hb + STRIP)])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation='horizontal', ticks=ticks)
    cb.ax.tick_params(labelsize=26); cb.set_label(etiqueta, fontsize=30)


def mapa_log(nom, plane, titol, sub):
    m = P[plane].astype(np.float64)
    lg = np.log10(np.where(m > 0, m, np.nan))
    cmap = plt.get_cmap('inferno').copy(); cmap.set_bad((0.18, 0.18, 0.18))
    norm = Normalize(-10.5, -5.3)
    fig, ax = figura(titol, sub)
    ax.imshow(lg, cmap=cmap, norm=norm, interpolation='nearest')
    neg = np.where(np.isfinite(m) & (m <= 0), 1.0, np.nan)
    ax.imshow(neg, cmap=ListedColormap([(0.25, 0.55, 0.60)]), interpolation='nearest')
    guarnicio(ax)
    barra(fig, cmap, norm, 'log$_{10}$ MSB (B/B$_\\odot$);  dark grey = no data;  teal = MSB $\\leq$ 0 after sky subtraction')
    fig.savefig(OUT / nom); plt.close(fig)


mapa_log('V1_msb_log.png', 'PRIMARY', 'Corona of 2026-08-12 in mean solar brightness (MSB = B/B$_\\odot$), extinction-corrected',
         'Total brightness (K+F), unpolarized, camera green; sky (constant + plane) subtracted; full canvas, 2x2 binned. '
         'PRELIMINARY. Lunar-motion band and limb gap: see FLAGS; uncertainties in SIGMA_* extensions.')
mapa_log('V2_msb_noext_log.png', 'MSB_NOEXT', 'Same map WITHOUT the differential-extinction correction',
         'Sun at 9 deg altitude: airmass 5.2-7.2 across +/-6 R$_\\odot$ along the vertical. Compare with V1.')

# extinció
E = 10 ** (0.4 * mc.K_EXT * (P['AIRMASS'].astype(np.float64) - mc.MassaAire().X_sol))
cmap = plt.get_cmap('RdBu_r'); norm = Normalize(-40, 40)
fig, ax = figura('Differential-extinction correction E = 10^(0.4 k (X - X$_\\odot$)) - 1, in %',
                 f'k = {mc.K_EXT} mag/airmass (model; band {mc.K_BANDA[0]}-{mc.K_BANDA[1]} in the systematic layer); '
                 f'X: Kasten-Young, apparent altitude at {mc.DATE_OBS} UTC; X$_\\odot$ = {mc.MassaAire().X_sol:.3f}.')
ax.imshow(100 * (E - 1), cmap=cmap, norm=norm, interpolation='nearest')
guarnicio(ax, 'k')
barra(fig, cmap, norm, 'E - 1 (%): applied multiplicatively after sky subtraction')
fig.savefig(OUT / 'V3_extinction_factor.png'); plt.close(fig)

# flags (prioritat de dalt a baix)
F = P['FLAGS']
cat = np.zeros(F.shape, np.uint8)
ordre = [('SONY_DOMINATED', (0.70, 0.90, 0.70)), ('SKY_LIMITED', (0.80, 0.80, 0.80)), ('OUTSIDE_INSCRIBED', (0.55, 0.65, 0.95)),
         ('SONY_GHOST', (1.0, 0.85, 0.0)), ('PROMINENCE', (0.9, 0.0, 0.9)), ('MOON_BAND', (1.0, 0.5, 0.0)),
         ('LIMB_GAP', (1.0, 0.0, 0.0)), ('NO_DATA', (0.0, 0.0, 0.0))]
colors = [(1, 1, 1)]
for i, (nom, col) in enumerate(ordre, start=1):
    cat[(F & mc.BITS[nom]) > 0] = i
    colors.append(col)
fig, ax = figura('Flags (uint8 bit field), shown by priority', 'Profiles exclude NO_DATA, LIMB_GAP, MOON_BAND,\nPROMINENCE, SONY_GHOST, OUTSIDE_INSCRIBED.')
ax.imshow(cat, cmap=ListedColormap(colors), vmin=-0.5, vmax=len(colors) - 0.5, interpolation='nearest')
guarnicio(ax, 'k')
for i, (nom, col) in enumerate([('no flag', (1, 1, 1))] + ordre):
    lab = nom if nom == 'no flag' else f'{nom} ({mc.BITS[nom]})'
    fig.text(0.42 + 0.145 * (i % 4), (0.80 - 0.25 * (i // 4)) * STRIP / (Hb + STRIP), '■ ' + lab,
             color=col if nom not in ('no flag', 'SKY_LIMITED') else (0.45, 0.45, 0.45), fontsize=26, weight='bold')
fig.savefig(OUT / 'V4_flags.png'); plt.close(fig)

# incerteses relatives
for nom, plane, tit in (('V5_sigma_sys_relative.png', 'SIGMA_SYS', 'Systematic uncertainty SIGMA_SYS / MSB (1 sigma)'),
                        ('V6_sigma_stat_relative.png', 'SIGMA_STAT', 'Statistical uncertainty SIGMA_STAT / MSB (per 2x2 pixel, upper bound)')):
    rel = P[plane].astype(np.float64) / np.abs(P['PRIMARY'].astype(np.float64))
    cmap = plt.get_cmap('viridis').copy(); cmap.set_bad((0.18, 0.18, 0.18)); norm = Normalize(-3, 1)
    fig, ax = figura(tit, 'Zero point 10 %, drift 4 %, colour 2.5 %, flat 1.6 %, extinction band, sky models (floor 1e-9 B$_\\odot$). '
                     'Halo of our optics NOT included.' if plane == 'SIGMA_SYS' else
                     'From the fusion variance maps (DoG 1.5-3 px of ln G, per train) with the fusion weights; '
                     'the real scatter of the map is 0.1-0.4 of this (see PROVES_P3).')
    ax.imshow(np.log10(rel), cmap=cmap, norm=norm, interpolation='nearest')
    guarnicio(ax)
    barra(fig, cmap, norm, 'log$_{10}$ (sigma / |MSB|)', ticks=[-3, -2, -1, 0, 1])
    fig.savefig(OUT / nom); plt.close(fig)

# cel
cmap = plt.get_cmap('cividis'); s_ = P['SKY'].astype(np.float64)
norm = Normalize(np.nanpercentile(s_, 1), np.nanpercentile(s_, 99))
fig, ax = figura('Adopted sky model (b: constant + plane), in B$_\\odot$ (not extinction-corrected)',
                 f'Sky at the Sun: {mc.FAC_G * mc.coef_cel()["b"]["c0"]:.3e} B$_\\odot$ (camera green). Spread of models a/b/c gives SIGMA_SKY.')
ax.imshow(s_, cmap=cmap, norm=norm, interpolation='nearest')
guarnicio(ax, 'k')
barra(fig, cmap, norm, 'sky (B$_\\odot$)')
fig.savefig(OUT / 'V7_sky_model.png'); plt.close(fig)

# ---------------------------------------------------------------- perfil
pj = json.load(open(mc.MAPA / 'perfils/perfils_msb.json'))
pr = pj['perfil_azimutal']
r = np.array([f['r_mid'] for f in pr]); q = lambda k: np.array([np.nan if f[k] is None else f[k] for f in pr], float)
fig, ax = plt.subplots(figsize=(13, 9), dpi=130)
ax.fill_between(r, q('MSB_median') - q('sigma_sys_median'), q('MSB_median') + q('sigma_sys_median'), color='orange', alpha=0.25,
                label='$\\pm$ systematic (1$\\sigma$; zero point, extinction, sky...)')
ax.fill_between(r, q('MSB_p16'), q('MSB_p84'), color='k', alpha=0.10, label='azimuthal spread (16-84 %)')
cob = q('sectors_10deg_covered') >= 30
ax.plot(r, np.where(cob, q('MSB_median'), np.nan), 'k-', lw=2, label='MSB, extinction-corrected (azimuthal median)')
ax.plot(r, np.where(~cob, q('MSB_median'), np.nan), 'k:', lw=2, label='same, < 30 of 36 sectors with data (biased)')
ax.plot(r, q('MSB_noext_median'), 'b--', lw=1.3, label='MSB without extinction correction')
ax.plot(r, q('MSB_skyA_median'), color='g', ls=':', lw=1.3, label='with sky model a (constant)')
ax.plot(r, q('MSB_skyC_median'), color='m', ls=':', lw=1.3, label='with sky model c (quadratic)')
ax.plot(r, q('sky_Bsun_median'), color='gray', lw=1.5, label='sky level (B$_\\odot$, subtracted)')
ax.axhline(mc.SIGMA_SKY_FLOOR_BSOL, color='gray', ls='--', lw=1, label='sky uncertainty floor 1e-9')
k76 = 959.0 / mc.RSOL_ARCSEC
R76 = {1.02: 118853.0, 1.10: 47766.0, 1.50: 4937.0, 2.00: 809.0, 3.00: 175.0, 5.00: 37.0}
ax.plot([(a + 0.01) * k76 for a in R76], [2.772e-11 * v for v in R76.values()], 'rs', ms=8,
        label='16-08 Vixen-only profile (no extinction correction)')
ax.axvspan(1.0, 1.16, color='orange', alpha=0.15)
ax.text(1.005, 3e-10, 'lunar-motion band\n(excluded)', fontsize=10, color='darkorange')
ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xlim(1.0, 6.0); ax.set_ylim(1e-10, 5e-6)
ax.set_xticks([1, 1.5, 2, 3, 4, 5, 6]); ax.set_xticklabels(['1', '1.5', '2', '3', '4', '5', '6'])
ax.set_xlabel('r (R$_\\odot$)', fontsize=14); ax.set_ylabel('MSB = B / B$_\\odot$', fontsize=14)
ax.set_title('2026-08-12 corona, camera green, total brightness (K+F): radial profile (PRELIMINARY)', fontsize=13)
ax.grid(True, which='both', alpha=0.3); ax.legend(fontsize=9, loc='upper right')
fig.tight_layout(); fig.savefig(OUT / 'F1_radial_profile.png'); plt.close(fig)
print('vistes fetes:', sorted(p.name for p in OUT.glob('*.png')))
