"""a2 (V109 · perles_psb) · Localitza les perles de Baily i els trets compactes brillants del limbe a la V107 (compost fusionat del Photoshop) i
en quantifica la pèrdua a la V108: per tret (contrast pic/voltant, energia DoG 1–4 i 4–16, amplada, saturació) i per zona, al compost fusionat
(el que Pere veu) i al recompost sense capes d'ajust (a1). Zones: PERLES (150–200°, just a tocar de la protuberància 267), DRETA (340–20°),
BAIX-DRETA (300–335°) com a controls, VEÏNA (125–150°) i TOT el limbe.
Sortida: A2_PERLES.json, A2_TRETS.npz"""
import numpy as np
from comu_perles import V107, V108, CAIXA, OUT, geom, fusionat, desa
from metriques import detecta, per_tret, per_zona
d, th = geom(CAIXA); X0, Y0 = CAIXA[:2]
IM = dict(FUS_V107=fusionat(V107, CAIXA), FUS_V108=fusionat(V108, CAIXA), REC_V107=np.load(OUT / 'REC_V107.npy'), REC_V108=np.load(OUT / 'REC_V108.npy'))
L7 = (IM['FUS_V107'][..., 0] + 2 * IM['FUS_V107'][..., 1] + IM['FUS_V107'][..., 2]) / 4
ZONES = dict(PERLES=(150, 200), DRETA=(340, 20), BAIX_DRETA=(300, 335), VEINA=(125, 150), TOT=(0, 360))
def sector(a, b): return ((th >= a) & (th < b)) if a < b else ((th >= a) | (th < b))
ys, xs, v, thr = detecta(L7, d, th, -2, 60)
tz = {z: sector(*ab)[ys, xs] for z, ab in ZONES.items()}
M = {k: per_tret(C, ys, xs) for k, C in IM.items()}
rep = dict(llindar_DoG14=thr, n_trets=int(len(ys)), definicio='metriques.py', zones_graus=ZONES, trets={}, zones={})
def resum(a, b, sel):
    o = {}
    for k in ('pic', 'voltant', 'contrast', 'contrast_rel', 'E_1_4', 'E_4_16', 'amplada', 'sat'):
        x, y = a[k][sel], b[k][sel]; ok = np.isfinite(x) & np.isfinite(y)
        if k in ('sat', 'amplada', 'pic', 'voltant'):
            o[k] = dict(V107_mitj=round(float(x[ok].mean()), 5), V108_mitj=round(float(y[ok].mean()), 5), dif_mitj=round(float((y - x)[ok].mean()), 5))
        else:
            r = y[ok] / np.where(x[ok] != 0, x[ok], np.nan); r = r[np.isfinite(r)]
            o[k] = dict(V108_sobre_V107_p5_p50_p95=np.percentile(r, [5, 50, 95]).round(4).tolist(), mitj_V107=round(float(x[ok].mean()), 6), mitj_V108=round(float(y[ok].mean()), 6))
    return o
for z in ZONES:
    for band, (a, b) in dict(perla_0_8=(-2, 8), voltant_8_60=(8, 60)).items():
        sel = tz[z] & (d[ys, xs] >= a) & (d[ys, xs] < b)
        if sel.sum() < 3: continue
        rep['trets'][f'{z}_{band}'] = dict(n=int(sel.sum()), fusionat=resum(M['FUS_V107'], M['FUS_V108'], sel), recompost=resum(M['REC_V107'], M['REC_V108'], sel))
BANDES = dict(b_m2_0=(-2, 0), b_0_4=(0, 4), b_4_8=(4, 8), b_8_20=(8, 20), b_20_40=(20, 40), b_40_60=(40, 60))
for z, ab in ZONES.items():
    for bn, (a, b) in BANDES.items():
        m = sector(*ab) & (d >= a) & (d < b); o = {}
        for k in IM: o[k] = {kk: round(vv, 6) for kk, vv in per_zona(IM[k], m).items()}
        for fam in ('FUS', 'REC'):
            o[f'{fam}_V108_sobre_V107'] = {kk: round(o[f'{fam}_V108'][kk] / o[f'{fam}_V107'][kk], 4) for kk in o[f'{fam}_V107'] if o[f'{fam}_V107'][kk]}
        rep['zones'][f'{z}_{bn}'] = o
# les perles, una per una (zona PERLES, 0–8 px), amb posició
sel = np.nonzero(tz['PERLES'] & (d[ys, xs] < 8))[0]
rep['perles_una_a_una'] = [dict(x=int(xs[i] + X0), y=int(ys[i] + Y0), d=round(float(d[ys[i], xs[i]]), 1), th=round(float(th[ys[i], xs[i]]), 1),
                               **{f'{k}_{t}': round(float(M[t][k][i]), 5) for k in ('pic', 'voltant', 'contrast', 'E_1_4', 'E_4_16', 'amplada', 'sat') for t in ('FUS_V107', 'FUS_V108', 'REC_V107', 'REC_V108')})
                          for i in sel]
np.savez(OUT / 'A2_TRETS.npz', ys=ys, xs=xs, v=v, **{f'{t}_{k}': M[t][k] for t in M for k in M[t]})
desa(OUT / 'A2_PERLES.json', rep)
for k, o in rep['trets'].items(): print(k, o['n'], 'FUS contrast', o['fusionat']['contrast']['V108_sobre_V107_p5_p50_p95'], 'E14', o['fusionat']['E_1_4']['V108_sobre_V107_p5_p50_p95'], 'E416', o['fusionat']['E_4_16']['V108_sobre_V107_p5_p50_p95'], '| REC contrast', o['recompost']['contrast']['V108_sobre_V107_p5_p50_p95'], 'E14', o['recompost']['E_1_4']['V108_sobre_V107_p5_p50_p95'])
for k, o in rep['zones'].items(): print(k, 'FUS', {a: o['FUS_V108_sobre_V107'].get(a) for a in ('L_mitj', 'rms_DoG_1_4', 'rms_DoG_4_16', 'rms_DoGln_1_4')}, 'REC', {a: o['REC_V108_sobre_V107'].get(a) for a in ('L_mitj', 'rms_DoG_1_4', 'rms_DoG_4_16')})
