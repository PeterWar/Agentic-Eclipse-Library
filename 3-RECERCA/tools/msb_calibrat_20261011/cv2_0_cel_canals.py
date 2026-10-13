"""cv2_0 · Cel per canal (R, G, B) amb la REGLA ADOPTADA a la v2 del mapa (b_new: constant + pla ajustats al canal a r ≥ 8 R☉,
4 rondes 3σ MAD, submostreig 4×, les mateixes màscares que w1_cel_v2.py: estrelles del verd, fantasma, protuberàncies, franja).
Comparacions v2, 12-10-2026. PREDECLARAT: la regla és la de w1 (no es tria res aquí); el verd ha de reproduir CEL_v2.json b_new.
El vermell serveix per a la prova de banda i per a la regressió del K-Cor amb MSB_R (prova de la línia verda Fe XIV).
Escriu v2/comparacions/banda/CEL_CANALS_v2.json. La cau de la Paperera només es llegeix."""
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as nd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv2_comu as cv   # noqa: E402

mc, m2 = cv.mc, cv.m2
T0 = time.time()
OUT = cv.RES2 / 'banda'; OUT.mkdir(parents=True, exist_ok=True)
cau = mc.obre_cau()
s = 4
f = np.asarray(cau['fusion_total_v42'][::s, ::s], np.float64)
sp = np.asarray(cau['support_v42'][::s, ::s])
yy, xx = np.mgrid[0:mc.H:s, 0:mc.W:s].astype(np.float64)
g = mc.geo_llenc()
r, pa = g.polar(xx, yy)
u, v = m2.uv(xx, yy)
dada = sp & np.all(np.isfinite(f), 2) & np.all(f > 0, 2)
CAM = mc.canals_camera(f)
Gv = np.where(dada, mc.verd_camera(f), np.nan)      # exactament el verd de w1 (per a les màscares)
del f
# ---------------------------------------------------------------- màscares (còpia literal de w1_cel_v2.py / p1)
ghost = np.hypot(xx - mc.GHOST_XY[0], yy - mc.GHOST_XY[1]) < mc.GHOST_R_PX
Gf = np.where(dada, Gv, 0.0)
medf = nd.median_filter(Gf, size=9)
res = np.where(dada, Gv - medf, np.nan)
zona_soroll = dada & (r > 3.0) & ~ghost
sd = 1.4826 * np.nanmedian(np.abs(res[zona_soroll] - np.nanmedian(res[zona_soroll])))
est = nd.binary_dilation(dada & (r > 2.0) & (res > 6 * sd), iterations=2)
prom = np.zeros_like(dada)
for p0, dpa in mc.PROM_SECTORS:
    prom |= (np.abs((pa - p0 + 180) % 360 - 180) <= dpa) & (r < mc.PROM_RMAX)
valid = dada & ~ghost & ~est & ~prom & (np.hypot(xx - mc.LLUNA_XY[0], yy - mc.LLUNA_XY[1]) >= mc.R_BANDA_PX)
sel8 = valid & (r >= 8.0)
del Gf, medf, res


def ajust_retall(Am, y, rondes=4, nsig=3.0):
    w = np.ones(len(y), bool)
    for _ in range(rondes):
        c, *_ = np.linalg.lstsq(Am[w], y[w], rcond=None)
        rr = y - Am @ c
        md = np.median(rr[w]); sdx = 1.4826 * np.median(np.abs(rr[w] - md))
        w = np.abs(rr - md) < nsig * sdx
    c, *_ = np.linalg.lstsq(Am[w], y[w], rcond=None)
    return c, w


Am = np.c_[np.ones(sel8.sum()), u[sel8], v[sel8]]
CEL = {}
for nom, Y in (('R', CAM[..., 0]), ('G', CAM[..., 1]), ('B', CAM[..., 2]), ('G_verd_camera', Gv)):
    c, w = ajust_retall(Am, np.where(dada, Y, np.nan)[sel8])
    c_a = float(np.median(np.where(dada, Y, np.nan)[valid & (r > 7.2 * 959.0 / mc.RSOL_ARCSEC)]))
    CEL[nom] = dict(c0=float(c[0]), gu=float(c[1]), gv=float(c[2]), n=int(sel8.sum()), n_final=int(w.sum()), a_c0=c_a)
    print(nom, CEL[nom], flush=True)
ref = m2.coef_cel_v2()['models']['b_new']
prova = dict(G_contra_CEL_v2=[CEL['G']['c0'] - ref['c0'], CEL['G']['gu'] - ref['gu'], CEL['G']['gv'] - ref['gv']],
             Gverd_contra_CEL_v2=[CEL['G_verd_camera']['c0'] - ref['c0'], CEL['G_verd_camera']['gu'] - ref['gu'],
                                  CEL['G_verd_camera']['gv'] - ref['gv']])
prova['passa'] = bool(max(abs(x) for x in prova['G_contra_CEL_v2'] + prova['Gverd_contra_CEL_v2']) < 1e-6)
print('prova verd', prova, flush=True)
cv.json_dump(dict(guio=cv.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'),
                  regla='b_new de la v2 per canal: constant + pla a r ≥ 8 R☉, 4 rondes 3σ MAD, submostreig 4×, màscares de w1',
                  unitats='ADU/s del canal natiu de la càmera per píxel natiu de la R6; u, v en R☉ des del centre del Sol',
                  cel=CEL, prova_verd=prova, sha256_cau={k: mc.SHA_CAU[k] for k in ('fusion_total_v42.npy', 'support_v42.npy')},
                  segons=round(time.time() - T0, 1)), OUT / 'CEL_CANALS_v2.json')
print(f'fet ({time.time() - T0:.0f} s)')
