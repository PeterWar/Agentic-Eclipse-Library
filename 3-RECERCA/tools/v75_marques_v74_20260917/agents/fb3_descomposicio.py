"""fb3: P = capa30_V69 + W_S8 (revelat de Pere abans de l'S8, reconstruït); alineació del camp W; descomposició de la taca entre P i W."""
import json, numpy as np
from scipy.ndimage import median as ndmed, gaussian_filter, gaussian_filter1d
S4='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
R='/Users/USUARI/Desktop/Eclipse 2026'
CX,CY,RS=998.88,998.41,456.0
Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY); az=(np.degrees(np.arctan2(-(Y-CY),X-CX)))%360; sec=(az//5).astype(int)
d69=np.load(OLD+'/roi_L30.npz'); G69=d69['c1'].astype(np.float64)
V=np.load(S4+'/fb2_vel_s8.npz'); W2s8=V['W2'].astype(np.float64)   # 1400², convenció S8, centre (699.57,699.65)
def coloca(W,dx=0,dy=0):
    out=np.zeros((2000,2000)); out[300+dy:1700+dy,300+dx:1700+dx]=W; return out
# alineació: P = G69 + W ha de ser suau al limbe (d −14…−2): tria (dx,dy) que minimitza l'energia d'alta freqüència radial/azimutal de P a l'anell
ann=(rr>RS-14)&(rr<RS-2)
def rug(P):
    h=P-gaussian_filter(P,2.0); return float(np.sqrt(np.mean(h[ann]**2)))
best=None; tab={}
for dy in range(-3,4):
    for dx in range(-3,4):
        P=G69+coloca(W2s8,dx,dy); v=rug(P); tab[f'{dx},{dy}']=round(v,1)
        if best is None or v<best[0]: best=(v,dx,dy)
print('rugositat de P al limbe per (dx,dy):',tab); print('millor',best,' rugositat de G69 sol:',rug(G69))
_,dx,dy=best; W=coloca(W2s8,dx,dy); P=G69+W
np.save(S4+'/fb3_W_s8_roi.npy',W.astype(np.float32)); np.save(S4+'/fb3_P_rec.npy',P.astype(np.float32))
# perfils per sector de 5° (mediana, bins 2 px, r 100–452) en DN16
rb=np.arange(100,454,2); rc=rb[:-1]+1; NS=72
def perfils(A,v=None):
    ib=((rr-100)//2).astype(int); ok=(rr>=100)&(rr<452)
    if v is not None: ok&=v
    lab=sec[ok]*len(rc)+ib[ok]; cnt=np.bincount(lab,minlength=NS*len(rc)); med=ndmed(A[ok],labels=lab,index=np.arange(NS*len(rc)))
    return np.where(cnt>=6,med,np.nan).reshape(NS,len(rc))
PG=perfils(G69); PW=perfils(W); PP=perfils(P)
rgb62=np.load(S4+'/roi74p_L62.npz'); L62=np.dstack([rgb62['c0'],rgb62['c1'],rgb62['c2']]).astype(np.float64).mean(-1); v62=rgb62['c-1']>30000
PL=perfils(L62,v62); RAW=np.load(OLD+'/raw_disc_norm_2000.npy').astype(np.float64); PRW=perfils(RAW,np.isfinite(RAW))
np.savez_compressed(S4+'/fb3_perfils_DN16.npz',rc=rc,G69=PG,W=PW,P=PP,LROC=PL,RAW=PRW)
T=list(range(48,54)); V1=list(range(42,48)); V2=list(range(54,60)); VV=V1+V2
def grp(Pf,idx): return np.nanmedian(Pf[idx],0)
rows=[]
print(' r    G69_t  G69_v | W_t   W_v  | P_t    P_v   | ln G69 t/v | ln P t/v | (W_t−W_v)/P_v | ln LROC t/v | RAW t/v')
for i in range(0,len(rc),10):
    g_t,g_v=grp(PG,T)[i],grp(PG,VV)[i]; w_t,w_v=grp(PW,T)[i],grp(PW,VV)[i]; p_t,p_v=grp(PP,T)[i],grp(PP,VV)[i]; l_t,l_v=grp(PL,T)[i],grp(PL,VV)[i]; r_t,r_v=grp(PRW,T)[i],grp(PRW,VV)[i]
    row=dict(r=int(rc[i]),G69_t=round(g_t),G69_v=round(g_v),W_t=round(w_t),W_v=round(w_v),P_t=round(p_t),P_v=round(p_v),ln_G69=round(float(np.log(g_t/g_v)),4),ln_P=round(float(np.log(p_t/p_v)),4),dW_rel=round(float((w_t-w_v)/p_v),4),ln_LROC=None if not np.isfinite(l_t*l_v) else round(float(np.log(l_t/l_v)),4),ln_RAW=None if not np.isfinite(r_t*r_v) else round(float(np.log(r_t/r_v)),4))
    rows.append(row); print(f"{row['r']:4d} {row['G69_t']:6d} {row['G69_v']:6d} | {row['W_t']:5d} {row['W_v']:5d} | {row['P_t']:6d} {row['P_v']:6d} | {row['ln_G69']:+.4f} | {row['ln_P']:+.4f} | {row['dW_rel']:+.4f} | {row['ln_LROC']} | {row['ln_RAW']}")
# la taca amb les màscares de Pere: dins/entorn de G69, P, W
M=np.load(S4+'/marques74_masks.npz'); m6=M['m6']; e6=M['ent_m6']
taca={}
for nom,A in (('G69',G69),('P_rec',P),('W',W)):
    taca[nom]=dict(dins=round(float(np.median(A[m6]))),entorn=round(float(np.median(A[e6]))),ln=round(float(np.log(np.median(A[m6])/np.median(A[e6]))),4) if nom!='W' else None)
print('taca dins/entorn (medianes DN16):',taca)
json.dump(dict(alineacio=dict(dx=dx,dy=dy,rugositat=tab,rug_G69=rug(G69)),perfils=rows,taca=taca,nota='sectors taca = az 240–270 (task), veïns 210–240 i 270–300; P = G69 + W_S8 (PNG calibrat)'),open(S4+'/fb3_descomposicio.json','w'),indent=1)
# figura
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig,ax=plt.subplots(2,2,figsize=(14,9))
for idx,lab,ls in ((T,'taca az 240–270','-'),(V1,'veïns 210–240','--'),(V2,'veïns 270–300',':')):
    ax[0,0].plot(rc,grp(PP,idx),'k'+ls,label='P (revelat Pere reconstruït) '+lab); ax[0,0].plot(rc,grp(PG,idx),'b'+ls,label='capa30 V69 '+lab)
    ax[0,1].plot(rc,grp(PW,idx),'r'+ls,label='W S8 '+lab)
ax[0,0].set_ylim(6000,14000); ax[0,0].set_title('perfils DN16 (mediana per sector)'); ax[0,0].legend(fontsize=7); ax[0,0].set_xlabel('r (px)')
ax[0,1].set_ylim(0,6000); ax[0,1].set_title('vel S8 restat, W (DN16)'); ax[0,1].legend(fontsize=7); ax[0,1].set_xlabel('r (px)')
ax[1,0].plot(rc,np.log(grp(PG,T)/grp(PG,VV)),'b',label='ln capa30_V69 taca/veïns'); ax[1,0].plot(rc,np.log(grp(PP,T)/grp(PP,VV)),'k',label='ln P taca/veïns'); ax[1,0].plot(rc,-(grp(PW,T)-grp(PW,VV))/grp(PP,VV),'r',label='−(W_t−W_v)/P_v'); ax[1,0].plot(rc,np.log(grp(PL,T)/grp(PL,VV)),'g',label='ln LROC taca/veïns'); ax[1,0].plot(rc,10*np.log(grp(PRW,T)/grp(PRW,VV)),'m',label='10× ln RAW taca/veïns')
ax[1,0].axhline(0,color='gray'); ax[1,0].set_ylim(-0.25,0.2); ax[1,0].legend(fontsize=7); ax[1,0].set_xlabel('r (px)'); ax[1,0].set_title('quocients sectorials')
im=np.clip((PP-np.nanmedian(PP,0)[None,:])/1500+0.5,0,1); ax[1,1].imshow(np.nan_to_num(im),aspect='auto',extent=[rc[0],rc[-1],360,0],cmap='gray'); ax[1,1].set_title('P − mediana azimutal (±1500 DN16), files = az'); ax[1,1].set_xlabel('r'); ax[1,1].set_ylabel('az')
plt.tight_layout(); plt.savefig(S4+'/v_fb3_perfils_P_W_capa.png',dpi=110); print('fet')
