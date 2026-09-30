"""A6 · Vistes en POLAR (norma: mira les vistes en polar): passa-alt 2D (σ16 en ln) de la base V32,
Vixen, Sony A, Sony B i de les capes de filtre, desplegats en (azimut, radi), amb els traços de
Pere a sobre. Un anell sencer surt com una línia horitzontal; una frontera de fotograma també.
Dos trams: interior 1,0–3,0 R☉ i intermedi 3,0–6,0 R☉. I el quocient Vixen/Sony B en polar.
Només lectura."""
from extract import *
from scipy.ndimage import gaussian_filter
V32T = ROOT / 'research/tools/v32_arcs_20260907'; C32 = V32T / 'cau'; PC = V32T / 'purs/cau'; CF = ROOT / 'research/tools/v29/cau_final'
H, W = 7506, 10551
NT = 2400


def to_polar(a, r0, r1, dr=1.0):
    rv = np.arange(r0 * RS, r1 * RS, dr, dtype=np.float32); th = np.linspace(-np.pi, np.pi, NT, endpoint=False, dtype=np.float32)
    X = (CX + rv[:, None] * np.cos(th)[None, :]).astype(np.float32); Y = (CY + rv[:, None] * np.sin(th)[None, :]).astype(np.float32)
    return cv2.remap(a, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan), rv / RS, np.degrees(th)


def hp2d(v, m, s):
    w = m.astype(np.float32)
    num = gaussian_filter(np.where(m, v, 0) * w, s); den = gaussian_filter(w, s)
    return np.where(m & (den > 0.2), v - num / np.maximum(den, 1e-6), np.nan)


def load(path, sup, ln, box):
    x0, y0, x1, y1 = box; a = np.load(path, mmap_mode='r')
    v = np.asarray(a[y0:y1, x0:x1, 1] if a.ndim == 3 else a[y0:y1, x0:x1], np.float32)
    m = np.isfinite(v) & ((v > 0) if ln else True)
    if sup is not None:
        m &= np.asarray(np.load(sup, mmap_mode='r')[y0:y1, x0:x1]) > 0
    return np.where(m, np.log(np.maximum(v, 1e-12)) if ln else v / 65535, 0).astype(np.float32), m


def panel(hp, scale):
    u = np.uint8(np.clip(0.5 + hp / (2 * scale), 0, 1) * 255); u[~np.isfinite(hp)] = 40
    return u


