import numpy as np, json, math
exec(open('corba.py').read().split("t_now, coef_now")[0])  # reutilitza definicions
cands = [(0.82,0.60,0.15),(0.79,0.48,0.17),(0.80,0.50,0.175),(0.80,0.52,0.18),(0.80,0.55,0.18),(0.78,0.50,0.18)]
radis = (1.15,1.25,1.5,1.75,2.05,2.25,2.55,3.05,3.55,4.05,4.55,5.05,6.05,6.85,7.55,8.05)
print('r      sketchY ' + ' '.join(f'{c}' for c in cands))
res = {}
for c in cands:
    t, _ = corba(c, u0); res[c] = t
for r0 in radis:
    i = np.argmin(np.abs(rm-r0)); k = np.argmin(np.abs(rs-r0))
    print(f'{r0:5.2f}  {Ys[k]:.4f}  ' + '  '.join(f'{res[c][i]:.4f}' for c in cands))
print('rms log (1.1-8.5, pes cobertura):')
for c in cands:
    m = rm >= 1.1; w = np.sqrt(np.interp(rm[m], rs, cs))
    e = (np.log(res[c][m]) - np.log(np.interp(rm[m], rs, Ys)))*w
    print(c, round(float(np.sqrt(np.mean(e**2))),4))
print('pendent d ln t/d ln L:')
lnL = np.log(Lm)
for c in cands:
    sl = np.gradient(np.log(res[c]), lnL)
    print(c, {float(r0): round(float(np.interp(r0, rm, sl)),2) for r0 in (1.5,2,2.5,3,4,5,6,7,8)})
# amplitud a pantalla de l'anell de ±1.7 % (lineal) a 5.2 R_sol amb cada corba
for c in cands:
    sl = np.gradient(np.log(res[c]), lnL); s52 = float(np.interp(5.2, rm, sl))
    print(c, f"anell +-1.7% lineal a 5.2 -> +-{1.7*s52:.1f} % a pantalla; caiguda cel 6.5->8 R_sol a pantalla: {100*(res[c][np.argmin(np.abs(rm-8.05))]/res[c][np.argmin(np.abs(rm-6.55))]-1):.1f} %")
