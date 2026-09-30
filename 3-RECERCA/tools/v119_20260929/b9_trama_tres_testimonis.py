"""b9 (V119, 29-09-2026) · «TRAMA»: EL DETALL TANGENCIAL (arcs, cims de llaços, cascs) CONFIRMAT PELS TRES TESTIMONIS (Sony A, Sony B, Vixen).
Encàrrec de Pere: «pots aprofitar la relliscada de la muntura per fer un altre filtre per captar justament l'altre tipus de detall?».
L'«Ordit» (la 416 de la V118, b8) compara al llarg de l'ARC i fa sortir els raigs; és cec al que s'estén al llarg de l'arc. La «Trama» fa el
contrari: compara al llarg del RADI, amb un promig al llarg de l'arc, i fa sortir el que creua els raigs.
Per què els testimonis hi valen més que a l'ordit: els anells falsos (residus del flat, caiguda de llum de l'òptica, anells blaus de la Vixen,
reflex de l'eix) van lligats al sensor o a l'òptica. Entre A i B el sensor es va moure ~750 px, i la Vixen és una altra òptica: no hi coincideixen.
Mètode, al pla log-polar centrat al Sol (ρ = ln r de 1,12 a 10,5 R☉; 2048 × 6144, fet de la graella del b1 promitjant 2 × 4):
  1. entrades de la V118 (b5): sense estrelles, peus d'halo, Vixen a la resolució de la Sony; x = ln L;
  2. es treu el perfil radial comú: la mediana de cada fila (anell) del suport;
  3. detall tangencial T = [G_ρ(1,2 %) − G_ρ(12 %)] ∘ G_θ(2°), i se'n treu la resta de gran escala (G_ρ(30 %) ∘ G_θ(2°) del resultat)
     i la part perfectament circular (la mitjana de cada anell);
  4. REGISTRE AL RADI (la lliçó de la V118): cada testimoni es desplaça al llarg de ρ fins a la geometria del compost de la V115 (el mateix
     operador sobre el canal G del render natiu), per finestres de 10° × 0,15 en ln r, ±0,02 ln r, correlació ≥ 0,5, mapa suau;
  5. concordança de tres: w₃ = min de les coherències per parelles (finestra 10 % r × 6°) i T₃ = w₃ · [mateix signe] · signe · min(|T_A|, |T_B|, |T_V|);
  6. controls nuls: la Vixen girada 30° i la Vixen desplaçada +0,14 en ln r (més que l'escala més gran) han de fer caure la coincidència;
  7. κ(r) = β del compost: pendent del detall tangencial del compost contra T₃, per anells de 0,4 R☉ (BETA_V115.json, com el b25).
Ús: b9_trama_tres_testimonis.py <carpeta_b5 de la V118> <carpeta_sortida>
  → D_minim_f32.npy (T₃ cartesià, el nom que espera el b3), W3_coherencia_f16.npy, DA_f16.npy (T_A registrat), BETA_V115.json, B9_REBUT.json"""
import sys, json, time, importlib.util, numpy as np, cv2, tifffile
from pathlib import Path
from scipy import ndimage as ndi
B5D, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
sys.argv = [sys.argv[0], str(OUT)]
R_ = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('b5', R_ / '3-RECERCA/tools/v118_20260929/b5_filtre_tres_testimonis.py'); b5 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b5)
b1, R, H, W, SOL, RS = b5.b1, b5.R, b5.H, b5.W, b5.SOL, b5.RS
REF = R / '4-RESULTATS/v115_nrgf_20260929/V115_natiu/visible_complet.tif'
FR, FT = 2, 4                                   # promig de la graella del b1: 4096 × 24576 → 2048 × 6144
NR, NT = b1.NR // FR, b1.NT // FT; DR = float(b1.dr * FR); DTH = 360.0 / NT
RHO = b1.rho.reshape(NR, FR).mean(1); RR = (np.exp(RHO) / RS)[:, None]
S_R1, S_R2, S_R3, S_T = 0.012 / DR, 0.12 / DR, 0.30 / DR, 2.0 / DTH
W_R, W_T = 0.10 / DR, 6.0 / DTH
REG = dict(ft=10.0, fr=0.15, maxd=0.02, cmin=0.5, st=15.0, sr=0.20)
t0 = time.time()
def redueix(P): return cv2.resize(P, (NT, NR), interpolation=cv2.INTER_AREA)
def gt(x, sr, st):
    """gaussiana amb θ periòdic (σ_ρ, σ_θ en mostres del pla reduït)."""
    p = int(4 * st) + 2; xp = np.concatenate([x[:, -p:], x, x[:, :p]], 1)
    return cv2.GaussianBlur(xp, (0, 0), sigmaX=float(st), sigmaY=float(sr), borderType=cv2.BORDER_REFLECT)[:, p:-p]
