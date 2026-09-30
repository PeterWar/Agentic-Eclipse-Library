"""Pas 4. Demostració controlada (corona SINTÈTICA, veritat coneguda): la màscara en arc (Espenak) és cega a l'estructura tangencial;
la màscara isòtropa adaptativa (precursor de l'ACHF) la conserva. Mateixa entrada, mateix procediment de resta."""
import numpy as np, cv2, json
from comu import IMG, REBUTS, png
from scipy.ndimage import gaussian_filter
rng=np.random.default_rng(20260812)
N=1400; c=N/2-0.5; RS=110.0                                    # 1 R☉ = 110 px
yy,xx=np.mgrid[0:N,0:N].astype(np.float32); X=xx-c; Y=yy-c
R=np.hypot(X,Y)/RS; TH=np.arctan2(-Y,X)
r=np.maximum(R,1.0)
P=2.565*r**-17+1.425*r**-7+0.0532*r**-2.5                     # perfil de Baumbach (unitats 1e-6 B☉)
def dang(a,b): return np.angle(np.exp(1j*(a-b)))
S=np.zeros_like(R)
# raigs radials (serrells i plomalls): estrets en angle
for th0,amp,wd in [(35,0.30,3.0),(62,0.18,1.5),(118,0.25,2.5),(150,0.15,1.2),(205,0.30,3.5),(243,0.16,1.4),(300,0.28,2.8),(332,0.15,1.3),(85,0.12,1.0),(270,0.12,1.0)]:
    S+=amp*np.exp(-dang(TH,np.deg2rad(th0))**2/(2*np.deg2rad(wd)**2))*np.clip((R-1.0)/0.15,0,1)
# llaços tancats amb els peus al limbe: anells prims centrats sobre el limbe
for th0,rho,amp in [(178,0.42,0.30),(178,0.30,0.25),(178,0.19,0.22),(15,0.35,0.28),(15,0.22,0.22),(255,0.30,0.25)]:
    lx,ly=np.cos(np.deg2rad(th0))*RS,-np.sin(np.deg2rad(th0))*RS
    d=np.hypot(X-lx,Y-ly)/RS
    S+=amp*np.exp(-(d-rho)**2/(2*0.018**2))
# un arc concèntric (front tangencial pur), 70° d'amplada a 2,3 R☉
arc=0.22*np.exp(-(R-2.3)**2/(2*0.035**2))*np.exp(-dang(TH,np.deg2rad(90))**4/(2*np.deg2rad(28)**4))
S+=arc
B=P*(1+S)+0.0006                                                # + cel
lluna=R<1.0
B[lluna]=0.0006*0.3
B=B+rng.normal(0,1,B.shape)*np.sqrt(np.maximum(B,1e-6))*0.0012   # gra (proporcional a l'arrel del senyal)
# entrada comuna als dos filtres: imatge aplanada pel perfil radial mitjà (com fa un NRGF)
rb=np.clip((R*RS).astype(int),0,None); val=~lluna
o=np.argsort(rb[val],kind='stable'); rbs=rb[val][o]; Bs=B[val][o]; lim_=np.searchsorted(rbs,np.arange(rbs.max()+2))
prof=np.array([np.median(Bs[lim_[i]:lim_[i+1]]) if lim_[i+1]>lim_[i] else 1.0 for i in range(len(lim_)-1)])   # mediana per anell (robusta a l'arc)
F=np.where(val,B/np.maximum(prof[rb],1e-9),1.0).astype(np.float32)
def spin(img,deg):
    Nt=7200; Nr=int(np.ceil(np.hypot(c,c)))+2
    pol=cv2.warpPolar(img,(Nr,Nt),(c,c),Nr,cv2.WARP_POLAR_LINEAR|cv2.INTER_LINEAR)
    k=int(round(Nt*deg/360.0)); k+=1-(k%2)
    ext=np.concatenate([pol[-k:],pol,pol[:k]],0).astype(np.float64)
    cs=np.cumsum(np.concatenate([np.zeros((1,ext.shape[1])),ext],0),0); box=((cs[k:]-cs[:-k])/k)[k-(k//2):k-(k//2)+Nt].astype(np.float32)
    return cv2.warpPolar(box,(N,N),(c,c),Nr,cv2.WARP_POLAR_LINEAR|cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)
g_esp=(F-spin(F,10.0))*val
w=val.astype(np.float32); sig=9.0
g_iso=(F-gaussian_filter(F*w,sig,truncate=2.5)/np.maximum(gaussian_filter(w,sig,truncate=2.5),1e-3))*val
# veritat filtrada amb el mateix passa-alt isòtrop (referència del que hi ha de debò)
# mesura: contrast recuperat a l'arc concèntric (centre de l'arc) i al cim del llaç gran
def amp_at(img,mask): return float(img[mask].mean())
m_arc=(np.abs(R-2.3)<0.02)&(np.abs(dang(TH,np.deg2rad(90)))<np.deg2rad(12))
lx,ly=np.cos(np.deg2rad(178))*RS,-np.sin(np.deg2rad(178))*RS; d=np.hypot(X-lx,Y-ly)/RS
m_cim=(np.abs(d-0.42)<0.012)&(np.abs(dang(TH,np.deg2rad(178)))<np.deg2rad(4))&(R>1.3)
m_raig=(np.abs(dang(TH,np.deg2rad(35)))<np.deg2rad(0.8))&(R>1.8)&(R<2.6)
res={}
for nom,m,veritat in (('arc_concentric',m_arc,0.22),('cim_del_llac',m_cim,0.30),('raig_radial',m_raig,0.30)):
    res[nom]=dict(posat=veritat,tangencial=amp_at(g_esp,m),isotrop=amp_at(g_iso,m))
print(json.dumps(res,indent=1))
json.dump(res,open(REBUTS/'sintetic_tangencial.json','w'),indent=1)
# sortides (retall central de 1000 px per no ensenyar les vores del gir; tot el camp sintètic hi cap fins a 4,5 R☉)
def desa(nom,im): png(nom,im[200:1200,200:1200])      # s'ensenya ±4,5 R☉: les vores del gir queden fora
disp=np.log10(np.maximum(B,1e-5)); disp=(disp-np.log10(0.0006*0.9))/(np.log10(P.max())-np.log10(0.0006*0.9)); disp[lluna]=0
lim=0.16
desa('sint_corona',disp); desa('sint_veritat',0.5+0.5*(S*val)/0.32)
desa('sint_tangencial',0.5+0.5*g_esp/lim); desa('sint_isotrop',0.5+0.5*g_iso/lim)
