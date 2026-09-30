"""s11 · La prova Lluna/corona i la ρ en sectors de 20° a 200–300° (la c1 de la V105 contra la separació), des dels npz desats."""
import numpy as np, json
import proves
proves.SECTORS = [(200, 220), (220, 240), (240, 260), (260, 280), (280, 300)]
proves.DS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]
def carrega(f):
    z = np.load(f, allow_pickle=True); C = {int(r[0]): (r[1], r[2]) for r in z['centres']}
    A = [j for j in C if j <= 10]; B = [j for j in C if 13 <= j <= 18]
    dg = z['dgrid'].astype(float); nth = int(z['nth'])
    m = proves.m1(dg, nth, z['hA'], z['pA'], z['hB'], z['pB'], np.mean([C[j] for j in A], 0), np.mean([C[j] for j in B], 0))
    r = proves.rho(dg, nth, np.nan_to_num(z['h125']), z['p125'], np.nan_to_num(z['hcurts']), z['pcurts'], sectors=proves.SECTORS, ds=proves.DS)
    return m, r
mc, rc = carrega('/Users/USUARI/Desktop/Eclipse 2026/4-RESULTATS/v105_limbe_20260926/claude/t2/DELTA_sigc32.npz')
ms, rs = carrega('DELTA_sep_final.npz')
out = {}
print('fracció lunar / ρ  ·  V105 c1  |  separació')
for sec in proves.SECTORS:
    print(f'== {sec[0]}-{sec[1]}')
    for d in proves.DS:
        k = (sec[0], sec[1], d)
        f = lambda m, r: (f"{m[k]['f']:+.2f}" if k in m else '  -  ') + '/' + (f"{r[k][0]:.2f}" if k in r else ' - ')
        print(f'  d{d:3.1f}: {f(mc, rc):>12} | {f(ms, rs):>12}')
        out[f'{sec[0]}-{sec[1]} d{d}'] = dict(v105_c1=f(mc, rc), separacio=f(ms, rs))
json.dump(out, open('SUBSECTORS_final.json', 'w'), indent=1)