def gn(x, M, sr, st):
    den = gt(M.astype(np.float32), sr, st); return gt(np.where(M, x, 0).astype(np.float32), sr, st) / np.maximum(den, 1e-6), den
def pla(L, m):
    """ln L al pla reduït i el seu suport (tot el promig dins del suport)."""
    Mf = redueix(b1.polar(m.astype(np.float32))); P = redueix(b1.polar(np.where(m, np.log(np.maximum(L, 1e-9)), 0).astype(np.float32)))
    M = Mf > 0.999; return np.where(M, P / np.maximum(Mf, 1e-6), 0).astype(np.float32), M
def tangencial(x, M):
    xm = np.where(M, x, np.nan); med = np.nanmedian(xm, axis=1, keepdims=True); med = np.where(np.isfinite(med), med, 0)
    y = np.where(M, x - med, 0).astype(np.float32)
    a, _ = gn(y, M, S_R1, S_T); c, _ = gn(y, M, S_R2, S_T); T = np.where(M, a - c, 0).astype(np.float32)
    g, den = gn(T, M, S_R3, S_T); T = np.where(M & (den > 0.3), T - g, 0).astype(np.float32)
    # la part perfectament circular (la mitjana de cada anell) fora: cap estructura real de la corona no és un anell sencer, i en canvi sí que
    # ho són els efectes de vora del suport (arran del limbe) i els anells del perfil radial; el control nul girat ho va mostrar (0,37 a 1,2–1,6 R☉)
    Mk = M & (T != 0); n_ = Mk.sum(1, keepdims=True); mu = np.where(n_ > 0, np.where(Mk, T, 0).sum(1, keepdims=True) / np.maximum(n_, 1), 0)
    return np.where(Mk, T - mu, 0).astype(np.float32)
