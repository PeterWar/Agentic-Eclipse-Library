"""cv2_2 · K-Cor contra el mapa v2 i prova de la línia verda Fe XIV (12-10-2026). Segueix PREDECLARACIO_COMPARACIONS_v2.md (A i B).

Referència K-Cor: la mitjana dels 7 fotogrames L2 pB de 15 s dins de la totalitat (com la v1). Model a la nostra variable:
pB/p(r) + s·F(r), píxel a píxel, mediana per casella d'1°. Només els anells 1,15–1,25 · 1,25–1,40 · 1,40–1,70 R☉
(més enllà d'1,7 R☉ el pB L2 d'aquell dia té un residu negatiu: no es fa servir).
Escriu v2/comparacions/kcor/KCOR_v2.json i kcor_caselles_v2.npz."""
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv2_comu as cv   # noqa: E402

mc, m2, cc1 = cv.mc, cv.m2, cv.cc1
T0 = time.time()
OUT = cv.RES2 / 'kcor'; OUT.mkdir(parents=True, exist_ok=True)
N = np.load(cv.RES2 / 'caselles_v2.npz')
AN = [tuple(a) for a in N['kcor_anells']]
NUS = cv.ANELLS_KCOR_US
usable = N['kcor_usable']
pa_c = np.arange(0.5, 360, 1.0)
pa_idx = np.arange(360)

# ---------------------------------------------------------------- K-Cor: referència, geometria i models
imgs = [cc1.carrega_kcor(s) for s in cc1.KCOR_TOT]
ref = np.mean([d for d, *_ in imgs], axis=0)
g0 = imgs[0][1]
yy, xx = np.mgrid[0:ref.shape[0], 0:ref.shape[1]].astype(np.float64)
rK, paK = g0.polar(xx, yy)
dins = (rK > 1.04) & (rK < 2.6)
Fpx = {'vdH1950': cc1.f_vdh1950(rK), 'KL1985': np.full_like(rK, np.nan)}
Fpx['KL1985'][dins] = cc1.f_kl1985(rK[dins], paK[dins])
ESCALES_F = (0.5, 0.7, 1.0, 1.3, 1.5)


def bins(img):
    _, q, _ = cc1.caselles_imatge(img, g0, AN)
    return q[50]


pb_bins = bins(ref)
Kb, Fb = {}, {}
for nomp in cc1.MODELS_DENSITAT:
    Kb[nomp] = bins(ref / cc1.p_de_r(rK, nomp))
for nomf, F in Fpx.items():
    Fb[nomf] = bins(F)
# model exacte per casella (mediana de K + s·F píxel a píxel) per a totes les combinacions
MOD = {}
for nomp in cc1.MODELS_DENSITAT:
    K = ref / cc1.p_de_r(rK, nomp)
    for nomf, F in Fpx.items():
        for s in ESCALES_F:
            MOD[(nomp, nomf, s)] = bins(K + s * F)
    print('model', nomp, f'({time.time() - T0:.0f} s)', flush=True)
MOD_SENSE_F = {nomp: Kb[nomp] for nomp in cc1.MODELS_DENSITAT}
# transferència de banda de la K (verd contra 735 nm), Baumbach–Allen, al centre de cada anell
T_banda = {}
for i in range(NUS):
    rm = 0.5 * (AN[i][0] + AN[i][1])
    vals = [cc1.transfer_banda_k(rm, cc1.MODELS_DENSITAT['Baumbach-Allen'], uG, uK) for uG in (0.60, 0.70) for uK in (0.45, 0.50)]
    T_banda[f'{AN[i][0]}-{AN[i][1]}'] = dict(min=float(min(vals)), max=float(max(vals)), mig=float(np.mean(vals)))
T_ADOPT = float(np.mean([v['mig'] for v in T_banda.values()]))
# residu negatiu del pB: perfil i desplaçament a 2,6–2,9 R☉
perf_pb = {}
for a, b in ((1.45, 1.55), (1.65, 1.75), (1.85, 1.95), (1.95, 2.05), (2.25, 2.35), (2.6, 2.9)):
    m = (rK >= a) & (rK < b) & np.isfinite(ref)
    perf_pb[f'{a}-{b}'] = dict(mediana=float(np.median(ref[m])), fraccio_negatius=float((ref[m] < 0).mean()))
DESPL = -perf_pb['2.6-2.9']['mediana']        # > 0: el que faltaria si el residu fos igual a dins
print('pB negatiu', perf_pb, flush=True)

