"""a3 (V109 · perles_psb) · Atribució per capa. RECOMPON la pila visible real (modes, màscares, alfes i opacitats de la V107, que són les de la
V108) canviant capes de V107 a V108 d'una en una (i a la inversa, i en grups), i mesura les perles i les zones de control sobre cada variant.
A més: (1) quant guanya la 76 (Aclarir) sobre el compost de sota a les perles, V107 i V108; (2) separa el canvi del compost FUSIONAT en la part
de les capes (passada per la corba de les capes d'ajust de la V107, ajustada punt a punt) i la resposta de les capes d'ajust (239–244), que no
és puntual. Entrades: cache/PILA_V10x.npz (a1), A2_TRETS.npz (a2). Sortida: A3_ATRIBUCIO.json"""
import numpy as np
from comu_perles import CAIXA, OUT, geom, compon, lum, fusionat, V107, V108, desa, CANVIADES
from metriques import per_tret, per_zona, dog
d, th = geom(CAIXA)
def carrega(tag):
    z = np.load(OUT / f'cache/PILA_{tag}.npz'); S = []
    for m in z['meta']:
        lid, mode, op, nom = str(m).split('|', 3); lid = int(lid)
        S.append(dict(id=lid, mode=mode, op=float(op), nom=nom, **{k: z[f'L{lid}_{k}'].astype(np.float32) / 65535 for k in ('rgb', 'alfa', 'masc')}))
    return S
S7, S8 = carrega('V107'), carrega('V108'); idx = {c['id']: i for i, c in enumerate(S7)}
def variant(base, altra, ids):
    S = list(base)
    for i in ids: S[idx[i]] = altra[idx[i]]
    return compon(S)
T = np.load(OUT / 'A2_TRETS.npz'); ys, xs = T['ys'], T['xs']
ZONES = dict(PERLES=(150, 200), DRETA=(340, 20), BAIX_DRETA=(300, 335))
def sector(a, b): return ((th >= a) & (th < b)) if a < b else ((th >= a) | (th < b))
sel_perla = sector(150, 200)[ys, xs] & (d[ys, xs] < 8)
BANDES = dict(b_0_4=(0, 4), b_4_8=(4, 8), b_8_20=(8, 20), b_20_40=(20, 40), b_40_60=(40, 60))
MZ = {f'{z}_{b}': sector(*ab) & (d >= lo) & (d < hi) for z, ab in ZONES.items() for b, (lo, hi) in BANDES.items()}
R7 = compon(S7); R8 = compon(S8); t7 = per_tret(R7, ys[sel_perla], xs[sel_perla]); z7 = {k: per_zona(R7, m) for k, m in MZ.items()}
def mesura(C):
    t = per_tret(C, ys[sel_perla], xs[sel_perla]); z = {k: per_zona(C, m) for k, m in MZ.items()}; L, L7 = lum(C), lum(R7)
    o = dict(perles_contrast_p50=round(float(np.nanmedian(t['contrast'] / t7['contrast'])), 5), perles_E14_p50=round(float(np.nanmedian(t['E_1_4'] / t7['E_1_4'])), 5),
             perles_E416_p50=round(float(np.nanmedian(t['E_4_16'] / t7['E_4_16'])), 5), perles_max_absdL_px=round(float(np.max(np.abs(L - L7)[sector(150, 200) & (d >= -2) & (d < 8)])), 6))
    for k in MZ: o[f'{k}_rmsDoG14'] = round(z[k]['rms_DoG_1_4'] / z7[k]['rms_DoG_1_4'], 5); o[f'{k}_rmsDoG416'] = round(z[k]['rms_DoG_4_16'] / z7[k]['rms_DoG_4_16'], 5)
    for k in ('PERLES_b_0_4', 'PERLES_b_4_8', 'PERLES_b_8_20', 'PERLES_b_20_40', 'PERLES_b_40_60', 'DRETA_b_20_40', 'DRETA_b_40_60'):
        o[f'{k}_rms_dL'] = round(float(np.sqrt(((L - L7)[MZ[k]] ** 2).mean())), 6)
    return o
rep = dict(n_perles=int(sel_perla.sum()), referencia='recompost V107 (sense capes d\'ajust)', variants={})
rep['variants']['V108 (tot)'] = mesura(R8)
GRUPS = {'base 3': [3], 'NRGF 41+42': [41, 42], 'MGN 54': [54], 'RHEF 45+46': [45, 46], 'ACHF 47+49+51': [47, 49, 51], 'WOW 55+56': [55, 56], 'filtres (tots)': [54, 41, 42, 47, 49, 51, 45, 46, 55, 56]}
for lid in CANVIADES:
    rep['variants'][f'V107 + {lid} de V108'] = mesura(variant(S7, S8, [lid])); print(lid, rep['variants'][f'V107 + {lid} de V108']['PERLES_b_20_40_rms_dL'], flush=True)
    rep['variants'][f'V108 − {lid} (de V107)'] = mesura(variant(S8, S7, [lid]))
