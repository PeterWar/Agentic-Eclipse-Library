"""w4 · Perfils MSB(r) de la v2, xifres clau i pressupost d'incerteses (12-10-2026).

Píxels: resolució plena (msb_comu_v2.calcul_bloc_v2), NOMÉS els que no porten cap bit d'EXCLOU_PERFILS (com la v1). Anells i sectors
iguals que la v1 (p3_perfils.py). Xifres clau: anells [0,99·r; 1,01·r] a r = 1,15, 1,5, 2, 3, 4, 5 R☉.
Pressupost per anell (relatiu a la mediana; 1σ):
  punt zero: −16,7 % / +2,0 % (bootstrap p16 / σ del wls); tria del terme de color ±9,4 %; deriva ±4 %; color i cadena ±2,5 %;
  flat ±1,6 %; linealitat ±0,13 %; extinció: mediana amb k = 0,35 i 0,72 contra 0,40 (asimètric); cel: |mediana amb el cel a −
  adoptada| i el terra d'1e-9 B☉·E (el més gran); geometria: els tres centres alternatius del Sol; estadística: amb el soroll de blocs
  de 32 px mesurat a w3a (ρ32 × σ_prop) sobre els blocs de l'anell.
  A part (un sol sentit): biaix del cel = mediana de SKY_BIAS a l'anell (model central) i forquilla de les variants del model.
  Fora del pressupost: Sony·ρ (~+20 % on mana la Sony), halo de la nostra òptica (sense model).
Franja lunar: es mesura la fracció de l'anell d'1,15 R☉ que hi cau i l'abast radial de la franja segons l'angle.
Escriu v2/mapa/perfils/ (CSV + JSON) i v2/mapa/PROVES_W4.json."""
import csv
import json
import math
import sys
import time
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import msb_comu as mc          # noqa: E402
import msb_comu_v2 as m2       # noqa: E402

warnings.filterwarnings('ignore', category=RuntimeWarning)
T0 = time.time()
cau = mc.obre_cau(); MA = mc.MassaAire(); CEL = m2.coef_cel_v2(); Z = mc.zones()
SOR = json.load(open(m2.MAPA2 / 'soroll' / 'SOROLL_BLOCS.json'))
ZP = m2.punt_zero()
OUT = m2.MAPA2 / 'perfils'; OUT.mkdir(parents=True, exist_ok=True)
K76 = 959.0 / mc.RSOL_ARCSEC
RMAX = 6.2
galt = {k: mc.geo_llenc(c) for k, c in mc.SOL_ALTERNATIUS.items()}
AD = CEL['adoptat']

cols = {k: [] for k in ('r', 'pa', 'msb', 'noe', 'msa', 'k035', 'k072', 'sst', 'slo', 'shi', 'ssk', 'bias', 'E', 'sony', 'G', 'sky')}
for k in galt:
    cols['r_' + k] = []
