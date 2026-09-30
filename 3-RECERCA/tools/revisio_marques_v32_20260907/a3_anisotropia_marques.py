"""A3 · A cada finestra de marca, on hi ha l'estructura tangencial?

Puntuació d'orientació del tensor d'estructura (mateixa definició que a4 de v32_arcs: +1 =
crestes tangencials/arcs centrats al Sol, −1 = radials, 0 = isòtrop; ponderada per l'energia del
gradient) dins de la caixa de cada marca, a les escales σ 4/8/16/32 px, sobre:
  · la capa de filtre on Pere ha pintat (u16 de la V32, sense pintura);
  · la base V32 (G lineal fusionat, ln) i la base V31 (abans de la cura);
  · cada tren V32 per separat: Vixen, Sony A, Sony B (ln).
Lectura: arc al filtre i a la base però no als trens → fusió; a Sony B sola → font Sony; als
dos trens → estructura compartida (corona o cel). Només lectura."""
from extract import *
from scipy.ndimage import gaussian_filter
V32T = ROOT / 'research/tools/v32_arcs_20260907'; C32 = V32T / 'cau'; PC = V32T / 'purs/cau'; V31P = ROOT / 'research/tools/v31_purs'
LAYER_ARRAY = {2: C32 / '03_v32_u16.npy', 3: C32 / '03v30_v32_u16.npy', 4: C32 / '07_v32_u16.npy', 5: C32 / '01_v32_u16.npy', 6: C32 / '02_v32_u16.npy', 7: C32 / '04_v32_u16.npy',
               8: C32 / '05_v32_u16.npy', 9: C32 / '06_v32_u16.npy', 12: PC / 'P01_NRGF_u16.npy', 13: PC / 'P02_RHEF_u16.npy', 14: PC / 'P03_MGN_u16.npy', 15: PC / 'P04_WOW_u16.npy',
               16: PC / 'P05_WOW_bilateral_u16.npy', 17: PC / 'P06_NAFE_u16.npy', 18: PC / 'P07_ACHF_precursor16_u16.npy', 19: PC / 'P08_ACHF_precursor32_u16.npy', 20: PC / 'P09_SWAP_pilot_u16.npy', 21: PC / 'C01_Passa_alt24_lineal_u16.npy'}
SOURCES = {'base_V32': (C32 / 'base_G_v32.npy', C32 / 'support_v32.npy', True), 'base_V31': (V31P / 'cau/base_G.npy', V31P / 'cau/support.npy', True),
           'vixen_V32': (C32 / 'vixen_total_v32.npy', None, True), 'sonyA_V32': (C32 / 'sony_A_total_v32.npy', None, True), 'sonyB_V32': (C32 / 'sony_B_total_v32.npy', None, True)}
SIGMES = [4, 8, 16, 32]
H, W = 7506, 10551


def score(img, m, t, sig):
    w = m.astype(np.float32)
    def ng(a, s):
        return gaussian_filter(a * w, s, mode='nearest') / np.maximum(gaussian_filter(w, s, mode='nearest'), 1e-6)
    band = np.where(m, ng(img, sig) - ng(img, 2 * sig), 0).astype(np.float32)
    gy, gx = np.gradient(band); s2 = 1.5 * sig
    Jxx = gaussian_filter(gx * gx, s2); Jyy = gaussian_filter(gy * gy, s2); Jxy = gaussian_filter(gx * gy, s2)
    c2 = Jxx - Jyy; s2v = 2 * Jxy; E = Jxx + Jyy
    proj = c2 * np.cos(2 * t) + s2v * np.sin(2 * t)
    return proj, E


def window(arr, sup, box, ln):
    x0, y0, x1, y1 = box
    a = np.asarray(arr[y0:y1, x0:x1, 1] if arr.ndim == 3 else arr[y0:y1, x0:x1], np.float32)
    m = np.isfinite(a) & ((a > 0) if ln else True)
    if sup is not None:
        m &= np.asarray(sup[y0:y1, x0:x1]) > 0
    v = np.where(m, np.log(np.maximum(a, 1e-12)) if ln else a, 0).astype(np.float32)
    return v, m


