"""s10 · Comparació justa: la MATEIXA prova (mateixos fotogrames S1/S2, mateixos pesos IRLS) amb el δ cru (sense separar, com la c1 sense
rampa) i amb la separació; i la c1 de la V105 (la seva rampa i els seus grups) com a referència."""
import numpy as np, json, sys
from pipeline import Pipeline
from proves import m1, rho, taula
cfg = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
P = Pipeline(cfg); R = P.proves(verbose=False); I1, I2, IT = R['I1'], R['I2'], R['IT']; S = IT.S; i4 = S.i4; dg = S.dg[i4:]; nth = S.nth
l1, l2 = I1.lam.copy(), I2.lam.copy(); I1.lam[:] = 0; I2.lam[:] = 0
hA0, pA0 = I1.grup(P.A); hB0, pB0 = I2.grup(P.B); C10, W10 = I1.grup(P.S1); C20, W20 = I2.grup(P.S2)
I1.lam[:] = l1; I2.lam[:] = l2
m_cru = m1(dg, nth, hA0[i4:], pA0[i4:], hB0[i4:], pB0[i4:], R['cA'], R['cB']); r_cru = rho(dg, nth, C10[i4:], W10[i4:], C20[i4:], W20[i4:])
z = np.load('/Users/USUARI/Desktop/Eclipse 2026/4-RESULTATS/v105_limbe_20260926/claude/t2/DELTA_sigc32.npz')
r_c1 = rho(z['dgrid'].astype(float), int(z['nth']), np.nan_to_num(z['h125']), z['p125'], np.nan_to_num(z['hcurts']), z['pcurts'])
Cz = {int(r[0]): (r[1], r[2]) for r in z['centres']}; A = [j for j in Cz if j <= 10]; B = [j for j in Cz if 13 <= j <= 18]
m_c1 = m1(z['dgrid'].astype(float), int(z['nth']), z['hA'], z['pA'], z['hB'], z['pB'], np.mean([Cz[j] for j in A], 0), np.mean([Cz[j] for j in B], 0))
def fila(m, r, sec, d):
    k = (sec[0], sec[1], d); f = m[k]['f'] if k in m else np.nan; rr = r[k][0] if k in r else np.nan
    return f'{f:+.2f}/{rr:.2f}'
out = {}
print('fracció lunar / ρ   ·  columnes: V105 c1 (rampa 0,6–2; ρ 1/125 vs curts) | δ cru amb els pesos i grups de la separació | SEPARACIÓ (inversió conjunta)')
for sec in [(60, 100), (100, 140), (200, 240), (240, 280), (280, 320)]:
    print(f'== {sec[0]}-{sec[1]}')
    for d in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]:
        a, b, c = fila(m_c1, r_c1, sec, d), fila(m_cru, r_cru, sec, d), fila(R['m1'], R['rho'], sec, d)
        if 'nan/nan' in a + b + c and a == b == c: continue
        print(f'  d{d:3.1f}:  {a:>12} | {b:>12} | {c:>12}')
        out[f'{sec[0]}-{sec[1]} d{d}'] = dict(v105_c1=a, cru=b, separacio=c)
json.dump(out, open('COMPARACIO_final.json', 'w'), indent=1)
