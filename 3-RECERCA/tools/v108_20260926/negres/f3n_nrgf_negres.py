"""f3n (V108 · negres) · VARIANT del generador E1 de f3_filtres_v98.py NOMÉS per a la P01 NRGF (41) i la P01b NRGF estès (42), amb les cures
de les zones negres A L'ORIGEN del filtre. Parteix exactament del mateix codi (anells d'1 px centrats al Sol, només dada; anells parcials
completats amb complete_from_partial; z = (a − μ)/σ; u = afí de pantalla (rang de la V58); nivell al buit (decisió B); alfa = clip(d, 0, 1)).
La variant V107 reprodueix el ràster de la V104–V107 (es comprova bit a bit contra filtres_v103).

LA CAUSA (N2_PERFILS_NRGF.json): la NRGF normalitza cada anell per la seva σ i suposa que TOT el que varia al llarg de l'anell és corona.
  (1) De 3 R☉ enfora, part de la σ de l'anell és el GRADIENT DEL CEL (model llis de 2n grau ajustat a 6,5–8,4 R☉): 3,5 % de la variància
      a 3 R☉, 21 % a 4, 48 % a 5, ~100 % a 7. Al cel, z = gradient/σ petita ≈ ±1: la 41 aixeca el cel de dalt i enfosqueix el de baix
      (el cel local del compost varia ×1,54 entre sectors; sense filtres ×1,05). Els buits de dalt queden per sota d'un cel aixecat.
  (2) A 3–4,5 R☉ la corona és només un 4–11 % del valor de pantalla per sobre del cel (base logarítmica amb pedestal), i la NRGF en
      Multiplicar hi enfosqueix els buits un 15–20 % respecte de la mitjana de l'anell: qualsevol buit amb un guany relatiu al del cel
      menor que B_cel/B cau per sota del cel. És aritmètica: la NRGF modula tot el píxel (cel inclòs) amb l'estadística de la corona.
Les cures (variables d'entorn o arguments; totes conserven el signe i l'ordre clar/fosc de z, cap no posa píxels que no vinguin de dada):
  V107     : l'original (control, ha de ser bit a bit).
  WIE      : NRGF de Wiener amb el cel separat. Numerador sense l’estructura azimutal del cel (S − ⟨S⟩_anell, model llis PLA (--cel pla, defecte) o de 2n grau
             ajustat a la dada de 6,5–8,4 R☉; mai no entra al ràster com a píxel), i normalització regularitzada pel S/N de l'anell:
             z = d·σ_K/(σ_K² + σ_0²), d = a − S_az − μ', σ_K² = max(σ'² − σ_0², 0), σ_0² = variància no coronal residual dels anells de
             7,5–8,4 R☉. On l'anell és corona (σ_K ≫ σ_0), z = la NRGF de sempre sense el cel; al cel, z → 0 (el guany segueix el S/N).
  WIE_TER  : WIE + TERRA FÍSIC: el buit no pot quedar per sota del cel. Amb el factor combinat de 41·42 en Multiplicar a les opacitats de
             la V107, F(z) = f41·f42, es posa un terra tou a z tal que F(z) ≥ F(0)·(1 − β·w), w = 1 − B_cel/B (fracció coronal de la
             base de pantalla, capa 3; B_cel = cel del sector de 10° a 6,5–8,5 R☉), β = part del «pressupost» per a la NRGF (0,6; la
             resta per a 54, 45, 46, 56…). Terra tou (softplus, s = 0,15 en z) i només on la NRGF té guany (× g Wiener de l'anell).
             Els plomalls i els buits que no toquen el cel no canvien.
  WIE_RAD  : WIE + GUANY PER RADI: l'amplitud de z es multiplica per g(r) tal que el buit p10 de cada anell quedi al terra (l'equivalent
             d'una rampa radial d'opacitat feta dins del filtre; també abaixa els plomalls).
  WIE_CUA  : WIE + COMPRESSIÓ DE LA CUA FOSCA sense cel: z < 0 → −c·asinh(−z/c), c = 0,7 (a tots els radis).
  TER      : TERRA sense la part de Wiener (per aïllar l'efecte de cadascuna).
  CEL      : només el cel fora del NUMERADOR: z = (a − S_az − μ)/σ amb la σ ORIGINAL de l'anell (el guany de la NRGF no canvia enlloc).
  CELW     : CEL × guany de Wiener de l'anell g(r) = σ_K²/(σ_K² + σ_0²): la NRGF s'apaga on l'anell ja no té variància coronal (el cel).
  CEL_TER, CELW_TER, CEL_RAD, CEL_CUA : les mateixes cures de dalt sobre CEL/CELW; el terra s'hi fon amb la mediana de w de l'anell
             (actiu on la corona és ≥ 2 % de la pantalla per sobre del cel: fins a ~5,5 R☉; al cel no rectifica el soroll).
Ús: f3n_nrgf_negres.py [variants separades per comes] [--cel pla|quad] [--beta 0.6] [--sufix _X] → 4-RESULTATS/v108_20260926/negres/candidats/<variant><sufix>/
    La RECOMANADA (26-09): f3n_nrgf_negres.py CEL_TER --cel quad --sufix _Q  → candidats/CEL_TER_Q/P01_NRGF_u16.npy (41), P01_NRGF_extrap_u16.npy (42),
    alfes idèntiques a les de la V104–V107. Entrades: la linealitzada i la franja de la variant E (V97_FONTS, V98_FRANJA) i la base de pantalla
    (capa 3) de l'estat V107 (4-RESULTATS/v108_20260926/negres/estat_v107, de n0_estat_v107.py)."""
