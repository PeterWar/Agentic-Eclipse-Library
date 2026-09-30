"""A29b: quina amplitud c(r)? per a c = k·c_LROC (k = 0,8…1,6): correlació residual capa~Gaz (ha de tendir a 0, no a negatiu) i capa~LROC, en holdout (sectors senars, c ajustat en parells)."""
import sys, json, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
from scipy.ndimage import gaussian_filter
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
RS=456.0; Y,X=np.mgrid[0:2000,0:2000]; rr2=np.hypot(X-998.88,Y-998.41); az=np.rad2deg(np.arctan2(-(Y-998.41),X-998.88))%360; disc=rr2<RS-8; sec=(az//10).astype(int); parell=sec%2==0
def ring_norm(A,mask,step=4):
    out=np.full(A.shape,np.nan)
    for k in range(0,int(RS)+step,step):
        m=mask&(rr2>=k)&(rr2<k+step)
        if m.sum()>10: out[m]=A[m]/np.mean(A[m])-1
    return out
Gaz=np.nan_to_num(np.load(SP+'/vel_Gaz_base.npy').astype(np.float64)); rgb30,_=carrega(30); L30=rgb30.mean(-1); LAY=ring_norm(gaussian_filter(L30,6),disc)
rgb62,_=carrega(62); L62=rgb62.mean(-1); v62=np.load(SP+'/roi_L62.npz')['c-1']>30000; LROC=ring_norm(gaussian_filter(L62,6),v62&disc)
bins=np.arange(20,RS-8,20); c_lroc=np.array(json.load(open(SP+'/a29_robustesa.json'))['c_lroc'])
for kf in (0.0,0.8,1.0,1.2,1.45,1.7):
    cG=[];cL=[]
    for i,k in enumerate(bins):
        m=disc&(rr2>=k)&(rr2<k+20)&np.isfinite(LAY)&np.isfinite(LROC)&~parell
        c=kf*max(c_lroc[i],0); Ln=ring_norm(gaussian_filter(L30/(1+c*Gaz),6),disc)
        cG.append(np.corrcoef(Ln[m],Gaz[m])[0,1]); cL.append(np.corrcoef(Ln[m],LROC[m])[0,1])
    cG=np.array(cG); cL=np.array(cL)
    print(f'k={kf:4.2f}: corr residual~Gaz (r 40–400) mitjana {cG[1:20].mean():+.3f} [{cG[1:20].min():+.2f},{cG[1:20].max():+.2f}] · corr~LROC mitjana {cL[1:20].mean():+.3f} · a r 260–400 (zona taca): Gaz {cG[12:20].mean():+.3f} LROC {cL[12:20].mean():+.3f}')
