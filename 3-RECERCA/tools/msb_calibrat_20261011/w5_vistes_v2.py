"""w5 · Vistes del mapa MSB v2 (12-10-2026). Llenç SENCER (graella 2×2 del FITS, 5276 × 3753), sense retalls. Rètols en anglès.
Canvis respecte de p4_vistes.py: llegenda de V4 amb els colors reals del mapa (blanc amb vora per a «no flag», gris 204 per a
SKY_LIMITED); V5 en dues (avall i amunt); V6 diu «propagated estimate, not an upper bound»; V8 nova (biaix del cel, un sol sentit);
F1 comença a la vora exterior de la franja lunar i ombreja la franja segons l'angle (a tots els angles / només a alguns).
Escriu v2/mapa/vistes/*.png."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                                    # noqa: E402
import numpy as np                                                 # noqa: E402
from astropy.io import fits                                        # noqa: E402
from matplotlib.colors import ListedColormap, Normalize            # noqa: E402
from matplotlib.patches import Rectangle                           # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import msb_comu as mc          # noqa: E402
import msb_comu_v2 as m2       # noqa: E402

OUT = m2.MAPA2 / 'vistes'; OUT.mkdir(parents=True, exist_ok=True)
with fits.open(m2.MAPA2 / 'msb_mapa_2x2_v2.fits') as hl:
    P = {h.name: np.asarray(h.data) for h in hl}
    H0 = hl[0].header
Hb, Wb = P['PRIMARY'].shape
g = mc.geo_llenc()
PAZ = json.load(open(mc.MAPA / 'PROVES_P0.json'))['zenit']['r1']['PA_solar_del_zenit']
W4 = json.load(open(m2.MAPA2 / 'PROVES_W4.json'))
SOR = json.load(open(m2.MAPA2 / 'soroll' / 'SOROLL_BLOCS.json'))['zones']['r_ge_8']
CEL = m2.coef_cel_v2()
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


bm = CEL['models'][CEL['adoptat']]
mapa_log('V1_msb_log_v2.png', 'PRIMARY', 'Corona of 2026-08-12 in mean solar brightness (MSB = B/B$_\\odot$), extinction-corrected (v2)',
         f'Total brightness (K+F), unpolarized, camera green; sky = constant + plane fitted at r $\\geq$ 8 R$_\\odot$ subtracted; full canvas, 2x2. '
         'PRELIMINARY. Lunar-motion band (FLAGS value 4) and limb gap: see FLAGS.')
mapa_log('V2_msb_noext_log_v2.png', 'MSB_NOEXT', 'Same map WITHOUT the differential-extinction correction (v2)',
         'Sun at 9 deg altitude: airmass 5.2-7.2 across +/-6 R$_\\odot$ along the vertical. Compare with V1.')

# extinció
E = m2.factor_extincio(P['AIRMASS'].astype(np.float64))
cmap = plt.get_cmap('RdBu_r'); norm = Normalize(-40, 40)
fig, ax = figura('Differential-extinction correction E = 10^(0.4 k (X - X$_{ZP}$)) - 1, in %  (v2)',
                 f'k = {m2.K_EXT} mag/airmass (band {m2.K_BANDA[0]}-{m2.K_BANDA[1]} in the systematic layer); X: Kasten-Young at {mc.DATE_OBS} UTC; '
                 f'reference X$_{{ZP}}$ = {m2.X_REF:.3f} (Sun at the zero-point epoch; X$_\\odot$ at DATE-OBS = {H0["XSUN"]:.3f}).')
ax.imshow(100 * (E - 1), cmap=cmap, norm=norm, interpolation='nearest')
guarnicio(ax, 'k')
barra(fig, cmap, norm, 'E - 1 (%): applied multiplicatively after sky subtraction')
fig.savefig(OUT / 'V3_extinction_factor_v2.png'); plt.close(fig)

# marques: colors i llegenda iguals
F = P['FLAGS']
cat = np.zeros(F.shape, np.uint8)
ordre = [('SONY_DOMINATED', (0.70, 0.90, 0.70)), ('SKY_LIMITED', (0.80, 0.80, 0.80)), ('OUTSIDE_INSCRIBED', (0.55, 0.65, 0.95)),
         ('SONY_GHOST', (1.0, 0.85, 0.0)), ('PROMINENCE', (0.9, 0.0, 0.9)), ('MOON_BAND', (1.0, 0.5, 0.0)),
         ('LIMB_GAP', (1.0, 0.0, 0.0)), ('NO_DATA', (0.0, 0.0, 0.0))]
colors = [(1, 1, 1)]
for i, (nom, col) in enumerate(ordre, start=1):
    cat[(F & mc.BITS[nom]) > 0] = i
    colors.append(col)
fig, ax = figura('Flags (uint8 bit field), shown by priority (v2)',
                 'Profiles exclude NO_DATA, LIMB_GAP, MOON_BAND (value 4 = bit 2),\nPROMINENCE, SONY_GHOST, OUTSIDE_INSCRIBED.')
ax.imshow(cat, cmap=ListedColormap(colors), vmin=-0.5, vmax=len(colors) - 0.5, interpolation='nearest')
guarnicio(ax, 'k')
fh = Hb + STRIP
for i, (nom, col) in enumerate([('no flag', (1, 1, 1))] + ordre):
    lab = nom if nom == 'no flag' else f'{nom} (value {mc.BITS[nom]})'
    x0f = 0.42 + 0.145 * (i % 4); y0f = (0.80 - 0.25 * (i // 4)) * STRIP / fh
    fig.patches.append(Rectangle((x0f, y0f - 0.002), 0.012, 0.012 * Wb / fh, transform=fig.transFigure, facecolor=col,
                                 edgecolor='k', lw=1.5, figure=fig))
    fig.text(x0f + 0.016, y0f, lab, color='k', fontsize=26, weight='bold', va='bottom')
fig.savefig(OUT / 'V4_flags_v2.png'); plt.close(fig)

# incerteses relatives
sub_sys = ('Zero point -16.7/+2.0 %, colour term 9.4 %, drift 4 %, chain 2.5 %, flat 1.6 %, extinction band, sky (floor 1e-9 B$_\\odot$). '
           'NOT included: halo, Sony-rho (~+20 % beyond 1.9 R$_\\odot$), sky bias (V8).')
r1 = max(SOR['1']['rho_files'], SOR['1']['rho_columnes']); r16 = max(SOR['16']['rho_files'], SOR['16']['rho_columnes'])
r32 = max(SOR['32']['rho_files'], SOR['32']['rho_columnes'])
for nom, plane, tit, sub in (
        ('V5a_sigma_sys_lo_relative_v2.png', 'SIGMA_SYS_LO', 'Systematic uncertainty DOWNWARDS, SIGMA_SYS_LO / MSB (1 sigma)', sub_sys),
        ('V5b_sigma_sys_hi_relative_v2.png', 'SIGMA_SYS_HI', 'Systematic uncertainty UPWARDS, SIGMA_SYS_HI / MSB (1 sigma)', sub_sys),
        ('V6_sigma_stat_relative_v2.png', 'SIGMA_STAT', 'Statistical uncertainty SIGMA_STAT / MSB (per 2x2 pixel): propagated estimate, NOT an upper bound',
         f'From the fusion variance maps with the fusion weights. Pixels are correlated: pixel-to-pixel scatter {r1:.2f} of it, '
         f'but 16 and 32 px block means scatter {r16:.2f} and {r32:.2f} x the independent-pixel prediction (sky zone).')):
    rel = P[plane].astype(np.float64) / np.abs(P['PRIMARY'].astype(np.float64))
    cmap = plt.get_cmap('viridis').copy(); cmap.set_bad((0.18, 0.18, 0.18)); norm = Normalize(-3, 1)
    fig, ax = figura(tit, sub)
    ax.imshow(np.log10(rel), cmap=cmap, norm=norm, interpolation='nearest')
    guarnicio(ax)
    barra(fig, cmap, norm, 'log$_{10}$ (sigma / |MSB|)', ticks=[-3, -2, -1, 0, 1])
    fig.savefig(OUT / nom); plt.close(fig)

# cel
cmap = plt.get_cmap('cividis'); s_ = P['SKY'].astype(np.float64)
norm = Normalize(np.nanpercentile(s_, 1), np.nanpercentile(s_, 99))
fig, ax = figura('Adopted sky (constant + plane fitted at r $\\geq$ 8 R$_\\odot$), in B$_\\odot$ (not extinction-corrected)  (v2)',
                 f'Sky at the Sun: {m2.FAC_G * bm["c0"]:.3e} B$_\\odot$ (camera green); gradient {bm["gu"]:+.2f}, {bm["gv"]:+.2f} ADU/s per R$_\\odot$ (x, row). '
                 'SIGMA_SKY: constant sky (a) and a floor of 1e-9 B$_\\odot$.')
ax.imshow(s_, cmap=cmap, norm=norm, interpolation='nearest')
guarnicio(ax, 'k')
barra(fig, cmap, norm, 'sky (B$_\\odot$)')
fig.savefig(OUT / 'V7_sky_model_v2.png'); plt.close(fig)

# biaix del cel (un sol sentit)
rel = P['SKY_BIAS'].astype(np.float64) / np.abs(P['PRIMARY'].astype(np.float64))
cmap = plt.get_cmap('magma').copy(); cmap.set_bad((0.18, 0.18, 0.18)); norm = Normalize(-3, 0)
fig, ax = figura('One-sided sky bias SKY_BIAS / MSB: the map is too LOW by about this fraction (model, not applied)',
                 'K+F corona of van de Hulst 1950 (K$_{max}$ + F) passed through the same sky estimator (r $\\geq$ 8 R$_\\odot$). '
                 'Model variants (K$_{min}$, Koutchmy-Lamy F) give x0.73 to x1.31 of it.')
ax.imshow(np.log10(rel), cmap=cmap, norm=norm, interpolation='nearest')
guarnicio(ax)
barra(fig, cmap, norm, 'log$_{10}$ (SKY_BIAS / |MSB|)', ticks=[-3, -2, -1, 0])
fig.savefig(OUT / 'V8_sky_bias_relative_v2.png'); plt.close(fig)

# ---------------------------------------------------------------- perfil
pj = json.load(open(m2.MAPA2 / 'perfils/perfils_msb_v2.json'))
pr = pj['perfil_azimutal']; FR = pj['franja_lunar']
r = np.array([f['r_mid'] for f in pr]); q = lambda k: np.array([np.nan if f[k] is None else f[k] for f in pr], float)   # noqa: E731
rin = np.array([f['r_in'] for f in pr])
fora = rin >= FR['r_vora_max_mesurat_Rsol']          # anells sencers fora de la franja
Mq = q('MSB_median')
fig, ax = plt.subplots(figsize=(13, 9), dpi=130)
ax.fill_between(r[fora], (Mq - q('sigma_sys_lo_median'))[fora], (Mq + q('sigma_sys_hi_median'))[fora], color='orange', alpha=0.25,
                label='systematic 1$\\sigma$ (down/up: zero point, colour term, extinction, sky...)')
ax.fill_between(r[fora], q('MSB_p16')[fora], q('MSB_p84')[fora], color='k', alpha=0.10, label='azimuthal spread (16-84 %)')
cob = (q('sectors_10deg_covered') >= 30) & fora
ax.plot(r, np.where(cob, Mq, np.nan), 'k-', lw=2, label='MSB, extinction-corrected (azimuthal median)')
ax.plot(r, np.where(~cob & fora, Mq, np.nan), 'k:', lw=2, label='same, < 30 of 36 sectors with data (biased)')
ax.plot(r[fora], (Mq + q('sky_bias_median'))[fora], color='firebrick', ls='--', lw=1.3,
        label='+ one-sided sky bias (K+F model in the sky, not applied)')
ax.plot(r[fora], q('MSB_noext_median')[fora], 'b--', lw=1.3, label='MSB without extinction correction')
ax.plot(r[fora], q('MSB_skyA_median')[fora], color='g', ls=':', lw=1.3, label='with the constant sky (a)')
ax.plot(r[fora], q('sky_Bsun_median')[fora], color='gray', lw=1.5, label='sky level (B$_\\odot$, subtracted)')
ax.axhline(m2.SIGMA_SKY_FLOOR_BSOL, color='gray', ls='--', lw=1, label='sky uncertainty floor 1e-9')
k76 = 959.0 / mc.RSOL_ARCSEC
R76 = {1.10: 47766.0, 1.50: 4937.0, 2.00: 809.0, 3.00: 175.0, 5.00: 37.0}
ax.plot([(a + 0.01) * k76 for a in R76], [2.772e-11 * v for v in R76.values()], 'rs', ms=8,
        label='16-08 Vixen-only profile (no extinction correction)')
ax.axvspan(1.0, FR['r_vora_min_mesurat_Rsol'], color='orange', alpha=0.35)
ax.axvspan(FR['r_vora_min_mesurat_Rsol'], FR['r_vora_max_mesurat_Rsol'], color='orange', alpha=0.15)
ax.text(1.003, 2.5e-10, 'lunar-motion band\n(excluded)\ndark: all PA\nlight: some PA\n(partial rings,\nnot plotted)', fontsize=8.5, color='darkorange')
ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xlim(1.0, 6.0); ax.set_ylim(1e-10, 5e-6)
ax.set_xticks([1, 1.5, 2, 3, 4, 5, 6]); ax.set_xticklabels(['1', '1.5', '2', '3', '4', '5', '6'])
ax.set_xlabel('r (R$_\\odot$)', fontsize=14); ax.set_ylabel('MSB = B / B$_\\odot$', fontsize=14)
ax.set_title('2026-08-12 corona, camera green, total brightness (K+F): radial profile, v2 (PRELIMINARY)', fontsize=13)
ax.grid(True, which='both', alpha=0.3); ax.legend(fontsize=8.5, loc='upper right')
fig.tight_layout(); fig.savefig(OUT / 'F1_radial_profile_v2.png'); plt.close(fig)
print('vistes fetes:', sorted(p.name for p in OUT.glob('*.png')))
