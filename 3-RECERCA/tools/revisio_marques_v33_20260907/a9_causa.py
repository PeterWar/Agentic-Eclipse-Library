"""A9 · La causa de cada marca de la V33, mesurada a la font.
Per a cada traç (sector azimutal del traç ± 2°): (1) perfil radial del SOROLL fi (rms del DoG 1,5/3 px de
ln G) en calaixos de 4 px a la Vixen V32, la Sony B V32 i la base V32; graó = rms just fora / rms just
dins del traç; (2) fraccions de pes per fotograma (A1, graella 1/4, canal G de la Vixen): radis d'entrada
(10 → 90 % del pes màxim) dels fotogrames que canvien dins del traç i AMPLADA de l'entrada en px;
(3) perfil de color ln(G/R), ln(G/B) de la Vixen (anell només-verd?); (4) per a les marques del WOW a
3–4,5 R☉: el mapa σ de la V33 (gradient dins del traç) — hipòtesi «artefacte de la V33 mateixa»."""
from extract import *
from scipy.ndimage import gaussian_filter
sys.path.insert(0, str(Path(__file__).parent)); from a4_color_i_rho import ring_profile, hp
V32T = ROOT / 'research/tools/v32_arcs_20260907'; C32 = V32T / 'cau'; CF = ROOT / 'research/tools/v29/cau_final'; C33 = ROOT / 'research/tools/v33_20260907/cau'
H, W = 7506, 10551


def load_ln(path, sup, box):
    x0, y0, x1, y1 = box; a = np.load(path, mmap_mode='r'); v = np.asarray(a[y0:y1, x0:x1, 1] if a.ndim == 3 else a[y0:y1, x0:x1], np.float32)
    m = np.isfinite(v) & (v > 0)
    if sup is not None:
        m &= np.asarray(np.load(sup, mmap_mode='r')[y0:y1, x0:x1]) > 0
    return np.where(m, np.log(np.maximum(v, 1e-9)), 0).astype(np.float32), m


def noise_profile(L, m, r, sect, lo, hi):
    w = m.astype(np.float32)
    def ng(a, s):
        return gaussian_filter(a * w, s) / np.maximum(gaussian_filter(w, s), 1e-6)
    fine = np.where(m, ng(L, 1.5) - ng(L, 3.0), 0)
    rr, p, n = ring_profile(fine ** 2, m & sect, r, max(1.02, lo - 0.35), hi + 0.35, step=4.0)
    return rr, np.sqrt(p)


