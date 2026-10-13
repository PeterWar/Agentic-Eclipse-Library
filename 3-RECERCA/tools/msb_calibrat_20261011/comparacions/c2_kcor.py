"""c2 · Comparació A: la nostra brillantor total (MSB) contra el K-Cor L2 (pB en B/B☉ mitjà): pB/p(r) + F(r). Encàrrec «comparacions», 11-10-2026.

1. Capçaleres (BUNIT, RSUN, CRPIX, CDELT, INST_ROT, P aplicat): geometria des del WCS (nord solar amunt). Prova d'anada i tornada.
2. Referència ADOPTADA (predeclarada): la mitjana dels 7 fotogrames de 15 s dins de la totalitat (18:28:46 … 18:30:17).
   Prova d'estabilitat: cada fotograma, els dos controls (18:28:31, 18:30:33) i les dues mitjanes de 2 min contra la referència.
3. Caselles d'1° als anells 1,15–1,25 · 1,25–1,40 · 1,40–1,70 · 1,70–2,00 · 2,0–2,5 R☉ (més l'1,10–1,15 de la c9, només informatiu);
   fora tota casella que toqui la franja lunar, el buit del limbe, una protuberància o el fantasma (c1_caselles_nostra.py).
   L'ocultador del K-Cor (RCAM_DCR 178,8 px ≈ 1,05 R☉) queda per sota de tots els anells: es comprova.
4. Model del K-Cor a la nostra variable: B_K+F = pB/p(r) + F(r), píxel a píxel, i mediana per casella.
   p: van de Hulst (u = 0,56) per a tres models de densitat; F: van de Hulst 1950 (eq. 7) i Koutchmy & Lamy 1985 (Fig. 3), i sense F.
5. Quocients (mediana nostra / mediana model sobre les mateixes caselles, i mediana dels quocients) i pendents robustes
   (la regressió de la c9 i Theil–Sen), amb i sense correcció d'extinció.
6. La GIF de la c9 (inversió «Intensity^0,8») tornada a passar per les MATEIXES caselles: el canvi GIF → FITS.
Escriu comparacions/kcor/."""
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cmp_comu as cc   # noqa: E402

mc = cc.mc
T0 = time.time()
OUT = cc.RES / 'kcor'; OUT.mkdir(parents=True, exist_ok=True)
N = np.load(cc.RES / 'caselles_nostra.npz')
AN = [tuple(a) for a in N['kcor_anells']]
usable = N['kcor_usable']
nostra = {'amb_extincio': N['kcor_msb'], 'sense_extincio': N['kcor_noe']}

# ---------------------------------------------------------------- 1. capçaleres i geometria
cap = {}
imgs = {}
for stem in cc.KCOR_TOT + cc.KCOR_CTRL:
    d, g, hd, f = cc.carrega_kcor(stem)
    imgs[stem] = (d, g)
    cap[stem] = dict(fitxer=cc.rel(f), sha256=cc.sha256(f), **{k: hd.get(k) for k in (
        'DATE-OBS', 'DATE-END', 'BUNIT', 'WAVELNTH', 'WAVEFWHM', 'CRPIX1', 'CRPIX2', 'CDELT1', 'CDELT2', 'RSUN_OBS', 'R_SUN', 'INST_ROT',
        'SOLAR_P0', 'RCAM_DCR', 'TCAM_DCR', 'QUALITY', 'LEVEL', 'DPSWID', 'CALFILE', 'SKYPOLRM', 'SKYTRANS', 'BIASCORR', 'BOPAL')})
for stem in cc.KCOR_AVG:
    d, g, hd, f = cc.carrega_kcor(stem, avg=True)
    imgs[stem + '_avg'] = (d, g)
    cap[stem + '_avg'] = dict(fitxer=cc.rel(f), sha256=cc.sha256(f), AVGTIME=str(hd.get('AVGTIME', ''))[:200],
                              **{k: hd.get(k) for k in ('DATE-OBS', 'DATE-END', 'BUNIT', 'CRPIX1', 'CRPIX2', 'CDELT1', 'RSUN_OBS', 'R_SUN', 'INST_ROT')})
g0 = imgs[cc.KCOR_TOT[0]][1]
geo_ok = all(np.allclose([imgs[k][1].cx, imgs[k][1].cy, imgs[k][1].R], [g0.cx, g0.cy, g0.R]) for k in imgs)
rr = np.array([1.1, 1.5, 2.0, 2.9]); pp = np.array([0.0, 77.0, 200.0, 333.0]); x, y = g0.px(rr, pp); r2, p2 = g0.polar(x, y)
prova_geo = dict(centre_0based=(g0.cx, g0.cy), R_sol_px=g0.R, nord=list(map(float, g0.n)), est=list(map(float, g0.e)),
                 geometria_igual_a_tots=bool(geo_ok), anada_tornada_max_r=float(np.max(np.abs(r2 - rr))),
                 anada_tornada_max_pa=float(np.max(np.abs((p2 - pp + 180) % 360 - 180))),
                 ocultador_R_sol=float(max(cap[cc.KCOR_TOT[0]]['RCAM_DCR'], cap[cc.KCOR_TOT[0]]['TCAM_DCR']) / g0.R))
