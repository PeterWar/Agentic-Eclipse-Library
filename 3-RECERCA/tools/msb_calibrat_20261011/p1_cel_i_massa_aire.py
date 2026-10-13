"""p1 · Cel i massa d'aire del mapa MSB (11-10-2026). Escriu mapa/CEL.json, mapa/massa_aire_graella.npz i mapa/PROVES_P1.json.

CEL, en ADU/s del verd natiu G_cam, sobre el compost submostrejat 4× (un píxel de cada 4×4; el cel és suau).
Tres models PREDECLARATS (abans de mirar cap resultat del mapa):
  a) constant: mediana de G_cam a r > 7,29 R☉ (= r76 > 7,2, com c9 i research/76);
  b) constant + pla (ADOPTAT): la constant d'(a) i els gradients ajustats per mínims quadrats al residu de G_cam menys el
     perfil azimutal (medianes en anells de 0,02·K76) a r > 3,546 R☉ (= r76 > 3,5), com c9_brillantor.py:43-56;
  c) quadràtic en x, y (6 termes), ajustat directament a G_cam a 4 R☉ < r < cercle inscrit, amb 4 rondes de retall a 3σ (MAD).
Màscares comunes als tres: dada vàlida, fantasma de la Sony (320 px), estrelles (residu > 6σ sobre una mediana de 9×9 del
submostreig, dilatat 2 px del submostreig = 8 px), protuberàncies (no hi arriben). La dispersió entre models és la incertesa
del cel, amb un terra d'1e-9 B☉ (msb_comu.SIGMA_SKY_FLOOR_BSOL).

MASSA D'AIRE: graella exacta d'astropy cada 64 px del llenç (altura refractada, T 20 °C, P 930 hPa, 0,55 µm, com zp.py),
DATE-OBS 18:29:34, i spline bicúbica. Es comprova contra astropy a 3.000 píxels a l'atzar i amb la variant geomètrica."""
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as nd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import msb_comu as mc

T0 = time.time()
rep = {'guio': 'p1_cel_i_massa_aire.py', 'data_execucio': time.strftime('%Y-%m-%dT%H:%M:%S')}
Z = mc.zones()
RINS = float(Z['R_inscrit_Rsol'])
cau = mc.obre_cau()
F = cau['fusion_total_v42']; sup = cau['support_v42']
s = 4
f = np.asarray(F[::s, ::s], np.float64)
sp = np.asarray(sup[::s, ::s])
yy, xx = np.mgrid[0:mc.H:s, 0:mc.W:s].astype(np.float64)
g = mc.geo_llenc()
r, pa = g.polar(xx, yy)
u = (xx - mc.SOL_XY[0]) / mc.RSOL_PX; v = (yy - mc.SOL_XY[1]) / mc.RSOL_PX
dada = sp & np.all(np.isfinite(f), 2) & np.all(f > 0, 2)
G = np.where(dada, mc.verd_camera(f), np.nan)
del f
print(f'submostreig {G.shape} ({time.time() - T0:.0f} s)', flush=True)

# ---------------------------------------------------------------- màscares
ghost = np.hypot(xx - mc.GHOST_XY[0], yy - mc.GHOST_XY[1]) < mc.GHOST_R_PX
Gf = np.where(dada, G, 0.0)
medf = nd.median_filter(Gf, size=9)
res = np.where(dada, G - medf, np.nan)
zona_soroll = dada & (r > 3.0) & ~ghost
sd = 1.4826 * np.nanmedian(np.abs(res[zona_soroll] - np.nanmedian(res[zona_soroll])))
est = dada & (r > 2.0) & (res > 6 * sd)
est = nd.binary_dilation(est, iterations=2)
prom = np.zeros_like(dada)
for p0, dpa in mc.PROM_SECTORS:
    prom |= (np.abs((pa - p0 + 180) % 360 - 180) <= dpa) & (r < mc.PROM_RMAX)
valid = dada & ~ghost & ~est & ~prom & (np.hypot(xx - mc.LLUNA_XY[0], yy - mc.LLUNA_XY[1]) >= mc.R_BANDA_PX)
rep['mascares'] = dict(submostreig=s, sigma_residu_estrelles_adu=float(sd), pixels_estrella_submostreig=int(est.sum()),
                       pixels_fantasma_submostreig=int((ghost & dada).sum()), pixels_valids=int(valid.sum()))
print('màscares', rep['mascares'], flush=True)

