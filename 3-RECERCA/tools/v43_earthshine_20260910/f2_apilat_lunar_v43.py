"""F2 (V43) · APILAT LUNAR HDR amb TOTS els fotogrames dels dos trens (88 tessel·les B2-Lluna V43, marge 40 px fora del limbe), a la manera del LDIC de Brno però
en coordenades LUNARS: cada píxel és la suma ponderada dels fotogrames on aquell píxel NO està saturat (pes de validesa del run) × t_exp × g_sensor. Al limbe les
llargues saturen (pes 0) i el pes se'n va SOL a les curtes (el que demana Pere: «les curtes han de comptar més a la vora»); a l'interior manen les llargues.
 · Unitats: Vixen (la Sony × guany per canal mesurat a la F1 V42). g_sensor = 1/(σ²_ln·t) mesurat a la F1 V42 (Sony 8 s, Vixen 10 s): per segon d'exposició la Sony pesa ~1,8× la Vixen.
 · Apuntament B de la Sony EXCLÒS (declarat: fantasma +30 % dins del disc, research/160 F1c).
 · Instant declarat T0 = 15 s (la Lluna de la base V38/V42, centre (+14,8, +0,9) del Sol). A l'ANELL del limbe (r ≥ 0,93 R, dins i fora) només compten els fotogrames
   propers a T0 (pes exp(−((t−T0)/τ)²), τ 10 s): el glow dins del limbe i la corona just fora canvien amb el temps (la cromosfera es tapa/destapa); a l'interior
   (r ≤ 0,85 R) compten tots (earthshine estàtic en coordenades lunars); entremig, fosa.
 · Registre: llargues (≥ 1 s) per PEARSON PER FORÇA BRUTA als mars (passa-alt, finestra lliure r < 0,80 R, ±6 px, paràbola subpíxel) contra 572A2983, amb CONTROL d'amplitud
   coneguda al rebut (⛔ la correlació de fase amb màscara comuna de la F1 era cega: +5,−3 px → 0,05); curtes (1/500–2 s): AJUST DE CERCLE al limbe només ANOTAT (desplaçament
   sistemàtic ~1,5 px entre el limbe fotogràfic i el model d'efemèride, igual a tots; no s'aplica: la base i les capes de Pere van amb el model).
 · Vel (glow) dins del disc: perfil radial (mediana per anell) fins a 1,0 R sense cap forat (ara hi ha dada al limbe) + polinomi 2D grau 4 a r ≤ 0,85 R. Residu = earthshine + gra.
 · Jutge: residu passa-alt × LROC (r < 0,85 R) amb nuls per girs de 45° (8) i de 90/180/270.
 · Capes (u16 al llenç, per la corba de la base; dada fins a R+40 px; màscara 1 fins a R 457,5 = vora del forat de la base, i una màscara àmplia fins a R+40 per si Pere vol):
   1. `HDR lineal (corba)`: E tal qual (vel + earthshine + gra) per la corba de to de la base: el disc tal com el van veure els sensors, ara amb el limbe sense saturar.
   2. `vel ×0,3 + relleu`: vel comprimit ×0,30 a l'interior (research/127 §7) pujant a ×1 al limbe (0,90→0,985 R: continuïtat amb la dada) + residu relatiu × K (contrast sRGB 12 %, σ 3 px) a r ≤ 0,85 R.
   3. `nivell POWAAAH3 + relleu`: igual però amb l'interior al nivell del POWAAAH3 (×2,58 el vel, declarat a la F1), baixant a ×1 al limbe.
Sortides: cau/e43_*.npy, REB43/F2_apilat_lunar.json, vistes 1:1 i perfils del limbe.  Ús: f2_apilat_lunar_v43.py"""
from comu43 import *
from scipy.ndimage import gaussian_filter, shift as ndshift, rotate as ndrotate
MC = (CX + 14.8, CY + 0.9); WIN = 700; RL = 453.5; T0 = 15.0; TAU = 10.0; MARGE = 40.0
PEND, ANC, TERRA = 0.22, 0.74, 0.045; VA = 70736.46875
REB42_ = ROOT / 'output/v42_20260910/4-rebuts'; CAU42_ = HERE42 / 'cau'


def hp(z, m, s1=3, s2=12):
    z = np.where(m, np.log(np.maximum(z, 1e-3)), 0); w = m.astype(np.float32); a = gaussian_filter(z * w, s1) / np.maximum(gaussian_filter(w, s1), 1e-6); b = gaussian_filter(z * w, s2) / np.maximum(gaussian_filter(w, s2), 1e-6); return np.where(m, a - b, 0)


