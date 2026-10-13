"""cv2_3 · LASCO C2 contra el mapa v2 (12-10-2026). Segueix PREDECLARACIO_COMPARACIONS_v2.md (C).

C2: la càrrega de la v1 (cmp_comu.carrega_c2: (DN − biaix)/(EXPTIME·expfac), vinyetatge c2vig_final.fts), mitjana per casella dels
fotogrames de 18:24:31 i 18:36:15, pilar de 288–360° fora. Dos calibratges SENSE preferència: SolarSoft c2_calfactor i
Colaninno & Howard 2015, eq. 8. Es comprova l'eq. 8 refent l'ajust ponderat de la seva Taula 2 (MJD de meitat d'any).
Quocients (QM i MQ) i pendents amb blocs de 10° i 30°; sensibilitat al cel (a, b_old, joint_c0fix; c contaminat, registre),
a k (0; 0,35; 0,40; 0,57; 0,72) i al biaix del cel (un sol sentit). Dipol cap al zenit per a cada cel × k.
Escriu v2/comparacions/lasco/LASCO_v2.json i c2_caselles_v2.npz."""
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv2_comu as cv   # noqa: E402

mc, m2, cc1 = cv.mc, cv.m2, cv.cc1
T0 = time.time()
OUT = cv.RES2 / 'lasco'; OUT.mkdir(parents=True, exist_ok=True)
N = np.load(cv.RES2 / 'caselles_v2.npz')
AN = [tuple(a) for a in N['c2_anells']]
pa_c = np.arange(0.5, 360, 1.0); pa_idx = np.arange(360)
pilar = (pa_c >= cv.PILAR[0]) & (pa_c < cv.PILAR[1])
usable = N['c2_usable'] & ~pilar[None, :]

# ---------------------------------------------------------------- C2
dns, infos, imgs = {}, [], {}
for f in cc1.C2_FITXERS:
    img, g, info = cc1.carrega_c2(f)
    _, q, _ = cc1.caselles_imatge(img, g, AN)
    dns[f] = q[50]; infos.append(info); imgs[f] = (img, g)
CAL = {'SolarSoft_c2_calfactor': cc1.calfac_ssw, 'Colaninno_Howard_2015_eq8': cc1.calfac_ch2015}
c2 = {nc: 0.5 * (dns[cc1.C2_FITXERS[0]] * fc(infos[0]['mjd']) + dns[cc1.C2_FITXERS[1]] * fc(infos[1]['mjd'])) for nc, fc in CAL.items()}

# ---------------------------------------------------------------- calibratges: 2013 contra 2026 i la Taula 2 de C&H
MJD_2013 = cv.mjd('2013-07-02T00:00:00'); MJD_OBS = infos[0]['mjd']
cal = dict(MJD_2013_5=MJD_2013, MJD_obs=MJD_OBS,
           SSW_2013=cc1.calfac_ssw(MJD_2013), CH_2013=cc1.calfac_ch2015(MJD_2013),
           SSW_2026=cc1.calfac_ssw(MJD_OBS), CH_2026=cc1.calfac_ch2015(MJD_OBS))
cal['CH_sobre_SSW_2013'] = cal['CH_2013'] / cal['SSW_2013']
cal['CH_sobre_SSW_2026'] = cal['CH_2026'] / cal['SSW_2026']
cal['pujada_CH_2013_2026'] = cal['CH_2026'] / cal['CH_2013'] - 1
cal['pujada_SSW_2013_2026'] = cal['SSW_2026'] / cal['SSW_2013'] - 1
T2 = np.array(cv.CH2015_TAULA2, float)
mjd_any = np.array([cv.mjd(f'{int(y)}-07-02T00:00:00') for y in T2[:, 0]])


