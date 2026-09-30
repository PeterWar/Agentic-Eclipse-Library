"""A10b · Linealitat a l'entrada, mesurada entre PARELLES d'exposicions veïnes (el «compost sense ell»
és mal condicionat per als fotogrames dominants). Per a cada parella (llarg, curt) del mateix tren:
ln(llarg) − ln(curt), amb k, offsets c03 (G) i φ de B1 aplicats, sobre cel·les on els DOS són a
l'altiplà (finestra = 1) i el curt té DN > 300 (offsets < 0,3 %), en calaixos del NIVELL PROPI del
llarg (DN / DN màxim retingut ≈ 0,85·sat). Una caiguda cap al sostre = no-linealitat del llarg."""
import json
from pathlib import Path
import numpy as np
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026'); C32 = ROOT / 'research/tools/v32_arcs_20260907/cau'; REB = ROOT / 'output/revisio_marques_v33_20260907/4-rebuts'; VIS = ROOT / 'output/revisio_marques_v33_20260907/lliurables/vistes'
import sys
RAMPA = '--rampa' in sys.argv
BINS = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.2])


def main():
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.5)); out = {}
    for ai, (tag, grpsel) in enumerate([('vixen', None), ('sony', 'sony_B')]):
        Wm = np.load(C32 / f'{tag}_w.npy', mmap_mode='r'); Vm = np.load(C32 / f'{tag}_v.npy', mmap_mode='r'); meta = json.loads((C32 / f'{tag}_meta.json').read_text())['frames']
        b1 = json.loads((ROOT / 'output/v32_arcs_20260907/4-rebuts' / (f'B1_camps_{tag}.json' if tag == 'vixen' else 'B1_camps_sony_B.json')).read_text())['frames']
        phi = np.load(C32 / ('vixen_G_phi.npy' if tag == 'vixen' else 'sony_B_G_phi.npy'), mmap_mode='r')
        idx = [i for i, m in enumerate(meta) if grpsel is None or m['group'] == grpsel]
        exps = sorted({meta[i]['exp'] for i in idx}); pairs = [(exps[j + 1], exps[j]) for j in range(len(exps) - 1)]
        def frame_val(i):
            w = np.asarray(Wm[i], np.float64); v = np.asarray(Vm[i], np.float64); m = meta[i]; e = m['exp']
            ph = np.asarray(phi[b1.index(m['name'])], np.float64) if m['name'] in b1 else 0.0
            val = (v * m['k'] + m['offset_RGB'][1]) * np.exp(-ph); plateau = np.isfinite(v) & (w >= 0.999 * e)   # finestra = 1
            if RAMPA: plateau = np.isfinite(v) & (w > 0.02 * e) & (w < 0.98 * e) & (v * e > np.nanpercentile((v * e)[np.isfinite(v)], 50))   # zona de RAMPA DE SOSTRE del llarg
            dn = v * e                                                   # ∝ DN cru
            return val, plateau, dn
        res = {}
        for el, es in pairs:
            L = [i for i in idx if meta[i]['exp'] == el]; S = [i for i in idx if meta[i]['exp'] == es]
            acc = [[] for _ in range(len(BINS) - 1)]
            for i in L:
                vl, pl_, dnl = frame_val(i); top = np.nanpercentile(dnl[np.isfinite(dnl) & (np.asarray(Wm[i]) > 0)], 99.9); rel = dnl / max(top, 1e-9)
                for j in S:
                    vs, ps_, dns = frame_val(j); ps_ = ps_ if not RAMPA else (np.isfinite(dns) & (np.asarray(Wm[j]) >= 0.999 * meta[j]['exp'])); ok = pl_ & ps_ & (dns > 300) & (vl > 0) & (vs > 0)
                    d = np.log(vl / vs)
                    for bi, (a, b) in enumerate(zip(BINS[:-1], BINS[1:])):
                        kk = ok & (rel >= a) & (rel < b)
                        if kk.sum() > 100:
                            acc[bi].append(float(np.median(d[kk])))
            med = [float(np.median(v)) if v else np.nan for v in acc]; n = [len(v) for v in acc]
            res[f'{el:g}s/{es:g}s'] = {'ln_ratio_pct_per_bin': [None if np.isnan(x) else 100 * x for x in med], 'n_pairs_per_bin': n}
            axs[ai].plot(0.5 * (BINS[:-1] + BINS[1:]), 100 * np.array(med), marker='o', ms=3, lw=.9, label=f'{el:g} s / {es:g} s')
            print(tag, f'{el:g}/{es:g}', [None if np.isnan(x) else round(100 * x, 2) for x in med])
        axs[ai].axhline(0, color='.5', lw=.6); axs[ai].axvspan(0.82, 1.0, color='orange', alpha=.12); axs[ai].set_ylim(-3, 3); axs[ai].set_xlabel('nivell propi del fotograma LLARG (DN / màxim retingut ≈ 0,85·sat)'); axs[ai].set_ylabel('ln(llarg/curt) [%]'); axs[ai].legend(fontsize=7, ncol=2); axs[ai].set_title(f'{tag}: parelles d\'exposicions veïnes, tots dos a l\'altiplà, φ de B1 i offsets c03 aplicats', fontsize=9)
        out[tag] = res
    fig.tight_layout(); fig.savefig(VIS / ('A10b_linealitat_parelles_rampa.png' if RAMPA else 'A10b_linealitat_parelles.png'), dpi=120); (REB / ('R33_A10b_linealitat_rampa.json' if RAMPA else 'R33_A10b_linealitat_parelles.json')).write_text(json.dumps({'bins': BINS.tolist(), **out}, indent=1))


if __name__ == '__main__':
    main()
