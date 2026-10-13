"""c9 (v2, 01-10 tarda, després de la revisió de Codex) · Brillantor absoluta de la nostra corona contra SOHO/LASCO C2 (B = K + F) i K-Cor (pB), en B/B☉ (brillantor mitjana del disc).
NOSTRA: fusion_total_v42 (canal G; unitats de la Vixen, sRGB lineal), passada a ADU/s pel perfil absolut de research/76 §5.1
        (luminància neta, ADU/s per píxel verd) a 1,10 i 1,50 R☉, on el cel pesa ≤ 5 %, i a B/B☉ amb el factor de research/75 §5.2
        (2,772 × 10⁻¹¹ per ADU/s, ±10 %). El cel NO es resta abans: la regressió el mesura.
LASCO C2: c2_calibrate.pro de la NRL: B = (DN − biaix) · calfac / exptime · vig, calfac(ORANGE, MJD) = (4,60403e-7·MJD + 0,0374116)·1e-10.
K-Cor: pB de la GIF pública de nivell 2 (escala 0–9 × 10⁻⁷ B☉, «Intensity^0,8»).
Per anells i per caselles d'1° d'angle: nostra(PA) = f · C2(PA) + s   (f: quocient de calibratge; s: cel + llum difusa nostra)
                                        nostra(PA) = g · pB(PA) + s'  (g ≈ 1/p: invers del grau de polarització de la corona K)
p(r) teòric: dispersió de Thomson (van de Hulst 1950) amb enfosquiment del limbe, per a models de densitat de manual.
v2 (revisió de Codex): (a) polar() afí exacte; (b) la transferència a research/76 es fa amb el SEU radi (R☉ = 959″) i la SEVA
luminància ((G + kr·R)/2, kr de 1,3–1,5 R☉) i el SEU tractament del cel (constant = mediana a r76 > 7,2; pla ajustat al residu del
perfil azimutal a r76 > 3,5); (c) medianes sobre les mateixes caselles d'angle; (d) regressió sobre la nostra brillantor menys el cel
(constant + pla), perquè la pendent no absorbeixi el gradient."""
import json, sys
import numpy as np
from scipy import ndimage as nd
from astropy.io import fits
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from comu_comp import *

OUT = RES / 'brillantor'; OUT.mkdir(exist_ok=True)
CAU = ARREL / '3-RECERCA/resultats/v97_refundacio_20260924/cadena_raw/b3_baseline/cau'
F = np.load(CAU / 'fusion_total_v42.npy', mmap_mode='r')
OFF = np.array([1385.67, 1147.95 + 77])
mars = json.load(open(ARREL / '3-RECERCA/resultats/ia_output/apod_anotada_20260918/mars_final.json'))
P = GEO['P_deg']; N = np.array(mars['N']); E = np.array(mars['E'])          # orientació del llenç (marc de la final del 18-09)
n_sol = np.cos(np.radians(P)) * N + np.sin(np.radians(P)) * E; e_sol = -np.sin(np.radians(P)) * N + np.cos(np.radians(P)) * E
SC = 2.15035                                                                # ″/px del llenç
gL = Geo('llenç', GEO['sol_px_efemeride'][0] + OFF[0], GEO['sol_px_efemeride'][1] + OFF[1], GEO['R_sol_arcsec'] / SC, n_sol, e_sol, '', '')
print(f"llenç {F.shape}; Sol ({gL.cx:.1f}, {gL.cy:.1f}); R☉ {gL.R:.2f} px")
Rch = np.asarray(F[..., 0], np.float32); G = np.asarray(F[..., 1], np.float32)
H, W = G.shape
K76 = 959.0 / GEO['R_sol_arcsec']          # radi de research/76 (959″) en R☉ reals d'aquest dia (946,66″): r_real = r76 · K76