# ---------------------------------------------------------------- (a) constant
K76 = 959.0 / mc.RSOL_ARCSEC
ma_ = valid & (r > 7.2 * K76)
c0 = float(np.median(G[ma_]))
# ---------------------------------------------------------------- (b) constant + pla sobre el residu del perfil azimutal
r76 = r / K76
edges = np.arange(1.0, 13.0, 0.02)
kb = np.digitize(r76, edges) - 1
okb = valid & (kb >= 0) & (kb < len(edges) - 1)
med = nd.median(G[okb], labels=kb[okb], index=np.arange(len(edges) - 1))
med = np.asarray(med, float)
cnt = np.bincount(kb[okb], minlength=len(edges) - 1)[:len(edges) - 1]
med[cnt < 30] = np.nan
rc = 0.5 * (edges[1:] + edges[:-1]); okm = np.isfinite(med)
base = np.interp(r76, rc[okm], med[okm])
fb = valid & (r76 > 3.5)
Ab = np.c_[np.ones(fb.sum()), u[fb], v[fb]]
cb, *_ = np.linalg.lstsq(Ab, (G - base)[fb], rcond=None)
# ---------------------------------------------------------------- (c) quadràtic directe a 4 R☉ < r < inscrit
fc = valid & (r > 4.0) & (r < RINS)
Ac = np.c_[np.ones(fc.sum()), u[fc], v[fc], u[fc] ** 2, u[fc] * v[fc], v[fc] ** 2]
yc = G[fc]; w = np.ones(fc.sum(), bool)
for it in range(4):
    cc, *_ = np.linalg.lstsq(Ac[w], yc[w], rcond=None)
    rr_ = yc - Ac @ cc; sdc = 1.4826 * np.median(np.abs(rr_[w] - np.median(rr_[w])))
    w = np.abs(rr_ - np.median(rr_[w])) < 3 * sdc
cc, *_ = np.linalg.lstsq(Ac[w], yc[w], rcond=None)
CEL = {'unitats': 'ADU/s del verd natiu de la càmera (G_cam), per píxel natiu de la R6; u = (x − cx)/R☉, v = (fila − cy)/R☉',
       'centre_px': mc.SOL_XY, 'R_sol_px': mc.RSOL_PX,
       'a': dict(c0=c0, regla='mediana de G_cam a r > 7,29 R☉ (r76 > 7,2), píxels vàlids', n=int(ma_.sum())),
       'b': dict(c0=c0, gu=float(cb[1]), gv=float(cb[2]), terme_independent_del_residu=float(cb[0]),
                 regla='constant d\'(a) + pla ajustat al residu G_cam − perfil azimutal (medianes, anells de 0,02·K76) a r > 3,546 R☉',
                 n=int(fb.sum())),
       'c': dict(coef=[float(x) for x in cc], regla='quadràtic 6 termes ajustat a G_cam a 4 R☉ < r < R_inscrit, 4 rondes 3σ MAD',
                 n=int(w.sum()), n_total=int(fc.sum()), rms_residu_adu=float(sdc)),
       'adoptat': 'b', 'sigma_floor_BSOL': mc.SIGMA_SKY_FLOOR_BSOL, 'sigma_floor_adu': mc.SIGMA_SKY_FLOOR_BSOL / mc.FAC_G,
       'R_inscrit_Rsol': RINS}
json.dump(CEL, open(mc.MAPA / 'CEL.json', 'w'), indent=1, ensure_ascii=False)

# diagnosi: valors al centre i al llarg dels eixos, en ADU/s i en B☉
mu_sol = -26.75 + 2.5 * np.log10(np.pi * mc.RSOL_ARCSEC ** 2)       # mag/arcsec² mitjana del disc solar (V)
diag = {}
for (nom, rr0, pa0) in [('centre', 0.0, 0.0), ('r3_zenit', 3.0, 33.2), ('r3_antizenit', 3.0, 213.2),
                        ('r5_zenit', 5.0, 33.2), ('r5_antizenit', 5.0, 213.2), ('r5_PA123', 5.0, 123.2), ('r5_PA303', 5.0, 303.2)]:
    x, y = g.px(rr0, pa0)
    vals = {m: float(mc.cel_model(x, y, m, CEL)) for m in ('a', 'b', 'c')}
    diag[nom] = dict(adu=vals, BSOL={m: vv * mc.FAC_G for m, vv in vals.items()},
                     mag_arcsec2_V_aprox={m: float(mu_sol - 2.5 * np.log10(vv * mc.FAC_G)) for m, vv in vals.items()})
