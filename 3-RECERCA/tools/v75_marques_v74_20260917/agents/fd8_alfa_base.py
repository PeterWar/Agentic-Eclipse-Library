"""fd8: alfa efectiva de la base 3 (el forat) i alfa del compost final per radi i sector; comparació L74 (recomp) vs compost Photoshop al limbe."""
import numpy as np, json
import fd_lib as F
c74=F.compo74(); C74,a74=c74.recompon(exclou=(222,)); Lps=F.Lstar(F.compost_ps()); L74=F.Lstar(C74)
rgb3,al3=c74.carrega(3); rgb30,al30=c74.carrega(30)
d3=np.load(F.S4+'/roi74p_L3.npz'); a3own=d3['c-1'].astype(np.float32)/65535; m3=d3['c-2'].astype(np.float32)/65535
res={}; rb=np.arange(440,464)
for nomS,(a0,a1) in {'N_az80_100':(80,100),'N_az100_120':(100,120),'E_az0_20':(0,20),'W_az150_160':(150,160),'W_az180_190':(180,190),'S_az260_280':(260,280)}.items():
    s=F.sector(a0,a1); q={'r':rb.tolist()}
    q['alfa3_propia']=[round(float(a3own[s&F.anell(r,r+1)].mean()),3) for r in rb]; q['masc3']=[round(float(m3[s&F.anell(r,r+1)].mean()),3) for r in rb]
    q['alfa3_ef']=[round(float(al3[s&F.anell(r,r+1)].mean()),3) for r in rb]; q['alfa30_ef']=[round(float(al30[s&F.anell(r,r+1)].mean()),3) for r in rb]
    q['alfa_compost']=[round(float(a74[s&F.anell(r,r+1)].mean()),3) for r in rb]; q['alfa_compost_min']=[round(float(a74[s&F.anell(r,r+1)].min()),3) for r in rb]
    q['L74']=[round(float(np.median(L74[s&F.anell(r,r+1)])),1) for r in rb]; q['Lps']=[round(float(np.median(Lps[s&F.anell(r,r+1)])),1) for r in rb]
    res[nomS]=q; print('--',nomS); [print('%-16s'%k,' '.join('%6s'%v for v in q[k])) for k in q]
# píxels del compost amb alfa < 0,99 dins r<470: quants i on
low=(a74<0.99)&(F.RR<470); res['compost_alfa_lt_099']=dict(n=int(low.sum()),r_min_max=[float(F.RR[low].min()),float(F.RR[low].max())] if low.any() else None,az_hist={int(a):int((low&F.sector(a,a+30)).sum()) for a in range(0,360,30)},alfa_min=float(a74[F.RR<470].min()))
print('compost alfa<0,99 dins r<470:',res['compost_alfa_lt_099'])
F.dump('fd8_alfa_base',res); print('fd8 fet')
