"""m3 (V108 · v108_final) · RESUM de les mesures (m0, m1, m2) en un sol JSON, amb la prova d'ADDITIVITAT de cada mètrica: la V108 contra el que
donarien el flat 2D sol (F) i el genoll sol (N) per separat. Per a quocients respecte de la V107 (energies, flamarada, buits, plomalls, cel):
predit = F × N; per a diferències (zones negres, Brno, T1–T6): predit = F + N − V107. Residu = V108 − predit.
Ús: m3_resum_v108.py   Sortida: 4-RESULTATS/v108_20260926/v108_final/V108_FINAL_RESULTATS.json (només llegeix els JSON de la mateixa carpeta)."""
import json
from pathlib import Path
R0 = Path(__file__).resolve().parents[4]; OUT = R0 / '4-RESULTATS/v108_20260926/v108_final'; CAD = R0 / '4-RESULTATS/v108_20260926/cadena/v108'
J = lambda n: json.loads((OUT / n).read_text())
M0, Z, D, T, S, B, FP, FP2, L, K, C, C2, G, M2 = (J(f) for f in ('M0_COMPOSTS.json', 'M1_Z_ZONES_NEGRES.json', 'M1_D_DETALL.json', 'M1_T_TRACOS.json', 'M1_S_ENERGIA_ESCALES.json',
    'M1_B_BRNO.json', 'M1_FP_PLOMALLS_PERLES.json', 'M1_FP2_PLOMALLS_ESCALES.json', 'M1_L_LIMBE.json', 'M1_K_COLOR.json', 'M1_C_COMBINACIO.json', 'M1_C2_INTERACCIO_MARC.json', 'M1_G_GANXO.json', 'M2_VISTES.json'))
V1 = json.loads((CAD / 'V1_STAGE.json').read_text()); MU = json.loads((CAD / 'V108_stage_MUNTATGE.json').read_text())
r = lambda x, n=4: None if x is None else round(float(x), n)
out = dict(tasca='V108 final: flat 2D v5 + genoll CEL_G_MAX_T_e30_W_H0 (decisió de Pere, 27-09, «aplica a de moment»)',
           psb_de_pas=dict(ruta='4-RESULTATS/v108_20260926/cadena/v108/V108_stage.psb', sha256=V1['sha256_psb'], bytes=MU['mida'], v1=V1['veredicte'],
                           capes_canviades=sorted(V1['capes_canviades']), capes_iguals_a_la_V107=MU['verificacio']['capes_iguals_a_la_V107'], errors_v1=V1['errors'],
                           mascares_i_alfes='totes byte a byte les de la V107 (canals −1 i −2: «V107 (bytes)» a les 41 capes)', referencia=V1['referencia']),
           bits=dict(v108_contra_flat2d_v5=M0['bits_v108_contra_flat2d_v5'], a_disc=M0['bits_v108_contra_flat2d_v5_a_disc'], F_refet=M0['F_41_42_refets'],
                     base_nova_diferent_del_control=M0['base_control_diferent_de_la_v108'], genoll_a_la_vora=M0['genoll_41_dins_del_limbe'], validacio_composts=M0['validacio_composts']),
           ganxo=dict(rebut=G['rebut_ganxo_v108_fitxer'], base=G['rebut_ganxo_v108']['base'], font=G['rebut_ganxo_v108']['font'], filtres_std=G['rebut_ganxo_v108']['filtres_std'],
                      psb=G['rebut_ganxo_v108']['psb'], capes_V107=G['rebut_ganxo_v108']['capes_V107']))
# ---- zones negres
zn = {}
for p in ('V107', 'V108', 'F', 'N'):
    z = Z['a1'][p]; zn[p] = {k.split('_')[0]: dict(total=r(100 * v['total'], 2), bandes=[r(100 * v[b], 2) for b in ('1.3-2', '2-3', '3-4.5')], sectors_45=[r(100 * x, 1) for x in v['sectors_45'].values()])
                             for k, v in z.items() if isinstance(v, dict) and 'total' in v}
    zn[p]['cel_max_sobre_min_A_B'] = [r(z['cel_A_max_sobre_min'], 3), r(z['cel_B_max_sobre_min'], 3)]
