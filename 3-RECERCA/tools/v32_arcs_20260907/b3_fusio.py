"""B3 · Fusió dels apuntaments Sony i dels dos trens amb la font corregida (V32).

1. Apuntaments A/B: mateix mètode que `v29/merge_pointings.py` (ln(B/A) polinomi de
   grau 2 per mediana de blocs del mateix cel + residu local σ128 a 1/8; B primària,
   A només a la vora del seu suport amb ploma de 384 px; ghost de A exclòs de l'ajust),
   recalculat sobre els totals V32 (camps + offsets + flat) → `sony_corrected_total_v32`.
2. Trens: la V31 usava UN guany escalar Sony→Vixen (0,3411) i el canvi de font
   smoothstep 2–2,65 R☉ amb tall SEC al límit del suport Sony. Aquí:
   · guany ρ(x) per canal = ln(Vixen/Sony) suavitzat (σ 256 px, normalitzat) on els dos
     trens tenen dada bona (1,5–4 R☉ i pes ≥ 2 % de l'assolible), estès per veí més proper
     fora d'aquesta finestra (constant cap enfora: cap estructura nova a >4 R☉);
   · el mateix smoothstep 2–2,65 R☉ dins del suport Sony;
   · a la VORA del suport Sony (on la V31 canviava de Sony a Vixen de cop) una ploma
     de 160 px cap endins perquè la Vixen agafi el relleu gradualment (família V de la skill).
   Sortides: `fusion_total_v32.npy` (H,W,3 sRGB lineal), `base_G_v32.npy`, `support_v32.npy`
   (= fusion_support de la V29, sense canvis), `rho_v32.npy`, rebut B3.
"""
from comu32 import *
from scipy.ndimage import distance_transform_edt

RHO_SIGMA_PX = 256.0
EDGE_FEATHER_PX = 160.0


def design(x, y):
    return np.stack([np.ones_like(x), x, y, x * x, x * y, y * y], axis=-1)


