"""A7 · El que els dos trens comparteixen és corona; el que no, no ho és.
En polar (1 px radial × 0,15° azimutal), passa-alt 2D σ12 (1,0–3,0 R☉) i σ24 (3,0–6,0 R☉) de
Vixen V32, Sony A V32, Sony B V32 i base V32. Per a cada traç de Pere (dilatat 25 px):
Pearson(Vixen, Sony B), Pearson(Sony A, Sony B) i el CONTROL NUL APARELLAT: Pearson(Vixen,
Sony B girada 180° en azimut) — mateixos radis, mateix soroll, cap estructura comuna possible.
També per bandes de radi (tot l'azimut). Només lectura."""
from extract import *
from scipy.ndimage import gaussian_filter
sys.path.insert(0, str(Path(__file__).parent)); from a6_vistes_polars import load, hp2d, NT
V32T = ROOT / 'research/tools/v32_arcs_20260907'; C32 = V32T / 'cau'; CF = ROOT / 'research/tools/v29/cau_final'
H, W = 7506, 10551


def polar_hp(path, sup, ln, r0, r1, sigma):
    pad = 4 * sigma + 8; box = (max(int(CX - r1 * RS) - pad, 0), max(int(CY - r1 * RS) - pad, 0), min(int(CX + r1 * RS) + pad, W), min(int(CY + r1 * RS) + pad, H)); x0, y0 = box[0], box[1]
    v, m = load(path, sup, ln, box); hp = hp2d(v, m, sigma)
    rvpx = np.arange(r0 * RS, r1 * RS, 1.0, dtype=np.float32); thr = np.linspace(-np.pi, np.pi, NT, endpoint=False, dtype=np.float32)
    X = (CX - x0 + rvpx[:, None] * np.cos(thr)[None, :]).astype(np.float32); Y = (CY - y0 + rvpx[:, None] * np.sin(thr)[None, :]).astype(np.float32)
    pol = cv2.remap(np.where(np.isfinite(hp), hp, 0).astype(np.float32), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    pm = cv2.remap(np.isfinite(hp).astype(np.float32), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) > 0.99
    return np.where(pm, pol, np.nan), box


def strokes_polar(cat, r0, r1, box):
    """Una màscara polar PER MARCA (abans, un sol mapa d'índexs feia que una marca sota una altra perdés píxels: caçat pel verificador el 07-09)."""
    x0, y0 = box[0], box[1]; hh, ww = box[3] - y0, box[2] - x0
    rvpx = np.arange(r0 * RS, r1 * RS, 1.0, dtype=np.float32); thr = np.linspace(-np.pi, np.pi, NT, endpoint=False, dtype=np.float32)
    X = (CX - x0 + rvpx[:, None] * np.cos(thr)[None, :]).astype(np.float32); Y = (CY - y0 + rvpx[:, None] * np.sin(thr)[None, :]).astype(np.float32)
    out = []
    for m in cat['marks']:
        lo, _, hi = m['paint_radius_R_p05_p50_p95']
        if hi < r0 - 0.1 or lo > r1 + 0.1 or m['color'] == 'neutre':
            continue
        c = (np.load(WIN / (m['id'] + '_codes.npy')) > 0).astype(np.uint8); c = cv2.dilate(c, np.ones((25, 25), np.uint8))
        wx0, wy0, wx1, wy1 = m['window_bbox']; full = np.zeros((hh, ww), np.uint8)
        ya, yb, xa, xb = max(wy0, y0), min(wy1, box[3]), max(wx0, x0), min(wx1, box[2])
        if yb > ya and xb > xa:
            full[ya - y0:yb - y0, xa - x0:xb - x0] = c[ya - wy0:yb - wy0, xa - wx0:xb - wx0]
        pm = cv2.remap(full, X, Y, cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT) > 0
        out.append((m['id'], pm))
    return out


def pearson(a, b, k):
    g = k & np.isfinite(a) & np.isfinite(b)
    if g.sum() < 200:
        return None, int(g.sum())
    x = a[g] - a[g].mean(); y = b[g] - b[g].mean(); d = np.sqrt((x * x).sum() * (y * y).sum())
    return (float((x * y).sum() / d) if d > 0 else None), int(g.sum())


def main():
    cat = json.loads(Path(RUN.rebut('review_catalog.json')).read_text()); out = {'marks': [], 'bandes': []}
    for tram, (r0, r1), sigma in [('interior', (1.0, 3.0), 12), ('intermedi', (3.0, 6.0), 24)]:
        P = {}
        for name, path, sup, ln in [('vixen', C32 / 'vixen_total_v32.npy', CF / 'vixen_support.npy', True), ('sonyA', C32 / 'sony_A_total_v32.npy', None, True), ('sonyB', C32 / 'sony_B_total_v32.npy', None, True), ('base', C32 / 'base_G_v32.npy', C32 / 'support_v32.npy', True)]:
            P[name], box = polar_hp(path, sup, ln, r0, r1, sigma); print(tram, name, flush=True)
        sB180 = np.roll(P['sonyB'], NT // 2, axis=1); sA180 = np.roll(P['sonyA'], NT // 2, axis=1)
        rr = r0 + np.arange(P['vixen'].shape[0]) / RS
        for mid, k in strokes_polar(cat, r0, r1, box):
            if k.sum() < 200:
                continue
            rVB, n = pearson(P['vixen'], P['sonyB'], k); rAB, _ = pearson(P['sonyA'], P['sonyB'], k); rVA, _ = pearson(P['vixen'], P['sonyA'], k)
            nVB, _ = pearson(P['vixen'], sB180, k); nAB, _ = pearson(P['sonyA'], sB180, k)
            rbB, _ = pearson(P['base'], P['sonyB'], k); rbV, _ = pearson(P['base'], P['vixen'], k)
            out['marks'].append({'id': mid, 'tram': tram, 'sigma': sigma, 'n_px_polar': n, 'r_Vixen_SonyB': rVB, 'r_SonyA_SonyB': rAB, 'r_Vixen_SonyA': rVA, 'nul_Vixen_SonyB180': nVB, 'nul_SonyA_SonyB180': nAB, 'r_base_SonyB': rbB, 'r_base_Vixen': rbV})
        for a, b in ([(1.1, 1.3), (1.3, 1.5), (1.5, 1.65), (1.65, 1.8), (1.8, 1.95), (1.95, 2.1), (2.1, 2.3), (2.3, 2.65), (2.65, 2.95)] if tram == 'interior' else [(3.0, 3.5), (3.5, 4.0), (4.0, 4.3), (4.3, 4.6), (4.6, 5.0), (5.0, 5.5), (5.5, 6.0)]):
            k = ((rr >= a) & (rr < b))[:, None] & np.ones((1, NT), bool)
            rVB, n = pearson(P['vixen'], P['sonyB'], k); rAB, _ = pearson(P['sonyA'], P['sonyB'], k); nVB, _ = pearson(P['vixen'], sB180, k); nAB, _ = pearson(P['sonyA'], sB180, k)
            out['bandes'].append({'tram': tram, 'sigma': sigma, 'banda_R': [a, b], 'n_px': n, 'r_Vixen_SonyB': rVB, 'r_SonyA_SonyB': rAB, 'nul_Vixen_SonyB180': nVB, 'nul_SonyA_SonyB180': nAB})
        del P
    write(RUN.rebut('R32_A7_correlacio_creuada.json'), out)
    lines = ['# R32 · A7 · correlació 2D entre trens al traç de cada marca (polar, passa-alt σ12 interior / σ24 intermedi), amb control nul aparellat (Sony B girada 180°)', '',
             '| marca | tram | n px | Vixen×SonyB | SonyA×SonyB | Vixen×SonyA | NUL Vixen×SonyB180 | NUL SonyA×SonyB180 | base×SonyB | base×Vixen |', '|---|---|---|---|---|---|---|---|---|---|']
    f = lambda v: '–' if v is None else f'{v:+.2f}'
    for m in out['marks']:
        lines.append(f"| {m['id']} | {m['tram']} | {m['n_px_polar']} | {f(m['r_Vixen_SonyB'])} | {f(m['r_SonyA_SonyB'])} | {f(m['r_Vixen_SonyA'])} | {f(m['nul_Vixen_SonyB180'])} | {f(m['nul_SonyA_SonyB180'])} | {f(m['r_base_SonyB'])} | {f(m['r_base_Vixen'])} |")
    lines += ['', '## Per bandes de radi (tot l\'azimut)', '', '| tram | banda R☉ | n px | Vixen×SonyB | SonyA×SonyB | NUL V×SB180 | NUL SA×SB180 |', '|---|---|---|---|---|---|---|']
    for b in out['bandes']:
        lines.append(f"| {b['tram']} | {b['banda_R'][0]}–{b['banda_R'][1]} | {b['n_px']} | {f(b['r_Vixen_SonyB'])} | {f(b['r_SonyA_SonyB'])} | {f(b['nul_Vixen_SonyB180'])} | {f(b['nul_SonyA_SonyB180'])} |")
    Path(RUN.lliurable('R32_A7_CORRELACIO_TAULA.md')).write_text('\n'.join(lines) + '\n'); print('\n'.join(lines))


if __name__ == '__main__':
    main()