# ---------------------------------------------------------------- sistemàtica del mapa v2 per anell (perfil azimutal v2)
import pandas as pd   # noqa: E402
AZ = pd.read_csv(m2.MAPA2 / 'perfils' / 'perfil_azimutal_v2.csv')
sis = {}
for i in range(NUS):
    a, b = AN[i]
    s_ = AZ[(AZ.r_mid >= a) & (AZ.r_mid < b) & np.isfinite(AZ.MSB_median)]
    sis[f'{a}-{b}'] = dict(lo=float(np.median(s_.sigma_sys_lo_median / s_.MSB_median)),
                           hi=float(np.median(s_.sigma_sys_hi_median / s_.MSB_median)))
PZ = m2.punt_zero()

# ---------------------------------------------------------------- A. quocients i pendents
nostra = {'amb_extincio': N['kcor_msb'], 'sense_extincio': N['kcor_noe']}
res = {}
forquilla = {}
for i in range(NUS):
    k = f'{AN[i][0]}-{AN[i][1]}'
    us = usable[i]
    principal = {}
    for ext, ours in nostra.items():
        y = np.where(us, ours[i], np.nan)
        principal[ext] = cv.estadistiques(y, MOD[('Baumbach-Allen', 'vdH1950', 1.0)][i], pa_idx)
    sense_f = cv.estadistiques(np.where(us, nostra['amb_extincio'][i], np.nan), MOD_SENSE_F['Baumbach-Allen'][i], pa_idx, pendents=False)
    amb_T = cv.estadistiques(np.where(us, nostra['amb_extincio'][i], np.nan),
                             T_ADOPT * Kb['Baumbach-Allen'][i] + Fb['vdH1950'][i], pa_idx, pendents=False)
    amb_desp = cv.estadistiques(np.where(us, nostra['amb_extincio'][i], np.nan),
                                bins((ref + DESPL) / cc1.p_de_r(rK, 'Baumbach-Allen') + Fpx['vdH1950'])[i], pa_idx, pendents=False)
    # forquilla: 3 densitats × 2 F × 5 escales × amb/sense extinció
    QM, MQ, QMi, MQi = [], [], [], []
    taula = []
    for (nomp, nomf, s), mod in MOD.items():
        for ext, ours in nostra.items():
            y = np.where(us, ours[i], np.nan); x = mod[i]
            ok = np.isfinite(y) & np.isfinite(x) & (x > 0)
            qm = float(np.median(y[ok]) / np.median(x[ok])); mq = float(np.median(y[ok] / x[ok]))
            QM.append(qm); MQ.append(mq)
            if 0.69 < s < 1.31:
                QMi.append(qm); MQi.append(mq)
            taula.append(dict(p=nomp, F=nomf, escala_F=s, nostra=ext, QM=qm, MQ=mq))
    lo, hi = min(min(QM), min(MQ)), max(max(QM), max(MQ))
    forquilla[k] = dict(QM=[min(QM), max(QM)], MQ=[min(MQ), max(MQ)], QM_F_30=[min(QMi), max(QMi)], MQ_F_30=[min(MQi), max(MQi)],
                        totes=[lo, hi],
                        totes_amb_punt_zero=[lo * (1 - sis[k]['lo']), hi * (1 + sis[k]['hi'])],
                        sistematica_mapa_v2=sis[k],
                        conte_1_amb_punt_zero=bool(lo * (1 - sis[k]['lo']) <= 1 <= hi * (1 + sis[k]['hi'])))
    pr = principal['amb_extincio']
    res[k] = dict(principal_BA_vdH_s1=principal, sense_F=sense_f, amb_transferencia_banda_T=dict(T=T_ADOPT, **amb_T),
                  si_el_pB_negatiu_fos_igual_a_dins=dict(desplacament_afegit=DESPL, **amb_desp),
                  amb_mediana_bootstrap_punt_zero=dict(QM=pr['quocient_medianes'] * (1 + PZ['rel']['p50']),
                                                       MQ=pr['mediana_quocients'] * (1 + PZ['rel']['p50'])),
                  totes_les_combinacions=taula)
    print(k, 'QM', round(pr['quocient_medianes'], 4), 'MQ', round(pr['mediana_quocients'], 4),
          'f', round(pr['pendent_c9'], 3), 'TS', round(pr['theil_sen'], 3), 'll', round(pr['pendent_loglog_theil_sen'], 3),
          'forquilla', [round(x, 3) for x in forquilla[k]['totes']], [round(x, 3) for x in forquilla[k]['totes_amb_punt_zero']], flush=True)