def merge_pointings():
    A = np.load(CAU32 / 'sony_A_total_v32.npy', mmap_mode='r'); B = np.load(CAU32 / 'sony_B_total_v32.npy', mmap_mode='r')
    pa = np.load(CAUF / 'sony_A_weights.npy', mmap_mode='r'); pb = np.load(CAUF / 'sony_B_weights.npy', mmap_mode='r')
    ma = np.all(np.isfinite(A) & (A > 0) & (pa > 0), axis=2); mb = np.all(np.isfinite(B) & (B > 0) & (pb > 0), axis=2)
    r, t = coords(); y, x = np.ogrid[:H, :W]; gx = (x - W / 2) / 4000; gy = (y - H / 2) / 4000
    db = cv2.distanceTransform((mb | (r < 1.2 * RS)).astype(np.uint8), cv2.DIST_L2, 5)
    da = cv2.distanceTransform((ma | (r < 1.2 * RS)).astype(np.uint8), cv2.DIST_L2, 5)
    dist = np.hypot(x - GHOST_XY[0], y - GHOST_XY[1])
    # la ploma A/B és la de la V29 (suport físic, B primària, 384 px): es reutilitza tal qual
    weight = np.asarray(np.load(CAUF / 'sony_A_blend_weight.npy', mmap_mode='r'), np.float32)
    mine = np.where(mb, (1 - smooth(db, 0, 384)) * ma, ma).astype(np.float32)
    diff = float(np.mean(np.abs(mine[::9, ::9] - weight[::9, ::9]) > 1e-3))
    out = np.lib.format.open_memmap(CAU32 / 'sony_corrected_total_v32.npy', mode='w+', dtype=np.float32, shape=(H, W, 3))
    rep = {'ploma_AB_fraccio_cel·les_diferents_de_la_V29': diff, 'model': 'com merge_pointings.py V29: ln(B/A) grau 2 (blocs 128 px, mediana), residu local σ128 a 1/8; B primària, A a la vora amb ploma 384 px; ghost A exclòs', 'channels': {}}
    boxes = []; overlap = ma & mb
    for yy in range(0, H - 128, 128):
        for xx in range(0, W - 128, 128):
            sl = (slice(yy, yy + 128, 4), slice(xx, xx + 128, 4)); good = overlap[sl] & (r[sl] > 2 * RS) & (r[sl] < 10 * RS) & (dist[sl] > 250) & (da[sl] > 60) & (db[sl] > 60)
            if good.mean() > .8:
                boxes.append((sl, good, (xx + 64 - W / 2) / 4000, (yy + 64 - H / 2) / 4000))
    D = design(np.array([b[2] for b in boxes]), np.array([b[3] for b in boxes]))
    for c in range(3):
        q = np.array([np.median(np.log(B[sl + (c,)][good] / A[sl + (c,)][good])) for sl, good, _, _ in boxes]); use = np.isfinite(q)
        for _ in range(4):
            coef = np.linalg.lstsq(D[use], q[use], rcond=None)[0]; res = q - D @ coef; mad = max(1.4826 * np.median(np.abs(res[use] - np.median(res[use]))), 1e-5); use = np.isfinite(q) & (np.abs(res) < 4 * mad)
        pred = coef[0] + coef[1] * gx + coef[2] * gy + coef[3] * gx * gx + coef[4] * gx * gy + coef[5] * gy * gy
        factor = np.exp(pred).astype(np.float32)
        ratio = np.where(overlap & (dist > 220) & (A[..., c] > 0), np.log(np.maximum(B[..., c], 1e-8) / np.maximum(A[..., c], 1e-8)) - pred, 0).astype(np.float32)
        ratio = np.nan_to_num(ratio, nan=0, posinf=0, neginf=0); ok = (overlap & (dist > 220)).astype(np.float32)
        small = (W // 8, H // 8); wr = cv2.resize(ok, small, interpolation=cv2.INTER_AREA); nr = cv2.resize(ratio * ok, small, interpolation=cv2.INTER_AREA)
        low = gauss(nr, 16) / np.maximum(gauss(wr, 16), 1e-6); local = cv2.resize(low, (W, H), interpolation=cv2.INTER_LINEAR); factor *= np.exp(local)
        aa = np.nan_to_num(A[..., c], nan=0) * factor; bb = np.nan_to_num(B[..., c], nan=0)
        out[..., c] = aa * weight + bb * (1 - weight)
        rep['channels'][str(c)] = {'coefficients': coef, 'blocks': len(q), 'used': int(use.sum()), 'factor_p1_p50_p99': np.percentile(factor[ma], [1, 50, 99]), 'log_ratio_residual_p5_p50_p95': np.percentile(res[use], [5, 50, 95])}
        log(f'A/B canal {c}: factor p1/p50/p99 {rep["channels"][str(c)]["factor_p1_p50_p99"]}')
    out.flush(); del out
    return rep


def fuse_trains():
    r, t = coords()
    mv = np.load(CAUF / 'vixen_support.npy'); ms = np.load(CAUF / 'sony_support.npy'); m = mv | ms
    assert np.array_equal(m, np.load(CAUF / 'fusion_support.npy'))
    V = np.load(CAU32 / 'vixen_total_v32.npy', mmap_mode='r'); S = np.load(CAU32 / 'sony_corrected_total_v32.npy', mmap_mode='r')
    wvG = np.load(CAUF / 'vixen_weight_G.npy', mmap_mode='r'); wsG = np.load(CAUF / 'sony_weight_G.npy', mmap_mode='r')
    # pesos: smoothstep 2–2,65 R dins del suport Sony; ploma cap endins a la vora del suport Sony
    ds = cv2.distanceTransform(ms.astype(np.uint8), cv2.DIST_L2, 5)
    dv = cv2.distanceTransform(mv.astype(np.uint8), cv2.DIST_L2, 5)
    wv = (1 - smooth(r / RS, 2, 2.65)) * mv
    # ploma a la vora del suport Sony (la Vixen agafa el relleu), esvaïda TAMBÉ a la vora del propi suport Vixen:
    # sense això, on la Vixen s'acaba dins de la zona de ploma el seu pes queia de cop i dibuixava una costura en V (comprovat el 07-09).
    edge = (1 - smooth(ds, 0, EDGE_FEATHER_PX)) * smooth(dv, 0, EDGE_FEATHER_PX)
    wv = np.where(ms, np.maximum(wv, edge * mv), mv.astype(np.float32)).astype(np.float32); ws = ((1 - wv) * ms).astype(np.float32)
    np.save(CAU32 / 'weight_vixen_v32.npy', wv)
    out = np.lib.format.open_memmap(CAU32 / 'fusion_total_v32.npy', mode='w+', dtype=np.float32, shape=(H, W, 3))
    rho_all = np.empty((H, W, 3), np.float32)
    good_fit = mv & ms & comu.mascara_dada(np.asarray(wvG), r) & comu.mascara_dada(np.asarray(wsG), r) & (r > 1.5 * RS) & (r < 4.0 * RS)
    y, x = np.ogrid[:H, :W]; good_fit &= np.hypot(x - GHOST_XY[0], y - GHOST_XY[1]) > 240
    rep = {'rho_sigma_px': RHO_SIGMA_PX, 'edge_feather_px': EDGE_FEATHER_PX, 'fit_window_R': [1.5, 4.0], 'channels': {}}
    small = (W // 8, H // 8)
    for c in range(3):
        v = np.asarray(V[..., c]); s = np.asarray(S[..., c])
        gf = good_fit & np.isfinite(v) & np.isfinite(s) & (v > 0) & (s > 0)
        lr = np.where(gf, np.log(np.maximum(v, 1e-9) / np.maximum(s, 1e-9)), 0).astype(np.float32); ok = gf.astype(np.float32)
        nr = cv2.resize(lr * ok, small, interpolation=cv2.INTER_AREA); wr = cv2.resize(ok, small, interpolation=cv2.INTER_AREA)
        sg = RHO_SIGMA_PX / 8
        num = gauss(nr, sg); den = gauss(wr, sg); low = np.where(den > 0.05, num / np.maximum(den, 1e-9), np.nan)
        bad = ~np.isfinite(low)
        if bad.any():
            idx = distance_transform_edt(bad, return_distances=False, return_indices=True); low = low[idx[0], idx[1]]
        rho = np.exp(cv2.resize(low.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)).astype(np.float32)
        rho_all[..., c] = rho
        # validació reservada: sectors alterns de 30° (mateix criteri que la V31 purs) amb el ρ ajustat a TOTS (el suavitzat σ256 no pot memoritzar sectors de 30° a 2–3,5 R)
        sect = (np.floor(np.degrees(np.mod(t, 2 * np.pi)) / 30).astype(int) % 2 == 1) & gf & (r > 2 * RS) & (r < 3.5 * RS)
        e = 100 * (s[sect] * rho[sect] / v[sect] - 1)
        ts = np.where(ms, s * rho, 0); tv = np.where(mv, v, 0)
        out[..., c] = (wv * tv + ws * ts).astype(np.float32)
        rep['channels'][str(c)] = {'rho_p1_p50_p99': [float(np.percentile(rho[ms & mv], q)) for q in (1, 50, 99)], 'holdout_sectors_median_bias_pct': float(np.median(e)), 'holdout_median_abs_err_pct': float(np.median(np.abs(e))), 'n_holdout': int(sect.sum())}
        log(f'tren canal {c}: ρ p1/p50/p99 {rep["channels"][str(c)]["rho_p1_p50_p99"]} · sectors reservats biaix {rep["channels"][str(c)]["holdout_sectors_median_bias_pct"]:+.3f}% |err| {rep["channels"][str(c)]["holdout_median_abs_err_pct"]:.3f}%')
        del v, s, lr, ok, rho, ts, tv
    out.flush()
    np.save(CAU32 / 'rho_v32.npy', rho_all); del rho_all
    base = np.asarray(out[..., 1]).copy(); base[~m] = 0
    np.save(CAU32 / 'base_G_v32.npy', base); np.save(CAU32 / 'support_v32.npy', m)
    rep['base_G_sha256'] = sha(CAU32 / 'base_G_v32.npy'); rep['fusion_sha256'] = sha(CAU32 / 'fusion_total_v32.npy')
    rep['nonpositive_observed_G'] = int((base[m] <= 0).sum())
    return rep


def main():
    if '--trains-only' in sys.argv and (REB / 'B3_fusio.json').exists():
        rep = json.loads((REB / 'B3_fusio.json').read_text())
    else:
        rep = {'pointings': merge_pointings()}
    rep['trains'] = fuse_trains()
    savejson(REB / 'B3_fusio.json', rep); log('B3 fet')


if __name__ == '__main__':
    main()
