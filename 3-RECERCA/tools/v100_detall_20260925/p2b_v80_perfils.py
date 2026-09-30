"""p2b (V100 detall · PÍXELS) · complement de p2: (1) perfils al llarg de l'arc (mitjana radial del pas alt tangencial dins de cada calaix:
els raigs de la corona són radials, i la mitjana radial en millora el S/N), amb meitats, nul i sostre; (2) desglossament per finestres de 15°;
(3) energies absolutes i part real/soroll de D29 (soroll = meitat de la diferència de les meitats); (4) V80 contra V99 directament.
Mateixa geometria polar que p2. Sortida: 4-RESULTATS/v100_detall_20260925/pixels/P2B_PERFILS.json (fitxer nou)."""
import json, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from p0_comu_pixels import SORT, FONTS, llegeix_finestra, ln_lum, d29_a_finestra
import p2_v80_correlacio as P2

DGRID, PAg, DS = P2.DGRID, P2.PAg, P2.DS
SECT = {'dalt_75_135': (75, 135), 'baixesq_205_255': (205, 255), 'dreta_300_360_control': (300, 360)}
CAL = [(0, 1), (1, 2), (2, 3), (3, 5), (5, 8), (10, 20)]
VERS = ['V80', 'V75C', 'V78', 'V71', 'V69', 'V98', 'V99']


def main():
    G, Gp, Gs = (d29_a_finestra(k) for k in ('G', 'G_parells', 'G_senars'))
    mG = np.isfinite(G) & (G > 0); mH = mG & (Gp > 0) & (Gs > 0)
    L = lambda a, m: np.where(m, np.log(np.where(m, a, 1)), np.nan)
    P = {'D29': P2.a_polars(L(G, mG), mG), 'D29p': P2.a_polars(L(Gp, mH), mH), 'D29s': P2.a_polars(L(Gs, mH), mH)}
    vers = [v for v in VERS if FONTS[v][0].exists()]
    for v in vers:
        P[v] = P2.a_polars(ln_lum(llegeix_finestra(v)))
    out = {'perfils': {}, 'finestres15': {}, 'energies': {}, 'V80_contra_V99': {}}
    for sg in (1.5, 3.0, 6.0):
        H = {k: P2.hp_tang(P[k], sg) for k in P}
        for sn, (a0, a1) in SECT.items():
            cs = (PAg >= a0) & (PAg < a1)
            for lo, hi in CAL:
                ri = (DGRID >= lo) & (DGRID < hi)
                # perfils 1D: mitjana radial (només columnes on tot el calaix és vàlid a D29)
                def perfil(k, roll=0):
                    h = np.roll(H[k], roll, axis=1) if roll else H[k]
                    b = h[ri]; ok = np.isfinite(b).mean(0) > 0.75
                    return np.where(ok, np.nanmean(np.where(np.isfinite(b), b, np.nan), axis=0), np.nan)
                pr = {k: perfil(k) for k in H}
                rh = P2.pear(pr['D29p'][cs], pr['D29s'][cs])[0]
                rel = 2 * rh / (1 + rh) if np.isfinite(rh) and rh > -0.99 else np.nan
                res = {'D29': dict(r_meitats=rh, fiabilitat=rel, sostre=float(np.sqrt(rel)) if np.isfinite(rel) and rel > 0 else None,
                                   n=int(np.isfinite(pr['D29'][cs]).sum()))}
                for v in vers:
                    r = P2.pear(pr[v][cs], pr['D29'][cs])[0]
                    nul = np.array([P2.pear(pr[v][cs], perfil('D29', sgn * int(round(s / DS)))[cs])[0] for s in P2.SH_NUL for sgn in (1, -1)])
                    res[v] = dict(r=r, r_parells=P2.pear(pr[v][cs], pr['D29p'][cs])[0], r_senars=P2.pear(pr[v][cs], pr['D29s'][cs])[0],
                                  nul_mitjana=float(np.nanmean(nul)), nul_sd=float(np.nanstd(nul)), z=float((r - np.nanmean(nul)) / max(np.nanstd(nul), 1e-6)),
                                  r_des=float(r / np.sqrt(rel)) if np.isfinite(rel) and rel > 0.02 else None)
                out['perfils'][f'tang{sg}|{sn}|{lo}_{hi}'] = res
                # energies absolutes (2D, com a p2) i descomposició de D29
                eD = float(np.nanstd(H['D29'][ri][:, cs])); eN = float(np.nanstd(H['D29p'][ri][:, cs] - H['D29s'][ri][:, cs]) / 2)
                out['energies'][f'tang{sg}|{sn}|{lo}_{hi}'] = dict(D29=eD, D29_soroll_estimat=eN, D29_senyal_estimat=float(np.sqrt(max(eD ** 2 - eN ** 2, 0))),
                                                                   **{v: float(np.nanstd(H[v][ri][:, cs])) for v in vers})
                out['V80_contra_V99'][f'tang{sg}|{sn}|{lo}_{hi}'] = P2.pear(H['V80'][ri][:, cs], H['V99'][ri][:, cs])[0]
        if sg == 3.0 or sg == 1.5:
            for sn, (a0, a1) in [('dalt', (75, 135)), ('baixesq', (205, 255))]:
                for w0 in range(a0, a1, 15):
                    cs = (PAg >= w0) & (PAg < w0 + 15)
                    for lo, hi in [(0, 3), (3, 5), (5, 8), (10, 20)]:
                        ri = (DGRID >= lo) & (DGRID < hi)
                        rh = P2.pear(H['D29p'][ri][:, cs], H['D29s'][ri][:, cs])[0]
                        out['finestres15'][f'tang{sg}|{w0}_{w0 + 15}|{lo}_{hi}'] = dict(r_meitats=rh, **{v: P2.pear(H[v][ri][:, cs], H['D29'][ri][:, cs])[0] for v in ('V80', 'V69', 'V99')})

    def neteja(o):
        if isinstance(o, dict):
            return {k: neteja(v) for k, v in o.items()}
        if isinstance(o, float):
            return None if not np.isfinite(o) else round(o, 4)
        return o
    p = SORT / 'P2B_PERFILS.json'
    if p.exists():
        p = SORT / f'P2B_PERFILS_{int(time.time())}.json'
    p.write_text(json.dumps(neteja(out), indent=1, ensure_ascii=False))
    print('fet', p)


if __name__ == '__main__':
    main()
