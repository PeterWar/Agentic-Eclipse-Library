"""CORONA (tasca B), pas 1: descodifica els 5 RAW Vixen (2970, 2971, 2972, 2979, 2983), troba el centre lunar (2972/2979/2983),
comprova la linealitat entre parells consecutius i compon l'HDR lineal (DN16/s) en coordenades del sensor (mig format)."""
import sys, json, time, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
from scipy.ndimage import map_coordinates, gaussian_filter, label, binary_dilation
exec(open(SP+'/a10_lluna_raw.py').read().split('res=[]')[0].split('# 2) fotogrames RAW')[1])   # llegeix(), troba_lluna(), ROOT (com a15)
# CORRECCIÓ A LA BASE: libraw llegeix un negre per canal [0,34,101,67] per a aquests CR3 (absurd; els marges òptics diuen 512 a tots els canals i
# fotogrames) i user_black=512 l'hi SUMA. Amb la recepta d'a10 queda un offset residual ≈1900 DN16 per fotograma (linealitat 0,29–0,58).
# → descodificació a mà (corona_raw.llegeix_ma): mateix agrupament 2×2 que half_size, negre 512, escala 65535/(16383−512)=4,1297, sense retall a 0.
from corona_raw import llegeix_ma
FR=[('572A2970.CR3',1/30),('572A2971.CR3',1/8),('572A2972.CR3',0.5),('572A2979.CR3',2.0),('572A2983.CR3',10.0)]
SAT=60000; disc3=(np.hypot(*np.mgrid[-3:4,-3:4])<=3)   # element estructurant radi 3 px
lum={}; rad={}; valid={}; sat={}; info={}
for f,t in FR:
    t0=time.time(); img,s=llegeix_ma(f); L=img.mean(-1); s=s|(img>=SAT).any(-1); sd=binary_dilation(s,disc3)
    lum[f]=L; sat[f]=sd; rad[f]=L/t; info[f]=dict(t=t,forma=list(L.shape),n_sat=int(s.sum()),n_sat_dil=int(sd.sum()),p50=float(np.median(L)),p99=float(np.percentile(L,99)),max=float(L.max()))
    print(f,info[f],'%.1fs'%(time.time()-t0),flush=True)
# centres lunars
cen={}
for f in ['572A2972.CR3','572A2979.CR3','572A2983.CR3']:
    cx,cy,R,rms=troba_lluna(lum[f]); cen[f]=dict(cx=float(cx),cy=float(cy),R=float(R),rms=float(rms)); print(f,'centre (%.2f,%.2f) R %.2f rms %.2f'%(cx,cy,R,rms),flush=True)
cen['572A2970.CR3']=dict(cen['572A2972.CR3']); cen['572A2971.CR3']=dict(cen['572A2972.CR3'])
H,W=lum[FR[0][0]].shape; yy,xx=np.mgrid[0:H,0:W]
# radi de saturació per fotograma (max r de píxels saturats respecte del seu centre, i fracció saturada per anell)
for f,t in FR:
    c=cen[f]; rr=np.hypot(xx-c['cx'],yy-c['cy']); s=sat[f]
    info[f]['r_sat_max_half']=float(rr[s].max()) if s.any() else 0.0
    # radi fins on >50 % de l'anell està saturat
    rs=0.0
    for k in np.arange(int(c['R']),1400,4):
        m=(rr>=k)&(rr<k+4)
        if m.any() and s[m].mean()>0.5: rs=float(k+4)
    info[f]['r_sat_50pct_half']=rs
    # màscara de validesa: no saturat i fora del disc lunar propi (R+3 px)
    marge=1.5 if t<=0.5 else 3.0   # curts: limbe net (50 % a 225,7, gradient màxim a 226,5); llargs: glow (i ja saturats al limbe)
    valid[f]=(~s)&(rr>=c['R']+marge)
    print(f,'r_sat_max %.0f  r_sat_50%% %.0f  (R=%.1f)'%(info[f]['r_sat_max_half'],rs,c['R']),flush=True)
# linealitat: parells consecutius, solapament vàlid i amb senyal (curt >= 1500 DN)
lin=[]
for (fa,ta),(fb,tb) in zip(FR[:-1],FR[1:]):
    m=valid[fa]&valid[fb]&(lum[fa]>=1500)&(lum[fb]>=1500)
    q=rad[fb][m]/rad[fa][m]; d=dict(parell=f'{fb[4:8]}/{fa[4:8]}',t=[tb,ta],n=int(m.sum()),quocient_mediana=float(np.median(q)),quocient_sumes=float(rad[fb][m].sum()/rad[fa][m].sum()),
        quocient_mitjana=float(q.mean()),q16_84=[float(np.percentile(q,16)),float(np.percentile(q,84))])
    # per nivells del curt (per veure dependència amb el nivell = offset o no-linealitat)
    bins=[1500,4000,10000,20000,40000,60000]; d['per_nivell_curt']=[]
    for lo,hi in zip(bins[:-1],bins[1:]):
        mm=m&(lum[fa]>=lo)&(lum[fa]<hi)
        if mm.sum()>200: d['per_nivell_curt'].append([lo,hi,int(mm.sum()),float(np.median(rad[fb][mm]/rad[fa][mm]))])
    lin.append(d); print(json.dumps(d),flush=True)
