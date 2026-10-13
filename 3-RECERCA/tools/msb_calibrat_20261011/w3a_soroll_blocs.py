"""w3a · Soroll mesurat sense dependre de la correlació entre píxels veïns (v2, 12-10-2026). Escriu v2/mapa/soroll/SOROLL_BLOCS.json.

Per què: la v1 deia que SIGMA_STAT és una «cota alta» perquè la MAD de (MSB − mediana 5×5) en surt 0,1–0,4 vegades. Però el compost
porta interpolació (desmosaic, registre subpíxel, pas al llenç): els píxels veïns estan correlacionats i aquest estimador subestima
el soroll. No hi ha dues meitats independents de l'apilat a la cau (només el total de cada tren).
Prova (predeclarada aquí, abans de córrer-la): soroll de les MITJANES de blocs b×b (b = 1, 2, 4, 8, 16, 32 px del llenç) mesurat
amb la segona diferència entre blocs veïns, d = m(i−1) − 2·m(i) + m(i+1), en files i en columnes: σ_b = 1,4826·MAD(d)/√6.
La segona diferència treu el pla del cel; per sobre de la longitud de correlació, les mitjanes de blocs veïns són independents.
Predicció de la v1 (píxels independents): σ_pred,b = √(⟨σ_px²⟩)/b, amb σ_px = κ·√(wv²·vV + ws²·vS)·G (ADU/s de G_cam).
Quocient ρ_b = σ_b/σ_pred,b. Si ρ_b ≤ 1 a b ≥ 8 (més enllà de la correlació), SIGMA_STAT és una cota alta per a les mitjanes
d'aquesta mida en aquella zona; si ρ_b > 1, no ho és. L'estructura real del cel (estrelles febles, textura) només pot fer pujar ρ.
Zones: r ≥ 8 R☉ (cel; Sony·ρ) i 6 ≤ r < 8 R☉; píxels vàlids, fora del fantasma, de la franja lunar i de les estrelles (residu > 6σ).
Longitud de correlació: autocorrelació del residu (G − mediana 9×9) a desplaçaments d'1 a 6 px."""
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as nd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import msb_comu as mc          # noqa: E402
import msb_comu_v2 as m2       # noqa: E402

T0 = time.time()
OUT = m2.MAPA2 / 'soroll'; OUT.mkdir(parents=True, exist_ok=True)
cau = mc.obre_cau()
g = mc.geo_llenc()
xl = int(mc.SOL_XY[0] - 6.0 * mc.RSOL_PX); xr = int(mc.SOL_XY[0] + 6.0 * mc.RSOL_PX)
# dues franges verticals senceres (esquerra i dreta), on hi ha r ≥ 6 R☉ a tota l'alçada
FR = {'esquerra': (0, xl), 'dreta': (xr, mc.W)}
BS = (1, 2, 4, 8, 16, 32)
res = {'guio': 'w3a_soroll_blocs.py', 'data_execucio': time.strftime('%Y-%m-%dT%H:%M:%S'), 'blocs_px': BS, 'zones': {}}
acum = {z: {b: dict(dx=[], dy=[], pred=[]) for b in BS} for z in ('r_ge_8', 'r_6_8')}
acf = {z: {L: [] for L in range(1, 7)} for z in ('r_ge_8', 'r_6_8')}
for nom, (xa, xb) in FR.items():
    F = np.asarray(cau['fusion_total_v42'][:, xa:xb], np.float32)
    sup = np.asarray(cau['support_v42'][:, xa:xb])
    wv = np.asarray(cau['weight_vixen_v42'][:, xa:xb], np.float64)
    vV = np.asarray(cau['var_vixen_v42'][:, xa:xb], np.float64)
    vS = np.asarray(cau['var_sony_v42'][:, xa:xb], np.float64)
    yy, xx = np.mgrid[0:mc.H, xa:xb].astype(np.float64)
    r, pa = g.polar(xx, yy)
    dada = sup & np.all(np.isfinite(F), 2) & np.all(F > 0, 2)
    G = np.where(dada, mc.verd_camera(F), np.nan)
    del F
    ws = np.where(np.isfinite(vS), 1.0 - wv, 0.0)
    vf = np.where(wv > 0, wv * wv * vV, 0.0) + np.where(ws > 0, ws * ws * vS, 0.0)
    sig = mc.KAPPA_DOG * np.sqrt(vf) * G
    del vV, vS, ws, vf
    Gf = np.where(dada, G, 0.0)
    resid = G - nd.median_filter(Gf, size=9)
    ok0 = dada & np.isfinite(sig) & (np.hypot(xx - mc.GHOST_XY[0], yy - mc.GHOST_XY[1]) >= mc.GHOST_R_PX) & \
        (np.hypot(xx - mc.LLUNA_XY[0], yy - mc.LLUNA_XY[1]) >= mc.R_BANDA_PX)
    sdr = 1.4826 * np.nanmedian(np.abs(resid[ok0 & (r >= 6)] - np.nanmedian(resid[ok0 & (r >= 6)])))
    star = nd.binary_dilation(ok0 & (np.abs(resid) > 6 * sdr), iterations=4)
    for zn, zm in (('r_ge_8', r >= 8.0), ('r_6_8', (r >= 6.0) & (r < 8.0))):
        ok = ok0 & ~star & zm
        # autocorrelació del residu (files), normalitzada
        rz = np.where(ok, resid, np.nan)
        for L in range(1, 7):
            a, b_ = rz[:, :-L], rz[:, L:]
            mm = np.isfinite(a) & np.isfinite(b_)
            if mm.sum() > 1000:
                acf[zn][L].append((np.sum(a[mm] * b_[mm]), np.sqrt(np.sum(a[mm] ** 2) * np.sum(b_[mm] ** 2)), int(mm.sum())))
        for b in BS:
            hb, wb = mc.H // b, (xb - xa) // b
            Gc = G[:hb * b, :wb * b].reshape(hb, b, wb, b)
            okc = ok[:hb * b, :wb * b].reshape(hb, b, wb, b).all(axis=(1, 3))
            m = np.where(okc, np.nanmean(Gc, axis=(1, 3)), np.nan)
            s2 = np.where(okc, np.nanmean((sig[:hb * b, :wb * b] ** 2).reshape(hb, b, wb, b), axis=(1, 3)), np.nan)
            dx = m[:, :-2] - 2 * m[:, 1:-1] + m[:, 2:]
            dy = m[:-2, :] - 2 * m[1:-1, :] + m[2:, :]
            acum[zn][b]['dx'].append(dx[np.isfinite(dx)]); acum[zn][b]['dy'].append(dy[np.isfinite(dy)])
            acum[zn][b]['pred'].append(np.sqrt(s2[np.isfinite(s2)]) / b)
    print(f'{nom} fet ({time.time() - T0:.0f} s)', flush=True)
    del G, Gf, resid, sig, r, pa, xx, yy, dada, star, ok0, wv, sup

