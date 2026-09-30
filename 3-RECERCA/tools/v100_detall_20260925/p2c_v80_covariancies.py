"""p2c (V100 detall · PÍXELS) · la prova clau refeta amb COVARIÀNCIES entre peces independents (immune al desequilibri de les meitats).
Motiu: les meitats de D29 (parells/senars) no tenen el mateix pes a la banda (pocs fotogrames, exposicions diferents), i aleshores la correlació
entre meitats infravalora la fiabilitat de D29 (una meitat lleugera és molt sorollosa). Amb peces independents p, s (meitats) i una versió V:
  S² = cov(p, s)  → potència del senyal comú als dos jocs de fotogrames (dada real reproduïble; si ≤ 0, no se'n detecta);
  ρ(V, S) = ½[cov(V, p) + cov(V, s)] / √(var V · S²)  → correlació (amb signe) de V amb aquest senyal comú; ρ² ≈ fracció de la textura de V que és senyal real;
  fiabilitat de D29 = S² / var(D29).
ATENCIÓ: les versions V80…V99 surten dels MATEIXOS fotogrames Vixen que D29; el seu soroll no és independent del de D29, i ρ pot quedar inflat
(fins i tot > 1) pel soroll compartit. Per això el que és robust aquí és S² (la dada: n'hi ha o no, de senyal reproduïble) i el signe/nul de ρ.
Interval: bootstrap per blocs de 20 px d'arc (400 rèpliques). Nul: D29 desplaçada ±20–40 px al llarg de l'arc.
Pas alt tangencial σ 1,5 · 3 · 6 px (mateixa geometria polar que p2) i perfils 1D (mitjana radial dins del calaix).
Sortida: 4-RESULTATS/v100_detall_20260925/pixels/P2C_COVARIANCIES.json (fitxer nou)."""
import json, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from p0_comu_pixels import SORT, FONTS, llegeix_finestra, ln_lum, d29_a_finestra
import p2_v80_correlacio as P2

DGRID, PAg, DS = P2.DGRID, P2.PAg, P2.DS
SECT = {'dalt_75_135': (75, 135), 'baixesq_205_255': (205, 255), 'dreta_300_360_control': (300, 360),
        'dalt_75_105': (75, 105), 'dalt_105_135': (105, 135)}
CAL = [(0, 1), (1, 2), (2, 3), (3, 5), (5, 8), (10, 20)]
VERS = ['V80', 'V75C', 'V78', 'V71', 'V69', 'V98', 'V99']
BLOC = int(round(20 / DS))


def estadistics(v, p, s, D):
    """v, p, s, D: arrays (files d, columnes arc) ja retallats; retorna dict amb S², ρ², fiabilitat."""
    ok = np.isfinite(v) & np.isfinite(p) & np.isfinite(s) & np.isfinite(D)
    if ok.sum() < 40:
        return None
    c = lambda a, b: float(np.mean((a[ok] - a[ok].mean()) * (b[ok] - b[ok].mean())))
    S2 = c(p, s); vv = c(v, v); vd = c(D, D)
    cvp, cvs, cvd = c(v, p), c(v, s), c(v, D)
    rho = 0.5 * (cvp + cvs) / np.sqrt(vv * S2) if S2 > 0 else np.nan
    return dict(S2=S2, var_V=vv, var_D29=vd, cov_Vp=cvp, cov_Vs=cvs, r_VD=cvd / np.sqrt(vv * vd), fiab_D29=S2 / vd if vd > 0 else np.nan,
                rho_V_real=rho, n=int(ok.sum()))