out['zones_negres_pc'] = zn
out['zones_negres_verificador_w1_pc'] = {p: {k: r(100 * v['total'], 2) for k, v in Z['w1'][p].items() if isinstance(v, dict)} for p in Z['w1']}
out['cel_que_es_veu_quocient'] = {p: {n: {k: r(v, 3) for k, v in o.items()} for n, o in Z['a1_cel_que_es_veu_quocient'][p].items()} for p in Z['a1_cel_que_es_veu_quocient']}
out['mapa_zones'] = M2
# ---- detall
def q(p, f): return f(D[p]) / f(D['V107'])
BN = ['1.02-1.3', '1.3-2', '2-3', '3-4.5', '4.5-7', '>7']
det = {}
for p in ('V108', 'F', 'N'):
    o = {f'rms_{s}': [r(q(p, lambda d, b=b: d['pas1'][b][f'rms_{s}']), 3) for b in BN] for s in ('0-1', '1-2', '2-8', '8-32')}
    o['rms_32-128'] = [r(q(p, lambda d, b=b: d['pas2']['rms_32-128'][b]), 3) for b in BN]
    o['flamarada_1.5_a_4.5'] = [r(q(p, lambda d, k=k: d['pas1']['flamarada'][k]['p90_menys_p10_ln']), 3) for k in D['V107']['pas1']['flamarada']]
    o['buits_4-64'] = [r(q(p, lambda d, k=k: d['pas2']['buits_plomalls_4-64px'][k]['buits_mitj_neg']), 3) for k in D['V107']['pas2']['buits_plomalls_4-64px']]
    o['plomalls_4-64'] = [r(q(p, lambda d, k=k: d['pas2']['buits_plomalls_4-64px'][k]['plomalls_mitj_pos']), 3) for k in D['V107']['pas2']['buits_plomalls_4-64px']]
    o['perles_p99_5'] = r(q(p, lambda d: d['pas1']['perles_1.02-1.15']['p99_5_dog_1_4']), 4)
    o['soroll'] = {z_: {k: r(q(p, lambda d, z_=z_, k=k: d['pas1']['soroll'][z_][k]), 4) for k in ('0-1', '1-2')} for z_ in D['V107']['pas1']['soroll']}
    o['brno_tangencial_2-64_diferencia'] = {lid: [r(D[p]['pas1']['brno_corr_tangencial_2-64'][lid][b] - D['V107']['pas1']['brno_corr_tangencial_2-64'][lid][b], 4) for b in BN if b in D['V107']['pas1']['brno_corr_tangencial_2-64'][lid]] for lid in ('230', '231', '232', '233')}
    o['mediana_L'] = [r(q(p, lambda d, b=b: d['pas1'][b]['mediana_L']), 3) for b in BN]
    det[p] = o
det['brno_tangencial_2-64_V107'] = {lid: [r(v, 3) for v in D['V107']['pas1']['brno_corr_tangencial_2-64'][lid].values()] for lid in ('230', '231', '232', '233')}
out['detall_quocients_contra_V107'] = det
# ---- additivitat de les mètriques
add = {}
def prod(a, b): return [None if (x is None or y is None) else r(x * y, 3) for x, y in zip(a, b)]
for k in ('rms_2-8', 'rms_8-32', 'rms_32-128', 'flamarada_1.5_a_4.5', 'buits_4-64', 'plomalls_4-64'):
    pr = prod(det['F'][k], det['N'][k]); add[k] = dict(V108=det['V108'][k], predit_FxN=pr, residu=[None if (a is None or b is None) else r(a - b, 3) for a, b in zip(det['V108'][k], pr)])
for k in ('A', 'B', 'Afix', 'Bfix'):
    if k in zn['V108'] and k in zn['F']:
        v8, f, n, v7 = zn['V108'][k]['total'], zn['F'][k]['total'], zn['N'][k]['total'], zn['V107'].get(k[0], {}).get('total')
        add[f'zones_negres_{k}_pc'] = dict(V108=v8, predit_F_mes_N_menys_V107=r(f + n - v7, 2), residu=r(v8 - (f + n - v7), 2))
