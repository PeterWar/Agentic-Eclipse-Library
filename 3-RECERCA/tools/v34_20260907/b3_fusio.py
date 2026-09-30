"""B3 (V34) · Fusió per VARIÀNCIA, a l'origen (research/149 §4.3).
1. Apuntaments Sony A/B: mateix model de guany A→B que la V32 (grau 2 + residu local σ128) i després
   fusió per variància: w = suport / σ² (σ² = variància local del gra fi de ln G, suavitzada 48 px),
   ghost de A exclòs (ploma 200→320 px), plomes de 160 px a la vora de cada suport. PORTA: correlació
   amb la Vixen (independent) a 2,5–5 R☉ (passa-alt σ12 i σ24 de ln G) de la fusió contra B sola; si la
   fusió no és ≥ B − 0,005 a les dues escales, es queda B sola (com la V32) i es declara.
2. Trens: ρ 2D per canal com la V32 (σ256, 1,5–4 R☉). Vixen sola fins a 1,9 R☉ (resolució nativa);
   pes Vixen = max(rampa V32, fracció 1/σ²): la variància només AFEGEIX Vixen de 2,65 enfora; plomes de 160 px a la vora
   del suport Sony (la Vixen agafa el relleu) i a la vora del suport Vixen (la Sony agafa el relleu).
Sortides: sony_corrected_total_v34, fusion_total_v34 (H,W,3), base_G_v34, support_v34, weight_vixen_v34, rho_v34, var maps."""
from comu34 import *
from scipy.ndimage import distance_transform_edt, gaussian_filter
RHO_SIGMA_PX = 256.0; EDGE_FEATHER_PX = 160.0; VAR_SIGMA_PX = 48.0; R_VIXEN_SOLA = (1.9, 2.1)
GHOST_IN, GHOST_OUT = 200.0, 320.0


def design(x, y):
    return np.stack([np.ones_like(x), x, y, x * x, x * y, y * y], axis=-1)


def var_map(G, m):
    """Variància local del gra fi (DoG 1,5/3 px de ln G), normalitzada al suport, suavitzada VAR_SIGMA_PX."""
    w = m.astype(np.float32); L = np.where(m, np.log(np.maximum(G, 1e-9)), 0).astype(np.float32)
    def ng(a, s):
        return gauss(a * w, s) / np.maximum(gauss(w, s), 1e-6)
    fine = np.where(m, ng(L, 1.5) - ng(L, 3.0), 0).astype(np.float32)
    v = gauss(fine * fine * w, VAR_SIGMA_PX) / np.maximum(gauss(w, VAR_SIGMA_PX), 1e-6)
    return np.where(m, np.maximum(v, 1e-12), np.nan).astype(np.float32)


def hp_ln(G, m, s):
    w = m.astype(np.float32); L = np.where(m, np.log(np.maximum(G, 1e-9)), 0).astype(np.float32)
    return np.where(m, L - gauss(L * w, s) / np.maximum(gauss(w, s), 1e-6), np.nan)


def corr_with(ref, refm, X, Xm, zone, s):
    a = hp_ln(ref, refm, s); b = hp_ln(X, Xm, s); k = zone & np.isfinite(a) & np.isfinite(b)
    x = a[k] - a[k].mean(); y = b[k] - b[k].mean(); d = np.sqrt((x * x).sum() * (y * y).sum()); return float((x * y).sum() / d) if d > 0 else None


