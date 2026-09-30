"""j0 (V97) · EL JUTGE: la vara fixa per dir si una versió és millor que la V96. Es passa igual a la V96 (línia de base) i a la V97.
Ús: j0_jutge.py <estat> <font_lineal> <sortida.json> [--sony-a <pesos_sony_A.npy>]
  <estat>: carpeta amb els ràsters de la versió (v96_ref o estat_v97); <font_lineal>: carpeta amb fusion_starless.npy (RGB) i base_G.npy.
Mesures (totes predeclarades; el llindar de «millor» és a LLINDARS):
  A2  polígon B/G: estructura de ln(B/G) lligada a la isofota (d 200–560 px), relativa al nul (isofota girada 90° al voltant del Sol) — a la font lineal
  A4  cercle r_in: salt de nivell a r = 469 px (centrat al Sol) als filtres radials
  A5  costures d'escala: residu del perfil de contrast (8–32 px) respecte d'una corba llisa, d 20–300 px, als WOW i al compost
  A6  banda del limbe: textura a d 2–8 respecte de d 12–30 (1 = igual), i píxels amb alfa dins del limbe (d < −1)
  A8  línies al llarg del limbe (104–228°, d 2–20): fracció coherent al llarg de l'arc del detall radial
  B   Brno: correlació del detall (DoG σ2–σ16, en ln de la lluminància) del compost amb les quatre capes de Brno, per anell de R☉
  D   gra: σ robusta del DoG σ0,7–σ2 del compost al cel (4,5–6,5 R☉), per sector
  E   regressió (si es dona --contra <estat>): diferència del compost fora de les zones d'artefacte"""
import sys, json, time, argparse
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jutge_comu import *
ap = argparse.ArgumentParser(); ap.add_argument('estat'); ap.add_argument('font'); ap.add_argument('sortida'); ap.add_argument('--contra'); ap.add_argument('--sony-a')
args = ap.parse_args(); t0 = time.time()
E = Estat(args.estat); F = Path(args.font); out = dict(estat=str(args.estat), font=str(args.font), mesures={})
def log(*a): print(f'[{time.time()-t0:6.0f}s]', *a, flush=True)
FILTRES = [lid for lid in (41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56) if E.te(lid)]
BOXL = (int(LLUNA[0] - 800), int(LLUNA[1] - 800), int(LLUNA[0] + 800), int(LLUNA[1] + 800))   # caixa de la Lluna (1600²)

# ---------- A2 · polígon B/G a la font lineal ----------
fus = np.load(F / 'fusion_starless.npy', mmap_mode='r')
x0, y0, x1, y1 = BOXL; f = np.asarray(fus[y0:y1, x0:x1], np.float32)
G = f[..., 1]; B = f[..., 2]; ok = (G > 0) & (B > 0) & np.isfinite(G) & np.isfinite(B)
lbg = np.where(ok, np.log(np.maximum(B, 1e-9) / np.maximum(G, 1e-9)), 0).astype(np.float32)
hp = lbg - cv2.GaussianBlur(lbg, (0, 0), 25) / np.maximum(cv2.GaussianBlur(ok.astype(np.float32), (0, 0), 25), 1e-6)
q = cv2.GaussianBlur(np.where(ok, np.log(np.maximum(G, 1e-9)), 0).astype(np.float32), (0, 0), 6)
d = dist_limbe(BOXL); zona = ok & (d > 200) & (d < 560)
def perfil_iso(qmap):
    v = qmap[zona]; e = np.quantile(v, np.linspace(0, 1, 161)); idx = np.clip(np.searchsorted(e, v) - 1, 0, 159)
    s = np.bincount(idx, hp[zona], 160); n = np.bincount(idx, None, 160); P = s / np.maximum(n, 1)
    return float(np.sqrt(np.mean((P - P.mean()) ** 2)))
Mrot = cv2.getRotationMatrix2D((SOL[0] - x0, SOL[1] - y0), 90, 1.0); qrot = cv2.warpAffine(q, Mrot, (q.shape[1], q.shape[0]), flags=cv2.INTER_LINEAR, borderValue=float(np.median(q[zona])))
a2 = perfil_iso(q); a2n = np.median([perfil_iso(cv2.warpAffine(q, cv2.getRotationMatrix2D((SOL[0] - x0, SOL[1] - y0), ang, 1.0), (q.shape[1], q.shape[0]), borderValue=float(np.median(q[zona])))) for ang in (60, 90, 135, 200)])
out['mesures']['A2_poligon_BG'] = dict(rms_per_isofota=a2, nul=float(a2n), ratio=float(a2 / a2n), nota='ratio ≈ 1: cap estructura de color lligada a la isofota; > 1: graó de color que segueix la brillantor')
log('A2', out['mesures']['A2_poligon_BG']); del fus, f, G, B, lbg, hp, q, qrot

