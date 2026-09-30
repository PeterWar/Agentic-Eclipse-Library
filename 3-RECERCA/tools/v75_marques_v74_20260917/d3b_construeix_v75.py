"""D3b (V75, disseny 2) · A partir de la V74 re-desada per Pere (retalls roi74p_L{id}.npz, compo74):
  · capa 30 (producte lunar): (a) contingut: resta per sector de l'excés radial del limbe (franja clara dels últims px del fotograma d'earthshine: L* 10 → 25 a r 452–456),
    de r ≥ 448 el contingut passa al NIVELL suau del sector (ajust lineal per sector de 2° a r 436–449, suavitzat 4°, pendent limitat), rampa 448→451: allà el fotograma d'earthshine només té llum del limbe, no albedo;
    (b) alfa pròpia c-1 = min(c-1, erf a R 456,0 σ 1): el producte lunar acaba a la silueta fotografiada; on la màscara de Pere surt de la silueta (az 165–207) ja no tapa la corona. Màscara c-2 intacta.
  · capa 3 (base): dins la silueta (erf 456,0 σ 1) el farcit passa a ser el mateix nivell continuat de la capa 30 (idèntic al seu contingut corregit): la posició de la màscara de Pere deixa de veure's; i la màscara de la base (meva des de V71) queda opaca fins a r 464 (erf σ 2) perquè retallar l'alfa de la 30 no pugui destapar cap forat.
Mètriques: ressalt a la vora de la màscara 30 (az 63–123), textura de la banda, anell 457–467 a az 165–207, dentat, canvis fora, transparència."""
import sys, os, json, numpy as np
from scipy.ndimage import gaussian_filter1d, map_coordinates, uniform_filter1d
from scipy.special import erf
from PIL import Image
S4='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'; sys.path.insert(0,S4); os.chdir(S4); import compo74 as c
CX,CY,RS=998.88,998.41,456.0; Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY); az=(np.degrees(np.arctan2(-(Y-CY),X-CX)))%360; ri=np.round(rr).astype(int)
w_in=lambda r0,s=1.0: 0.5*(1-erf((rr-r0)/(np.sqrt(2)*s)))
# ---------- capa 30 ----------
d30=np.load('roi74p_L30.npz'); G=np.dstack([d30['c0'],d30['c1'],d30['c2']]).astype(np.float64)/65535; a30=d30['c-1'].astype(np.float64)/65535
Lg=G.mean(-1); NS=180; sec=(az//2).astype(int)%NS; R0,R1=436,450
prof=np.full((NS,R1-R0),np.nan)
for s_ in range(NS):
    for r in range(R0,R1):
        k=(sec==s_)&(ri==r)
        if k.any(): prof[s_,r-R0]=np.median(Lg[k])
prof=np.where(np.isfinite(prof),prof,np.nanmedian(prof,0)[None,:])
rs=np.arange(R0,R1)+0.0; A=np.c_[np.ones_like(rs),rs-448.0]; coef=np.linalg.lstsq(A,prof.T,rcond=None)[0]   # per sector: nivell a r=448 i pendent
niv=gaussian_filter1d(coef[0],2.0,mode='wrap'); pend=np.clip(gaussian_filter1d(coef[1],2.0,mode='wrap'),-0.0015,0.0015)
NIV=np.interp(az,np.arange(NS)*2+1.0,niv,period=360); PEND=np.interp(az,np.arange(NS)*2+1.0,pend,period=360)
NIVELL=np.clip(NIV+PEND*np.clip(rr-448.0,0,12),0,1)      # nivell del sector continuat cap al limbe (pendent limitat a ±0,15 %/px)
ramp=np.clip((rr-448.0)/3.0,0,1)
Gn=G*(1-ramp[...,None])+NIVELL[...,None]*ramp[...,None]
a30n=np.minimum(a30,w_in(RS,1.0))
np.savez_compressed(S4+'/roi75_L30.npz',c0=np.uint16(np.round(Gn[...,0]*65535)),c1=np.uint16(np.round(Gn[...,1]*65535)),c2=np.uint16(np.round(Gn[...,2]*65535)),**{'c-1':np.uint16(np.round(a30n*65535)),'c-2':d30['c-2']})
print('capa 30: px del contingut canviats %d (r mín %.1f) · alfa canviada a %d px (r mín %.1f)'%((np.abs(Gn-G).max(-1)>0.5/65535).sum(),rr[np.abs(Gn-G).max(-1)>0.5/65535].min(),(np.abs(a30n-a30)>0.5/65535).sum(),rr[np.abs(a30n-a30)>0.5/65535].min()))
print('  perfil del contingut (×1000) després, mediana per sector de 30°, r 446..460:')
for a0 in (0,60,90,150,180,240,300):
    s=(az>=a0)&(az<a0+30); print('   az %3d: '%a0+' '.join('%4.0f'%(1000*np.median(Gn[...,0][s&(ri==r)])) for r in range(446,461)))
# ---------- capa 3 ----------
b3=np.load('roi74p_L3.npz'); B=np.dstack([b3['c0'],b3['c1'],b3['c2']]).astype(np.float64)/65535
w=w_in(RS,1.0)[...,None]; Bn=B*(1-w)+Gn*w
m3=b3['c-2'].astype(np.float64)/65535; m3n=np.maximum(m3,w_in(464.0,2.0)); print('base: màscara canviada a %d px (r màx %.1f); alfa pròpia c-1 mín %.3f'%((np.abs(m3n-m3)>0.5/65535).sum(),rr[np.abs(m3n-m3)>0.5/65535].max(),b3['c-1'].min()/65535))
np.savez_compressed(S4+'/roi75_L3.npz',c0=np.uint16(np.round(Bn[...,0]*65535)),c1=np.uint16(np.round(Bn[...,1]*65535)),c2=np.uint16(np.round(Bn[...,2]*65535)),**{'c-1':b3['c-1'],'c-2':np.uint16(np.round(m3n*65535))})
print('capa 3: px canviats %d · r màx %.1f'%((np.abs(Bn-B).max(-1)>0.5/65535).sum(),rr[np.abs(Bn-B).max(-1)>0.5/65535].max()))
# ---------- recomposició i mètriques ----------
def lab(C):
    lin=np.clip(C,0,1)**2.2; M=np.array([[0.5767,0.1856,0.1882],[0.2974,0.6273,0.0753],[0.0270,0.0707,0.9911]]); XYZ=lin@M.T; wn=np.array([0.9505,1.0,1.089]); f=lambda t: np.where(t>0.008856,np.cbrt(t),7.787*t+16/116); fx,fy,fz=f(XYZ[...,0]/wn[0]),f(XYZ[...,1]/wn[1]),f(XYZ[...,2]/wn[2]); return 116*fy-16,500*(fx-fy),200*(fy-fz)
C0=np.load('roi74p_C_sensemarques.npy'); c.OVERRIDE.update({3:S4+'/roi75_L3.npz',30:S4+'/roi75_L30.npz'}); C1,a1=c.recompon(exclou=(222,)); C1=C1.astype(np.float32); np.save('roi75_C.npy',C1); np.savez_compressed('roi75_compost.npz',C=np.uint16(np.round(np.clip(C1,0,1)*65535)),a=np.uint16(np.round(np.clip(a1,0,1)*65535)))
L0,_,_=lab(C0); L1,_,_=lab(C1); rep={}
# ressalt a la vora de la màscara 30 (desviació respecte a la recta ±2,5 px) per sector de 2° a az 63–123, r 449–453
m30=d30['c-2'].astype(np.float64)/65535
def ressalt(L):
    out=[]
    for a0 in range(63,123,2):
        s=(az>=a0)&(az<a0+2); pr=np.array([np.median(m30[s&(ri==r)]) for r in range(446,458)]); e=446+int(np.argmax(pr<0.5)) if (pr<0.5).any() else 452
        rs=np.arange(e-3,e+4); vals=np.array([np.median(L[s&(ri==r)]) for r in rs]); fit=np.polyval(np.polyfit(rs,vals,1),rs); out.append(float((vals-fit)[3]))
    return np.array(out)
r0,r1=ressalt(L0),ressalt(L1); rep['ressalt_vora_mascara_az63_123']={'V74':[float(np.abs(r0).max()),float(np.abs(r0).mean())],'V75':[float(np.abs(r1).max()),float(np.abs(r1).mean())]}
# textura azimutal de la banda 450–455 a az 63–123 (std del pas alt σ2 al llarg de l'anell) i del disc 442–447
def tex(L,ra,rb,a0,a1):
    v=[]
    for r in range(ra,rb):
        s=(ri==r)&(az>=a0)&(az<a1); o=np.argsort(az[s]); x=L[s][o]; v.append(float((x-gaussian_filter1d(x,3)).std()))
    return float(np.mean(v))
rep['textura_banda_450_455']={'V74':tex(L0,450,455,63,123),'V75':tex(L1,450,455,63,123),'disc_442_447':tex(L1,442,447,63,123)}
# anell 457–467 a az 165–207 (on la màscara surt): L* contra sectors veïns
def anell(L,a0,a1): return float(L[(rr>=457)&(rr<467)&(az>=a0)&(az<a1)].mean())
rep['anell_457_467']={'az165_207':{'V74':anell(L0,165,207),'V75':anell(L1,165,207)},'veins_140_165':{'V74':anell(L0,140,165),'V75':anell(L1,140,165)},'veins_207_230':{'V74':anell(L0,207,230),'V75':anell(L1,207,230)}}
# el punt més fosc de l'oest (az 178–188, r 461–469)
z=(az>=178)&(az<=188)&(rr>=461)&(rr<=469); rep['fosc_W_az178_188_r461_469']={'V74_Lmin':float(L0[z].min()),'V74_Lmitj':float(L0[z].mean()),'V75_Lmin':float(L1[z].min()),'V75_Lmitj':float(L1[z].mean())}
# dentat i radi
def dentat(C):
    Lm=C.mean(-1); r50=[]
    for a0 in np.arange(0,360,1.0):
        s=(az>=a0)&(az<a0+1)&(rr>=440)&(rr<470); rs=rr[s]; ls=Lm[s]; o=np.argsort(rs); rs,ls=rs[o],ls[o]; lo=np.median(ls[rs<446]); hi=np.median(ls[rs>464]); mid=(lo+hi)/2; r50.append(rs[np.argmax(ls>mid) if hi>lo else 0])
    r50=np.array(r50); hp=r50-gaussian_filter1d(r50,1.0,mode='wrap'); return r50,np.array([hp[i:i+10].std() for i in range(0,360,10)])
rA,dA=dentat(C0); rB,dB=dentat(C1); rep['dentat']={'V74':[float(dA.mean()),float(dA.max())],'V75':[float(dB.mean()),float(dB.max())],'r50_std_V74_V75':[float(rA.std()),float(rB.std())]}
dl=np.abs(L1-L0); fora=(rr>462)&~((az>=160)&(az<=212)); rep['canvis']={'max_dL_fora_r462_fora_W':float(dl[fora].max()),'max_dL_disc_r440':float(dl[rr<440].max()),'max_dL_W_az160_212_r456_470':float(dl[(az>=160)&(az<=212)&(rr>=456)&(rr<470)].max()),'alfa_min_V74_V75':[float(np.load('roi74p_compost.npz')['C'][...,3].min()/65535),float(a1.min())]}
json.dump(rep,open('d3_metriques_v75.json','w'),indent=1); print(json.dumps(rep,indent=1))
# vistes: tires polars i retalls
def polar(C,a0,a1):
    A=np.linspace(a0,a1,int((a1-a0)*4)+1); Rr=np.arange(430,480,0.5); AA,RR=np.meshgrid(np.radians(A),Rr); xs=CX+RR*np.cos(AA); ys=CY-RR*np.sin(AA); return np.dstack([map_coordinates(C[...,k],[ys,xs],order=1) for k in range(3)])
for nom,(a0,a1) in {'dalt_az50_130':(50,130),'oest_az150_220':(150,220)}.items():
    P0,P1=polar(C0,a0,a1),polar(C1,a0,a1); lo,hi=np.percentile(P0,[0.5,99.5]); st=lambda v: np.uint8(np.clip((v-lo)/(hi-lo),0,1)*255)
    im=np.vstack([st(P0),np.full((4,P0.shape[1],3),255,np.uint8),st(P1)]); Image.fromarray(im).resize((im.shape[1]*2,im.shape[0]*2),Image.NEAREST).save('v_D14_polar_%s_V74_V75.png'%nom)
    # el mateix amb el to ×3 (Lluna aclarida) per veure el limbe fosc
    st3=lambda v: np.uint8(np.clip(((v-lo)/(hi-lo))**(1/2.5),0,1)*255); im=np.vstack([st3(P0),np.full((4,P0.shape[1],3),255,np.uint8),st3(P1)]); Image.fromarray(im).resize((im.shape[1]*2,im.shape[0]*2),Image.NEAREST).save('v_D14_polar_%s_V74_V75_to3.png'%nom)
for nom,(x0,y0,x1,y1) in {'dalt_az80_110':(5250,3290,5420,3360),'oest_az175_195':(4900,3700,4960,3860)}.items():
    sl=(slice(y0-2777,y1-2777),slice(x0-4377,x1-4377)); a=np.clip(C0[sl],0,1); b=np.clip(C1[sl],0,1); lo,hi=np.percentile(a,[1,99]); st=lambda v: np.uint8(np.clip(((v-lo)/(hi-lo))**(1/2.0),0,1)*255)
    im=np.hstack([st(a),np.full((a.shape[0],3,3),255,np.uint8),st(b)]); Image.fromarray(im).resize((im.shape[1]*4,im.shape[0]*4),Image.NEAREST).save('v_D14_retall_%s_V74_V75_x4.png'%nom)
print('vistes fetes')
