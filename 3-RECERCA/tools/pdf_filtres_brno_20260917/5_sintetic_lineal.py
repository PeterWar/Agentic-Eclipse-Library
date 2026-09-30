"""Pas 5. Demostració (corona SINTÈTICA): compondre exposicions en lineal contra compondre-les després d'una corba de to.
Cinc exposicions separades 4x d'un mateix sensor lineal.
Camí A (Brno): valors lineals dividits pel temps, mitjana ponderada, fora saturats i negats.
Camí B (clàssic): cada exposició «revelada» (gamma 2,2 + corba de contrast mitjà), igualada a la veïna amb UN sol factor
(com un ajust de nivells a mà) i apilada amb màscares de lluminositat 0,70→0,90.
Després, EL MATEIX filtre de visualització als dos composts."""
import numpy as np, json
from comu import IMG, REBUTS, TREBALL, png
from scipy.ndimage import gaussian_filter
from scipy.interpolate import PchipInterpolator
from numpy.polynomial import Chebyshev
N=1200; c=N/2-0.5; RS=100.0
yy,xx=np.mgrid[0:N,0:N].astype(np.float32); X=xx-c; Y=yy-c
R=np.hypot(X,Y)/RS; TH=np.arctan2(-Y,X); r=np.maximum(R,1.0)
P=2.565*r**-17+1.425*r**-7+0.0532*r**-2.5                       # perfil de Baumbach
lluna=R<1.0; val=~lluna
def dang(a,b): return np.angle(np.exp(1j*(a-b)))
RAIGS=[(35,0.30,3.0),(62,0.18,1.5),(118,0.25,2.5),(150,0.15,1.2),(205,0.30,3.5),(243,0.16,1.4),(300,0.28,2.8),(332,0.15,1.3),(85,0.12,1.0),(270,0.12,1.0)]
S=np.zeros_like(R)
for th0,amp,wd in RAIGS: S+=amp*np.exp(-dang(TH,np.deg2rad(th0))**2/(2*np.deg2rad(wd)**2))*np.clip((R-1.0)/0.15,0,1)
temps=np.array([1,4,16,64,256],float)
_c=PchipInterpolator([0,0.25,0.5,0.75,1.0],[0,0.20,0.5,0.80,1.0])
def revela(v): return _c(np.clip(v,0,1)**(1/2.2))
def dos_camins(S,llavor):
    rng=np.random.default_rng(llavor)
    B=P*(1+S)+0.0006; B[lluna]=0.0002; t0=0.8/B.max()
    raws=[np.clip(B*t0*t+rng.normal(0,1,B.shape)*np.sqrt(np.maximum(B*t0*t,0)/60000.0+1e-10),0,1) for t in temps]
    num=np.zeros_like(B); den=np.zeros_like(B)
    for v,t in zip(raws,temps):
        w=(np.clip((0.85-v)/0.10,0,1)*np.clip(v/0.02,0,1)+1e-6)*t
        num+=w*v/(t0*t); den+=w
    A=num/den
    devs=[revela(v) for v in raws]; g=[1.0]*len(devs)
    for k in range(len(devs)-2,-1,-1):
        llarga,curta=devs[k+1],devs[k]; zona=(llarga>0.50)&(llarga<0.80)&val
        g[k]=g[k+1]*float(np.median(llarga[zona]/np.maximum(curta[zona],1e-6)))
    comp=g[0]*devs[0]
    for k in range(1,len(devs)):
        m=np.clip((devs[k]-0.70)/0.20,0,1); m=m*m*(3-2*m); comp=(1-m)*g[k]*devs[k]+m*comp
    return B,A,comp,[g[k]/g[k+1] for k in range(len(g)-1)]
def visualitza(img):
    rb=np.clip((R*RS).astype(int),0,None)
    o=np.argsort(rb[val],kind='stable'); rbs=rb[val][o]; Is=img[val][o]; lim_=np.searchsorted(rbs,np.arange(rbs.max()+2))
    prof=np.array([np.median(Is[lim_[i]:lim_[i+1]]) if lim_[i+1]>lim_[i] else 1.0 for i in range(len(lim_)-1)])
    rad=np.arange(len(prof))/RS; ok=(rad>1.02)&(rad<8.3)
    ch=Chebyshev.fit(np.log(rad[ok]),np.log(np.maximum(prof[ok],1e-12)),16)     # perfil SUAU: no pot seguir una costura
    F=np.where(val,img/np.exp(ch(np.log(np.clip(R,1.02,8.3)))),1.0)
    w=val.astype(np.float32)
    return (F-gaussian_filter(F*w,14)/np.maximum(gaussian_filter(w,14),1e-3))*val      # convolució incompleta: la Lluna no hi compta
def desa(nom,im): png(nom,im[80:1120,80:1120])        # s'ensenya ±5,2 R☉
# 1) amb raigs: imatges
B,A,Bc,gp=dos_camins(S,12082026); gA=visualitza(A); gB=visualitza(Bc); lim=0.12
gA[R<1.03]=0; gB[R<1.03]=0                      # la vora mateixa del disc no s'ensenya (resposta del filtre a la vora, igual als dos)
desa('lin_A_filtrat',0.5+0.5*gA/lim); desa('lin_B_filtrat',0.5+0.5*gB/lim)
# 2) sense cap estructura: tot el que surti és fals
B0,A0,Bc0,gp0=dos_camins(np.zeros_like(S),7); g0A=visualitza(A0); g0B=visualitza(Bc0)
rr=np.arange(1.06,5.5,0.01); pA=[]; pB=[]
for r0 in rr:
    m=(np.abs(R-r0)<0.006); pA.append(np.median(g0A[m])); pB.append(np.median(g0B[m]))
pA=np.array(pA)*100; pB=np.array(pB)*100
np.savez(TREBALL/'lineal_anells.npz',r=rr,pA=pA,pB=pB)
# 3) quocient entre dues exposicions consecutives segons la brillantor (analític, sense soroll)
x=np.logspace(-3,np.log10(0.25),400); q_dev=revela(4*x)/np.maximum(revela(x),1e-9)
np.savez(TREBALL/'lineal_quocient.npz',x=x,q_lin=np.full_like(x,4.0),q_dev=q_dev)
res=dict(anells_lineal_max_pct=float(np.abs(pA[rr>1.1]).max()),anells_revelat_max_pct=float(np.abs(pB[rr>1.1]).max()),
         anells_revelat_pic_a_pic_pct=float(pB[rr>1.1].max()-pB[rr>1.1].min()),
         quocient_revelat_min=float(q_dev.min()),quocient_revelat_max=float(q_dev.max()),factor_unic_mesurat=gp,
         error_fotometric_lineal_max_pct=float(np.max(np.abs(np.array([np.median(A[np.abs(R-r0)<0.012]/B[np.abs(R-r0)<0.012]) for r0 in np.arange(1.05,5.6,0.05)])-1))*100))
print(json.dumps(res,indent=1)); json.dump(res,open(REBUTS/'sintetic_lineal.json','w'),indent=1)
