"""Tests sobre el fonament (S3→S4→S5→S7): porta de costura a cada pas, cobertura, sectors absolut, pilots."""
import numpy as np
from tests_v3c import *
tag = os.environ.get('TAG', 'fonament')
QA = f'{SCR}/QA/{tag}'; os.makedirs(QA, exist_ok=True)
masks = {i: np.load(f'{SCR}/masks/mask_{i}.npy') for i in (4, 5, 7)}
S = {k: np.load(f'{SCR}/states/S{k}.npy', mmap_mode='r') for k in (3, 4, 5, 7)}
summary = {}
prev = 3; acc = {}
for i in (4, 5, 7):
    acc[i] = masks[i]
    abans = np.asarray(S[prev], np.float32)/65535.; despres = np.asarray(S[i], np.float32)/65535.
    g, _ = lunar_gate_single(ell[str(i)], XX, YY, *{4: (2.0, 10.0), 5: (3.0, 12.0), 7: (3.0, 16.0)}[i]); g[~frame_sel(i)] = 0
    res, _, _ = porta(abans, despres, masks[i], i, lum(layer_rgb_canvas(i)), g, f'{QA}/porta_ID{i}.json')
    print(f"ID{i} porta: {res['veredicte']} | mínims defecte {res['n_minims_defecte']} (nous {res['n_minims_nous_reportats']}) | empremta {res['empremta_no_radial_rms_pct']} % (max {res['empremta_no_radial_max_abs_pct']}) | nuclis dif {res['nuclis_dif_max_DN']} α {res['nuclis_alpha_max']} | fora {res['fora_suport_dif_max_DN']} | V1 {len(res['V1_minims_locals_lunar'])} | disc propi α {res['disc_propi']['alpha_max']} dif {res['disc_propi']['dif_max_DN']}", flush=True)
    for m in res['minims']:
        if m['defecte'] or (m['nou'] and m['prominencia_pct'] >= 0.7): print('    mínim:', m)
    cov = cobertura(dict(acc), f'S{i}', f'{QA}/cobertura_S{i}.json', solar_rmax={4: 1.65, 5: 2.4, 7: 3.0}[i])
    sa = sectors_absolut(despres, dict(acc), f'S{i}', f'{QA}/sectors_S{i}.json')
    for s_ in sa['sots'][:10]: print('    sot:', s_)
    summary[i] = dict(porta=res['veredicte'], minims_defecte=res['n_minims_defecte'], empremta=res['empremta_no_radial_rms_pct'], cobertura_ok=cov['ok'], cobertura_bad={k: v['n_bad'] for k, v in cov['zones'].items()}, sectors_sots=sa['n_sots'], sota_085=sa['n_cells_sota_085_abans_de_comparar_amb_capa'], pitjor=sa['pitjor_ratio_compost_sobre_capa'])
    prev = i
sa3 = sectors_absolut(np.asarray(S[3], np.float32)/65535., {}, 'S3', f'{QA}/sectors_S3.json')
cov3 = cobertura({}, 'S3', f'{QA}/cobertura_S3.json', solar_rmax=1.55)
pil = pilots([S[3], S[4], S[5], S[7]], ['ID3 sol', '+ID4 1/500', '+ID5 1/125', '+ID7 1/60'], f'{QA}/pilot')
overview(S[7], f'{QA}/compost_fonament_1de4.png')
summary['S3'] = dict(sectors_sots=sa3['n_sots'], cobertura_bad={k: v['n_bad'] for k, v in cov3['zones'].items()}); summary['pilots'] = pil
jdump(summary, f'{QA}/resum.json'); print(json.dumps({k: v for k, v in summary.items() if k != 'pilots'}, indent=1))
