"""h1_encongiment (V108, flat2d_v4) · LA PORTA PER GRUP: la a de cada estructura que la porta de la v3 rebutja, ENCONGIDA cap a la població
del seu grup (sony_A, sony_B, vixen) amb un model bayesià jeràrquic que fa servir l'error de cada a.
Per què: el verificador 3 va veure que les rebutjades, preses com a grup, SÍ que són a la dada (Sony A a = 0,80 ± 0,06, z 14; Sony B 0,68;
Vixen 0,75 al subgrup z 2–3). La porta dura per z individual les llençava senceres. Però la pols també es mou (els flats són de 10 dies després):
algunes, ben mesurades, NO hi són (Vixen (5839, 5350): a = 0,16 ± 0,11; la v2 hi posava una taca nova de +38 ‱).
Model (per grup; dada = a_taca − ⟨nul⟩ i σ_nul de g1_porta_v4, la plantilla de la part d'escala de taca, que és la que s'escala):
  a_k ~ π·N(μ, τ²) + (1 − π)·δ(0)       la pols que hi era (amplitud μ ± τ) o la que s'havia mogut (0)
  â_k | a_k ~ N(a_k, σ_k²)
  π, μ, τ per màxima versemblança amb les estructures REBUTJADES provades del grup (el grup de què parla el verificador). No amb tota la
  població: les aplicades són les fortes i tenen a_taca ≈ 1,2–1,3; les febles, menys (Vixen 0,59 ± 0,07); amb el previ de tota la població,
  les rebutjades rebrien â ≈ 1,0–1,16 de mitjana, fins a 6σ per sobre del que el seu grup mesura (no són intercanviables: s'hi injectaria).
  El previ de les rebutjades és conservador (la porta les tria per z baixa, i això esbiaixa la seva a mesurada cap avall). Fora de l'ajust
  (però amb posterior) les que porten molt MÉS del que C explica (z_excés > 3: és una altra cosa, p. ex. el «ghost» de l'eix òptic a A).
  a encongida = mitjana posterior = P(hi és | dada)·[a_k − B_k·(a_k − μ)], B_k = σ_k²/(σ_k² + τ²); limitada a [0, 1,2].
  Una estructura ben mesurada conserva la seva a (i si és ≈ 0, P → 0: no s'hi posa res); una de mal mesurada va cap a la del grup (π·μ).
Comparació (al rebut, no s'aplica): el James-Stein normal (π = 1) i el previ de tota la població (aplicades + rebutjades); bootstrap de 400 del previ.
Regles de sortida per estructura: v3_aplica (a = 1, com la v3) · encongida (rebutjada provada) · encongida_sense_dada (a la vora del camp,
cap referència no la cobreix: la posterior és el previ, π·μ) · v3_fora_del_llenc (no toca cap fotograma del grup: regla de la v3).
LA DADA QUE S'ENCONGEIX (--dada): «control» = a_taca de g1 (la taca a l'apilat sense corregir); «a0» = r0 de g2_residu_porta_v4 sobre els apilats
de la C «a0» (la v4 amb â = 0: la textura i el fons de la petjada ja aplicats), és a dir, la part de taca que QUEDA a la dada un cop tret el que
ja està validat. Cal «a0»: a la dada sense corregir, la plantilla de taca també recull la textura i el fons del voltant (que també hi són), i
encongir a_taca sobrecorregia la Vixen (el grup de rebutjades passava de +0,47 a −0,34 ± 0,07; primer intent, a l'INFORME).
--zero: escriu H1_ENCONGIDA_ZERO_<TREN>.json amb â = 0 a totes les rebutjades (per fer la C «a0»).
Sortida: 4-RESULTATS/v108_20260926/flat2d_v4/flat2d/H1_ENCONGIDA[_ZERO]_<TREN>.json.  Ús: h1_encongiment.py VIXEN|SONYTOT [--dada control|a0] [--zero]   (només lectura; segons)"""
import json, sys, time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.stats import norm
ARREL = Path(__file__).resolve().parents[4]; D = ARREL / '4-RESULTATS/v108_20260926/flat2d_v4/flat2d'
import argparse
ap = argparse.ArgumentParser(); ap.add_argument('tren', choices=['VIXEN', 'SONYTOT']); ap.add_argument('--dada', choices=['control', 'a0'], default='a0'); ap.add_argument('--zero', action='store_true')
A_ = ap.parse_args(); TREN = A_.tren; t0 = time.time()
G1 = json.loads((D / f'G1_PORTA_V4_{TREN}.json').read_text()); LIM = (0.0, 1.2)
G2 = json.loads((D.parent / 'G2_RESIDU_PORTA_a0.json').read_text())[TREN]['grups'] if A_.dada == 'a0' else None
def mixt_fit(a, s):
    def nll(p):
        pi = 1 / (1 + np.exp(-p[0])); mu = p[1]; t = np.exp(p[2])
        L = pi * norm.pdf(a, mu, np.sqrt(s ** 2 + t ** 2)) + (1 - pi) * norm.pdf(a, 0, s)
        return -np.log(L + 1e-300).sum()
    best = None
    for p0 in ([1.0, 0.9, np.log(0.2)], [0.0, 1.0, np.log(0.1)], [2.5, 0.8, np.log(0.3)], [3.0, 0.7, np.log(0.02)]):
        r = minimize(nll, p0, method='Nelder-Mead', options=dict(maxiter=6000, xatol=1e-7, fatol=1e-9))
        if best is None or r.fun < best.fun: best = r
    p = best.x; return dict(pi=float(1 / (1 + np.exp(-p[0]))), mu=float(p[1]), tau=float(np.exp(p[2])), nll=float(best.fun))