banda = dict(r=[], pa=[])
anell115 = dict(tot=0, banda=0, valid=0)
y_lo = max(0, int(mc.SOL_XY[1] - (RMAX + 0.3) * mc.RSOL_PX)); y_hi = min(mc.H, int(mc.SOL_XY[1] + (RMAX + 0.3) * mc.RSOL_PX) + 1)
for y0 in range(y_lo - y_lo % 2, y_hi, 512):
    y1 = min(y0 + 512, y_hi)
    o = m2.calcul_bloc_v2(y0, y1, cau, MA, CEL, Z)
    fl = o['flags']; r = o['r']
    ok = ((fl & mc.EXCLOU_PERFILS) == 0) & (r >= 1.0) & (r < RMAX) & np.isfinite(o['msb'])
    E = o['E'].astype(np.float64)
    yy = np.arange(y0, y1, dtype=np.float64)[:, None] * np.ones((1, mc.W)); xx = np.ones((y1 - y0, 1)) * np.arange(mc.W, dtype=np.float64)[None, :]
    Sa = m2.cel_model_v2(xx[ok], yy[ok], 'a', CEL)
    noe = o['msb_noext'][ok].astype(np.float64)
    X = o['X'][ok].astype(np.float64)
    cols['r'].append(r[ok]); cols['pa'].append(o['pa'][ok]); cols['msb'].append(o['msb'][ok]); cols['noe'].append(o['msb_noext'][ok])
    cols['msa'].append((o['msb'][ok] + m2.FAC_G * E[ok] * (o['sky'][ok] - Sa)).astype(np.float32))
    cols['k035'].append((noe * m2.factor_extincio(X, 0.35)).astype(np.float32))
    cols['k072'].append((noe * m2.factor_extincio(X, 0.72)).astype(np.float32))
    cols['sst'].append(o['sigma_stat'][ok]); cols['slo'].append(o['sigma_sys_lo'][ok]); cols['shi'].append(o['sigma_sys_hi'][ok])
    cols['ssk'].append(o['sigma_sky_msb'][ok]); cols['bias'].append(o['sky_bias_msb'][ok])
    cols['E'].append(o['E'][ok]); cols['sony'].append(((fl[ok] & mc.BITS['SONY_DOMINATED']) > 0))
    cols['G'].append(o['G_cam'][ok]); cols['sky'].append(o['sky'][ok])
    for k, ga in galt.items():
        cols['r_' + k].append(ga.polar(xx[ok], yy[ok])[0].astype(np.float32))
    # franja lunar: on és (radi i angle), i l'anell d'1,15 R☉
    bb = ((fl & mc.BITS['MOON_BAND']) > 0) & (r < 1.3)
    banda['r'].append(r[bb]); banda['pa'].append(o['pa'][bb])
    a115 = (r >= 0.99 * 1.15) & (r < 1.01 * 1.15) & ((fl & mc.BITS['NO_DATA']) == 0)
    anell115['tot'] += int(a115.sum()); anell115['banda'] += int((a115 & ((fl & mc.BITS['MOON_BAND']) > 0)).sum())
    anell115['valid'] += int((a115 & ok).sum())
    print(f'files {y0}-{y1}: {ok.sum()} px ({time.time() - T0:.0f} s)', flush=True)
C = {k: np.concatenate(v) for k, v in cols.items()}
BD = {k: np.concatenate(v) for k, v in banda.items()}
del cols, banda
N = C['r'].size
print(f'{N} píxels vàlids ({time.time() - T0:.0f} s)', flush=True)


def medianes(key, val, ngr, quant=(50,)):
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


# ---------------------------------------------------------------- franja lunar: abast radial segons l'angle
dmoon = math.hypot(mc.LLUNA_XY[0] - mc.SOL_XY[0], mc.LLUNA_XY[1] - mc.SOL_XY[1])
rb_min = (mc.R_BANDA_PX - dmoon) / mc.RSOL_PX; rb_max = (mc.R_BANDA_PX + dmoon) / mc.RSOL_PX
pa_bins = np.floor(BD['pa'] / 10).astype(int) % 36
rmax_sec = np.array([BD['r'][pa_bins == s].max() if np.any(pa_bins == s) else np.nan for s in range(36)])
FRANJA = dict(desplacament_lluna_sol_px=dmoon, r_vora_min_Rsol=rb_min, r_vora_max_Rsol=rb_max,
              r_vora_max_mesurat_Rsol=float(np.nanmax(rmax_sec)), r_vora_min_mesurat_Rsol=float(np.nanmin(rmax_sec)),
              r_vora_per_sector_10graus=[None if not np.isfinite(x) else round(float(x), 4) for x in rmax_sec],
              anell_115=dict(anell=[0.99 * 1.15, 1.01 * 1.15], pixels_amb_dada=anell115['tot'], pixels_a_la_franja=anell115['banda'],
                             fraccio_a_la_franja=anell115['banda'] / max(anell115['tot'], 1), pixels_valids=anell115['valid'],
                             sectors_10graus_tallats=int(np.sum(rmax_sec > 0.99 * 1.15))))
