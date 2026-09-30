"""p1 (V100 detall · PÍXELS) · REGISTRE subpíxel de la V80 (i de les versions de l'època V69–V78) contra la V99 i contra la dada D29.
Hipòtesi: V80 = llenç[1142:6263, 1325:9348]. Es mesura, per pegats de 128 px de corona (d 20–330 px del cercle de presentació),
el desplaçament per correlació de fase amb sobremostreig ×100 sobre el pas de banda (σ1 − σ6) de ln(lluminància lineal),
i s'hi ajusta una afí robusta (desplaçament + rotació + escala + cisalla). Contrast independent: ECC afí d'OpenCV sobre la mateixa màscara.
Porta: |desplaçament previst a la banda| i incertesa < 0,5 px; si no, s'atura (sortida != 0).
Sortida: 4-RESULTATS/v100_detall_20260925/pixels/P1_REGISTRE.json  (només fitxers nous)."""
import json, sys, time
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter
from skimage.registration import phase_cross_correlation
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from p0_comu_pixels import FIN, SORT, LX, LY, RL, llegeix_finestra, ln_lum, geometria, d29_a_finestra, FONTS

SORT.mkdir(parents=True, exist_ok=True)
y0, y1, x0, x1 = FIN
d, pa = geometria()
YY, XX = np.mgrid[y0:y1, x0:x1].astype(np.float64)


def bp(a, m=None):
    """pas de banda σ1 − σ6 amb convolució normalitzada dins de m (si n'hi ha)."""
    if m is None:
        m = np.isfinite(a)
    a0 = np.where(m, a, 0.0); w = m.astype(np.float64)
    g1 = gaussian_filter(a0, 1.0) / np.maximum(gaussian_filter(w, 1.0), 1e-9)
    g6 = gaussian_filter(a0, 6.0) / np.maximum(gaussian_filter(w, 6.0), 1e-9)
    return np.where(m, g1 - g6, 0.0)