# AJUST LINEAL per parell: llarg = a + b·curt (medianes per caixes log del curt, mínims quadrats ponderats pel nombre de píxels).
# Els quocients dels llargs baixen amb el nivell: és un OFFSET (cel que s'enfosqueix després de C2), no un guany. S'alinea tot al 2972 (referència C2+11 s).
def ajust_lineal(x,y,m):
    xb=x[m]; yb=y[m]; ed=np.geomspace(1500,max(xb.max(),1600),14); X=[];Y=[];N=[]
    for lo,hi in zip(ed[:-1],ed[1:]):
        k=(xb>=lo)&(xb<hi)
        if k.sum()>300: X.append(np.median(xb[k])); Y.append(np.median(yb[k])); N.append(k.sum())
    X=np.array(X);Y=np.array(Y);Wt=np.sqrt(np.array(N,float)); A=np.stack([np.ones_like(X),X],1)*Wt[:,None]; c,*_=np.linalg.lstsq(A,Y*Wt,rcond=None)
    return float(c[0]),float(c[1]),[[round(float(a),1),round(float(b),1),int(n)] for a,b,n in zip(X,Y,N)]
radc={f:rad[f].copy() for f,_ in FR}; ajust={}; alin={}
ordre_amunt=['572A2972.CR3','572A2979.CR3','572A2983.CR3']; ordre_avall=['572A2972.CR3','572A2971.CR3','572A2970.CR3']
for seq in (ordre_amunt,ordre_avall):
    for fa,fb in zip(seq[:-1],seq[1:]):   # fa ja alineat; fb s'alinea a fa
        m=valid[fa]&valid[fb]&(lum[fa]>=1500)&(lum[fb]>=1500)
        a,b,caixes=ajust_lineal(radc[fa],radc[fb],m)   # fb = a + b·fa  →  fb_alineat = (fb − a)/b
        radc[fb]=(radc[fb]-a)/b; q=np.median(radc[fb][m]/radc[fa][m])
        ajust[fb]=dict(respecte=fa,a_DN16_s=a,b=b,caixes_curt_llarg_n=caixes,quocient_despres=float(q),
                       nivell_cel_llunya_abans=float(np.median(rad[fb][valid[fb]&(np.hypot(xx-cen[fb]['cx'],yy-cen[fb]['cy'])>1000)])),
                       nivell_cel_llunya_despres=float(np.median(radc[fb][valid[fb]&(np.hypot(xx-cen[fb]['cx'],yy-cen[fb]['cy'])>1000)])))
        print('ajust %s respecte %s: a=%.1f DN16/s  b=%.4f  → quocient després %.4f  (cel llunyà abans %.0f, després %.0f)'%(fb[4:8],fa[4:8],a,b,q,ajust[fb]['nivell_cel_llunya_abans'],ajust[fb]['nivell_cel_llunya_despres']),flush=True)
ajust['572A2972.CR3']=dict(respecte='referència',a_DN16_s=0.0,b=1.0,nivell_cel_llunya_abans=float(np.median(rad['572A2972.CR3'][valid['572A2972.CR3']&(np.hypot(xx-cen['572A2972.CR3']['cx'],yy-cen['572A2972.CR3']['cy'])>1000)])))
fact={f:1.0 for f,_ in FR}; corr_aplicades=[[f,ajust[f]['a_DN16_s'],ajust[f]['b']] for f,_ in FR]
# HDR ponderat per temps d'exposició
num=np.zeros((H,W),np.float64); den=np.zeros((H,W),np.float64); nval=np.zeros((H,W),np.int8)
for f,t in FR:
    w=t*valid[f]; num+=w*radc[f]; den+=w; nval+=valid[f]
hdr=np.where(den>0,num/np.maximum(den,1e-12),0).astype(np.float32); vany=nval>0
c=cen['572A2972.CR3']; rr=np.hypot(xx-c['cx'],yy-c['cy'])
# quins fotogrames contribueixen per anell (r en px de mig format des del centre 2972)
contrib=[]
for k in range(220,720,10):
    m=(rr>=k)&(rr<k+10); contrib.append([k,k+10]+[round(float(valid[f][m].mean()),3) for f,_ in FR]+[round(float(vany[m].mean()),3)])
np.savez_compressed(SP+'/corona_hdr_sensor_half.npz',hdr=hdr,valid=vany,nval=nval,cx=c['cx'],cy=c['cy'],R=c['R'])
json.dump(dict(fotogrames=info,centres=cen,linealitat=lin,ajust_lineal=ajust,correccions_a_b=corr_aplicades,contribucio_per_anell_half=contrib,
               nota='contribucio: [r0,r1, fracció vàlida 2970,2971,2972,2979,2983, fracció amb ≥1]'),open(SP+'/corona_1_sensor.json','w'),indent=1)
print('contribució per anell (r half des del centre 2972): r0 r1 | 2970 2971 2972 2979 2983 | qualsevol')
for c_ in contrib: print(c_)
print('fet')