def main():
    cat = json.loads(Path(RUN.rebut('review_catalog.json')).read_text()); marks = cat['marks']
    meta = json.loads((C32 / 'vixen_meta.json').read_text())['frames']; Wm = np.load(C32 / 'vixen_w.npy', mmap_mode='r'); hc, wc = Wm.shape[1:]
    rc = np.hypot(np.arange(wc)[None, :] * 4 + 1.5 - CX, np.arange(hc)[:, None] * 4 + 1.5 - CY); tc = np.degrees(np.arctan2(np.arange(hc)[:, None] * 4 + 1.5 - CY, np.arange(wc)[None, :] * 4 + 1.5 - CX))
    smap = np.load(C33 / 'resolucio_v33.npy', mmap_mode='r')
    out = []
    for mk in marks:
        lo, mid, hi = mk['paint_radius_R_p05_p50_p95']; a0, a1 = mk['paint_azimuth_deg_min_max']; full = (a1 - a0) > 300
        r1 = hi + 0.4; box = (max(int(CX - r1 * RS), 0), max(int(CY - r1 * RS), 0), min(int(CX + r1 * RS) + 1, W), min(int(CY + r1 * RS) + 1, H)); x0, y0 = box[0], box[1]
        yy, xx = np.mgrid[y0:box[3], x0:box[2]].astype(np.float32); r = np.hypot(xx - CX, yy - CY); t = np.degrees(np.arctan2(yy - CY, xx - CX))
        sect = np.ones_like(r, bool) if full else ((t >= a0 - 2) & (t <= a1 + 2))
        res = {'id': mk['id'], 'layer': mk['layer'], 'r': [lo, mid, hi], 'az': [a0, a1], 'soroll': {}, 'fotogrames': [], 'color': {}, 'sigma_v33': None}
        for name, path, sup in [('vixen', C32 / 'vixen_total_v32.npy', CF / 'vixen_support.npy'), ('sonyB', C32 / 'sony_B_total_v32.npy', None), ('base', C32 / 'base_G_v32.npy', C32 / 'support_v32.npy')]:
            L, m = load_ln(path, sup, box); rr, prof = noise_profile(L, m, r, sect, lo, hi)
            ins = (rr >= lo - 0.06) & (rr < lo); outs = (rr > hi) & (rr <= hi + 0.06); within = (rr >= lo) & (rr <= hi)
            g = np.isfinite(prof)
            step = float(np.nanmean(prof[outs & g]) / np.nanmean(prof[ins & g])) if (ins & g).sum() > 1 and (outs & g).sum() > 1 else None
            # el graó més gran de 12 px dins del tram ±0,1 R
            k = (rr >= lo - 0.1) & (rr <= hi + 0.1) & g; pr = prof[k]; rk = rr[k]
            ratio = pr[3:] / np.maximum(pr[:-3], 1e-12) if len(pr) > 4 else np.array([1.0]); j = int(np.argmax(np.abs(np.log(ratio)))) if len(ratio) else 0
            res['soroll'][name] = {'rms_dins_pct': float(100 * np.nanmean(prof[ins & g])) if (ins & g).any() else None, 'rms_fora_pct': float(100 * np.nanmean(prof[outs & g])) if (outs & g).any() else None, 'graó_fora_sobre_dins': step,
                                   'graó_max_12px': float(ratio[j]) if len(ratio) else None, 'r_graó_max': float(rk[j + 3]) if len(rk) > j + 3 else None, 'perfil_r': rr[g].tolist(), 'perfil_rms_pct': (100 * prof[g]).tolist()}
            if name == 'vixen':
                # color
                a = np.load(path, mmap_mode='r'); A = np.asarray(a[y0:box[3], x0:box[2]], np.float32); ok = m & (A > 0).all(2)
                for key, c in (('G/R', 0), ('G/B', 2)):
                    rr2, p2, _ = ring_profile(np.log(np.maximum(A[..., 1], 1e-9)) - np.log(np.maximum(A[..., c], 1e-9)), ok & sect, r, max(1.02, lo - 0.35), hi + 0.35, step=2.0); h24 = hp(p2, 12)
                    kin = (rr2 >= lo) & (rr2 <= hi); kct = ((rr2 >= lo - 0.3) & (rr2 < lo - 0.08)) | ((rr2 > hi + 0.08) & (rr2 <= hi + 0.3))
                    res['color'][key] = {'p2p_pct_dins': float(100 * (np.nanmax(h24[kin]) - np.nanmin(h24[kin]))) if np.isfinite(h24[kin]).sum() > 2 else None, 'rms_pct_dins': float(100 * np.sqrt(np.nanmean(h24[kin] ** 2))) if np.isfinite(h24[kin]).sum() > 2 else None, 'rms_pct_control': float(100 * np.sqrt(np.nanmean(h24[kct] ** 2))) if np.isfinite(h24[kct]).sum() > 2 else None}
                del A
        # fotogrames (Vixen G) al sector: fraccions per calaix de 8 px
        cells = (rc >= (lo - 0.3) * RS) & (rc < (hi + 0.3) * RS) & (np.ones_like(rc, bool) if full else ((tc >= a0 - 2) & (tc <= a1 + 2)))
        idx = np.flatnonzero(cells.ravel()); rcv = rc.ravel()[idx]; b = ((rcv - rcv.min()) / 8).astype(int); nb = int(b.max()) + 1; rb = np.array([rcv[b == i].mean() for i in range(nb)]) / RS
        tot = np.zeros(nb); F = []
        for i in range(Wm.shape[0]):
            w = np.asarray(Wm[i]).ravel()[idx]; sw = np.bincount(b, weights=w, minlength=nb); F.append(sw); tot += sw
        for i, sw in enumerate(F):
            f = sw / np.maximum(tot, 1e-20); k = (rb >= lo - 0.15) & (rb <= hi + 0.15)
            if k.sum() < 2 or (f[k].max() - f[k].min()) < 0.08:
                continue
            fm = f.max(); r10 = rb[np.flatnonzero(f >= 0.1 * fm)]; r90 = rb[np.flatnonzero(f >= 0.9 * fm)]
            entra = float(r10.min()) if r10.size else None; ple = float(r90.min()) if r90.size else None
            res['fotogrames'].append({'name': meta[i]['name'], 'exp': meta[i]['exp'], 'f_dins': float(f[k][0]), 'f_fora': float(f[k][-1]), 'delta_f': float(f[k][-1] - f[k][0]), 'r_entrada_10pct': entra, 'r_90pct': ple, 'amplada_entrada_px': float((ple - entra) * RS) if entra is not None and ple is not None else None})
        res['fotogrames'].sort(key=lambda z: -abs(z['delta_f']))
        # σ de la V33 al traç
        s = np.asarray(smap[y0:box[3], x0:box[2]]); kin = sect & (r >= lo * RS) & (r <= hi * RS)
        if kin.sum() > 100:
            s_in = s[kin]; res['sigma_v33'] = {'p10': float(np.percentile(s_in, 10)), 'p90': float(np.percentile(s_in, 90))}
        out.append(res)
        fz = res['fotogrames'][:3]
        print(f"{mk['id']} r {lo:.2f}-{hi:.2f} | soroll fora/dins: V {res['soroll']['vixen']['graó_fora_sobre_dins'] if res['soroll']['vixen']['graó_fora_sobre_dins'] is None else round(res['soroll']['vixen']['graó_fora_sobre_dins'],2)} SB {None if res['soroll']['sonyB']['graó_fora_sobre_dins'] is None else round(res['soroll']['sonyB']['graó_fora_sobre_dins'],2)} base {None if res['soroll']['base']['graó_fora_sobre_dins'] is None else round(res['soroll']['base']['graó_fora_sobre_dins'],2)} | graó max 12px base {round(res['soroll']['base']['graó_max_12px'],2) if res['soroll']['base']['graó_max_12px'] else None}@{round(res['soroll']['base']['r_graó_max'],2) if res['soroll']['base']['r_graó_max'] else None} | G/B dins/ctl {res['color'].get('G/B',{}).get('rms_pct_dins')} | fotogrames: " + ', '.join(f"{z['exp']:g}s Δf{z['delta_f']:+.2f} entra {z['r_entrada_10pct']}→{z['r_90pct']} ({z['amplada_entrada_px'] and round(z['amplada_entrada_px'])} px)" for z in fz), flush=True)
    write(RUN.rebut('R33_A9_causa.json'), {'marks': out, 'definicions': 'soroll fi = rms DoG 1,5/3 px de ln G per calaixos de 4 px al sector; graó = mitjana a 0,06 R fora / 0,06 R dins del traç; fotogrames: fraccions de pes A1 (Vixen G) per calaixos de 8 px; entrada = radi on la fracció passa del 10 al 90 % del seu màxim'})


if __name__ == '__main__':
    main()
