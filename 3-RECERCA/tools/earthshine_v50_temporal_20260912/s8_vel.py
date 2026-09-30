"""S8: vel de llum dispersada dins del disc lunar (ala de la PSF de la corona), mesurat a la capa lunar de Pere i restat.
Model: per sector de 5° (72), perfil radial mediana de G (2 px); nivell del disc = mediana a d∈[−260,−200]; excés = perfil − nivell,
suavitzat en d (σ 3 px) i en θ (σ 2 sectors), monòton creixent cap al limbe; taper 1 a d ≥ −200 → 0 a d = −260.
La capa és monocroma (R=G=B a 0,1 %): es resta el mateix camp als tres canals. Cap textura tocada: només un camp suau."""
import json, numpy as np
from pathlib import Path
from scipy.ndimage import gaussian_filter1d, map_coordinates
from PIL import Image
ROOT=Path('/Users/USUARI/Downloads/Eclipse 2026'); HERE=Path(__file__).resolve().parent; CAU=HERE/'cau'; OUT=ROOT/'output/earthshine_v50_temporal_20260912'; VIS=OUT/'vistes'
N=1400; CX=699.568111973117; CY=699.6475341408573
f4=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy'); th=np.linspace(0,2*np.pi,1440,endpoint=False); f4s=gaussian_filter1d(f4,3.0,mode='wrap')
yy,xx=np.mgrid[0:N,0:N]; r=np.hypot(xx-CX,yy-CY); ang=np.arctan2(yy-CY,xx-CX)%(2*np.pi); F4=np.interp(ang,np.append(th,2*np.pi),np.append(f4s,f4s[0])); d=r-F4
L=np.stack([np.load(CAU/f'lun_ch{c}_roi.npy') for c in (0,1,2)],-1).astype(np.float64)
G=L[...,1]; NS=72; sec=(ang/(2*np.pi)*NS).astype(int)
dbins=np.arange(-300,4,2.0); dc=dbins[:-1]+1
P=np.full((NS,len(dc)),np.nan)
for s in range(NS):
    m=sec==s
    for i,(a,b) in enumerate(zip(dbins[:-1],dbins[1:])):
        mm=m&(d>=a)&(d<b)
        if mm.sum()>=12: P[s,i]=np.median(G[mm])
# omple NaN per interpolació radial
for s in range(NS):
    ok=np.isfinite(P[s]); P[s]=np.interp(dc,dc[ok],P[s][ok])
base=np.median(P[:,(dc>=-260)&(dc<=-200)],axis=1)                       # nivell del disc per sector
exc=np.maximum(P-base[:,None],0.0); exc=gaussian_filter1d(exc,1.5,axis=1)   # suau en d (3 px)
exc=gaussian_filter1d(exc,2.0,axis=0,mode='wrap')                        # suau en θ (10°)
W=np.maximum.accumulate(np.where(dc[None,:]>=-260,exc,0.0),axis=1)       # monòton cap al limbe
taper=np.clip((dc+260)/60.0,0,1); W=W*taper[None,:]
# camp 2D: interpolació bilineal en (sector, d)
si=(ang/(2*np.pi)*NS); di=np.interp(d,dc,np.arange(len(dc)))
Wpad=np.concatenate([W,W[:1]],0)                                        # tancament circular
Wf=map_coordinates(Wpad,[si,di],order=1,mode='nearest'); Wf[d<-300]=0
Lnew=np.clip(L-Wf[...,None],0,65535)
# refinament: el residu mediana per sector a d∈[−70,0] (1 px) ha de ser el nivell del disc; una iteració, suau en θ (σ 1 sector),
# amb taper CONTINU (1 a d ≥ −40, 0 a d ≤ −70): ⛔ un tall sec a −40 deixava un graó de ±3–7 % (marques de Pere a la V52)
d1=np.arange(-70,2,1.0); d1c=d1[:-1]+0.5; R=np.zeros((NS,len(d1c)))
for s in range(NS):
    m=sec==s
    for i,(a,b) in enumerate(zip(d1[:-1],d1[1:])):
        mm=m&(d>=a)&(d<b); R[s,i]=(np.median(Lnew[...,1][mm])-base[s]) if mm.sum()>=6 else 0.0
R=gaussian_filter1d(R,1.0,axis=0,mode='wrap'); R=gaussian_filter1d(R,1.0,axis=1)
tap=np.clip((d1c+70)/30.0,0,1); tap=tap*tap*(3-2*tap); R=R*tap[None,:]
Rpad=np.concatenate([R,R[:1]],0); di1=np.interp(d,d1c,np.arange(len(d1c))); Rf=map_coordinates(Rpad,[si,di1],order=1,mode='nearest'); Rf[(d<-70)|(d>1)]=0
Wf=np.maximum(Wf+Rf,0); Lnew=np.clip(L-Wf[...,None],0,65535)
np.save(CAU/'lun_rgb_vel_u16.npy',np.rint(Lnew).astype(np.uint16)); np.save(CAU/'vel_field.npy',Wf.astype(np.float32))
rows=[]
for s in range(0,NS,6):
    rows.append(dict(sector_5deg=s,nivell=float(base[s]),W_a=[float(np.interp(x,dc,W[s])) for x in (-200,-100,-60,-40,-20,-10,-4,-1)]))
np.set_printoptions(linewidth=250)
print('vel restat (DN16) per sector de 5° cada 30°, a d = -200,-100,-60,-40,-20,-10,-4,-1 :')
for x in rows: print(x['sector_5deg'],int(x['nivell']),[int(v) for v in x['W_a']])
sec12=(ang/(2*np.pi)*12).astype(int)
print('capa lunar G després, mediana per sector de 30°, d=-100..0 pas 10:')
for s in range(12):
    m=sec12==s; print(s,[int(np.median(Lnew[...,1][m&(d>=a)&(d<a+10)])) for a in range(-100,0,10)])
# graó residual a −40 (mediana azimutal del salt entre d∈[−44,−41] i [−39,−36]) i mètrica d'arcs
sec12=(ang/(2*np.pi)*12).astype(int); steps=[float(np.median(Lnew[...,1][(sec12==s_)&(d>=-39)&(d<-36)])-np.median(Lnew[...,1][(sec12==s_)&(d>=-44)&(d<-41)])) for s_ in range(12)]
print('graó a −40 per sector (DN16):',[int(x) for x in steps])
json.dump(dict(model='vel radial per sector: mediana 2 px, nivell d∈[−260,−200], excés suavitzat σd 3 px σθ 10°, monòton, taper −260→−200; refinament d∈[−70,0] amb taper continu −70→−40',sectors=rows,grao_a_menys40_per_sector=steps),open(OUT/'S8_vel.json','w'),ensure_ascii=False,indent=1)
Image.fromarray(np.rint(np.clip(Wf/Wf.max(),0,1)*255).astype(np.uint8)).save(VIS/'S8_vel_camp.png'); print('S8 fet; vel max',float(Wf.max()))