# 1–3: els tres testimonis i el compost
HALO = json.load(open(B5D / 'B5_AJUSTOS_ESTRELLES.json'))['halo']; RADIS = {tuple(int(v) for v in k.split(',')): d['radi'] for k, d in HALO.items()}
LA, LB, LV, m, info = b5.entrades(RADIS); print(f'entrades {time.time() - t0:.0f}s', flush=True)
xA, M = pla(LA, m); xB, _ = pla(LB, m); xV, _ = pla(LV, m); del LA, LB, LV
U = tifffile.memmap(REF, mode='r'); G = np.empty((H, W), np.float32)
for y0 in range(0, H, 1024): G[y0:y0 + 1024] = np.asarray(U[y0:y0 + 1024, :, 1], np.float32) / 65535
xU, MU = pla(G, G > 0.004); del G
TA, TB, TV, TU = tangencial(xA, M), tangencial(xB, M), tangencial(xV, M), tangencial(xU, MU); del xA, xB, xV, xU
print(f'detall tangencial {time.time() - t0:.0f}s', flush=True)
# 4: registre al llarg del radi
def mapa_radial(TX, nom):
    v = M & MU; wt = int(round(REG['ft'] / DTH)); wr = int(round(REG['fr'] / DR)); ms = int(np.ceil(REG['maxd'] / DR))
    box = lambda z: cv2.boxFilter(np.concatenate([z[:, -wt:], z, z[:, :wt]], 1), -1, (wt, wr), normalize=True, borderType=cv2.BORDER_REFLECT)[:, wt:-wt]
    uu = box(np.where(v, TU * TU, 0)); cor = []
    for s in range(-ms, ms + 1):
        xs = np.roll(TX, -s, axis=0); vs = v & np.roll(v, -s, axis=0)
        num = box(np.where(vs, xs * TU, 0)); xx = box(np.where(vs, xs * xs, 0)); cov = box(vs.astype(np.float32))
        cor.append(np.where(cov > 0.9, num / np.sqrt(np.maximum(xx * uu, 1e-20)), np.nan))
    cor = np.nan_to_num(np.stack(cor), nan=-1); i = np.argmax(cor, 0); cmax = np.take_along_axis(cor, i[None], 0)[0]
    ii = np.clip(i, 1, 2 * ms - 1); y0, y1, y2 = [np.take_along_axis(cor, (ii + k)[None], 0)[0] for k in (-1, 0, 1)]
    den_ = y0 - 2 * y1 + y2; sub = np.where(np.abs(den_) > 1e-9, 0.5 * (y0 - y2) / np.where(np.abs(den_) > 1e-9, den_, 1), 0)
    d = (ii + sub - ms).astype(np.float32); bo = (cmax >= REG['cmin']) & (i > 0) & (i < 2 * ms) & v
    g = np.zeros_like(d); g[::max(wr // 2, 1), ::max(wt // 2, 1)] = 1; pes = (bo & (g > 0)).astype(np.float32)
    gg = (g > 0).astype(np.float32)
    def nivell(k):
        sm = lambda z: gt(z, k * REG['sr'] / DR, k * REG['st'] / DTH); num, den, dg = sm(d * pes), sm(pes), sm(gg)
        return np.where(den > 1e-12, num / np.maximum(den, 1e-12), 0), np.clip(den / np.maximum(0.3 * dg, 1e-12), 0, 1)
    df, af = nivell(1.0); dc, ac = nivell(3.0)
    dm = (af * df + (1 - af) * ac * dc).astype(np.float32)             # mapa continu (la lliçó del b8 de la V118)
    mes = d[pes > 0] * DR; rrm = (RR * np.ones((1, NT)))[pes > 0]
    est = dict(finestres_bones=int(pes.sum()), finestres=int(g.sum()), mediana_ln_r=round(float(np.median(mes)), 4) if mes.size else None,
               p10_p90_ln_r=[round(float(np.percentile(mes, q)), 4) for q in (10, 90)] if mes.size else None,
               per_radi={f'{a}-{b}': (round(float(np.median(mes[(rrm >= a) & (rrm < b)])), 4) if ((rrm >= a) & (rrm < b)).sum() > 5 else None) for a, b in ((1.2, 2), (2, 3), (3, 4.5), (4.5, 7))})
    print(nom, json.dumps(est, ensure_ascii=False), flush=True); return dm, est
def desplaca(TX, dm):
    my = (np.arange(NR, dtype=np.float32)[:, None] + dm).astype(np.float32); mx = np.repeat(np.arange(NT, dtype=np.float32)[None, :], NR, 0)
    out = cv2.remap(TX, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    ok = cv2.remap(M.astype(np.float32), mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0) > 0.999
    return np.where(ok & M, out, 0).astype(np.float32), ok
reg, Mr = {}, M.copy()
for nom, TX in (('A', TA), ('B', TB), ('V', TV)):
    dm, est = mapa_radial(TX, nom); Tr, ok = desplaca(TX, dm); Mr &= ok; reg[nom] = dict(T=Tr, est=est); np.save(OUT / f'desplacament_{nom}_ln_r_f16.npy', (dm * DR).astype(np.float16))
res_reg = {n: mapa_radial(reg[n]['T'], n + ' registrat')[1] for n in reg}
abans_reg = {n: reg[n]['est'] for n in reg}
TA, TB, TV = (np.where(Mr, reg[n]['T'], 0).astype(np.float32) for n in ('A', 'B', 'V')); del reg
# 5: concordança de tres
def coh(u, v, Mk):
    cov, den = gn(u * v, Mk, W_R, W_T); vu, _ = gn(u * u, Mk, W_R, W_T); vv, _ = gn(v * v, Mk, W_R, W_T)
    w = np.clip(cov / np.maximum(0.5 * (vu + vv), 1e-12), 0, 1).astype(np.float32); w[~Mk] = 0; return w * np.clip((den - 0.6) / 0.4, 0, 1).astype(np.float32)
def tres(TA, TB, TV, Mk):
    wp = {'A·B': coh(TA, TB, Mk), 'A·V': coh(TA, TV, Mk), 'B·V': coh(TB, TV, Mk)}; w3 = np.minimum(np.minimum(wp['A·B'], wp['A·V']), wp['B·V'])
    mag = np.minimum(np.minimum(np.abs(TA), np.abs(TB)), np.abs(TV)); igual = (TA * TB > 0) & (TA * TV > 0)
    return wp, w3, (w3 * np.where(igual, np.sign(TA) * mag, 0)).astype(np.float32)
wp, w3, T3 = tres(TA, TB, TV, Mr)
print(f'concordança {time.time() - t0:.0f}s', flush=True)
BANDES = ((1.2, 1.6), (1.6, 2.2), (2.2, 3.2), (3.2, 4.5), (4.5, 7))
def mediana(X, Mk, a, b): k = Mk & (RR >= a) & (RR < b); return round(float(np.median(X[k])), 3) if k.sum() > 1000 else None
# 6: controls nuls (la Vixen girada 30°; la Vixen desplaçada +0,14 en ln r)
nuls = {}
for nom, TVn, Mn in (('vixen_girada_30graus', np.roll(TV, int(30 / DTH), axis=1), Mr & np.roll(Mr, int(30 / DTH), axis=1)),
                     ('vixen_desplacada_0.14_ln_r', np.roll(TV, int(0.14 / DR), axis=0), Mr & np.roll(Mr, int(0.14 / DR), axis=0))):
    wpn, w3n, _ = tres(TA, TB, np.where(Mn, TVn, 0).astype(np.float32), Mn)
    nuls[nom] = {f'{a}-{b}': dict(tres=mediana(w3n, Mn, a, b), AV=mediana(wpn['A·V'], Mn, a, b), AB=mediana(wpn['A·B'], Mn, a, b)) for a, b in BANDES}
print('nuls', json.dumps(nuls, ensure_ascii=False), flush=True)
# 7: κ del compost (β per anells de 0,4 R☉, com el b25): pendent del detall tangencial del compost contra T₃
TUr = np.where(Mr & MU, TU, 0); edges = np.arange(1.2, 9.6, 0.4); beta = []
for a, b in zip(edges[:-1], edges[1:]):
    k = (RR >= a) & (RR < b) & (T3 != 0) & (TUr != 0); x_, y_ = T3[k], TUr[k]
    beta.append(float(np.sum(x_ * y_) / np.sum(x_ * x_)) if k.sum() > 1000 else None)
json.dump(dict(r_centres=[(a + b) / 2 for a, b in zip(edges[:-1], edges[1:])], beta=beta,
               nota='β = pendent del detall tangencial del compost desat de la V115 contra la trama de tres testimonis (T₃), per anells de 0,4 R☉'),
          open(OUT / 'BETA_V115.json', 'w'), ensure_ascii=False, indent=1)
# sortides cartesianes
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); rc = np.hypot(xx - SOL[0], yy - SOL[1]); tc = np.mod(np.arctan2(-(yy - SOL[1]), xx - SOL[0]), 2 * np.pi); del yy, xx
IX = (tc / (2 * np.pi) * NT).astype(np.float32); IY = ((np.log(np.maximum(rc, 1)) - RHO[0]) / DR).astype(np.float32); fora = (IY < 0) | (IY > NR - 1); del rc, tc
def cart(P): o = cv2.remap(np.concatenate([P, P[:, :2]], 1).astype(np.float32), IX, IY, cv2.INTER_LINEAR, borderValue=0); o[fora] = 0; return o
mc = cart(Mr.astype(np.float32)) > 0.5; viu = ~mc & ~ndi.binary_dilation(mc, iterations=2)
c = cart(T3); c[viu] = 0; np.save(OUT / 'D_minim_f32.npy', c.astype(np.float32)); np.save(OUT / 'W3_coherencia_f16.npy', cart(w3).astype(np.float16))
np.save(OUT / 'DA_f16.npy', cart(TA).astype(np.float16)); np.save(OUT / 'TU_compost_f16.npy', cart(np.where(MU, TU, 0)).astype(np.float16))
bandes = {f'{a}-{b}': dict(coincidencia_mediana={**{p: mediana(v, Mr, a, b) for p, v in wp.items()}, 'tres (mínim)': mediana(w3, Mr, a, b)},
                           sd_pct={n: (round(float(X[Mr & (RR >= a) & (RR < b)].std() * 100), 4) if (Mr & (RR >= a) & (RR < b)).sum() > 1000 else None) for n, X in (('A', TA), ('B', TB), ('V', TV), ('T3', T3))})
          for a, b in BANDES}
rep = dict(guio=str(Path(__file__).relative_to(R)), entrades_b5=str(B5D.relative_to(R)), referencia_geometria=str(REF.relative_to(R)),
           pla=dict(NR=NR, NT=NT, r0_Rsol=1.12, r1_Rsol=10.5), operador=dict(radi_frac=[0.012, 0.12], gran_escala_frac=0.30, promig_arc_graus=2.0, finestra_coherencia=dict(frac_r=0.10, graus=6.0)),
           registre_radial=dict(parametres=REG, abans=abans_reg, despres=res_reg),
           combinacio='T = min(w_AB, w_AV, w_BV) · [A, B i V del mateix signe] · signe · min(|T_A|, |T_B|, |T_V|)', controls_nuls=nuls, bandes=bandes,
           beta=dict(zip([f'{(a + b) / 2:.1f}' for a, b in zip(edges[:-1], edges[1:])], [None if v is None else round(v, 2) for v in beta])), segons=round(time.time() - t0, 1))
(OUT / 'B9_REBUT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print(json.dumps(dict(bandes=bandes, beta=rep['beta']), ensure_ascii=False))
