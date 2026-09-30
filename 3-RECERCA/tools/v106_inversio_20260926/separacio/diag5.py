"""Geometria per fotograma: sense correcció, correccions de centre del b1 (PSF+LOLA), o autocalibratge amb pesos IRLS.
Mesura: dispersió del residu per fotograma a D < 2 i 2–4 (mediana sobre fotogrames), i el χ²."""
import numpy as np, json, sys
from pipeline import Pipeline
B1 = {r['j']: r for r in json.load(open('/Users/USUARI/Desktop/Eclipse 2026/4-RESULTATS/v106_inversio_20260926/b1/B1_PSF_LOLA_canal1.json'))['fotogrames']}
P = Pipeline({})
def mesura(I, tag):
    L = I.L; res = L['y'] - I.C.ravel()[L['p']] - I.pred_lun; h = L['w'] / I.Wt[L['p']]; q = res ** 2 / np.maximum(1 - h, 0.1)
    out = []
    for lo, hi in [(0.6, 1.2), (1.2, 2.0), (2.0, 3.0), (3.0, 4.0)]:
        per = [np.sqrt(np.mean(q[(L['j'] == j) & (L['D'] >= lo) & (L['D'] < hi) & (h < 0.9)])) for j in P.fr if ((L['j'] == j) & (L['D'] >= lo) & (L['D'] < hi)).sum() > 300]
        out.append(np.median(per))
    print(tag, 'σ mediana per fotograma a D [0.6,1.2) [1.2,2) [2,3) [3,4):', ' '.join(f'{v:.3f}' for v in out), '| χ²', round(float(np.mean(L['w'] * res ** 2)), 3), flush=True)
I = P.inverteix(P.fr); mesura(I, 'sense correcció')
vt = I.var_tab
I2 = P.nova()
for j in P.fr:
    if j in B1: I2.dxy[j] = (B1[j]['dx'], B1[j]['dy'])
I2 = P.inverteix(P.fr, var_tab=vt, I=I2); mesura(I2, 'centres del b1 ')
# autocalibratge amb pesos IRLS fixos
I3 = P.nova(); I3 = P.inverteix(P.fr, var_tab=vt, I=I3)
for it in range(6):
    out = I3.autocalibra(amplitud=False, dany=1.0)
    I3 = P.inverteix(P.fr, var_tab=vt, I=I3); mesura(I3, f'autocal {it}  ')
np.savez('DXY_autocal.npz', dxy=I3.dxy)
print('autocal dxy:', ' '.join(f'{j}:{I3.dxy[j,0]:+.2f},{I3.dxy[j,1]:+.2f}' for j in P.fr))
print('b1 dxy     :', ' '.join(f'{j}:{B1[j]["dx"]:+.2f},{B1[j]["dy"]:+.2f}' for j in P.fr if j in B1))
m = [j for j in P.fr if j in B1]
print('correlació autocal vs b1: x', np.corrcoef(I3.dxy[m, 0], [B1[j]['dx'] for j in m])[0, 1], ' y', np.corrcoef(I3.dxy[m, 1], [B1[j]['dy'] for j in m])[0, 1])
