"""07 — Cadena V4: ID8 → ID9 → … → ID17 sobre el fonament V4. Mateix mètode que V3c (rampa lineal
suavitzada × porta lunar per membre de l'apilat × protecció P3/P4, pes w_max del disseny, cerca per
simulació i confirmació per la porta). Diferències de domini (llindars IDÈNTICS): els perfils solars
i el domini de defecte s'estenen fins a r_b + marge per a les capes que entren més lluny de 3 R☉.
Env: GRIDi='Δ:w,…', R_A_i=…, START=7."""
import numpy as np
from v4_tests import *
from v4_tests import _P3, _P4
from g5_11_gate import (CHAIN_IDS, FOUNDATION_LAYER_IDS, FOUNDATION_STATES,
                        artifact_record, artifact_record_matches, candidate_pass,
                        coverage_gate_snapshot, foundation_gate, g5_10_snapshot,
                        sha256_file)

ids = [int(s) for s in sys.argv[1:]] or [8, 9, 10, 11, 12, 13, 16, 17]
START = int(os.environ.get('START', 7))
if START != 7 or tuple(ids) != CHAIN_IDS:
    raise SystemExit(f'CADENA NO CANÒNICA: cal START=7 i ordre complet {list(CHAIN_IDS)}; '
                     f'rebut START={START}, ids={ids}')
QA = V4W / 'QA/cadena'
def _occupied(path):
    return path.exists() or path.is_symlink()

_existing = [str(path) for i in CHAIN_IDS
             for path in (V4W / f'masks/mask_{i}.npy', V4W / f'states/S{i}.npy')
             if _occupied(path)]
if QA.is_symlink() or (QA.exists() and any(QA.iterdir())):
    _existing.append(str(QA))
if _existing:
    raise SystemExit(f'NO-CLOBBER CADENA: ja existeixen outputs: {_existing}')
foundation_receipt_path = V4W / 'QA/fonament/resum.json'
if not foundation_receipt_path.exists():
    raise SystemExit('FONAMENT NO SEGELLAT: falta QA/fonament/resum.json')
with open(foundation_receipt_path) as fh:
    foundation_receipt = json.load(fh)
foundation_check = foundation_gate(foundation_receipt)
if not foundation_check['ok']:
    raise SystemExit(f'FONAMENT NO PROMOCIONABLE: {foundation_check["failures"]}')
foundation_artifacts = foundation_receipt['artifacts']
artifact_failures = []
for foundation_state in FOUNDATION_STATES:
    path = V4W / f'states/{foundation_state}.npy'
    if not artifact_record_matches(foundation_artifacts['states'][foundation_state], path):
        artifact_failures.append(str(path))
for foundation_layer_id in FOUNDATION_LAYER_IDS:
    path = V4W / f'masks/mask_{foundation_layer_id}.npy'
    if not artifact_record_matches(foundation_artifacts['masks'][str(foundation_layer_id)], path):
        artifact_failures.append(str(path))
if artifact_failures:
    raise SystemExit(f'FONAMENT STALE O ALTERAT: no coincideixen els artefactes vius: {artifact_failures}')
os.makedirs(QA, exist_ok=True)
prot = (1 - np.asarray(_P3)) * (1 - np.asarray(_P4))
abans_u16 = np.load(V4W / f'states/S{START}.npy')
abans = np.asarray(abans_u16, np.float32) / 65535.0
state = f'S{START}'
masks = {i: np.load(V4W / f'masks/mask_{i}.npy') for i in FOUNDATION_LAYER_IDS}
receipt = {'_contract': {'gate': 'CHAIN_SEQUENCE', 'status': 'IN_PROGRESS',
                         'start_state': 'S7', 'layer_ids': list(CHAIN_IDS)}}