for zn in acum:
    z = {}
    for b in BS:
        dx = np.concatenate(acum[zn][b]['dx']); dy = np.concatenate(acum[zn][b]['dy']); pr = np.concatenate(acum[zn][b]['pred'])
        if dx.size < 50 or dy.size < 50:
            z[str(b)] = dict(n=int(min(dx.size, dy.size)), nota='massa pocs blocs')
            continue
        sx = 1.4826 * np.median(np.abs(dx - np.median(dx))) / np.sqrt(6); sy = 1.4826 * np.median(np.abs(dy - np.median(dy))) / np.sqrt(6)
        sp_ = float(np.median(pr))
        z[str(b)] = dict(n_dx=int(dx.size), n_dy=int(dy.size), sigma_mesurada_files_adu=float(sx), sigma_mesurada_columnes_adu=float(sy),
                         sigma_predita_independents_adu=sp_, rho_files=float(sx / sp_), rho_columnes=float(sy / sp_))
    ac = {}
    for L, lst in acf[zn].items():
        if lst:
            num = sum(t[0] for t in lst); den = sum(t[1] for t in lst)
            ac[str(L)] = float(num / den)
    z['autocorrelacio_residu_files'] = ac
    res['zones'][zn] = z
    print(zn, json.dumps({k: (round(v['rho_files'], 3), round(v['rho_columnes'], 3)) for k, v in z.items() if isinstance(v, dict) and 'rho_files' in v}),
          'acf', {k: round(v, 3) for k, v in ac.items()}, flush=True)
# conclusió (regla predeclarada al docstring)
conc = {}
for zn, z in res['zones'].items():
    rr = [max(z[str(b)]['rho_files'], z[str(b)]['rho_columnes']) for b in (8, 16, 32) if 'rho_files' in z.get(str(b), {})]
    conc[zn] = dict(rho_max_b8_32=float(max(rr)) if rr else None,
                    cota_alta_per_a_mitjanes_b_ge_8=bool(rr and max(rr) <= 1.0))
res['conclusio'] = conc
res['temps_s'] = time.time() - T0
json.dump(res, open(OUT / 'SOROLL_BLOCS.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(conc, ensure_ascii=False), f'fet en {time.time() - T0:.0f} s')
