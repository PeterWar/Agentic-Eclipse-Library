"""p3 · Perfils radials MSB(r) del mapa calibrat (11-10-2026): medianes azimutals i per sectors de 10°, d'1,0 a 6,0 R☉.

Píxels: resolució plena (msb_comu.calcul_bloc), NOMÉS els que no porten cap bit d'EXCLOU_PERFILS (sense dada, buit del limbe,
franja lunar, protuberàncies, fantasma de la Sony, fora del cercle inscrit). Els dominats per la Sony hi són (és dada) i se'n
dona la fracció. Anells predeclarats: 0,01 R☉ d'1 a 2; 0,02 de 2 a 4; 0,05 de 4 a 6. Sectors de 10° des del nord solar cap a l'est.
Xifres clau: anells [0,99·r; 1,01·r] a r = 1,15, 1,5, 2, 3, 4, 5 R☉.
Proves: (1) coherència amb research/76 §5.1 (anells [r76, r76+0,02]·959/946,66; sense extinció, com allà);
(2) geometria: els mateixos anells amb tres centres alternatius del Sol; (3) soroll: dispersió real del mapa agrupat contra
SIGMA_STAT en zones de cel; (4) sensibilitat al model de cel (a, c contra b).
Escriu mapa/perfils/ (CSV + JSON) i mapa/PROVES_P3.json."""
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as nd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import msb_comu as mc

T0 = time.time()
import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)
cau = mc.obre_cau(); MA = mc.MassaAire(); CEL = mc.coef_cel(); Z = mc.zones()
OUT = mc.MAPA / 'perfils'; OUT.mkdir(parents=True, exist_ok=True)
K76 = 959.0 / mc.RSOL_ARCSEC
RMAX = 6.2
galt = {k: mc.geo_llenc(c) for k, c in mc.SOL_ALTERNATIUS.items()}

cols = {k: [] for k in ('r', 'pa', 'msb', 'noe', 'msa', 'msc', 'sst', 'ssy', 'ssk', 'E', 'sony', 'G', 'R', 'sky')}
for k in galt:
    cols['r_' + k] = []
banda = {k: [] for k in ('r', 'noe', 'G', 'R', 'sky')}           # diagnòstic de la franja (NO és mesura)
y_lo = max(0, int(mc.SOL_XY[1] - (RMAX + 0.3) * mc.RSOL_PX)); y_hi = min(mc.H, int(mc.SOL_XY[1] + (RMAX + 0.3) * mc.RSOL_PX) + 1)
for y0 in range(y_lo - y_lo % 2, y_hi, 512):
    y1 = min(y0 + 512, y_hi)
    o = mc.calcul_bloc(y0, y1, cau, MA, CEL, Z)
    fl = o['flags']; r = o['r']
    ok = ((fl & mc.EXCLOU_PERFILS) == 0) & (r >= 1.0) & (r < RMAX) & np.isfinite(o['msb'])
    E = o['E'].astype(np.float64)
    cols['r'].append(r[ok]); cols['pa'].append(o['pa'][ok]); cols['msb'].append(o['msb'][ok]); cols['noe'].append(o['msb_noext'][ok])
    cols['msa'].append((o['msb'][ok] + mc.FAC_G * E[ok] * (o['sky'][ok] - o['sky_a'][ok])).astype(np.float32))
    cols['msc'].append((o['msb'][ok] + mc.FAC_G * E[ok] * (o['sky'][ok] - o['sky_c'][ok])).astype(np.float32))
    cols['sst'].append(o['sigma_stat'][ok]); cols['ssy'].append(o['sigma_sys'][ok]); cols['ssk'].append(o['sigma_sky_msb'][ok])
    cols['E'].append(o['E'][ok]); cols['sony'].append(((fl[ok] & mc.BITS['SONY_DOMINATED']) > 0))
    cols['G'].append(o['G_cam'][ok]); cols['R'].append(o['R_cam'][ok]); cols['sky'].append(o['sky'][ok])
    yy = np.arange(y0, y1, dtype=np.float64)[:, None] * np.ones((1, mc.W)); xx = np.ones((y1 - y0, 1)) * np.arange(mc.W, dtype=np.float64)[None, :]
    for k, ga in galt.items():
        cols['r_' + k].append(ga.polar(xx[ok], yy[ok])[0].astype(np.float32))
    bb = ((fl & mc.BITS['MOON_BAND']) > 0) & ((fl & (mc.BITS['NO_DATA'] | mc.BITS['LIMB_GAP'])) == 0) & (r < 1.2)
    banda['r'].append(r[bb]); banda['noe'].append(o['msb_noext'][bb]); banda['G'].append(o['G_cam'][bb]); banda['R'].append(o['R_cam'][bb]); banda['sky'].append(o['sky'][bb])
    print(f'files {y0}-{y1}: {ok.sum()} px vàlids ({time.time() - T0:.0f} s)', flush=True)
