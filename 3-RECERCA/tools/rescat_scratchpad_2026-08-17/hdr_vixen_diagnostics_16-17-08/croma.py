import numpy as np, json, math
per = json.load(open('perfils.json')); lin = json.load(open('lineal.json'))
def prof(name, key):
    return np.array([d['rmid'] for d in per[name] if key in d]), np.array([d[key] for d in per[name] if key in d])
rs, RGs = prof('sketch','RG'); _, BGs = prof('sketch','BG')
rf, RGf = prof('foto','RG'); _, BGf = prof('foto','BG')
rp, RGp = prof('sketch_p3','RG'); _, BGp = prof('sketch_p3','BG')
rm = np.array([d['r0']+0.05 for d in lin['files']]); Lm = np.array([d['L'] for d in lin['files']])
L_cel, L_cor = lin['L_cel'], lin['L_cor']
u_tool = np.clip(np.log10(np.maximum(Lm, L_cel)/L_cel)/math.log10(max(L_cor/L_cel,1.2)), 0, 1)
def med(r, v, a, b): m = (r >= a) & (r < b); return float(np.median(v[m]))
# ancoratges mesurats a cada imatge
for nom, r, RG, BG in (('sketch sRGB', rs, RGs, BGs), ('sketch P3', rp, RGp, BGp), ('foto', rf, RGf, BGf)):
    cor = (med(r,RG,1.5,2.2), med(r,BG,1.5,2.2)); cel = (med(r,RG,6.2,7.0), med(r,BG,6.2,7.0))
    print(f'{nom:12s} corona 1.5-2.2: R/G={cor[0]:.3f} B/G={cor[1]:.3f} | cel 6.2-7.0: R/G={cel[0]:.3f} B/G={cel[1]:.3f} | 1.2-1.5: {med(r,RG,1.2,1.5):.3f}/{med(r,BG,1.2,1.5):.3f} | 2.5-3: {med(r,RG,2.5,3.0):.3f}/{med(r,BG,2.5,3.0):.3f} | 3.8-4.6: {med(r,RG,3.8,4.6):.3f}/{med(r,BG,3.8,4.6):.3f} | 5-6: {med(r,RG,5.0,6.0):.3f}/{med(r,BG,5.0,6.0):.3f}')
# u implícit per R/G i B/G (sRGB) del sketch i de la foto, contra el u del tool
cor_s = (med(rs,RGs,1.5,2.2), med(rs,BGs,1.5,2.2)); cel_s = (med(rs,RGs,6.2,7.0), med(rs,BGs,6.2,7.0))
cor_f = (med(rf,RGf,1.5,2.2), med(rf,BGf,1.5,2.2)); cel_f = (med(rf,RGf,6.2,7.0), med(rf,BGf,6.2,7.0))
print('\n r    u_tool(L)  sketch u_RG u_BG   foto u_RG u_BG   | sketch R/G B/G  foto R/G B/G')
for r0 in (1.15,1.35,1.55,1.75,2.05,2.25,2.55,2.85,3.05,3.35,3.55,3.85,4.05,4.35,4.55,5.05,5.55,6.05,6.55,7.05,7.55,8.05):
    i = np.argmin(np.abs(rm-r0)); k = np.argmin(np.abs(rs-r0)); j = np.argmin(np.abs(rf-r0))
    us = ((RGs[k]-cel_s[0])/(cor_s[0]-cel_s[0]), (BGs[k]-cel_s[1])/(cor_s[1]-cel_s[1]))
    uf = ((RGf[j]-cel_f[0])/(cor_f[0]-cel_f[0]), (BGf[j]-cel_f[1])/(cor_f[1]-cel_f[1]))
    print(f'{r0:5.2f}  {u_tool[i]:.3f}      {us[0]:.3f} {us[1]:.3f}     {uf[0]:.3f} {uf[1]:.3f}   | {RGs[k]:.3f} {BGs[k]:.3f}   {RGf[j]:.3f} {BGf[j]:.3f}')
# radi on el sketch i la foto creuen R/G=1 i B/G=1
def creu(r, v):
    for a, b, va, vb in zip(r[:-1], r[1:], v[:-1], v[1:]):
        if (va-1)*(vb-1) <= 0 and va != vb: return float(a + (1-va)/(vb-va)*(b-a))
    return None
print('creuament R/G=1: sketch', creu(rs,RGs), 'foto', creu(rf,RGf), '; B/G=1: sketch', creu(rs,BGs), 'foto', creu(rf,BGf))
# ajust d'una potència: u_sketch ≈ u_tool**p
m = (rm >= 1.5) & (rm <= 6.0)
us_i = np.interp(rm[m], rs, (RGs-cel_s[0])/(cor_s[0]-cel_s[0])); ub_i = np.interp(rm[m], rs, (BGs-cel_s[1])/(cor_s[1]-cel_s[1]))
ut = u_tool[m]; ok = (ut > 0.02) & (ut < 0.98) & (us_i > 0.02) & (ub_i > 0.02)
p_rg = float(np.median(np.log(us_i[ok])/np.log(ut[ok]))); p_bg = float(np.median(np.log(ub_i[ok])/np.log(ut[ok])))
print('exponent p (u_sketch ~ u_tool^p): R/G', round(p_rg,2), 'B/G', round(p_bg,2))