def main():
    cat = json.loads(Path(RUN.rebut('review_catalog.json')).read_text()); marks = [m for m in cat['marks'] if m['color'] != 'neutre']
    srcs = {k: (np.load(p, mmap_mode='r'), (np.load(s, mmap_mode='r') if s else None), ln) for k, (p, s, ln) in SOURCES.items()}
    layers = {}
    out = []
    TILE, PAD = 512, 96
    for n, mk in enumerate(marks):
        i = mk['layer_index']; x0, y0, x1, y1 = mk['bbox']
        codes = np.load(WIN / (mk['id'] + '_codes.npy')) > 0; wx0, wy0, wx1, wy1 = mk['window_bbox']
        res = {'id': mk['id'], 'layer_index': i, 'layer': mk['layer'], 'color': mk['color'], 'family': mk['family'], 'r_p05_p50_p95': mk['paint_radius_R_p05_p50_p95'], 'scores': {}}
        names = (['filtre'] if i in LAYER_ARRAY else []) + list(srcs)
        if i in LAYER_ARRAY and i not in layers:
            layers[i] = np.load(LAYER_ARRAY[i], mmap_mode='r')
        acc = {k: {sig: [0.0, 0.0] for sig in SIGMES} for k in names}; npx = 0
        # tessel·les de TILE px sobre la finestra del traç; només les que tenen pintura
        for ty in range(wy0, wy1, TILE):
            for tx in range(wx0, wx1, TILE):
                sub = codes[ty - wy0:min(ty + TILE, wy1) - wy0, tx - wx0:min(tx + TILE, wx1) - wx0]
                if not sub.any():
                    continue
                X0, Y0, X1, Y1 = max(tx - PAD, 0), max(ty - PAD, 0), min(tx + TILE + PAD, W), min(ty + TILE + PAD, H)
                yy, xx = np.mgrid[Y0:Y1, X0:X1].astype(np.float32); t = np.arctan2(yy - CY, xx - CX)
                painted = np.zeros((Y1 - Y0, X1 - X0), bool); painted[ty - Y0:ty - Y0 + sub.shape[0], tx - X0:tx - X0 + sub.shape[1]] = sub
                painted = cv2.dilate(painted.astype(np.uint8), np.ones((25, 25), np.uint8)) > 0
                inner = np.zeros_like(painted); inner[ty - Y0:min(ty + TILE, Y1) - Y0, tx - X0:min(tx + TILE, X1) - X0] = True
                sel0 = painted & inner
                for k in names:
                    if k == 'filtre':
                        v, m = window(layers[i], srcs['base_V32'][1], (X0, Y0, X1, Y1), False)
                    else:
                        arr, sup, ln = srcs[k]; v, m = window(arr, sup, (X0, Y0, X1, Y1), ln)
                    if m.sum() < 500:
                        continue
                    sel = sel0 & m
                    if sel.sum() < 50:
                        continue
                    for sig in SIGMES:
                        proj, E = score(v, m, t, sig); acc[k][sig][0] += float(np.sum(proj[sel])); acc[k][sig][1] += float(np.sum(E[sel]))
                npx += int(sel0.sum())
        for k in names:
            row = {}
            for sig in SIGMES:
                sp, se = acc[k][sig]; row[f's{sig}_traç'] = (sp / se) if se > 0 else None
            res['scores'][k] = row if any(v is not None for v in row.values()) else None
        res['n_px_traç_dilatat'] = npx
        out.append(res)
        if n % 10 == 0:
            print(n, mk['id'], {k: (None if v is None else round(v.get('s8_traç') or 0, 3)) for k, v in res['scores'].items()}, flush=True)
    write(RUN.rebut('R32_anisotropia_marques.json'), {'marks': out, 'sigmes': SIGMES, 'definition': 'structure-tensor tangential score (+1 arcs centred on the Sun, -1 rays) weighted by gradient energy; DoG sigma/2sigma; evaluated on the painted stroke dilated 25 px, by 512-px tiles with 96-px pad'})
    # taula: puntuació σ8 al traç
    lines = ['# R32 · anisotropia tangencial al traç de cada marca (σ 8 px; + arcs, − raigs)', '', '| marca | capa | color | família | r | filtre | base V32 | base V31 | Vixen V32 | Sony A V32 | Sony B V32 |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for r in out:
        def f(k):
            v = r['scores'].get(k); s = None if v is None else v.get('s8_traç')
            return '–' if s is None else f'{s:+.2f}'
        lines.append(f"| {r['id']} | {r['layer'][:24]} | {r['color']} | {r['family'][:30]} | {r['r_p05_p50_p95'][0]:.2f}–{r['r_p05_p50_p95'][2]:.2f} | {f('filtre')} | {f('base_V32')} | {f('base_V31')} | {f('vixen_V32')} | {f('sonyA_V32')} | {f('sonyB_V32')} |")
    Path(RUN.lliurable('R32_ANISOTROPIA_TAULA.md')).write_text('\n'.join(lines) + '\n'); print('A3 fet', len(out), flush=True)


if __name__ == '__main__':
    main()
