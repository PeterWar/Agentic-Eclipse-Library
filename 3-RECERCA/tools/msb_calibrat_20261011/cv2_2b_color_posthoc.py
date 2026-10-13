"""cv2_2b · POST HOC (fet després de mirar cv2_2): el color per casella c = ln(MSB_G/MSB_R) contra la massa d'aire i la Fe XIV.
Comparacions v2, 12-10-2026.

Per què: a cv2_2, c(PA) té un patró gran que va del zenit (PA 33°, c alt) a l'antizenit (213°, c baix). És el que faria una
extinció diferent al verd i al vermell (k_G ≠ k_R), perquè el mapa corregeix els dos canals amb el mateix k = 0,40.
El forat coronal del sud (PA ~185°, AIA 211 mínim) cau a prop de l'antizenit: el traçador de la Fe XIV i la massa d'aire es
confonen. El dipol cos/sin predeclarat és una aproximació; aquí es fa servir la forma física, (X − X_ZP) per casella.

Model: c = a + κ·(X − X_ZP) [+ β·z], amb X − X_ZP = ln E(k 0,40)/(0,4·ln10·0,40) per casella. Si el mapa fa servir el mateix k
per als dos canals, κ = −0,4·ln10·(k_G − k_R). z = ln AIA 211 (Fe XIV) o ln pB (brillantor de la K), menys la mediana.
Errors amb bootstrap per blocs de 10° i 30°; β amb el nul de girs (30°–330°). Tot és INDICATIU (post hoc).
Escriu v2/comparacions/kcor/COLOR_POSTHOC_v2.json."""
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv2_comu as cv   # noqa: E402

T0 = time.time()
N = np.load(cv.RES2 / 'caselles_v2.npz')
K = np.load(cv.RES2 / 'kcor' / 'kcor_caselles_v2.npz')
AN = [tuple(a) for a in N['kcor_anells']]
pa_c = np.arange(0.5, 360, 1.0); pa_idx = np.arange(360)
C = 0.4 * np.log(10)


def ajust(c, cols, ok):
    A = np.c_[np.ones(ok.sum()), *[x[ok] for x in cols]]
    return np.linalg.lstsq(A, c[ok], rcond=None)[0]


res = {}
for i in range(cv.ANELLS_KCOR_US):
    k = f'{AN[i][0]}-{AN[i][1]}'
    us = N['kcor_usable'][i]
    with np.errstate(invalid='ignore', divide='ignore'):
        c = np.log(N['kcor_msb'][i] / N['kcor_msbR'][i])
        dX = np.log(N['kcor_E'][i]) / (C * 0.40)
        zA = np.log(K['aia211']) - np.nanmedian(np.log(K['aia211']))
        zP = np.log(K['pb_ref'][i]) - np.nanmedian(np.log(np.where(us, K['pb_ref'][i], np.nan)))
    ok = us & np.isfinite(c) & np.isfinite(dX) & np.isfinite(zA) & np.isfinite(zP)
    c = np.where(ok, c - np.nanmedian(c[ok]), np.nan)
    b0 = ajust(c, [dX], ok); kap = float(b0[1])
    # dipol de direcció lliure (informatiu)
    t = np.radians(pa_c)
    bd = ajust(c, [np.cos(t), np.sin(t)], ok)
    amp = float(np.hypot(bd[1], bd[2])); dirpa = float(np.degrees(np.arctan2(bd[2], bd[1])) % 360)
    out = dict(n=int(ok.sum()), kappa=kap, dk_G_menys_R=-kap / C, dipol_lliure=dict(amplitud=amp, PA_del_maxim=dirpa),
               rang_X_menys_XZP=[float(np.nanmin(dX[ok])), float(np.nanmax(dX[ok]))])
    for bloc in cv.BLOCS:
        kb = []
        pos = np.nonzero(ok)[0]
        for sel in cv.remostreigs(pa_idx[ok], bloc, 1000):
            o2 = np.zeros(360, bool); idx = pos[sel]
            A = np.c_[np.ones(len(idx)), dX[idx]]
            kb.append(np.linalg.lstsq(A, c[idx], rcond=None)[0][1])
        out[f'dk_err_blocs_{bloc}'] = float(np.std(kb) / C)
    resid = c - (b0[0] + kap * dX)
    out['dispersio_c_abans'] = float(1.4826 * np.nanmedian(np.abs(c[ok])))
    out['dispersio_residu'] = float(1.4826 * np.nanmedian(np.abs(resid[ok] - np.nanmedian(resid[ok]))))
    for nom, z in (('AIA211', zA), ('pB_KCor', zP)):
        b = ajust(c, [dX, z], ok); beta = float(b[2])
        nul = []
        for s in range(30, 331):
            zs = np.roll(z, s); o2 = ok & np.isfinite(zs)
            nul.append(ajust(c, [dX, zs], o2)[2])
        nul = np.array(nul)
        rz = resid[ok]; zz = z[ok]
        q_alt = np.median(rz[zz >= np.percentile(zz, 75)]) - np.median(rz[zz <= np.percentile(zz, 25)])
        out[f'traçador_{nom}'] = dict(beta=beta, p_girs=float((nul >= beta).mean()), nul_p50_p95=[float(np.median(nul)), float(np.percentile(nul, 95))],
                                      rang_z=[float(zz.min()), float(zz.max())], efecte_sobre_el_rang=float(beta * (zz.max() - zz.min())),
                                      residu_quartil_alt_menys_baix=float(q_alt))
    res[k] = out
    print(k, {kk: (round(v, 4) if isinstance(v, float) else v) for kk, v in out.items()}, flush=True)
cv.json_dump(dict(guio=cv.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'), caracter='POST HOC, indicatiu',
                  model='c = a + κ·(X − X_ZP) [+ β·z]; Δk = k_G − k_R = −κ/(0,4·ln10)', resultats=res,
                  entrades_sha256={cv.rel(cv.RES2 / 'caselles_v2.npz'): cv.sha256(cv.RES2 / 'caselles_v2.npz'),
                                   cv.rel(cv.RES2 / 'kcor' / 'kcor_caselles_v2.npz'): cv.sha256(cv.RES2 / 'kcor' / 'kcor_caselles_v2.npz')},
                  segons=round(time.time() - T0, 1)), cv.RES2 / 'kcor' / 'COLOR_POSTHOC_v2.json')
print(f'fet ({time.time() - T0:.0f} s)')