prev_id = START
for i in ids:
    predecessor_state = f'S{prev_id}'
    predecessor_path = V4W / f'states/{predecessor_state}.npy'
    predecessor_sha256 = sha256_file(predecessor_path)
    rows = rang[str(i)]
    r_a_ring = float(min(r['r'] for r in rows if r.get('sat_frac', 1) <= 0.5 and r.get('snr', 0) >= 5))
    r_a_cell, n_inv = r_a_cells(i)
    r_a = r_a_ring if os.environ.get('R_A_MODE', 'anell') == 'anell' else max(r_a_ring, r_a_cell or 0.0)
    # entrada per defecte no abans de la vora del plateau de la capa precedent (SNR): últim anell
    # amb sat_frac ≥ 0,5 de la precedent, menys 0,1 R☉ de solapament
    rows_p = rang.get(str(prev_id), [])
    edges_p = [r['r'] for r in rows_p if r.get('sat_frac', 0) >= 0.5]
    if edges_p:
        r_a = max(r_a, round(max(edges_p) - 0.1, 3))
    r_a = float(os.environ.get(f'R_A_{i}', r_a))
    Lc = lum(layer_rgb_canvas(i))
    La = lum(abans)
    cS, pA, SA = ring_medians(La, RS, 1.0, 4.6, 0.005, SEL, 24, AZS)
    _, pL, SL = ring_medians(Lc, RS, 1.0, 4.6, 0.005, SEL, 24, AZS)
    floor_L = float(np.nanmedian(pL[cS > 4.3])) if (cS > 4.3).any() else float(np.nanmin(pL))
    r_lin = min([r['r'] for r in rows if r.get('snr', 0) >= 10 and r['r'] >= r_a] or [r_a + 0.25])
    sim = {}
    cands = []
    for D in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0, 1.2):
        if r_a + D < r_lin:
            continue
        for wm in np.round(np.arange(1.0, 0.19, -0.05), 2):
            w = wm * rampa(cS, r_a, r_a + D)
            g = created_rises(cS, pA, pL, w, floor_L)
            sw = max(created_rises(cS, SA[s], SL[s], w, floor_L) for s in range(24))
            sim[f'D={D}_w={wm}'] = [round(100 * g, 3), round(100 * sw, 3)]
            if g < 0.002 and sw < 0.005:
                cands.append((-(float(wm)), D, float(wm)))
    cands.sort()
    cands = [(D, wm) for _, D, wm in cands][:4] or [(0.5, 1.0), (0.7, 1.0), (0.9, 1.0), (0.7, 0.8), (0.9, 0.8), (0.9, 0.6)]
    if os.environ.get(f'GRID{i}'):
        cands = [(float(x.split(':')[0]), float(x.split(':')[1])) for x in os.environ[f'GRID{i}'].split(',')]
    print(f'== ID{i} ({LAYER_PREFIX[i]}): r_a anell {r_a_ring}, cel·les {r_a_cell} ({n_inv} inv.) → r_a={r_a}; '
          f'r_lin={r_lin}; candidats {cands}', flush=True)
    gate_l, _ = band_gate(i, ell[str(i)], XX, YY)
    gate_l[~frame_sel(i)] = 0
    from scipy import ndimage as _ndi
    # la capa no pot contribuir on ella mateixa és saturada: factor per píxels (1 − sat) amb ploma 1+2 px
    satc = np.asarray(np.load(V4W / 'npy' / f'sat_{i}.npy', mmap_mode='r'))
    dist_sat = _ndi.distance_transform_edt(~satc)
    fsat = np.ones((CH, CW), np.float32)
    fsat[dist_sat <= 1.0] = 0.0
    zsat = (dist_sat > 1.0) & (dist_sat < 3.0)
    fsat[zsat] = smootherstep((dist_sat[zsat] - 1.0) / 2.0)
    prot_i = prot * fsat
    chosen = None
    tried = {}
    for D, wm in cands:
        m = np.float32(wm) * rampa(RS, r_a, r_a + D) * gate_l * prot_i
        m[~frame_sel(i)] = 0
        mu = quantize(m)
        despres_unquantized = compose_over(abans, i, mu)
        despres_u16 = quantize(despres_unquantized)
        del despres_unquantized
        despres = np.asarray(despres_u16, np.float32) / 65535.0
        r_b = r_a + D
        res, Qa, Qd = porta(abans, despres, mu, i, Lc, gate_l, f'{QA}/porta_ID{i}_D{D}_w{wm}.json',
                            extra=dict(r_a_rsun=r_a, r_a_anell=r_a_ring, r_a_cel·les=r_a_cell, r_b_rsun=round(r_b, 3),
                                       w_max=wm, r_lin_rsun=r_lin, simulacio_pct=sim, abans=state),
                            r_solar_max=min(12.0, r_b + 1.5), r_def=min(12.0, r_b + 0.5),
                            excl=dist_sat <= 3.0, r_empremta_max=min(12.0, r_b + 0.5))
        candidate_masks = dict(masks)
        candidate_masks[i] = mu
        cov = cobertura(candidate_masks, f'S{i}', f'{QA}/cobertura_S{i}_D{D}_w{wm}.json',
                        solar_rmax=min(12.0, r_a + D + 0.5))
        sa_candidate = sectors_absolut(despres, candidate_masks, f'S{i}',
                                       f'{QA}/sectors_S{i}_D{D}_w{wm}.json')
        g5_11 = coverage_gate_snapshot(cov, f'S{i}')
        g5_10 = g5_10_snapshot(sa_candidate, f'S{i}')
        tried[f'D={D}_w={wm}'] = dict(veredicte=res['veredicte'], minims_defecte=res['n_minims_defecte'],
                                      empremta=res['empremta_no_radial_rms_pct'], V1=len(res['V1_minims_locals_lunar']),
                                      g5_11=g5_11, g5_10=g5_10,
                                      pitjors=[dict(p=x['perfil'], r=x['r'], pct=x['prominencia_pct'])
                                               for x in sorted(res['minims'], key=lambda x: -x['prominencia_pct'])[:3]])
        print(f"   Δ={D} w={wm}: {tried[f'D={D}_w={wm}']}", flush=True)
        if chosen is None and candidate_pass(res['veredicte'], cov, sa_candidate, f'S{i}'):
            chosen = (D, wm, mu, despres, Qd, res, cov, sa_candidate)
            continue
        del despres
    if chosen is None:
        receipt['_contract']['status'] = 'FAIL'
        receipt['_contract']['failed_state'] = f'S{i}'
        receipt[str(i)] = dict(veredicte='REBUTJADA', r_a=r_a,
                               g5_10='NO_CANDIDATE_PASSED', g5_11='NO_CANDIDATE_PASSED', provats=tried)
        jdump(receipt, f'{QA}/cadena.json')
        raise SystemExit(f'ID{i} REBUTJADA: cap candidata passa porta + G5.10 + G5.11; cadena aturada')
    D, wm, mu, despres, Qd, res, cov, sa = chosen
    mask_path = V4W / f'masks/mask_{i}.npy'
    state_path = V4W / f'states/S{i}.npy'
    np.save(mask_path, mu)
    masks[i] = mu
    np.save(state_path, Qd)
    jdump(cov, f'{QA}/cobertura_S{i}.json')
    jdump(sa, f'{QA}/sectors_S{i}.json')
    receipt[str(i)] = dict(
        veredicte='ACCEPTADA', r_a=r_a, r_b=round(r_a + D, 3), delta=D, w_max=wm,
        mask_sha256_u16=sha256_u16(mu), mask_max=int(mu.max()), provats=tried,
        porta=dict(minims_defecte=res['n_minims_defecte'], nous=res['n_minims_nous_reportats'],
                   empremta=res['empremta_no_radial_rms_pct'], nuclis_dif=res['nuclis_dif_max_DN'],
                   fora=res['fora_suport_dif_max_DN']),
        g5_11=coverage_gate_snapshot(cov, f'S{i}'), g5_10=g5_10_snapshot(sa, f'S{i}'),
        predecessor_state=predecessor_state, predecessor_state_sha256=predecessor_sha256,
        mask_artifact=artifact_record(mask_path), state_artifact=artifact_record(state_path),
        cobertura_bad={k: v['n_bad'] for k, v in cov['zones'].items()}, sectors_sots=sa['n_sots'],
        alpha_max_P3=int(mu[np.asarray(_P3) >= 1].max()), alpha_max_P4=int(mu[np.asarray(_P4) >= 1].max()))
    abans = np.asarray(Qd, np.float32) / 65535.0
    prev_id = i
    state += f'+{i}'
    print(f'   ID{i} ACCEPTADA Δ={D} w={wm}', flush=True)
receipt['_contract']['status'] = 'PASS'
receipt['_contract']['final_state'] = f'S{CHAIN_IDS[-1]}'
jdump(receipt, f'{QA}/cadena.json')
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'provats'} for k, v in receipt.items()}, indent=1))
