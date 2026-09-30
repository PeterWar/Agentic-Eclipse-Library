"""F2c (V43) · DISC PLA + RELLEU amb el LIMBE NET (la manera de Brno): el glow dins del disc és l'ala de la PSF (seeing amb el Sol a 9° + òptica) de la cromosfera/corona de
just fora del limbe (F2b: IGUAL als dos trens: 2,5–2,9 % de la corona a 0,99 R, 14–16 % a 0,995 R → no és la lent, és el limbe vist a través de l'atmosfera). Es modela i es
resta com a VEL (research/127) fins a 0,995 R —a la vora depèn de l'azimut: on fora hi ha la cromosfera (100× més brillant) l'ala és més alta— i es substitueix per un NIVELL
PLA declarat (com la F1 feia només fins a 0,85 R): vel2(r,φ) = vel radial+polinomi (F2) a r ≤ 0,85 R, mediana per anell d'1 px i SECTOR de ±10° de 0,92 R enfora (fosa 0,85→0,92).
Residu = E − vel2 (earthshine + gra); relleu ρ = residu/vel2 (σ 3 px), NOMÉS a r ≤ 0,85 R i esvaït a 0 fins a 0,95 R (regla de la F1: a 0,85–0,97 R el residu × LROC no supera el nul); de 0,95 a 0,995 R el disc és pla. Capa: r < 0,995 R → pla × color × (1 + Kρ);
de r_limbe(φ) − 1 px a r_limbe(φ) → fosa a la dada mesurada (r_limbe(φ) = el 50 % de la rampa, mesurat azimut a azimut, no el cercle nominal: a l'est, a la cromosfera, cau 2–3 px més enfora); enfora → dada mesurada (corona de l'instant declarat). Dues alçades del
pla: FOSC (×0,3 el vel interior → sRGB ≈ 0,16, com el disc de Brno 0,14) i POWAAAH3 (×2,45 → 0,37). K per contrast sRGB 12 % a r < 0,85 R. Cap píxel pintat: el pla és
un nivell i un color constants declarats en lloc del vel mesurat; el relleu i la vora són dada. Sortides: cau/e43_pla_{fosc,powaaah3}_relleu12_u16.npy, REB43/F2c_disc_pla.json."""
from comu43 import *
from scipy.ndimage import gaussian_filter, gaussian_filter1d
MC = (CX + 14.8, CY + 0.9); WIN = 700; RL = 453.5; PEND, ANC, TERRA = 0.22, 0.74, 0.045; VA = 70736.46875; REB42_ = ROOT / 'output/v42_20260910/4-rebuts'; CAU42_ = HERE42 / 'cau'