print('franja', {k: v for k, v in FRANJA.items() if k != 'r_vora_per_sector_10graus'}, flush=True)

# ---------------------------------------------------------------- perfils
edges = np.unique(np.round(np.r_[np.arange(1.00, 2.00, 0.01), np.arange(2.00, 4.00, 0.02), np.arange(4.00, 6.0001, 0.05)], 4))
nr = len(edges) - 1
ri = np.searchsorted(edges, C['r'], side='right') - 1
ri[(C['r'] >= edges[-1])] = -1
si = (np.floor(C['pa'] / 10.0).astype(np.int64)) % 36
cnt, q_msb = medianes(ri, C['msb'].astype(np.float64), nr, (16, 50, 84))
Q = {k: medianes(ri, C[k].astype(np.float64), nr)[1][50] for k in ('noe', 'msa', 'k035', 'k072', 'sst', 'slo', 'shi', 'ssk', 'bias', 'E')}
_, q_sky = medianes(ri, (m2.FAC_G * C['sky']).astype(np.float64), nr)
fsony = np.bincount(ri[ri >= 0], weights=C['sony'][ri >= 0].astype(float), minlength=nr)[:nr] / np.maximum(cnt, 1)
q_alt = {}
for k in galt:
    rk = np.searchsorted(edges, C['r_' + k], side='right') - 1; rk[C['r_' + k] >= edges[-1]] = -1
    q_alt[k] = medianes(rk, C['msb'].astype(np.float64), nr)[1][50]
keyS = np.where(ri >= 0, ri * 36 + si, -1)
cntS, q_S = medianes(keyS, C['msb'].astype(np.float64), nr * 36)
_, q_Snoe = medianes(keyS, C['noe'].astype(np.float64), nr * 36)
_, q_SE = medianes(keyS, C['E'].astype(np.float64), nr * 36)
_, q_Slo = medianes(keyS, C['slo'].astype(np.float64), nr * 36)
_, q_Shi = medianes(keyS, C['shi'].astype(np.float64), nr * 36)
cobert = (cntS.reshape(nr, 36) >= 20).sum(axis=1)
mig = 0.5 * (edges[1:] + edges[:-1])
files = []
for i in range(nr):
    files.append(dict(r_in=round(float(edges[i]), 4), r_out=round(float(edges[i + 1]), 4), r_mid=round(float(mig[i]), 4), n_px=int(cnt[i]),
                      sectors_10deg_covered=int(cobert[i]), frac_sony_dominated=float(fsony[i]),
                      partial_ring_lunar_band=bool(edges[i] < FRANJA['r_vora_max_mesurat_Rsol']),
                      MSB_median=q_msb[50][i], MSB_p16=q_msb[16][i], MSB_p84=q_msb[84][i], MSB_noext_median=Q['noe'][i],
                      MSB_skyA_median=Q['msa'][i], MSB_k035_median=Q['k035'][i], MSB_k072_median=Q['k072'][i],
                      sigma_stat_px_median_propagated=Q['sst'][i], sigma_sys_lo_median=Q['slo'][i], sigma_sys_hi_median=Q['shi'][i],
                      sigma_sky_median=Q['ssk'][i], sky_bias_median=Q['bias'][i], E_median=Q['E'][i], sky_Bsun_median=q_sky[50][i],
                      **{f'MSB_median_centre_{k}': q_alt[k][i] for k in galt}))
