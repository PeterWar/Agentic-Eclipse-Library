"""A8 · El GRA (soroll fi) per radi: rms del passa-alt fi (DoG σ1,5/σ3 en ln) per anells de
0,02 R☉ a la base V32, Vixen V32 i Sony B V32, 1,0–3,0 R☉. Un graó de gra (no de nivell) on
entra un fotograma o on comença la rampa Vixen→Sony és el que els filtres que amplifiquen
el soroll (04 micro, MGN, WOW) ensenyen com a contorn. Només lectura."""
from extract import *
from scipy.ndimage import gaussian_filter
V32T = ROOT / 'research/tools/v32_arcs_20260907'; C32 = V32T / 'cau'; CF = ROOT / 'research/tools/v29/cau_final'
sys.path.insert(0, str(Path(__file__).parent)); from a6_vistes_polars import load
from a4_color_i_rho import ring_profile


def main():
    r1 = 3.05; box = (int(CX - r1 * RS), int(CY - r1 * RS), int(CX + r1 * RS) + 1, int(CY + r1 * RS) + 1); x0, y0 = box[0], box[1]
    yy, xx = np.mgrid[y0:box[3], x0:box[2]].astype(np.float32); r = np.hypot(xx - CX, yy - CY)
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 1, figsize=(9, 6), sharex=True); out = {}
    for name, path, sup in [('base V32', C32 / 'base_G_v32.npy', C32 / 'support_v32.npy'), ('Vixen V32', C32 / 'vixen_total_v32.npy', CF / 'vixen_support.npy'), ('Sony B V32', C32 / 'sony_B_total_v32.npy', None), ('Sony A V32', C32 / 'sony_A_total_v32.npy', None)]:
        v, m = load(path, sup, True, box); w = m.astype(np.float32)
        def ng(a, s):
            return gaussian_filter(a * w, s) / np.maximum(gaussian_filter(w, s), 1e-6)
        fine = np.where(m, ng(v, 1.5) - ng(v, 3.0), 0); mid = np.where(m, ng(v, 6) - ng(v, 12), 0)
        rr, pf, n = ring_profile(fine ** 2, m, r, 1.0, 3.0, step=0.02 * RS); _, pm, _ = ring_profile(mid ** 2, m, r, 1.0, 3.0, step=0.02 * RS)
        out[name] = {'r': rr.tolist(), 'rms_fi_pct': (100 * np.sqrt(pf)).tolist(), 'rms_mig_pct': (100 * np.sqrt(pm)).tolist()}
        ax[0].plot(rr, 100 * np.sqrt(pf), lw=.9, label=name); ax[1].plot(rr, 100 * np.sqrt(pm), lw=.9, label=name)
        del v, m, w, fine, mid
    for a_ in ax:
        for r_, lab in [(1.21, '0,5 s'), (1.33, '1 s'), (1.47, '2 s'), (1.96, '10 s'), (2.0, 'rampa Sony'), (2.65, 'fi rampa')]:
            a_.axvline(r_, color='.5', lw=.6, ls='--'); a_.text(r_, a_.get_ylim()[1] * .9 if a_.get_ylim()[1] > 0 else 1, lab, fontsize=7, rotation=90, va='top')
        a_.legend(fontsize=8); a_.set_yscale('log')
    ax[0].set_ylabel('gra fi rms [%] (DoG 1,5/3 px)'); ax[1].set_ylabel('gra mitjà rms [%] (DoG 6/12 px)'); ax[1].set_xlabel('r [R☉]')
    ax[0].set_title('Gra per radi a la base V32 i a cada tren: els graons de gra són on els filtres que amplifiquen el soroll dibuixen contorns', fontsize=9)
    fig.tight_layout(); fig.savefig(RUN.vista('R32_A8_gra_per_radi.png'), dpi=120)
    # graons: quocient del gra a ±0,06 R de cada radi candidat
    steps = {}
    for name, d in out.items():
        rr = np.array(d['r']); f = np.array(d['rms_fi_pct']); g = np.array(d['rms_mig_pct'])
        steps[name] = {}
        for r_ in (1.21, 1.33, 1.47, 1.65, 1.96, 2.05, 2.3, 2.65):
            a = (rr > r_ - 0.08) & (rr < r_ - 0.02); b = (rr > r_ + 0.02) & (rr < r_ + 0.08)
            steps[name][str(r_)] = {'fi_fora_sobre_dins': float(np.nanmean(f[b]) / np.nanmean(f[a])), 'mig_fora_sobre_dins': float(np.nanmean(g[b]) / np.nanmean(g[a]))}
    out['graons_quocient_gra'] = steps
    write(RUN.rebut('R32_A8_gra_per_radi.json'), out)
    for name, s in steps.items():
        print(name, {k: (round(v['fi_fora_sobre_dins'], 2), round(v['mig_fora_sobre_dins'], 2)) for k, v in s.items()})


if __name__ == '__main__':
    main()
