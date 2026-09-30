"""esceptic_03c: comparació NOMÉS azimutal (mapes normalitzats per anells, lp12, r<0,88): obs vs (S1+S2+dipol), vs nul girat 180°/90°/270° + dipol, vs dipol sol. També albedo sol."""
import sys, json, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from esceptic_comu import *
from compo import carrega
from scipy.ndimage import gaussian_filter, map_coordinates, rotate
PHI=json.load(open(SP+'/esceptic_01.json'))['gir_RAW_compost']['phi']; S=1080; N=4096
def retall(Y,cx,cy):
    yy,xx=np.mgrid[-S:S,-S:S]; return map_coordinates(Y,[yy+cy,xx+cx],order=1,cval=np.nan)
obs=[]
for f in ('572A2982','572A2983','572A2984'):
    d=llegeix(f); cx,cy,R,_=troba_lluna(d['Y']); obs.append(retall(d['Y'],cx,cy))
OBS=np.nanmean(obs,0); R=223.3; yy,xx=np.mgrid[-S:S,-S:S]; rr=np.hypot(xx,yy)/R; az=(np.rad2deg(np.arctan2(-yy,xx))+PHI)%360
COR=np.load(SP+'/esceptic_corona_hdr_half.npy').astype(np.float64)
ky,kx=np.mgrid[-N//2:N//2,-N//2:N//2]; kr=np.hypot(kx,ky)
def conv(img,K):
    K=K/K.sum(); F=np.fft.rfft2(np.fft.ifftshift(K)); I=np.zeros((N,N)); I[:2*S,:2*S]=img; return np.fft.irfft2(np.fft.rfft2(I)*F,s=(N,N))[:2*S,:2*S]
K=(rr<0.88)&np.isfinite(OBS); lp=lambda m: gaussian_filter(np.nan_to_num(m,nan=0.0),12)
rgb62,_=carrega(62); L62=rgb62.mean(-1); p=np.deg2rad(PHI); s=R/RS; dxr=xx/s; dyr=yy/s; Xc=CX+(dxr*np.cos(p)+dyr*np.sin(p)); Yc=CY+(-dxr*np.sin(p)+dyr*np.cos(p))
LR=lp(map_coordinates(L62,[Yc,Xc],order=1,cval=0.0)); R7=map_coordinates(marca7().astype(np.float32),[Yc,Xc],order=1,cval=0)>0.5
O=lp(OBS); X=xx/R; Yv=yy/R; one=np.ones_like(O)
def nrm(m): return norm_anells(np.where(K,m,np.nan),S,S,R,0.88)
nO=nrm(O); aO=np.nan_to_num(nO-1,nan=0.0)
def fit(cols):
    A=np.stack([c[K] for c in cols],1); x,*_=np.linalg.lstsq(A,O[K],rcond=None); return sum(xi*c for xi,c in zip(x,cols)),x
out={}
for g in (0,90,180,270):
    s1=lp(conv(rotate(COR,g,reshape=False,order=1,cval=0.0) if g else COR,(1+(kr/3)**2)**-1.5)); s2=lp(conv(rotate(COR,g,reshape=False,order=1,cval=0.0) if g else COR,(1+(kr/160)**2)**-1.5))
    for nom,cols in ((f'S1+S2+c+dipol gir{g}',[s1,s2,one,X,Yv]),(f'S1+S2+c gir{g}',[s1,s2,one])):
        M,x=fit(cols); aM=np.nan_to_num(nrm(M)-1,nan=0.0)
        out[nom]=dict(pearson_azimutal=round(pearson(aO,aM,K),4),R2_azimutal=round(float(1-np.var((aO-aM)[K])/np.var(aO[K])),4),marca7_model_pct=round(profunditat_taca(nrm(M),R7,rr,az),3),dipol=[round(float(v),1) for v in x[3:]] if len(x)>3 else None)
        print(nom,out[nom],flush=True)
for nom,cols in (('c+dipol',[one,X,Yv]),('c+LROC',[one,LR]),('c+dipol+LROC',[one,X,Yv,LR])):
    M,x=fit(cols); aM=np.nan_to_num(nrm(M)-1,nan=0.0)
    out[nom]=dict(pearson_azimutal=round(pearson(aO,aM,K),4),R2_azimutal=round(float(1-np.var((aO-aM)[K])/np.var(aO[K])),4),marca7_model_pct=round(profunditat_taca(nrm(M),R7,rr,az),3)); print(nom,out[nom])
out['marca7_obs_pct']=round(profunditat_taca(nO,R7,rr,az),3)
json.dump(out,open(SP+'/esceptic_03c.json','w'),indent=1,default=float); print('fet')
