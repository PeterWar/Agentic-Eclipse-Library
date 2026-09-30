import numpy as np, json, math
from scipy.optimize import least_squares
lin = json.load(open('lineal.json')); per = json.load(open('perfils.json'))
lo, hi = 275.8047409057617, 1200409.0
def a_u0(x):
    u = (np.log10(np.maximum(x, lo*0.5)) - math.log10(lo))/(math.log10(hi)-math.log10(lo))
    u = np.where(u > 0.06, u, 0.06*np.exp(np.minimum(u-0.06, 0)/0.06))
    return np.clip(u, 1e-4, None)
rm = np.array([d['r0']+0.05 for d in lin['files']]); Lm = np.array([d['L'] for d in lin['files']])
u0 = a_u0(Lm)
def u0_a(r0):   # mediana de u0 a l'anell r0*0.97..1.03 (aprox: interpolem el perfil)
    return float(np.interp(r0, rm, u0))
def corba(niv, u):
    ancs = [(math.log(u0_a(r0)), math.log(n)) for r0, n in zip((1.05, 2.0, 6.8), niv)]
    A = np.array([[1.0, a, a*a] for a, _ in ancs]); coef = np.linalg.solve(A, np.array([b for _, b in ancs]))
    lu = np.log(u); t = np.exp(coef[0] + coef[1]*lu + coef[2]*lu**2)
    nn = niv[0]
    t = np.where(u > math.exp(ancs[0][0]), nn + (1-nn)*(1-np.exp(-(u/math.exp(ancs[0][0]) - 1)*3)), t)
    return np.clip(t, 0, 1), coef
# perfils mesurats (Y) sketch i foto
def prof(name, key='Y'):
    rr, vv, cc = [], [], []
    for d in per[name]:
        if key in d: rr.append(d['rmid']); vv.append(d[key]); cc.append(d['cob'])
    return np.array(rr), np.array(vv), np.array(cc)
rs, Ys, cs = prof('sketch'); rf, Yf, cf = prof('foto')
rs_G, Gs, _ = prof('sketch', 'G')
t_now, coef_now = corba((0.82, 0.60, 0.15), u0)
print('coef actuals', coef_now)
print(' r    u0     t_model(0.82/0.60/0.15)  FOTO Y   sketch Y')
for r0 in (1.05,1.15,1.25,1.35,1.5,1.75,2.05,2.25,2.55,3.05,3.55,4.05,4.55,5.05,5.55,6.05,6.55,6.85,7.55,8.05):
    i = np.argmin(np.abs(rm-r0)); j = np.argmin(np.abs(rf-r0)); k = np.argmin(np.abs(rs-r0))
    print(f'{r0:5.2f} {u0[i]:.4f}   {t_now[i]:.4f}      {Yf[j]:.4f}   {Ys[k]:.4f}')
# pendent local d ln t / d ln L
lnL = np.log(Lm); lnt = np.log(t_now)
sl = np.gradient(lnt, lnL)
print('pendent d ln t/d ln L (model actual):', {float(r0): round(float(np.interp(r0, rm, sl)),2) for r0 in (1.2,1.5,2,2.5,3,4,5,6,7,8)})
# pendent implicat pel sketch: d ln Y_sk / d ln L
Ys_i = np.interp(rm, rs, Ys)
sl_sk = np.gradient(np.log(Ys_i), lnL)
print('pendent implicat pel sketch:', {float(r0): round(float(np.interp(r0, rm, sl_sk)),2) for r0 in (1.2,1.5,2,2.5,3,4,5,6,7,8)})
# ajust dels tres nivells al perfil Y del sketch, r>=1.1 (fora del rim pintat), pes = cobertura
def resid(p):
    t, _ = corba(p, u0)
    m = rm >= 1.1
    w = np.sqrt(np.interp(rm[m], rs, cs))
    return (np.log(t[m]) - np.log(np.interp(rm[m], rs, Ys)))*w
fit = least_squares(resid, x0=[0.82,0.60,0.15], bounds=([0.5,0.3,0.05],[0.99,0.9,0.4]))
print('AJUST 3 nivells al sketch (Y, r>=1.1):', np.round(fit.x, 4), 'rms log', float(np.sqrt(np.mean(fit.fun**2))))
t_fit, coef_fit = corba(fit.x, u0)
# el mateix amb G
def residG(p):
    t, _ = corba(p, u0); m = rm >= 1.1
    w = np.sqrt(np.interp(rm[m], rs_G, cs))
    return (np.log(t[m]) - np.log(np.interp(rm[m], rs_G, Gs)))*w
fitG = least_squares(residG, x0=[0.82,0.60,0.15], bounds=([0.5,0.3,0.05],[0.99,0.9,0.4]))
print('AJUST 3 nivells al sketch (G, r>=1.1):', np.round(fitG.x, 4))
# ajust nomes 1.1-4.5 (dins del cercle inscrit del sketch)
def resid2(p):
    t, _ = corba(p, u0); m = (rm >= 1.1) & (rm <= 4.6)
    return (np.log(t[m]) - np.log(np.interp(rm[m], rs, Ys)))
fit2 = least_squares(resid2, x0=[0.82,0.60,0.15], bounds=([0.5,0.3,0.05],[0.99,0.9,0.4]))
print('AJUST nomes 1.1-4.6:', np.round(fit2.x, 4))
print(' r     sketch Y  model ajustat  model actual')
for r0 in (1.1,1.15,1.25,1.5,1.75,2.05,2.5,3.05,3.5,4.05,4.5,5.05,5.5,6.05,6.85,7.5,8.05):
    i = np.argmin(np.abs(rm-r0)); k = np.argmin(np.abs(rs-r0))
    print(f'{r0:5.2f}  {Ys[k]:.4f}   {t_fit[i]:.4f}      {t_now[i]:.4f}')
json.dump(dict(fit_Y=list(map(float,fit.x)), fit_G=list(map(float,fitG.x)), fit_1_1_4_6=list(map(float,fit2.x)),
               coef_now=list(map(float,coef_now)), coef_fit=list(map(float,coef_fit))), open('corba_fit.json','w'), indent=1)