def mixt_post(a, s, P):
    L1 = P['pi'] * norm.pdf(a, P['mu'], np.sqrt(s ** 2 + P['tau'] ** 2)); L0 = (1 - P['pi']) * norm.pdf(a, 0, s); pr = L1 / np.maximum(L1 + L0, 1e-300)
    B = s ** 2 / (s ** 2 + P['tau'] ** 2); return pr * (a - B * (a - P['mu'])), pr
def reml(a, s):
    def nll(lt):
        t2 = np.exp(lt); v = s ** 2 + t2; w = 1 / v; mu = (w * a).sum() / w.sum()
        return 0.5 * (np.log(v).sum() + np.log(w.sum()) + (w * (a - mu) ** 2).sum())
    r = minimize_scalar(nll, bounds=(-14, 3), method='bounded'); t2 = float(np.exp(r.x)); w = 1 / (s ** 2 + t2)
    return dict(mu=float((w * a).sum() / w.sum()), tau=float(np.sqrt(t2)), se_mu=float(1 / np.sqrt(w.sum())))
def mitjana_ponderada(a, s):
    w = 1 / s ** 2; m = float((w * a).sum() / w.sum()); e = float(1 / np.sqrt(w.sum())); return dict(a=round(m, 4), err=round(e, 4), z=round(m / e, 2), n=int(len(a)))