# ---------------------------------------------------------------- 1. luminància i cel com a research/76
Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
Rfull, PAfull = gL.polar(X, Y); RR76 = Rfull / K76
ref = (RR76 > 1.3) & (RR76 < 1.5) & np.isfinite(G) & np.isfinite(Rch)
kr = float(np.median(G[ref]) / np.median(Rch[ref]))
LUM = np.where(np.isfinite(Rch) & np.isfinite(G), 0.5 * (G + kr * Rch), G).astype(np.float32)
del Rch
print(f"luminància = (verd + {kr:.3f}·vermell)/2, com a research/76")
sl = (slice(0, H, 4), slice(0, W, 4))
l4 = LUM[sl]; r4 = RR76[sl]; x4 = X[sl]; y4 = Y[sl]
# perfil azimutal (mediana per anell de 0,02 en unitats de research/76) i residu
edges = np.arange(1.0, 13.0, 0.02); k = np.digitize(r4, edges) - 1; ok4 = np.isfinite(l4)
med = np.array([np.median(l4[ok4 & (k == i)]) if np.any(ok4 & (k == i)) else np.nan for i in range(len(edges) - 1)])
base = np.interp(r4, 0.5 * (edges[1:] + edges[:-1])[np.isfinite(med)], med[np.isfinite(med)])
fora = ok4 & (r4 > 3.5)
Apla = np.c_[np.ones(fora.sum()), (x4[fora] - gL.cx) / gL.R, (y4[fora] - gL.cy) / gL.R]
cpla, *_ = np.linalg.lstsq(Apla, (l4 - base)[fora], rcond=None)
cel_const = float(np.median(l4[ok4 & (r4 > 7.2)]))
ccel = np.array([cel_const, cpla[1], cpla[2]])
print(f"cel (com research/76, unitats del llenç): constant {cel_const:.1f} (mediana a r76 > 7,2), gradient {cpla[1]:+.2f}, {cpla[2]:+.2f} per R☉")
def cel(x, y): return ccel[0] + ccel[1] * (x - gL.cx) / gL.R + ccel[2] * (y - gL.cy) / gL.R
del l4, r4, x4, y4, k, base

# ---------------------------------------------------------------- 2. pas a ADU/s amb el perfil de research/76 (luminància neta)
R76 = {1.10: 47766.0, 1.50: 4937.0, 2.00: 809.0, 3.00: 175.0, 5.00: 37.0}   # ADU/s, mediana de l'anell [r, r + 0,02]
# Sensibilitat de Q(1,50) al cel (revisió 2 de Codex): (a) l'adoptat (perfil per medianes en anells de 0,02); (b) com hdr_corona_vixen:
# mitjana per anell d'1 px i suavitzat de 17 punts; (c) el de la v1: pla ajustat directament al cel a r > 7,5 R☉.
def q15(celf):
    m = (RR76 > 1.50) & (RR76 < 1.52) & np.isfinite(LUM); yi, xi = np.nonzero(m)
    return float(np.median(LUM[yi, xi] - celf(xi, yi)) / R76[1.50])
sens = {'a_mediana_0,02': None}
rpx = (r4 * K76 * gL.R).astype(np.int32) if False else None
l4 = LUM[sl]; r4 = RR76[sl]; x4 = X[sl]; y4 = Y[sl]; ok4 = np.isfinite(l4)
ib = np.round(r4 * K76 * gL.R / 4).astype(np.int32)                 # anells d'1 px de la graella de 4 (= 4 px del llenç)
nb = ib.max() + 1; sm_ = np.bincount(ib[ok4], weights=l4[ok4], minlength=nb); ct = np.bincount(ib[ok4], minlength=nb)
prof = np.where(ct > 30, sm_ / np.maximum(ct, 1), np.nan); idx = np.arange(nb); okp = np.isfinite(prof)
prof = np.interp(idx, idx[okp], prof[okp]); prof = np.convolve(np.pad(prof, 8, mode='edge'), np.ones(17) / 17, 'valid')
fb = ok4 & (r4 > 3.5); Ab = np.c_[np.ones(fb.sum()), (x4[fb] - gL.cx) / gL.R, (y4[fb] - gL.cy) / gL.R]
cb, *_ = np.linalg.lstsq(Ab, (l4 - prof[ib])[fb], rcond=None)
cel_b = lambda x, y: ccel[0] + cb[1] * (x - gL.cx) / gL.R + cb[2] * (y - gL.cy) / gL.R
mc = ok4 & (r4 * K76 > 7.5); vc = l4[mc]; lo_, hi_ = np.percentile(vc, [5, 95]); mmc = (vc > lo_) & (vc < hi_)
Ac = np.c_[np.ones(mmc.sum()), (x4[mc][mmc] - gL.cx) / gL.R, (y4[mc][mmc] - gL.cy) / gL.R]
cc_, *_ = np.linalg.lstsq(Ac, vc[mmc], rcond=None)
cel_c = lambda x, y: cc_[0] + cc_[1] * (x - gL.cx) / gL.R + cc_[2] * (y - gL.cy) / gL.R
del l4, r4, x4, y4
Q = {}
for r0, adu in R76.items():
    m = (RR76 > r0) & (RR76 < r0 + 0.02) & np.isfinite(LUM)          # el mateix anell que research/76 (radis de 959″)
    yi, xi = np.nonzero(m)
    net = np.median(LUM[yi, xi] - cel(xi, yi))
    Q[r0] = float(net / adu)
