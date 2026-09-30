"""B3 (V36) · Fusió amb les cures de research/151: suports PLENS per a les distàncies, conformació de la Vixen a la
Sony·ρ en baixa freqüència, esvaïments llargs a les vores dels dos camps (Vixen 720 px, A 480 px), relleu entre trens
1,9→3,5 R☉. Apuntaments A/B: com la V34 (guany A→B grau 2 + residu σ128; pesos per variància; porta contra la Vixen).
Sortides: sony_corrected_total_v36, fusion_total_v36 (H,W,3), base_G_v36, support_v36, weight_vixen_v36, rho_v36, delta_v36, var maps."""
from comu38 import *
from scipy.ndimage import distance_transform_edt
RHO_SIGMA_PX = 256.0; EDGE_FEATHER_PX = 160.0; VAR_SIGMA_PX = 48.0
GHOST_IN, GHOST_OUT = 200.0, 320.0


def design(x, y):
    return np.stack([np.ones_like(x), x, y, x * x, x * y, y * y], axis=-1)


def var_map(G, m):
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


def dist_in(mask_filled):
    return cv2.distanceTransform(mask_filled.astype(np.uint8), cv2.DIST_L2, 5)


def merge_pointings():
    A = np.load(CAU36 / 'sony_A_total_v36.npy', mmap_mode='r'); B = np.load(CAU36 / 'sony_B_total_v36.npy', mmap_mode='r')
    pa = np.load(CAUF / 'sony_A_weights.npy', mmap_mode='r'); pb = np.load(CAUF / 'sony_B_weights.npy', mmap_mode='r')
    ma = np.all(np.isfinite(A) & (A > 0) & (pa > 0), axis=2); mb = np.all(np.isfinite(B) & (B > 0) & (pb > 0), axis=2)
    r, t = coords(); y, x = np.ogrid[:H, :W]; gx = (x - W / 2) / 4000; gy = (y - H / 2) / 4000
    db = dist_in(mb | (r < 1.2 * RS)); da = dist_in(ma | (r < 1.2 * RS))       # suports PLENS (sense forat lunar)
    dist = np.hypot(x - GHOST_XY[0], y - GHOST_XY[1]).astype(np.float32)
    overlap = ma & mb; boxes = []
    for yy in range(0, H - 128, 128):
        for xx in range(0, W - 128, 128):
            sl = (slice(yy, yy + 128, 4), slice(xx, xx + 128, 4)); good = overlap[sl] & (r[sl] > 2 * RS) & (r[sl] < 10 * RS) & (dist[sl] > 250) & (da[sl] > 60) & (db[sl] > 60)
            if good.mean() > .8:
                boxes.append((sl, good, (xx + 64 - W / 2) / 4000, (yy + 64 - H / 2) / 4000))
    D = design(np.array([b[2] for b in boxes]), np.array([b[3] for b in boxes]))
    Acorr = np.lib.format.open_memmap(CAU36 / 'sony_A_corr_v36.npy', mode='w+', dtype=np.float32, shape=(H, W, 3)); rep = {'channels': {}}
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
    vA = var_map(np.asarray(Acorr[..., 1]), ma); vB = var_map(np.asarray(B[..., 1]), mb)
    gA = smooth(dist, GHOST_IN, GHOST_OUT)
    # V35: esvaïment LLARG de A a la vora del seu suport (la V34 hi feia un graó de gra del 25 % en 160 px); B igual per simetria
    wA = np.where(ma, gA * smooth(da, 0, TAPER_A_PX) / np.nan_to_num(vA, nan=np.inf), 0).astype(np.float32)
    wB = np.where(mb, smooth(db, 0, TAPER_A_PX) / np.nan_to_num(vB, nan=np.inf), 0).astype(np.float32)
    wA = np.where(mb, wA, ma.astype(np.float32)); wB = np.where(ma, wB, mb.astype(np.float32))
    tot = wA + wB; fA = np.where(tot > 0, wA / np.maximum(tot, 1e-30), 0).astype(np.float32)
    fused = np.empty((H, W, 3), np.float32)
    for c in range(3):
        fused[..., c] = fA * np.nan_to_num(Acorr[..., c]) + (1 - fA) * np.nan_to_num(B[..., c])
    V = np.load(CAU38 / 'vixen_total_v38.npy', mmap_mode='r'); mv = np.load(CAUF / 'vixen_support.npy') & np.all(np.isfinite(V) & (V > 0), axis=2)
    zone = mv & overlap & (r > 2.5 * RS) & (r < 5.0 * RS) & (dist > GHOST_OUT)
    VG = np.asarray(V[..., 1]); gate = {}
    for s in (12, 24):
        gate[f'sigma{s}'] = {'B_sola': corr_with(VG, mv, np.asarray(B[..., 1]), mb, zone, s), 'A+B': corr_with(VG, mv, fused[..., 1], ma | mb, zone, s)}
    fine_B = var_map(np.asarray(B[..., 1]), mb); fine_F = var_map(fused[..., 1], ma | mb)
    gate['gra_fi_rms_pct_zona'] = {'B_sola': float(100 * np.sqrt(np.nanmean(fine_B[zone]))), 'A+B': float(100 * np.sqrt(np.nanmean(fine_F[zone])))}
    accept = all(gate[f'sigma{s}']['A+B'] is not None and gate[f'sigma{s}']['A+B'] >= gate[f'sigma{s}']['B_sola'] - 0.005 for s in (12, 24))
    gate['acceptada_A+B'] = bool(accept); log(f'PORTA A+B: {gate}')
    out = np.lib.format.open_memmap(CAU36 / 'sony_corrected_total_v36.npy', mode='w+', dtype=np.float32, shape=(H, W, 3))
    if accept:
        out[:] = fused; np.save(CAU36 / 'sony_fA_v36.npy', fA)
    else:
        weight = np.asarray(np.load(CAUF / 'sony_A_blend_weight.npy', mmap_mode='r'), np.float32)
        for c in range(3):
            out[..., c] = np.nan_to_num(Acorr[..., c]) * weight + np.nan_to_num(B[..., c]) * (1 - weight)
    out.flush(); del out, fused
    # perfil del pes A contra la distància a la seva vora (zona amb B, r > 2,5)
    sdA = np.where(ma | (r < 1.2 * RS), da, -dist_in(~(ma | (r < 1.2 * RS)))); prof = []
    for b0 in range(-200, 1000, 100):
        k = mb & (r > 2.5 * RS) & (dist > GHOST_OUT) & (sdA >= b0) & (sdA < b0 + 100)
        if k.sum() > 500:
            prof.append({'dist_px': [b0, b0 + 100], 'fA_p50': float(np.median(fA[k]))})
    rep.update({'porta': gate, 'variancia': {'sigma_px': VAR_SIGMA_PX, 'banda': 'DoG 1,5/3 px de ln G'}, 'ghost_A_ploma_px': [GHOST_IN, GHOST_OUT], 'taper_vora_A_px': TAPER_A_PX, 'fraccio_A_p50_solapament': float(np.median(fA[overlap])), 'perfil_fA_vora_A': prof})
    return rep


