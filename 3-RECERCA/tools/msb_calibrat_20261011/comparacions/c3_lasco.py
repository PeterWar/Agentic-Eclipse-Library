"""c3 · Comparació B: la nostra brillantor total (MSB, menys el cel) contra la brillantor total del LASCO C2 (K + F, sense polaritzar, Orange).
Encàrrec «comparacions», 11-10-2026.

C2: comu_comp.carrega_lasco (01-10) + factor d'exposició i biaix de la taula oficial c2_expfactor_260812.dat:
    B = (DN − biaix)·calfac/(EXPTIME·expfac)·vig    (c2_calibrate.pro + get_exp_factor.pro; vig = c2vig_final.fts, 0–100)
Dos calibratges (predeclarats): SolarSoft c2_calfactor (6,5618e-12 a l'MJD 61264) i Colaninno & Howard 2015, eq. (8) (extrapolada).
Referència: la MITJANA, casella a casella, dels dos fotogrames que envolten la totalitat (18:24:31 i 18:36:15). Cadascun es dona a part.
Anells de la c9 (2,4–2,6 … 4,5–5,5 R☉), caselles d'1°, pilar 288–360° fora, i fora tota casella que toqui el fantasma de la Sony.
Quocients i pendents amb i sense extinció; sensibilitat al model de cel (a, c).
Dipol cap al zenit (PROVA de la correcció, no ajust): ln q(PA) = c0 + a·cos PA + b·sin PA per anell, abans i després de corregir;
projecció sobre la direcció del zenit (PA 33,21°); predicció = el mateix ajust sobre ln E; control nul = ln(C2 18:36/C2 18:24).
Escriu comparacions/lasco/."""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cmp_comu as cc   # noqa: E402

mc = cc.mc
T0 = time.time()
OUT = cc.RES / 'lasco'; OUT.mkdir(parents=True, exist_ok=True)
N = np.load(cc.RES / 'caselles_nostra.npz')
PA_ZENIT = 33.21     # capçalera PAZENITH del FITS del mapa (p2_mapa.py)


def bins_c2(anells):
    out = {}
    infos = []
    for f in cc.C2_FITXERS:
        img, g, info = cc.carrega_c2(f)
        _, q, _ = cc.caselles_imatge(img, g, anells)
        out[f] = q[50]
        infos.append(info)
    return out, infos


AN = [tuple(a) for a in N['c2_anells']]
dns, infos = bins_c2(AN)
pa_c = np.arange(0.5, 360, 1.0)
pilar = (pa_c >= cc.PILAR[0]) & (pa_c < cc.PILAR[1])
usable = N['c2_usable'] & ~pilar[None, :]
CAL = {'SSW_c2_calfactor': cc.calfac_ssw, 'Colaninno_Howard_2015_eq8': cc.calfac_ch2015}
c2 = {}
for nc, fcal in CAL.items():
    per = [dns[f] * fcal(info['mjd']) for f, info in zip(cc.C2_FITXERS, infos)]
    c2[nc] = dict(mitjana=0.5 * (per[0] + per[1]), **{f: p for f, p in zip(cc.C2_FITXERS, per)})
nostra = {'amb_extincio': N['c2_msb'], 'sense_extincio': N['c2_noe'], 'cel_a_amb_extincio': N['c2_skyA'], 'cel_c_amb_extincio': N['c2_skyC'],
          'k035': N['c2_k035'], 'k072': N['c2_k072']}


def dipol(lnq, pa, nboot=400, llavor=3):
    ok = np.isfinite(lnq)
    if ok.sum() < 30:
        return None
    y = lnq[ok]; t = np.radians(pa[ok])
    A = np.c_[np.ones(ok.sum()), np.cos(t), np.sin(t)]
    w = np.ones(ok.sum(), bool)
    for _ in range(4):
        c, *_ = np.linalg.lstsq(A[w], y[w], rcond=None); res = y - A @ c; sd = 1.4826 * np.median(np.abs(res[w])); w = np.abs(res) < 3 * sd
    tz = math.radians(PA_ZENIT)
    dz = c[1] * math.cos(tz) + c[2] * math.sin(tz); dperp = -c[1] * math.sin(tz) + c[2] * math.cos(tz)
    idx = np.nonzero(ok)[0]; blocs = idx // 10; ub = np.unique(blocs); rng = np.random.default_rng(llavor); bz, bp, ba = [], [], []
    pos = np.arange(ok.sum())
    for _ in range(nboot):
        tria = rng.choice(ub, len(ub)); sel = np.concatenate([pos[blocs == b] for b in tria]); sel = sel[w[sel]]
        cb, *_ = np.linalg.lstsq(A[sel], y[sel], rcond=None)
        bz.append(cb[1] * math.cos(tz) + cb[2] * math.sin(tz)); bp.append(-cb[1] * math.sin(tz) + cb[2] * math.cos(tz)); ba.append(math.hypot(cb[1], cb[2]))
    return dict(c0=float(c[0]), a_cos=float(c[1]), b_sin=float(c[2]), amplitud=float(math.hypot(c[1], c[2])),
                direccio_PA=float(math.degrees(math.atan2(c[2], c[1])) % 360), cap_al_zenit=float(dz), cap_al_zenit_err=float(np.std(bz)),
                perpendicular=float(dperp), perpendicular_err=float(np.std(bp)), amplitud_err=float(np.std(ba)), n=int(w.sum()))


