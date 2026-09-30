"""r1_resum_flat2d_v4 (V108, flat2d_v4) · RESUM_FLAT2D_V4.json: les xifres clau de totes les mesures (M1_*, M2, M4, G2, diag/D2*, D3*, H1, G1, P1,
rebuts), per a l'INFORME. Còpia ampliada de r1_resum_flat2d_v3.py. Només llegeix JSON de 4-RESULTATS/v108_20260926/flat2d_v4/ (i la P1 de la cadena)."""
import json
from pathlib import Path
A = Path(__file__).resolve().parents[4]; R = A / '4-RESULTATS/v108_20260926/flat2d_v4'
def J(p):
    p = R / p if not str(p).startswith('/') else Path(p); return json.loads(p.read_text()) if p.exists() else None
out = {}
T = J('M1_T_TRACOS.json')
if T:
    out['tracos'] = {img: {t: {v: (None if x is None else [x['solc_ppm'], x['p_atzar'], x['z_atzar']]) for v, x in o.items()} for t, o in T[img].items()} for img in ('compost', 'base_G', 'sonyA_G', 'sonyB_G', 'vixen_G') if img in T}
    out['T1_AmenysB'] = T.get('T1_AmenysB')
S = J('M1_S_CURA_INJECCIO.json')
if S: out['s_lluminancia'] = {k: {b: {r: [x['s'], x['s_nul'], x['dE_pc']] for r, x in o.items()} for b, o in v.items()} for k, v in S.items()}
K = J('M1_K_COLOR.json')
if K: out['color'] = K
B = J('M1_B_BRNO.json')
if B: out['brno'] = {cb: {img: {bd: {r: {v: x['r'] for v, x in o.items()} for r, o in rr.items()} for bd, rr in d.items()} for img, d in v.items()} for cb, v in B['B_brno'].items()}
F = J('M1_F_PLOMALLS.json')
if F: out['plomalls'] = {k: dict(contrast_min=min(x['contrast_azimutal'] for x in o.values()), contrast_max=max(x['contrast_azimutal'] for x in o.values()),
                                 corr_min=min(x['corr_perfils'] for x in o.values()), nivell_min=min(x['nivell_radial'] for x in o.values()), nivell_max=max(x['nivell_radial'] for x in o.values())) for k, o in F.items()}
for nom, f in (('perles', 'M1_P_PERLES.json'), ('limbe', 'M1_L_LIMBE.json'), ('vora_vixen', 'M1_V_VORA_VIXEN.json'), ('taques', 'M1_Q_TAQUES.json'), ('taques_sonyA_AmenysB', 'M1_Q2_TAQUES_SONYA_AmenysB.json'),
               ('taques_vixen_VmenysS', 'M1_Q3_TAQUES_VIXEN_VmenysS.json'), ('energia_compost', 'M4_ENERGIA_compost.json')):
    x = J(f)
    if x: out[nom] = x
if out.get('vora_vixen'): out['vora_vixen'] = {k: v['dins_sobre_fora'] for k, v in out['vora_vixen'].items()}
M2 = J('M2_TAQUES_FORATS.json')
if M2:
    out['cel_anullat_taques'] = {t: {k: v for k, v in M2[t].items() if k != 'pics_control_z4_llista'} for t in ('sony', 'vixen') if t in M2}
    out['forats_i_petjades'] = {k: v['resum'] for k, v in M2.items() if k.startswith(('forats_', 'petjades_'))}
G2 = J('G2_RESIDU_PORTA.json')
if G2: out['residu_per_grup'] = {tr: {g: {k: v for k, v in o.items() if k != 'estructures'} for g, o in d['grups'].items()} for tr, d in G2.items()}
for T_ in ('VIXEN', 'SONYTOT'):
    h = J(f'flat2d/H1_ENCONGIDA_{T_}.json')
    if h: out[f'encongiment_{T_}'] = {g: {k: v for k, v in o.items() if k != 'estructures'} for g, o in h['grups'].items()}
    rb = J(f'flat2d/{T_}_flat2d_v4_REBUT.json')
    if rb: out[f'rebut_C_{T_}'] = rb
for nom in ('D2_PROVA_AB_v4.json', 'D3_PROVA_VS_v4.json'):
    d = J('diag/' + nom)
    if d: out[nom.replace('.json', '')] = {q: {b: {r: {c: (v[c]['beta'], v[c]['sigma_nul']) for c in d['comps'] if isinstance(v.get(c), dict)} for r, v in o.items()} for b, o in bb.items()} for q, bb in d['quantitats'].items()}
M5 = J('M5_PICS_CONTROL.json')
if M5: out['pics_control'] = {k: v for k, v in M5.items() if k != 'pics'}
M6 = J('M6_CURA_PETJADES.json')
if M6: out['cura_petjades'] = {b: {par: {r: {k: v for k, v in x.items() if k != 'petjades'} for r, x in pp.items()} for par, pp in bb.items()} for b, bb in M6.items()}
g2a0 = J('G2_RESIDU_PORTA_a0.json')
if g2a0: out['residu_per_grup_a0'] = {tr: {g: {k: v for k, v in o.items() if k != 'estructures'} for g, o in d['grups'].items()} for tr, d in g2a0.items()}
p1 = J(A / '4-RESULTATS/v108_20260926/cadena/flat2d_v4/franja/P1_PROTUBERANCIA.json')
if p1: out['protuberancia_franja'] = {k: v for k, v in p1.items() if k != 'regla'}
(R / 'RESUM_FLAT2D_V4.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n'); print('FET', list(out))
