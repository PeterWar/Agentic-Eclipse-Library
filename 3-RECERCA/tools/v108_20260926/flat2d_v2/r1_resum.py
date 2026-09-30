"""r1 (V108, flat2d_v2) · RESUM de totes les mesures (només lectura): escriu RESUM_FLAT2D_V2.json amb les xifres clau i les imprimeix."""
import json
from pathlib import Path
ARREL = Path(__file__).resolve().parents[4]; OUT = ARREL / '4-RESULTATS/v108_20260926/flat2d_v2'; R = ARREL / '4-RESULTATS/v108_20260926/cadena/flat2d_v2'
def j(p):
    p = Path(p); return json.loads(p.read_text()) if p.exists() else None
res = {}
# flats
for T in ('VIXEN', 'SONYTOT'):
    f = j(OUT / f'flat2d/{T}_flat2d_v2_REBUT.json')
    res[f'C_{T}'] = dict(portes=f['portes'], ondulacio_sha256=f['ondulacio_sha256'], canals={c: dict(p1_p99_pct=[round(100 * v['C_menys_1_p1_p50_p99'][0], 2), round(100 * v['C_menys_1_p1_p50_p99'][2], 2)],
        max_pct=round(100 * v['max_abs_C_menys_1_fora_vores'], 2), n_sobre_3pc=v['n_px_fora_vores_sobre_3pc'], disc_centre_bp=round(1e4 * v['disc_central_r_lt_20px'], 1),
        REF_disc_cadena=round(v['REF_disc_cadena_r_lt_17px'], 4), REF_extrapolada=round(v['REF_extrapolada_r_lt_17px'], 4), radial_max_bp=round(1e4 * v['contingut_radial_de_C']['max_abs'], 1)) for c, v in f['canals'].items()})
res['congelats'] = j(OUT / 'M3_CONGELATS.json')
res['c8'] = j(R / 'C8_COMPARA.json')
T = j(OUT / 'M1_T_TRACOS.json') or {}
res['tracos'] = {nom: {qui: {tk: dict(solc_bp=round(1e4 * tv['solc'], 1), p_A=tv.get('A', {}).get('p'), p_P=tv.get('P', {}).get('p'), z_P=tv.get('P', {}).get('z')) for tk, tv in d.items()} for qui, d in v.items()} for nom, v in T.items()}
res['energia'] = j(OUT / 'M1_E_ENERGIA.json'); res['brno'] = j(OUT / 'M1_B_BRNO.json'); res['nivell_color'] = j(OUT / 'M1_N_NIVELL_COLOR.json')
res['vora_vixen'] = {k: v.get('dins_sobre_fora') for k, v in (j(OUT / 'M1_V_VORA_VIXEN.json') or {}).items()}
res['limbe'] = j(OUT / 'M1_L_LIMBE.json'); res['capes_305_306'] = j(OUT / 'M2_LIMBE_305_306.json')
(OUT / 'RESUM_FLAT2D_V2.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
for nom in ('compost', 'base_G', 'L55_P04_WOW', 'L56_P05_WOW', 'vixen_G', 'sonyA_G', 'sonyB_G'):
    if nom in res['tracos']:
        for qui, d in res['tracos'][nom].items():
            print(f'{nom:12s} {qui:8s}', ' '.join(f"{tk}:{v['solc_bp']:+6.1f}‱ pA {v['p_A'] if v['p_A'] is None else round(v['p_A'], 3)} pP {v['p_P'] if v['p_P'] is None else round(v['p_P'], 3)}" for tk, v in d.items()))
print('vora Vixen dins/fora:', json.dumps(res['vora_vixen']))