def boot(v, p, s, D, nrep=400, seed=3):
    ncol = v.shape[1]; nb = max(ncol // BLOC, 2); rng = np.random.default_rng(seed); out = []
    for _ in range(nrep):
        idx = np.concatenate([np.arange(b * BLOC, min((b + 1) * BLOC, ncol)) for b in rng.integers(0, nb, nb)])
        e = estadistics(v[:, idx], p[:, idx], s[:, idx], D[:, idx])
        if e:
            out.append((e['S2'], e['rho_V_real'], e['fiab_D29'], e['r_VD']))
    a = np.array(out, float)
    q = lambda k: [float(np.nanpercentile(a[:, k], 5)), float(np.nanpercentile(a[:, k], 95))] if len(a) else None
    return dict(S2_ic90=q(0), rho_ic90=q(1), fiab_ic90=q(2), r_ic90=q(3), frac_S2_positiu=float(np.mean(a[:, 0] > 0)) if len(a) else None)


def main():
    t0 = time.time()
    G, Gp, Gs = (d29_a_finestra(k) for k in ('G', 'G_parells', 'G_senars'))
    mG = np.isfinite(G) & (G > 0); mH = mG & (Gp > 0) & (Gs > 0)
    L = lambda a, m: np.where(m, np.log(np.where(m, a, 1)), np.nan)
    P = {'D29': P2.a_polars(L(G, mH), mH), 'D29p': P2.a_polars(L(Gp, mH), mH), 'D29s': P2.a_polars(L(Gs, mH), mH)}
    vers = [v for v in VERS if FONTS[v][0].exists()]
    for v in vers:
        P[v] = P2.a_polars(ln_lum(llegeix_finestra(v)))
    out = {'nota': 'S2 = cov(meitat parells, meitat senars) del pas alt (senyal reproduïble de la dada); fiab_D29 = S2/var(D29); rho_V_real = ½(cov(V,p)+cov(V,s))/√(var V·S2), inflable pel soroll compartit (mateixos fotogrames)', 'r': {}}
    for sg in (1.5, 3.0, 6.0):
        H = {k: P2.hp_tang(P[k], sg) for k in P}
        for mode in ('2d', 'perfil'):
            for sn, (a0, a1) in SECT.items():
                cs = (PAg >= a0) & (PAg < a1)
                for lo, hi in CAL:
                    ri = (DGRID >= lo) & (DGRID < hi)

                    def tall(k, roll=0):
                        h = (np.roll(H[k], roll, axis=1) if roll else H[k])[ri][:, cs]
                        if mode == 'perfil':
                            okc = np.isfinite(h).mean(0) > 0.75
                            h = np.where(okc, np.nanmean(np.where(np.isfinite(h), h, np.nan), axis=0), np.nan)[None, :]
                        return h
                    p, s, D = tall('D29p'), tall('D29s'), tall('D29')
                    res = {}
                    for v in vers:
                        e = estadistics(tall(v), p, s, D)
                        if e is None:
                            res[v] = None; continue
                        e.update(boot(tall(v), p, s, D))
                        nul = [estadistics(tall(v), tall('D29p', g * int(round(sh / DS))), tall('D29s', g * int(round(sh / DS))), tall('D29', g * int(round(sh / DS))))
                               for sh in P2.SH_NUL for g in (1, -1)]
                        rn = np.array([x['rho_V_real'] if x else np.nan for x in nul]); cn = np.array([0.5 * (x['cov_Vp'] + x['cov_Vs']) if x else np.nan for x in nul])
                        e['nul_rho_mitjana'] = float(np.nanmean(rn)) if np.isfinite(rn).any() else None
                        e['nul_rho_sd'] = float(np.nanstd(rn)) if np.isfinite(rn).any() else None
                        e['cov_VS'] = float(0.5 * (e['cov_Vp'] + e['cov_Vs']))
                        e['nul_covVS_sd'] = float(np.nanstd(cn)); e['nul_covVS_mitjana'] = float(np.nanmean(cn))
                        res[v] = e
                    out['r'][f'tang{sg}|{mode}|{sn}|{lo}_{hi}'] = res

    def neteja(o):
        if isinstance(o, dict):
            return {k: neteja(v) for k, v in o.items()}
        if isinstance(o, list):
            return [neteja(v) for v in o]
        if isinstance(o, float):
            return None if not np.isfinite(o) else float(f'{o:.5g}')
        return o
    p = SORT / 'P2C_COVARIANCIES.json'
    if p.exists():
        p = SORT / f'P2C_COVARIANCIES_{int(time.time())}.json'
    p.write_text(json.dumps(neteja(out), indent=1, ensure_ascii=False))
    print('fet', p, round(time.time() - t0, 1), 's')


if __name__ == '__main__':
    main()