# ---------- polars dels filtres (Lluna) ----------
def polar_capa(lid, centre=LLUNA, r0=RLLUNA - 12, r1=RLLUNA + 320, nth=5760):
    v = E.rgb(lid, BOXL); v = v if v.ndim == 2 else v[..., 1]; a = E.dada(lid, BOXL)
    c = (centre[0] - BOXL[0], centre[1] - BOXL[1])
    P, r, th = polar(v, c, r0, r1, 0.5, nth); A, _, _ = polar(a, c, r0, r1, 0.5, nth); return P, A, r, th


def a8_linies(P, valid, dd, th):
    """Fracció del detall radial (σ 4 px) que és coherent en 60 px d'arc, a 104–228°, d 2–20. Soroll ≈ 0,2; línies ≈ 1."""
    sect = (th >= 104) & (th <= 228); band = (dd >= 2) & (dd <= 20)
    Pr = P[np.ix_(band, sect)]; Vr = valid[np.ix_(band, sect)]
    rad = Pr - cv2.GaussianBlur(np.nan_to_num(Pr), (0, 0), sigmaX=0.1, sigmaY=4); rad = np.where(Vr, rad, np.nan); n = 120
    coh = np.array([np.nanmean(rad[:, i:i + n], axis=1) for i in range(0, rad.shape[1] - n, n)]).T
    return float(np.nanstd(coh) / max(np.nanstd(rad), 1e-9))
def a5_costura(P, valid, dd):
    """Costura d'escala: salt del ln(contrast 8–32 px) al mateix d a tots els sectors. Per cada sector de 15°, el perfil de contrast
    (calaixos de 2 px, d 20–300) i la seva derivada suavitzada; la mediana entre sectors d'aquesta derivada, i el pic a d 40–220
    respecte de la dispersió robusta de la mateixa mediana (z). Una costura real surt a tots els sectors al mateix d."""
    c8 = np.abs(P - cv2.GaussianBlur(np.nan_to_num(P), (0, 0), 16)); c8 = np.where(valid, c8, np.nan)
    edges = np.arange(20, 302, 2); ns = 24; w = P.shape[1] // ns; D = []
    for k in range(ns):
        blk = c8[:, k * w:(k + 1) * w]
        prof = np.array([np.nanmean(blk[(dd >= a) & (dd < a + 2)]) for a in edges[:-1]])
        if np.isfinite(prof).mean() < 0.9: continue
        lp = np.log(np.maximum(prof, 1e-9)); lp = np.interp(np.arange(lp.size), np.flatnonzero(np.isfinite(lp)), lp[np.isfinite(lp)])
        D.append(np.gradient(cv2.GaussianBlur(lp.reshape(1, -1).astype(np.float32), (0, 0), 1.5).ravel()))
    if len(D) < 6: return None, None, None
    med = np.median(np.array(D), 0); dm = edges[:-1] + 1; z = (med - np.median(med)) / (1.4826 * np.median(np.abs(med - np.median(med))) + 1e-9)
    s = (dm >= 40) & (dm <= 220); i = np.argmax(np.abs(z[s])); return float(np.abs(z[s])[i]), int(dm[s][i]), len(D)
res_capes = {}
for lid in FILTRES:
    P, A, r, th = polar_capa(lid); dd = r - RLLUNA; valid = (A > 0.98) & np.isfinite(P)
    R = {}
    # A6: textura a la vora
    hpr = P - cv2.GaussianBlur(np.nan_to_num(P), (0, 0), sigmaX=6, sigmaY=6)
    def tex(d0, d1):
        m = (dd[:, None] >= d0) & (dd[:, None] < d1) & valid
        return float(np.nanstd(hpr[m])) if m.sum() > 500 else np.nan
    R['A6_textura_2_8_sobre_12_30'] = tex(2, 8) / tex(12, 30) if tex(12, 30) else np.nan
    R['A6_px_alfa_dins_limbe'] = int(((dd[:, None] < -1) & (A > 0.02)).sum())
    R['A8_linies_60px_arc'] = a8_linies(P, valid, dd, th)
    z, dz, ns_ = a5_costura(P, valid, dd); R['A5_costura_z'] = z; R['A5_costura_d'] = dz; R['A5_sectors'] = ns_
    res_capes[lid] = R
# A4: cercle r_in al voltant del Sol (filtres radials)
for lid in [l for l in (41, 42, 43, 44, 45, 46) if l in FILTRES]:
    P, A, r, th = polar_capa(lid, centre=SOL, r0=440, r1=500, nth=2880); valid = (A > 0.98) & np.isfinite(P)
    def m(a, b):
        s = (r >= a) & (r < b); X = np.where(valid[s], P[s], np.nan); return np.nanmean(X, axis=0)
    J = m(470, 474) - 0.5 * (m(464, 468) + m(476, 480))
    # (V97, correcció de la mètrica declarada al veredicte) només els azimuts on el limbe lunar és a > 20 px de r = 464 (la Lluna, desplaçada
    # 14 px a la dreta del Sol, hi posa el buit sense dada a la dreta i la mesura hi barrejava la vora del buit amb el cercle)
    thS = np.radians(th); dmin_llu = np.hypot(SOL[0] + 464 * np.cos(thS) - LLUNA[0], SOL[1] - 464 * np.sin(thS) - LLUNA[1]) - RLLUNA
    J = J[np.isfinite(J) & (dmin_llu > 20)]
    res_capes[lid]['A4_salt_r469_mediana'] = float(np.median(J)) if J.size > 100 else None
    res_capes[lid]['A4_salt_r469_p90abs'] = float(np.percentile(np.abs(J), 90)) if J.size > 100 else None