def main():
    cat = json.loads(Path(RUN.rebut('review_catalog.json')).read_text())
    for tram, (r0, r1), sigma, srcs in [
        ('interior', (1.0, 3.0), 12, [('base V32', C32 / 'base_G_v32.npy', C32 / 'support_v32.npy', True), ('Vixen V32', C32 / 'vixen_total_v32.npy', CF / 'vixen_support.npy', True), ('Sony A V32', C32 / 'sony_A_total_v32.npy', None, True), ('Sony B V32', C32 / 'sony_B_total_v32.npy', None, True),
                                    ('capa 04 micro', C32 / '04_v32_u16.npy', C32 / 'support_v32.npy', False), ('capa P03 MGN', PC / 'P03_MGN_u16.npy', C32 / 'support_v32.npy', False), ('capa P04 WOW', PC / 'P04_WOW_u16.npy', C32 / 'support_v32.npy', False)]),
        ('intermedi', (3.0, 6.0), 24, [('base V32', C32 / 'base_G_v32.npy', C32 / 'support_v32.npy', True), ('Vixen V32', C32 / 'vixen_total_v32.npy', CF / 'vixen_support.npy', True), ('Sony A V32', C32 / 'sony_A_total_v32.npy', None, True), ('Sony B V32', C32 / 'sony_B_total_v32.npy', None, True),
                                     ('capa 05 fi 2-48', C32 / '05_v32_u16.npy', C32 / 'support_v32.npy', False), ('capa 06 estructura', C32 / '06_v32_u16.npy', C32 / 'support_v32.npy', False), ('base V31', ROOT / 'research/tools/v31_purs/cau/base_G.npy', ROOT / 'research/tools/v31_purs/cau/support.npy', True)])]:
        pad = 4 * sigma + 8; box = (max(int(CX - r1 * RS) - pad, 0), max(int(CY - r1 * RS) - pad, 0), min(int(CX + r1 * RS) + pad, W), min(int(CY + r1 * RS) + pad, H))
        x0, y0 = box[0], box[1]
        # traços de Pere en polar (tots els colors), com a màscara
        strokes = np.zeros((box[3] - y0, box[2] - x0), np.uint8)
        for m in cat['marks']:
            lo, _, hi = m['paint_radius_R_p05_p50_p95']
            if hi < r0 - 0.1 or lo > r1 + 0.1:
                continue
            c = np.load(WIN / (m['id'] + '_codes.npy')); wx0, wy0, wx1, wy1 = m['window_bbox']
            ys, xs = np.nonzero(c); ys += wy0 - y0; xs += wx0 - x0; k = (ys >= 0) & (ys < strokes.shape[0]) & (xs >= 0) & (xs < strokes.shape[1]); strokes[ys[k], xs[k]] = 1
        pol_s, rv, th = to_polar(strokes.astype(np.float32), r0, r1)
        pol_s = np.nan_to_num(pol_s) > 0.3
        # shift de coordenades: to_polar treballa amb CX,CY absoluts; els arrays són retallats → ajusta
        panels = []
        for name, path, sup, ln in srcs:
            v, m = load(path, sup, ln, box); hp = hp2d(v, m, sigma)
            # remap amb centre relatiu al retall
            rvpx = np.arange(r0 * RS, r1 * RS, 1.0, dtype=np.float32); thr = np.linspace(-np.pi, np.pi, NT, endpoint=False, dtype=np.float32)
            X = (CX - x0 + rvpx[:, None] * np.cos(thr)[None, :]).astype(np.float32); Y = (CY - y0 + rvpx[:, None] * np.sin(thr)[None, :]).astype(np.float32)
            hpn = np.where(np.isfinite(hp), hp, 0).astype(np.float32); mk = np.isfinite(hp).astype(np.float32)
            pol = cv2.remap(hpn, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); pm = cv2.remap(mk, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) > 0.99
            pol = np.where(pm, pol, np.nan)
            z = pol[np.isfinite(pol)]; scale = float(np.percentile(np.abs(z), 98)) if z.size else 1.0
            panels.append((name, pol, scale))
            del v, m, hp
        # el traç en polar amb el mateix remap
        X = (CX - x0 + np.arange(r0 * RS, r1 * RS, 1.0, dtype=np.float32)[:, None] * np.cos(np.linspace(-np.pi, np.pi, NT, endpoint=False, dtype=np.float32))[None, :]).astype(np.float32)
        Y = (CY - y0 + np.arange(r0 * RS, r1 * RS, 1.0, dtype=np.float32)[:, None] * np.sin(np.linspace(-np.pi, np.pi, NT, endpoint=False, dtype=np.float32))[None, :]).astype(np.float32)
        pol_s = cv2.remap(strokes.astype(np.float32), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) > 0.3
        nr = panels[0][1].shape[0]; ph = nr + 24; im = Image.new('RGB', (NT + 60, ph * len(panels)), (30, 30, 30)); dr = ImageDraw.Draw(im)
        for i, (name, pol, scale) in enumerate(panels):
            u = panel(pol, scale); rgb = np.stack([u, u, u], -1)
            edge = cv2.morphologyEx(pol_s.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
            rgb[edge] = (200, 60, 255)
            im.paste(Image.fromarray(rgb), (60, i * ph + 24))
            dr.text((64, i * ph + 4), f"{name} · passa-alt 2D σ{sigma} · ±{scale*100:.2f}{'%' if 'capa' not in name else ' u'} · r {r0}–{r1} R☉ (amunt→avall) · azimut −180…180° · contorn lila = traços de Pere", fill=(255, 255, 255), font=font(13))
            for rr_ in np.arange(np.ceil(r0 * 4) / 4, r1, 0.25):
                yy_ = int((rr_ - r0) * RS); dr.text((2, i * ph + 24 + yy_ - 6), f'{rr_:.2f}', fill=(200, 200, 200), font=font(11)); dr.line([(56, i * ph + 24 + yy_), (60, i * ph + 24 + yy_)], fill=(200, 200, 200))
        im.save(RUN.vista(f'R32_A6_polar_{tram}.png')); print('polar', tram, im.size, flush=True)
    # quocient Vixen / Sony B en polar (2,0–6,0 R☉), suavitzat σ8: el que un tren té i l'altre no
    r0, r1 = 2.0, 6.0; box = (max(int(CX - r1 * RS) - 40, 0), max(int(CY - r1 * RS) - 40, 0), min(int(CX + r1 * RS) + 40, W), min(int(CY + r1 * RS) + 40, H)); x0, y0 = box[0], box[1]
    v1, m1 = load(C32 / 'vixen_total_v32.npy', CF / 'vixen_support.npy', True, box); v2, m2 = load(C32 / 'sony_B_total_v32.npy', None, True, box); v3, m3 = load(C32 / 'sony_A_total_v32.npy', None, True, box)
    for nm, (va, ma, vb, mb) in {'Vixen_sobre_SonyB': (v1, m1, v2, m2), 'SonyA_sobre_SonyB': (v3, m3, v2, m2)}.items():
        m = ma & mb; d = np.where(m, va - vb, 0).astype(np.float32); d = gaussian_filter(d * m, 8) / np.maximum(gaussian_filter(m.astype(np.float32), 8), 1e-6)
        d = d - np.nanmedian(d[m]); d = np.where(m, d, np.nan)
        rvpx = np.arange(r0 * RS, r1 * RS, 1.0, dtype=np.float32); thr = np.linspace(-np.pi, np.pi, NT, endpoint=False, dtype=np.float32)
        X = (CX - x0 + rvpx[:, None] * np.cos(thr)[None, :]).astype(np.float32); Y = (CY - y0 + rvpx[:, None] * np.sin(thr)[None, :]).astype(np.float32)
        pol = cv2.remap(np.nan_to_num(d), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); pm = cv2.remap(m.astype(np.float32), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) > 0.99
        pol = np.where(pm, pol, np.nan); u = panel(pol, 0.02)
        im = Image.new('L', (NT + 60, pol.shape[0] + 24), 30); im.paste(Image.fromarray(u), (60, 24)); dr = ImageDraw.Draw(im)
        dr.text((64, 4), f'ln({nm.replace("_", " ")}) σ8, mediana restada · ±2 % · r {r0}–{r1} R☉ amunt→avall · azimut −180…180°', fill=255, font=font(13))
        for rr_ in np.arange(2.0, r1, 0.5):
            yy_ = int((rr_ - r0) * RS); dr.text((2, 24 + yy_ - 6), f'{rr_:.1f}', fill=200, font=font(11))
        im.save(RUN.vista(f'R32_A6_polar_quocient_{nm}.png')); print('quocient', nm, flush=True)


if __name__ == '__main__':
    main()
