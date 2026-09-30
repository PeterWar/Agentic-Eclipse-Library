"""n7 (V108 · negres) · Resum de totes les variants (N3_*.json) en quocients respecte de la V107: zones negres, cel, detall per escales i bandes,
flamarada, ordre clar/fosc, perles, soroll del cel i jutge Brno. → 4-RESULTATS/v108_20260926/negres/N_RESUM.json"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comu_negres import OUT, desa
B4 = ('1.3-2', '2-3', '3-4.5', '4.5-7')
DESC = {'V107': 'la V107 (control; ràsters de la 41 i la 42 bit a bit)',
        'TER': 'terra físic sense treure el cel de la NRGF', 'WIE': 'NRGF de Wiener (cel de 2n grau fora; σ sense cel)', 'WIE_TER': 'WIE + terra',
        'WIE_RAD': 'WIE + guany per radi', 'WIE_CUA': 'WIE + compressió de la cua fosca', 'WIE_P': 'WIE amb cel pla', 'WIE_TER_P': 'WIE_TER amb cel pla',
        'CEL': 'cel (pla) fora del numerador, σ original', 'CEL_TER': 'CEL (pla) + terra físic (β 0,6)', 'CEL_TER_b04': 'CEL (pla) + terra (β 0,4)',
        'CEL_RAD': 'CEL (pla) + guany per radi', 'CEL_CUA': 'CEL (pla) + compressió de la cua fosca',
        'CEL_TER_Q': 'RECOMANADA: cel (2n grau) fora del numerador, σ original + terra físic (β 0,6), res a menys de 40 px del limbe',
        'CELW_Q': 'CEL (2n grau) × guany de Wiener de l\'anell', 'CELW_TER_Q': 'CELW (2n grau) + terra',
        'CTQ_56': 'CEL_TER_Q + terra també a la 56 (β 0,15)', 'CTQ_56b04': 'CEL_TER_Q + terra a la 56 (β 0,4)',
        'CTQ_TOTS': 'CEL_TER_Q + terra a 56 (0,15), 45, 46 i 54 (0,05 cadascuna)'}
R = {p.stem[3:]: json.loads(p.read_text()) for p in sorted(OUT.glob('N3_*.json'))}
ref = R['V107']; out = dict(nota='quocients variant / V107 (1 = igual); zones negres en fracció de 1,3–4,5 R☉; pila de la V107 emulada sense capes d\'ajust', variants={})
for k, d in R.items():
    z = d['pas2']; p = d['pas1']; rp = ref['pas1']
    x = dict(descripcio=DESC.get(k, ''), especificacio=d.get('spec'),
             zones_negres=dict(local_suau=z['1.3-4.5']['local_suau'], local_pixel=z['1.3-4.5']['local'], global_=z['1.3-4.5']['global_'],
                               local_suau_per_banda={b: z[b]['local_suau'] for b in ('1.3-2', '2-3', '3-4.5')},
                               local_suau_per_sector_45=z['1.3-4.5']['local_suau_per_sector_45']),
             cel_max_sobre_min_sectors=z['cel_max_sobre_min'],
             detall={sc: {b: p[b][f'rms_{sc}'] / rp[b][f'rms_{sc}'] for b in B4} for sc in ('1-2', '2-8', '8-32')},
             flamarada_p90_p10={r_: p['flamarada'][r_]['p90_menys_p10_ln'] / rp['flamarada'][r_]['p90_menys_p10_ln'] for r_ in p['flamarada']},
             perles_p99_5=p['perles_1.02-1.15']['p99_5_dog_1_4'] / rp['perles_1.02-1.15']['p99_5_dog_1_4'],
             soroll_1_2px={zn: p['soroll'][zn]['1-2'] / rp['soroll'][zn]['1-2'] for zn in p['soroll']},
             brno_corr={lid: {b: v.get(b) for b in B4} for lid, v in p['brno_corr_tangencial_2-64'].items()},
             ordre=p.get('ordre'))
    x['detall']['32-128'] = {b: z['rms_32-128'][b] / ref['pas2']['rms_32-128'][b] for b in B4}
    out['variants'][k] = x
desa(OUT / 'N_RESUM.json', out); print('FET', len(R))
