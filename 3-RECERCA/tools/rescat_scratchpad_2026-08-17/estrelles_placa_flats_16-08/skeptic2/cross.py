import numpy as np, pandas as pd, json
X='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/xmatch/'
s=pd.read_csv(X+'zp_sony.csv'); r=pd.read_csv(X+'zp_r6.csv')
m=s.merge(r,on='TYC',suffixes=('_s','_r'))
m=m[np.isfinite(m.minst_s)&np.isfinite(m.minst_r)].copy()
m['D']=m.minst_s-m.minst_r
print(f'Estrelles comunes als dos trens amb fotometria: {len(m)}')
print(f'{"TYC":14s} {"V":>5s} {"BV":>6s} {"X":>5s} {"m_s":>8s} {"m_r":>8s} {"D":>7s} {"snr_s":>6s} {"snr_r":>6s}')
for _,q in m.sort_values('X_s').iterrows():
    print(f'{q.TYC:14s} {q.V_s:5.2f} {q.BV_s:6.3f} {q.X_s:5.2f} {q.minst_s:8.3f} {q.minst_r:8.3f} {q.D:7.3f} {q.snr_s:6.1f} {q.snr_r:6.1f}')
D=m.D.values; Xa=m.X_s.values; BV=m.BV_s.values
print(f'\nD: mediana={np.median(D):.3f}  desv={np.std(D,ddof=1):.3f}  interval={D.min():.3f}..{D.max():.3f}')
# L'ATMOSFERA ES CANCEL.LA en D. Qualsevol pendent amb X es INSTRUMENTAL.
for lab,A in (('D ~ const', np.ones((len(D),1))),
              ('D ~ const + a*X', np.column_stack([np.ones(len(D)),Xa])),
              ('D ~ const + a*X + b*BV', np.column_stack([np.ones(len(D)),Xa,BV]))):
    sol,res,*_=np.linalg.lstsq(A,D,rcond=None)
    pr=A@sol; rr=D-pr
    n,p=len(D),A.shape[1]
    s2=(rr**2).sum()/max(n-p,1); cov=s2*np.linalg.pinv(A.T@A); e=np.sqrt(np.diag(cov))
    print(f'  {lab:26s} rms={np.sqrt(s2):.3f}  '+'  '.join(f'{v:+.3f}+-{ee:.3f}' for v,ee in zip(sol,e)))
print(f'\nPREDICCIO del model de zp2: pendent de D amb X hauria de ser (k_sony - k_r6) = {0.4158-0.7234:+.3f} +- {np.hypot(0.0496,0.0370):.3f}')
print('   (si k fos extincio ATMOSFERICA de veritat, D no pot dependre de X: es cancel.la)')