def ajust_t2(sel, pes=True):
    x = mjd_any[sel]; y = T2[sel, 2]; s = T2[sel, 3]
    w = 1 / s ** 2 if pes else np.ones(sel.sum())
    A = np.c_[x, np.ones(sel.sum())]
    Aw = A * np.sqrt(w)[:, None]; yw = y * np.sqrt(w)
    c, *_ = np.linalg.lstsq(Aw, yw, rcond=None)
    res = y - A @ c; chi2 = float((w * res ** 2).sum()); dof = sel.sum() - 2
    cov = np.linalg.inv(Aw.T @ Aw) * (chi2 / dof if pes else (res ** 2).sum() / dof)
    v26 = c[0] * MJD_OBS + c[1]; e26 = float(np.sqrt(np.array([MJD_OBS, 1]) @ cov @ np.array([MJD_OBS, 1])))
    return dict(pendent_per_dia=float(c[0]), ordenada=float(c[1]), pendent_err=float(np.sqrt(cov[0, 0])), ordenada_err=float(np.sqrt(cov[1, 1])),
                chi2_reduida=chi2 / dof if pes else None, n=int(sel.sum()), valor_2026=float(v26), err_2026=e26,
                pujada_percent_per_any=float(100 * c[0] * 365.25 / (c[0] * MJD_2013 + c[1])))


tot = np.ones(len(T2), bool); sense96 = T2[:, 0] > 1996.5
cal['refit_taula2'] = dict(ponderat=ajust_t2(tot), ponderat_sense_1996=ajust_t2(sense96), sense_pesos=ajust_t2(tot, False),
                           eq8_llegida='PCF = (3,9 [±0,5]·1e-5·MJD + 5,2 [±0,3])·1e-12 (imatge de l\'equació a PMC4479163)',
                           conveni_MJD='MJD estàndard (dies): amb l\'MJD de meitat d\'any l\'ordenada surt 5,2, com l\'eq. 8; amb un altre origen '
                                       '(p. ex. dies des del 1996) sortiria ~7,1. Sencer o fraccionari: diferència < 1e-5 relativa.')
cal['vinyetatge'] = ('C&H 2015 (§3): «we used the vignetting correction that is available through the SSW routine»; no anomenen el fitxer. '
                     'El 2013–2014 SolarSoft feia servir per al C2 Orange/Clear c2vig_final.fts («entire mission», disponible des del juny del '
                     '2005; la capçalera del nostre fitxer diu DATE 05/09/20). És, doncs, MOLT PROBABLEMENT la mateixa funció que fem servir; '
                     'no s\'ha pogut llegir c2_calibrate.pro d\'aquell moment per confirmar-ho línia a línia. C&H avisen que «the normalization '
                     'of the vignetting correction is only poorly defined».')
cal['tercer_punt_Llebaria_2021'] = ('Llebaria et al. 2021, Sol. Phys. 296, 53 (doi 10.1007/s11207-021-01800-w; arXiv 2011.12920) NO dona un factor '
                                    'de calibratge numèric ni una llei amb el temps: només el mètode (estrelles), una exactitud < 1 % i '
                                    'productes de 1996–2019. Remet a Lamy et al. 2020, la Fig. 9 de la qual dona el factor només en gràfic '
                                    '(eix 6,6–8,0 × 1e-12) fins al 2019. No hi ha tercer punt utilitzable per al 2026.')
cal['context_text_CH'] = ('C&H 2015 (text): el seu PCF és un 17–19 % més gran que el de SolarSoft; Gardès, Lamy & Llebaria 2013 (estrelles, '
                          'independent) també queda un 15–19 % per sobre de SolarSoft; la mitjana 1999–2009 de C&H és 7,30 ± 0,08 i la de '
                          'GLL13 7,36 (1e-12). Lamy et al. 2020: salts de −3,5 % (1999) i +1,3 % (2010) no modelats per una recta.')
print('calibratges', {k: v for k, v in cal.items() if not isinstance(v, (dict, str))}, flush=True)
print('refit', cal['refit_taula2']['ponderat'], flush=True)

# ---------------------------------------------------------------- sistemàtica del mapa v2 per anell
import pandas as pd   # noqa: E402
AZ = pd.read_csv(m2.MAPA2 / 'perfils' / 'perfil_azimutal_v2.csv')
sis = {}
for a, b in AN:
    s_ = AZ[(AZ.r_mid >= a) & (AZ.r_mid < b) & np.isfinite(AZ.MSB_median)]
    sis[f'{a}-{b}'] = dict(lo=float(np.median(s_.sigma_sys_lo_median / s_.MSB_median)), hi=float(np.median(s_.sigma_sys_hi_median / s_.MSB_median)),
                           biaix_cel=float(np.median(s_.sky_bias_median / s_.MSB_median)), sony=float(np.median(s_.frac_sony_dominated)))