for g, ids in GRUPS.items():
    rep['variants'][f'V107 + {g} de V108'] = mesura(variant(S7, S8, ids)); rep['variants'][f'V108 − {g} (de V107)'] = mesura(variant(S8, S7, ids))
# (1) la 76 en Aclarir: compost de sota (fins a la 258) contra la 76
for tag, S in (('V107', S7), ('V108', S8)):
    i76 = idx[76]; sota = compon(S[:i76]); c76 = S[i76]; a76 = c76['alfa'] * c76['masc'] * c76['op']
    guanya = (c76['rgb'] > sota).all(-1) & (a76 > 0.5); guanya_G = (c76['rgb'][..., 1] > sota[..., 1]) & (a76 > 0.5)
    o = {}
    for b, (lo, hi) in dict(b_m2_0=(-2, 0), b_0_2=(0, 2), b_2_4=(2, 4), b_4_8=(4, 8), b_8_20=(8, 20), b_20_60=(20, 60)).items():
        m = sector(150, 200) & (d >= lo) & (d < hi)
        o[b] = dict(frac_76_guanya_3canals=round(float(guanya[m].mean()), 4), frac_76_guanya_G=round(float(guanya_G[m].mean()), 4), alfa76_mitj=round(float(a76[m].mean()), 4),
                    marge_G_mitj=round(float((c76['rgb'][..., 1] - sota[..., 1])[m].mean()), 5))
    rep[f'lighten_76_{tag}'] = o
    if tag == 'V107': sota7 = sota
    else: sota8 = sota
m = sector(150, 200) & (d >= -2) & (d < 8)
rep['sota_76_perles_rms_dif_V108_V107'] = round(float(np.sqrt(((lum(sota8) - lum(sota7))[m] ** 2).mean())), 6)
# (2) capes contra capes d'ajust al compost fusionat: corba punt a punt REC→FUS de la V107 (per canal, 4096 calaixos)
F7, F8 = fusionat(V107, CAIXA), fusionat(V108, CAIXA)
def corba(rec, fus):
    out = []
    for c in range(3):
        b = np.clip((rec[..., c] * 4095).astype(np.int32), 0, 4095).ravel(); n = np.bincount(b, minlength=4096); s = np.bincount(b, fus[..., c].ravel(), 4096)
        v = np.where(n > 0, s / np.maximum(n, 1), np.nan); ok = np.isfinite(v); v = np.interp(np.arange(4096), np.nonzero(ok)[0], v[ok]); out.append(v)
    return out
def aplica(lut, rec): return np.stack([np.interp(rec[..., c] * 4095, np.arange(4096), lut[c]) for c in range(3)], -1).astype(np.float32)
lut = corba(R7, F7); P7, P8 = aplica(lut, R7), aplica(lut, R8)
capes = lum(P8) - lum(P7); resposta = (lum(F8) - lum(P8)) - (lum(F7) - lum(P7)); total = lum(F8) - lum(F7)
o = dict(residu_corba_V107_rms_per_banda={}, per_zona={})
for b, (lo, hi) in dict(disc_m60_m2=(-60, -2), b_m2_0=(-2, 0), b_0_4=(0, 4), b_4_8=(4, 8), b_8_20=(8, 20), b_20_40=(20, 40), b_40_60=(40, 60)).items():
    for z, ab in dict(PERLES=(150, 200), TOT=(0, 360)).items():
        mm = sector(*ab) & (d >= lo) & (d < hi)
        o['residu_corba_V107_rms_per_banda'][f'{z}_{b}'] = round(float(np.sqrt(((lum(F7) - lum(P7))[mm] ** 2).mean())), 6)
        o['per_zona'][f'{z}_{b}'] = dict(total_mitj=round(float(total[mm].mean()), 6), total_rms=round(float(np.sqrt((total[mm] ** 2).mean())), 6),
                                          capes_mitj=round(float(capes[mm].mean()), 6), capes_rms=round(float(np.sqrt((capes[mm] ** 2).mean())), 6),
                                          ajust_mitj=round(float(resposta[mm].mean()), 6), ajust_rms=round(float(np.sqrt((resposta[mm] ** 2).mean())), 6),
                                          ajust_sobre_L7=round(float(resposta[mm].mean() / lum(F7)[mm].mean()), 5))
rep['fusionat_capes_contra_ajust'] = o
np.save(OUT / 'cache/RESPOSTA_AJUST.npy', resposta.astype(np.float32)); np.save(OUT / 'cache/CAPES_PER_CORBA.npy', capes.astype(np.float32))
desa(OUT / 'A3_ATRIBUCIO.json', rep); print('fet')
