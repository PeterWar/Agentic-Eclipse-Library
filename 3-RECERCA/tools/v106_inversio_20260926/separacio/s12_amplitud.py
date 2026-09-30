import numpy as np, json, sys
import proves
from pipeline import Pipeline
cfg = json.loads(sys.argv[1])
P = Pipeline(cfg); R = P.proves(verbose=True)
print('A_j:', ' '.join(f'{j}:{R["IT"].A[j]:.2f}' for j in P.fr))
proves.SECTORS = [(220, 240), (240, 260), (260, 280)]
S = R['IT'].S; i4 = S.i4; dg = S.dg[i4:]
m = proves.m1(dg, S.nth, R['hA'][i4:], R['pA'][i4:], R['hB'][i4:], R['pB'][i4:], R['cA'], R['cB'])
W1 = R['I1'].Wt.reshape(R['I1'].C.shape); W2 = R['I2'].Wt.reshape(R['I2'].C.shape)
r = proves.rho(dg, S.nth, R['I1'].C[i4:], W1[i4:], R['I2'].C[i4:], W2[i4:], sectors=proves.SECTORS)
for sec in proves.SECTORS:
    print(f'{sec[0]}-{sec[1]}: ' + ' '.join(f"d{d:g}:{m[(sec[0],sec[1],d)]['f']:+.2f}/{r.get((sec[0],sec[1],d),(np.nan,))[0]:.2f}" for d in proves.DS if (sec[0], sec[1], d) in m))
