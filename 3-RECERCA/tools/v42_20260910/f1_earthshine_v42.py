"""F1 (V42/V43) · APILAT NOU D'EARTHSHINE a partir de les 8 tessel·les registrades sobre la Lluna amb la geometria viva (b2_lluna_v42: Sony DSC06987/06993 8 s,
DSC06984/06996/06999 2 s; Vixen 572A2982/83/84 10 s), sense la guarda de 8 px al limbe.
 1. Guany Sony→Vixen per canal (medianes a r < 0,8 R): tot en unitats Vixen.
 2. Registre entre tessel·les MESURAT als mars: correlació de fase del disc interior (r < 0,85 R) passa-alt (ln, σ 3–12) de cada tessel·la contra la mitjana Vixen;
    s'aplica el desplaçament (enter) si |d| > 0,7 px i la resposta és clara; s'anota tot.
 3. Pesos per variància inversa MESURADA: σ² de cada classe (Vixen 10 s: diferències entre les tres; Sony 8 s: 06987−06993; Sony 2 s: 06996−06999) al disc interior
    passa-alt, en unitats Vixen; w_i = validesa_i / σ²_classe. Cobertura per UNIÓ (no intersecció): on falta un fotograma, els altres hi són amb el seu pes.
 4. Vel de corona dins del disc: perfil radial (mediana per anell fins a 0,975 R: el vel SEGUEIX el glow del limbe; amb 0,85 R el relleu amplificava el glow en un anell de 60 px)
    + polinomi 2D de grau 4 al residu ajustat a r ≤ 0,85 R (com la V4) i avaluat fins a 0,975 R.
 5. Jutge: correlació del residu passa-alt amb la capa LROC de la V39 (r < 0,85 R), amb nul per girs de 90/180/270°.
 5b. Exclusió DECLARADA de l'apuntament B de la Sony (DSC06993/06996/06999): un FANTASMA de +30 % (16 σ) dins del disc a 230 px del centre, present als tres
    fotogrames B i a cap A ni Vixen (F1c), i un vel residual amb σ 4–5× (research/126: 40 comptes). Pesaven el 2,4 %; el jutge LROC no hi perd.
 6. Capes (u16 RGB al llenç sencer, màscara 1 fins al limbe mesurat R 453,5 i 0 a la vora del forat de la base R 457,5):
    · `Earthshine V42 lineal (corba)`: E_lin (vel inclòs) per la corba de to de la base (declarat: el disc tal com el van veure els sensors, gra inclòs);
    · `Earthshine V42 relleu`: disc pla al NIVELL de la POWAAAH3 (mediana sRGB del seu disc, F1b; factor declarat) amb el COLOR mesurat (medianes per canal del vel)
      i el relleu relatiu (E − vel)/vel amplificat per K, amb K triat perquè el contrast p5–p95/mediana en sRGB sigui el de la POWAAAH3 (12 %) o el doble (24 %);
      variants: gra tal qual (sense suavitzar) i residu suavitzat σ 3 px (declarat). El relleu és NOMÉS a r ≤ 0,85 R (zona de ciència del model de vel, research/127),
      fos a 0 fins a 0,95 R (més enllà el vel és el glow asimètric i el model el converteix en anells o mitges llunes); la franja 0,975–1,0 R passa a la dada lineal (glow).
      Cap píxel dibuixat: tot surt de les tessel·les A + Vixen; nivell i amplificació DECLARATS.
Sortides: cau/earthshine_v42_{lineal,relleu12_gra,relleu12_suau,relleu24_suau}_u16.npy, cau/earthshine_v42_mascara_u16.npy, REB42/F1_earthshine.json, vistes 1:1 del disc."""
from comu42 import *
from scipy.ndimage import gaussian_filter, shift as ndshift
MC = (CX + 14.8, CY + 0.9); WIN = 700; RL = 453.5; EXCL_B = ('DSC06993', 'DSC06996', 'DSC06999'); CONTRASTS = {'relleu12_gra': (0.12, 0), 'relleu12_suau': (0.12, 3), 'relleu24_suau': (0.24, 3)}; VA = 70736.46875; PEND, ANC, TERRA = 0.22, 0.74, 0.045
FR = [('sony', 'DSC06987', 8.0, 'S8'), ('sony', 'DSC06993', 8.0, 'S8'), ('sony', 'DSC06984', 2.0, 'S2'), ('sony', 'DSC06996', 2.0, 'S2'), ('sony', 'DSC06999', 2.0, 'S2'), ('vixen', '572A2982', 10.0, 'V10'), ('vixen', '572A2983', 10.0, 'V10'), ('vixen', '572A2984', 10.0, 'V10')]