print('geometria K-Cor', prova_geo, flush=True)

# ---------------------------------------------------------------- 2. referència i estabilitat
ref = np.mean([imgs[s][0] for s in cc.KCOR_TOT], axis=0)
nb, qref, (rK, paK) = cc.caselles_imatge(ref, g0, AN)
pb_ref = qref[50]
estab = {}
for k in cc.KCOR_TOT + cc.KCOR_CTRL + [s + '_avg' for s in cc.KCOR_AVG]:
    _, q, _ = cc.caselles_imatge(imgs[k][0], imgs[k][1], AN)
    fila = []
    for i, a in enumerate(AN):
        ok = usable[i] & np.isfinite(q[50][i]) & np.isfinite(pb_ref[i]) & (pb_ref[i] > 0)
        rq = q[50][i][ok] / pb_ref[i][ok]
        fila.append(dict(anell=list(a), n=int(ok.sum()), mediana_quocient=float(np.median(rq)) if ok.any() else None,
                         dispersio_robusta=float(1.4826 * np.median(np.abs(rq - np.median(rq)))) if ok.any() else None))
    estab[k] = fila
print('estabilitat (mediana del quocient contra la mitjana dels 7):', flush=True)
for k, v in estab.items():
    print('  ', k, ' '.join((f"{x['mediana_quocient']:.4f}±{x['dispersio_robusta']:.4f}" if x['mediana_quocient'] is not None else f"— (n {x['n']})") for x in v), flush=True)

# ---------------------------------------------------------------- 3–5. model pB/p + F i quocients
F_px = {'cap': np.zeros_like(rK), 'vdH1950': cc.f_vdh1950(rK), 'KL1985': np.full_like(rK, np.nan)}
dins = (rK > 1.04) & (rK < 2.6)
F_px['KL1985'][dins] = cc.f_kl1985(rK[dins], paK[dins])
res = {}
mod_bins = {}
for nomp in cc.MODELS_DENSITAT:
    p = cc.p_de_r(rK, nomp)
    K = ref / p
    for nomf, F in F_px.items():
        tot = K + F
        _, q, _ = cc.caselles_imatge(tot, g0, AN)
        mod_bins[(nomp, nomf)] = q[50]
        for ext, ours in nostra.items():
            for i, a in enumerate(AN):
                y = np.where(usable[i], ours[i], np.nan); x = q[50][i]
                qq = cc.quocients(y, x)
                rg = cc.regressio(x, y)
                res.setdefault(f'{a[0]}-{a[1]}', []).append(dict(p_model=nomp, F_model=nomf, nostra=ext, **qq,
                                                                 regressio=rg))
# p per anell (mediana dels píxels) per al resum
p_anell = {nomp: [float(np.nanmedian(cc.p_de_r(rK[(rK >= a) & (rK < b)], nomp))) for a, b in AN] for nomp in cc.MODELS_DENSITAT}
F_anell = {nomf: [float(np.nanmedian(F_px[nomf][(rK >= a) & (rK < b)])) for a, b in AN] for nomf in F_px}
K_frac = {}
for i, a in enumerate(AN):
    ok = usable[i]
    K_ = np.nanmedian(pb_ref[i][ok] / p_anell['Baumbach-Allen'][i])
    K_frac[f'{a[0]}-{a[1]}'] = {nomf: float(F_anell[nomf][i] / (K_ + F_anell[nomf][i])) for nomf in F_px}

# ---------------------------------------------------------------- 6. GIF de la c9 contra FITS (mateixes caselles)
gif, gG = cc.carrega_gif_c9()
_, qg, _ = cc.caselles_imatge(gif, gG, AN)
avg = imgs['20260812_182932_avg']
_, qa, _ = cc.caselles_imatge(avg[0], avg[1], AN)
gif_fits = []
for i, a in enumerate(AN):
    ok = usable[i] & np.isfinite(qg[50][i]) & np.isfinite(qa[50][i]) & (qa[50][i] > 0)
    fila = dict(anell=list(a), caselles_gif=int(ok.sum()))
    if ok.sum() >= 5:
        rq = qg[50][i][ok] / qa[50][i][ok]
        fila.update(pB_gif_sobre_pB_fits_avg_mediana=float(np.median(rq)), dispersio=float(1.4826 * np.median(np.abs(rq - np.median(rq)))))
    gif_fits.append(fila)
