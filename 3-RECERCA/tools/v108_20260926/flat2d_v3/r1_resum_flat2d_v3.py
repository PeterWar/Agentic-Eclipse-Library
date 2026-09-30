"""r1_resum_flat2d_v3 (V108, flat2d_v3) · RESUM_FLAT2D_V3.json: les xifres clau de totes les mesures (M1_*, diag/D2*, D3*, G1_PORTA_*, rebuts),
per a l'INFORME. Només llegeix JSON de 4-RESULTATS/v108_20260926/flat2d_v3/."""
import json
from pathlib import Path
A = Path(__file__).resolve().parents[4]; R = A / '4-RESULTATS/v108_20260926/flat2d_v3'
def J(p):
    p = R / p; return json.loads(p.read_text()) if p.exists() else None
out = {}
T = J('M1_T_TRACOS.json')
if T:
    out['tracos'] = {img: {t: {v: (None if x is None else [x['solc_ppm'], x['p_atzar'], x['z_atzar']]) for v, x in o.items()} for t, o in T[img].items()} for img in ('compost', 'base_G', 'sonyA_G', 'sonyB_G', 'vixen_G')}
    out['T1_AmenysB'] = T['T1_AmenysB']
S = J('M1_S_CURA_INJECCIO.json')
if S:
    out['s_lluminancia'] = {k: {b: {r: [x['s'], x['s_nul'], x['dE_pc']] for r, x in o.items()} for b, o in v.items()} for k, v in S.items()}
K = J('M1_K_COLOR.json')
if K: out['color'] = K
B = J('M1_B_BRNO.json')
if B: out['brno'] = {cb: {img: {bd: {r: {v: x['r'] for v, x in o.items()} for r, o in rr.items()} for bd, rr in d.items()} for img, d in v.items()} for cb, v in B['B_brno'].items()}
F = J('M1_F_PLOMALLS.json')
if F: out['plomalls'] = {k: dict(contrast_min=min(x['contrast_azimutal'] for x in o.values()), contrast_max=max(x['contrast_azimutal'] for x in o.values()),
                                 corr_min=min(x['corr_perfils'] for x in o.values()), nivell_min=min(x['nivell_radial'] for x in o.values()), nivell_max=max(x['nivell_radial'] for x in o.values())) for k, o in F.items()}
for nom, f in (('perles', 'M1_P_PERLES.json'), ('limbe', 'M1_L_LIMBE.json'), ('vora_vixen', 'M1_V_VORA_VIXEN.json'), ('taques', 'M1_Q_TAQUES.json'), ('taques_sonyA_AmenysB', 'M1_Q2_TAQUES_SONYA_AmenysB.json'), ('taques_vixen_VmenysS', 'M1_Q3_TAQUES_VIXEN_VmenysS.json')):
    x = J(f)
    if x: out[nom] = x
if out.get('vora_vixen'): out['vora_vixen'] = {k: v['dins_sobre_fora'] for k, v in out['vora_vixen'].items()}
for nom in ('D2_PROVA_AB.json', 'D2_PROVA_AB_anells.json', 'D2_PROVA_AB_files_t6.json', 'D2_PROVA_AB_v3.json', 'D3_PROVA_VS.json', 'D3_PROVA_VS_v3.json'):
    d = J('diag/' + nom)
    if d: out[nom.replace('.json', '')] = {q: {b: {r: {c: (v[c]['beta'], v[c]['sigma_nul']) for c in d['comps'] if isinstance(v.get(c), dict)} for r, v in o.items()} for b, o in bb.items()} for q, bb in d['quantitats'].items()}
for T_ in ('VIXEN', 'SONYTOT'):
    g = J(f'flat2d/G1_PORTA_{T_}.json')
    if g:
        out[f'porta_{T_}'] = {gr: dict(n_estructures=v['n_estructures'], n_provades=v['n_provades'], n_aplicades=v['n_aplicades'],
                                       decisions={k: {kk: d.get(kk) for kk in ('a', 'sigma_nul', 'z_present', 'aplica', 'ref', 'R_sol', 'centre_llenc', 'motiu')} for k, d in v['decisions'].items()}) for gr, v in g['grups'].items()}
    rb = J(f'flat2d/{T_}_flat2d_v3_REBUT.json')
    if rb: out[f'rebut_C_{T_}'] = rb
(R / 'RESUM_FLAT2D_V3.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n'); print('FET', list(out))