# ---------------------------------------------------------------- B1. vermell contra verd (pendents sense escala)
feXIV = {}
for i in range(NUS):
    k = f'{AN[i][0]}-{AN[i][1]}'
    us = usable[i]
    x = MOD[('Baumbach-Allen', 'vdH1950', 1.0)][i]
    yG = np.where(us, N['kcor_msb'][i], np.nan); yR = np.where(us, N['kcor_msbR'][i], np.nan)
    eG = cv.estadistiques(yG, x, pa_idx); eR = cv.estadistiques(yR, x, pa_idx)
    dif = cv.diferencia_pendents(yG, yR, x, pa_idx)
    # sense F (només pB/p), per si la F constant per anell hi té a veure
    xs = MOD_SENSE_F['Baumbach-Allen'][i]
    dif_sF = cv.diferencia_pendents(yG, yR, xs, pa_idx)
    feXIV[k] = dict(verd=eG, vermell=eR, diferencia_G_menys_R=dif, diferencia_G_menys_R_contra_pB_sobre_p=dif_sF)
    print(k, 'G: rel', round(eG['pendent_relativa_c9'], 3), 'll', round(eG['pendent_loglog_theil_sen'], 3),
          '| R: rel', round(eR['pendent_relativa_c9'], 3), 'll', round(eR['pendent_loglog_theil_sen'], 3),
          '| Δll', round(dif['dif_loglog'], 4), '±', round(dif['bootstrap_blocs_30']['dif_loglog_err'], 4), flush=True)

# ---------------------------------------------------------------- B2. color per casella contra AIA 211 (Fe XIV) i contra el pB
from astropy.io import fits   # noqa: E402
AIA = mc.ARREL / '3-RECERCA/data/externes_20261001/sdo_aia'


def aia_pa(ona, rr=(1.10, 1.25)):
    perfils = []
    info = []
    for hhmm in ('1828', '1830'):
        f = AIA / f'AIA20260812_{hhmm}_{ona}.fits'
        h = fits.open(f)[-1]; d = h.data.astype(np.float64) / float(h.header['EXPTIME']); hd = h.header
        ga = mc.Geo(hd['CRPIX1'] - 1, hd['CRPIX2'] - 1, float(hd['RSUN_OBS']) / float(hd['CDELT1']), (0, 1), (-1, 0))
        _, q, _ = cc1.caselles_imatge(d, ga, [rr])
        perfils.append(q[50][0])
        info.append(dict(fitxer=cv.rel(f), sha256=cv.sha256(f), DATE_OBS=hd.get('DATE-OBS'), EXPTIME=hd.get('EXPTIME'),
                         LVL_NUM=hd.get('LVL_NUM'), CROTA2=hd.get('CROTA2'), R_sol_px=float(hd['RSUN_OBS']) / float(hd['CDELT1'])))
    return 0.5 * (perfils[0] + perfils[1]), info, float(np.nanmedian(perfils[1] / perfils[0]))


aia211, info211, est211 = aia_pa('0211')
aia193, info193, est193 = aia_pa('0193')
tz = np.radians(pa_c - cv.PA_ZENIT)


def prova_color(c, z, us):
    """c = a + β z + γ cos(PA − PAz) + δ sin(PA − PAz); ρ de Spearman; nul amb girs de z de 30° a 330°."""
    from scipy.stats import spearmanr
    ok = us & np.isfinite(c) & np.isfinite(z)
    A = np.c_[np.ones(ok.sum()), z[ok], np.cos(tz[ok]), np.sin(tz[ok])]
    beta = float(np.linalg.lstsq(A, c[ok], rcond=None)[0][1])
    rho = float(spearmanr(c[ok], z[ok])[0])
    nb, nr = [], []
    for sft in range(30, 331):
        zs = np.roll(z, sft)
        o2 = ok & np.isfinite(zs)
        A2 = np.c_[np.ones(o2.sum()), zs[o2], np.cos(tz[o2]), np.sin(tz[o2])]
        nb.append(np.linalg.lstsq(A2, c[o2], rcond=None)[0][1]); nr.append(spearmanr(c[o2], zs[o2])[0])
    nb = np.array(nb); nr = np.array(nr)
    zq = z[ok]; cq = c[ok]
    alt = cq[zq >= np.percentile(zq, 75)]; baix = cq[zq <= np.percentile(zq, 25)]
    return dict(n=int(ok.sum()), beta=beta, rho_spearman=rho, p_beta_girs=float((nb >= beta).mean()), p_rho_girs=float((nr >= rho).mean()),
                beta_girs_p50_p95=[float(np.median(nb)), float(np.percentile(nb, 95))],
                rho_girs_p50_p95=[float(np.median(nr)), float(np.percentile(nr, 95))],
                c_quartil_alt_menys_baix=float(np.median(alt) - np.median(baix)),
                dispersio_c=float(1.4826 * np.median(np.abs(cq - np.median(cq)))))


