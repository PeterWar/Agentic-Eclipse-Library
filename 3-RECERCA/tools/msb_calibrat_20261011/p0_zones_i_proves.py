"""p0 · Zones i proves prèvies del mapa MSB (11-10-2026). Només llegeix la cau (mmap); escriu a resultats/msb_calibrat_20261011/mapa/.

1. Hashes de les entrades (contra B3_V42_FROZEN.json).
2. Color: M i wb de 572A2955.CR3 amb rawpy; color cru R/G i B/G de càmera a 1,05–1,3 R☉ (esperat 0,81 i ≈0,37).
3. Geometria: prova d'anada i tornada; massa d'aire del Sol (ha de reproduir el 6,024 de zp2.json); zenit.
4. Lluna: zona sense dada, buit de 2 px (desat), trajectòria de la Lluna (efemèride) contra les vores mesurades,
   i comprovació que la franja de 496 px conté tota la zona que la Lluna va tapar en algun moment.
5. Cercle inscrit (el més gran centrat al Sol amb dada a tot arreu).
6. Protuberàncies: excés de R/G de càmera per angle, per comprovar els sectors predeclarats.
Executar amb l'entorn que tingui numpy/scipy/astropy/rawpy (vegeu executa.sh), amb PYTHONDONTWRITEBYTECODE=1."""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as nd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import msb_comu as mc

T0 = time.time()
mc.MAPA.mkdir(parents=True, exist_ok=True)
rep = {'guio': 'p0_zones_i_proves.py', 'data_execucio': time.strftime('%Y-%m-%dT%H:%M:%S')}
cau_dir = mc.troba_cau()
rep['cau'] = str(cau_dir).replace(str(Path.home()), '~')

# ---------------------------------------------------------------- 1. hashes
hs = {}
for n, esperat in mc.SHA_CAU.items():
    if n in ('rho_v42.npy', 'sony_corrected_total_v42.npy'):
        continue                                            # no es fan servir al mapa
    got = mc.sha256(cau_dir / n)
    hs[n] = dict(sha256=got, igual_que_B3_V42_FROZEN=(got == esperat))
    if got != esperat:
        raise SystemExit(f'SHA diferent a {n}: {got}')
for f in (mc.CR3_MATRIU, mc._GEOF, mc._MARS, mc._ESTR, mc._ZPDIR / 'zp2.json', mc._ZPDIR / 'corona2.csv',
          mc._ZPDIR / 'final_solution.json', mc._GHOST_GEOM):
    hs[str(Path(f).relative_to(mc.ARREL))] = dict(sha256=mc.sha256(f))
rep['entrades_sha256'] = hs
print(f'hashes fets ({time.time() - T0:.0f} s)', flush=True)

# ---------------------------------------------------------------- 2. color
M, wb = mc.matrius_rawpy()
rep['color'] = dict(M_cam_a_sRGB=M.tolist(), M_inversa=np.linalg.inv(M).tolist(), wb_dia=wb.tolist(),
                    guany_CIENCIA=mc.GUANY_CIENCIA.tolist(), A_u_a_ucam=mc.matriu_inversa().tolist(),
                    coincideix_amb_constants=bool(np.allclose(M, mc.M_R6, atol=6e-5) and np.allclose(wb, mc.WB_R6, atol=6e-5)),
                    neutre_conservat=float(np.max(np.abs(M @ np.ones(3) - 1))))
cau = mc.obre_cau()
F = cau['fusion_total_v42']
g = mc.geo_llenc()
s = 2                                                   # submostreig 2× per a la prova de color (anell 1,05–1,3 R☉)
y0, y1 = int(mc.SOL_XY[1] - 1.35 * mc.RSOL_PX), int(mc.SOL_XY[1] + 1.35 * mc.RSOL_PX)
x0, x1 = int(mc.SOL_XY[0] - 1.35 * mc.RSOL_PX), int(mc.SOL_XY[0] + 1.35 * mc.RSOL_PX)
f = np.asarray(F[y0:y1:s, x0:x1:s], np.float64)
yy, xx = np.mgrid[y0:y1:s, x0:x1:s].astype(np.float64)
r, pa = g.polar(xx, yy)
ok = np.all(np.isfinite(f), 2) & np.all(f > 0, 2)
uc = mc.canals_camera(f)
rm = np.hypot(xx - mc.LLUNA_XY[0], yy - mc.LLUNA_XY[1])
res_c = {}
for nom, m in (('tot_1.05-1.30', ok & (r >= 1.05) & (r < 1.30)),
               ('sense_franja_1.05-1.30', ok & (r >= 1.05) & (r < 1.30) & (rm >= mc.R_BANDA_PX)),
               ('sense_franja_1.30-1.50', ok & (r >= 1.30) & (r < 1.50))):
    res_c[nom] = dict(R_sobre_G=float(np.median(uc[..., 0][m] / uc[..., 1][m])),
                      B_sobre_G=float(np.median(uc[..., 2][m] / uc[..., 1][m])), n=int(m.sum()))
