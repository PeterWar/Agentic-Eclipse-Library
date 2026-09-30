"""esceptic_04: relació capa 30 ↔ RAW 10 s (normalitzats per anells, lp12, r<0,85): pendent global k (capa−1 = k·(RAW−1)) i residu a la marca 7; el mateix per sectors (245–275°) i per radis."""
import sys, json, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from esceptic_comu import *
from compo import carrega
from scipy.ndimage import gaussian_filter
rr,az=graella(); R7=marca7(); A=np.load(SP+'/esceptic_raw10s_compost.npy'); rgb30,_=carrega(30); L30=rgb30.mean(-1); al30=np.load(SP+'/roi_L30.npz')['c-1']/65535.
n30=norm_anells(L30,CX,CY,RS,0.95,mask=al30>0.5); nA=A
l30=gaussian_filter(np.nan_to_num(n30,nan=1.0),12)-1; lA=gaussian_filter(np.nan_to_num(nA,nan=1.0),12)-1
K=(rr<0.85)&np.isfinite(n30)&np.isfinite(nA)
k=float(np.sum(l30[K]*lA[K])/np.sum(lA[K]**2)); res=l30-k*lA
out=dict(k_global=round(k,3),pearson=round(pearson(l30,lA,K),4),marca7_capa30_pct=round(profunditat_taca(l30+1,R7,rr,az),3),marca7_RAW_x_k_pct=round(profunditat_taca(k*lA+1,R7,rr,az),3),marca7_residu_pct=round(profunditat_taca(res+1,R7,rr,az),3))
# pendent per anell (l'estirament pot dependre del nivell)
per_anell={}
for r0,r1 in ((0.15,0.35),(0.35,0.55),(0.55,0.75),(0.75,0.85)):
    kk=K&(rr>=r0)&(rr<r1); per_anell[f'{r0}-{r1}']=dict(k=round(float(np.sum(l30[kk]*lA[kk])/np.sum(lA[kk]**2)),3),pearson=round(pearson(l30,lA,kk),3))
out['per_anell']=per_anell
# relació capa30 vs RAW punt a punt: és lineal o log? compara k en zones clares i fosques
cl=K&(lA>0.01); fo=K&(lA<-0.01); out['k_zones_clares']=round(float(np.sum(l30[cl]*lA[cl])/np.sum(lA[cl]**2)),3); out['k_zones_fosques']=round(float(np.sum(l30[fo]*lA[fo])/np.sum(lA[fo]**2)),3)
print(out); json.dump(out,open(SP+'/esceptic_04.json','w'),indent=1,default=float)
