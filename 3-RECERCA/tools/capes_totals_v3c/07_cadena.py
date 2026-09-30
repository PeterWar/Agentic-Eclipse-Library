"""Cadena ID8 → ID9 → ID10 sobre el fonament V3c (mètode de V3b: rampa lineal suavitzada × porta lunar per membre de
l'apilat × protecció; pes màxim w_max part del disseny), amb la protecció NOVA per píxels (P3/P4) i cap zero heretat.
r_a = màx(1r anell vàlid, 1r radi vàlid a totes les cel·les). Cerca (Δ, w_max) per simulació i confirmació per la porta."""
import numpy as np
from tests_v3c import *
from v3b_lib import created_rises, band_gate
ids = [int(s) for s in sys.argv[1:]] or [8, 9, 10]
QA = f'{SCR}/QA/cadena'; os.makedirs(QA, exist_ok=True)
prot = (1-np.asarray(P3))*(1-np.asarray(P4))
rang_v3b = json.load(open(f'{V3B}/rang.json'))
START = int(os.environ.get('START', 7))   # estat de partida: S<START> amb les màscares fins a START
abans_u16 = np.load(f'{SCR}/states/S{START}.npy'); abans = np.asarray(abans_u16, np.float32)/65535.; state = f'S{START}'
masks = {i: np.load(f'{SCR}/masks/mask_{i}.npy') for i in (4, 5, 7, 8, 9) if i <= START}
receipt = {}
for i in ids:
    rows = rang_v3b[str(i)]
    r_a_ring = float(min(r['r'] for r in rows if r['p50'] <= 0.46 and r['p95'] <= 0.66))
    r_a_cell, n_inv = r_a_cells(i)
    r_a = r_a_ring if os.environ.get('R_A_MODE', 'anell') == 'anell' else max(r_a_ring, r_a_cell or 0.0)   # per anell (research/84 §5); el nivell per cel·les es reporta
    r_a = float(os.environ.get(f'R_A_{i}', r_a))   # entrada posposada admesa (més conservadora)
    Lc = lum(layer_rgb_canvas(i)); La = lum(abans)
    cS, pA, SA = ring_medians(La, RS, 1.0, 4.6, 0.005, SEL, 24, AZS); _, pL, SL = ring_medians(Lc, RS, 1.0, 4.6, 0.005, SEL, 24, AZS)
    floor_L = float(np.nanmedian(pL[cS > 4.3]))
    r_lin = min([r['r'] for r in rows if r['p50'] <= 0.20 and r['r'] >= r_a] or [r_a+0.25])
    sim = {}; cands = []
    for D in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
        if r_a + D < r_lin: continue
        for wm in np.round(np.arange(1.0, 0.19, -0.05), 2):
            w = wm*rampa(cS, r_a, r_a+D)
            g = created_rises(cS, pA, pL, w, floor_L); sw = max(created_rises(cS, SA[s], SL[s], w, floor_L) for s in range(24))
            sim[f'D={D}_w={wm}'] = [round(100*g, 3), round(100*sw, 3)]
            if g < 0.002 and sw < 0.005: cands.append((-(float(wm)), D, float(wm)))
    cands.sort(); cands = [(D, wm) for _, D, wm in cands][:4] or [(0.5, 1.0), (0.7, 1.0), (0.9, 1.0), (0.7, 0.8), (0.9, 0.8), (0.9, 0.6)]
    if os.environ.get(f'GRID{i}'):   # graella explícita (Δ:w) provada directament per la porta, sense passar per la simulació
        cands = [(float(x.split(':')[0]), float(x.split(':')[1])) for x in os.environ[f'GRID{i}'].split(',')]
    print(f'== ID{i}: r_a anell {r_a_ring}, cel·les {r_a_cell} ({n_inv} inv.) → r_a={r_a}; r_lin={r_lin}; candidats {cands}', flush=True)
    gate_l, _ = band_gate(i, XX, YY)
    chosen = None; tried = {}
    for D, wm in cands:
        m = np.float32(wm)*rampa(RS, r_a, r_a+D)*gate_l*prot; m[~frame_sel(i)] = 0; mu = quantize(m)
        despres = compose_over(abans, i, mu)
        res, Qa, Qd = porta(abans, despres, mu, i, Lc, gate_l, f'{QA}/porta_ID{i}_D{D}_w{wm}.json', extra=dict(r_a_rsun=r_a, r_a_anell=r_a_ring, r_a_cel·les=r_a_cell, r_b_rsun=round(r_a+D, 3), w_max=wm, r_lin_rsun=r_lin, simulacio_pct=sim, abans=state))
        tried[f'D={D}_w={wm}'] = dict(veredicte=res['veredicte'], minims_defecte=res['n_minims_defecte'], empremta=res['empremta_no_radial_rms_pct'], V1=len(res['V1_minims_locals_lunar']),
                                     pitjors=[dict(p=x['perfil'], r=x['r'], pct=x['prominencia_pct']) for x in sorted(res['minims'], key=lambda x: -x['prominencia_pct'])[:3]])
        print(f"   Δ={D} w={wm}: {tried[f'D={D}_w={wm}']}", flush=True)
        if res['veredicte'] == 'ACCEPTADA' and (chosen is None or wm > chosen[1]):
            if chosen is not None: del chosen
            chosen = (D, wm, mu, despres, Qd, res); continue
        del despres
    if chosen is None:
        receipt[i] = dict(veredicte='REBUTJADA', r_a=r_a, provats=tried); print(f'   ID{i} REBUTJADA', flush=True); continue
    D, wm, mu, despres, Qd, res = chosen
    np.save(f'{SCR}/masks/mask_{i}.npy', mu); masks[i] = mu
    np.save(f'{SCR}/states/S{i}.npy', Qd)
    cov = cobertura(dict(masks), f'S{i}', f'{QA}/cobertura_S{i}.json')
    sa = sectors_absolut(despres, dict(masks), f'S{i}', f'{QA}/sectors_S{i}.json')
    receipt[i] = dict(veredicte='ACCEPTADA', r_a=r_a, r_b=round(r_a+D, 3), delta=D, w_max=wm, mask_sha256_u16=sha256_u16(mu), mask_max=int(mu.max()), provats=tried,
                      porta=dict(minims_defecte=res['n_minims_defecte'], nous=res['n_minims_nous_reportats'], empremta=res['empremta_no_radial_rms_pct'], nuclis_dif=res['nuclis_dif_max_DN'], fora=res['fora_suport_dif_max_DN']),
                      cobertura_bad={k: v['n_bad'] for k, v in cov['zones'].items()}, sectors_sots=sa['n_sots'], alpha_max_P3=int(mu[np.asarray(P3) >= 1].max()), alpha_max_P4=int(mu[np.asarray(P4) >= 1].max()))
    abans = despres; state += f'+{i}'
    print(f'   ID{i} ACCEPTADA Δ={D} w={wm}', flush=True)
jdump(receipt, f'{QA}/cadena.json'); print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'provats'} for k, v in receipt.items()}, indent=1))