res = {}
dip = {}
for i, a in enumerate(AN):
    k = f'{a[0]}-{a[1]}'
    res[k] = []
    for nc in CAL:
        x = np.where(usable[i], c2[nc]['mitjana'][i], np.nan)
        for ext, ours in nostra.items():
            y = np.where(usable[i], ours[i], np.nan)
            res[k].append(dict(calibratge=nc, nostra=ext, **cc.quocients(y, x), regressio=cc.regressio(x, y)))
        for f in cc.C2_FITXERS:      # cada fotograma, amb extinció
            x1 = np.where(usable[i], c2[nc][f][i], np.nan); y = np.where(usable[i], nostra['amb_extincio'][i], np.nan)
            res[k].append(dict(calibratge=nc, nostra='amb_extincio', c2=f, **cc.quocients(y, x1)))
    # dipol (calibratge SSW; el calibratge és una constant i no canvia el dipol)
    x = np.where(usable[i], c2['SSW_c2_calfactor']['mitjana'][i], np.nan)
    dd = {}
    for ext in ('sense_extincio', 'amb_extincio'):
        y = np.where(usable[i], nostra[ext][i], np.nan)
        with np.errstate(invalid='ignore', divide='ignore'):
            dd[ext] = dipol(np.log(y / x), pa_c)
    dd['prediccio_lnE'] = dipol(np.log(np.where(usable[i], N['c2_E'][i], np.nan)), pa_c)
    with np.errstate(invalid='ignore', divide='ignore'):
        dd['control_nul_C2_1836_sobre_1824'] = dipol(np.log(np.where(usable[i], dns[cc.C2_FITXERS[1]][i] / dns[cc.C2_FITXERS[0]][i], np.nan)), pa_c)
        dd['k072_amb_extincio'] = dipol(np.log(np.where(usable[i], nostra['k072'][i], np.nan) / x), pa_c)
        dd['k035_amb_extincio'] = dipol(np.log(np.where(usable[i], nostra['k035'][i], np.nan) / x), pa_c)
    dip[k] = dd

# perfil del C2 a la figura (anells fins), els dos calibratges
F = [tuple(a) for a in N['fig_anells']]
fig_dns, _ = bins_c2(F)
pil_fig = pilar[None, :] & np.ones((len(F), 1), bool)
fig = {}
for nc, fcal in CAL.items():
    m = 0.5 * (fig_dns[cc.C2_FITXERS[0]] * fcal(infos[0]['mjd']) + fig_dns[cc.C2_FITXERS[1]] * fcal(infos[1]['mjd']))
    fig[nc] = m
np.savez_compressed(OUT / 'c2_caselles.npz', anells=np.array(AN), usable=usable, fig_anells=np.array(F), fig_usable=N['fig_usable'] & ~pil_fig,
                    **{f'c2_{nc}': c2[nc]['mitjana'] for nc in CAL}, **{f'fig_{nc}': v for nc, v in fig.items()})
entr = {cc.rel(cc.D01 / 'soho_lasco' / f): cc.sha256(cc.D01 / 'soho_lasco' / f) for f in cc.C2_FITXERS}
entr[cc.rel(cc.D01 / 'lasco_calib/c2vig_final.fts')] = cc.sha256(cc.D01 / 'lasco_calib/c2vig_final.fts')
entr[cc.rel(cc.D11 / 'lasco_calib/c2_expfactor_260812.dat')] = cc.sha256(cc.D11 / 'lasco_calib/c2_expfactor_260812.dat')
entr[cc.rel(cc.RES / 'caselles_nostra.npz')] = cc.sha256(cc.RES / 'caselles_nostra.npz')
json.dump(dict(guio=cc.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'), fotogrames=infos,
               calibratges={nc: {f: fcal(info['mjd']) for f, info in zip(cc.C2_FITXERS, infos)} for nc, fcal in CAL.items()},
               quocient_CH_sobre_SSW=float(cc.calfac_ch2015(infos[0]['mjd']) / cc.calfac_ssw(infos[0]['mjd'])),
               referencia='mitjana per casella dels dos fotogrames (18:24:31, 18:36:15)', pilar=cc.PILAR, PA_zenit=PA_ZENIT,
               resultats=res, dipol=dip, entrades_sha256=entr, segons=round(time.time() - T0, 1)),
          open(OUT / 'LASCO.json', 'w'), indent=1, ensure_ascii=False, default=float)
print('fotogrames:', json.dumps(infos, indent=0, default=float)[:1500])
for k, L in res.items():
    s = []
    for d in L:
        if 'c2' not in d and d['nostra'] in ('amb_extincio', 'sense_extincio'):
            s.append(f"{d['calibratge'][:3]} {d['nostra'][:4]}: qm {d['quocient_medianes']:.3f} f {d['regressio']['f']:.3f}±{d['regressio']['f_err']:.3f} s {d['regressio']['s']:.1e} ρ {d['regressio']['rho']:.2f}")
    print(k, ' | '.join(s))
for k, dd in dip.items():
    print(k, {kk: (round(v['cap_al_zenit'], 4), round(v['cap_al_zenit_err'], 4), round(v['amplitud'], 4), round(v['direccio_PA'], 1)) if v else None for kk, v in dd.items()})
print(f'fet ({time.time() - T0:.0f} s)')