camps = list(files[0].keys())
with open(OUT / 'perfil_azimutal_v2.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=camps); w.writeheader()
    for f in files:
        w.writerow({k: (f'{v:.6e}' if isinstance(v, float) else v) for k, v in f.items()})
with open(OUT / 'perfil_sectors_10graus_v2.csv', 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['r_in', 'r_out', 'pa_from', 'pa_to', 'n_px', 'MSB_median', 'MSB_noext_median', 'E_median', 'sigma_sys_lo_median', 'sigma_sys_hi_median'])
    for i in range(nr):
        for s_ in range(36):
            j = i * 36 + s_
            w.writerow([f'{edges[i]:.4f}', f'{edges[i + 1]:.4f}', s_ * 10, s_ * 10 + 10, int(cntS[j]), f'{q_S[50][j]:.6e}',
                        f'{q_Snoe[50][j]:.6e}', f'{q_SE[50][j]:.6f}', f'{q_Slo[50][j]:.6e}', f'{q_Shi[50][j]:.6e}'])
print(f'perfils fets ({time.time() - T0:.0f} s)', flush=True)

# ---------------------------------------------------------------- xifres clau i pressupost
V1 = json.load(open(mc.MAPA / 'PROVES_P3.json'))['xifres_clau']
sor = SOR['zones']['r_ge_8']
rho32 = max(sor['32']['rho_files'], sor['32']['rho_columnes'])
bk = CEL['biaix_KF'][AD]
var_dc0 = {k: v['dc0'] for k, v in bk.items()}
bias_lo = min(var_dc0.values()) / var_dc0['central']; bias_hi = max(var_dc0.values()) / var_dc0['central']
rel_const = dict(zp_lo=ZP['rel_lo'], zp_hi=ZP['rel_hi'], terme_color=ZP['terme_color_rel'], **m2.SIS_REL_SIM)
clau = {}
for r0 in (1.15, 1.5, 2.0, 3.0, 4.0, 5.0):
    lo, hi = 0.99 * r0, 1.01 * r0
    m = (C['r'] >= lo) & (C['r'] < hi)
    M = float(np.median(C['msb'][m]))
    sec = np.unique(si[m], return_counts=True)
    ext035 = float(np.median(C['k035'][m])) / M - 1; ext072 = float(np.median(C['k072'][m])) / M - 1
    e_up = max(ext035, ext072, 0.0); e_dn = max(-ext035, -ext072, 0.0)
    skyA = float(np.median(C['msa'][m])) / M - 1
    floor_rel = m2.SIGMA_SKY_FLOOR_BSOL * float(np.median(C['E'][m])) / M
    sky_rel = max(abs(skyA), floor_rel)
    alt = {}
    for k in galt:
        ma_ = (C['r_' + k] >= lo) & (C['r_' + k] < hi)
        alt[k] = float(np.median(C['msb'][ma_]))
    geo = max(abs(v / M - 1) for v in alt.values())
    nblk = m.sum() / 1024.0
    stat = rho32 * float(np.nanmedian(C['sst'][m])) / 32.0 / math.sqrt(max(nblk, 1.0)) / M
    bias_c = float(np.median(C['bias'][m])) / M
    terms_lo = [rel_const['zp_lo'], rel_const['terme_color'], *m2.SIS_REL_SIM.values(), e_dn, sky_rel, geo, stat]
    terms_hi = [rel_const['zp_hi'], rel_const['terme_color'], *m2.SIS_REL_SIM.values(), e_up, sky_rel, geo, stat]
    tlo = math.sqrt(sum(x * x for x in terms_lo)); thi = math.sqrt(sum(x * x for x in terms_hi))
    fs = float(C['sony'][m].mean())
    d = dict(anell=[lo, hi], n_px=int(m.sum()), sectors_10graus_amb_20px=int((sec[1] >= 20).sum()), frac_sony=fs,
             MSB=M, MSB_noext=float(np.median(C['noe'][m])), MSB_p16_p84_azimutal=[float(np.percentile(C['msb'][m], 16)), float(np.percentile(C['msb'][m], 84))],
             MSB_v1=V1[f'{r0:g}']['MSB'], quocient_v2_v1=M / V1[f'{r0:g}']['MSB'],
             MSB_cel_a=float(np.median(C['msa'][m])), E_mediana=float(np.median(C['E'][m])),
             cel_Bsun_mediana=float(np.median(m2.FAC_G * C['sky'][m])),
             termes_rel=dict(punt_zero_avall=rel_const['zp_lo'], punt_zero_amunt=rel_const['zp_hi'], terme_color=rel_const['terme_color'],
                             deriva=m2.SIS_REL_SIM['transparency_drift_in_totality'], color_i_cadena=m2.SIS_REL_SIM['colour_inversion_and_chain'],
                             flat=m2.SIS_REL_SIM['flat_field'], linealitat=m2.SIS_REL_SIM['linearity'],
                             extincio_k035=ext035, extincio_k072=ext072, cel_a_menys_adoptat=skyA, cel_terra=floor_rel, cel_usat=sky_rel,
                             geometria_centre=geo, estadistica_blocs=stat),
             total_avall=tlo, total_amunt=thi,
             biaix_cel_un_sol_sentit=dict(central=bias_c, forquilla=[bias_c * bias_lo, bias_c * bias_hi],
                                          nota='el mapa queda massa baix en aquesta fracció (model K+F dins del cel; no aplicat)'),
             fora_del_pressupost=dict(sony_rho=('~+20 % (calibratge propi de la Sony: 0,83 contra 0,95; sense resoldre)' if fs > 0.05 else 'no hi entra (Vixen sola)'),
                                      halo='sense model'),
             MSB_centres_alternatius=alt)
    clau[f'{r0:g}'] = d
    print(r0, f'MSB {M:.4e} (v1 {d["MSB_v1"]:.4e}, ×{d["quocient_v2_v1"]:.3f})  −{100 * tlo:.1f} % / +{100 * thi:.1f} %  biaix +{100 * bias_c:.1f} %  sony {fs:.2f}', flush=True)

# coherència amb research/76 §5.1 (verd, sense extinció)
R76 = {1.10: 47766.0, 1.50: 4937.0, 2.00: 809.0, 3.00: 175.0, 5.00: 37.0}
coh = {}
for r76, adu in R76.items():
    lo, hi = r76 * K76, (r76 + 0.02) * K76
    m = (C['r'] >= lo) & (C['r'] < hi)
    if m.sum() > 200:
        noe = float(np.median(C['noe'][m]))
        coh[f'{r76:.2f}'] = dict(n_px=int(m.sum()), nostre_MSB_noext=noe, research76_MSB=2.772e-11 * adu, quocient=noe / (2.772e-11 * adu))
rep = dict(guio='w4_perfils_v2.py', data_execucio=time.strftime('%Y-%m-%dT%H:%M:%S'), temps_s=time.time() - T0, pixels_valids=int(N),
           cel_adoptat=AD, franja_lunar=FRANJA, xifres_clau=clau, coherencia_research76_G_sense_extincio=coh,
           soroll_rho32_cel=rho32, biaix_variants_relatives_al_central=dict(lo=bias_lo, hi=bias_hi, dc0=var_dc0),
           punt_zero=ZP)
json.dump(rep, open(m2.MAPA2 / 'PROVES_W4.json', 'w'), indent=1, ensure_ascii=False, default=float)
json.dump(dict(descripcio=('Radial profiles of the calibrated MSB map, VERSION 2 (B/Bsun, total K+F, unpolarized, camera green). '
                           'Azimuthal medians over valid pixels; flags excluded: ' + ', '.join(k for k, b in mc.BITS.items() if b & mc.EXCLOU_PERFILS) +
                           f'. Rings with r_in < {FRANJA["r_vora_max_mesurat_Rsol"]:.3f} Rsun are partial (lunar-motion band at some PA).'),
               unitats='MSB = B/Bsun', r_unitats='Rsun (946.66 arcsec)', perfil_azimutal=files, xifres_clau=clau, franja_lunar=FRANJA,
               sectors_10graus=dict(vores_r=edges.tolist(), pa_inici=list(range(0, 360, 10)), n_px=cntS.reshape(nr, 36).tolist(),
                                    MSB_median=np.where(cntS > 0, q_S[50], np.nan).reshape(nr, 36).tolist())),
          open(OUT / 'perfils_msb_v2.json', 'w'), indent=1, ensure_ascii=False, default=float)
print(json.dumps(coh, indent=0), f'fet en {time.time() - T0:.0f} s')
