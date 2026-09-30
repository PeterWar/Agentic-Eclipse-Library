import numpy as np, pandas as pd
X='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/xmatch/'
s=pd.read_csv(X+'zp_sony.csv'); r=pd.read_csv(X+'zp_r6.csv')
ids=pd.read_csv(X+'IDENTIFICACIONS_sony.csv')[['TYC','R_Rsol']]
m=s.merge(r,on='TYC',suffixes=('_s','_r')).merge(ids,on='TYC')
m=m[np.isfinite(m.minst_s)&np.isfinite(m.minst_r)].copy()
m['D']=m.minst_s-m.minst_r
m=m.sort_values('R_Rsol')
print(f'{"TYC":14s} {"R/Rsol":>7s} {"V":>5s} {"D=m_s-m_r":>10s} {"snr_s":>6s} {"snr_r":>6s}')
for _,q in m.iterrows():
    print(f'{q.TYC:14s} {q.R_Rsol:7.2f} {q.V_s:5.2f} {q.D:10.3f} {q.snr_s:6.1f} {q.snr_r:6.1f}')
in_=m[m.R_Rsol<6]; out=m[m.R_Rsol>=6]
print(f'\nR<6 Rsol  (n={len(in_)}): |D| mediana={np.median(np.abs(in_.D)):.3f}  desv(D)={np.std(in_.D,ddof=1):.3f}')
print(f'R>=6 Rsol (n={len(out)}): |D| mediana={np.median(np.abs(out.D)):.3f}  desv(D)={np.std(out.D,ddof=1):.3f}')
hi=m[(m.snr_s>15)]
print(f'\nNomes snr_sony>15 (n={len(hi)}): desv(D)={np.std(hi.D,ddof=1):.3f}, |D| mediana={np.median(np.abs(hi.D)):.3f}')
hi2=m[(m.snr_s>15)&(m.R_Rsol>6)]
print(f'snr_sony>15 I R>6 (n={len(hi2)}): desv(D)={np.std(hi2.D,ddof=1):.3f} -> aquest es el terra real de la fotometria')
