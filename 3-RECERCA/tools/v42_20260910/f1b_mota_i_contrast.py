"""F1b · diagnòstic de l'apilat d'earthshine V42: (1) el punt brillant del residu és la MOTA DE POLS del R6 (research/127 §7)? Es busca per fotograma
Vixen contra la Sony A (la mota és fixa al sensor de la Vixen; la Lluna es mou entre els tres 10 s → tres posicions); (2) quin contrast té la POWAAAH3 al disc
(per triar l'amplificació declarada de la capa de relleu) i quin color; (3) soroll del residu per banda (per declarar el suavitzat)."""
import json, numpy as np
from scipy.ndimage import gaussian_filter, maximum_filter, label, center_of_mass
from comu42 import *
MC = (CX + 14.8, CY + 0.9); WIN = 700; RL = 453.5
FR = [('sony', 'DSC06987'), ('sony', 'DSC06984'), ('vixen', '572A2982'), ('vixen', '572A2983'), ('vixen', '572A2984')]
x0, y0 = int(round(MC[0])) - WIN, int(round(MC[1])) - WIN; yy, xx = np.mgrid[0:2 * WIN, 0:2 * WIN]; r = np.hypot(xx + x0 - MC[0], yy + y0 - MC[1]); inn = r < 0.93 * RL
def hp(z, m, s1=2, s2=10):
    zz = np.where(m, z, 0).astype(np.float32); mm = m.astype(np.float32)
    def g(s): return gaussian_filter(zz, s) / np.maximum(gaussian_filter(mm, s), 1e-6)
    return np.where(m, g(s1) - g(s2), 0)
T = {}
for tag, stem in FR:
    a = np.load(CAU42 / f'lluna_{tag}_{stem}_v42.npy')[..., 1]; p = np.load(CAU42 / f'lluna_{tag}_{stem}_v42_pes.npy'); ok = np.isfinite(a) & (p > 0)
    a = a / np.nanmedian(a[inn & ok]); T[stem] = (np.where(ok, a, np.nan), ok)
ref = hp(np.nan_to_num(T['DSC06987'][0], nan=1), T['DSC06987'][1] & inn); rep = {}
for stem in ['572A2982', '572A2983', '572A2984', 'DSC06984']:
    z, ok = T[stem]; h = hp(np.nan_to_num(z, nan=1), ok & inn); d = np.where(ok & inn & T['DSC06987'][1], h - ref, 0); sd = np.std(d[inn]); k = 8
    ds = gaussian_filter(d, 1.5); pk = (ds == maximum_filter(ds, 15)) & (ds > 5 * np.std(ds[inn])) & inn; ys, xs = np.nonzero(pk); ordre = np.argsort(-ds[ys, xs])[:3]
    rep[stem] = [dict(x_llenc=float(xs[i] + x0), y_llenc=float(ys[i] + y0), z=float(ds[ys[i], xs[i]] / np.std(ds[inn])), amplitud_pct=float(100 * d[ys[i], xs[i]])) for i in ordre]
    print(stem, 'pics > 5σ del residu (fotograma − Sony 8 s):', [(round(q['x_llenc'], 1), round(q['y_llenc'], 1), round(q['z'], 1), round(q['amplitud_pct'], 2)) for q in rep[stem]])
# POWAAAH3: contrast dins del disc i color
pw = np.load(CAU42 / 'powaaah3_rgb_u16.npy').astype(np.float32) / 65535; pm = np.load(CAU42 / 'powaaah3_mascara_disc_u16.npy') > 32000
d_in = np.zeros(pw.shape[:2], bool); yy2, xx2 = np.mgrid[0:pw.shape[0], 0:pw.shape[1]]; rr = np.hypot(xx2 - MC[0], yy2 - MC[1]); d_in = rr < 0.9 * RL
med = [float(np.median(pw[..., c][d_in])) for c in range(3)]; g = pw[..., 1]; hpg = hp(g, d_in, 2, 40); ctr = float(np.std(hpg[d_in]) / med[1]); p5, p95 = np.percentile(g[d_in], [5, 95])
print(f'POWAAAH3 dins de 0,9 R: medianes sRGB R/G/B {med[0]:.3f}/{med[1]:.3f}/{med[2]:.3f} · contrast (σ passa-alt 2–40 px / mediana) {100*ctr:.1f} % · p5–p95 del G {p5:.3f}–{p95:.3f} ({100*(p95-p5)/med[1]:.0f} % de la mediana)')
# perfil del limbe de la POWAAAH3 (G en funció de r) per veure com és el «llimb decent»
prof = [float(np.median(g[(rr >= a) & (rr < a + 2)])) for a in range(430, 470, 2)]; print('POWAAAH3 perfil G r=430..470 pas 2:', [round(v, 3) for v in prof])
rep['powaaah3'] = dict(medianes=med, contrast_pct=100 * ctr, p5=float(p5), p95=float(p95), perfil_limbe_430_470=prof)
(REB42 / 'F1b_mota_i_contrast.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False))
