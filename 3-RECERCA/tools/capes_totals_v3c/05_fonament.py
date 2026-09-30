"""Fonament V3c: màscares d'ID4, ID5, ID7 = rampa radial solar (lineal suavitzada σ 0,05 R☉) × porta lunar pròpia
(el·lipse mesurada al ràster) × (1−P3) [× (1−P4) per a 5 i 7]. r_a (inici de la rampa) = primer radi solar on la capa és
vàlida a TOTES les cel·les 5°×4 px (p50≤0,46, p95≤0,66); Δ (amplada) per cerca: la més curta que passa la porta de
costura sobre el compost real (0 mínims-defecte, V1 net) i, entre les que passen, la de menys pujada creada als sectors.
Baixada de cada capa: quan la següent ja és plena (+0,05) i abans que el seu SNR per anell caigui de 5 (amplada 0,2 R☉).
Env: GRID5/GRID7 ('Δ' o 'Δ:w', separats per comes); DOWN=1 per afegir baixades (per defecte NO: el final del rang
d'una capa del fonament el tapa la capa de sobre, i una baixada cap a una capa inferior que allà és soroll crea un mínim
—mesurat: 16 % a 2,7 R☉ per a la 1/125— i un vel al test de baix a dalt)."""
import numpy as np
from tests_v3c import *
from v3b_lib import created_rises
def _pairs(v): return [(float(x.split(':')[0]), float(x.split(':')[1]) if ':' in x else 1.0) for x in v.split(',')]
GRID5 = _pairs(os.environ.get('GRID5', '0.5'))
GRID7 = _pairs(os.environ.get('GRID7', '0.7,0.9,1.1'))
DOWN = os.environ.get('DOWN', '0') == '1'
def down(r0, r1): return (1-rampa(RS, r0, r1)) if DOWN else np.float32(1.0)
GATE = {4: (2.0, 10.0), 5: (3.0, 12.0), 7: (3.0, 16.0)}
QA = f'{SCR}/QA/cerca'; os.makedirs(QA, exist_ok=True)
def r_snr(i, s): return max(r['r'] for r in rang[str(i)] if r['snr'] >= s)
def floor_of(i): return float(np.median([r['medG'] for r in rang[str(i)] if r['r'] > 4.3]))
def gate_of(i):
    g, d = lunar_gate_single(ell[str(i)], XX, YY, *GATE[i]); g[~frame_sel(i)] = 0; return g
rep = {}
S3 = layer_rgb_canvas(3); np.save(f'{SCR}/states/S3.npy', quantize(S3))
g4, g5, g7 = gate_of(4), gate_of(5), gate_of(7)
prot4 = 1-np.asarray(P3); prot57 = prot4*(1-np.asarray(P4))
ra = {}
for i in (4, 5, 7):
    ra[i] = r_a_cells(i); print(f'ID{i}: r_a per cel·les = {ra[i][0]} ({ra[i][1]} cel·les invàlides per saturació); 1r anell vàlid per anell = {min(r["r"] for r in rang[str(i)] if r["p50"] <= 0.46 and r["p95"] <= 0.66)}', flush=True)
assert ra[4][0] is None, 'la 1/500 hauria de ser vàlida des del limbe'
def search(i, abans_f, r_a, gate, prot, grid):
    Lc = lum(layer_rgb_canvas(i)); La = lum(abans_f)
    cS, pA, SA = ring_medians(La, RS, 1.0, 4.6, 0.005, SEL, 24, AZS); _, pL, SL = ring_medians(Lc, RS, 1.0, 4.6, 0.005, SEL, 24, AZS)
    fl = floor_of(i); sim = {}; res_all = {}; chosen = None
    for D, wm in grid:
        w = wm*rampa(cS, r_a, r_a+D)
        sim[(D, wm)] = [round(100*created_rises(cS, pA, pL, w, fl), 3), round(100*max(created_rises(cS, SA[s], SL[s], w, fl) for s in range(24)), 3)]
        D_key = (D, wm)
        m = np.float32(wm)*rampa(RS, r_a, r_a+D)*gate*prot; m[~frame_sel(7)] = 0; mu = quantize(m)
        despres = compose_over(abans_f, i, mu)
        res, _, _ = porta(abans_f, despres, mu, i, Lc, gate, f'{QA}/porta_ID{i}_D{D}_w{wm}.json', extra=dict(r_a=r_a, delta=D, w_max=wm))
        res_all[f'{D}:{wm}'] = dict(D=D, w=wm, veredicte=res['veredicte'], minims_defecte=res['n_minims_defecte'], V1=len(res['V1_minims_locals_lunar']), empremta=res['empremta_no_radial_rms_pct'], sim=sim[(D, wm)],
                          pitjors=[dict(p=x['perfil'], r=x['r'], pct=x['prominencia_pct']) for x in sorted(res['minims'], key=lambda x: -x['prominencia_pct'])[:3]])
        print(f'   ID{i} Δ={D} w={wm}: {res_all[f"{D}:{wm}"]}', flush=True)
        if chosen is None and res['veredicte'] == 'ACCEPTADA': chosen = (D, wm)
        del despres
    if chosen is None:
        k = min(res_all, key=lambda k: (res_all[k]['minims_defecte'], res_all[k]['sim'][1])); chosen = (res_all[k]['D'], res_all[k]['w'])
    return chosen, {f'{a}:{b}': v for (a, b), v in sim.items()}, res_all
