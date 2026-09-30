"""w3 (V108 · verifica2_negres) · El ràster de la 41 per dins (pas 2, llenç sencer): Δu = candidat − cadena, i el genoll sol (candidat − CEL sol
si existeix). Proves: (1) EMPREMTA d'altres capes: correlació parcial del pas alt (6–64 px) de Δu amb el de ln F_altres (54·45·46, de la
cadena, amb alfes i màscares de la V107) descomptant el de u; (2) RADIS cada 10° (nusos de la interpolació del cel SEC): energia de la
2a derivada angular de Δu segons la fase θ mod 10°, contra el mateix per a u de la V107 (nul); (3) línia horitzontal a y = CY i salts;
(4) vistes del llenç sencer de Δu i del seu pas alt, per mirar anells, línies i costures. Ús: w3_raster.py [carpeta_candidat]"""
import sys, json, time
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import map_coordinates
sys.path.insert(0, str(Path(__file__).resolve().parent))
from w0_comu import *
T0 = time.time(); PAS = 2
CAND = Path(sys.argv[1]) if len(sys.argv) > 1 else R0 / '4-RESULTATS/v108_20260926/negres_v2/candidats_v4/CEL_G_MAX_T_e30_W_H0'
NOM = CAND.name
G = geo(pas=PAS); r, th, ok, marc, dl = G['r'], G['th'], G['ok'], G['marc'], G['dl']
def ld(p): return np.load(p, mmap_mode='r')[::PAS, ::PAS].astype(np.float32) / 65535
u0 = ld(STD / 'P01_NRGF_u16.npy'); u1 = ld(CAND / 'P01_NRGF_u16.npy'); du = u1 - u0; res = dict(candidat=str(CAND))
TAGS = {54: 'P03_MGN', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native'}
lF = np.zeros_like(u0)
for lid, tg in TAGS.items():
    a = alfa(lid, (0, 0, W, H), PAS); lF += np.log(np.maximum(1 - a * (1 - ld(STD / f'{tg}_u16.npy')), 1e-3))
def hp(x): return cv2.GaussianBlur(x, (0, 0), 1.5) - cv2.GaussianBlur(x, (0, 0), 16)
Hd, Hu, Hf = hp(du), hp(u0), hp(lF); emp = {}
for a_, b_ in ((2, 3), (3, 4.5), (4.5, 7), (7, 9.5)):
    m = ok & marc & (r >= a_) & (r < b_) & (dl > 60)
    X = np.stack([Hu[m], Hf[m], np.ones(m.sum(), np.float32)], 1); y = Hd[m]
    cf, *_ = np.linalg.lstsq(X, y, rcond=None); yhat = X @ cf
    # correlació parcial Δu ~ F_altres | u
    ru = lambda v: v - np.polyval(np.polyfit(Hu[m], v, 1), Hu[m])
    pc = float(np.corrcoef(ru(y), ru(Hf[m]))[0, 1])
    emp[f'{a_:g}-{b_:g}'] = dict(corr_parcial_dHu_Faltres=pc, coef_u_Faltres=[float(cf[0]), float(cf[1])], R2=float(1 - np.var(y - yhat) / np.var(y)),
                                 rms_hp_du_sobre_rms_hp_u=float(np.std(y) / np.std(Hu[m])))
res['empremta_altres_capes'] = emp; del Hd, Hu, Hf, lF
# (2) radis cada 10°: 2a derivada angular de Δu (suau) a anells de 2–5 R☉, segons la fase θ mod 10°
dus = cv2.GaussianBlur(du, (0, 0), 3); u0s = cv2.GaussianBlur(u0, (0, 0), 3)
rad = {}
for nom, img in (('du', dus), ('u_V107_nul', u0s)):
    acc = np.zeros(200); cnt = np.zeros(200)
    for rs in np.arange(2.0, 5.0, 0.05):
        n = 7200; t = np.linspace(0, 2 * np.pi, n, endpoint=False); R_ = rs * RSOL / PAS
        X = (SOL[0] / PAS + np.cos(t) * R_); Y = (SOL[1] / PAS - np.sin(t) * R_)
        v = map_coordinates(img, [Y, X], order=1, mode='nearest'); okv = map_coordinates(ok.astype(np.float32), [Y, X], order=1) > 0.999
        d2 = np.abs(np.roll(v, -20) - 2 * v + np.roll(v, 20)); okv &= np.roll(okv, 20) & np.roll(okv, -20)
        fase = ((np.degrees(t) % 10) / 10 * 200).astype(int) % 200
        np.add.at(acc, fase[okv], d2[okv]); np.add.at(cnt, fase[okv], 1)
    prof = acc / np.maximum(cnt, 1); rad[nom] = dict(perfil_20_fases=[float(x) for x in prof.reshape(20, 10).mean(1)], pic_a_5graus_sobre_mediana=float(prof[95:105].mean() / np.median(prof)))
res['radis_cada_10_graus'] = rad
# (3) línia horitzontal (y = CY) i perfil vertical a x = CX ± 2,5 R☉ i a les vores
pv = {}
for dx in (-3.5, -2.5, 2.5, 3.5, -6.0, 6.0):
    x = int((SOL[0] + dx * RSOL) / PAS); col = dus[:, x - 5:x + 5].mean(1); y0 = int(SOL[1] / PAS); seg = col[y0 - 60:y0 + 60]
    pv[f'{dx:g}R'] = dict(salt_max_2px=float(np.abs(np.diff(seg)).max()), d2_max=float(np.abs(np.diff(seg, 2)).max()), d2_mediana_fora=float(np.median(np.abs(np.diff(col[y0 - 400:y0 - 100], 2)))))
res['perfil_vertical_a_y_CY'] = pv
# (4) vistes
V = OUT / 'vistes'; V.mkdir(exist_ok=True)
def colors(x, lim, fons):
    t = np.clip(x / lim, -1, 1); o = np.zeros(x.shape + (3,), np.uint8)
    o[..., 2] = (255 * np.where(t > 0, 1, 1 + t)).astype(np.uint8); o[..., 0] = (255 * np.where(t < 0, 1, 1 - t)).astype(np.uint8); o[..., 1] = (255 * (1 - np.abs(t))).astype(np.uint8)
    o[~fons] = 60; return o
fons = (alfa(3, (0, 0, W, H), PAS) > 0.5)
cv2.imwrite(str(V / f'W3_{NOM}_du41_pm0.10.png'), colors(du, 0.10, fons))
cv2.imwrite(str(V / f'W3_{NOM}_du41_pm0.02.png'), colors(du, 0.02, fons))
h = cv2.GaussianBlur(du, (0, 0), 2) - cv2.GaussianBlur(du, (0, 0), 24)
cv2.imwrite(str(V / f'W3_{NOM}_du41_pasalt_4-48px_pm0.01.png'), colors(h, 0.01, fons))
res['segons'] = round(time.time() - T0)
(OUT / f'W3_{NOM}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n'); print('FET', res['segons'], 's')
