"""F1 (V42/V43) · APILAT NOU D'EARTHSHINE a partir de les 8 tessel·les registrades sobre la Lluna amb la geometria viva (b2_lluna_v42: Sony DSC06987/06993 8 s,
DSC06984/06996/06999 2 s; Vixen 572A2982/83/84 10 s), sense la guarda de 8 px al limbe.
 1. Guany Sony→Vixen per canal (medianes a r < 0,8 R): tot en unitats Vixen.
 2. Registre entre tessel·les MESURAT als mars: correlació de fase del disc interior (r < 0,85 R) passa-alt (ln, σ 3–12) de cada tessel·la contra la mitjana Vixen;
    s'aplica el desplaçament (enter) si |d| > 0,7 px i la resposta és clara; s'anota tot.
 3. Pesos per variància inversa MESURADA: σ² de cada classe (Vixen 10 s: diferències entre les tres; Sony 8 s: 06987−06993; Sony 2 s: 06996−06999) al disc interior
    passa-alt, en unitats Vixen; w_i = validesa_i / σ²_classe. Cobertura per UNIÓ (no intersecció): on falta un fotograma, els altres hi són amb el seu pes.
 4. Vel de corona dins del disc: perfil radial (mediana per anell, r ≤ 0,85 R, interpolat) + polinomi 2D de grau 4 al residu (com la V4); s'avalua fins a 0,975 R.
 5. Jutge: correlació del residu passa-alt amb la capa LROC de la V39 (r < 0,85 R), amb nul per girs de 90/180/270°.
 6. Capes (u16 RGB al llenç sencer, màscara de disc R 453,5 + 10 px amb ploma 6):
    · `Earthshine V42 lineal (corba)`: E_lin (vel inclòs) per la corba de to de la base (declarat: el disc tal com el van veure els sensors, gra inclòs);
    · `Earthshine V42 disc pla + relleu ×K`: nivell pla = mediana del vel a r < 0,85; relleu = (E − vel)·K (K = 5) sobre la luminància, color = medianes per canal del vel;
      la franja 0,975–1,0 R passa de mica en mica a la dada lineal (el glow del limbe, com al POWAAAH3). Cap píxel dibuixat: tot surt de les 8 tessel·les.
Sortides: cau/earthshine_v42_{lineal,relleu}_u16.npy, cau/earthshine_v42_mascara_u16.npy, REB42/F1_earthshine.json, vistes 1:1 del disc."""
from comu42 import *
from scipy.ndimage import gaussian_filter, shift as ndshift
MC = (CX + 14.8, CY + 0.9); WIN = 700; RL = 453.5; K_RELLEU = 5.0; VA = 70736.46875; PEND, ANC, TERRA = 0.22, 0.74, 0.045
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
        w = np.where(np.isfinite(T[stem][..., 1]), P[stem] / max(np.nanmax(P[stem]), 1e-9), 0).astype(np.float32) / var[stem]; num += np.nan_to_num(T[stem]) * w[..., None]; den += w; wtot[stem] = float(w[inn].sum())
    E = np.where(den[..., None] > 0, num / np.maximum(den, 1e-12)[..., None], np.nan).astype(np.float32); s_ = sum(wtot.values()); rep['pes_efectiu_pct'] = {k: 100 * v / s_ for k, v in wtot.items()}; rep['cobertura'] = {'px_disc': int(disc.sum()), 'px_disc_amb_dada': int((disc & (den > 0)).sum())}
    log('pes efectiu (%): ' + ' · '.join(f'{k} {v:.1f}' for k, v in rep['pes_efectiu_pct'].items()) + f" · cobertura del disc {100 * rep['cobertura']['px_disc_amb_dada'] / rep['cobertura']['px_disc']:.1f} %")
    np.save(CAU42 / 'earthshine_v42_lineal_tessella.npy', E)
    # 4. vel: perfil radial + polinomi 2D grau 4 (r ≤ 0,85), avaluat a ≤ 0,975
    G = E[..., 1]; okG = np.isfinite(G); rb = np.minimum((r / (0.85 * RL) * 160).astype(int), 200); prof = np.full(201, np.nan)
    for i in range(0, 160):
        sel = okG & (rb == i)
        if sel.sum() >= 40: prof[i] = np.median(G[sel])
    ii = np.arange(201); good = np.isfinite(prof); prof = np.interp(ii, ii[good], prof[good]); vel_r = np.interp(r / (0.85 * RL) * 160, ii, prof)
    X = (xx - cxt) / 500; Y = (yy - cyt) / 500; terms = [X ** i * Y ** j for i in range(5) for j in range(5 - i)]; A = np.stack([t_[inn & okG] for t_ in terms], 1); res = (G - vel_r)[inn & okG]
    coef = np.linalg.lstsq(A, res, rcond=None)[0]; poly = sum(c * t_ for c, t_ in zip(coef, terms)); vel = (vel_r + poly).astype(np.float32); R_ = np.where(okG, G - vel, 0).astype(np.float32)
    rep['vel'] = {'r_fit_R': 0.85, 'grau_poly': 4, 'mediana_vel_interior': float(np.median(vel[inn])), 'rms_residu_interior': float(np.std(R_[inn & okG])), 'contrast_residu_pct': float(100 * np.std(R_[inn & okG]) / np.median(vel[inn]))}
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
    mfull = okG & (r < RL + 12)
    lineal = to_srgb(np.nan_to_num(E), mfull)
    med = np.array([float(np.median(np.nan_to_num(E[..., c])[inn])) for c in range(3)], np.float32); vmed = float(np.median(vel[inn])); fade = np.clip((r - 0.975 * RL) / (0.025 * RL), 0, 1)   # 0 dins, 1 al limbe
    rel = np.empty_like(E)
    for c in range(3): rel[..., c] = (med[c] / vmed) * (vmed + K_RELLEU * R_)
    rel = np.where(mfull[..., None], (1 - fade[..., None]) * rel + fade[..., None] * np.nan_to_num(E), 0); relleu = to_srgb(rel, mfull)
    Rs = gaussian_filter(np.where(okG, R_, 0), 3) / np.maximum(gaussian_filter(okG.astype(np.float32), 3), 1e-6); rel2 = np.empty_like(E)
    for c in range(3): rel2[..., c] = (med[c] / vmed) * (vmed + K_RELLEU * Rs)
    rel2 = np.where(mfull[..., None], (1 - fade[..., None]) * rel2 + fade[..., None] * np.nan_to_num(E), 0); relleu_suau = to_srgb(rel2, mfull)
    mask = np.clip((RL + 10 - r) / 6.0, 0, 1)
    def full(u16tile):
        out = np.zeros((H, W) + u16tile.shape[2:], np.uint16); out[y0:y0 + 2 * WIN, x0:x0 + 2 * WIN] = u16tile; return out
    np.save(CAU42 / 'earthshine_v42_lineal_u16.npy', full(np.round(lineal * 65535).astype(np.uint16))); np.save(CAU42 / 'earthshine_v42_relleu_u16.npy', full(np.round(relleu * 65535).astype(np.uint16))); np.save(CAU42 / 'earthshine_v42_relleu_suau_u16.npy', full(np.round(relleu_suau * 65535).astype(np.uint16))); np.save(CAU42 / 'earthshine_v42_mascara_u16.npy', full(np.round(mask * 65535).astype(np.uint16)))
    rep['capes'] = {'lineal': 'E_lin per la corba de la base', 'relleu': f'disc pla (mediana del vel) + (E − vel)·{K_RELLEU:g}, color = medianes per canal, fosa a la dada lineal de 0,975 a 1,0 R', 'relleu_suau': 'igual amb el residu suavitzat σ 3 px (declarat)', 'mascara': 'R 453,5 + 10 px, ploma 6'}
    savejson(REB42 / 'F1_earthshine.json', rep)
    # vistes 1:1 del disc (1400 px): E lineal (estirat p1–p99), residu ±3σ, LROC, capa relleu, capa lineal
    def png8(a, lo, hi): return (np.clip((np.nan_to_num(a) - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)
    p1, p99 = np.nanpercentile(G[disc], [1, 99]); sd = np.std(R_[inn & okG]); tiles = [png8(G, p1, p99), png8(R_, -3 * sd, 3 * sd), png8(np.log(np.maximum(L, 1e-3)), *np.percentile(np.log(np.maximum(L[inn], 1e-3)), [1, 99])), (relleu[..., 1] * 255).astype(np.uint8), (relleu_suau[..., 1] * 255).astype(np.uint8), (lineal[..., 1] * 255).astype(np.uint8)]
    labels = ['E lineal G (p1-p99)', 'residu E - vel (+-3 sigma)', 'LROC (V39)', f'capa relleu x{K_RELLEU:g} (G)', f'relleu x{K_RELLEU:g} suau s3 (G)', 'capa lineal corba (G)']; can = np.full((2 * WIN + 30, 6 * (2 * WIN + 6), 3), 25, np.uint8)
    for i, (tl, lab) in enumerate(zip(tiles, labels)): can[30:, i * (2 * WIN + 6):i * (2 * WIN + 6) + 2 * WIN] = cv2.cvtColor(tl, cv2.COLOR_GRAY2BGR); cv2.putText(can, lab, (i * (2 * WIN + 6) + 8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imwrite(str(VIS42 / 'F1_earthshine_disc_1a1.png'), can); cv2.imwrite(str(VIS42 / 'F1_earthshine_relleu_rgb_1a1.png'), cv2.cvtColor((relleu * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)); log('F1 fet')


if __name__ == '__main__':
    main()