del X
print('quocient unitats del llenç / ADU/s (research/76): ' + ', '.join(f'{k:.2f} R☉: {v:.4f}' for k, v in Q.items()))
# Q a 1,50 R☉: el cel hi pesa un 5 % i el perfil ja no és tan dret com a 1,10 (on 3 px de centre canvien la mediana uns quants %).
# Els altres radis (2–5 R☉: 1,16–1,23) en donen l'error; el d'1,10 R☉ (1,34) queda fora per la pendent.
QREF = float(Q[1.50])
sens = {'a: perfil per medianes (adoptat)': q15(cel), 'b: perfil per mitjanes d’1 px i suavitzat de 17 (hdr_corona_vixen)': q15(cel_b),
        'c: pla ajustat al cel a r > 7,5 R☉ (v1)': q15(cel_c)}
print('sensibilitat de Q(1,50) al cel: ' + '; '.join(f'{k}: {v:.4f}' for k, v in sens.items()))
FAC = 2.772e-11 / QREF                                                      # B/B☉ per unitat del llenç
print(f"Q adoptat (1,50 R☉): {QREF:.4f}; resta de radis {[round(v, 3) for k, v in Q.items() if k != 1.5]}; factor {FAC:.4e} B/B☉ per unitat")
del Rfull, PAfull, RR76, Y

# ---------------------------------------------------------------- 3. instruments
def c2_calibrat(fitxer):
    d, g, hd = carrega_lasco(fitxer)                      # (DN − OFFSET)/EXPTIME, geometria de la capçalera
    from astropy.time import Time
    mjd = Time(hd['date-obs'].replace('/', '-') + 'T' + hd['time-obs']).mjd
    calfac = (4.60403e-07 * mjd + 0.0374116) * 1e-10
    vig = fits.open(DADES / 'lasco_calib/c2vig_final.fts')[0].data.astype(np.float32)
    vig = np.clip(vig, 0, 100)
    return d * calfac * vig, g, calfac, mjd
c2, gC2, calfac, mjd = c2_calibrat('24038985.fts')
print(f"C2: MJD {mjd:.3f}, calfac {calfac:.5e} B/B☉ per DN/s")
kp, gKp = carrega_kcor('20260812_182932_kcor_l2_pb_avg_cropped.gif')
pb = 9e-7 * (kp / 255.0) ** 1.25
rK, _ = gKp.polar(*np.meshgrid(np.arange(512), np.arange(512)))
pb[(rK < 1.075) | (kp >= 254)] = np.nan
for (a, b, c, d) in [(0, 150, 0, 48), (395, 512, 0, 40), (0, 265, 462, 512), (340, 512, 462, 512)]: pb[c:d, a:b] = np.nan

# ---------------------------------------------------------------- 4. perfils per anell i casella d'1°
def perfil(img, g, r1, r2, dpa=1.0, nsub=4):
    pa = np.arange(0, 360, dpa / nsub) + dpa / (2 * nsub); rs = np.linspace(r1, r2, 12)
    RR, PP = np.meshgrid(rs, pa, indexing='ij')
    v = mostreja(img, g, RR, PP)                                        # (radis, angles fins)
    nb = int(round(360 / dpa))
    v = v.reshape(len(rs), nb, nsub).transpose(1, 0, 2).reshape(nb, -1)  # (caselles, radis × subangles)
    return np.nanmedian(v, axis=1)