C = {k: np.concatenate(v) for k, v in cols.items()}
BD = {k: np.concatenate(v) for k, v in banda.items()}
del cols, banda
N = C['r'].size
print(f'{N} píxels vàlids a 1–{RMAX} R☉ ({time.time() - T0:.0f} s)', flush=True)


def medianes(key, val, ngr, quant=(50,)):
    """Percentils per grup (key en [0, ngr)), ignorant NaN. Retorna (n, {q: valors})."""
    m = (key >= 0) & (key < ngr) & np.isfinite(val)
    k = key[m]; v = val[m]
    o = np.lexsort((v, k)); k = k[o]; v = v[o]
    n = np.bincount(k, minlength=ngr)
    ini = np.concatenate([[0], np.cumsum(n)[:-1]])
    res = {}
    for q in quant:
        out = np.full(ngr, np.nan)
        ok = n > 0
        pos = ini[ok] + (n[ok] - 1) * q / 100.0
        lo = np.floor(pos).astype(np.int64); hi = np.ceil(pos).astype(np.int64); fr = pos - lo
        out[ok] = v[lo] * (1 - fr) + v[hi] * fr
        res[q] = out
    return n, res


# ---------------------------------------------------------------- anells i sectors
edges = np.unique(np.round(np.r_[np.arange(1.00, 2.00, 0.01), np.arange(2.00, 4.00, 0.02), np.arange(4.00, 6.0001, 0.05)], 4))
nr = len(edges) - 1
ri = np.searchsorted(edges, C['r'], side='right') - 1
ri[(C['r'] >= edges[-1])] = -1
si = (np.floor(C['pa'] / 10.0).astype(np.int64)) % 36
cnt, q_msb = medianes(ri, C['msb'].astype(np.float64), nr, (16, 50, 84))
_, q_noe = medianes(ri, C['noe'].astype(np.float64), nr)
_, q_msa = medianes(ri, C['msa'].astype(np.float64), nr)
_, q_msc = medianes(ri, C['msc'].astype(np.float64), nr)
_, q_sst = medianes(ri, C['sst'].astype(np.float64), nr)
_, q_ssy = medianes(ri, C['ssy'].astype(np.float64), nr)
_, q_ssk = medianes(ri, C['ssk'].astype(np.float64), nr)
_, q_E = medianes(ri, C['E'].astype(np.float64), nr)
_, q_sky = medianes(ri, (mc.FAC_G * C['sky']).astype(np.float64), nr)
fsony = np.bincount(ri[ri >= 0], weights=C['sony'][ri >= 0].astype(float), minlength=nr)[:nr] / np.maximum(cnt, 1)
q_alt = {}
for k in galt:
    rk = np.searchsorted(edges, C['r_' + k], side='right') - 1; rk[C['r_' + k] >= edges[-1]] = -1
    q_alt[k] = medianes(rk, C['msb'].astype(np.float64), nr)[1][50]
keyS = np.where(ri >= 0, ri * 36 + si, -1)
cntS, q_S = medianes(keyS, C['msb'].astype(np.float64), nr * 36)
_, q_Snoe = medianes(keyS, C['noe'].astype(np.float64), nr * 36)
_, q_SE = medianes(keyS, C['E'].astype(np.float64), nr * 36)
_, q_Ssy = medianes(keyS, C['ssy'].astype(np.float64), nr * 36)
cobert = (cntS.reshape(nr, 36) >= 20).sum(axis=1)
mig = 0.5 * (edges[1:] + edges[:-1])
files = []
for i in range(nr):
    files.append(dict(r_in=round(float(edges[i]), 4), r_out=round(float(edges[i + 1]), 4), r_mid=round(float(mig[i]), 4), n_px=int(cnt[i]),
                      sectors_10deg_covered=int(cobert[i]), frac_sony_dominated=float(fsony[i]),
                      MSB_median=q_msb[50][i], MSB_p16=q_msb[16][i], MSB_p84=q_msb[84][i], MSB_noext_median=q_noe[50][i],
                      MSB_skyA_median=q_msa[50][i], MSB_skyC_median=q_msc[50][i],
                      sigma_stat_px_median=q_sst[50][i], sigma_sys_median=q_ssy[50][i], sigma_sky_median=q_ssk[50][i],
                      E_median=q_E[50][i], sky_Bsun_median=q_sky[50][i],
                      **{f'MSB_median_centre_{k}': q_alt[k][i] for k in galt}))