def main():
    x0, y0 = int(round(MC[0])) - WIN, int(round(MC[1])) - WIN; yy, xx = np.mgrid[0:2 * WIN, 0:2 * WIN].astype(np.float32); cxt, cyt = MC[0] - x0, MC[1] - y0; r = np.hypot(xx - cxt, yy - cyt); phi = np.degrees(np.arctan2(yy - cyt, xx - cxt)) % 360
    inn = r < 0.85 * RL; E = np.load(CAU43 / 'e43_lineal_tessella.npy'); vel1 = np.load(CAU43 / 'e43_vel.npy'); G = E[..., 1]; okG = np.isfinite(G); E0 = np.nan_to_num(E); okE = okG & (r < RL + 40)
    # vel per sector: mediana d'1 px en r × ±10° en azimut (36 centres cada 10°, interpolació lineal en φ), de 0,80 R a R+40
    r0 = int(0.80 * RL); NBR = int(RL + 40) - r0 + 1; rb = np.floor(r).astype(int) - r0; cents = np.arange(0, 360, 10); tab = np.full((len(cents), NBR), np.nan, np.float32)
    for i, c in enumerate(cents):
        dphi = np.abs(((phi - c + 180) % 360) - 180); sec = okG & (dphi <= 10) & (rb >= 0) & (rb < NBR)
        for k in range(NBR):
            sel = sec & (rb == k)
            if sel.sum() >= 6: tab[i, k] = np.median(G[sel])
    for i in range(len(cents)):
        good = np.isfinite(tab[i]); tab[i] = np.interp(np.arange(NBR), np.where(good)[0], tab[i][good]) if good.sum() > 2 else np.nanmedian(tab, axis=0)
    tab = np.exp(gaussian_filter1d(np.log(np.maximum(tab, 1e-3)), 1.0, axis=1))   # suau en r (1 px) en LOG: el perfil puja ×5 en 2 px a la vora i suavitzar-lo en lineal l'inflava ×2
    ip = phi / 10.0; i0 = np.floor(ip).astype(int) % len(cents); i1 = (i0 + 1) % len(cents); f = (ip - np.floor(ip)).astype(np.float32); rk = np.clip(r - r0, 0, NBR - 1.001); k0 = np.floor(rk).astype(int); g = (rk - k0).astype(np.float32); k1 = np.minimum(k0 + 1, NBR - 1)
    def samp(i): return tab[i, k0] * (1 - g) + tab[i, k1] * g
    vel_sec = (samp(i0) * (1 - f) + samp(i1) * f).astype(np.float32)
    s = np.clip((r - 0.85 * RL) / (0.07 * RL), 0, 1); s = s * s * (3 - 2 * s); vel2 = np.where(r < 0.80 * RL, vel1, (1 - s) * vel1 + s * vel_sec).astype(np.float32)
    R2 = np.where(okG, G - vel2, 0).astype(np.float32); okf = okG.astype(np.float32)
    # relleu NOMÉS a r ≤ 0,85 R, fos a 0 fins a 0,95 R (regla de la F1/research/127: el jutge LROC a 0,85–0,97 R no supera el nul)
    tap = 1 - np.clip((r - 0.85 * RL) / (0.10 * RL), 0, 1); tap = tap * tap * (3 - 2 * tap); rho = (np.where(okG, R2 / np.maximum(vel2, 1e-9), 0) * tap).astype(np.float32); rho_s = gaussian_filter(rho, 3) / np.maximum(gaussian_filter(okf, 3), 1e-6)
    # jutge del residu nou (com la F2) a r < 0,85 R i a l'anell 0,85–0,97 R (on el vel nou és per sector)
    lr = np.load(CAU42_ / 'lroc_capa_v39_rgba.npy'); lb = json.loads((REB42_ / 'P2b_rotacio.json').read_text())['lroc_bbox']; L = np.zeros((2 * WIN, 2 * WIN), np.float32); oy, ox = lb[1] - y0, lb[0] - x0; L[oy:oy + lr.shape[0], ox:ox + lr.shape[1]] = lr[..., :3].mean(-1)
    def pear(a, b, m): u = a[m] - a[m].mean(); v = b[m] - b[m].mean(); return float((u * v).sum() / np.sqrt((u * u).sum() * (v * v).sum() + 1e-12))
    lnL = np.log(np.maximum(L, 1e-3)); rep = {'vel2': 'radial+poly (F2) a r ≤ 0,85 R; mediana per anell d\'1 px i sector ±10° de 0,92 R enfora; fosa 0,85–0,92', 'jutge_lroc': {}}
    for zona, m in (('interior_0.85', inn), ('anell_0.85_0.97', (r >= 0.85 * RL) & (r < 0.97 * RL))):
        hpR = np.where(okG & (r < 0.97 * RL), gaussian_filter(R2, 2) - gaussian_filter(R2, 12), 0); hpL = np.where(r < 0.97 * RL, gaussian_filter(lnL, 2) - gaussian_filter(lnL, 12), 0); mm = m & okG
        rl = pear(hpR, hpL, mm); nul = [pear(hpR, np.rot90(hpL, k_), mm & np.rot90(mm, k_)) for k_ in (1, 2, 3)]; rep['jutge_lroc'][zona] = {'r': rl, 'nuls_90_180_270': nul}; log(f'residu (vel per sector) × LROC {zona}: r {rl:+.3f} · nuls {max(map(abs, nul)):.3f}')
    prof = {}
    for a_, b_ in ((0.5, 0.51), (0.85, 0.86), (0.95, 0.955), (0.975, 0.98), (0.99, 0.995), (0.995, 1.0)):
        m = okG & (r >= a_ * RL) & (r < b_ * RL); prof[f'{a_:.3f}R'] = {'G': float(np.median(G[m])), 'vel2': float(np.median(vel2[m])), 'residu_rms': float(np.std(R2[m]))}
    rep['perfil'] = prof; log('vel2 vs G: ' + ' · '.join(f"{k} G {v['G']:.0f} vel2 {v['vel2']:.0f} rms {v['residu_rms']:.0f}" for k, v in prof.items()))
    # capes
    def to_srgb(rgb, m):
        Lum = (rgb[..., 0] + 2 * rgb[..., 1] + rgb[..., 2]) / 4; tone = comu.corba_to(np.nan_to_num(Lum), m, VA, pend=PEND, anc=ANC, terra=TERRA); ylin = comu.a_lineal(tone)
        q = rgb / np.maximum(Lum, 1e-9)[..., None]; q = np.nan_to_num(q, nan=1.0); qmax = q.max(axis=2)
        with np.errstate(divide='ignore', invalid='ignore'): wmax = np.where(qmax > 1, (1 / np.maximum(ylin, 1e-8) - 1) / (qmax - 1), 1)
        wg = np.clip(np.nan_to_num(wmax, nan=0, posinf=1), 0, 1); return np.clip(np.nan_to_num(comu.a_srgb(ylin[..., None] * (1 + wg[..., None] * (q - 1)))), 0, 1) * m[..., None]
    med = np.array([float(np.median(E0[..., c][inn])) for c in range(3)], np.float32); Lm = float((med[0] + 2 * med[1] + med[2]) / 4); col = med / Lm
    def srgb_gris(x): a = np.full((8, 8, 3), x, np.float32); return float(to_srgb(a, np.ones((8, 8), bool))[4, 4, 1])
    try: TG = json.loads((REB42_ / 'F1b_mota_i_contrast.json').read_text())['powaaah3']['medianes'][1]
    except Exception: TG = 0.364
    lo, hi = np.log10(Lm) - 3, np.log10(Lm) + 3
    for _ in range(50):
        mid = 0.5 * (lo + hi); lo, hi = (mid, hi) if srgb_gris(10 ** mid) < TG else (lo, mid)
    lv_pow = 10 ** (0.5 * (lo + hi))
    # LIMBE PER AZIMUT (10-09, vespre; marca verda de Pere): la vora fotogràfica de l'apilat NO és el cercle nominal (R 453,5 al centre d'efemèride): va a (−1,6, −0,3) px i, on fora hi ha
    # la cromosfera, el 50 % de la rampa cau 2–3 px més enfora (est: 456 px; nord: 452). Amb la vora al cercle nominal quedava una franja de rampa entre el disc pla i la cromosfera.
    # Cura: r_limbe(φ) = radi on G creua el 50 % (aritmètic) entre el disc (0,90–0,97 R) i la corona (1,02–1,04 R) a cada azimut (720), suavitzat ±3° (mediana circular), acotat a ±5 px;
    # el disc pla arriba a r_limbe(φ) − 1 px i s'hi fon a la dada en 1 px; enfora, la dada. (Primer intent amb la mitjana geomètrica: la vora queia 1–3 px massa endins i deixava la rampa vista: refusat per la mesura F3.)
    NAZ = 720; th = np.radians(np.arange(NAZ) * 360.0 / NAZ); rr = np.arange(0.96 * RL, 1.04 * RL, 0.25); rl = np.full(NAZ, np.nan)
    for i, t in enumerate(th):
        xs = cxt + rr * np.cos(t); ys = cyt + rr * np.sin(t); xi = np.clip(np.round(xs).astype(int), 0, 2 * WIN - 1); yi = np.clip(np.round(ys).astype(int), 0, 2 * WIN - 1); g = np.nan_to_num(G[yi, xi], nan=0)
        din = np.median(g[(rr >= 0.90 * RL) & (rr < 0.97 * RL)]) if ((rr >= 0.90 * RL) & (rr < 0.97 * RL)).any() else np.nan
        d2 = (np.hypot(xx - cxt, yy - cyt)); sec = (np.abs(((phi - np.degrees(t) + 180) % 360) - 180) <= 1.0)
        din = np.median(G[okG & sec & (r >= 0.90 * RL) & (r < 0.97 * RL)]); fora = np.median(G[okG & sec & (r >= 1.02 * RL) & (r < 1.04 * RL)])
        if not (np.isfinite(din) and np.isfinite(fora)) or fora < 3 * max(din, 1e-6): continue
        mid = 0.5 * (din + fora); gs = g; idx = np.where((gs[:-1] < mid) & (gs[1:] >= mid))[0]   # 50 % ARITMÈTIC: la vora visual; per sota del 50 % és l'ala de la PSF dins del disc (vel), per sobre la cromosfera/corona
        if len(idx) == 0: continue
        k = idx[-1]; f = (mid - gs[k]) / max(gs[k + 1] - gs[k], 1e-9); rl[i] = rr[k] + f * (rr[1] - rr[0])
    good = np.isfinite(rl); rl = np.interp(np.arange(NAZ), np.where(good)[0], rl[good], period=NAZ) if good.sum() > NAZ // 4 else np.full(NAZ, RL)
    from scipy.ndimage import median_filter, gaussian_filter1d as gf1
    rl = median_filter(rl, size=7, mode='wrap'); rl = gf1(rl, 2.0, mode='wrap'); rl = np.clip(rl, RL - 5, RL + 5)
    rep['limbe_per_azimut'] = {'n_azimuts_mesurats': int(good.sum()), 'mediana_px': float(np.median(rl)), 'min_px': float(rl.min()), 'max_px': float(rl.max()), 'per_sector_45': {int(k): float(np.median(rl[(np.degrees(th) >= k) & (np.degrees(th) < k + 45)])) for k in range(0, 360, 45)}}
    log(f"limbe per azimut: {good.sum()} azimuts · mediana {np.median(rl):.2f} px · mín {rl.min():.2f} · màx {rl.max():.2f} · per sector de 45° (az 180 = est): " + ' · '.join(f"{k}: {v:.1f}" for k, v in rep['limbe_per_azimut']['per_sector_45'].items()))
    rlim = np.interp(phi, np.degrees(th), rl, period=360.0).astype(np.float32); edge = np.clip((r - (rlim - 1.0)) / 1.0, 0, 1)   # 0 fins a r_limbe(φ) − 1 px, 1 al limbe mesurat (50 %): la meitat interior de la rampa de la PSF és vel i s'aplana
    np.save(CAU43 / 'e43_limbe_per_azimut.npy', rl)
    def contrast_srgb(img): gg = img[..., 1][inn]; p5, p95 = np.percentile(gg, [5, 95]); return float((p95 - p5) / np.median(gg))
    def capa(lv, K):
        pla = (lv * col)[None, None, :] * (1 + K * rho_s)[..., None]; out = np.where(okE[..., None], (1 - edge[..., None]) * pla + edge[..., None] * E0, 0); out = np.where((r >= rlim)[..., None], E0, out); return to_srgb(out, okE)
    rep['capes'] = {'color_relatiu_R_G_B': [float(c) for c in col], 'vel_interior_mediana': Lm}
    for nomv, lv in (('pla_fosc_relleu12', 0.30 * Lm), ('pla_powaaah3_relleu12', lv_pow)):
        a, b = 0.0, 400.0
        for _ in range(22):
            K = 0.5 * (a + b); a, b = (K, b) if contrast_srgb(capa(lv, K)) < 0.12 else (a, K)
        K = 0.5 * (a + b); im = capa(lv, K); rep['capes'][nomv] = {'nivell_lineal': lv, 'factor_sobre_vel': lv / Lm, 'K': K, 'contrast_srgb': contrast_srgb(im), 'nivell_srgb_G_interior': float(np.median(im[..., 1][inn])), 'srgb_G_0.99R': float(np.median(im[..., 1][(r > 0.985 * RL) & (r < 0.995 * RL)]))}
        full = np.zeros((H, W, 3), np.uint16); full[y0:y0 + 2 * WIN, x0:x0 + 2 * WIN] = np.round(im * 65535).astype(np.uint16); np.save(CAU43 / f'e43_{nomv}_u16.npy', full); del full
        log(f"capa {nomv}: nivell ×{lv / Lm:.2f} el vel · K {K:.1f} · contrast 12 % · sRGB G interior {rep['capes'][nomv]['nivell_srgb_G_interior']:.3f}, a 0,99 R {rep['capes'][nomv]['srgb_G_0.99R']:.3f}")
        if nomv == 'pla_fosc_relleu12': im_fosc = im
    np.save(CAU43 / 'e43_vel2.npy', vel2); np.save(CAU43 / 'e43_residu2.npy', R2); savejson(REB43 / 'F2c_disc_pla.json', rep)
    # vistes: retalls del limbe ×4 (HDR lineal | pla fosc | pla POWAAAH3) a est/oest/nord + residu nou
    def rgb8(im): return (np.clip(im, 0, 1) * 255).astype(np.uint8)
    lin = np.load(CAU43 / 'e43_lineal_u16.npy', mmap_mode='r')[y0:y0 + 2 * WIN, x0:x0 + 2 * WIN].astype(np.float32) / 65535; pw2 = np.load(CAU43 / 'e43_pla_powaaah3_relleu12_u16.npy', mmap_mode='r')[y0:y0 + 2 * WIN, x0:x0 + 2 * WIN].astype(np.float32) / 65535
    for nomz, (xa, ya) in (('est', (int(cxt - RL), int(cyt))), ('oest', (int(cxt + RL), int(cyt))), ('nord', (int(cxt), int(cyt - RL)))):
        sl = (slice(ya - 60, ya + 60), slice(xa - 60, xa + 60)); row = [cv2.resize(rgb8(im)[sl], (480, 480), interpolation=cv2.INTER_NEAREST) for im in (lin, im_fosc, pw2)]
        cv2.imwrite(str(VIS43 / f'F2c_limbe_{nomz}_x4.png'), cv2.cvtColor(np.concatenate(row, 1), cv2.COLOR_RGB2BGR))
    sd = float(np.std(R2[inn & okG])); can = np.concatenate([cv2.cvtColor((np.clip((np.nan_to_num(R2) + 3 * sd) / (6 * sd), 0, 1) * 255).astype(np.uint8), cv2.COLOR_GRAY2RGB), rgb8(im_fosc), rgb8(pw2)], 1); cv2.imwrite(str(VIS43 / 'F2c_disc_pla_1a1.png'), cv2.cvtColor(can, cv2.COLOR_RGB2BGR))
    log(f'vistes a {VIS43}')


if __name__ == '__main__':
    main()