# ID4
r_b5_guess = None
# ID5 sobre 3+4 (4 amb porta lunar i P3; la seva baixada és més enllà de la rampa de la 5 i no hi influeix)
m4_tmp = g4*prot4; m4_tmp[~frame_sel(7)] = 0; m4_tmp = quantize(m4_tmp); S4tmp = compose_over(S3, 4, m4_tmp)
r_a5 = float(os.environ.get('R_A_5', ra[5][0]))   # R_A_MODE=anell: el 1r anell vàlid (research/84 §5, per anell)
(D5, W5), sim5, res5 = search(5, S4tmp, r_a5, g5, prot57, GRID5)
r_b5 = round(r_a5+D5, 3)
# baixada de la 4
rd4 = round(max(r_b5+0.05, r_snr(4, 5)-0.20), 3); rampa4 = (rd4, round(rd4+0.20, 3))
m4 = g4*prot4*down(*rampa4); m4[~frame_sel(7)] = 0; M4 = quantize(m4)   # ID4/ID5: ràster de llenç sencer amb vora blanca fora de la imatge (457,463)-(7417,5103): màscara 0 fora
S4 = compose_over(S3, 4, M4); np.save(f'{SCR}/states/S4.npy', quantize(S4))
up5 = np.float32(W5)*rampa(RS, r_a5, r_b5)
m5_tmp = up5*g5*prot57; m5_tmp[~frame_sel(7)] = 0
S5tmp = compose_over(S4, 5, quantize(m5_tmp))
r_a7 = float(os.environ.get('R_A_7', ra[7][0]))
(D7, W7), sim7, res7 = search(7, S5tmp, r_a7, g7, prot57, GRID7)
r_b7 = round(r_a7+D7, 3)
rd5 = round(max(r_b7+0.05, r_snr(5, 5)-0.20), 3); rampa5 = (rd5, round(rd5+0.20, 3))
m5 = up5*g5*prot57*down(*rampa5); m5[~frame_sel(7)] = 0; M5 = quantize(m5)
S5 = compose_over(S4, 5, M5); np.save(f'{SCR}/states/S5.npy', quantize(S5))
rd7 = round(r_snr(7, 5)-0.20, 3); rampa7 = (rd7, round(rd7+0.25, 3))
m7 = np.float32(W7)*rampa(RS, r_a7, r_b7)*g7*prot57*down(*rampa7); m7[~frame_sel(7)] = 0; M7 = quantize(m7)
S7 = compose_over(S5, 7, M7); np.save(f'{SCR}/states/S7.npy', quantize(S7))
masks = {4: M4, 5: M5, 7: M7}
rep = {4: dict(r_a=None, rampa_pujada=None, rampa_baixada=(rampa4 if DOWN else None), r_snr5=r_snr(4, 5), porta_lunar=dict(core_px=GATE[4][0], feather_px=GATE[4][1], ellipse=ell['4']), proteccio='(1-P3)'),
       5: dict(r_a=r_a5, r_a_cel·les_invalides=ra[5][1], delta=D5, w_max=W5, rampa_pujada=(r_a5, r_b5), cerca=res5, rampa_baixada=(rampa5 if DOWN else None), r_snr5=r_snr(5, 5), porta_lunar=dict(core_px=GATE[5][0], feather_px=GATE[5][1], ellipse=ell['5']), proteccio='(1-P3)(1-P4)'),
       7: dict(r_a=r_a7, r_a_cel·les_invalides=ra[7][1], delta=D7, w_max=W7, rampa_pujada=(r_a7, r_b7), cerca=res7, rampa_baixada=(rampa7 if DOWN else None), r_snr5=r_snr(7, 5), porta_lunar=dict(core_px=GATE[7][0], feather_px=GATE[7][1], ellipse=ell['7']), proteccio='(1-P3)(1-P4)')}
for i in (4, 5, 7):
    np.save(f'{SCR}/masks/mask_{i}.npy', masks[i]); rep[i]['mask_sha256_u16'] = sha256_u16(masks[i]); rep[i]['mask_max'] = int(masks[i].max())
    d = d_moon(ell[str(i)], XX, YY); rep[i]['alpha_max_disc_propi_R+2'] = int(masks[i][d <= R_eq(ell[str(i)])+2].max())
    rep[i]['alpha_max_P3'] = int(masks[i][np.asarray(P3) >= 1].max()); rep[i]['alpha_max_P4'] = int(masks[i][np.asarray(P4) >= 1].max()) if i != 4 else None
    # valor de la màscara dins la banda d'artefacte d'ID7 (R+21..R+48 cap a 150°) per documentar la tria de porta
    if i == 7:
        d7_, az7_, R7_ = lunar_coords(7); band = (d7_ > R7_+21) & (d7_ <= R7_+48) & (az7_ > 120) & (az7_ < 185)
        rep[i]['alpha_max_dins_banda_apilat_pct'] = round(100*float(masks[i][band].max())/65535, 3); rep[i]['alpha_mean_dins_banda_apilat_pct'] = round(100*float(masks[i][band].mean())/65535, 3)
    print(i, {k: v for k, v in rep[i].items() if k not in ('porta_lunar', 'cerca')}, flush=True)
jdump(rep, f'{SCR}/QA/fonament_disseny.json')
