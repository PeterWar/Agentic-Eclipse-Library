"""Quantifica la reserva de cobertura: a les cel·les <0,9, quin és el p95 real de la capa que hi contribueix sense ser vàlida
i quant hi pesa."""
import numpy as np
from tests_v3c import *
state = sys.argv[1]; ids = [int(x) for x in sys.argv[2].split(',')]
masks = {i: np.load(f'{SCR}/masks/mask_{i}.npy') for i in ids if i != 3}
W = effective_weights(masks)
d7, az7, R7 = lunar_coords(7); edges = np.arange(R7+3, 1.5*R_SUN+(R7-R_SUN)+1e-3, 4.0)
cov = json.load(open(f'{SCR}/QA/{"fonament" if state in ("S4","S5","S7") else "cadena"}/cobertura_{state}.json'))
rows = []
for c in cov['zones']['lunar_R+3_a_1.5Rsun']['bad_cells']:
    s = int(c['sector_deg']/5); r = int(round((c['r']+R7-edges[0])/4.0))
    row = dict(sector=c['sector_deg'], r_px=c['r'], cobertura=c['cobertura'], capes_invalides={})
    for i in ids:
        V, P50, P95 = cell_validity(i, d7, az7, edges, 72, True)
        Wm, n = cell_mean(W[i], d7, az7, edges, 72, SEL & ~PROT)
        if not V[s, r] and np.nan_to_num(Wm)[s, r] > 0.02:
            row['capes_invalides'][i] = dict(pes=round(float(Wm[s, r]), 3), p50=round(float(P50[s, r]), 3), p95=round(float(P95[s, r]), 3))
    rows.append(row)
jdump(rows, f'{SCR}/QA/reserva_cobertura_{state}.json')
p95s = [v['p95'] for row in rows for v in row['capes_invalides'].values()]; pes = [v['pes'] for row in rows for v in row['capes_invalides'].values()]
print(state, 'cel·les', len(rows), 'p95 de la capa no vàlida: min/max', min(p95s) if p95s else None, max(p95s) if p95s else None, 'pes max', max(pes) if pes else None)
for row in rows[:6]: print(row)