# ---------------------------------------------------------------- quocients
VARIANTS = {'b_new_k040 (adoptat)': N['c2_msb'], 'b_new_k000 (sense extinció)': N['c2_noe'],
            'b_new_k035': N['c2_b_new_k035'], 'b_new_k057': N['c2_b_new_k057'], 'b_new_k072': N['c2_b_new_k072'],
            'a_k040 (cel constant)': N['c2_a_k040'], 'b_old_k040 (cel de la v1)': N['c2_b_old_k040'],
            'joint_c0fix_k040 (post hoc)': N['c2_joint_c0fix_k040'], 'c_k040 (CONTAMINAT, registre)': N['c2_c_k040'],
            'b_new_k040 + biaix del cel (central)': N['c2_msb'] + N['c2_sky_bias'],
            'b_new_k040 + biaix del cel (màxim de les variants)': N['c2_msb'] + N['c2_sky_bias_max']}
res = {}
for i, (a, b) in enumerate(AN):
    k = f'{a}-{b}'
    res[k] = {}
    for nc in CAL:
        x = np.where(usable[i], c2[nc][i], np.nan)
        res[k][nc] = {}
        for nv, ours in VARIANTS.items():
            y = np.where(usable[i], ours[i], np.nan)
            res[k][nc][nv] = cv.estadistiques(y, x, pa_idx, pendents=nv.startswith('b_new_k040 (adoptat)'))
        for f in cc1.C2_FITXERS:
            x1 = np.where(usable[i], dns[f][i] * CAL[nc]([inf for inf in infos if inf['fitxer'] == f][0]['mjd']), np.nan)
            res[k][nc][f'fotograma {f}'] = cv.estadistiques(np.where(usable[i], N['c2_msb'][i], np.nan), x1, pa_idx, pendents=False)
    p = res[k]
    print(k, 'SSW QM/MQ', round(p['SolarSoft_c2_calfactor']['b_new_k040 (adoptat)']['quocient_medianes'], 3),
          round(p['SolarSoft_c2_calfactor']['b_new_k040 (adoptat)']['mediana_quocients'], 3),
          '| C&H', round(p['Colaninno_Howard_2015_eq8']['b_new_k040 (adoptat)']['quocient_medianes'], 3),
          round(p['Colaninno_Howard_2015_eq8']['b_new_k040 (adoptat)']['mediana_quocients'], 3),
          '| pendent C&H', round(p['Colaninno_Howard_2015_eq8']['b_new_k040 (adoptat)']['pendent_c9'], 3), flush=True)

# ---------------------------------------------------------------- dipol condicionat al cel
CELS = ('b_new', 'a', 'b_old', 'joint_c0fix', 'joint', 'c')
dip = {}
for s_ in CELS:
    dip[s_] = {}
    for kk in ((0.0, 0.35, 0.40, 0.57, 0.72) if s_ == 'b_new' else (0.0, 0.40, 0.57, 0.72)):
        nom = f'c2_{s_}_k{int(round(100 * kk)):03d}'
        dip[s_][f'{kk:.2f}'] = {}
        for i, (a, b) in enumerate(AN):
            y = np.where(usable[i] & (N[nom][i] > 0), N[nom][i], np.nan)
            with np.errstate(invalid='ignore', divide='ignore'):
                d = cv.dipol2(np.log(y / c2['SolarSoft_c2_calfactor'][i]), pa_c)
            d['caselles_no_positives'] = int((usable[i] & ~(N[nom][i] > 0)).sum())
            dip[s_][f'{kk:.2f}'][f'{a}-{b}'] = d
pred = {f'{kk:.2f}': {f'{a}-{b}': cv.dipol(kk / 0.40 * np.log(np.where(usable[i], N['c2_E'][i], np.nan)), pa_c)['cap_al_zenit']
                      for i, (a, b) in enumerate(AN)} for kk in (0.35, 0.40, 0.57, 0.72)}
with np.errstate(invalid='ignore', divide='ignore'):
    nul = {f'{a}-{b}': cv.dipol(np.log(np.where(usable[i], dns[cc1.C2_FITXERS[1]][i] / dns[cc1.C2_FITXERS[0]][i], np.nan)), pa_c)['cap_al_zenit']
           for i, (a, b) in enumerate(AN)}
