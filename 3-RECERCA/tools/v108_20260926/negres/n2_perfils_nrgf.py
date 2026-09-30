"""n2 (V108 · negres) · (2) Per què la NRGF (41/42) enfosqueix els buits per sota del cel: perfils per anell de l'entrada lineal de la V104–V107
(base_G de la variant E amb la franja A3C), de les estadístiques de l'anell que la normalitzen (μ, σ), del cel (model llis de 2n grau ajustat
a 6,5–8,4 R☉, NOMÉS per mesurar quanta σ de l'anell és gradient de cel) i del soroll (banda fina ≤ 1,5 px), i de l'excés de la base de pantalla
(capa 3) sobre el cel del seu sector. Tot a pas 1 amb bincount per anells d'1 px (com l'E1) i agregat en anells de 0,25 R☉.
Sortida: 4-RESULTATS/v108_20260926/negres/N2_PERFILS_NRGF.json"""
import sys, os, json, time
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comu_negres import E, W, H, SOL, RSOL, OUT, desa, lum, cel_local, radi
R0 = Path(__file__).resolve().parents[4]
FONTS = R0 / '4-RESULTATS/v103_banda_20260926/E/lineal_v103'; FR = R0 / '4-RESULTATS/v103_banda_20260926/E/lineal_v103_franja/A3C_franja_silueta.npz'
t0 = time.time()
Q = np.load(FR); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; BOXQ = (slice(qy0, qy1), slice(qx0, qx1))
a = np.load(FONTS / 'base_G.npy').astype(np.float32); m = np.load(FONTS / 'support.npy') & np.isfinite(a) & (a > 0)
a[BOXQ] = Q['G']; m[BOXQ] = Q['domini'] & (Q['G'] > 0); a = np.nan_to_num(a)
yy, xx = np.mgrid[:H, :W].astype(np.float32); r = np.hypot(xx - SOL[0], yy - SOL[1]); ri = np.floor(r).astype(np.int32); nr = int(ri.max()) + 1
ids = ri[m]; v = a[m].astype(np.float64)
cnt = np.bincount(ids, minlength=nr); s1 = np.bincount(ids, v, nr); s2 = np.bincount(ids, v * v, nr)
mu = s1 / np.maximum(cnt, 1); sd = np.sqrt(np.maximum(s2 / np.maximum(cnt, 1) - mu * mu, 0)); print('anells', round(time.time() - t0), flush=True)
# model de cel llis (2n grau en x, y) a 6,5–8,4 R☉, robust (3 passades, fora residus > 2,5 σ): només per MESURAR la seva part de σ
sel = m & (r > 6.5 * RSOL) & (r < 8.4 * RSOL); sel[::1, :] &= ((xx.astype(np.int32) % 4 == 0) & (yy.astype(np.int32) % 4 == 0))
X = (xx[sel] - SOL[0]) / 4000; Y = (yy[sel] - SOL[1]) / 4000; A = np.stack([np.ones_like(X), X, Y, X * X, X * Y, Y * Y], 1).astype(np.float64); b = a[sel].astype(np.float64)
ok = np.ones(len(b), bool)
for _ in range(3):
    c, *_ = np.linalg.lstsq(A[ok], b[ok], rcond=None); res = b - A @ c; s = np.std(res[ok]); ok = np.abs(res) < 2.5 * s
Xf = (xx - SOL[0]) / 4000; Yf = (yy - SOL[1]) / 4000
S = (c[0] + c[1] * Xf + c[2] * Yf + c[3] * Xf * Xf + c[4] * Xf * Yf + c[5] * Yf * Yf).astype(np.float32); del Xf, Yf
vs = S[m].astype(np.float64); ss1 = np.bincount(ids, vs, nr); ss2 = np.bincount(ids, vs * vs, nr); mus = ss1 / np.maximum(cnt, 1); sds = np.sqrt(np.maximum(ss2 / np.maximum(cnt, 1) - mus * mus, 0))
# soroll: banda fina a − G1,5(a) (convolució normalitzada pel domini), per anell
mf = m.astype(np.float32); den = cv2.GaussianBlur(mf, (0, 0), 1.5); g = cv2.GaussianBlur(a * mf, (0, 0), 1.5) / np.maximum(den, 1e-6)
hf = np.where(m & (den > 0.99), a - g, 0).astype(np.float32); okf = (m & (den > 0.99))[m]
vh = hf[m].astype(np.float64); c2 = np.bincount(ids[okf], minlength=nr); h2 = np.bincount(ids[okf], vh[okf] ** 2, nr); sdn = np.sqrt(h2 / np.maximum(c2, 1))
# estructura suavitzada σ 8 px: σ de l'anell de la part llisa
den8 = cv2.GaussianBlur(mf, (0, 0), 8); g8 = cv2.GaussianBlur(a * mf, (0, 0), 8) / np.maximum(den8, 1e-6); v8 = g8[m].astype(np.float64)
t1 = np.bincount(ids, v8, nr); t2 = np.bincount(ids, v8 * v8, nr); mu8 = t1 / np.maximum(cnt, 1); sd8 = np.sqrt(np.maximum(t2 / np.maximum(cnt, 1) - mu8 * mu8, 0))
del g, g8, den, den8, hf
print('sorolls', round(time.time() - t0), flush=True)
# base de pantalla (capa 3): excés sobre el cel del seu sector (pas 2)
P = 2; B = lum(E.rgb(3, (0, 0, W, H), P)); rr, th = radi((0, 0, W, H), P); okb = E.alfa_efectiva(3, (0, 0, W, H), P) > 0.5
_, BS = cel_local(B, rr, th, okb)
out = dict(model_cel_coef=c.tolist(), anells=[])
for a0 in np.arange(1.1, 8.5, 0.25):
    k = np.arange(int(a0 * RSOL), int((a0 + 0.25) * RSOL)); k = k[cnt[k] > 100]
    if not len(k): continue
    mb = okb & (rr >= a0) & (rr < a0 + 0.25)
    wexc = 1 - BS[mb] / np.maximum(B[mb], 1e-6)
    out['anells'].append(dict(r=float(a0 + 0.125), mu=float(np.median(mu[k])), sigma=float(np.median(sd[k])), sigma_rel=float(np.median(sd[k] / mu[k])),
                              cel_mitja=float(np.median(mus[k])), sigma_cel_azimutal=float(np.median(sds[k])), frac_var_cel=float(np.median(sds[k] ** 2 / sd[k] ** 2)),
                              sigma_soroll_fi=float(np.median(sdn[k])), frac_var_soroll_fi=float(np.median(sdn[k] ** 2 / sd[k] ** 2)),
                              sigma_llisa_8px=float(np.median(sd8[k])), corona_sobre_cel_lineal=float(np.median((mu[k] - mus[k]) / mus[k])),
                              w_pantalla_p10=float(np.percentile(wexc, 10)), w_pantalla_mediana=float(np.median(wexc)), w_pantalla_p90=float(np.percentile(wexc, 90))))
    x = out['anells'][-1]; print(f"{x['r']:.2f} σ/μ {x['sigma_rel']:.3f} var_cel {x['frac_var_cel']:.3f} var_soroll_fi {x['frac_var_soroll_fi']:.3f} corona/cel {x['corona_sobre_cel_lineal']:.3f} w {x['w_pantalla_p10']:.3f}/{x['w_pantalla_mediana']:.3f}/{x['w_pantalla_p90']:.3f}", flush=True)
desa(OUT / 'N2_PERFILS_NRGF.json', out); print('FET', round(time.time() - t0))
