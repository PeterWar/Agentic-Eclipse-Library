"""A29: robustesa de la correcció del vel: (1) amplitud sense LROC (A del RAW × transferència RAW→capa per anell), (2) holdout per sectors (ajust en sectors parells, validació en senars), (3) retenció de bandes fines, (4) color."""
import sys, json, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
from scipy.ndimage import gaussian_filter
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
RS=456.0; rr2=np.hypot(*np.mgrid[0:2000,0:2000][::-1]-np.array([[[998.88]],[[998.41]]])); az=np.rad2deg(np.arctan2(-(np.mgrid[0:2000,0:2000][0]-998.41),np.mgrid[0:2000,0:2000][1]-998.88))%360
disc=rr2<RS-8
def ring_norm(A,mask,step=4):
    out=np.full(A.shape,np.nan)
    for k in range(0,int(RS)+step,step):
        m=mask&(rr2>=k)&(rr2<k+step)
        if m.sum()>10: out[m]=A[m]/np.mean(A[m])-1
    return out
Gaz=np.load(SP+'/vel_Gaz_base.npy').astype(np.float64); fit=json.load(open(SP+'/a28_vel2d_base.json'))['millor']; A=fit['A']
M=np.load(SP+'/raw_disc_norm_2000.npy').astype(np.float64); Mv=np.isfinite(M); Mz=gaussian_filter(np.nan_to_num(np.where(Mv,M-1,0)),6)
rgb30,a30=carrega(30); L30=rgb30.mean(-1); LAY=ring_norm(gaussian_filter(L30,6),disc)
rgb62,a62=carrega(62); L62=rgb62.mean(-1); v62=np.load(SP+'/roi_L62.npz')['c-1']>30000; LROC=ring_norm(gaussian_filter(L62,6),v62&disc)
bins=np.arange(20,RS-8,20); T=[]; c_lroc=[]; c_alt=[]
for k in bins:
    m=disc&Mv&(rr2>=k)&(rr2<k+20)&np.isfinite(LAY)&np.isfinite(LROC)
    # transferència RAW→capa: LAY ≈ T·Mz (regressió sense terme LROC, ortogonalitzant abans amb Gaz? no: directa)
    t=np.polyfit(Mz[m],LAY[m],1)[0]; T.append(t); c_alt.append(A*t)
    X=np.stack([Gaz[m],LROC[m],np.ones(m.sum())],1); coef,*_=np.linalg.lstsq(X,LAY[m],rcond=None); c_lroc.append(coef[0])
print('anell r:        ',' '.join(f'{int(k):4d}' for k in bins)); print('T (capa/RAW):   ',' '.join(f'{x:4.1f}' for x in T)); print('c via LROC:     ',' '.join(f'{x:4.2f}' for x in c_lroc)); print('c via RAW (A·T):',' '.join(f'{x:4.2f}' for x in c_alt))
print('quocient mitjà c_RAW/c_LROC (r 40–400): %.2f'%(np.mean(np.array(c_alt)[1:20])/np.mean(np.array(c_lroc)[1:20])))
# holdout per sectors: ajust de c(r) en sectors parells de 10°, validació (correlació amb LROC) en senars
sec=(az//10).astype(int); parell=(sec%2==0)
def corr_lroc(Lz,m): return np.corrcoef(Lz[m],LROC[m])[0,1]
res_ho=[]
for k in bins:
    m=disc&(rr2>=k)&(rr2<k+20)&np.isfinite(LAY)&np.isfinite(LROC)&np.isfinite(Gaz)
    mp=m&parell; ms=m&~parell
    X=np.stack([Gaz[mp],LROC[mp],np.ones(mp.sum())],1); coef,*_=np.linalg.lstsq(X,LAY[mp],rcond=None); c=max(coef[0],0)
    Ln=ring_norm(gaussian_filter(L30/(1+c*np.nan_to_num(Gaz)),6),disc)
    res_ho.append((int(k),round(corr_lroc(LAY,ms),2),round(corr_lroc(Ln,ms),2)))
print('holdout (sectors senars): correlació amb LROC abans → després per anell:',res_ho)
# retenció de bandes fines i color (capa corregida a28)
v71=np.load(SP+'/roi_L30_v71_base.npz'); rgbn=np.dstack([v71['c0'],v71['c1'],v71['c2']]).astype(np.float64)/65535; Ln=rgbn.mean(-1)
for lo,hi in ((3,8),(8,32),(32,64)):
    b0=gaussian_filter(L30,lo)-gaussian_filter(L30,hi); b1=gaussian_filter(Ln,lo)-gaussian_filter(Ln,hi); m=rr2<RS-30
    print(f'banda {lo}–{hi} px: correlació abans/després {np.corrcoef(b0[m],b1[m])[0,1]:.4f}; quocient d\'amplitud {b1[m].std()/b0[m].std():.3f}')
m=rr2<RS-30; print('color: R/G mediana abans %.4f després %.4f · B/G %.4f → %.4f'%(np.median(rgb30[...,0][m]/rgb30[...,1][m]),np.median(rgbn[...,0][m]/rgbn[...,1][m]),np.median(rgb30[...,2][m]/rgb30[...,1][m]),np.median(rgbn[...,2][m]/rgbn[...,1][m])))
print('mitjana per anell (r 100,200,300,400) abans/després:',[(int(k),round(float(L30[disc&(rr2>=k)&(rr2<k+20)].mean()),4),round(float(Ln[disc&(rr2>=k)&(rr2<k+20)].mean()),4)) for k in (100,200,300,400)])
json.dump(dict(T=[float(x) for x in T],c_lroc=[float(x) for x in c_lroc],c_alt=[float(x) for x in c_alt],holdout=res_ho),open(SP+'/a29_robustesa.json','w'),indent=1)