def pegats(ref, mov, zona, P=128, pas=48):
    win = np.outer(np.hanning(P), np.hanning(P))
    res = []
    for cy in range(P // 2 + 4, ref.shape[0] - P // 2 - 4, pas):
        for cx in range(P // 2 + 4, ref.shape[1] - P // 2 - 4, pas):
            sl = (slice(cy - P // 2, cy + P // 2), slice(cx - P // 2, cx + P // 2))
            if zona[sl].mean() < 0.97:
                continue
            a, b = ref[sl], mov[sl]
            if a.std() < 1e-6 or b.std() < 1e-6:
                continue
            sh, err, _ = phase_cross_correlation(a * win, b * win, upsample_factor=100, normalization=None)
            # sh = desplaçament que cal aplicar a `mov` per registrar-la a `ref`: ref(x) ≈ mov(x − sh)
            M = np.float32([[1, 0, sh[1]], [0, 1, sh[0]]])
            bw = cv2.warpAffine(b.astype(np.float32), M, (P, P), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
            c = np.corrcoef((a * win)[16:-16, 16:-16].ravel(), (bw * win)[16:-16, 16:-16].ravel())[0, 1]
            c0 = np.corrcoef((a * win)[16:-16, 16:-16].ravel(), (b * win)[16:-16, 16:-16].ravel())[0, 1]
            res.append((cx + x0, cy + y0, -sh[1], -sh[0], c, c0))  # (X, Y llenç del centre, ux, uy) amb mov(x) ≈ ref(x − u)... vegeu nota
    return np.array(res)


def ajusta(R, ncc_min=0.35):
    """u(p) = t + A (p − centre Lluna), robust (3 passades, 3σ). u = on és a `mov` (en px del llenç) el detall que a `ref` és a p, menys p."""
    ok = R[:, 4] >= ncc_min
    for _ in range(4):
        P = np.c_[np.ones(ok.sum()), R[ok, 0] - LX, R[ok, 1] - LY]
        cx, *_ = np.linalg.lstsq(P, R[ok, 2], rcond=None); cy, *_ = np.linalg.lstsq(P, R[ok, 3], rcond=None)
        Pa = np.c_[np.ones(len(R)), R[:, 0] - LX, R[:, 1] - LY]
        rx, ry = R[:, 2] - Pa @ cx, R[:, 3] - Pa @ cy
        s = np.sqrt(np.mean(rx[ok] ** 2 + ry[ok] ** 2) / 2)
        ok = (R[:, 4] >= ncc_min) & (np.hypot(rx, ry) < 3 * max(s, 0.05))
    # incertesa per bootstrap
    rng = np.random.default_rng(1); idx = np.flatnonzero(ok); bt = []
    for _ in range(300):
        j = rng.choice(idx, len(idx)); P = np.c_[np.ones(len(j)), R[j, 0] - LX, R[j, 1] - LY]
        bx_, *_ = np.linalg.lstsq(P, R[j, 2], rcond=None); by_, *_ = np.linalg.lstsq(P, R[j, 3], rcond=None); bt.append(np.r_[bx_, by_])
    bt = np.array(bt)
    A = np.array([[cx[1], cx[2]], [cy[1], cy[2]]])
    rot = np.degrees((A[1, 0] - A[0, 1]) / 2) * 60  # arcmin (y cap avall: positiu = gir horari a la imatge)
    esc = (A[0, 0] + A[1, 1]) / 2  # A = gradient del desplaçament: escala − 1
    def u_a(pa_, dd):
        X = LX + (RL + dd) * np.cos(np.radians(pa_)); Y = LY - (RL + dd) * np.sin(np.radians(pa_))
        v = np.array([1, X - LX, Y - LY]); ux, uy = v @ cx, v @ cy
        su = np.std(bt[:, :3] @ v), np.std(bt[:, 3:] @ v)
        return [round(float(ux), 3), round(float(uy), 3), round(float(su[0]), 3), round(float(su[1]), 3)]
    return dict(n_pegats=int(len(R)), n_usats=int(ok.sum()), ncc_mediana=round(float(np.median(R[ok, 4])), 3),
                ncc_mediana_sense_moure=round(float(np.median(R[ok, 5])), 3),
                t_al_centre_px=[round(float(cx[0]), 3), round(float(cy[0]), 3)], t_sigma=[round(float(bt[:, 0].std()), 3), round(float(bt[:, 3].std()), 3)],
                rotacio_arcmin=round(float(rot), 3), escala_ppm=round(float(esc * 1e6), 1),
                A=np.round(A, 7).tolist(), residu_rms_px=round(float(s), 3),
                u_banda_dalt_PA105_d0=u_a(105, 0), u_banda_baix_PA230_d0=u_a(230, 0), u_PA0_d0=u_a(0, 0), u_PA270_d0=u_a(270, 0),
                coef_x=cx.tolist(), coef_y=cy.tolist()), ok


def ecc(ref, mov, zona):
    W = np.eye(2, 3, dtype=np.float32)
    try:
        cc, W = cv2.findTransformECC(ref.astype(np.float32), mov.astype(np.float32), W, cv2.MOTION_AFFINE,
                                     (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-7), zona.astype(np.uint8), 1)
    except cv2.error as e:
        return dict(error=str(e)[:200])
    # mov(W·x) ≈ ref(x), coords de finestra; desplaçament a la banda
    def u_a(pa_, dd):
        X = LX + (RL + dd) * np.cos(np.radians(pa_)) - x0; Y = LY - (RL + dd) * np.sin(np.radians(pa_)) - y0
        q = W @ np.array([X, Y, 1.0]); return [round(float(q[0] - X), 3), round(float(q[1] - Y), 3)]
    return dict(cc=round(float(cc), 4), W=np.round(W, 6).tolist(), u_banda_dalt_PA105_d0=u_a(105, 0), u_banda_baix_PA230_d0=u_a(230, 0),
                u_PA0_d0=u_a(0, 0), u_PA270_d0=u_a(270, 0))


def main():
    t0 = time.time()
    fonts = [f for f in sys.argv[1:]] or ['V98', 'V80', 'V75C', 'V78', 'V71', 'V69']
    zona = (d > 20) & (d < 330)
    refs = {'V99': ln_lum(llegeix_finestra('V99'))}
    G = d29_a_finestra('G'); mG = np.isfinite(G) & (G > 0) & (d > 2)
    refs['D29'] = np.where(mG, np.log(np.where(mG, G, 1.0)), np.nan)
    bref = {'V99': bp(refs['V99']), 'D29': bp(refs['D29'], mG)}
    zref = {'V99': zona, 'D29': zona & mG & (d < 300)}
    out = {'hipotesi_offsets': {k: v[1] for k, v in FONTS.items()}, 'nota_signe': "u = on és al fitxer (en px del llenç, sobre la hipòtesi) el detall que a la referència és al punt; mov(p + u) ≈ ref(p)"}
    for f in fonts:
        if not FONTS[f][0].exists():
            out[f] = 'no existeix'; continue
        m = ln_lum(llegeix_finestra(f))
        bm = bp(m)
        for rn in (['V99', 'D29'] if f in ('V80', 'V75C', 'V78') else ['V99']):
            if f == rn:
                continue
            R = pegats(bref[rn], bm, zref[rn])
            fit, ok = ajusta(R)
            fit['ecc'] = ecc(bref[rn], bm, zref[rn])
            out[f'{f}_contra_{rn}'] = fit
            np.save(SORT / f'P1_pegats_{f}_contra_{rn}.npy', R)
            print(f, 'contra', rn, json.dumps({k: fit[k] for k in ('n_usats', 'ncc_mediana', 'ncc_mediana_sense_moure', 't_al_centre_px', 't_sigma', 'rotacio_arcmin', 'escala_ppm', 'residu_rms_px', 'u_banda_dalt_PA105_d0', 'u_banda_baix_PA230_d0')}), fit['ecc'].get('u_banda_dalt_PA105_d0'), fit['ecc'].get('cc'), flush=True)
    # V99 contra D29: control del marc (han de coincidir)
    R = pegats(bref['D29'], bref['V99'], zref['D29']); fit, _ = ajusta(R); fit['ecc'] = ecc(bref['D29'], bref['V99'], zref['D29'])
    out['V99_contra_D29'] = fit
    print('V99 contra D29', fit['t_al_centre_px'], fit['rotacio_arcmin'], fit['residu_rms_px'], fit['u_banda_dalt_PA105_d0'], fit['ecc'].get('u_banda_dalt_PA105_d0'))
    out['segons'] = round(time.time() - t0, 1)
    p = SORT / 'P1_REGISTRE.json'
    if p.exists():
        p = SORT / f'P1_REGISTRE_{int(time.time())}.json'
    p.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print('fet', p)


if __name__ == '__main__':
    main()