import sys, os, json, time, argparse
from pathlib import Path
R0 = Path(__file__).resolve().parents[4]
os.environ.setdefault('V97_FONTS', str(R0 / '4-RESULTATS/v103_banda_20260926/E/lineal_v103'))
os.environ.setdefault('V97_SORT', str(R0 / '4-RESULTATS/v108_20260926/negres/candidats'))
os.environ.setdefault('V98_FRANJA', str(R0 / '4-RESULTATS/v103_banda_20260926/E/lineal_v103_franja/A3C_franja_silueta.npz'))
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v97_refundacio_20260924'))
from v97_comu import *   # noqa: F401,F403  (H, W, CX, CY, RS, FONTS, SORT, log, sha, coords, claim)
from v86_operadors import ring_stats, complete_from_partial, smoothstep, NB
from scipy.ndimage import gaussian_filter1d
import numpy as np, cv2
ap = argparse.ArgumentParser(); ap.add_argument('variants', nargs='?', default='V107,WIE,WIE_TER,WIE_RAD,WIE_CUA,TER')
ap.add_argument('--beta', type=float, default=0.6); ap.add_argument('--suau', type=float, default=0.15); ap.add_argument('--cua', type=float, default=0.7)
ap.add_argument('--sufix', default=''); ap.add_argument('--cel', choices=['pla', 'quad'], default='pla', help='model llis del cel: pla (1, x, y: només el gradient, 1r harmònic) o 2n grau')
A = ap.parse_args(); VARS = A.variants.split(','); claim(); T0 = time.time()
DISP = R0 / '2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/filters_v58_dependencies/display'
def display(tag): d = json.loads((DISP / f'{tag}.json').read_text())['display']; return float(d['black']), float(d['white'])
O41, O42 = 99 / 255, 36 / 255                                   # opacitats de la V107 (només per al terra: el seu «pressupost» es declara amb elles)
# ---------- fonts i domini (idèntic a f3_filtres_v98.py) ----------
Q = np.load(os.environ['V98_FRANJA']); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; BOXQ = (slice(qy0, qy1), slice(qx0, qx1))
cx, cy, R = [float(v) for v in Q['centre']]; DMIN = Q['DMIN']; NBZ = len(DMIN)
a = np.load(FONTS / 'base_G.npy').astype(np.float32); m_sup = np.load(FONTS / 'support.npy') & np.isfinite(a) & (a > 0)
a[BOXQ] = Q['G']; m = m_sup.copy(); m[BOXQ] = Q['domini'] & (Q['G'] > 0); a = np.nan_to_num(a); del m_sup
r, t = coords()
yy, xx = np.ogrid[:H, :W]; dL = (np.hypot(xx - cx, yy - cy) - R).astype(np.float32)
thL = ((np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360).astype(np.float32)
def nivell_buit(u01, mm, fosa=(0.0, 1.5)):
    """Còpia literal de f3_filtres_v98.nivell_buit (decisió B de Pere, 24-09)."""
    out = u01.copy(); d = dL[BOXQ]; th = thL[BOXQ]; dist = d - np.maximum(DMIN, 0)[(th / 360 * NBZ).astype(int) % NBZ]; mb = mm[BOXQ]; ub = out[BOXQ]
    NT = 3600; tb = (th / 360 * NT).astype(int) % NT; zona = mb & (dist >= 2) & (dist < 8)
    s = np.bincount(tb[zona], weights=ub[zona], minlength=NT); n = np.bincount(tb[zona], minlength=NT).astype(float); sig = 3.0 / (R * np.radians(360 / NT))
    L = (gaussian_filter1d(s, sig, mode='wrap') / np.maximum(gaussian_filter1d(n, sig, mode='wrap'), 1e-9))[tb].astype(np.float32)
    buit = (~mb) & (d >= 0) & (d < 45); ub = np.where(buit, L, ub)
    zf = mb & (dist >= 0) & (dist < fosa[1]) & (d < 45)
    wfs = smoothstep(dist, fosa[0], fosa[1]); ub = np.where(zf, L + (ub - L) * wfs, ub)
    out[BOXQ] = ub; out[~mm & ~np.pad(np.ones_like(mb), ((qy0, H - qy1), (qx0, W - qx1)))] = 0.5
    return out, int(buit.sum())
def u_affine(q, lo, hi): return np.clip((q - lo) / (hi - lo), 0, 1).astype(np.float32)
ALFA = np.round(np.clip(dL, 0, 1) * 65535).astype(np.uint16)
# ---------- estadística d'anells (idèntica a l'E1) ----------
ri = np.floor(r).astype('int32'); nr = int(ri.max()) + 1; ids = ri[m]; tb = np.floor((t[m] + np.pi) / (2 * np.pi) * NB).astype('int32') % NB
nodes = np.arange(nr) + .5
def estadistica(vals):
    """μ, σ completades per anell (outer i inner com l'E1) i interpolades al radi continu. vals = valors al domini (float64)."""
    count, mean, std = ring_stats(vals, ids, nr); good = count > 0
    comp = count / (2 * np.pi * nodes); refc = np.median(comp[int(3 * RS):int(8 * RS)])
    cand_out = np.flatnonzero((nodes > 3 * RS) & (comp < 0.98 * refc)); r_edge = int(cand_out[0]) if cand_out.size else nr
    r_in = int(np.flatnonzero((comp >= 0.98 * refc) & (nodes > 0.9 * RS))[0])
    inner = [i for i in range(r_in) if count[i] > 0]; outer = list(range(r_edge, nr))
    mean_u, std_u, ok_o, _, _ = complete_from_partial(mean, std, ids, tb, vals, outer, list(range(r_edge - 40, r_edge)))
    mean_u, std_u2, ok_i, _, _ = complete_from_partial(mean_u, std_u, ids, tb, vals, inner, list(range(r_in, r_in + 40)))
    ok_ring = good & ok_o & ok_i
    return mean_u, std_u2, ok_ring, r_in, r_edge
v = a[m].astype('float64')
mean_u, std_u2, ok_ring, r_in, r_edge = estadistica(v); log(f'E1 · r_in {r_in} · r_edge {r_edge}')
mu = np.interp(r, nodes[ok_ring], mean_u[ok_ring]).astype('float32'); sd = np.interp(r, nodes[ok_ring], std_u2[ok_ring]).astype('float32')
z0 = np.divide(a - mu, sd, out=np.zeros_like(a), where=sd > 0).astype('float32'); del mu
sd0 = sd
rep = dict(cel=A.cel, font=str(FONTS), franja=os.environ['V98_FRANJA'], r_in=r_in, r_edge=r_edge, beta=A.beta, suau=A.suau, cua=A.cua, variants={})
# ---------- cel llis (només per a WIE*): 2n grau en (x, y), robust, a 6,5–8,4 R☉ ----------
need_wie = any(k.startswith('WIE') or k.startswith('CEL') for k in VARS)
if need_wie:
    sel = m & (r > 6.5 * RS) & (r < 8.4 * RS); sub = np.zeros_like(sel); sub[::4, ::4] = True; sel &= sub; del sub
    ys_, xs_ = np.nonzero(sel); X = (xs_ - CX) / 4000; Y = (ys_ - CY) / 4000
    Am = np.stack([np.ones_like(X), X, Y, X * X, X * Y, Y * Y], 1)[:, :(3 if A.cel == 'pla' else 6)]; b = a[sel].astype(np.float64); okf = np.ones(len(b), bool)
    for _ in range(3):
        cf, *_ = np.linalg.lstsq(Am[okf], b[okf], rcond=None); res = b - Am @ cf; s_ = np.std(res[okf]); okf = np.abs(res) < 2.5 * s_
    rep['cel_model'] = dict(tipus=A.cel, coef=cf.tolist(), residu_rms=float(s_), punts=int(okf.sum()))
    Xf = ((np.arange(W, dtype=np.float32) - CX) / 4000)[None, :]; Yf = ((np.arange(H, dtype=np.float32) - CY) / 4000)[:, None]
    cf6 = np.r_[cf, np.zeros(6 - len(cf))]; S = (cf6[0] + cf6[1] * Xf + cf6[2] * Yf + cf6[3] * Xf * Xf + cf6[4] * Xf * Yf + cf6[5] * Yf * Yf).astype(np.float32); del Xf, Yf
    cS = np.bincount(ids, minlength=nr); sS = np.bincount(ids, S[m].astype(np.float64), nr); mS = sS / np.maximum(cS, 1)
    S_az = np.where(m, S - np.interp(r, nodes[cS > 0], mS[cS > 0]).astype(np.float32), 0).astype(np.float32); del S
    a2 = (a - S_az).astype(np.float32)
    mean2, std2, ok2, _, _ = estadistica(a2[m].astype('float64'))
    ko = (nodes > 7.5 * RS) & (nodes < 8.4 * RS) & ok2; s0 = float(np.median(std2[ko])); rep['sigma_0_no_coronal'] = s0
    sK2 = np.maximum(std2 ** 2 - s0 ** 2, 0); gW = sK2 / (sK2 + s0 ** 2)                        # guany de Wiener de l'anell
    zfac = np.sqrt(sK2) / (sK2 + s0 ** 2)
    mu2 = np.interp(r, nodes[ok2], mean2[ok2]).astype('float32'); zf_ = np.interp(r, nodes[ok2], zfac[ok2]).astype('float32')
    zW = np.where(m, (a2 - mu2) * zf_, 0).astype('float32'); gWr = np.interp(r, nodes[ok2], gW[ok2]).astype('float32'); del mu2, zf_, a2
    # CEL: el mateix numerador sense el cel, però la σ ORIGINAL de l'anell (cap guany nou: el cel ja hi feia de regularitzador)
    zC = np.where(m & (sd0 > 0), (a - S_az - np.interp(r, nodes[ok_ring], mean_u[ok_ring]).astype('float32')) / np.maximum(sd0, 1e-12), 0).astype('float32')
    prof = []
    for rr_ in (1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 6, 7, 8):
        k = int(rr_ * RS); prof.append(dict(r=rr_, sigma=float(std_u2[k]), sigma_sense_cel=float(std2[k]), guany_wiener=float(gW[k])))
    rep['perfil_wiener'] = prof; log('Wiener: ' + ' · '.join(f"{p['r']}:{p['guany_wiener']:.2f}" for p in prof))
# ---------- base de pantalla (capa 3) i cel del sector: fracció coronal w ----------
lo41, hi41 = display('P01_NRGF'); lo42, hi42 = display('P01_NRGF_extrap')
ZG = np.linspace(-6, 6, 12001).astype(np.float64)
def Fz(zz): return (1 - O41 * (1 - np.clip((zz - lo41) / (hi41 - lo41), 0, 1))) * (1 - O42 * (1 - np.clip((zz - lo42) / (hi42 - lo42), 0, 1)))
FG = Fz(ZG); F0 = float(Fz(np.array(0.0)))
if any(('TER' in k) or ('RAD' in k) for k in VARS):
    sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_negres import E as E7, lum as lum7, cel_local
    B = np.empty((H, W), np.float32)
    for y0 in range(0, H, 1024): B[y0:y0 + 1024] = lum7(E7.rgb(3, (0, y0, W, min(H, y0 + 1024))))
    rr_, th_ = r / RS, ((np.degrees(-t)) % 360).astype(np.float32)             # t = atan2(y − CY, x − CX) → θ amunt = −t
    okb = (E7.alfa_efectiva(3) > 0.5)
    cvs, BS = cel_local(B, rr_, th_, okb); rep['cel_pantalla_sectors'] = [float(x) for x in cvs]
    w = np.clip(1 - BS / np.maximum(B, 1e-6), 0, 1).astype(np.float32); del B, BS, okb, rr_, th_
    # fosa del terra: només on la corona és ≥ 2 % de la pantalla per sobre del cel (mediana de w per anell); al cel, cap terra (no rectifica el soroll)
    wv_ = w[m]; w_ring = np.zeros(nr, np.float32)
    order = np.argsort(ids, kind='stable'); cnt_ = np.bincount(ids, minlength=nr); cut = np.r_[0, np.cumsum(cnt_)]; ws_ = wv_[order]
    for i in range(nr):
        if cnt_[i] > 50: w_ring[i] = np.median(ws_[cut[i]:cut[i + 1]])
    del order, ws_, wv_
    w_ring = gaussian_filter1d(w_ring, 4.0, mode='nearest'); fade_r = smoothstep(w_ring, 0.005, 0.02).astype(np.float32)
    FADE = np.interp(r, nodes, fade_r).astype(np.float32)
    rep['terra_fosa_per_radi'] = {f'{x:g}': float(fade_r[int(x * RS)]) for x in (3, 4, 4.5, 5, 5.5, 6, 6.5, 7, 8)}
    rep['w_mediana_per_radi'] = {f'{x:g}': float(w_ring[int(x * RS)]) for x in (1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 6, 7)}
    def z_terra(wv):
        """z mínima perquè F(z) ≥ F(0)·(1 − β·w) (−inf si el terra queda per sota de tot el rang)."""
        tgt = F0 * (1 - A.beta * wv); FGu, iu = np.unique(FG, return_index=True)
        zt = np.interp(tgt, FGu, ZG[iu]).astype(np.float32); return np.where(tgt <= FG[0] + 1e-9, -np.inf, zt).astype(np.float32)
    def softfloor(zz, zfl, s):
        x = (zz - zfl) / s; return np.where(np.isfinite(zfl), zfl + s * np.logaddexp(0, x), zz).astype(np.float32)
def desa_variant(nom, z):
    d = SORT / (nom + A.sufix); d.mkdir(parents=True, exist_ok=True); info = {}
    for tag, lo, hi in (('P01_NRGF', lo41, hi41), ('P01_NRGF_extrap', lo42, hi42)):
        u = np.where(m, u_affine(z, lo, hi), 0.5); u, nb = nivell_buit(u, m)
        u16 = np.round(np.clip(np.nan_to_num(u, nan=0.5), 0, 1) * 65535).astype(np.uint16); np.save(d / f'{tag}_u16.npy', u16)
        if not (d / f'{tag}_alfa_u16.npy').exists(): np.save(d / f'{tag}_alfa_u16.npy', ALFA)
        info[tag] = dict(display=[lo, hi], sha256_u16=sha(d / f'{tag}_u16.npy'), px_buit_nivell=nb)
    rep['variants'][nom + A.sufix] = info; log(nom + A.sufix + ' desada')
for nom in VARS:
    base_ = nom.split('_')[0]
    zb = {'V107': z0, 'TER': z0, 'WIE': zW if need_wie else None, 'CEL': zC if need_wie else None, 'CELW': (zC * gWr).astype(np.float32) if need_wie else None}[base_]
    if nom in ('V107', 'WIE', 'CEL', 'CELW'): z = zb
    elif nom.endswith('TER'):
        # el terra mai a tocar de la Lluna (d < 40 px del limbe de presentació, fosa fins a 80 px): allà la base de pantalla no és «corona + cel»
        # (vora del disc, franja) i w hi sortia petita (a 150–180° movia la NRGF de 828 px arran del limbe); els buits negres són a 1,3–4,5 R☉
        LIMB = smoothstep(dL, 40.0, 80.0).astype(np.float32)
        fade = {'TER': LIMB, 'WIE': (gWr * LIMB) if need_wie else None, 'CEL': FADE * LIMB, 'CELW': FADE * LIMB}[base_]
        zfl = z_terra(w); zt = softfloor(zb, zfl, A.suau); z = (zb + fade * (zt - zb)).astype(np.float32); del zfl, zt, LIMB
    elif nom.endswith('RAD'):
        # g(r): el buit p10 de cada anell al terra que dona la w p10 de l'anell (una rampa radial d'opacitat feta dins del filtre)
        ids_z = zb[m]; wv = w[m]; g_r = np.ones(nr, np.float32); step = 8
        for k0 in range(0, nr, step):
            sel_ = (ids >= k0) & (ids < k0 + step)
            if sel_.sum() < 500: continue
            zp = float(np.percentile(ids_z[sel_], 10)); wp = float(np.percentile(wv[sel_], 10)); zt = float(z_terra(np.array([wp]))[0])
            g_r[k0:k0 + step] = 1.0 if (not np.isfinite(zt) or zp >= zt or zt >= 0) else max(0.05, zt / zp)
        g_r = gaussian_filter1d(g_r, 16.0, mode='nearest'); rep.setdefault('guany_per_radi', {})[nom] = {f'{x:g}': float(g_r[int(x * RS)]) for x in (1.3, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 6, 7)}
        z = (zb * np.interp(r, nodes, g_r)).astype(np.float32); log('g(r) ' + json.dumps(rep['guany_per_radi'][nom]))
    elif nom.endswith('CUA'):
        c = A.cua; z = np.where(zb < 0, -c * np.arcsinh(-zb / c), zb).astype(np.float32)
    else: raise SystemExit('variant desconeguda ' + nom)
    desa_variant(nom, z)
# control: la V107 bit a bit
if 'V107' in VARS:
    orig = R0 / '4-RESULTATS/v103_banda_20260926/E/filtres_v103/filtres'
    rep['control_V107_bit_a_bit'] = {tag: bool(np.array_equal(np.load(SORT / 'V107' / f'{tag}_u16.npy'), np.load(orig / f'{tag}_u16.npy'))) for tag in ('P01_NRGF', 'P01_NRGF_extrap')}
    rep['control_alfa_bit_a_bit'] = bool(np.array_equal(ALFA, np.load(orig / 'P01_NRGF_alfa_u16.npy')))
    log('control ' + json.dumps(rep['control_V107_bit_a_bit']) + ' alfa ' + str(rep['control_alfa_bit_a_bit']))
rep['segons'] = round(time.time() - T0)
p = SORT / f'F3N_NRGF{A.sufix}_{"_".join(VARS)}.json'; p.write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=float) + '\n'); log('FET ' + str(p))