DW = json.load(open(m2.MAPA2 / 'dipol_c2' / 'DIPOL_C2_v2.json'))
control_dipol = {}
for s_ in ('b_new', 'a', 'b_old', 'c'):
    for kz in ('0.00', '0.40', '0.57', '0.72'):
        for kk, d in dip[s_][kz].items():
            dw = DW['dipol'][s_][kz][kk]
            if 'cap_al_zenit' in d and 'cap_al_zenit' in dw:
                control_dipol[f'{s_} k{kz} {kk}'] = abs(d['cap_al_zenit'] - dw['cap_al_zenit'])
control = dict(max_dif_dipol_contra_mapa_v2=float(max(control_dipol.values())), n=len(control_dipol))
print('control dipol contra DIPOL_C2_v2.json', control, flush=True)
for s_ in CELS:
    print(s_, {kz: [round(v.get('cap_al_zenit', np.nan), 3) for v in dd.values()] for kz, dd in dip[s_].items()}, flush=True)

# ---------------------------------------------------------------- perfil del C2 als anells fins (figura)
FIGR = [tuple(a) for a in N['fig_anells']]
fig_c2 = {}
for nc, fc in CAL.items():
    per = []
    for f, inf in zip(cc1.C2_FITXERS, infos):
        img, g = imgs[f]
        _, q, _ = cc1.caselles_imatge(img, g, FIGR)
        per.append(q[50] * fc(inf['mjd']))
    fig_c2[nc] = 0.5 * (per[0] + per[1])
fig_us = N['fig_usable'] & ~pilar[None, :]
np.savez_compressed(OUT / 'c2_caselles_v2.npz', anells=np.array(AN), usable=usable, fig_anells=np.array(FIGR), fig_usable=fig_us,
                    **{f'c2_{nc}': v for nc, v in c2.items()}, **{f'fig_{nc}': v for nc, v in fig_c2.items()})
entr = {cv.rel(cc1.D01 / 'soho_lasco' / f): cv.sha256(cc1.D01 / 'soho_lasco' / f) for f in cc1.C2_FITXERS}
entr[cv.rel(cc1.D01 / 'lasco_calib/c2vig_final.fts')] = cv.sha256(cc1.D01 / 'lasco_calib/c2vig_final.fts')
entr[cv.rel(cc1.D11 / 'lasco_calib/c2_expfactor_260812.dat')] = cv.sha256(cc1.D11 / 'lasco_calib/c2_expfactor_260812.dat')
entr[cv.rel(cv.RES2 / 'caselles_v2.npz')] = cv.sha256(cv.RES2 / 'caselles_v2.npz')
entr[cv.rel(m2.MAPA2 / 'dipol_c2' / 'DIPOL_C2_v2.json')] = cv.sha256(m2.MAPA2 / 'dipol_c2' / 'DIPOL_C2_v2.json')
cv.json_dump(dict(guio=cv.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'), predeclaracio=cv.rel(cv.RES2 / 'PREDECLARACIO_COMPARACIONS_v2.md'),
                  fotogrames=infos, referencia='mitjana per casella de 18:24:31 i 18:36:15', pilar=cv.PILAR, PA_zenit=cv.PA_ZENIT,
                  calibratges=cal, sistematica_mapa_v2_per_anell=sis, resultats=res,
                  dipol=dict(definicio='dipol de ln(nostra/C2) cap al zenit; positiu = la nostra més brillant cap al zenit; σ amb blocs de 10 i 30',
                             per_cel_i_k=dip, prediccio_lnE=pred, control_nul_C2_1836_sobre_1824=nul, control_contra_mapa_v2=control),
                  avisos=['Totes les ± són estadístiques (bootstrap per blocs de PA).', 'Cap dels dos calibratges es privilegia.',
                          'Fora d\'1,9 R☉ el nostre mapa és Sony·ρ; el calibratge propi de la Sony donaria ~+20 % (no resolt, no al pressupost).',
                          'El model de cel c és contaminat de corona: només registre.', 'El joint predeclarat no és calculable (cel > G).',
                          'Banda: verd de càmera contra Orange del C2; la transferència no es pot fixar (prova de banda no concloent).'],
                  entrades_sha256=entr, segons=round(time.time() - T0, 1)), OUT / 'LASCO_v2.json')
print(f'fet ({time.time() - T0:.0f} s)')