rep['color']['prova_color_cru_camera'] = res_c
rep['color']['esperat'] = 'R/G ≈ 0,81 i B/G ≈ 0,37 (scout 0,812/0,375; research/76:286-287 0,816/0,361)'
t = res_c['tot_1.05-1.30']
rep['color']['passa'] = bool(abs(t['R_sobre_G'] - 0.81) < 0.02 and abs(t['B_sobre_G'] - 0.37) < 0.02)
print('color', res_c, flush=True)
del f, uc, xx, yy, r, pa, ok, rm

# ---------------------------------------------------------------- 3. geometria, massa d'aire del Sol i zenit
rep['geometria'] = dict(prova_geo=mc.prova_geo(), sol_xy=mc.SOL_XY, R_sol_px=mc.RSOL_PX, escala_arcsec_px=mc.SC,
                        R_sol_arcsec=mc.RSOL_ARCSEC, P_deg=mc.P_DEG, nord_solar=mc.NORD_SOLAR.tolist(), est_solar=mc.EST_SOLAR.tolist(),
                        lluna_xy=mc.LLUNA_XY, R_lluna_px=mc.R_LLUNA_PX, centres_alternatius=mc.SOL_ALTERNATIUS,
                        font='c9_brillantor.py:24-29 (Sol = sol_px_efemeride + OFF; nord i est solars de mars_final.json girats per P)')
ma = {}
for d in ('2026-08-12T18:29:18.6', mc.DATE_OBS, mc.DATE_BEG, mc.DATE_END):
    hr, az = mc.altura_sol(d, True); hg, _ = mc.altura_sol(d, False)
    ma[d] = dict(h_refractada=hr, X_refractada=float(mc.kasten_young(hr)), h_geometrica=hg, X_geometrica=float(mc.kasten_young(hg)), azimut=az)
rep['massa_aire_sol'] = ma
rep['massa_aire_sol']['reprodueix_zp2'] = dict(zp2_Xsun=mc.ZP_X_SOL, astropy_refractat_18_29_18_6=ma['2026-08-12T18:29:18.6']['X_refractada'],
                                               diferencia=ma['2026-08-12T18:29:18.6']['X_refractada'] - mc.ZP_X_SOL)
pa1 = np.arange(0, 360, 1.0)
for rr in (1.0, 4.0):
    x, y = g.px(np.full_like(pa1, rr), pa1)
    h, _ = mc.altures_astropy(x, y)
    A = np.c_[np.ones_like(pa1), np.cos(np.radians(pa1)), np.sin(np.radians(pa1))]
    c, *_ = np.linalg.lstsq(A, h, rcond=None)
    rep.setdefault('zenit', {})[f'r{rr:g}'] = dict(PA_solar_del_zenit=float(np.degrees(np.arctan2(c[2], c[1])) % 360),
                                                   amplitud_h_graus=float(np.hypot(c[1], c[2])),
                                                   r_en_graus=rr * mc.RSOL_ARCSEC / 3600)
# angle paral·làctic (com dipol.py del scout)
import astropy.units as u
from astropy.coordinates import EarthLocation, get_body
from astropy.time import Time
loc = EarthLocation(lat=mc.LLOC['lat'] * u.deg, lon=mc.LLOC['lon'] * u.deg, height=mc.LLOC['alt_m'] * u.m)
tt = Time(mc.DATE_OBS)
sun = get_body('sun', tt, loc)
lst = tt.sidereal_time('apparent', longitude=loc.lon)
Ha = (lst - sun.ra).wrap_at(180 * u.deg).rad; dec = sun.dec.rad; phi = loc.lat.rad
q = math.degrees(math.atan2(math.sin(Ha), math.tan(phi) * math.cos(dec) - math.sin(dec) * math.cos(Ha)))
rep['zenit']['angle_parallactic_q'] = q
rep['zenit']['PA_solar_zenit_q_menys_P'] = (q - mc.P_DEG) % 360
print('zenit', rep['zenit'], flush=True)