color = {}
for i in range(NUS):
    k = f'{AN[i][0]}-{AN[i][1]}'
    us = usable[i]
    with np.errstate(invalid='ignore', divide='ignore'):
        c = np.log(N['kcor_msb'][i] / N['kcor_msbR'][i])
    c = c - np.nanmedian(np.where(us, c, np.nan))
    with np.errstate(invalid='ignore', divide='ignore'):
        zA = np.log(aia211) - np.nanmedian(np.log(aia211)); zA3 = np.log(aia193) - np.nanmedian(np.log(aia193))
        zP = np.log(pb_bins[i]) - np.nanmedian(np.log(np.where(us, pb_bins[i], np.nan)))
    color[k] = dict(traçador_AIA211=prova_color(c, zA, us), traçador_AIA193=prova_color(c, zA3, us), traçador_pB_KCor=prova_color(c, zP, us),
                    mediana_RG_MSB=float(np.nanmedian(np.where(us, N['kcor_msbR'][i] / N['kcor_msb'][i], np.nan))))
    print(k, 'color vs AIA211', {kk: (round(v, 4) if isinstance(v, float) else v) for kk, v in color[k]['traçador_AIA211'].items()}, flush=True)
    print(k, 'color vs pB', {kk: (round(v, 4) if isinstance(v, float) else v) for kk, v in color[k]['traçador_pB_KCor'].items()}, flush=True)
# PA dels màxims de l'AIA 211 (regions actives al limbe, informatiu)
z = np.log(aia211)
pics = [int(j) for j in np.argsort(-np.nan_to_num(z, nan=-99))[:40]]
pics_pa = sorted(set(int(round(p / 5.0) * 5) for p in pics))

# ---------------------------------------------------------------- sortides
np.savez_compressed(OUT / 'kcor_caselles_v2.npz', pb_ref=pb_bins, anells=np.array(AN), usable=usable, aia211=aia211, aia193=aia193,
                    **{f'K_{p}': v for p, v in Kb.items()}, **{f'F_{f}': v for f, v in Fb.items()},
                    model_BA_vdH_s1=MOD[('Baumbach-Allen', 'vdH1950', 1.0)])
cv.json_dump(dict(
    guio=cv.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'), predeclaracio=cv.rel(cv.RES2 / 'PREDECLARACIO_COMPARACIONS_v2.md'),
    referencia='mitjana dels 7 fotogrames L2 pB de 15 s dins de la totalitat', anells_usats=AN[:NUS],
    anells_no_usats={f'{a}-{b}': 'pB L2 negatiu o a prop del zero (residu del cel): no es fa servir' for a, b in AN[NUS:]},
    perfil_pB_negatiu=perf_pb, escales_F=ESCALES_F, transferencia_banda_K=T_banda, T_adoptada_un_sol_sentit=T_ADOPT,
    sistematica_mapa_v2_per_anell=sis, punt_zero=dict(rel=PZ['rel'], rel_lo=PZ['rel_lo'], rel_hi=PZ['rel_hi'], terme_color=PZ['terme_color_rel']),
    resultats=res, forquilla=forquilla, prova_FeXIV_pendents=feXIV, prova_FeXIV_color=color,
    AIA=dict(fitxers_211=info211, fitxers_193=info193, estabilitat_1830_sobre_1828=dict(a211=est211, a193=est193),
             anell='1,10–1,25 R☉', PA_dels_40_maxims_de_211_arrodonits_a_5=pics_pa),
    avisos=['Totes les ± són estadístiques (bootstrap per blocs de PA): no porten cap sistemàtica.',
            'El calibratge absolut del K-Cor no s\'ha trobat a la documentació llegida.',
            'Més enllà d\'1,7 R☉ el pB L2 d\'aquell dia no es fa servir (negatiu més enllà d\'1,95 R☉).',
            'MSB_R: el nivell absolut depèn del punt zero vermell (incert); només es fan servir pendents sense escala i colors relatius.'],
    entrades_sha256={**{cv.rel(cc1.D11 / 'kcor' / f'{s}_kcor_l2_pb.fts.gz'): cv.sha256(cc1.D11 / 'kcor' / f'{s}_kcor_l2_pb.fts.gz') for s in cc1.KCOR_TOT},
                     cv.rel(cv.RES2 / 'caselles_v2.npz'): cv.sha256(cv.RES2 / 'caselles_v2.npz'),
                     cv.rel(cc1.RES / 'models_f/F_KL1985_digitalitzat.json'): cv.sha256(cc1.RES / 'models_f/F_KL1985_digitalitzat.json'),
                     cv.rel(m2.MAPA2 / 'perfils' / 'perfil_azimutal_v2.csv'): cv.sha256(m2.MAPA2 / 'perfils' / 'perfil_azimutal_v2.csv')},
    segons=round(time.time() - T0, 1)), OUT / 'KCOR_v2.json')
print(f'fet ({time.time() - T0:.0f} s)')
