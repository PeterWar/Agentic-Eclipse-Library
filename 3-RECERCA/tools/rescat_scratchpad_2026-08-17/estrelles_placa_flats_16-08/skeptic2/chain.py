import numpy as np, pandas as pd, json
XD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/xmatch/'
zp=json.load(open(XD+'zp2.json')); sol=json.load(open(XD+'final_solution.json'))
BV_SOL=0.653
print('=== A) EL TERME DE COLOR NO S\'APLICA AL SOL ===')
print('   Model:  V - m_inst = ZP - k(X-Xsun) - c(B-V)   =>  m_inst(Sol) = -26,75 - ZP + c*0,653')
print('   El codi (corona2.py) fa:  F_sol = 10^(0,4*(ZP+26,75))   -- SENSE el terme c*0,653\n')
print(f'{"tren":6s} {"c ajustat":>10s} {"F_sol usat":>12s} {"F_sol correcte":>15s} {"error en B/Bsol":>16s}')
fac={}
for t in ('sony','r6'):
    ZP=zp[t]['ZPsun']; c=zp[t]['c']
    Fu=10**(0.4*(ZP+26.75)); Fc=10**(0.4*(ZP+26.75-c*BV_SOL))
    fac[t]=Fu/Fc
    print(f'{t:6s} {c:+10.3f} {Fu:12.4e} {Fc:15.4e} {100*(Fu/Fc-1):+15.1f} %')
print(f'\n   Efecte sobre el QUOCIENT R6/Sony publicat (0,83):')
q=0.83*(fac["r6"]/fac["sony"])
print(f'   corregit = 0,83 x ({fac["r6"]:.4f}/{fac["sony"]:.4f}) = {q:.3f}')
print(f'   -> {abs(-2.5*np.log10(q)):.3f} mag en lloc de 0,20 mag. Part de la discrepancia entre trens')
print(f'      es un terme de color no propagat, no llum difosa.')

print('\n=== B) CURVATURA DE BOUGUER: es lineal l\'ajust en X entre 4,6 i 7,1 ? ===')
d=pd.read_csv(XD+'zp_sony.csv'); ids=pd.read_csv(XD+'IDENTIFICACIONS_sony.csv')[['det','R_Rsol']]
d=d.merge(ids,on='det'); d=d[np.isfinite(d.minst)&(d.R_Rsol>2.6)].reset_index(drop=True)
BANDS=[(1.6,2.6),(2.6,4),(4,6),(6,9),(9,14)]
NO=np.load('/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/skeptic2/noise.npy')
def noi(R):
    for (lo,hi),v in zip(BANDS,NO):
        if lo<=R<hi: return v
    return NO[-1]
sg=np.array([1.0857*noi(R)/f for R,f in zip(d.R_Rsol,d.flux_tot)])
w=1/(sg**2+0.10**2+0.10**2)
y=(d.V-d.minst).values; BV=np.where(np.isfinite(d.BV),d.BV,0.); Xs=6.077645211221788
dX=d.X.values-Xs
def f(A):
    W=np.sqrt(w)[:,None]
    s,*_=np.linalg.lstsq(A*W,y*np.sqrt(w),rcond=None)
    r=y-A@s; cov=np.linalg.pinv((A*w[:,None]).T@A)
    return s,np.sqrt(np.diag(cov)),np.sqrt(np.average(r**2,weights=w))
for lab,A in (('lineal en X',np.column_stack([np.ones(len(y)),-dX,-BV])),
              ('+ quadratic X^2',np.column_stack([np.ones(len(y)),-dX,dX**2,-BV]))):
    s,e,rms=f(A)
    print(f'   {lab:18s} ZP={s[0]:+.3f}+-{e[0]:.3f}  k={s[1]:+.3f}+-{e[1]:.3f}  '
          +(f'q={s[2]:+.4f}+-{e[2]:.4f}  ' if len(s)==4 else '')+f'rms={rms:.3f}')
print('   -> el ZP es defineix a X=Xsol, DINS del rang mostrejat (4,62-7,13): es interpolacio,')
print('      i per aixo la curvatura de Bouguer amb prou feines el mou.')

print('\n=== C) k Sony vs k R6: poden ser tots dos extincio ATMOSFERICA? ===')
print(f'   Sony k={zp["sony"]["k"]:.3f}+-{zp["sony"]["ek"]:.3f}   R6 k={zp["r6"]["k"]:.3f}+-{zp["r6"]["ek"]:.3f}')
dk=zp["sony"]["k"]-zp["r6"]["k"]; edk=np.hypot(zp["sony"]["ek"],zp["r6"]["ek"])
print(f'   diferencia = {dk:+.3f} +- {edk:.3f}  ->  {abs(dk/edk):.1f} sigma')
print('   Els dos trens miraven la MATEIXA atmosfera al MATEIX instant. Si k fos extincio,')
print('   haurien de coincidir. No coincideixen: almenys un dels dos absorbeix vinyetatge.')
print(f'   R6 nomes cobreix X=5,34-7,20 (palanca 1,86) contra 4,62-7,13 de la Sony (2,51).')
