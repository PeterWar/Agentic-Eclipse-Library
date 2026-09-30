"""w1 (verificador adversari 2, V108 marrons) · C del flat 2D v2 i el disc del centre del sensor, amb codi propi (només lectura).
 1. FLAT_RADIAL de la cadena: calaix central (r < 17 px del RAW) contra l'anell 19–25 px, per canal CFA; i el màster de flats mateix (mediana
    de 9 flats, sense dark: la forma relativa disc/anell no en depèn a l'1 ‰) al mateix disc i anell.
 2. C v2 per canal: p1/p50/p99, màxim i píxels > 3 % a ≥ 100 px de la vora visible; disc central; i, a la Sony, perfil radial de C al voltant
    del centre del sensor per veure si l'empalmament a r_ext = 180 px deixa un graó.
 3. Apilat A de la Sony a (4881, 2549) (centre del sensor d'A al llenç): disc r < 20 px contra anell 35–60 px, control / v2 / pilot; i perfil
    radial de ln(v2/control) de 0 a 600 px (anell a l'empalmament?).
Sortida: 4-RESULTATS/v108_20260926/verifica2_marrons/W1_C_I_DISC.json"""
import json, glob
from pathlib import Path
import numpy as np, rawpy, cv2
from astropy.io import fits
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica2_marrons'; OUT.mkdir(parents=True, exist_ok=True)
RI = A / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/raw_inputs'; CAL = A / '4-RESULTATS/v97_refundacio_20260924/cadena_raw'
F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; PI = A / '4-RESULTATS/v108_20260926/marrons/pilot'
R = {}
for tren in ('VIXEN', 'SONYTOT'):
    fl = sorted((RI / tren / 'flats').glob('*'))
    with rawpy.imread(str(fl[0])) as r:
        sz = r.sizes; pat = r.raw_pattern.copy(); desc = r.color_desc.decode(); h, w = r.raw_image.shape
    M = np.median(np.stack([rawpy.imread(str(f)).raw_image.astype(np.float32) for f in fl[:9]]), 0)
    FR = fits.getdata(CAL / f'calibration_{tren}/0-calibracio/FLAT_RADIAL.fits').astype(np.float32)
    C = np.load(F2 / f'flat2d/{tren}_flat2d_v2.npz')['C']
    Cp = np.load(A / f'4-RESULTATS/v108_20260926/marrons/flat2d/{tren}_flat2d.npz')['C']
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); rad = np.hypot(yy - h / 2, xx - w / 2)
    T_, L_ = sz.top_margin, sz.left_margin; B_, R_ = T_ + sz.height, L_ + sz.width
    dv = np.minimum(np.minimum(yy - T_, (B_ - 1) - yy), np.minimum(xx - L_, (R_ - 1) - xx)); del yy, xx
    res = dict(forma=[h, w], canals={})
    for oy in range(2):
        for ox in range(2):
            nm = desc[pat[oy, ox]] + str(pat[oy, ox]); sl = (slice(oy, None, 2), slice(ox, None, 2))
            rr = rad[sl]; d = dv[sl]; fr = FR[sl]; c = C[sl]; m = M[sl]
            disc = rr < 17; ane = (rr >= 19) & (rr < 25); lliure = d >= 100
            x = c[lliure] - 1
            prof = []
            for r0 in range(0, 400, 10):
                k = (rr >= r0) & (rr < r0 + 10); prof.append([r0, float(np.mean(c[k] - 1))])
            res['canals'][nm] = dict(
                FLAT_RADIAL_disc=float(fr[disc].mean()), FLAT_RADIAL_anell=float(fr[ane].mean()), exces_a_la_dada_pc=float(100 * (fr[ane].mean() / fr[disc].mean() - 1)),
                master_disc_sobre_anell_pc=float(100 * (m[disc].mean() / m[ane].mean() - 1)),
                C_p1_p50_p99_pc=(100 * np.percentile(x, [1, 50, 99])).round(3).tolist(), C_max_abs_pc=float(100 * np.abs(x).max()), n_sobre_3pc=int((np.abs(x) > 0.03).sum()),
                C_disc_r20_ppm=float(1e4 * np.mean(c[rr < 20] - 1)), C_max_abs_zona_vora_pc=float(100 * np.abs(c[(d < 100) & (d >= 0)] - 1).max()),
                C_perfil_radial_mitja_ppm_cada_10px=[[p[0], round(1e4 * p[1], 2)] for p in prof],
                C_pilot_disc_r20_pc=(None if Cp is None else float(100 * np.mean(Cp[sl][rr < 20] - 1))))
    R[tren] = res; print(tren, json.dumps({k: {kk: v[kk] for kk in ('FLAT_RADIAL_disc', 'FLAT_RADIAL_anell', 'exces_a_la_dada_pc', 'master_disc_sobre_anell_pc', 'C_p1_p50_p99_pc', 'C_max_abs_pc', 'n_sobre_3pc', 'C_disc_r20_ppm', 'C_pilot_disc_r20_pc')} for k, v in res['canals'].items()}), flush=True)
    del M, FR, C, rad, dv
# ---- 3. apilat A de la Sony al centre del sensor
X0, Y0 = 4881, 2549; W = 700
def talla(p):
    a = np.load(p, mmap_mode='r'); return np.asarray(a[Y0 - W:Y0 + W, X0 - W:X0 + W, 1], np.float64)
ims = dict(control=talla(A / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy'), v2=talla(F2 / 'apilats/sony_A_total.npy'), pilot=talla(PI / 'flat2d/sony_A_total.npy'))
yy, xx = np.mgrid[-W:W, -W:W]; rr = np.hypot(yy, xx)
disc = {k: float(np.nanmean(v[rr < 20]) / np.nanmean(v[(rr >= 35) & (rr < 60)]) - 1) for k, v in ims.items()}
# nul: el mateix disc/anell a 12 posicions a 400 px (control), per saber el gra de la mesura
nul = []
for ang in range(0, 360, 30):
    cx, cy = int(W + 400 * np.cos(np.radians(ang))), int(W + 400 * np.sin(np.radians(ang))); r2 = np.hypot(yy - (cy - W), xx - (cx - W))
    v = ims['control']; nul.append(float(np.nanmean(v[r2 < 20]) / np.nanmean(v[(r2 >= 35) & (r2 < 60)]) - 1))
lr = np.log(ims['v2'] / ims['control']); lp = np.log(ims['pilot'] / ims['control'])
prof = []
for r0 in range(0, 640, 8):
    k = (rr >= r0) & (rr < r0 + 8) & np.isfinite(lr); prof.append([r0, round(1e4 * float(np.nanmedian(lr[k])), 2), round(1e4 * float(np.nanmedian(lp[k])), 2)])
R['apilat_A_centre_sensor'] = dict(centre=[X0, Y0], disc_r20_sobre_anell_35_60=disc, nul_12_posicions_control=dict(mediana=float(np.median(nul)), max_abs=float(np.max(np.abs(nul)))),
                                   perfil_ln_v2_sobre_control_i_pilot_sobre_control_ppm=prof)
print('DISC', disc, 'nul', np.round(nul, 4).tolist(), flush=True)
print('PERFIL (r, v2 ‱, pilot ‱)', prof[::3], flush=True)
(OUT / 'W1_C_I_DISC.json').write_text(json.dumps(R, ensure_ascii=False, indent=1))