out = dict(tren=TREN, dada=A_.dada, zero=A_.zero, model=__doc__.split('Model')[1].split('Comparació')[0].strip(), limit=LIM, grups={}); rng = np.random.default_rng(20260927)
for g, G in G1['grups'].items():
    dec = G['decisions']; ids = sorted(dec, key=int)
    prov = [k for k in ids if 'a_taca' in dec[k] and np.isfinite(dec[k]['a_taca'])]
    if G2 is None: x = np.array([dec[k]['a_taca'] - dec[k]['nul_mitjana_taca'] for k in prov])
    else: x = np.array([G2[g]['estructures'][k]['a_taca_a0'] for k in prov])          # r0: la taca que queda amb la textura i el fons ja aplicats
    s = np.array([dec[k]['sigma_nul_taca'] for k in prov])
    ap = np.array([bool(dec[k]['aplica']) for k in prov]); exc = (x - 1) / s > 3; fit = ~exc
    P = mixt_fit(x[fit & ~ap], s[fit & ~ap]); JS = reml(x[fit & ~ap], s[fit & ~ap])
    Ppob = mixt_fit(x[fit], s[fit]) if G2 is None else P      # amb «a0», les aplicades ja porten la taca treta (x ≈ 0): la «població» no té sentit
    ah, pr = mixt_post(x, s, P); ah = np.clip(ah, *LIM)
    Bjs = s ** 2 / (s ** 2 + JS['tau'] ** 2); ajs = np.clip(x - Bjs * (x - JS['mu']), *LIM); apob, _ = mixt_post(x, s, Ppob); apob = np.clip(apob, *LIM)
    # bootstrap del previ (les estructures de l'ajust, amb reposició): dispersió de π, μ, τ i de cada â
    bs = []; abs_ = []
    idx = np.flatnonzero(fit & ~ap)
    for _ in range(400):
        j = rng.choice(idx, len(idx), replace=True); Pb = mixt_fit(x[j], s[j]); bs.append((Pb['pi'], Pb['mu'], Pb['tau'])); abs_.append(np.clip(mixt_post(x, s, Pb)[0], *LIM))
    bs = np.array(bs); abs_ = np.array(abs_)
    prior_mean = float(np.clip(P['pi'] * P['mu'], *LIM))
    est = {}
    for i, k in enumerate(prov):
        d = dec[k]; base = dict(a_plena=d['a'], sigma_plena=d['sigma_nul'], z_present_plena=d['z_present'], a_taca_control=round(d['a_taca'] - d['nul_mitjana_taca'], 4),
                                dada=A_.dada, a_taca=round(float(x[i]), 4), sigma_taca=round(float(s[i]), 4), z_taca=round(float(x[i] / s[i]), 3), z_excés_taca=round(float((x[i] - 1) / s[i]), 3), P_hi_es=round(float(pr[i]), 4), a_mixt=round(float(ah[i]), 4),
                                a_mixt_bootstrap_p16_p84=np.percentile(abs_[:, i], [16, 84]).round(4).tolist(), a_james_stein=round(float(ajs[i]), 4),
                                a_previ_poblacio=round(float(apob[i]), 4), fora_de_l_ajust=bool(exc[i]), ref=d['ref'], centre_llenc=d['centre_llenc'], R_sol=d['R_sol'],
                                escala_subpla=d.get('escala_subpla'), amplitud_pic_ppm=d['amplitud_pic_ppm'])
        if ap[i]: est[k] = dict(regla='v3_aplica', a_encongida=1.0, **base)
        else: est[k] = dict(regla='encongida', a_encongida=0.0 if A_.zero else round(float(ah[i]), 4), **base)
    for k in ids:
        if k in est: continue
        d = dec[k]
        if d.get('motiu') == 'fora del llenç': est[k] = dict(regla='v3_fora_del_llenc', motiu=d['motiu'])
        elif d.get('aplica'): est[k] = dict(regla='v3_aplica', a_encongida=1.0)
        else: est[k] = dict(regla='encongida_sense_dada', a_encongida=0.0 if A_.zero else round(prior_mean, 4), motiu=d.get('motiu'), nota='cap dada la cobreix: la posterior és el previ, π·μ')
    rej = np.array([not a_ for a_ in ap])
    res = dict(n_estructures=len(ids), n_provades=len(prov), n_aplicades_v3=int(ap.sum()), n_rebutjades_provades=int(rej.sum()),
               n_fora_ajust_exces=int(exc.sum()), fora_ajust=[k for i, k in enumerate(prov) if exc[i]],
               previ_mixt=dict(**{k_: round(v, 4) for k_, v in P.items()}, bootstrap_p16_p84=dict(pi=np.percentile(bs[:, 0], [16, 84]).round(3).tolist(), mu=np.percentile(bs[:, 1], [16, 84]).round(3).tolist(),
                                                                                                      tau=np.percentile(bs[:, 2], [16, 84]).round(3).tolist()), mitjana_previ=round(prior_mean, 4)),
               james_stein_normal=dict(**{k_: round(v, 4) for k_, v in JS.items()}), previ_poblacio_tota=dict(**{k_: round(v, 4) for k_, v in Ppob.items()}) if G2 is None else 'no aplicable amb la dada a0',
               grup_rebutjades_mitjana_ponderada_taca=mitjana_ponderada(x[rej & fit], s[rej & fit]),
               grup_rebutjades_mitjana_ponderada_plena=mitjana_ponderada(np.array([dec[k]['a'] - dec[k]['nul_mitjana'] for i, k in enumerate(prov) if rej[i] and fit[i]]),
                                                                        np.array([dec[k]['sigma_nul'] for i, k in enumerate(prov) if rej[i] and fit[i]])),
               per_z_plena={f'{lo}..{hi}': mitjana_ponderada(x[m_], s[m_]) for lo, hi in ((-99, 1), (1, 2), (2, 3), (3, 99))
                           for m_ in [rej & fit & (np.array([dec[k]['z_present'] for k in prov]) >= lo) & (np.array([dec[k]['z_present'] for k in prov]) < hi)] if m_.sum() > 0},
               a_encongida_rebutjades=dict(mitjana=round(float(ah[rej].mean()), 4) if rej.any() else None, p5_p50_p95=np.percentile(ah[rej], [5, 50, 95]).round(3).tolist() if rej.any() else None,
                                           n_zero=int((ah[rej] <= 0.05).sum()), n_sobre_1=int((ah[rej] > 1.0).sum()),
                                           james_stein_mitjana=round(float(ajs[rej].mean()), 4) if rej.any() else None, previ_poblacio_mitjana=round(float(apob[rej].mean()), 4) if rej.any() else None),
               n_sense_dada=sum(1 for v in est.values() if v['regla'] == 'encongida_sense_dada'), estructures=est)
    out['grups'][g] = res
    print(g, 'provades', len(prov), 'aplicades v3', int(ap.sum()), 'rebutjades', int(rej.sum()), 'fora ajust', res['fora_ajust'], '| previ', res['previ_mixt'], '| JS', res['james_stein_normal'],
          '| població', res['previ_poblacio_tota'], '| grup rebutjades (taca)', res['grup_rebutjades_mitjana_ponderada_taca'], '(plena)', res['grup_rebutjades_mitjana_ponderada_plena'],
          '| â rebutjades', res['a_encongida_rebutjades'], '| sense dada', res['n_sense_dada'], flush=True)
    for k in sorted([k for k in prov if not dec[k]['aplica']], key=lambda k: est[k]['a_encongida'])[:8]:
        e = est[k]; print('   ', k, 'a_taca', e['a_taca'], '±', e['sigma_taca'], 'P', e['P_hi_es'], '→ â', e['a_encongida'], '(JS', e['a_james_stein'], ') centre', e['centre_llenc'], flush=True)
(D / f'H1_ENCONGIDA{"_ZERO" if A_.zero else ""}_{TREN}.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n'); print('FET', f'{time.time()-t0:.1f}s')