camps = list(files[0].keys())
with open(OUT / 'perfil_azimutal.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=camps); w.writeheader()
    for f in files:
        w.writerow({k: (f'{v:.6e}' if isinstance(v, float) else v) for k, v in f.items()})
with open(OUT / 'perfil_sectors_10graus.csv', 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['r_in', 'r_out', 'pa_from', 'pa_to', 'n_px', 'MSB_median', 'MSB_noext_median', 'E_median', 'sigma_sys_median'])
    for i in range(nr):
        for s_ in range(36):
            j = i * 36 + s_
            w.writerow([f'{edges[i]:.4f}', f'{edges[i + 1]:.4f}', s_ * 10, s_ * 10 + 10, int(cntS[j]),
                        f'{q_S[50][j]:.6e}', f'{q_Snoe[50][j]:.6e}', f'{q_SE[50][j]:.6f}', f'{q_Ssy[50][j]:.6e}'])
print(f'perfils fets ({time.time() - T0:.0f} s)', flush=True)


# ---------------------------------------------------------------- xifres clau
def anell(lo, hi, sel=None):
    m = (C['r'] >= lo) & (C['r'] < hi)
    if sel is not None:
        m &= sel
    return m


clau = {}
for r0 in (1.15, 1.5, 2.0, 3.0, 4.0, 5.0):
    lo, hi = 0.99 * r0, 1.01 * r0
    m = anell(lo, hi)
    sec = np.unique(si[m], return_counts=True)
    d = dict(anell=[lo, hi], n_px=int(m.sum()), sectors_10graus_amb_20px=int((sec[1] >= 20).sum()),
             frac_sony=float(C['sony'][m].mean()),
             MSB=float(np.median(C['msb'][m])), MSB_noext=float(np.median(C['noe'][m])),
             efecte_extincio_mediana_pct=100 * (float(np.median(C['msb'][m])) / float(np.median(C['noe'][m])) - 1),
             MSB_cel_a=float(np.median(C['msa'][m])), MSB_cel_c=float(np.median(C['msc'][m])),
             sigma_sys_mediana=float(np.median(C['ssy'][m])), sigma_sky_mediana=float(np.median(C['ssk'][m])),
             sigma_stat_px_mediana=float(np.nanmedian(C['sst'][m])),
             MSB_p16_p84_azimutal=[float(np.percentile(C['msb'][m], 16)), float(np.percentile(C['msb'][m], 84))],
             E_mediana=float(np.median(C['E'][m])), cel_Bsun_mediana=float(np.median(mc.FAC_G * C['sky'][m])))
    alt = {}
    for k in galt:
        ma_ = (C['r_' + k] >= lo) & (C['r_' + k] < hi)
        alt[k] = float(np.median(C['msb'][ma_]))
    d['MSB_centres_alternatius'] = alt
    d['sigma_geometria_rel'] = float(max(abs(v / d['MSB'] - 1) for v in alt.values()))
    d['sigma_cel_models_rel'] = float(max(abs(d['MSB_cel_a'] / d['MSB'] - 1), abs(d['MSB_cel_c'] / d['MSB'] - 1)))
    d['sigma_sys_rel'] = d['sigma_sys_mediana'] / d['MSB']
    clau[f'{r0:g}'] = d
    print(r0, {k: v for k, v in d.items() if k in ('MSB', 'MSB_noext', 'sigma_sys_rel', 'sigma_geometria_rel', 'sectors_10graus_amb_20px')}, flush=True)

# ---------------------------------------------------------------- 1. coherència amb research/76 §5.1
R76 = {1.02: 118853.0, 1.10: 47766.0, 1.50: 4937.0, 2.00: 809.0, 3.00: 175.0, 5.00: 37.0}   # ADU/s, luminància neta (76:154-163)
FAC76 = 2.772e-11
# kr i cel de la luminància (G + kr·R)/2 com research/76 (constant = mediana a r76 > 7,2), sobre el submostreig 4×
F4 = np.asarray(cau['fusion_total_v42'][::4, ::4], np.float64)
sp4 = np.asarray(cau['support_v42'][::4, ::4])
yy4, xx4 = np.mgrid[0:mc.H:4, 0:mc.W:4].astype(np.float64)
r4, _ = mc.geo_llenc().polar(xx4, yy4)
ok4 = sp4 & np.all(np.isfinite(F4), 2) & np.all(F4 > 0, 2) & (np.hypot(xx4 - mc.GHOST_XY[0], yy4 - mc.GHOST_XY[1]) >= mc.GHOST_R_PX)
uc4 = mc.canals_camera(F4)
ref = ok4 & (r4 / K76 > 1.3) & (r4 / K76 < 1.5)
kr = float(np.median(uc4[..., 1][ref]) / np.median(uc4[..., 0][ref]))
L4 = 0.5 * (uc4[..., 1] + kr * uc4[..., 0])
Lsky = float(np.median(L4[ok4 & (r4 / K76 > 7.2)]))
Gsky_const = float(np.median(uc4[..., 1][ok4 & (r4 / K76 > 7.2)]))
del F4, uc4, L4, xx4, yy4, r4, sp4, ok4
coh = {}
for r76, adu in R76.items():
    lo, hi = r76 * K76, (r76 + 0.02) * K76
    m = anell(lo, hi)
    ent = dict(anell_r76=[r76, r76 + 0.02], anell_real=[lo, hi], research76_ADU_s=adu, research76_MSB=FAC76 * adu, n_px_valids=int(m.sum()))
    if m.sum() > 200:
        noe = float(np.median(C['noe'][m])); ent['nostre_MSB_noext_G'] = noe
        ent['quocient_G'] = noe / (FAC76 * adu)
        Ln = 0.5 * (C['G'][m].astype(np.float64) + kr * C['R'][m]) - Lsky
        ent['nostre_luminancia_neta_ADU_s'] = float(np.median(Ln)); ent['quocient_luminancia'] = float(np.median(Ln)) / adu
        ent['nostre_MSB_amb_extincio'] = float(np.median(C['msb'][m]))
    else:
        ent['nostre_MSB_noext_G'] = None
        ent['motiu'] = 'cap píxel vàlid: tot l\'anell és dins la franja del moviment lunar o sense dada (exclòs)'
    mb = (BD['r'] >= lo) & (BD['r'] < hi)
    if mb.sum() > 200:
        Lb = 0.5 * (BD['G'][mb].astype(np.float64) + kr * BD['R'][mb]) - Lsky
        ent['DIAGNOSTIC_franja_no_es_mesura'] = dict(n_px=int(mb.sum()), MSB_noext_G=float(np.median(BD['noe'][mb])),
                                                    quocient_G=float(np.median(BD['noe'][mb])) / (FAC76 * adu),
                                                    quocient_luminancia=float(np.median(Lb)) / adu)
    coh[f'{r76:.2f}'] = ent
print('coherència 76', json.dumps(coh, indent=0)[:3000], flush=True)
# color net del que queda després de restar un cel constant a cada canal (diagnòstic de l'efecte de banda)
Rsky_const = (2 * Lsky - Gsky_const) / kr
color_net = dict(cel_constant_ADU_s=dict(G=Gsky_const, R=Rsky_const, R_sobre_G_cel=Rsky_const / Gsky_const),
                 nota=('ratio de medianes (R − R_cel)/(G − G_cel) amb cels CONSTANTS (r > 7,29 R☉) a cada canal; '
                       'luminància/G = 0,5·(1 + kr·R_net/G_net); és el que canvia si la variable no és el verd sol'))
for r0 in (1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0):
    m = anell(0.99 * r0, 1.01 * r0)
    Gn = float(np.median(C['G'][m])) - Gsky_const; Rn = float(np.median(C['R'][m])) - Rsky_const
    color_net[f'{r0:g}'] = dict(R_sobre_G_net=Rn / Gn, luminancia_sobre_G=0.5 * (1 + kr * Rn / Gn),
                                MSB_noext_G_cel_constant=mc.FAC_G * Gn, MSB_noext_luminancia_cel_constant=mc.FAC_G * 0.5 * (Gn + kr * Rn),
                                frac_sony=float(C['sony'][m].mean()))
print('color net', json.dumps(color_net, indent=0)[:2500], flush=True)

# ---------------------------------------------------------------- 3. soroll: dispersió real contra SIGMA_STAT (mapa agrupat 2×2)
from astropy.io import fits
with fits.open(mc.MAPA / 'msb_mapa_2x2.fits', memmap=True) as hl:
    Mb = np.asarray(hl['PRIMARY'].data, np.float64); Sb = np.asarray(hl['SIGMA_STAT'].data, np.float64)
    Fb = np.asarray(hl['FLAGS'].data)
Hb, Wb = Mb.shape
yb, xb = np.mgrid[0:Hb, 0:Wb].astype(np.float64)
rb, _ = mc.geo_llenc().polar(2 * xb + 0.5, 2 * yb + 0.5)
fin = np.isfinite(Mb)
Mf = np.where(fin, Mb, 0.0)
med5 = nd.median_filter(Mf, size=5)
tot5 = nd.minimum_filter(fin.astype(np.uint8), size=5) > 0
res = Mb - med5
# factor de l'estimador (x − mediana 5×5) per a soroll blanc
rng = np.random.default_rng(3); wn = rng.standard_normal((1024, 1024))
fw = float(np.std((wn - nd.median_filter(wn, size=5))[8:-8, 8:-8]))
soroll = {}
for (a, b) in ((1.5, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 5.0), (5.0, 6.0), (6.0, 8.0)):
    m = tot5 & (rb >= a) & (rb < b) & ((Fb & mc.EXCLOU_PERFILS) == 0) & np.isfinite(Sb)
    rr_ = res[m]
    sd = 1.4826 * np.median(np.abs(rr_ - np.median(rr_))) / fw
    soroll[f'{a}-{b}'] = dict(n=int(m.sum()), dispersio_real_MSB=float(sd), sigma_stat_mediana=float(np.median(Sb[m])),
                              quocient_real_sobre_sigma_stat=float(sd / np.median(Sb[m])),
                              MSB_mediana=float(np.median(Mb[m])))
soroll['nota'] = ('dispersió real = MAD robust de (MSB − mediana 5×5) del mapa agrupat, corregida pel factor del mateix estimador '
                  f'sobre soroll blanc ({fw:.3f}). Inclou estructura fina real i correlació entre píxels veïns: '
                  'si el quocient < 1, SIGMA_STAT sobreestima el soroll; si > 1, l\'estructura fina hi suma.')
print('soroll', json.dumps(soroll, indent=0)[:2000], flush=True)
del Mb, Sb, Fb, med5, res, Mf

rep = dict(guio='p3_perfils.py', data_execucio=time.strftime('%Y-%m-%dT%H:%M:%S'), temps_s=time.time() - T0,
           pixels_valids_1_6=int(N), exclosos_bits=mc.EXCLOU_PERFILS, anells=dict(vores=edges.tolist()),
           xifres_clau=clau, coherencia_research76=dict(kr_luminancia_cam=kr, cel_luminancia_constant_ADU_s=Lsky,
                                                        cel_G_constant_ADU_s=Gsky_const, anells=coh),
           color_net_efecte_de_banda=color_net,
           soroll=soroll, extincio_vertical=json.load(open(mc.MAPA / 'PROVES_P1.json'))['massa_aire'])
json.dump(rep, open(mc.MAPA / 'PROVES_P3.json', 'w'), indent=1, ensure_ascii=False, default=float)
json.dump(dict(descripcio=('Radial profiles of the calibrated MSB map (B/Bsun, total K+F, unpolarized, camera green). '
                           'Azimuthal medians over valid pixels; flags excluded: ' +
                           ', '.join(k for k, b in mc.BITS.items() if b & mc.EXCLOU_PERFILS)),
               unitats='MSB = B/Bsun (mean solar brightness)', r_unitats='Rsun (946.66 arcsec)', sectors='10 deg from solar north towards east',
               perfil_azimutal=files, xifres_clau=clau,
               sectors_10graus=dict(vores_r=edges.tolist(), pa_inici=list(range(0, 360, 10)),
                                    n_px=cntS.reshape(nr, 36).tolist(),
                                    MSB_median=np.where(cntS > 0, q_S[50], np.nan).reshape(nr, 36).tolist(),
                                    MSB_noext_median=np.where(cntS > 0, q_Snoe[50], np.nan).reshape(nr, 36).tolist(),
                                    E_median=np.where(cntS > 0, q_SE[50], np.nan).reshape(nr, 36).tolist())),
          open(OUT / 'perfils_msb.json', 'w'), indent=1, ensure_ascii=False, default=float)
print(f'fet en {time.time() - T0:.0f} s')