# models píxel a píxel a la GIF i a la mitjana de 2 min (per comparar amb el que feia la c9: pB/p, sense F)
yyG, xxG = np.mgrid[0:gif.shape[0], 0:gif.shape[1]].astype(np.float64)
rG, paG = gG.polar(xxG, yyG)
yyA, xxA = np.mgrid[0:avg[0].shape[0], 0:avg[0].shape[1]].astype(np.float64)
rA, paA = avg[1].polar(xxA, yyA)
taula_gif = []
for nomf in ('cap', 'vdH1950', 'KL1985'):
    FG = cc.f_vdh1950(rG) if nomf == 'vdH1950' else (np.zeros_like(rG) if nomf == 'cap' else np.where((rG > 1.04) & (rG < 2.6), cc.f_kl1985(np.clip(rG, 1.04, 2.59), paG), np.nan))
    FA = cc.f_vdh1950(rA) if nomf == 'vdH1950' else (np.zeros_like(rA) if nomf == 'cap' else np.where((rA > 1.04) & (rA < 2.6), cc.f_kl1985(np.clip(rA, 1.04, 2.59), paA), np.nan))
    pG = cc.p_de_r(rG, 'Baumbach-Allen'); pA = cc.p_de_r(rA, 'Baumbach-Allen')
    _, qGm, _ = cc.caselles_imatge(gif / pG + FG, gG, AN)
    _, qAm, _ = cc.caselles_imatge(avg[0] / pA + FA, avg[1], AN)
    for i, a in enumerate(AN):
        ok = usable[i] & np.isfinite(qGm[50][i]) & np.isfinite(qAm[50][i])
        if ok.sum() < 5:
            taula_gif.append(dict(anell=list(a), F_model=nomf, caselles=int(ok.sum()))); continue
        for ext, ours in nostra.items():
            y = np.where(ok, ours[i], np.nan)
            taula_gif.append(dict(anell=list(a), F_model=nomf, nostra=ext, caselles=int(ok.sum()),
                                  amb_GIF=cc.quocients(y, np.where(ok, qGm[50][i], np.nan))['quocient_medianes'],
                                  amb_FITS_avg_182932=cc.quocients(y, np.where(ok, qAm[50][i], np.nan))['quocient_medianes'],
                                  amb_FITS_mitjana_7=cc.quocients(y, np.where(ok, mod_bins[('Baumbach-Allen', nomf)][i], np.nan))['quocient_medianes']))
c9_vell = json.load(open(cc.RES01 / 'brillantor/C9_BRILLANTOR.json'))['anells_kcor']

# ---------------------------------------------------------------- sortides
np.savez_compressed(OUT / 'kcor_caselles.npz', pb_ref=pb_ref, anells=np.array(AN), usable=usable,
                    **{f'model_{a}_{b}': v for (a, b), v in mod_bins.items()}, pb_gif=qg[50], pb_avg_182932=qa[50])
json.dump(dict(
    guio=cc.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'),
    capcaleres=cap, geometria=prova_geo,
    referencia='mitjana dels 7 fotogrames L2 pB de 15 s dins de la totalitat (predeclarat)',
    estabilitat=estab,
    p_mediana_per_anell=p_anell, F_mediana_per_anell=F_anell, fraccio_F_del_total_model=K_frac,
    resultats=res,
    gif_contra_fits=dict(pB_per_casella=gif_fits, quocients=taula_gif,
                         c9_original_01_10=c9_vell,
                         nota='c9 (01-10): nostra = LUM·FAC − cel (transferència Q, R☉ 959″ per a la luminància), pB de la GIF / p, SENSE F, '
                              'anells 1,10–1,15 / 1,15–1,25 / 1,25–1,40, mostreig bilineal de 48 punts per casella; aquí: mapa MSB nou, '
                              'píxels per casella, caselles que toquen la franja o les protuberàncies FORA'),
    entrades_sha256={cc.rel(cc.RES / 'caselles_nostra.npz'): cc.sha256(cc.RES / 'caselles_nostra.npz'),
                     cc.rel(cc.D01 / 'kcor' / cc.GIF_C9): cc.sha256(cc.D01 / 'kcor' / cc.GIF_C9),
                     cc.rel(cc.RES / 'models_f/F_KL1985_digitalitzat.json'): cc.sha256(cc.RES / 'models_f/F_KL1985_digitalitzat.json')},
    segons=round(time.time() - T0, 1)), open(OUT / 'KCOR.json', 'w'), indent=1, ensure_ascii=False, default=float)

print('\nquocient de medianes (nostra / (pB/p + F)), Baumbach-Allen, amb extinció:')
for an, L in res.items():
    s = []
    for d in L:
        if d['p_model'] == 'Baumbach-Allen' and d['nostra'] == 'amb_extincio' and 'quocient_medianes' in d:
            s.append(f"{d['F_model']}: {d['quocient_medianes']:.3f} (n {d['n']}, f {d['regressio']['f']:.3f}±{d['regressio']['f_err']:.3f}, TS {d['regressio']['theil_sen']:.3f})")
    print(an, ' | '.join(s))
print('GIF contra FITS:'); [print(x) for x in gif_fits]
print(f'fet ({time.time() - T0:.0f} s)')