out['mesures']['capes'] = {str(k): v for k, v in res_capes.items()}
log('A4-A8 capes fet')

# ---------- compost (sense capes d'ajust) ----------
PAS = 2
C, cob = E.compost(pas=PAS)
Lc = (0.25 * C[..., 0] + 0.5 * C[..., 1] + 0.25 * C[..., 2]).astype(np.float32)
lnL = np.log(np.maximum(Lc, 1e-4)).astype(np.float32)
rs = radi_sol(pas=PAS); dl = dist_limbe(pas=PAS)
# A6/A8 al compost (a resolució completa a la caixa de la Lluna)
Cf, _ = E.compost(pas=1, box=BOXL); Lf = (0.25 * Cf[..., 0] + 0.5 * Cf[..., 1] + 0.25 * Cf[..., 2]).astype(np.float32)
Pc, r, th = polar(Lf, (LLUNA[0] - BOXL[0], LLUNA[1] - BOXL[1]), RLLUNA - 12, RLLUNA + 320, 0.5, 5760); dd = r - RLLUNA
hpc = Pc - cv2.GaussianBlur(np.nan_to_num(Pc), (0, 0), 6)
def texc(a, b): return float(np.nanstd(hpc[(dd >= a) & (dd < b)]))
validc = np.isfinite(Pc) & (dd[:, None] > 0.5)
z, dz, _ = a5_costura(Pc, validc, dd)
out['mesures']['compost'] = dict(A6_textura_2_8_sobre_12_30=texc(2, 8) / texc(12, 30), A8_linies_60px_arc=a8_linies(Pc, validc, dd, th),
                                 A5_costura_z=z, A5_costura_d=dz, cobertura_min=float(cob.min()))
log('compost', out['mesures']['compost'])

# ---------- B · Brno ----------
det = dog(lnL, 1.0, 8.0)  # σ 1–8 px del mostreig de pas 2 = σ 2–16 px a escala completa
Bres = {}
for lid in (230, 231, 232, 233):
    if not E.te(lid): continue
    Br = E.rgb(lid, pas=PAS); Br = Br if Br.ndim == 2 else (0.25 * Br[..., 0] + 0.5 * Br[..., 1] + 0.25 * Br[..., 2])
    okb = Br > 0.002; lb = np.log(np.maximum(Br, 1e-4)).astype(np.float32); db = dog(lb, 1.0, 8.0)
    okb = cv2.erode(okb.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool) & (cob > 0.99)
    Bres[lid] = {f'{a}-{b}': corr(det, db, okb & (rs >= a) & (rs < b) & (dl > 6)) for a, b in ((1.02, 1.5), (1.5, 2.5), (2.5, 4.0), (4.0, 6.0))}
out['mesures']['B_brno_corr_detall'] = {str(k): v for k, v in Bres.items()}
log('B', Bres)

# ---------- D · gra al cel ----------
g = dog(Lc, 0.35, 1.0); th2 = np.degrees(np.arctan2(-(np.mgrid[0:Lc.shape[0], 0:Lc.shape[1]][0] * PAS - SOL[1]), np.mgrid[0:Lc.shape[0], 0:Lc.shape[1]][1] * PAS - SOL[0])) % 360
gra = []
for s0 in range(0, 360, 30):
    m = (rs >= 4.5) & (rs < 6.5) & (th2 >= s0) & (th2 < s0 + 30) & (cob > 0.99)
    if m.sum() > 2000: v = g[m]; gra.append(float(1.4826 * np.median(np.abs(v - np.median(v)))) / max(float(np.median(Lc[m])), 1e-6))
out['mesures']['D_gra_relatiu_4.5_6.5Rsol'] = dict(mediana=float(np.median(gra)), per_sector=gra)
log('D', out['mesures']['D_gra_relatiu_4.5_6.5Rsol']['mediana'])

# ---------- E · regressió contra una altra versió ----------
if args.contra:
    E2 = Estat(args.contra); C2, _ = E2.compost(pas=PAS); dif = np.abs(C - C2).max(-1)
    zona_art = (dl < 40) | ((rs > 1.5) & (rs < 2.3))
    fora = ~zona_art & (cob > 0.99)
    out['mesures']['E_regressio'] = dict(mediana_abs_fora=float(np.median(dif[fora])), p99_fora=float(np.percentile(dif[fora], 99)),
                                        corr_detall_fora=corr(dog(lnL, 1, 8), dog(np.log(np.maximum(0.25 * C2[..., 0] + 0.5 * C2[..., 1] + 0.25 * C2[..., 2], 1e-4)).astype(np.float32), 1, 8), fora))
    log('E', out['mesures']['E_regressio'])
desa(args.sortida, out); log('FET', args.sortida)