for lid in ('230', '231'):
    v8 = det['V108']['brno_tangencial_2-64_diferencia'][lid]; pr = [r(a + b, 4) for a, b in zip(det['F']['brno_tangencial_2-64_diferencia'][lid], det['N']['brno_tangencial_2-64_diferencia'][lid])]
    add[f'brno_{lid}_diferencia'] = dict(V108=v8, predit_F_mes_N=pr, residu=[r(a - b, 4) for a, b in zip(v8, pr)])
tr = {}
for t, o in T['C1'].items():
    tr[t] = {p: (o[p]['solc_ppm'], o[p]['p_atzar'], o[p]['z_atzar']) if o.get(p) else None for p in ('V107', 'V108', 'F', 'N')}
    tr[t].update({f'z_canvi_{p}': o.get(f'z_canvi_{p}') for p in ('V108', 'F', 'N')})
    if all(o.get(p) for p in ('V107', 'V108', 'F', 'N')):
        add[f'{t}_solc_ppm'] = dict(V108=o['V108']['solc_ppm'], predit=r(o['F']['solc_ppm'] + o['N']['solc_ppm'] - o['V107']['solc_ppm'], 2),
                                    residu=r(o['V108']['solc_ppm'] - (o['F']['solc_ppm'] + o['N']['solc_ppm'] - o['V107']['solc_ppm']), 2), z_residu_als_nuls=C2['tracos_interaccio'][t]['z'])
out['tracos_T1_T6_compost_C1_solc_p_z'] = tr
out['additivitat'] = add
out['interaccio_mapa'] = dict(per_bandes={b: {k: r(v, 5) for k, v in o.items() if k in ('rms_interaccio', 'p99_9_abs_interaccio', 'max_abs_interaccio', 'frac_abs_interaccio_gt_0_5pc', 'corr_delta_V108_i_suma', 'interaccio_sobre_delta_V108')} for b, o in C['per_bandes'].items()},
                              dins_del_marc=C2['dins_del_marc_per_bandes'], per_escales=C['per_escales_rms_I_sobre_rms_delta_V108'], on_es_mes_gran=C['on_es_mes_gran_fora_40px'][:3])
out['energia_per_escales_C1_dE_pc'] = {p: {b: {a: o[b][a]['dE_pc'] for a in o[b]} for b in o} for p, o in ((p, S[f'C1_{p}']) for p in ('V108', 'F', 'N'))}
out['brno_m1_C1'] = {cb: {s: {a: {p: v['r'] for p, v in x.items()} for a, x in o.items()} for s, o in B[cb].items()} for cb in B}
out['plomalls_contrast_azimutal_C1'] = {p: {k: v['contrast_azimutal'] for k, v in list(o.items())[::5]} for p, o in FP['plomalls'].items()}
out['plomalls_menys_i_mes_de_10graus_C1'] = {p: {k: [v['contrast_menys_10graus'], v['contrast_mes_10graus'], v['corr_menys_10graus']] for k, v in list(o.items())[::5]} for p, o in FP2.items()}
out['perles_300'] = FP['perles']
out['limbe'] = {n: {p: {k: [v['rms_pc'], v['p99_abs_pc']] for k, v in o.items()} for p, o in L[n].items()} for n in ('C1', 'PLE')}
out['color_i_nivell_gran_escala'] = {p: {k: ({kk: r(vv, 6) for kk, vv in v.items() if not isinstance(vv, dict)}) for k, v in o.items()} for p, o in K.items()}
out['genoll_v108_contra_negres_v2'] = {lid: {b: {k: (r(v, 5) if isinstance(v, float) else v) for k, v in o.items()} if isinstance(o, dict) else o for b, o in G[f'delta_genoll_{lid}'].items()} for lid in ('41', '42')}
(OUT / 'V108_FINAL_RESULTATS.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n'); print('FET', len(json.dumps(out)), 'bytes')