def fase(a, b, m):
    A = np.where(m, a - a[m].mean(), 0).astype(np.float32); B_ = np.where(m, b - b[m].mean(), 0).astype(np.float32); (dx, dy), resp = cv2.phaseCorrelate(A, B_); return float(dx), float(dy), float(resp)


def pearson_bf(z, ref, m, rng=10):
    """Desplaçament (dx, dy) que maximitza la Pearson entre z desplaçat i ref DINS de la finestra m (finestra lliure: el desplaçament es fa sobre tot z i m és més petita que el suport).
    Refinament subpíxel per paràbola al voltant del pic. Retorna (r_pic, dx, dy, r_segon_lluny)."""
    C = np.full((2 * rng + 1, 2 * rng + 1), -1.0); v = ref[m] - ref[m].mean(); vv = float((v * v).sum())
    for j, dy in enumerate(range(-rng, rng + 1)):
        for i, dx in enumerate(range(-rng, rng + 1)):
            zs = np.roll(np.roll(z, dy, 0), dx, 1); u = zs[m] - zs[m].mean(); C[j, i] = float((u * v).sum() / np.sqrt((u * u).sum() * vv + 1e-12))
    j0, i0 = np.unravel_index(int(np.argmax(C)), C.shape); r0 = float(C[j0, i0]); dx, dy = float(i0 - rng), float(j0 - rng)
    if 0 < i0 < 2 * rng and 0 < j0 < 2 * rng:
        a_, b_, c_ = C[j0, i0 - 1], C[j0, i0], C[j0, i0 + 1]; den = a_ - 2 * b_ + c_; dx += float(np.clip(0.5 * (a_ - c_) / den, -0.5, 0.5)) if den < -1e-9 else 0.0
        a_, b_, c_ = C[j0 - 1, i0], C[j0, i0], C[j0 + 1, i0]; den = a_ - 2 * b_ + c_; dy += float(np.clip(0.5 * (a_ - c_) / den, -0.5, 0.5)) if den < -1e-9 else 0.0
    jj, ii = np.mgrid[0:2 * rng + 1, 0:2 * rng + 1]; lluny = np.hypot(ii - i0, jj - j0) >= 2.5; r2 = float(C[lluny].max()) if lluny.any() else -1.0
    return r0, dx, dy, r2


def ajust_limbe(G, ok, cx, cy, R=RL, naz=360):
    """Ajust de cercle a la vora fosc→clar (disc→corona) d'un fotograma curt. Retorna (dx, dy, dR, rms, n_azimuts) o None."""
    th = np.linspace(0, 2 * np.pi, naz, endpoint=False); rr = np.arange(0.93 * R, 1.07 * R, 0.5); pts = []
    for t in th:
        xs = cx + rr * np.cos(t); ys = cy + rr * np.sin(t); xi = np.clip(np.round(xs).astype(int), 0, G.shape[1] - 1); yi = np.clip(np.round(ys).astype(int), 0, G.shape[0] - 1)
        g = G[yi, xi]; o = ok[yi, xi]
        if o.mean() < 0.95: continue
        ins = np.median(g[rr < 0.97 * R]); out = np.median(g[rr > 1.03 * R])
        if not (np.isfinite(ins) and np.isfinite(out)) or out < 1.5 * max(ins, 1e-6): continue
        mid = 0.5 * (ins + out); gs = gaussian_filter(g, 1.0); idx = np.where((gs[:-1] < mid) & (gs[1:] >= mid))[0]
        if len(idx) == 0: continue
        i = idx[-1]; f = (mid - gs[i]) / max(gs[i + 1] - gs[i], 1e-9); r_edge = rr[i] + f * (rr[1] - rr[0]); pts.append((cx + r_edge * np.cos(t), cy + r_edge * np.sin(t)))
    if len(pts) < 60: return None
    P = np.array(pts); A = np.c_[2 * P[:, 0], 2 * P[:, 1], np.ones(len(P))]; b = (P ** 2).sum(1); sol = np.linalg.lstsq(A, b, rcond=None)[0]; x0, y0 = sol[0], sol[1]; Rf = np.sqrt(sol[2] + x0 ** 2 + y0 ** 2)
    res = np.hypot(P[:, 0] - x0, P[:, 1] - y0) - Rf; keep = np.abs(res) < 3 * max(np.std(res), 0.3)
    if keep.sum() >= 60:
        P = P[keep]; A = np.c_[2 * P[:, 0], 2 * P[:, 1], np.ones(len(P))]; b = (P ** 2).sum(1); sol = np.linalg.lstsq(A, b, rcond=None)[0]; x0, y0 = sol[0], sol[1]; Rf = np.sqrt(sol[2] + x0 ** 2 + y0 ** 2); res = np.hypot(P[:, 0] - x0, P[:, 1] - y0) - Rf
    return float(x0 - cx), float(y0 - cy), float(Rf - R), float(np.std(res)), int(len(P))