Gb = np.where(np.isfinite(LUM), LUM, np.nan)
def nostra(r1, r2):
    # mateixa geometria; valors del llenç → B/B☉ (sense restar el cel)
    return perfil(Gb, gL, r1, r2) * FAC
def cel_anell(r1, r2):
    pa = np.arange(0.5, 360, 1.0); x, y = gL.px(np.full_like(pa, 0.5 * (r1 + r2)), pa)
    return cel(x, y) * FAC
pilar = (np.arange(0.5, 360, 1.0) >= 288)        # 288–360°, la mateixa màscara efectiva que a les correlacions (c2: 288–359,5°)

def regressio(x, y, nboot=400):
    ok = np.isfinite(x) & np.isfinite(y)
    xx_, yy_ = x[ok], y[ok]
    w = np.ones(ok.sum(), bool)
    for _ in range(4):
        f, s = np.polyfit(xx_[w], yy_[w], 1); res = yy_ - (f * xx_ + s); sd = 1.4826 * np.median(np.abs(res[w])); w = np.abs(res) < 3 * sd
    # incertesa per blocs de 10° (les caselles veïnes no són independents)
    idx = np.nonzero(ok)[0]; blocs = idx // 10; ub = np.unique(blocs); rng = np.random.default_rng(1); fb = []
    for _ in range(nboot):
        tria = rng.choice(ub, len(ub)); sel = np.concatenate([np.nonzero(blocs == b)[0] for b in tria]); sel = sel[w[sel]]
        if len(sel) > 10: fb.append(np.polyfit(xx_[sel], yy_[sel], 1))
    fb = np.array(fb)
    rho = float(np.corrcoef(xx_[w], yy_[w])[0, 1])
    return dict(f=float(f), s=float(s), f_err=float(fb[:, 0].std()), s_err=float(fb[:, 1].std()), rho=rho, n=int(w.sum()))

res = {'Q_unitats_per_ADU_s': Q, 'Q_adoptat': QREF, 'Q_sensibilitat_cel': sens, 'factor_BBsol_per_unitat': FAC, 'cel_unitats': ccel.tolist(),
       'cel_BBsol_al_centre': float(ccel[0] * FAC), 'c2_calfac': calfac, 'c2_mjd': mjd, 'anells_c2': {}, 'anells_kcor': {}}
print(f"cel al centre del Sol: {ccel[0] * FAC:.3e} B/B☉ = {-2.5 * np.log10(ccel[0] * FAC) - 10.60:.2f} mag/arcsec² (V, aprox.)")
prof = {}
for r1, r2 in [(2.4, 2.6), (2.6, 2.9), (2.9, 3.3), (3.3, 3.8), (3.8, 4.5), (4.5, 5.5)]:
    y = nostra(r1, r2) - cel_anell(r1, r2); x = perfil(c2, gC2, r1, r2); x[pilar] = np.nan
    parell = np.isfinite(x) & np.isfinite(y)
    rg = regressio(x, y); rg['cel_nostre_mesurat'] = float(np.nanmedian(cel_anell(r1, r2)))
    rg['pendent_sense_restar_pla'] = regressio(x, nostra(r1, r2))['f']
    rg['mediana_C2'] = float(np.median(x[parell])); rg['mediana_nostra_menys_cel'] = float(np.median(y[parell])); rg['caselles'] = int(parell.sum())
    res['anells_c2'][f'{r1}-{r2}'] = rg; prof[f'c2_{r1}-{r2}'] = (x, y)
    print(f"C2   r {r1}–{r2}: f = {rg['f']:.3f} ± {rg['f_err']:.3f} (sense restar el pla {rg['pendent_sense_restar_pla']:.3f}); s = {rg['s']:.2e} ± {rg['s_err']:.1e} (cel mesurat {rg['cel_nostre_mesurat']:.2e}); ρ {rg['rho']:.3f}; "
          f"mediana C2 {rg['mediana_C2']:.2e}, nostra−cel {rg['mediana_nostra_menys_cel']:.2e}")