CEL_diag = diag
# dispersió dels models a tot el camp del cercle inscrit (submostreig)
Sa, Sb, Sc = (mc.cel_model(xx, yy, m, CEL) for m in ('a', 'b', 'c'))
spread = np.maximum(np.abs(Sa - Sb), np.abs(Sc - Sb))
ins = r < RINS
rep['cel'] = dict(models=CEL, diagnosi=CEL_diag,
                  dispersio_adu_dins_inscrit=dict(p50=float(np.median(spread[ins])), p95=float(np.percentile(spread[ins], 95)),
                                                  max=float(spread[ins].max())),
                  dispersio_BSOL_p50=float(np.median(spread[ins]) * mc.FAC_G),
                  fraccio_on_mana_el_terra=float(np.mean(spread[ins] < mc.SIGMA_SKY_FLOOR_BSOL / mc.FAC_G)))
for rr0 in (1.5, 2.0, 3.0, 4.0, 5.0, 6.0):
    m = valid & (np.abs(r - rr0) < 0.05)
    rep['cel'][f'anell_{rr0}'] = dict(G_cam_mediana=float(np.median(G[m])), cel_b_mediana=float(np.median(Sb[m])),
                                      fraccio_cel=float(np.median(Sb[m]) / np.median(G[m])),
                                      dispersio_mediana_adu=float(np.median(spread[m])))
print(json.dumps(rep['cel'], indent=0, ensure_ascii=False)[:4000], flush=True)
del G, res, medf, Gf, Sa, Sb, Sc, spread

# ---------------------------------------------------------------- massa d'aire
t1 = time.time()
gr = mc.construeix_graella_massa_aire(pas=64, refractat=True)
np.savez_compressed(mc.MAPA / 'massa_aire_graella.npz', **gr, refractat=True, data=mc.DATE_OBS, pas=64)
print(f'graella de massa d\'aire {gr["alt"].shape} en {time.time() - t1:.0f} s', flush=True)
MA = mc.MassaAire()
rng = np.random.default_rng(11)
px_ = rng.uniform(0, mc.W - 1, 3000); py_ = rng.uniform(0, mc.H - 1, 3000)
h_ex, _ = mc.altures_astropy(px_, py_, refractat=True)
h_sp = MA.altura_punts(px_, py_)
h_geo, _ = mc.altures_astropy(px_, py_, refractat=False)
hs_geo, _ = mc.altura_sol(refractat=False)
X_ex = mc.kasten_young(h_ex); X_geo = mc.kasten_young(h_geo)
E_ref = mc.factor_extincio(X_ex, MA.X_sol); E_geo = mc.factor_extincio(X_geo, float(mc.kasten_young(hs_geo)))
rr_, _ = g.polar(px_, py_)
dins = rr_ < 6.0
rep['massa_aire'] = dict(
    convencio='altura aparent (refractada: T 20 °C, P 930 hPa, HR 0, 0,55 µm; com zp.py) i Kasten–Young 1989',
    data=mc.DATE_OBS, h_sol_refractada=MA.h_sol, X_sol=MA.X_sol, h_sol_geometrica=hs_geo, X_sol_geometrica=float(mc.kasten_young(hs_geo)),
    graella=dict(pas_px=64, forma=list(gr['alt'].shape), alt_min=float(gr['alt'].min()), alt_max=float(gr['alt'].max())),
    prova_spline=dict(n=3000, max_abs_err_altura_graus=float(np.max(np.abs(h_sp - h_ex))), max_abs_err_X=float(np.max(np.abs(mc.kasten_young(h_sp) - X_ex)))),
    variant_geometrica=dict(max_dif_E_relativa_dins_6Rsol=float(np.max(np.abs(E_geo[dins] / E_ref[dins] - 1))),
                            max_dif_E_relativa_tot_el_llenc=float(np.max(np.abs(E_geo / E_ref - 1)))),
    X_min_max_llenc=[float(X_ex.min()), float(X_ex.max())])
for rr0 in (1.5, 4.0, 6.0):
    for nom, p0 in (('zenit', 33.2072), ('antizenit', 213.2072)):
        x, y = g.px(rr0, p0)
        h = float(MA.altura_punts(np.array([x]), np.array([y]))[0]); X = float(mc.kasten_young(h))
        E = float(mc.factor_extincio(X, MA.X_sol))
        rep['massa_aire'][f'r{rr0:g}_{nom}'] = dict(h=h, X=X, X_menys_Xsol=X - MA.X_sol, E=E, E_pct=100 * (E - 1),
                                                    delta_mag=float(0.4 * (X - MA.X_sol)),
                                                    E_k035=float(mc.factor_extincio(X, MA.X_sol, 0.35)), E_k072=float(mc.factor_extincio(X, MA.X_sol, 0.72)))
print(json.dumps(rep['massa_aire'], indent=0, ensure_ascii=False), flush=True)
rep['temps_s'] = time.time() - T0
json.dump(rep, open(mc.MAPA / 'PROVES_P1.json', 'w'), indent=1, ensure_ascii=False, default=float)
print(f'fet en {time.time() - T0:.0f} s')
