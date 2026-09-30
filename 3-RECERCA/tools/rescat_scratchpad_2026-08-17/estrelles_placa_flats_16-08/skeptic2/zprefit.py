import numpy as np, pandas as pd, json
XD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/xmatch/'
BANDS=[(1.6,2.6),(2.6,4),(4,6),(6,9),(9,14)]
NO=np.load('/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/skeptic2/noise.npy')
d=pd.read_csv(XD+'zp_sony.csv'); ids=pd.read_csv(XD+'IDENTIFICACIONS_sony.csv')[['det','R_Rsol']]
d=d.merge(ids,on='det'); d=d[np.isfinite(d.minst)].reset_index(drop=True)
def noi(R):
    for (lo,hi),v in zip(BANDS,NO):
        if lo<=R<hi: return v
    return NO[-1]
d['sig_true']=[1.0857*noi(R)/f for R,f in zip(d.R_Rsol,d.flux_tot)]
d['sig_quot']=1.0857/d.snr
print(f'{"det":5s} {"V":>5s} {"R/Rsol":>7s} {"snr_citat":>10s} {"sig_citat":>10s} {"SOROLL_REAL":>12s} {"snr_real":>9s} {"sig_real":>9s}')
for _,q in d.sort_values('R_Rsol').iterrows():
    print(f'{q.det:5s} {q.V:5.2f} {q.R_Rsol:7.2f} {q.snr:10.1f} {q.sig_quot:10.3f} {noi(q.R_Rsol):12.1f} {q.flux_tot/noi(q.R_Rsol):9.1f} {q.sig_true:9.3f}')
y=(d.V-d.minst).values; BV=np.where(np.isfinite(d.BV),d.BV,0.); Xs=6.077645211221788
dX=d.X.values-Xs; sg=d.sig_true.values
CAT=0.10   # error tipic de la V de cataleg (Hipparcos ~0,01 ; VT/BT derivada ~0,1)
w=1/(sg**2+CAT**2)
def fit(A,w,clip=None,y=y):
    ok=np.ones(len(y),bool)
    for _ in range(8):
        W=np.sqrt(w[ok])[:,None]
        s,*_=np.linalg.lstsq(A[ok]*W,y[ok]*np.sqrt(w[ok]),rcond=None)
        r=y-A@s
        if clip is None: break
        sd=1.4826*np.median(np.abs(r[ok]-np.median(r[ok])))
        new=np.abs(r-np.median(r[ok]))<clip*max(sd,0.02)
        if (new==ok).all(): break
        ok=new
    W=np.sqrt(w[ok])[:,None]
    s,*_=np.linalg.lstsq(A[ok]*W,y[ok]*np.sqrt(w[ok]),rcond=None)
    r=(y[ok]-A[ok]@s)
    chi2=(w[ok]*r**2).sum()/max(ok.sum()-A.shape[1],1)
    cov=np.linalg.pinv((A[ok]*w[ok][:,None]).T@A[ok])
    e=np.sqrt(np.diag(cov))
    return s,e,ok,float(np.sqrt(np.average(r**2,weights=w[ok]))),chi2
A=np.column_stack([np.ones(len(y)),-dX,-BV])
print('\n=== REAJUST del punt zero amb ERRORS REALS (minims quadrats PONDERATS) ===')
for lab,sub in (('totes',np.ones(len(y),bool)),
                ('nomes R>2,6 Rsol',d.R_Rsol.values>2.6),
                ('nomes R>4 Rsol',d.R_Rsol.values>4.0),
                ('R>2,6 i snr_real>5',(d.R_Rsol.values>2.6)&((d.flux_tot/np.array([noi(R) for R in d.R_Rsol]))>5))):
    s,e,ok,rms,chi2=fit(A[sub],w[sub],clip=None,y=y[sub])
    print(f'  {lab:22s} n={sub.sum():2d}  ZP={s[0]:+.3f}+-{e[0]:.3f}  k={s[1]:+.3f}+-{e[1]:.3f}  '
          f'c={s[2]:+.3f}+-{e[2]:.3f}  chi2red={chi2:5.2f}  rms={rms:.3f}')
print(f'\n  PUBLICAT (sense pesos, retall 2,5 sigma, 30 de 38): ZP=+14.167+-0.065  k=+0.416+-0.050  c=-0.076')
print(f'\n  chi2red >> 1 vol dir que la dispersio NO l\'expliquen ni el soroll real ni 0,10 mag de cataleg.')
# quant caldria d'error extra per fer chi2=1
s,e,ok,rms,chi2=fit(A,w,clip=None)
for extra in (0.0,0.1,0.2,0.3,0.4):
    w2=1/(sg**2+CAT**2+extra**2)
    s2,e2,ok2,rms2,c2=fit(A,w2,clip=None)
    print(f'   error extra {extra:.2f} mag -> chi2red={c2:5.2f}  ZP={s2[0]:+.3f}+-{e2[0]:.3f}  k={s2[1]:+.3f}+-{e2[1]:.3f}')