def fuse_trains():
    r, t = coords(); mv0 = np.load(CAUF / 'vixen_support.npy'); ms0 = np.load(CAUF / 'sony_support.npy'); m = mv0 | ms0
    V = np.load(CAU38 / 'vixen_total_v38.npy', mmap_mode='r'); S = np.load(CAU36 / 'sony_corrected_total_v36.npy', mmap_mode='r')
    mv = mv0 & np.all(np.isfinite(V) & (V > 0), axis=2); ms = ms0 & np.all(np.isfinite(S) & (S > 0), axis=2)
    wvG = np.load(CAUF / 'vixen_weight_G.npy', mmap_mode='r'); wsG = np.load(CAUF / 'sony_weight_G.npy', mmap_mode='r')
    ds = dist_in(ms | (r < 1.6 * RS)); dv = dist_in(mv | (r < 1.6 * RS))          # V35: suports PLENS (trampa del forat lunar de la V34)
    good_fit = mv & ms & comu.mascara_dada(np.asarray(wvG), r) & comu.mascara_dada(np.asarray(wsG), r) & (r > 1.5 * RS) & (r < 4.0 * RS)
    y, x = np.ogrid[:H, :W]; good_fit &= np.hypot(x - GHOST_XY[0], y - GHOST_XY[1]) > 240
    rep = {'rho_sigma_px': RHO_SIGMA_PX, 'edge_feather_px': EDGE_FEATHER_PX, 'fit_window_R': [1.5, 4.0], 'taper_vixen_px': TAPER_VIXEN_PX, 'relleu_R': RELLEU_R, 'delta': {'sigma_px': DELTA_SIGMA_PX, 'ramp_R': DELTA_RAMP_R}, 'var_sigma_px': VAR_SIGMA_PX, 'channels': {}}
    small = (W // 8, H // 8); rho_all = np.empty((H, W, 3), np.float32); both = mv & ms; wboth = both.astype(np.float32)
    delta_all = np.empty((H, W, 3), np.float32); sect_hold = (np.floor(np.degrees(np.mod(t, 2 * np.pi)) / 30).astype(int) % 2 == 1)
    for c in range(3):
        v = np.asarray(V[..., c]); s = np.asarray(S[..., c]); gf = good_fit & np.isfinite(v) & np.isfinite(s) & (v > 0) & (s > 0)
        lr = np.where(gf, np.log(np.maximum(v, 1e-9) / np.maximum(s, 1e-9)), 0).astype(np.float32); ok = gf.astype(np.float32)
        nr = cv2.resize(lr * ok, small, interpolation=cv2.INTER_AREA); wr = cv2.resize(ok, small, interpolation=cv2.INTER_AREA); sg = RHO_SIGMA_PX / 8
        num = gauss(nr, sg); den = gauss(wr, sg); low = np.where(den > 0.05, num / np.maximum(den, 1e-9), np.nan); bad = ~np.isfinite(low)
        if bad.any():
            idx = distance_transform_edt(bad, return_distances=False, return_indices=True); low = low[idx[0], idx[1]]
        rho_all[..., c] = np.exp(cv2.resize(low.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)).astype(np.float32)
        sect = sect_hold & gf & (r > 2 * RS) & (r < 3.5 * RS); e = 100 * (s[sect] * rho_all[..., c][sect] / v[sect] - 1)
        # V35: δ_c = ⟨ln(V/(S·ρ))⟩ σ256 a TOT el solapament (ajust amb sectors senars reservats per al holdout), entrada smoothstep DELTA_RAMP_R
        d = np.where(both, np.log(np.maximum(v, 1e-9) / np.maximum(s * rho_all[..., c], 1e-9)), 0).astype(np.float32)
        fitm = (both & ~sect_hold).astype(np.float32)
        nr2 = cv2.resize(d * fitm, small, interpolation=cv2.INTER_AREA); wr2 = cv2.resize(fitm, small, interpolation=cv2.INTER_AREA); sg2 = DELTA_SIGMA_PX / 8
        low2 = np.where(gauss(wr2, sg2) > 0.02, gauss(nr2, sg2) / np.maximum(gauss(wr2, sg2), 1e-9), np.nan); bad2 = ~np.isfinite(low2)
        if bad2.any():
            idx = distance_transform_edt(bad2, return_distances=False, return_indices=True); low2 = low2[idx[0], idx[1]]
        dl = cv2.resize(low2.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR) * smooth(r / RS, *DELTA_RAMP_R)
        delta_all[..., c] = dl.astype(np.float32)
        hold = both & sect_hold & (r > 2.65 * RS); e2 = 100 * (d[hold] - dl[hold]); e2b = 100 * d[hold]
        rep['channels'][str(c)] = {'rho_p1_p50_p99': [float(np.percentile(rho_all[..., c][ms & mv], q)) for q in (1, 50, 99)], 'holdout_rho_median_bias_pct': float(np.median(e)), 'holdout_rho_median_abs_err_pct': float(np.median(np.abs(e))),
                                   'delta_p1_p50_p99_pct': [float(100 * np.percentile(dl[both], q)) for q in (1, 50, 99)], 'holdout_delta_abans_median_abs_pct': float(np.median(np.abs(e2b))), 'holdout_delta_despres_median_abs_pct': float(np.median(np.abs(e2))), 'holdout_delta_despres_p90_abs_pct': float(np.percentile(np.abs(e2), 90))}
        log(f"canal {c}: ρ holdout |err| {rep['channels'][str(c)]['holdout_rho_median_abs_err_pct']:.2f} % · δ p1/p50/p99 {rep['channels'][str(c)]['delta_p1_p50_p99_pct']} · holdout |ln V/Sρ| {rep['channels'][str(c)]['holdout_delta_abans_median_abs_pct']:.2f} → {rep['channels'][str(c)]['holdout_delta_despres_median_abs_pct']:.2f} %")
        del v, s, lr, ok, d
    np.save(CAU38 / 'rho_v38.npy', rho_all); np.save(CAU38 / 'delta_v38.npy', delta_all)
    vV = var_map(np.asarray(V[..., 1]), mv); vS = var_map(np.asarray(S[..., 1]), ms)
    fv_var = np.where(mv & ms, (1 / np.nan_to_num(vV, nan=np.inf)) / np.maximum(1 / np.nan_to_num(vV, nan=np.inf) + 1 / np.nan_to_num(vS, nan=np.inf), 1e-30), np.where(mv, 1.0, 0.0)).astype(np.float32)
    fv_ramp = (1 - smooth(r / RS, *RELLEU_R)).astype(np.float32)                 # V35: relleu 1,9→3,5 (V34: 2,0→2,65)
    fv = np.where(mv, np.maximum(fv_ramp, fv_var), 0.0).astype(np.float32)
    edge_s = (1 - smooth(ds, 0, EDGE_FEATHER_PX)) * smooth(dv, 0, EDGE_FEATHER_PX)   # vora del suport Sony: la Vixen agafa el relleu
    fv = np.where(ms, np.maximum(fv, edge_s * mv), mv.astype(np.float32)).astype(np.float32)
    fv = np.where(ms & mv, fv * smooth(dv, 0, TAPER_VIXEN_PX), fv)                    # V35: vora del suport Vixen (PLE): esvaïment de 720 px
    fv = np.where(ms, fv, mv.astype(np.float32)); wv = fv; ws = ((1 - wv) * ms).astype(np.float32)
    np.save(CAU38 / 'weight_vixen_v38.npy', wv); np.save(CAU38 / 'var_vixen_v38.npy', vV); np.save(CAU38 / 'var_sony_v38.npy', vS)
    out = np.lib.format.open_memmap(CAU38 / 'fusion_total_v38.npy', mode='w+', dtype=np.float32, shape=(H, W, 3))
    for c in range(3):
        tv = np.where(mv, np.asarray(V[..., c]) * np.exp(-delta_all[..., c]), 0); ts = np.where(ms, np.asarray(S[..., c]) * rho_all[..., c], 0)
        out[..., c] = (wv * np.nan_to_num(tv) + ws * np.nan_to_num(ts)).astype(np.float32)
    out.flush(); base = np.asarray(out[..., 1]).copy(); base[~m] = 0; np.save(CAU38 / 'base_G_v38.npy', base); np.save(CAU38 / 'support_v38.npy', m)
    prof = []
    for a in (1.0, 1.1, 1.2, 1.3, 1.5, 1.9, 2.0, 2.2, 2.4, 2.65, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0):
        k = ms & mv & (r >= a * RS) & (r < (a + 0.1) * RS)
        prof.append({'r': a, 'frac_vixen_p05': float(np.percentile(wv[k], 5)) if k.sum() > 100 else None, 'frac_vixen_p50': float(np.median(wv[k])) if k.sum() > 100 else None, 'sigma_vixen_pct': float(100 * np.sqrt(np.nanmedian(vV[k]))) if k.sum() > 100 else None, 'sigma_sony_pct': float(100 * np.sqrt(np.nanmedian(vS[k]))) if k.sum() > 100 else None})
    sdv = np.where(mv | (r < 1.6 * RS), dv, -dist_in(~(mv | (r < 1.6 * RS)))); pv = []
    for b0 in range(-300, 1300, 100):
        k = ms & (r > 4 * RS) & (sdv >= b0) & (sdv < b0 + 100)
        if k.sum() > 500:
            pv.append({'dist_px': [b0, b0 + 100], 'wv_p50': float(np.median(wv[k]))})
    rep['perfil_pesos'] = prof; rep['perfil_wv_vora_vixen'] = pv; rep['base_G_sha256'] = sha(CAU38 / 'base_G_v38.npy')
    log('perfil de pesos: ' + ', '.join(f"{z['r']}R {z['frac_vixen_p50']:.2f}" for z in prof if z['frac_vixen_p50'] is not None)); log('vora Vixen: ' + ', '.join(f"{z['dist_px'][0]}:{z['wv_p50']:.2f}" for z in pv))
    return rep


def main():
    rep = {'canvis_v36': REP_CANVIS, 'v38': 'Vixen recomposta amb la correcció de la vora lunar per fotograma (B2 V38); Sony A/B corregides de la V36 reutilitzades (no entren a < 1,9 R☉)', 'pointings': 'reutilitzat de la V36 (CAU36/sony_corrected_total_v36.npy)'}; rep['trains'] = fuse_trains(); savejson(REB38 / 'B3_fusio.json', rep); log('B3 fet')


if __name__ == '__main__':
    main()