def hp(z, m, s1=3, s2=12):
    z = np.where(m, np.log(np.maximum(z, 1e-3)), 0); w = m.astype(np.float32); a = gaussian_filter(z * w, s1) / np.maximum(gaussian_filter(w, s1), 1e-6); b = gaussian_filter(z * w, s2) / np.maximum(gaussian_filter(w, s2), 1e-6); return np.where(m, a - b, 0)


def fase(a, b, m):
    A = np.where(m, a - a[m].mean(), 0).astype(np.float32); B_ = np.where(m, b - b[m].mean(), 0).astype(np.float32); (dx, dy), resp = cv2.phaseCorrelate(A, B_); return float(dx), float(dy), float(resp)


def main():
    x0, y0 = int(round(MC[0])) - WIN, int(round(MC[1])) - WIN; yy, xx = np.mgrid[0:2 * WIN, 0:2 * WIN].astype(np.float32); cxt, cyt = MC[0] - x0, MC[1] - y0; r = np.hypot(xx - cxt, yy - cyt); inn = r < 0.85 * RL; disc = r < 0.975 * RL
    T = {}; P = {}
    for tag, stem, t, cls in FR:
        a = np.load(CAU42 / f'lluna_{tag}_{stem}_v42.npy'); p = np.load(CAU42 / f'lluna_{tag}_{stem}_v42_pes.npy'); ok = np.all(np.isfinite(a), axis=2) & (p > 0); a = np.where(ok[..., None], a, np.nan); T[stem] = a; P[stem] = p * ok
    rep = {'finestra': [x0, y0, 2 * WIN, 2 * WIN], 'centre_lluna_llenc': list(MC), 'RL_px': RL}
    # 1. guany Sony→Vixen per canal
    Vm = np.nanmean(np.stack([T[s] for _, s, _, c in FR if c == 'V10']), axis=0); g = {}
    for tag, stem, t, cls in FR:
        if tag == 'sony':
            gg = [float(np.nanmedian(Vm[..., c][inn]) / np.nanmedian(T[stem][..., c][inn])) for c in range(3)]; g[stem] = gg; T[stem] = T[stem] * np.array(gg, np.float32)
    rep['guany_vixen_sobre_sony'] = g; log('guany Vixen/Sony per canal: ' + ' · '.join(f"{k}: {v[0]:.3f}/{v[1]:.3f}/{v[2]:.3f}" for k, v in g.items()))
    # 2. registre als mars contra la mitjana Vixen (ln passa-alt del G)
    ref = hp(np.nan_to_num(Vm[..., 1], nan=np.nanmedian(Vm[..., 1])), inn); regs = {}
    for tag, stem, t, cls in FR:
        okm = inn & np.isfinite(T[stem][..., 1]); z = hp(np.nan_to_num(T[stem][..., 1], nan=np.nanmedian(T[stem][..., 1])), okm); dx, dy, resp = fase(z, ref, okm); regs[stem] = dict(dx=dx, dy=dy, resp=resp, aplicat=[0, 0])
        if np.hypot(dx, dy) > 0.7 and resp > 0.08:
            sx, sy = int(round(-dx)), int(round(-dy)); regs[stem]['aplicat'] = [sx, sy]
            for c in range(3): T[stem][..., c] = ndshift(np.nan_to_num(T[stem][..., c], nan=0), (sy, sx), order=1, cval=0)
            P[stem] = ndshift(P[stem], (sy, sx), order=1, cval=0); T[stem] = np.where((P[stem] > 0)[..., None], T[stem], np.nan)
        log(f"registre {stem}: ({dx:+.2f}, {dy:+.2f}) px resp {resp:.3f} → aplicat {regs[stem]['aplicat']}")
    rep['registre_vs_mitjana_vixen'] = regs
    # 3. pesos per variància inversa MESURADA amb l'estimador del walking noise (research/127 §8): soroll² = potència total de banda − senyal², amb el senyal
    #    per la covariància ENTRE SENSORS (Vixen mitjana × Sony 8 s mitjana: sorolls independents; els parells entre germans cancel·len el patró fix i el subestimen)
    def hpm(a): m = inn & np.isfinite(a); return hp(np.nan_to_num(a, nan=np.nanmedian(a)), m), m
    Vh, mV = hpm(Vm[..., 1]); S8m = np.nanmean(np.stack([T['DSC06987'][..., 1], T['DSC06993'][..., 1]]), axis=0); Sh, mS = hpm(S8m); mm = mV & mS
    senyal2 = float(np.mean((Vh[mm] - Vh[mm].mean()) * (Sh[mm] - Sh[mm].mean()))); var = {}; var_tot = {}
    for tag, stem, t, cls in FR:
        z, m = hpm(T[stem][..., 1]); vt = float(np.var(z[m])); var_tot[stem] = vt; var[stem] = max(vt - senyal2, 0.1 * vt)
    rep['senyal2_ln_hp'] = senyal2; rep['variancia_total_per_fotograma'] = var_tot; rep['variancia_soroll_per_fotograma'] = var
    log(f'senyal² (cov Vixen×Sony8, ln passa-alt) {senyal2:.2e} · σ soroll per fotograma: ' + ' · '.join(f'{k} {np.sqrt(v):.4f}' for k, v in var.items()))
    num = np.zeros((2 * WIN, 2 * WIN, 3), np.float32); den = np.zeros((2 * WIN, 2 * WIN), np.float32); wtot = {}
    for tag, stem, t, cls in FR:
        w = np.where(np.isfinite(T[stem][..., 1]), P[stem] / max(np.nanmax(P[stem]), 1e-9), 0).astype(np.float32) / var[stem]
        if stem in EXCL_B: w[:] = 0
        num += np.nan_to_num(T[stem]) * w[..., None]; den += w; wtot[stem] = float(w[inn].sum())
    E = np.where(den[..., None] > 0, num / np.maximum(den, 1e-12)[..., None], np.nan).astype(np.float32); s_ = sum(wtot.values()); rep['pes_efectiu_pct'] = {k: 100 * v / s_ for k, v in wtot.items()}; rep['cobertura'] = {'px_disc': int(disc.sum()), 'px_disc_amb_dada': int((disc & (den > 0)).sum())}
    rep['exclosos'] = {'fotogrames': list(EXCL_B), 'motiu': 'fantasma +30 % (16 σ) dins del disc a (5365, 3546) del llenç, només als tres fotogrames B (F1c_punt_brillant.json); σ del vel residual 4–5× la dels A/Vixen'}; log('exclosos (apuntament B, fantasma): ' + ', '.join(EXCL_B))
    log('pes efectiu (%): ' + ' · '.join(f'{k} {v:.1f}' for k, v in rep['pes_efectiu_pct'].items()) + f" · cobertura del disc {100 * rep['cobertura']['px_disc_amb_dada'] / rep['cobertura']['px_disc']:.1f} %")
    np.save(CAU42 / 'earthshine_v42_lineal_tessella.npy', E)
    # 4. vel: perfil radial + polinomi 2D grau 4 (r ≤ 0,85), avaluat a ≤ 0,975
    G = E[..., 1]; okG = np.isfinite(G); NB = 184; rb = np.minimum((r / (0.975 * RL) * NB).astype(int), 200); prof = np.full(201, np.nan)   # perfil radial fins a 0,975 R (anells sencers): així el vel segueix el glow del limbe i el relleu no l'amplifica
    for i in range(0, NB):
        sel = okG & (rb == i)
        if sel.sum() >= 40: prof[i] = np.median(G[sel])
    ii = np.arange(201); good = np.isfinite(prof); prof = np.interp(ii, ii[good], prof[good]); vel_r = np.interp(r / (0.975 * RL) * NB, ii, prof)
    X = (xx - cxt) / 500; Y = (yy - cyt) / 500; terms = [X ** i * Y ** j for i in range(5) for j in range(5 - i)]; A = np.stack([t_[inn & okG] for t_ in terms], 1); res = (G - vel_r)[inn & okG]
    coef = np.linalg.lstsq(A, res, rcond=None)[0]; poly = sum(c * t_ for c, t_ in zip(coef, terms)); vel = (vel_r + poly).astype(np.float32); R_ = np.where(okG, G - vel, 0).astype(np.float32)
    rep['vel'] = {'r_perfil_radial_R': 0.975, 'r_fit_poly_R': 0.85, 'grau_poly': 4, 'mediana_vel_interior': float(np.median(vel[inn])), 'rms_residu_interior': float(np.std(R_[inn & okG])), 'contrast_residu_pct': float(100 * np.std(R_[inn & okG]) / np.median(vel[inn]))}
    # 5. jutge LROC
    lr = np.load(CAU42 / 'lroc_capa_v39_rgba.npy'); lb = json.loads((REB42 / 'P2b_rotacio.json').read_text())['lroc_bbox']; L = np.zeros((2 * WIN, 2 * WIN), np.float32); oy, ox = lb[1] - y0, lb[0] - x0; L[oy:oy + lr.shape[0], ox:ox + lr.shape[1]] = lr[..., :3].mean(-1)
    hpR = np.where(inn & okG, gaussian_filter(R_, 2) - gaussian_filter(R_, 12), 0); hpL = np.where(inn, gaussian_filter(np.log(np.maximum(L, 1e-3)), 2) - gaussian_filter(np.log(np.maximum(L, 1e-3)), 12), 0)
    def pear(a, b, m): u = a[m] - a[m].mean(); v = b[m] - b[m].mean(); return float((u * v).sum() / np.sqrt((u * u).sum() * (v * v).sum() + 1e-12))
    rl = pear(hpR, hpL, inn & okG); nuls = [pear(hpR, np.rot90(hpL, k_), inn & okG & np.rot90(inn, k_)) for k_ in (1, 2, 3)]
    hpR4 = np.where(inn & okG, gaussian_filter(R_, 4) - gaussian_filter(R_, 16), 0); hpL4 = np.where(inn, gaussian_filter(np.log(np.maximum(L, 1e-3)), 4) - gaussian_filter(np.log(np.maximum(L, 1e-3)), 16), 0); rl4 = pear(hpR4, hpL4, inn & okG); nuls4 = [pear(hpR4, np.rot90(hpL4, k_), inn & okG & np.rot90(inn, k_)) for k_ in (1, 2, 3)]
    rep['jutge_lroc'] = {'banda_2_12': {'r': rl, 'nuls_90_180_270': nuls}, 'banda_4_16': {'r': rl4, 'nuls_90_180_270': nuls4}}; log(f'residu × LROC: banda 2–12 r {rl:+.3f} (nuls {max(map(abs, nuls)):.3f}) · banda 4–16 r {rl4:+.3f} (nuls {max(map(abs, nuls4)):.3f}) · contrast del residu {rep["vel"]["contrast_residu_pct"]:.2f} % del vel')
    # 6. capes
    def to_srgb(rgb, m):
        Lum = (rgb[..., 0] + 2 * rgb[..., 1] + rgb[..., 2]) / 4; tone = comu.corba_to(np.nan_to_num(Lum), m, VA, pend=PEND, anc=ANC, terra=TERRA); ylin = comu.a_lineal(tone)
        q = rgb / np.maximum(Lum, 1e-9)[..., None]; q = np.nan_to_num(q, nan=1.0); qmax = q.max(axis=2)
        with np.errstate(divide='ignore', invalid='ignore'): wmax = np.where(qmax > 1, (1 / np.maximum(ylin, 1e-8) - 1) / (qmax - 1), 1)
        wg = np.clip(np.nan_to_num(wmax, nan=0, posinf=1), 0, 1); return np.clip(np.nan_to_num(comu.a_srgb(ylin[..., None] * (1 + wg[..., None] * (q - 1)))), 0, 1) * m[..., None]
    mfull = okG & (r < RL + 8)
    lineal = to_srgb(np.nan_to_num(E), mfull)
    med = np.array([float(np.median(np.nan_to_num(E[..., c])[inn])) for c in range(3)], np.float32); Lm = float((med[0] + 2 * med[1] + med[2]) / 4); col = med / Lm; fade = np.clip((r - 0.975 * RL) / (0.025 * RL), 0, 1)   # 0 dins, 1 al limbe
    try: TG = json.loads((REB42 / 'F1b_mota_i_contrast.json').read_text())['powaaah3']['medianes'][1]
    except Exception: TG = 0.364
    def srgb_gris(x): a = np.full((8, 8, 3), x, np.float32); return float(to_srgb(a, np.ones((8, 8), bool))[4, 4, 1])
    lo, hi = np.log10(Lm) - 3, np.log10(Lm) + 3
    for _ in range(50):
        mid = 0.5 * (lo + hi); lo, hi = (mid, hi) if srgb_gris(10 ** mid) < TG else (lo, mid)
    lv = 10 ** (0.5 * (lo + hi)); flat = (lv * col).astype(np.float32); Es = np.nan_to_num(E) * (lv / Lm)
    taper = 1 - np.clip((r - 0.85 * RL) / (0.10 * RL), 0, 1); taper = taper * taper * (3 - 2 * taper)   # relleu només a la zona de ciència (r ≤ 0,85 R), fos a 0 fins a 0,95 R: el model de vel no val més enllà (glow asimètric)
    rho = (np.where(okG, R_ / np.maximum(vel, 1e-9), 0) * taper).astype(np.float32); okf = okG.astype(np.float32)
    def contrast_srgb(img): g = img[..., 1][inn]; p5, p95 = np.percentile(g, [5, 95]); return float((p95 - p5) / np.median(g))
    def capa(rh, K):
        rel = flat[None, None, :] * (1 + K * rh)[..., None]; rel = np.where(mfull[..., None], (1 - fade[..., None]) * rel + fade[..., None] * Es, 0); return to_srgb(rel, mfull)
    capes = {}; rep['relleu'] = {'nivell_srgb_G_objectiu': TG, 'luminancia_lineal_pla': lv, 'factor_nivell_sobre_vel_mesurat': lv / Lm, 'color_relatiu_R_G_B': [float(c) for c in col], 'variants': {}}
    for nomv, (ctr_obj, sig) in CONTRASTS.items():
        rh = rho if sig == 0 else gaussian_filter(rho, sig) / np.maximum(gaussian_filter(okf, sig), 1e-6)
        a, b = 0.0, 400.0
        for _ in range(22):
            K = 0.5 * (a + b); a, b = (K, b) if contrast_srgb(capa(rh, K)) < ctr_obj else (a, K)
        K = 0.5 * (a + b); capes[nomv] = capa(rh, K); c_ = contrast_srgb(capes[nomv]); rep['relleu']['variants'][nomv] = {'K': K, 'suavitzat_sigma_px': sig, 'contrast_p5_p95_sobre_mediana_srgb': c_}
        log(f'capa {nomv}: K {K:.1f} (σ {sig} px) → contrast sRGB p5–p95/mediana {100 * c_:.1f} % (objectiu {100 * ctr_obj:.0f} %)')
    log(f'nivell del disc pla: sRGB G {TG:.3f} (POWAAAH3) = luminància lineal {lv:.4g}, ×{lv / Lm:.2f} sobre el vel mesurat · color R/G/B {col[0]:.3f}/{col[1]:.3f}/{col[2]:.3f}')
    mask = np.clip((RL + 4 - r) / 4.0, 0, 1)   # 1 fins al limbe mesurat (453,5), 0 a la vora del forat de la base (457,5): sense escletxa ni solapament
    def full(u16tile):
        out = np.zeros((H, W) + u16tile.shape[2:], np.uint16); out[y0:y0 + 2 * WIN, x0:x0 + 2 * WIN] = u16tile; return out
    np.save(CAU42 / 'earthshine_v42_lineal_u16.npy', full(np.round(lineal * 65535).astype(np.uint16)))
    for nomv, im in capes.items(): np.save(CAU42 / f'earthshine_v42_{nomv}_u16.npy', full(np.round(im * 65535).astype(np.uint16)))
    np.save(CAU42 / 'earthshine_v42_mascara_u16.npy', full(np.round(mask * 65535).astype(np.uint16)))
    for vell in ('earthshine_v42_relleu_u16.npy', 'earthshine_v42_relleu_suau_u16.npy'): (CAU42 / vell).unlink(missing_ok=True)
    rep['capes'] = {'lineal': 'E_lin per la corba de la base (nivell mesurat, gra inclòs)', 'relleu*': 'disc pla al nivell POWAAAH3 amb el color mesurat + relleu relatiu (E − vel)/vel × K a r ≤ 0,85 R (fos a 0 fins a 0,95 R); disc pla de 0,95 a 0,975 R; fosa a la dada lineal (×factor de nivell) de 0,975 a 1,0 R', 'mascara': '1 fins a R 453,5 (limbe mesurat), 0 a R 457,5 (vora del forat de la base): la franja és el glow mesurat ×factor de nivell'}
    savejson(REB42 / 'F1_earthshine.json', rep)
    # vistes 1:1 del disc (1400 px): E lineal (estirat p1–p99), residu ±3σ, LROC, capa relleu, capa lineal
    def png8(a, lo, hi): return (np.clip((np.nan_to_num(a) - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)
    def rgb8(im): return (np.clip(im, 0, 1) * 255).astype(np.uint8)
    pw = np.load(CAU42 / 'powaaah3_rgb_u16.npy', mmap_mode='r')[y0:y0 + 2 * WIN, x0:x0 + 2 * WIN].astype(np.float32) / 65535; pwm = np.load(CAU42 / 'powaaah3_mascara_disc_u16.npy', mmap_mode='r')[y0:y0 + 2 * WIN, x0:x0 + 2 * WIN].astype(np.float32) / 65535
    lrgb = np.zeros((2 * WIN, 2 * WIN, 3), np.float32); lrgb[oy:oy + lr.shape[0], ox:ox + lr.shape[1]] = lr[..., :3]
    p1, p99 = np.nanpercentile(G[disc], [1, 99]); sd = np.std(R_[inn & okG])
    tiles = [cv2.cvtColor(png8(G, p1, p99), cv2.COLOR_GRAY2RGB), cv2.cvtColor(png8(R_, -3 * sd, 3 * sd), cv2.COLOR_GRAY2RGB), rgb8(lineal)] + [rgb8(capes[k]) for k in CONTRASTS] + [rgb8(pw * pwm[..., None]), rgb8(lrgb / max(float(lrgb.max()), 1e-6))]
    labels = ['E lineal G (p1-p99)', 'residu E - vel (+-3 sigma)', 'lineal corba (mesurat)'] + [f"{k} K{rep['relleu']['variants'][k]['K']:.0f}" for k in CONTRASTS] + ['POWAAAH3 (Pere)', 'LROC (NASA)']
    can = np.full((2 * WIN + 30, len(tiles) * (2 * WIN + 6), 3), 25, np.uint8)
    for i, (tl, lab) in enumerate(zip(tiles, labels)): can[30:, i * (2 * WIN + 6):i * (2 * WIN + 6) + 2 * WIN] = cv2.cvtColor(tl, cv2.COLOR_RGB2BGR); cv2.putText(can, lab, (i * (2 * WIN + 6) + 8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imwrite(str(VIS42 / 'F1_earthshine_disc_1a1.png'), can); (VIS42 / 'F1_earthshine_relleu_rgb_1a1.png').unlink(missing_ok=True)
    # llenç sencer (quart) amb la capa relleu12_suau sobre la base corba, per veure-ho al seu lloc
    base = np.load(CAU42 / 'base_corba_total_v42_u16.npy', mmap_mode='r'); q = cv2.resize(np.asarray(base[::2, ::2]), None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA).astype(np.float32) / 65535
    lay = np.zeros((H, W, 3), np.float32); lay[y0:y0 + 2 * WIN, x0:x0 + 2 * WIN] = capes['relleu12_suau']; mk_ = np.zeros((H, W), np.float32); mk_[y0:y0 + 2 * WIN, x0:x0 + 2 * WIN] = mask
    lq = cv2.resize(lay[::2, ::2], None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA); mq = cv2.resize(mk_[::2, ::2], None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)[..., None]; comp = q * (1 - mq) + lq * mq
    cv2.imwrite(str(VIS42 / 'F1_llenc_base_amb_earthshine_relleu12_suau_quart.png'), cv2.cvtColor((np.clip(comp, 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)); log('F1 fet')


if __name__ == '__main__':
    main()