for r1, r2 in [(1.10, 1.15), (1.15, 1.25), (1.25, 1.40)]:
    y = nostra(r1, r2) - cel_anell(r1, r2); x = perfil(pb, gKp, r1, r2)
    parell = np.isfinite(x) & np.isfinite(y)
    rg = regressio(x, y); rg['mediana_pB'] = float(np.median(x[parell])); rg['mediana_nostra_menys_cel'] = float(np.median(y[parell])); rg['caselles'] = int(parell.sum())
    res['anells_kcor'][f'{r1}-{r2}'] = rg; prof[f'kcor_{r1}-{r2}'] = (x, y)
    print(f"K-Cor r {r1}–{r2}: g = {rg['f']:.2f} ± {rg['f_err']:.2f} (≈ 1/p); s' = {rg['s']:.2e}; ρ {rg['rho']:.3f}; mediana pB {rg['mediana_pB']:.2e}, nostra−cel {rg['mediana_nostra_menys_cel']:.2e}")

# ---------------------------------------------------------------- 5. grau de polarització teòric de la corona K
def coef(r):
    s = 1.0 / r; c = np.sqrt(np.clip(1 - s * s, 0, 1)); L = np.log((1 + s) / np.maximum(c, 1e-12))
    A = c * s * s
    B = -(1 / 8) * (1 - 3 * s * s - (c * c / s) * (1 + 3 * s * s) * L)
    C = 4 / 3 - c - c ** 3 / 3
    D = (1 / 8) * (5 + s * s - (c * c / s) * (5 - s * s) * L)
    return A, B, C, D
MODELS = {'Baumbach–Allen': lambda r: 2.99 * r ** -16 + 1.55 * r ** -6 + 0.036 * r ** -1.5,
          'Saito (equador)': lambda r: 3.09 * r ** -16 + 1.58 * r ** -6 + 0.0251 * r ** -2.5,
          'serpentí (n ∝ r⁻⁴)': lambda r: r ** -4.0}
def polaritzacio(rho, model, u=0.56):
    z = np.linspace(0, 20, 20001); r = np.sqrt(rho ** 2 + z ** 2); A, B, C, D = coef(r); n = model(r)
    It = np.trapezoid(n * ((1 - u) * C + u * D), z); pB_ = np.trapezoid(n * (rho / r) ** 2 * ((1 - u) * A + u * B), z)
    return pB_ / (2 * It - pB_)
teo = {nom: {f'{rho:.3f}': float(polaritzacio(rho, m)) for rho in (1.125, 1.20, 1.325, 1.5, 2.0, 2.5, 3.0)} for nom, m in MODELS.items()}
res['p_teoric_u056'] = teo
for nom, t in teo.items(): print(f"p teòric {nom}: " + ', '.join(f'{k}: {v:.3f}' for k, v in t.items()))

# ---------------------------------------------------------------- 6. perfils mitjans en funció del radi (per a la figura)
rads = np.round(np.geomspace(1.08, 6.0, 40), 3); mit = dict(r=rads.tolist(), nostra_menys_cel=[], c2=[], pB=[])
mit['nostra_aparellada_c2'] = []; mit['nostra_aparellada_pB'] = []
for r0 in rads:                                       # revisió 2 de Codex: cada parell de corbes, sobre les mateixes caselles d'angle
    r1, r2 = r0 * 0.985, r0 * 1.015
    y = nostra(r1, r2) - cel_anell(r1, r2); mit['nostra_menys_cel'].append(float(np.nanmedian(y)))
    x = perfil(c2, gC2, r1, r2) if r1 > 2.3 else np.full(360, np.nan); x[pilar] = np.nan
    pc = np.isfinite(x) & np.isfinite(y)
    mit['c2'].append(float(np.median(x[pc])) if pc.sum() > 20 else None); mit['nostra_aparellada_c2'].append(float(np.median(y[pc])) if pc.sum() > 20 else None)
    p_ = perfil(pb, gKp, r1, r2) if r2 < 1.48 else np.full(360, np.nan)
    pk = np.isfinite(p_) & np.isfinite(y)
    mit['pB'].append(float(np.median(p_[pk])) if pk.sum() > 20 else None); mit['nostra_aparellada_pB'].append(float(np.median(y[pk])) if pk.sum() > 20 else None)
res['perfils_mitjans'] = mit
json.dump(res, open(OUT / 'C9_BRILLANTOR.json', 'w'), indent=1, ensure_ascii=False)
np.savez_compressed(OUT / 'C9_perfils_anells.npz', **{k: np.vstack(v) for k, v in prof.items()})
print('fet')