def main():
    x0, y0 = int(round(MC[0])) - WIN, int(round(MC[1])) - WIN; yy, xx = np.mgrid[0:2 * WIN, 0:2 * WIN].astype(np.float32); cxt, cyt = MC[0] - x0, MC[1] - y0; r = np.hypot(xx - cxt, yy - cyt)
    inn = r < 0.85 * RL; disc = r < RL; anell = (r >= 0.93 * RL) & (r < RL); fora = (r >= RL) & (r < RL + MARGE); ple = r < RL + MARGE
    FR = json.loads((CAU43 / 'fotogrames_v43.json').read_text()); f1 = json.loads((REB42_ / 'F1_earthshine.json').read_text())
    gain = np.array(f1['guany_vixen_sobre_sony']['DSC06987'], np.float32); vs = f1['variancia_soroll_per_fotograma']
    s2t = {'sony': vs['DSC06987'] * 8.0, 'vixen': float(np.mean([vs[k] for k in ('572A2982', '572A2983', '572A2984')])) * 10.0}; gsens = {k: 1.0 / v for k, v in s2t.items()}
    rep = {'finestra': [x0, y0, 2 * WIN, 2 * WIN], 'centre_lluna_llenc': list(MC), 'RL_px': RL, 'T0_s': T0, 'tau_s': TAU, 'marge_px': MARGE, 'guany_vixen_sobre_sony': gain.tolist(), 'sigma2_ln_per_s': s2t, 'g_sensor_relatiu_sony_sobre_vixen': gsens['sony'] / gsens['vixen'], 'exclosos': {'grup': 'sony_B', 'motiu': 'fantasma +30 % (16 σ) dins del disc als fotogrames B (research/160 F1c) i vel residual 4–5×'}}
    log(f"g_sensor Sony/Vixen per segon d'exposició: {gsens['sony'] / gsens['vixen']:.2f} · guany Vixen/Sony {gain}")
    T = {}; P = {}; META = {}
    for fr in FR:
        if fr['grup'] == 'sony_B': continue
        stem = fr['nom'].split('.')[0]; a = np.load(CAU43 / f"lluna_{fr['tren']}_{stem}_v43.npy"); p = np.load(CAU43 / f"lluna_{fr['tren']}_{stem}_v43_pes.npy")
        ok = np.all(np.isfinite(a), axis=2) & (p > 0); a = np.where(ok[..., None], a, np.nan)
        if fr['tren'] == 'sony': a = a * gain
        T[stem] = a.astype(np.float32); P[stem] = (p * ok).astype(np.float32); META[stem] = fr
    log(f'{len(T)} tessel·les carregades (B exclòs)')
    # --- registre --- (⛔ la correlació de fase amb la MATEIXA màscara als dos costats és CEGA: un control de +5,−3 px tornava −0,05,−0,03 (research/125, 160 §7);
    #     aquí: Pearson per força bruta ±6 px sobre el passa-alt dels mars dins d'una finestra r < 0,80 R —lliure: el desplaçament es fa sobre tot el suport—, paràbola subpíxel,
    #     referència 572A2983 (Vixen 10 s, t 55); s'aplica si r_pic ≥ 0,30 i |d| > 0,5 px; CONTROL amb l'amplitud sospitada al rebut)
    # ⛔ el patró fix del sensor CAMINA amb la Lluna (research/127 §8): entre dos fotogrames del MATEIX sensor la Pearson troba el patró (desplaçat el que la Lluna s'ha mogut), no els mars
    #     → cada fotograma es registra contra l'ALTRE sensor (Vixen contra DSC06987; Sony contra 572A2983), banda 6–24 px (els mars fan desenes de px; el patró fi queda fora), i tot es
    #     porta al marc de 572A2983 pel vector creuat DSC06987→572A2983
    REFN = '572A2983'; REFS = 'DSC06987'; m80 = r < 0.80 * RL
    def hpm(name): g = T[name][..., 1]; return hp(np.nan_to_num(g, nan=np.nanmedian(g)), inn, 6, 24)
    refS = hpm(REFN); refV = hpm(REFS); rS = pearson_bf(refV, refS, m80); dS = (rS[1], rS[2]); regs = {}
    log(f"vector creuat DSC06987 → 572A2983: ({dS[0]:+.2f},{dS[1]:+.2f}) r {rS[0]:.3f} (segon {rS[3]:.3f})")
    ctrl = {}
    for nomc, refc, imp in (('DSC06987', refS, (5, -3)), ('572A2982', refV, (4, 2))):
        g = T[nomc][..., 1]; g0 = np.nan_to_num(g, nan=np.nanmedian(g)); c0 = pearson_bf(hp(g0, inn, 6, 24), refc, m80); c1 = pearson_bf(hp(ndshift(g0, (imp[1], imp[0]), order=1), inn, 6, 24), refc, m80)
        ctrl[nomc] = {'imposat': list(imp), 'original': [c0[1], c0[2]], 'desplacat': [c1[1], c1[2]], 'recuperat': [c1[1] - c0[1], c1[2] - c0[2]], 'esperat': [-imp[0], -imp[1]]}
        log(f"control del registre ({nomc} desplaçat {imp[0]:+d},{imp[1]:+d} px): original ({c0[1]:+.2f},{c0[2]:+.2f}) r {c0[0]:.3f} · desplaçat ({c1[1]:+.2f},{c1[2]:+.2f}) → recuperat ({c1[1] - c0[1]:+.2f},{c1[2] - c0[2]:+.2f}) (esperat {-imp[0]:+d},{-imp[1]:+d})")
    rep['registre_control'] = ctrl; rep['registre_vector_creuat_06987_a_2983'] = list(dS)
    for s, a in T.items():
        e = META[s]['exp']; okm = np.isfinite(a[..., 1]); d = dict(metode=None, dx=0.0, dy=0.0, aplicat=[0.0, 0.0])
        if e >= 1.0 and s != REFN:
            z = hp(np.nan_to_num(a[..., 1], nan=np.nanmedian(a[..., 1])), okm & inn, 6, 24); refc = refV if META[s]['tren'] == 'vixen' else refS; r0, dx, dy, r2 = pearson_bf(z, refc, m80 & okm)
            if META[s]['tren'] == 'vixen': dx, dy = dx + dS[0], dy + dS[1]   # al marc de 572A2983 pel vector creuat
            d.update(metode='pearson_mars_creuat', r_pic=r0, r_segon=r2, dx=dx, dy=dy)
            if r0 >= 0.30 and np.hypot(dx, dy) > 0.5: d['aplicat'] = [dx, dy]   # els mars són amples (desenes de px): el «segon pic a 2,5 px» és sempre ~0,99 del pic i no discrimina; el control d'amplitud coneguda (rebut) és la validació
        if 1 / 600 <= e <= 2.0:
            L = ajust_limbe(np.nan_to_num(a[..., 1], nan=0), okm, cxt, cyt)
            if L is not None: dx_, dy_, dR, rms, n = L; d['limbe'] = dict(dx=dx_, dy=dy_, dR=dR, rms=rms, n=n)   # només s'anota: és un desplaçament SISTEMÀTIC de ~1,5 px entre el limbe fotogràfic i el model d'efemèride, igual a tots els curts
        sx, sy = d['aplicat']
        if sx or sy:
            for c in range(3): a[..., c] = ndshift(np.nan_to_num(a[..., c], nan=0), (sy, sx), order=1, cval=0)
            P[s] = ndshift(P[s], (sy, sx), order=1, cval=0); okm = P[s] > 1e-3; T[s] = np.where(okm[..., None], a, np.nan)
        regs[s] = d
        if d['metode']: log(f"registre {s} ({e:g} s, t {META[s]['t']:.0f}): ({d['dx']:+.2f},{d['dy']:+.2f}) r {d['r_pic']:.3f} (segon {d['r_segon']:.3f}) → aplicat {d['aplicat'][0]:+.2f},{d['aplicat'][1]:+.2f}")
    rep['registre'] = regs; n_ap = sum(1 for d in regs.values() if any(d['aplicat'])); log(f"registre: {n_ap} fotogrames desplaçats (Pearson als mars, referència 572A2983)")
    lim = [(s, d['limbe']) for s, d in regs.items() if 'limbe' in d]
    if lim: log('ajust del limbe (curtes), mediana dx/dy/dR: ' + ', '.join(f'{np.median([l[k] for _, l in lim]):+.2f}' for k in ('dx', 'dy', 'dR')) + f' px sobre {len(lim)} fotogrames')
    # --- pesos i apilat ---
    alpha = np.clip((r - 0.85 * RL) / (0.08 * RL), 0, 1); alpha = alpha * alpha * (3 - 2 * alpha)   # 0 a ≤0,85 R (tots els fotogrames), 1 a ≥0,93 R (només l'instant)
    num = np.zeros((2 * WIN, 2 * WIN, 3), np.float64); den = np.zeros((2 * WIN, 2 * WIN), np.float64); den2 = np.zeros_like(den); texp = np.zeros_like(den); wcurt = np.zeros_like(den); nfr = np.zeros_like(den); pes = {}
    for s, a in T.items():
        m = META[s]; t = m['exp']; wt = np.exp(-((m['t'] - T0) / TAU) ** 2); okm = np.isfinite(a[..., 1]); pv = np.where(okm, P[s] / max(float(P[s].max()), 1e-9), 0)
        w = pv * t * gsens[m['tren']] * ((1 - alpha) + alpha * wt)
        num += np.nan_to_num(a) * w[..., None]; den += w; den2 += w * w; texp += pv * t; nfr += (pv > 0.5); wcurt += w * (t < 1.0)
        pes[s] = dict(interior=float(w[inn].sum()), anell=float(w[anell].sum()), fora=float(w[fora].sum()), t=m['t'], exp=t, tren=m['tren'])
    E = np.where(den[..., None] > 0, num / np.maximum(den, 1e-12)[..., None], np.nan).astype(np.float32); okE = np.isfinite(E[..., 1]) & ple
    for zona in ('interior', 'anell', 'fora'):
        tot = sum(v[zona] for v in pes.values()); top = sorted(pes.items(), key=lambda kv: -kv[1][zona])[:6]; log(f"pes a {zona}: " + ' · '.join(f"{k} ({v['exp']:g} s, t {v['t']:.0f}) {100 * v[zona] / tot:.1f} %" for k, v in top))
    rep['pes_pct'] = {z: {k: 100 * v[z] / sum(u[z] for u in pes.values()) for k, v in pes.items()} for z in ('interior', 'anell', 'fora')}
    neff = np.where(den2 > 0, den * den / np.maximum(den2, 1e-30), 0); fcurt = np.where(den > 0, wcurt / np.maximum(den, 1e-30), 0)
    rep['cobertura'] = {'px_ple': int(ple.sum()), 'px_ple_amb_dada': int(okE.sum()), 'px_disc_sense_dada': int((disc & ~okE).sum()), 'neff_mediana_interior': float(np.median(neff[inn])), 'neff_mediana_anell': float(np.median(neff[anell])), 'neff_mediana_fora': float(np.median(neff[fora])), 'fraccio_pes_curtes_interior': float(np.median(fcurt[inn])), 'fraccio_pes_curtes_anell': float(np.median(fcurt[anell])), 'fraccio_pes_curtes_fora': float(np.median(fcurt[fora])), 'texp_efectiva_s_interior': float(np.median(texp[inn])), 'texp_efectiva_s_a_0.99R': float(np.median(texp[(r > 0.985 * RL) & (r < 0.995 * RL)]))}
    log(f"cobertura: {rep['cobertura']['px_disc_sense_dada']} px del disc sense dada · N_eff interior {rep['cobertura']['neff_mediana_interior']:.1f}, anell {rep['cobertura']['neff_mediana_anell']:.1f}, fora {rep['cobertura']['neff_mediana_fora']:.1f} · pes de les curtes (<1 s): interior {100 * rep['cobertura']['fraccio_pes_curtes_interior']:.0f} %, anell {100 * rep['cobertura']['fraccio_pes_curtes_anell']:.0f} %, fora {100 * rep['cobertura']['fraccio_pes_curtes_fora']:.0f} % · t_exp efectiva interior {rep['cobertura']['texp_efectiva_s_interior']:.1f} s, a 0,99 R {rep['cobertura']['texp_efectiva_s_a_0.99R']:.2f} s")
    np.save(CAU43 / 'e43_lineal_tessella.npy', E); np.save(CAU43 / 'e43_neff.npy', neff.astype(np.float32)); np.save(CAU43 / 'e43_fraccio_curtes.npy', fcurt.astype(np.float32)); np.save(CAU43 / 'e43_texp.npy', texp.astype(np.float32))
    # --- vel: perfil radial fins a 1,0 R (anells d'1 px) + polinomi grau 4 a ≤0,85 R ---
    G = E[..., 1]; okG = np.isfinite(G); rb = np.floor(r).astype(int); NB = int(RL + MARGE) + 1; prof = np.full(NB + 1, np.nan)
    for i in range(NB):
        sel = okG & (rb == i)
        if sel.sum() >= 20: prof[i] = np.median(G[sel])
    ii = np.arange(NB + 1); good = np.isfinite(prof); prof = np.interp(ii, ii[good], prof[good]); vel_r = np.interp(r, ii, prof)
    X = (xx - cxt) / 500; Y = (yy - cyt) / 500; terms = [X ** i * Y ** j for i in range(5) for j in range(5 - i)]; A = np.stack([t_[inn & okG] for t_ in terms], 1); res = (G - vel_r)[inn & okG]
    coef = np.linalg.lstsq(A, res, rcond=None)[0]; poly = sum(c * t_ for c, t_ in zip(coef, terms)); vel = (vel_r + poly).astype(np.float32); R_ = np.where(okG, G - vel, 0).astype(np.float32)
    rep['vel'] = {'perfil_radial_fins_R': 1.0 + MARGE / RL, 'r_fit_poly_R': 0.85, 'grau_poly': 4, 'mediana_vel_interior': float(np.median(vel[inn])), 'rms_residu_interior': float(np.std(R_[inn & okG])), 'contrast_residu_pct': float(100 * np.std(R_[inn & okG]) / np.median(vel[inn])), 'perfil_G_per_px': [float(v) for v in prof]}
    rp = lambda a_, b_: float(np.median(G[okG & (r >= a_ * RL) & (r < b_ * RL)]))
    rep['perfil_limbe_G'] = {'0.50R': rp(0.49, 0.51), '0.85R': rp(0.84, 0.86), '0.95R': rp(0.945, 0.955), '0.98R': rp(0.975, 0.985), '0.995R': rp(0.99, 1.0), '1.005R': rp(1.0, 1.01), '1.02R': rp(1.015, 1.025), '1.05R': rp(1.045, 1.055)}
    log('perfil G (mediana): ' + ' · '.join(f'{k} {v:.0f}' for k, v in rep['perfil_limbe_G'].items()) + f" · contrast del residu {rep['vel']['contrast_residu_pct']:.2f} % del vel")
    # --- jutge LROC ---
    lr = np.load(CAU42_ / 'lroc_capa_v39_rgba.npy'); lb = json.loads((REB42_ / 'P2b_rotacio.json').read_text())['lroc_bbox']; L = np.zeros((2 * WIN, 2 * WIN), np.float32); oy, ox = lb[1] - y0, lb[0] - x0; L[oy:oy + lr.shape[0], ox:ox + lr.shape[1]] = lr[..., :3].mean(-1)
    def pear(a, b, m): u = a[m] - a[m].mean(); v = b[m] - b[m].mean(); return float((u * v).sum() / np.sqrt((u * u).sum() * (v * v).sum() + 1e-12))
    def bandes(s1, s2):
        hpR = np.where(inn & okG, gaussian_filter(R_, s1) - gaussian_filter(R_, s2), 0); lnL = np.log(np.maximum(L, 1e-3)); hpL = np.where(inn, gaussian_filter(lnL, s1) - gaussian_filter(lnL, s2), 0)
        rl = pear(hpR, hpL, inn & okG); nul90 = [pear(hpR, np.rot90(hpL, k_), inn & okG & np.rot90(inn, k_)) for k_ in (1, 2, 3)]
        nul45 = []
        for ang in range(45, 360, 45):
            hpLr = ndrotate(hpL, ang, reshape=False, order=1); nul45.append(pear(hpR, hpLr, inn & okG))
        return {'r': rl, 'nuls_90_180_270': nul90, 'nuls_45': nul45, 'nul_max_abs': float(max(map(abs, nul90 + nul45))), 'nul_std': float(np.std(nul45 + nul90))}
    rep['jutge_lroc'] = {'banda_2_12': bandes(2, 12), 'banda_4_16': bandes(4, 16)}
    for k, v in rep['jutge_lroc'].items(): log(f"residu × LROC {k}: r {v['r']:+.3f} · nuls (11 girs) màx |{v['nul_max_abs']:.3f}|, σ {v['nul_std']:.3f} → {v['r'] / max(v['nul_std'], 1e-6):.1f} σ")
    np.save(CAU43 / 'e43_vel.npy', vel); np.save(CAU43 / 'e43_residu.npy', R_)
    # --- capes ---
    def to_srgb(rgb, m):
        Lum = (rgb[..., 0] + 2 * rgb[..., 1] + rgb[..., 2]) / 4; tone = comu.corba_to(np.nan_to_num(Lum), m, VA, pend=PEND, anc=ANC, terra=TERRA); ylin = comu.a_lineal(tone)
        q = rgb / np.maximum(Lum, 1e-9)[..., None]; q = np.nan_to_num(q, nan=1.0); qmax = q.max(axis=2)
        with np.errstate(divide='ignore', invalid='ignore'): wmax = np.where(qmax > 1, (1 / np.maximum(ylin, 1e-8) - 1) / (qmax - 1), 1)
        wg = np.clip(np.nan_to_num(wmax, nan=0, posinf=1), 0, 1); return np.clip(np.nan_to_num(comu.a_srgb(ylin[..., None] * (1 + wg[..., None] * (q - 1)))), 0, 1) * m[..., None]
    mfull = okE; E0 = np.nan_to_num(E); lineal = to_srgb(E0, mfull)
    col = E0 / np.maximum(vel, 1e-9)[..., None]   # color local (E/vel per canal) — el vel és del canal G
    s_lim = np.clip((r - 0.90 * RL) / (0.085 * RL), 0, 1); s_lim = s_lim * s_lim * (3 - 2 * s_lim)   # 0 a ≤0,90 R, 1 a ≥0,985 R
    taper = 1 - np.clip((r - 0.85 * RL) / (0.10 * RL), 0, 1); taper = taper * taper * (3 - 2 * taper)
    okf = okG.astype(np.float32); rho = (np.where(okG, R_ / np.maximum(vel, 1e-9), 0) * taper).astype(np.float32); rho_s = gaussian_filter(rho, 3) / np.maximum(gaussian_filter(okf, 3), 1e-6)
    def contrast_srgb(img): g = img[..., 1][inn]; p5, p95 = np.percentile(g, [5, 95]); return float((p95 - p5) / np.median(g))
    def capa(c_in, K, rh):
        c = c_in + (1 - c_in) * s_lim; base = vel[..., None] * c[..., None] * col * (1 + K * rh)[..., None]; out = np.where(okE[..., None], (1 - s_lim[..., None]) * base + s_lim[..., None] * E0, 0); out = np.where((r >= 0.985 * RL)[..., None], E0, out); return to_srgb(out, mfull)
    try: TG = json.loads((REB42_ / 'F1b_mota_i_contrast.json').read_text())['powaaah3']['medianes'][1]
    except Exception: TG = 0.364
    def srgb_gris(x): a = np.full((8, 8, 3), x, np.float32); return float(to_srgb(a, np.ones((8, 8), bool))[4, 4, 1])
    Lm = float(np.median(vel[inn])); lo, hi = np.log10(Lm) - 3, np.log10(Lm) + 3
    for _ in range(50):
        mid = 0.5 * (lo + hi); lo, hi = (mid, hi) if srgb_gris(10 ** mid) < TG else (lo, mid)
    c_pow = 10 ** (0.5 * (lo + hi)) / Lm
    capes = {}; rep['capes'] = {}
    for nomv, c_in in (('vel03_relleu12', 0.30), ('powaaah3_relleu12', c_pow)):
        a, b = 0.0, 400.0
        for _ in range(22):
            K = 0.5 * (a + b); a, b = (K, b) if contrast_srgb(capa(c_in, K, rho_s)) < 0.12 else (a, K)
        K = 0.5 * (a + b); capes[nomv] = capa(c_in, K, rho_s); rep['capes'][nomv] = {'factor_vel_interior': c_in, 'K': K, 'contrast_srgb': contrast_srgb(capes[nomv]), 'nivell_srgb_G_interior': float(np.median(capes[nomv][..., 1][inn]))}
        log(f"capa {nomv}: vel ×{c_in:.2f} a l'interior → ×1 al limbe (0,90–0,985 R), K {K:.1f} (σ 3) → contrast 12 %, nivell sRGB G {rep['capes'][nomv]['nivell_srgb_G_interior']:.3f}")
    rep['capes']['lineal'] = {'nivell_srgb_G_interior': float(np.median(lineal[..., 1][inn])), 'nivell_srgb_G_0.99R': float(np.median(lineal[..., 1][(r > 0.985 * RL) & (r < 0.995 * RL)])), 'nivell_srgb_G_1.02R': float(np.median(lineal[..., 1][(r > 1.015 * RL) & (r < 1.025 * RL)]))}
    mask = np.clip((RL + 4 - r) / 4.0, 0, 1); mask_ampla = np.clip((RL + MARGE - 8 - r) / 8.0, 0, 1)
    def full(u16tile):
        out = np.zeros((H, W) + u16tile.shape[2:], np.uint16); out[y0:y0 + 2 * WIN, x0:x0 + 2 * WIN] = u16tile; return out
    np.save(CAU43 / 'e43_lineal_u16.npy', full(np.round(lineal * 65535).astype(np.uint16)))
    for nomv, im in capes.items(): np.save(CAU43 / f'e43_{nomv}_u16.npy', full(np.round(im * 65535).astype(np.uint16)))
    np.save(CAU43 / 'e43_mascara_u16.npy', full(np.round(mask * 65535).astype(np.uint16))); np.save(CAU43 / 'e43_mascara_ampla_u16.npy', full(np.round(mask_ampla * 65535).astype(np.uint16)))
    savejson(REB43 / 'F2_apilat_lunar.json', rep)
    # --- vistes 1:1 ---
    def png8(a, lo, hi): return (np.clip((np.nan_to_num(a) - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)
    def rgb8(im): return (np.clip(im, 0, 1) * 255).astype(np.uint8)
    pw = np.load(CAU42_ / 'powaaah3_rgb_u16.npy', mmap_mode='r')[y0:y0 + 2 * WIN, x0:x0 + 2 * WIN].astype(np.float32) / 65535; pwm = np.load(CAU42_ / 'powaaah3_mascara_disc_u16.npy', mmap_mode='r')[y0:y0 + 2 * WIN, x0:x0 + 2 * WIN].astype(np.float32) / 65535
    lrgb = np.zeros((2 * WIN, 2 * WIN, 3), np.float32); lrgb[oy:oy + lr.shape[0], ox:ox + lr.shape[1]] = lr[..., :3]; old = np.load(CAU42_ / 'earthshine_v42_lineal_u16.npy', mmap_mode='r')[y0:y0 + 2 * WIN, x0:x0 + 2 * WIN].astype(np.float32) / 65535
    p1, p99 = np.nanpercentile(G[inn], [1, 99]); sd = np.std(R_[inn & okG])
    tiles = [cv2.cvtColor(png8(G, p1, p99), cv2.COLOR_GRAY2RGB), cv2.cvtColor(png8(np.log10(np.maximum(np.nan_to_num(G), 1)), np.log10(max(p1, 1)), np.log10(np.nanmax(G[ple]))), cv2.COLOR_GRAY2RGB), cv2.cvtColor(png8(R_, -3 * sd, 3 * sd), cv2.COLOR_GRAY2RGB), cv2.cvtColor(png8(fcurt, 0, 1), cv2.COLOR_GRAY2RGB), rgb8(old), rgb8(lineal), rgb8(capes['vel03_relleu12']), rgb8(capes['powaaah3_relleu12']), rgb8(pw * pwm[..., None]), rgb8(lrgb / max(float(lrgb.max()), 1e-6))]
    labels = ['E43 G lineal (p1-p99 interior)', 'E43 G log (limbe i glow)', 'residu E43 - vel (+-3 sigma)', 'fraccio de pes de les curtes (<1 s)', 'V42 lineal (corba) [vell]', 'V43 HDR lineal (corba)', f"V43 vel x0.3 + relleu K{rep['capes']['vel03_relleu12']['K']:.0f}", f"V43 nivell POWAAAH3 + relleu K{rep['capes']['powaaah3_relleu12']['K']:.0f}", 'POWAAAH3 (Pere)', 'LROC (NASA)']
    can = np.full((2 * WIN + 30, len(tiles) * (2 * WIN + 6), 3), 25, np.uint8)
    for i, (tl, lab) in enumerate(zip(tiles, labels)): can[30:, i * (2 * WIN + 6):i * (2 * WIN + 6) + 2 * WIN] = cv2.cvtColor(tl, cv2.COLOR_RGB2BGR); cv2.putText(can, lab, (i * (2 * WIN + 6) + 8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imwrite(str(VIS43 / 'F2_apilat_lunar_disc_1a1.png'), can)
    # retall del limbe est i oest ×4 (V42 lineal | V43 lineal | V43 vel0.3 | POWAAAH3)
    for nomz, (xa, ya) in (('est', (int(cxt - RL), int(cyt))), ('oest', (int(cxt + RL), int(cyt))), ('nord', (int(cxt), int(cyt - RL)))):   # al llenç l'est és a l'ESQUERRA (−x)
        sl = (slice(ya - 60, ya + 60), slice(xa - 60, xa + 60)); row = [cv2.resize(rgb8(im)[sl], (480, 480), interpolation=cv2.INTER_NEAREST) for im in (old, lineal, capes['vel03_relleu12'], capes['powaaah3_relleu12'], pw * pwm[..., None])]
        cv2.imwrite(str(VIS43 / f'F2_limbe_{nomz}_x4.png'), cv2.cvtColor(np.concatenate(row, 1), cv2.COLOR_RGB2BGR))
    log(f"vistes a {VIS43}")


if __name__ == '__main__':
    main()
