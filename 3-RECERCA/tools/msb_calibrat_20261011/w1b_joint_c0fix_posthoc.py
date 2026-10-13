"""w1b · POST HOC (després de veure que l'ajust conjunt predeclarat és degenerat; després de la tria del cel, que NO canvia).

L'ajust conjunt predeclarat (w1: c0, gu, gv i C(r) lliures) no determina c0: σ_jackknife(c0) ≈ 212 ADU/s, correlació c0–gv −0,9998,
i C(r) surt negativa (no física). Aquí es repeteix amb c0 FIX al valor de b_new (439,09 ADU/s, ajustat a r ≥ 8 R☉) i es lliuren
gu, gv i C(r)·10^(−0,4·k·(X − X_ZP)) per anells de 0,1 R☉ des de 3,546 R☉, amb k = 0,40 (i, per veure'n la sensibilitat, 0,57 i 0,72).
Mateixes màscares i mateix retall que w1. Escriu v2/mapa/cel/JOINT_C0FIX_posthoc.json. No toca CEL_v2.json."""
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
CEL2 = m2.coef_cel_v2()
C0FIX = CEL2['models']['b_new']['c0']
cau = mc.obre_cau()
s = 4
f = np.asarray(cau['fusion_total_v42'][::s, ::s], np.float64)
sp = np.asarray(cau['support_v42'][::s, ::s])
yy, xx = np.mgrid[0:mc.H:s, 0:mc.W:s].astype(np.float64)
g = mc.geo_llenc()
r, pa = g.polar(xx, yy)
u, v = m2.uv(xx, yy)
dada = sp & np.all(np.isfinite(f), 2) & np.all(f > 0, 2)
G = np.where(dada, mc.verd_camera(f), np.nan)
del f
ghost = np.hypot(xx - mc.GHOST_XY[0], yy - mc.GHOST_XY[1]) < mc.GHOST_R_PX
Gf = np.where(dada, G, 0.0)
res = np.where(dada, G - nd.median_filter(Gf, size=9), np.nan)
zs = dada & (r > 3.0) & ~ghost
sd = 1.4826 * np.nanmedian(np.abs(res[zs] - np.nanmedian(res[zs])))
est = nd.binary_dilation(dada & (r > 2.0) & (res > 6 * sd), iterations=2)
prom = np.zeros_like(dada)
for p0, dpa in mc.PROM_SECTORS:
    prom |= (np.abs((pa - p0 + 180) % 360 - 180) <= dpa) & (r < mc.PROM_RMAX)
valid = dada & ~ghost & ~est & ~prom & (np.hypot(xx - mc.LLUNA_XY[0], yy - mc.LLUNA_XY[1]) >= mc.R_BANDA_PX)
del Gf, res
MA = mc.MassaAire()
X = mc.kasten_young(MA.sp.ev(yy.ravel(), xx.ravel()).reshape(yy.shape))
K76 = 959.0 / mc.RSOL_ARCSEC
RJ0 = 3.5 * K76
dj = valid & (r > RJ0)
ej = np.arange(RJ0, float(r[dj].max()) + 0.1, 0.1)
ring_all = np.digitize(r, ej) - 1
SECTOR = (np.floor(pa / 30.0).astype(np.int64)) % 12


def fit_c0fix(sel, A, rondes=4, nsig=3.0):
    yv = G[sel] - C0FIX; uu = u[sel]; vv = v[sel]; Av = A[sel]; jv = ring_all[sel]
    nr = len(ej) - 1
    cnt = np.bincount(jv, minlength=nr)[:nr]; okr = cnt >= 200
    w = okr[jv].copy(); use = w.copy()
    for it in range(rondes + 1):
        P = 2 + nr
        N = np.zeros((P, P)); b = np.zeros(P)
        B = [uu[w], vv[w]]
        for i in range(2):
            for k in range(2):
                N[i, k] = np.dot(B[i], B[k])
            b[i] = np.dot(B[i], yv[w])
            N[i, 2:] = np.bincount(jv[w], weights=B[i] * Av[w], minlength=nr)[:nr]; N[2:, i] = N[i, 2:]
        N[np.arange(2, P), np.arange(2, P)] = np.bincount(jv[w], weights=Av[w] ** 2, minlength=nr)[:nr]
        b[2:] = np.bincount(jv[w], weights=Av[w] * yv[w], minlength=nr)[:nr]
        act = np.r_[np.ones(2, bool), okr & (np.diag(N)[2:] > 0)]
        beta = np.zeros(P); beta[act] = np.linalg.solve(N[np.ix_(act, act)], b[act])
        rr_ = yv - (beta[0] * uu + beta[1] * vv + beta[2 + np.clip(jv, 0, nr - 1)] * Av)
        md = np.median(rr_[w]); sdx = 1.4826 * np.median(np.abs(rr_[w] - md))
        if it < rondes:
            w = use & (np.abs(rr_ - md) < nsig * sdx)
    return beta, float(sdx), int(w.sum()), float(np.linalg.cond(N[np.ix_(act, act)]))


out = dict(guio='w1b_joint_c0fix_posthoc.py', caracter='POST HOC: no canvia la tria del cel (b_new, feta a w1)',
           data=time.strftime('%Y-%m-%dT%H:%M:%S'), c0_fix_adu=C0FIX, regla=__doc__.split('\n\n')[1].replace('\n', ' '), k={})
for k in (0.40, 0.57, 0.72):
    A = 1.0 / m2.factor_extincio(X, k)
    beta, rms, n, cond = fit_c0fix(dj, A)
    presents = [j for j in range(12) if np.any(dj & (SECTOR == j))]
    th = np.array([fit_c0fix(dj & (SECTOR != j), A)[0][:2] for j in presents])
    m = len(presents); sig = np.sqrt((m - 1) / m * ((th - th.mean(0)) ** 2).sum(0))
    rc = 0.5 * (ej[1:] + ej[:-1])
    out['k'][f'{k:.2f}'] = dict(gu=float(beta[0]), gv=float(beta[1]), sigma_jk_gu=float(sig[0]), sigma_jk_gv=float(sig[1]),
                                rms_mad_adu=rms, n=n, nombre_condicio=cond,
                                C_r=dict(r_mig=rc.tolist(), C_adu=[float(x) for x in beta[2:]]))
    print(k, {kk: out['k'][f'{k:.2f}'][kk] for kk in ('gu', 'gv', 'sigma_jk_gu', 'sigma_jk_gv', 'rms_mad_adu', 'nombre_condicio')},
          f'C(3.6)={beta[2]:.1f} C(8)={beta[2 + int((8 - RJ0) / 0.1)]:.2f}', flush=True)
json.dump(out, open(m2.CELDIR / 'JOINT_C0FIX_posthoc.json', 'w'), indent=1, ensure_ascii=False)
print(f'fet en {time.time() - T0:.0f} s')