def merge_pointings():
    A = np.load(CAU34 / 'sony_A_total_v34.npy', mmap_mode='r'); B = np.load(CAU34 / 'sony_B_total_v34.npy', mmap_mode='r')
    pa = np.load(CAUF / 'sony_A_weights.npy', mmap_mode='r'); pb = np.load(CAUF / 'sony_B_weights.npy', mmap_mode='r')
    ma = np.all(np.isfinite(A) & (A > 0) & (pa > 0), axis=2); mb = np.all(np.isfinite(B) & (B > 0) & (pb > 0), axis=2)
    r, t = coords(); y, x = np.ogrid[:H, :W]; gx = (x - W / 2) / 4000; gy = (y - H / 2) / 4000
    db = cv2.distanceTransform((mb | (r < 1.2 * RS)).astype(np.uint8), cv2.DIST_L2, 5); da = cv2.distanceTransform((ma | (r < 1.2 * RS)).astype(np.uint8), cv2.DIST_L2, 5)
    dist = np.hypot(x - GHOST_XY[0], y - GHOST_XY[1]).astype(np.float32)
    overlap = ma & mb; boxes = []
    for yy in range(0, H - 128, 128):
        for xx in range(0, W - 128, 128):
            sl = (slice(yy, yy + 128, 4), slice(xx, xx + 128, 4)); good = overlap[sl] & (r[sl] > 2 * RS) & (r[sl] < 10 * RS) & (dist[sl] > 250) & (da[sl] > 60) & (db[sl] > 60)
            if good.mean() > .8:
                boxes.append((sl, good, (xx + 64 - W / 2) / 4000, (yy + 64 - H / 2) / 4000))
    D = design(np.array([b[2] for b in boxes]), np.array([b[3] for b in boxes]))
    Acorr = np.lib.format.open_memmap(CAU34 / 'sony_A_corr_v34.npy', mode='w+', dtype=np.float32, shape=(H, W, 3)); rep = {'channels': {}}
    for c in range(3):
        q = np.array([np.median(np.log(B[sl + (c,)][good] / A[sl + (c,)][good])) for sl, good, _, _ in boxes]); use = np.isfinite(q)
        for _ in range(4):
            coef = np.linalg.lstsq(D[use], q[use], rcond=None)[0]; res = q - D @ coef; mad = max(1.4826 * np.median(np.abs(res[use] - np.median(res[use]))), 1e-5); use = np.isfinite(q) & (np.abs(res) < 4 * mad)
        pred = coef[0] + coef[1] * gx + coef[2] * gy + coef[3] * gx * gx + coef[4] * gx * gy + coef[5] * gy * gy; factor = np.exp(pred).astype(np.float32)
        ratio = np.where(overlap & (dist > 220) & (A[..., c] > 0), np.log(np.maximum(B[..., c], 1e-8) / np.maximum(A[..., c], 1e-8)) - pred, 0).astype(np.float32); ratio = np.nan_to_num(ratio); ok = (overlap & (dist > 220)).astype(np.float32)
        small = (W // 8, H // 8); wr = cv2.resize(ok, small, interpolation=cv2.INTER_AREA); nr = cv2.resize(ratio * ok, small, interpolation=cv2.INTER_AREA)
        low = gauss(nr, 16) / np.maximum(gauss(wr, 16), 1e-6); local = cv2.resize(low, (W, H), interpolation=cv2.INTER_LINEAR); factor *= np.exp(local)
        Acorr[..., c] = np.nan_to_num(A[..., c], nan=0) * factor
        rep['channels'][str(c)] = {'coefficients': coef, 'blocks': len(q), 'used': int(use.sum()), 'factor_p1_p50_p99': np.percentile(factor[ma], [1, 50, 99])}
        log(f'A/B guany canal {c}: factor p1/p50/p99 {rep["channels"][str(c)]["factor_p1_p50_p99"]}')
    Acorr.flush()
    # pesos per variància
    vA = var_map(np.asarray(Acorr[..., 1]), ma); vB = var_map(np.asarray(B[..., 1]), mb)
    gA = smooth(dist, GHOST_IN, GHOST_OUT)
    wA = np.where(ma, gA * smooth(da, 0, EDGE_FEATHER_PX) / np.nan_to_num(vA, nan=np.inf), 0).astype(np.float32)
    wB = np.where(mb, smooth(db, 0, EDGE_FEATHER_PX) / np.nan_to_num(vB, nan=np.inf), 0).astype(np.float32)
    # on només hi ha un apuntament, aquell (sense ploma): les plomes només actuen on tots dos existeixen
    wA = np.where(mb, wA, ma.astype(np.float32)); wB = np.where(ma, wB, mb.astype(np.float32))
    tot = wA + wB; fA = np.where(tot > 0, wA / np.maximum(tot, 1e-30), 0).astype(np.float32)
    fused = np.empty((H, W, 3), np.float32)
    for c in range(3):
        fused[..., c] = fA * np.nan_to_num(Acorr[..., c]) + (1 - fA) * np.nan_to_num(B[..., c])
    # porta contra la Vixen (2,5–5 R☉, on hi ha Vixen i solapament A/B)
    V = np.load(CAU34 / 'vixen_total_v34.npy', mmap_mode='r'); mv = np.load(CAUF / 'vixen_support.npy') & np.all(np.isfinite(V) & (V > 0), axis=2)
    zone = mv & overlap & (r > 2.5 * RS) & (r < 5.0 * RS) & (dist > GHOST_OUT)
    VG = np.asarray(V[..., 1]); gate = {}
    for s in (12, 24):
        gate[f'sigma{s}'] = {'B_sola': corr_with(VG, mv, np.asarray(B[..., 1]), mb, zone, s), 'A+B': corr_with(VG, mv, fused[..., 1], ma | mb, zone, s)}
    fine_B = var_map(np.asarray(B[..., 1]), mb); fine_F = var_map(fused[..., 1], ma | mb)
    gate['gra_fi_rms_pct_zona'] = {'B_sola': float(100 * np.sqrt(np.nanmean(fine_B[zone]))), 'A+B': float(100 * np.sqrt(np.nanmean(fine_F[zone])))}
    accept = all(gate[f'sigma{s}']['A+B'] is not None and gate[f'sigma{s}']['A+B'] >= gate[f'sigma{s}']['B_sola'] - 0.005 for s in (12, 24))
    gate['acceptada_A+B'] = bool(accept); log(f'PORTA A+B: {gate}')
    out = np.lib.format.open_memmap(CAU34 / 'sony_corrected_total_v34.npy', mode='w+', dtype=np.float32, shape=(H, W, 3))
    if accept:
        out[:] = fused; np.save(CAU34 / 'sony_fA_v34.npy', fA)
    else:   # B primària amb A només a la vora, com la V32
        weight = np.asarray(np.load(CAUF / 'sony_A_blend_weight.npy', mmap_mode='r'), np.float32)
        for c in range(3):
            out[..., c] = np.nan_to_num(Acorr[..., c]) * weight + np.nan_to_num(B[..., c]) * (1 - weight)
    out.flush(); del out, fused
    rep.update({'porta': gate, 'variancia': {'sigma_px': VAR_SIGMA_PX, 'banda': 'DoG 1,5/3 px de ln G'}, 'ghost_A_ploma_px': [GHOST_IN, GHOST_OUT], 'ploma_vora_px': EDGE_FEATHER_PX, 'fraccio_A_p50_solapament': float(np.median(fA[overlap]))})
    return rep


def fuse_trains():
    r, t = coords(); mv0 = np.load(CAUF / 'vixen_support.npy'); ms0 = np.load(CAUF / 'sony_support.npy'); m = mv0 | ms0
    V = np.load(CAU34 / 'vixen_total_v34.npy', mmap_mode='r'); S = np.load(CAU34 / 'sony_corrected_total_v34.npy', mmap_mode='r')
    mv = mv0 & np.all(np.isfinite(V) & (V > 0), axis=2); ms = ms0 & np.all(np.isfinite(S) & (S > 0), axis=2)
    wvG = np.load(CAUF / 'vixen_weight_G.npy', mmap_mode='r'); wsG = np.load(CAUF / 'sony_weight_G.npy', mmap_mode='r')
    ds = cv2.distanceTransform(ms.astype(np.uint8), cv2.DIST_L2, 5); dv = cv2.distanceTransform(mv.astype(np.uint8), cv2.DIST_L2, 5)
    good_fit = mv & ms & comu.mascara_dada(np.asarray(wvG), r) & comu.mascara_dada(np.asarray(wsG), r) & (r > 1.5 * RS) & (r < 4.0 * RS)
    y, x = np.ogrid[:H, :W]; good_fit &= np.hypot(x - GHOST_XY[0], y - GHOST_XY[1]) > 240
    rep = {'rho_sigma_px': RHO_SIGMA_PX, 'edge_feather_px': EDGE_FEATHER_PX, 'fit_window_R': [1.5, 4.0], 'pes_vixen': 'max(rampa V32 [1 fins a 2,0; smoothstep 2,0→2,65], fracció per variància)', 'var_sigma_px': VAR_SIGMA_PX, 'channels': {}}
    small = (W // 8, H // 8); rho_all = np.empty((H, W, 3), np.float32)
    for c in range(3):
        v = np.asarray(V[..., c]); s = np.asarray(S[..., c]); gf = good_fit & np.isfinite(v) & np.isfinite(s) & (v > 0) & (s > 0)
        lr = np.where(gf, np.log(np.maximum(v, 1e-9) / np.maximum(s, 1e-9)), 0).astype(np.float32); ok = gf.astype(np.float32)
        nr = cv2.resize(lr * ok, small, interpolation=cv2.INTER_AREA); wr = cv2.resize(ok, small, interpolation=cv2.INTER_AREA); sg = RHO_SIGMA_PX / 8
        num = gauss(nr, sg); den = gauss(wr, sg); low = np.where(den > 0.05, num / np.maximum(den, 1e-9), np.nan); bad = ~np.isfinite(low)
        if bad.any():
            idx = distance_transform_edt(bad, return_distances=False, return_indices=True); low = low[idx[0], idx[1]]
        rho_all[..., c] = np.exp(cv2.resize(low.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)).astype(np.float32)
        sect = (np.floor(np.degrees(np.mod(t, 2 * np.pi)) / 30).astype(int) % 2 == 1) & gf & (r > 2 * RS) & (r < 3.5 * RS); e = 100 * (s[sect] * rho_all[..., c][sect] / v[sect] - 1)
        rep['channels'][str(c)] = {'rho_p1_p50_p99': [float(np.percentile(rho_all[..., c][ms & mv], q)) for q in (1, 50, 99)], 'holdout_median_bias_pct': float(np.median(e)), 'holdout_median_abs_err_pct': float(np.median(np.abs(e)))}
        del v, s, lr, ok
    np.save(CAU34 / 'rho_v34.npy', rho_all)
    # pesos per variància (ln G, a cada tren; la Sony ja escalada per ρ no canvia la variància en ln)
    vV = var_map(np.asarray(V[..., 1]), mv); vS = var_map(np.asarray(S[..., 1]), ms)
    fv_var = np.where(mv & ms, (1 / np.nan_to_num(vV, nan=np.inf)) / np.maximum(1 / np.nan_to_num(vV, nan=np.inf) + 1 / np.nan_to_num(vS, nan=np.inf), 1e-30), np.where(mv, 1.0, 0.0)).astype(np.float32)
    # la Vixen mai no té MENYS pes que a la V32 (Vixen sola fins a 2,0, smoothstep 2,0→2,65): la variància fina confon
    # soroll amb borrositat (la Sony va remostrejada ×1,49) i sola cediria resolució a 2,0–2,6; de 2,65 enfora només AFEGEIX Vixen
    fv_v32 = (1 - smooth(r / RS, 2.0, 2.65)).astype(np.float32)
    fv = np.where(mv, np.maximum(fv_v32, fv_var), 0.0).astype(np.float32)
    edge_s = (1 - smooth(ds, 0, EDGE_FEATHER_PX)) * smooth(dv, 0, EDGE_FEATHER_PX)     # vora del suport Sony: la Vixen agafa el relleu
    fv = np.where(ms, np.maximum(fv, edge_s * mv), mv.astype(np.float32)).astype(np.float32)
    fv = np.where(ms & mv, fv * smooth(dv, 0, EDGE_FEATHER_PX) + (1 - smooth(dv, 0, EDGE_FEATHER_PX)) * 0.0, fv)       # vora del suport Vixen: la Sony agafa el relleu
    fv = np.where(ms, fv, mv.astype(np.float32)); wv = fv; ws = ((1 - wv) * ms).astype(np.float32)
    np.save(CAU34 / 'weight_vixen_v34.npy', wv); np.save(CAU34 / 'var_vixen_v34.npy', vV); np.save(CAU34 / 'var_sony_v34.npy', vS)
    out = np.lib.format.open_memmap(CAU34 / 'fusion_total_v34.npy', mode='w+', dtype=np.float32, shape=(H, W, 3))
    for c in range(3):
        tv = np.where(mv, np.asarray(V[..., c]), 0); ts = np.where(ms, np.asarray(S[..., c]) * rho_all[..., c], 0)
        out[..., c] = (wv * np.nan_to_num(tv) + ws * np.nan_to_num(ts)).astype(np.float32)
    out.flush(); base = np.asarray(out[..., 1]).copy(); base[~m] = 0; np.save(CAU34 / 'base_G_v34.npy', base); np.save(CAU34 / 'support_v34.npy', m)
    prof = []
    for a in (1.5, 1.9, 2.0, 2.1, 2.3, 2.65, 3.0, 4.0, 5.0, 6.0, 8.0):
        k = ms & mv & (r >= a * RS) & (r < (a + 0.2) * RS)
        prof.append({'r': a, 'frac_vixen_p50': float(np.median(wv[k])) if k.sum() > 100 else None, 'sigma_vixen_pct': float(100 * np.sqrt(np.nanmedian(vV[k]))) if k.sum() > 100 else None, 'sigma_sony_pct': float(100 * np.sqrt(np.nanmedian(vS[k]))) if k.sum() > 100 else None})
    rep['perfil_pesos'] = prof; rep['base_G_sha256'] = sha(CAU34 / 'base_G_v34.npy'); log('perfil de pesos: ' + ', '.join(f"{z['r']}R {z['frac_vixen_p50']}" for z in prof if z['frac_vixen_p50'] is not None))
    return rep


def main():
    rep = {'canvis_v34': REP_CANVIS, 'pointings': merge_pointings()}; rep['trains'] = fuse_trains(); savejson(REB34 / 'B3_fusio.json', rep); log('B3 fet')


if __name__ == '__main__':
    main()
