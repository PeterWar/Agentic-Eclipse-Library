"""A10 · Corba d'entrada de cada fotograma: quocient (fotograma·k·e^{−φ}) / compost-sense-ell en
funció del NIVELL PROPI del fotograma (DN relatiu al sostre), amb la graella grossa de l'A1 (V32).
Si el quocient s'aparta d'1 quan el nivell s'acosta al sostre (70–85 % de saturació), el fotograma
entra esbiaixat: no-linealitat del sensor (o del calibratge) a l'origen, que cap camp suau no cura.
Vixen (canal G) i Sony B, per grups d'exposició. Només lectura."""
import sys, json
from pathlib import Path
import numpy as np
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026'); C32 = ROOT / 'research/tools/v32_arcs_20260907/cau'; REB = ROOT / 'output/revisio_marques_v33_20260907/4-rebuts'; VIS = ROOT / 'output/revisio_marques_v33_20260907/lliurables/vistes'
BINS = np.array([0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.05])


def main():
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.5)); out = {}
    for ai, (tag, wf, vf, mf, pf) in enumerate([('vixen', 'vixen_w.npy', 'vixen_v.npy', 'vixen_meta.json', 'vixen_G_phi.npy'), ('sony', 'sony_w.npy', 'sony_v.npy', 'sony_meta.json', 'sony_B_G_phi.npy')]):
        Wm = np.load(C32 / wf, mmap_mode='r'); Vm = np.load(C32 / vf, mmap_mode='r'); meta = json.loads((C32 / mf).read_text())['frames']
        phi = np.load(C32 / pf, mmap_mode='r') if (C32 / pf).exists() else None
        n = Wm.shape[0]; names = [m['name'] for m in meta]
        if tag == 'sony':
            grp = [m['group'] for m in meta]; sel = [i for i in range(n) if grp[i] == 'sony_B']
            phin = json.loads((ROOT / 'output/v32_arcs_20260907/4-rebuts/B1_camps_sony_B.json').read_text())['frames'] if (ROOT / 'output/v32_arcs_20260907/4-rebuts/B1_camps_sony_B.json').exists() else None
        else:
            sel = list(range(n)); phin = json.loads((ROOT / 'output/v32_arcs_20260907/4-rebuts/B1_camps_vixen.json').read_text())['frames']
        # compost gros (amb φ i k, sense offsets: els offsets són additius i petits al nivell alt)
        num = np.zeros(Wm.shape[1:], np.float64); den = np.zeros_like(num); lev = {}
        for i in sel:
            w = np.asarray(Wm[i], np.float64); v = np.asarray(Vm[i], np.float64); k = meta[i]['k']
            ph = np.asarray(phi[phin.index(names[i])], np.float64) if phi is not None and names[i] in phin else 0.0
            val = np.where(np.isfinite(v), v * k * np.exp(-ph), 0.0); good = np.isfinite(v) & (w > 0)
            num += np.where(good, w * val, 0); den += np.where(good, w, 0); lev[i] = (val, good, w)
        C = np.where(den > 0, num / np.maximum(den, 1e-20), np.nan)
        groups = {}
        for i in sel:
            val, good, w = lev[i]; e = meta[i]['exp']
            # compost sense el fotograma i
            Ci = np.where(den - w > 1e-9, (num - w * val) / np.maximum(den - w, 1e-20), np.nan)
            dn = val / max(meta[i]['k'], 1e-9) * e     # ∝ DN del fotograma (pl·t); normalitzat al seu sostre retingut
            top = np.nanpercentile(dn[good], 99.9); rel = dn / max(top, 1e-9)
            ratio = np.where(good & np.isfinite(Ci) & (Ci > 0), val / np.maximum(Ci, 1e-20), np.nan)
            rows = []
            for a, b in zip(BINS[:-1], BINS[1:]):
                kk = good & (rel >= a) & (rel < b) & np.isfinite(ratio)
                rows.append(float(np.median(ratio[kk])) if kk.sum() > 200 else np.nan)
            groups.setdefault(f'{e:g}', []).append(rows)
        res = {}
        ax = axs[ai]
        for e, rr in sorted(groups.items(), key=lambda z: float(z[0])):
            arr = np.array(rr); med = np.nanmedian(arr, axis=0); res[e] = {'n_frames': len(rr), 'ratio_per_bin': med.tolist()}
            ax.plot(0.5 * (BINS[:-1] + BINS[1:]), 100 * (med - 1), marker='o', ms=3, lw=.9, label=f'{e} s (n={len(rr)})')
        ax.axhline(0, color='.5', lw=.6); ax.axvspan(0.82, 1.0, color='orange', alpha=.12); ax.set_xlabel('nivell propi del fotograma (DN / sostre retingut ≈ 0,85·sat)'); ax.set_ylabel('fotograma / compost sense ell − 1 [%]'); ax.set_title(f'{tag}: corba d\'entrada per grup d\'exposició (graella A1, φ de B1 aplicat)', fontsize=9); ax.legend(fontsize=7, ncol=2); ax.set_ylim(-4, 4)
        out[tag] = {'bins': BINS.tolist(), 'groups': res}
        print(tag, {e: [None if np.isnan(x) else round(100 * (x - 1), 2) for x in v['ratio_per_bin']] for e, v in res.items()})
    fig.tight_layout(); fig.savefig(VIS / 'A10_corba_entrada_per_exposicio.png', dpi=120)
    (REB / 'R33_A10_linealitat_entrada.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