# ---------------------------------------------------------------- 4. Lluna: zona sense dada, buit, trajectòria
sup = cau['support_v42']
B = 760
ly0, lx0 = int(mc.LLUNA_XY[1]) - B, int(mc.LLUNA_XY[0]) - B
fb = np.asarray(F[ly0:ly0 + 2 * B, lx0:lx0 + 2 * B], np.float32)
sb = np.asarray(sup[ly0:ly0 + 2 * B, lx0:lx0 + 2 * B])
dada = sb & np.all(np.isfinite(fb), 2) & np.all(fb > 0, 2)
lab, nlab = nd.label(~dada)
lluna_nd = lab == lab[B, B]
dist = nd.distance_transform_edt(~lluna_nd)
gap = dada & (dist <= mc.GAP_PX)
np.savez_compressed(mc.MAPA / 'zona_lunar_gap.npz', x0=lx0, y0=ly0, mask=gap)
yy, xx = np.mgrid[ly0:ly0 + 2 * B, lx0:lx0 + 2 * B].astype(np.float64)
ey, ex = np.nonzero(lluna_nd & ~nd.binary_erosion(lluna_nd))
ex = ex + lx0; ey = ey + ly0
# trajectòria de la Lluna respecte del Sol (topocèntrica) en px del llenç, relativa a 18:28:49
moon_t = {}
for d in (mc.DATE_BEG, '2026-08-12T18:28:49', mc.DATE_OBS, mc.DATE_END):
    tq = Time(d); su = get_body('sun', tq, loc); mo = get_body('moon', tq, loc)
    dE = float(((mo.ra - su.ra).wrap_at(180 * u.deg)).to(u.arcsec).value * math.cos(su.dec.rad))
    dN = float((mo.dec - su.dec).to(u.arcsec).value)
    moon_t[d] = (dE, dN)
ref = moon_t['2026-08-12T18:28:49']
track = {}
for d, (dE, dN) in moon_t.items():
    v = ((dE - ref[0]) * mc.EST_CEL + (dN - ref[1]) * mc.NORD_CEL) / mc.SC
    track[d] = [float(mc.LLUNA_XY[0] + v[0]), float(mc.LLUNA_XY[1] + v[1])]
c2 = np.array(track[mc.DATE_BEG]); c3 = np.array(track[mc.DATE_END])
long_track = float(np.hypot(*(c3 - c2)))
# zona que la Lluna va tapar en algun moment (distància al segment C2–C3 < R☾) i la seva ala de 13,9 px
def dist_segment(px, py, a, b):
    ab = b - a; tpar = np.clip(((px - a[0]) * ab[0] + (py - a[1]) * ab[1]) / (ab @ ab), 0, 1)
    return np.hypot(px - (a[0] + tpar * ab[0]), py - (a[1] + tpar * ab[1]))
dseg = dist_segment(xx, yy, c2, c3)
ala = mc.R_BANDA_PX - mc.R_LLUNA_PX - 28.5
rmb = np.hypot(xx - mc.LLUNA_XY[0], yy - mc.LLUNA_XY[1])
fora = dada & (dseg < mc.R_LLUNA_PX + ala) & (rmb >= mc.R_BANDA_PX)
# vores mesurades contra predites: la zona sense dada ha de ser la intersecció dels discs (C2 ∩ C3)
ang = np.degrees(np.arctan2(ey - mc.LLUNA_XY[1], ex - mc.LLUNA_XY[0])) % 360
pred_int = np.maximum(np.hypot(ex - c2[0], ey - c2[1]), np.hypot(ex - c3[0], ey - c3[1]))   # >= R☾ a la vora de la intersecció
vores = {}
for a0 in range(0, 360, 30):
    m = (ang >= a0) & (ang < a0 + 30)
    vores[f'{a0}-{a0 + 30}'] = dict(r_vora_des_de_lluna_1828_49_med=float(np.median(rmb[ey - ly0, ex - lx0][m])),
                                   max_dist_als_centres_C2_C3_menys_Rlluna_med=float(np.median(pred_int[m] - mc.R_LLUNA_PX)))
rep['lluna'] = dict(pixels_sense_dada_zona_lunar=int(lluna_nd.sum()), pixels_buit_limbe_2px=int(gap.sum()),
                    trajectoria_px=track, longitud_C2_C3_px=long_track,
                    ala_franja_px=ala, franja_conte_tota_la_zona_tapada_mes_ala=bool(fora.sum() == 0),
                    pixels_tapats_fora_de_la_franja=int(fora.sum()), vores_zona_sense_dada=vores,
                    nota=('la vora de la zona sense dada ha de quedar ≈ 0–4 px per fora de la intersecció dels discs de C2 i C3 '
                          '(max dist als dos centres − R☾ ≈ 0–4 px)'))
print('lluna', json.dumps(rep['lluna'], indent=0)[:1500], flush=True)
del fb, sb, dada, lab, lluna_nd, dist, xx, yy, dseg, rmb

