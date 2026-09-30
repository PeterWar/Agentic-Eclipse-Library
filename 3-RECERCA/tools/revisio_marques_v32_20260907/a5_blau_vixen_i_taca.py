"""A5 · (1) Els anells del canal blau de la Vixen: ¿V29 (abans de B1) o V32? Perfils ln(G/B) i
ln(R/B) passa-alt σ24 de vixen_total (V29) i vixen_total_v32, i per canal contra la Sony B
(ln V_c − ln S_c, que treu la corona real). (2) Els anells contra les fronteres d'entrada dels
fotogrames Vixen per canal natiu (A1: pesos per fotograma a la graella grossa). (3) Taca NE a
l'escala del filtre 05 (DoG σ12−σ48 de ln) a la posició exacta del blob de la capa."""
from extract import *
from scipy.ndimage import gaussian_filter1d, gaussian_filter
V32T = ROOT / 'research/tools/v32_arcs_20260907'; C32 = V32T / 'cau'; CF = ROOT / 'research/tools/v29/cau_final'
sys.path.insert(0, str(Path(__file__).parent))   # ring_profile i hp són de l'a4 LOCAL d'aquesta carpeta
from a4_color_i_rho import ring_profile, hp


def main():
    out = {}
    x0, x1, y0, y1 = int(CX - 2.8 * RS), int(CX + 2.8 * RS) + 1, int(CY - 2.8 * RS), int(CY + 2.8 * RS) + 1
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32); r = np.hypot(xx - CX, yy - CY)
    sup = np.asarray(np.load(CF / 'vixen_support.npy', mmap_mode='r')[y0:y1, x0:x1]) > 0
    S = np.asarray(np.load(C32 / 'sony_B_total_v32.npy', mmap_mode='r')[y0:y1, x0:x1], np.float32); okS = np.isfinite(S).all(2) & (S > 0).all(2)
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(3, 1, figsize=(9, 9), sharex=True)
    prof = {}
    for tag, path in [('V29', CF / 'vixen_total.npy'), ('V32', C32 / 'vixen_total_v32.npy')]:
        V = np.asarray(np.load(path, mmap_mode='r')[y0:y1, x0:x1], np.float32); ok = np.isfinite(V).all(2) & (V > 0).all(2) & sup
        L = np.log(np.maximum(V, 1e-9)); LS = np.log(np.maximum(S, 1e-9))
        rr, gb, _ = ring_profile(L[..., 1] - L[..., 2], ok, r, 1.05, 2.7); _, rb, _ = ring_profile(L[..., 0] - L[..., 2], ok, r, 1.05, 2.7)
        prof[tag] = {'G/B': hp(gb, 24), 'R/B': hp(rb, 24)}
        ax[0].plot(rr, 100 * prof[tag]['G/B'], lw=.8, label=f'Vixen {tag} ln(G/B) σ24'); ax[0].plot(rr, 100 * prof[tag]['R/B'], lw=.8, ls=':', label=f'Vixen {tag} ln(R/B) σ24')
        for c, nm in enumerate('RGB'):
            _, d, _ = ring_profile(L[..., c] - LS[..., c], ok & okS, r, 1.05, 2.7); prof[tag][nm + '_vs_SonyB'] = hp(d, 24)
            ax[1 if tag == 'V29' else 2].plot(rr, 100 * prof[tag][nm + '_vs_SonyB'], lw=.8, color={'R': 'tab:red', 'G': 'tab:green', 'B': 'tab:blue'}[nm], label=f'{tag}: ln V_{nm} − ln SonyB_{nm} σ24')
        out[tag] = {k: {'rms_pct_1.1_2.0': float(100 * np.sqrt(np.nanmean(v[(rr > 1.1) & (rr < 2.0)] ** 2))), 'p2p_pct_1.1_2.0': float(100 * (np.nanmax(v[(rr > 1.1) & (rr < 2.0)]) - np.nanmin(v[(rr > 1.1) & (rr < 2.0)])))} for k, v in prof[tag].items()}
        del V, L, ok
    # fronteres d'entrada per canal natiu (graella grossa d'A1): radi on cada fotograma passa del 5 % al 50 % del seu pes màxim
    meta = json.loads((C32 / 'vixen_meta.json').read_text())['frames']
    fronts = {}
    for ch in ('G', 'B'):
        Wm = np.load(C32 / ('vixen_w.npy' if ch == 'G' else f'vixen_{ch}_w.npy'), mmap_mode='r'); hc, wc = Wm.shape[1:]
        rc = np.hypot(np.arange(wc)[None, :] * 4 + 1.5 - CX, np.arange(hc)[:, None] * 4 + 1.5 - CY)
        rows = []
        for i, m in enumerate(meta):
            w = np.asarray(Wm[i]); k = w > 0
            if k.sum() < 100:
                continue
            rr_, p, n = ring_profile(w, np.ones_like(k), rc, 1.0, 2.8, step=4.0)
            p = np.nan_to_num(p); mx = p.max()
            if mx < 0.05:
                continue
            ins = np.flatnonzero(p > 0.5 * mx)
            rows.append({'name': m['name'], 'exp': m['exp'], 'r_entrada_50pct': float(rr_[ins[0]]), 'r_sortida_50pct': float(rr_[ins[-1]]), 'pes_max': float(mx)})
        fronts[ch] = sorted(rows, key=lambda z: z['r_entrada_50pct'])
        for z in fronts[ch]:
            ax[0].axvline(z['r_entrada_50pct'], color='tab:green' if ch == 'G' else 'tab:blue', lw=.5, ls='--', alpha=.6)
    out['fronteres_entrada_per_canal'] = fronts
    for a_ in ax:
        a_.axhline(0, color='.6', lw=.5); a_.legend(fontsize=7, ncol=3); a_.set_ylabel('%')
    ax[0].set_title('Vixen: anells de color (G/B, R/B) a la V29 i a la V32; línies = entrada (50 % del pes) de cada fotograma al G (verd) i al B (blau)', fontsize=8)
    ax[2].set_xlabel('r [R☉]'); fig.tight_layout(); fig.savefig(RUN.vista('R32_A5_anells_blau_vixen.png'), dpi=120); plt.close(fig)
    # taca NE a l'escala del filtre
    cat = json.loads(Path(RUN.rebut('review_catalog.json')).read_text()); m0 = [m for m in cat['marks'] if m['family'] == 'Anomalia local NE'][0]
    cx0, cy0 = m0['center_xy']; half = 260; ya, yb, xa, xb = int(cy0 - half), int(cy0 + half), int(cx0 - half), int(cx0 + half)
    lay = np.asarray(np.load(C32 / '05_v32_u16.npy', mmap_mode='r')[ya:yb, xa:xb], np.float32) / 65535
    resp = gaussian_filter(lay, 12) - gaussian_filter(lay, 48); win = resp[half - 100:half + 100, half - 100:half + 100]
    iy, ix = np.unravel_index(np.argmin(win), win.shape); py, px = half - 100 + iy, half - 100 + ix
    taca = {'pos_xy_capa05': [int(px + xa), int(py + ya)], 'capa05_resp': float(resp[py, px]), 'capa05_soroll': float(np.std(resp[40:-40, 40:-40])), 'fonts': {}}
    for k, p in [('base_V32', C32 / 'base_G_v32.npy'), ('base_V31', ROOT / 'research/tools/v31_purs/cau/base_G.npy'), ('sonyA_V32', C32 / 'sony_A_total_v32.npy'), ('sonyB_V32', C32 / 'sony_B_total_v32.npy'), ('vixen_V32', C32 / 'vixen_total_v32.npy')]:
        a = np.load(p, mmap_mode='r'); A = np.asarray(a[ya:yb, xa:xb, 1] if a.ndim == 3 else a[ya:yb, xa:xb], np.float32); ok = np.isfinite(A) & (A > 0)
        if ok.mean() < 0.5:
            taca['fonts'][k] = None; continue
        v = np.where(ok, np.log(np.maximum(A, 1e-9)), np.nanmedian(np.log(np.maximum(A[ok], 1e-9))))
        rs = gaussian_filter(v, 12) - gaussian_filter(v, 48); sd = float(np.std(rs[40:-40, 40:-40][ok[40:-40, 40:-40]]))
        taca['fonts'][k] = {'resp_pct_a_la_posicio': 100 * float(rs[py, px]), 'z': float(rs[py, px] / sd), 'soroll_pct': 100 * sd, 'suport_frac': float(ok.mean())}
    out['taca_NE_escala_filtre'] = taca
    write(RUN.rebut('R32_A5_blau_vixen_i_taca.json'), out)
    print(json.dumps({k: v for k, v in out.items() if k in ('V29', 'V32')}, indent=1)); print('fronteres G', [(z['exp'], round(z['r_entrada_50pct'], 2), round(z['r_sortida_50pct'], 2)) for z in fronts['G']]); print('fronteres B', [(z['exp'], round(z['r_entrada_50pct'], 2), round(z['r_sortida_50pct'], 2)) for z in fronts['B']]); print('taca', json.dumps(taca, indent=1))


if __name__ == '__main__':
    main()
