"""a2 (V108 · negres_v2) · Resum comparatiu dels A1_<variant>.json (quocients respecte de la V107): zones negres (A i B), cel, detall, flamarada,
contrast buit/plomall, Brno, perles, soroll, ràster (tocats, control nul, arc a r_edge) i canvi del compost. Ús: a2_resum.py [variants…] [--json SORTIDA]"""
import sys, json
from pathlib import Path
R0 = Path(__file__).resolve().parents[4]; OUT = R0 / '4-RESULTATS/v108_20260926/negres_v2'
_a = sys.argv[1:]; args = [a for i, a in enumerate(_a) if not a.startswith('--') and not (i > 0 and _a[i - 1] == '--json')]; jout = next((sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == '--json'), None)
V = json.loads((OUT / 'A1_V107.json').read_text())
def q(a, b): return round(a / b, 3) if b else None
def fila(nom):
    d = json.loads((OUT / f'A1_{nom}.json').read_text()); z = d['zones']; p1 = d['pas1']; v1 = V['pas1']; r = d.get('raster_41', {})
    o = dict(variant=nom)
    for ref in ('A_cel_6.5-8.5', 'B_cel_5-5.6_marc'):
        k = ref[0]; o[f'negres_{k}'] = round(100 * z[ref]['total'], 2); o[f'negres_{k}_bandes'] = [round(100 * z[ref][b], 2) for b in ('1.3-2', '2-3', '3-4.5')]
        o[f'negres_{k}_sectors45'] = [round(100 * v, 1) for v in z[ref]['sectors_45'].values()]
    o['negres_A_pixel'] = round(100 * z['A_cel_6.5-8.5']['pixel_a_pixel'], 2)
    o['cel_maxmin_A_B'] = [round(z['cel_A_max_sobre_min'], 3), round(z['cel_B_max_sobre_min'], 3)]
    c, c0 = z['cel_que_es_veu'], V['zones']['cel_que_es_veu']
    o['cel_dalt_baix_5-5.6_quocient'] = [q(c['cel_5-5.6_marc']['dalt_45-135'], c0['cel_5-5.6_marc']['dalt_45-135']), q(c['cel_5-5.6_marc']['baix_225-315'], c0['cel_5-5.6_marc']['baix_225-315'])]
    o['cel_dalt_baix_6.5-8.5_quocient'] = [q(c['cel_6.5-8.5']['dalt_45-135'], c0['cel_6.5-8.5']['dalt_45-135']), q(c['cel_6.5-8.5']['baix_225-315'], c0['cel_6.5-8.5']['baix_225-315'])]
    B = ('1.3-2', '2-3', '3-4.5', '4.5-7')
    for esc in ('1-2', '2-8', '8-32'):
        o[f'detall_{esc}'] = [q(p1[b][f'rms_{esc}'], v1[b][f'rms_{esc}']) for b in B]
    o['detall_32-128'] = [q(d['pas2']['rms_32-128'][b], V['pas2']['rms_32-128'][b]) for b in B]
    o['flamarada_1.5..4.5'] = [q(p1['flamarada'][k]['p90_menys_p10_ln'], v1['flamarada'][k]['p90_menys_p10_ln']) for k in ('1.5', '2', '2.5', '3', '3.5', '4', '4.5')]
    bp, bp0 = d['pas2']['buits_plomalls_4-64px'], V['pas2']['buits_plomalls_4-64px']
    o['buits_4-64'] = [q(bp[b]['buits_mitj_neg'], bp0[b]['buits_mitj_neg']) for b in B]; o['plomalls_4-64'] = [q(bp[b]['plomalls_mitj_pos'], bp0[b]['plomalls_mitj_pos']) for b in B]
    o['brno230_1.3-2_2-3_3-4.5'] = [round(p1['brno_corr_tangencial_2-64']['230'][b], 3) for b in ('1.3-2', '2-3', '3-4.5')]
    o['brno230_V107'] = [round(v1['brno_corr_tangencial_2-64']['230'][b], 3) for b in ('1.3-2', '2-3', '3-4.5')]
    o['brno231_232_3-4.5'] = [round(p1['brno_corr_tangencial_2-64'][k]['3-4.5'], 3) for k in ('231', '232')]
    o['perles'] = q(p1['perles_1.02-1.15']['rms_dog_1_4'], v1['perles_1.02-1.15']['rms_dog_1_4'])
    o['soroll_cel_1-2_i_4.5-7'] = [q(p1['soroll']['cel_>7']['1-2'], v1['soroll']['cel_>7']['1-2']), q(p1['soroll']['corona_feble_4.5-7']['1-2'], v1['soroll']['corona_feble_4.5-7']['1-2'])]
    if 'ordre' in p1: o['ordre_corr_pendents_3-4.5'] = [round(p1['ordre']['3-4.5'][k], 3) for k in ('corr', 'pendent_clars', 'pendent_foscos', 'signe_invertit')]
    if r:
        o['raster_tocats_pc_1.02-1.3_1.3-2_2-3_3-4.5_4.5-7_7-9.5'] = [round(100 * r['per_bandes'][b]['frac_tocats_1_512'], 2) for b in ('1.02-1.3', '1.3-2', '2-3', '3-4.5', '4.5-7', '7-9.5')]
        o['raster_mitj_abs_du'] = [round(r['per_bandes'][b]['mitj_abs_dA'], 4) for b in ('1.3-2', '2-3', '3-4.5', '4.5-7', '7-9.5')]
        o['raster_limbe_40px_px_diferents'] = r['limbe_<40px']['px_diferents']
        o['control_nul_raster'] = {k: round(v, 4) for k, v in r['control_nul_baix_225-315_1.3-3'].items()}
        o['raster_energia_2-8'] = [round(v, 3) for v in r['energia_raster_41']['2-8'].values()]
        a = r['arc_r_edge']; o['arc_canvi_pendent_dA_max'] = round(max(abs(v['canvi_pendent_dA']) for v in a.values()), 4)
        o['arc_salt_max_dA'] = round(max(v['salt_max_dA_0_01R'] for v in a.values()), 4)
        o['arc_canvi_pendent_u_V107_i_cand_max'] = [round(max(abs(v['canvi_pendent_u_V107']) for v in a.values()), 4), round(max(abs(v['canvi_pendent_u_cand']) for v in a.values()), 4)]
    ch = d.get('canvi_compost_ln_p1_p50_p99_frac_gt_0_5pc', {})
    if ch: o['compost_frac_canvi_gt_0.5pc_1.3-2_i_nul'] = [round(ch['1.3-2'][3], 4), round(ch['control_nul_baix_225-315_1.3-3'][3], 4)]; o['compost_ln_p50_3-4.5'] = round(ch['3-4.5'][1], 4)
    return o
F = [fila(n) for n in args]
for o in F:
    print('=' * 20, o['variant'])
    for k, v in o.items():
        if k != 'variant': print(f'  {k}: {v}')
if jout: Path(jout).write_text(json.dumps(F, ensure_ascii=False, indent=1) + '\n')