# ---------------------------------------------------------------- 5. cercle inscrit
rmin = np.inf; arg = None
for a in range(0, mc.H, 512):
    b = min(a + 512, mc.H)
    sbk = np.asarray(sup[a:b]); fbk = np.asarray(F[a:b, :, 1])
    nd_ = ~(sbk & np.isfinite(fbk) & (fbk > 0))
    yy, xx = np.nonzero(nd_)
    if len(yy) == 0:
        continue
    rr, _ = g.polar(xx.astype(np.float64), (yy + a).astype(np.float64))
    rr = np.where(rr < 1.25, np.inf, rr)                       # la Lluna no compta
    i = int(np.argmin(rr))
    if rr[i] < rmin:
        rmin = float(rr[i]); arg = (int(xx[i]), int(yy[i] + a))
dist_vores = [mc.SOL_XY[0], mc.W - 1 - mc.SOL_XY[0], mc.SOL_XY[1], mc.H - 1 - mc.SOL_XY[1]]
rep['cercle_inscrit'] = dict(R_inscrit_Rsol=float(min(rmin, min(dist_vores) / mc.RSOL_PX)),
                             R_primer_pixel_sense_dada_dins_del_llenç=rmin, primer_pixel_sense_dada=arg,
                             distancia_minima_a_les_vores_del_llenç_Rsol=float(min(dist_vores) / mc.RSOL_PX),
                             regla='el menor entre el primer píxel sense dada (fora de la Lluna) i la vora del llenç')
print('inscrit', rep['cercle_inscrit'], flush=True)

# ---------------------------------------------------------------- 6. protuberàncies (R/G de càmera per angle, 1,0–1,4 R☉, sense la Lluna)
s = 1
y0, y1 = int(mc.SOL_XY[1] - 1.45 * mc.RSOL_PX), int(mc.SOL_XY[1] + 1.45 * mc.RSOL_PX)
x0, x1 = int(mc.SOL_XY[0] - 1.45 * mc.RSOL_PX), int(mc.SOL_XY[0] + 1.45 * mc.RSOL_PX)
f = np.asarray(F[y0:y1, x0:x1], np.float64)
yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
r, pa = g.polar(xx, yy)
ok = np.all(np.isfinite(f), 2) & np.all(f > 0, 2) & np.asarray(sup[y0:y1, x0:x1])
uc = mc.canals_camera(f)
rg = np.where(ok, uc[..., 0] / uc[..., 1], np.nan)
rbins = [(1.00, 1.05), (1.05, 1.10), (1.10, 1.15), (1.15, 1.20), (1.20, 1.25), (1.25, 1.30), (1.30, 1.40)]
pab = np.floor(pa).astype(int) % 360
prom = {}
for (ra, rb) in rbins:
    m = ok & (r >= ra) & (r < rb)
    med = np.full(360, np.nan)
    sums = nd.median(rg[m], labels=pab[m], index=np.arange(360)) if m.any() else med
    med = np.asarray(sums, float)
    base = np.nanmedian(med)
    exc = med / base - 1
    prom[f'{ra:.2f}-{rb:.2f}'] = dict(mediana_RG=float(base),
                                      PA_amb_exces_gt_10pc=[int(p) for p in np.nonzero(exc > 0.10)[0]],
                                      exces_als_PA_predeclarats={str(int(p0)): float(np.nanmax(exc[[int((p0 + d) % 360) for d in range(-6, 7)]]))
                                                                 for p0 in mc.PROM_PA})
rep['protuberancies'] = dict(predeclarat=dict(PA=mc.PROM_PA, dPA=mc.PROM_DPA, rmax=mc.PROM_RMAX), sectors_finals=mc.PROM_SECTORS, per_anell=prom,
                             nota='excés de R/G de càmera (Hα) sobre la mediana de l\'anell, per graus d\'angle; inclou píxels de la franja lunar (només diagnòstic)')
print('prom', json.dumps(prom)[:3000], flush=True)
del f, uc, rg, xx, yy, r, pa, ok

# ---------------------------------------------------------------- desa
json.dump(dict(R_inscrit_Rsol=rep['cercle_inscrit']['R_inscrit_Rsol'], font='p0_zones_i_proves.py',
               R_banda_px=mc.R_BANDA_PX, gap_px=mc.GAP_PX, ghost_xy=mc.GHOST_XY, ghost_r_px=mc.GHOST_R_PX,
               prominencies=dict(PA=mc.PROM_PA, dPA=mc.PROM_DPA, rmax=mc.PROM_RMAX, sectors_finals=mc.PROM_SECTORS)),
          open(mc.MAPA / 'ZONES.json', 'w'), indent=1, ensure_ascii=False)
rep['temps_s'] = time.time() - T0
json.dump(rep, open(mc.MAPA / 'PROVES_P0.json', 'w'), indent=1, ensure_ascii=False, default=float)
print(f'fet en {time.time() - T0:.0f} s')
