"""S2: candidat V50 a la ROI lunar (1400×1400), mateix model de fusió que S1 (verificat a 2,8 DN16).
Canvis respecte de la V49, tots declarats:
 (1) màscara de la base oberta fins al limbe aparent de la font lunar (F4 suavitzat, rampa 1 px);
 (2) capa nova «anell»: corona fotografiada pels fotogrames Vixen 572A2968 (1/500 s, 7,4 s) i 572A2969 (1/125 s, 8,3 s),
     registrats a la Lluna, igualats al to de la base per canal i sector a l'anell on tots dos tenen dada;
     visible només on la base NO té dada (entre F4 i la vora de dada de la base, sectors esquerra/dalt/baix);
 (3) alfa de la capa lunar = cobertura geomètrica del disc F4 (rampa 1 px), en lloc del pes fotogràfic V44.
Píxels de Pere (capa lunar RGB), capa 09 i base RGB: intactes."""
import json, numpy as np
from pathlib import Path
from scipy.ndimage import map_coordinates, gaussian_filter1d
from PIL import Image
ROOT=Path('/Users/USUARI/Downloads/Eclipse 2026'); HERE=Path(__file__).resolve().parent; CAU=HERE/'cau'
OUT=ROOT/'output/earthshine_v50_temporal_20260912'; VIS=OUT/'vistes'; VIS.mkdir(exist_ok=True)
V=ROOT/'output/earthshine_v49_pere_reveal_20260912'; N=1400; CX=699.568111973117; CY=699.6475341408573
f4=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy'); th=np.linspace(0,2*np.pi,1440,endpoint=False)
SIG=3.0  # suavitzat circular de F4: 3 mostres = 0,75° ≈ 6 px de limbe (treu soroll de mesura, conserva relleu > 6 px)
f4s=gaussian_filter1d(f4,SIG,mode='wrap')
yy,xx=np.mgrid[0:N,0:N]; r=np.hypot(xx-CX,yy-CY); ang=np.arctan2(yy-CY,xx-CX)%(2*np.pi)
def polar(v): return np.interp(ang,np.append(th,2*np.pi),np.append(v,v[0]))
F4=polar(f4s); d=r-F4
sec12=(ang/(2*np.pi)*12).astype(int)
f=lambda nm,c: np.load(CAU/f'{nm}_ch{c}_roi.npy').astype(np.float64)/65535
B=np.stack([f('base',c) for c in (0,1,2)],-1); Bm_old=f('base',-2)
S=np.stack([f('l09',c) for c in (0,1,2)],-1); Sa=f('l09',-1)
Lr=np.stack([f('lun',c) for c in (0,1,2)],-1); Lm_old=f('lun',-2); La1=f('lun',-1)
# (3) alfa lunar geomètrica
wg=np.clip((d+10)/2,0,1)  # 0 a d<=-10 (màscara de Pere exacta), 1 a d>=-8 (geomètrica)
Lm_new=wg*np.clip(0.5-d/2.0,0,1)+(1-wg)*Lm_old
# (1) màscara de la base oberta fins a F4
Bm_new=np.maximum(Bm_old,np.clip(d+0.5,0,1))
# vora de dada de la base (S1) per azimut, suavitzada
s1=np.load(OUT/'S1_base_dada.npz'); dada=s1['dada'].copy(); ok=np.isfinite(dada)
dada[~ok]=np.interp(th[~ok],th[ok],dada[ok]); dada_s=gaussian_filter1d(dada,SIG,mode='wrap'); DADA=polar(dada_s)
# (2) anell: fotogrames Vixen curts a 5,0–8,3 s (1/3200 ×2, 1/2000, 1/500, 1/125), pes ∝ exposició,
#     valors retallats de cada exposició exclosos per píxel (sostre = 0,97 × màxim del fotograma a l'anell),
#     els de 1/3200 i 1/2000 (sense registre fi) desplaçats al centre lunar del 2968 mesurat per la seva pròpia vora (M1-bis).
from scipy.ndimage import shift as ndshift
b=json.load(open(ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json'))['frames']
STEMS=['572A2965','572A2966','572A2967','572A2968','572A2969']
CENT={'572A2965':(-0.83,-1.21),'572A2966':(-0.46,-0.99),'572A2967':(-1.0,-0.99),'572A2968':(-1.09,-0.64),'572A2969':(-0.58,-0.55)}  # (dx,dy) de la vora pròpia, fit de cercle
FR=[next(x for x in b if x['stem']==st) for st in STEMS]
acc=np.zeros((N,N,3)); wacc=np.zeros((N,N)); ring=(d>-6)&(d<30); sost={}
# correcció V38 (B2) del dèficit de llum de cada fotograma prop de la SEVA vora lunar: valor × exp(−B_classe(d)); d = distància al limbe F4 (fotogrames registrats a la Lluna)
TAULA=json.load(open(ROOT/'research/tools/v38_20260908/cau/correccio_vora_lunar.json'))['taula']
def classe(e): return 'curts' if e<=1/800 else ('mitjans' if e<=1/50 else 'llargs')
def corr_vora(e):
    tb=TAULA[classe(e)]; Bv=np.interp(d,np.asarray(tb['d_px']),np.asarray(tb['B_ln']),left=tb['B_ln'][0],right=0.0); return np.exp(-Bv)
for x in FR:
    g=np.load(x['path']).astype(np.float64); w=np.load(x['weight']).astype(np.float64)
    dxy=(CENT['572A2968'][0]-CENT[x['stem']][0], CENT['572A2968'][1]-CENT[x['stem']][1])
    if x['stem']!='572A2968' and x['stem']!='572A2969':
        g=np.stack([ndshift(np.nan_to_num(g[...,c],nan=np.nan),(dxy[1],dxy[0]),order=1,mode='nearest') for c in range(3)],-1)
        w=ndshift(w,(dxy[1],dxy[0]),order=1,mode='nearest')
    g=g*corr_vora(x['exp'])[...,None]
    fin=np.isfinite(g).all(-1)
    ceil=np.array([0.97*np.nanmax(g[ring][:,c]) for c in range(3)]); sost[x['stem']]=ceil.tolist()
    ok=fin&(w>0)&(g<ceil).all(-1)
    wk=1.0  # pesos iguals: mitjana temporal 5,0–8,3 s (la banda canvia amb l'instant, no és soroll)
    acc[ok]+=g[ok]*wk; wacc[ok]+=wk
lin=np.where(wacc[...,None]>0,acc/np.maximum(wacc[...,None],1e-12),np.nan)
# forats sense cap dada: veí vàlid més proper
from scipy.ndimage import distance_transform_edt
nod=~np.isfinite(lin).all(-1)
if nod.any():
    idx=distance_transform_edt(nod,return_distances=False,return_indices=True); lin=lin[idx[0],idx[1]]
# igualació de to per canal i sector (36 de 10°) a l'anell de solapament [DADA+1, DADA+12] on la base té dada
sec36=(ang/(2*np.pi)*36).astype(int); R0=np.maximum(DADA,F4)+2; prom09=(S[...,0]-S[...,1]>0.25)
ov=(r>=R0)&(r<=R0+10)&(Bm_old>0.999)&np.isfinite(lin).all(-1)&(lin>0).all(-1)&(B>0.02).all(-1)&~prom09
ovfit=ov&(B<0.97).all(-1)  # el R de la base és retallat a 1,0 al limbe: el pendent només amb píxels no retallats
alpha=np.zeros((36,3)); beta=np.zeros((36,3)); res=np.zeros((36,3)); npx=np.zeros(36,int)
# beta global per canal (robust), alfa per sector
bg=np.zeros(3)
for c in range(3):
    X=np.log(lin[ovfit][:,c]); Y=np.log(B[ovfit][:,c]); sid=sec36[ovfit]
    # treu la mitjana per sector abans d'ajustar el pendent (alfa lliure per sector)
    for _ in range(3):
        Xm=X-np.bincount(sid,X,36)[sid]/np.maximum(np.bincount(sid,minlength=36),1)[sid]; Ym=Y-np.bincount(sid,Y,36)[sid]/np.maximum(np.bincount(sid,minlength=36),1)[sid]
        b_=np.sum(Xm*Ym)/np.sum(Xm*Xm); e=Ym-b_*Xm; k=np.abs(e)<2.5*e.std(); X,Y,sid=X[k],Y[k],sid[k]
    bg[c]=b_
for s_ in range(36):
    m=ov&(sec36==s_); npx[s_]=m.sum()
    for c in range(3):
        if m.sum()<200: alpha[s_,c]=beta[s_,c]=res[s_,c]=np.nan; continue
        X=np.log(lin[m][:,c]); Y=np.log(B[m][:,c]); e=Y-bg[c]*X
        for _ in range(3):
            a_=np.median(e); k=np.abs(e-a_)<2.5*e.std(); e=e[k]
        alpha[s_,c]=a_; beta[s_,c]=bg[c]; res[s_,c]=e.std()
# suavitzat circular dels coeficients (σ=1 sector) i interpolació contínua per azimut
th36=(np.arange(36)+0.5)/36*2*np.pi
def smooth36(a):
    a=a.copy(); bad=~np.isfinite(a)
    if bad.any(): a[bad]=np.interp(th36[bad],np.r_[th36[~bad]-2*np.pi,th36[~bad],th36[~bad]+2*np.pi],np.tile(a[~bad],3))
    return gaussian_filter1d(a,1.0,mode='wrap')
al=np.stack([np.interp(ang,np.r_[th36-2*np.pi,th36,th36+2*np.pi],np.tile(smooth36(alpha[:,c]),3)) for c in range(3)],-1)
be=np.stack([np.interp(ang,np.r_[th36-2*np.pi,th36,th36+2*np.pi],np.tile(smooth36(beta[:,c]),3)) for c in range(3)],-1)
fill=np.clip(np.exp(al+be*np.log(np.maximum(lin,1e-6))),0,1); fill[~np.isfinite(lin)]=0
# alfa de l'anell: 1 entre F4-1 i DADA+1, rampes d'1 px; zero on la base ja té dada dins de F4 (DADA < F4+0,5)
need=DADA-F4>0.5
Fa=np.clip((d+2.5)/2.0,0,1)*np.clip((DADA+1.0)-r+0.5,0,1)*need
# --- composició (model S1) ---
def compose(Bm,Lm,use_fill):
    Ca=Bm; Cc=B*Bm[...,None]
    if use_fill:
        Cc=Fa[...,None]*fill+(1-Fa[...,None])*Cc; Ca=Fa+Ca-Fa*Ca
    Cb=np.where(Ca[...,None]>0,Cc/np.maximum(Ca[...,None],1e-9),0)
    mix=(1-Ca[...,None])*S+Ca[...,None]*np.maximum(S,Cb); Cc=Sa[...,None]*mix+(1-Sa[...,None])*Cc; Ca=Sa+Ca-Sa*Ca
    La=La1*Lm; Cc=La[...,None]*Lr+(1-La[...,None])*Cc; Ca=La+Ca-La*Ca
    return np.where(Ca[...,None]>0,Cc/np.maximum(Ca[...,None],1e-9),0),Ca
v49,_=compose(Bm_old,Lm_old,False); cand,Ca=compose(Bm_new,Lm_new,True)
pere=np.load(V/'A2_Pere_actual_RGB16.npy').astype(np.float64)/65535
assert np.abs(v49-pere).max()*65535<3.5
np.save(CAU/'cand_roi_u16.npy',np.rint(cand*65535).astype(np.uint16)); np.save(CAU/'cand_alpha_roi.npy',Ca)
np.save(CAU/'base_mask_new_u16.npy',np.rint(Bm_new*65535).astype(np.uint16)); np.save(CAU/'lun_mask_new_u16.npy',np.rint(Lm_new*65535).astype(np.uint16))
np.save(CAU/'fill_rgb_u16.npy',np.rint(fill*65535).astype(np.uint16)); np.save(CAU/'fill_alpha_u16.npy',np.rint(Fa*65535).astype(np.uint16))
# --- mètriques ---
G=lambda a:a[...,1]*65535
def med(img,m): return float(np.median(img[m])) if m.any() else None
rows=[]
for s in range(12):
    m=sec12==s
    rows.append(dict(sector=s,corona_8_14=med(G(v49),m&(d>=8)&(d<14)),
        v49_d0_2=med(G(v49),m&(d>=0)&(d<2)),cand_d0_2=med(G(cand),m&(d>=0)&(d<2)),
        v49_d2_5=med(G(v49),m&(d>=2)&(d<5)),cand_d2_5=med(G(cand),m&(d>=2)&(d<5)),
        v49_dm3_0=med(G(v49),m&(d>=-3)&(d<0)),cand_dm3_0=med(G(cand),m&(d>=-3)&(d<0)),
        v49_min_d0_8=float(np.min([med(G(v49),m&(d>=k)&(d<k+1)) for k in range(0,8)])),cand_min_d0_8=float(np.min([med(G(cand),m&(d>=k)&(d<k+1)) for k in range(0,8)])),
        dada_menys_F4=float(np.median((DADA-F4)[m&(d>-1)&(d<1)])),fill_res_rms_pct=float(np.nanmedian(res[[s*3,s*3+1,s*3+2]][:,1])*100)))
inner=d<-10; assert np.abs(cand-v49)[inner].max()*65535<1.0, 'interior canviat'
# protuberàncies: píxels del 09 amb R-G gran a [-4,+10]: el candidat no pot ser més fosc que la V49
prom=(S[...,0]-S[...,1]>0.25)&(d>-4)&(d<10)
darker=int(((v49-cand)[...,0][prom]*65535>500).sum())
junc=[]
for s_ in range(12):
    m=(sec12==s_)&~prom09; a=[float(np.median(cand[...,c][m&(r>=DADA-2.5)&(r<DADA-0.5)&(DADA-F4>0.5)])) if (m&(DADA-F4>0.5)).any() else None for c in range(3)]
    b_=[float(np.median(cand[...,c][m&(r>=DADA+1)&(r<DADA+3)])) for c in range(3)]
    junc.append(dict(sector=s_,fill_RGB=a,base_RGB=b_,salt_pct=[None if a[c] is None else round((a[c]/b_[c]-1)*100,1) for c in range(3)]))
print('junció per sector (salt % R,G,B):',[(j['sector'],j['salt_pct']) for j in junc])
rep=dict(juncio=junc,beta_global=bg.tolist(),F4_suavitzat_max_abs_px=float(np.abs(f4-f4s).max()),F4_suavitzat_rms_px=float(np.std(f4-f4s)),frames_anell=[(x['stem'],x['exp'],x['t_mid_C2'],classe(x['exp'])) for x in FR],correccio_vora_lunar='research/tools/v38_20260908/cau/correccio_vora_lunar.json (V38 B2)',sostres=sost,centres_vora=CENT,
    solapament_px_per_sector36=npx.tolist(),to_alpha=alpha.tolist(),to_beta=beta.tolist(),to_res_rms_ln=res.tolist(),
    anell_necessari_sectors12=[bool(np.median(need[(sec12==s)&(d>-1)&(d<1)])) for s in range(12)],
    prominencies_pixels=int(prom.sum()),prominencies_mes_foscos_que_v49_500DN=darker,interior_max_diff_DN16=float(np.abs(cand-v49)[inner].max()*65535),
    per_sector=rows)
json.dump(rep,open(OUT/'S2_candidat.json','w'),ensure_ascii=False,indent=1)
print('F4 suau: max',rep['F4_suavitzat_max_abs_px'],'rms',rep['F4_suavitzat_rms_px']); print('residu to (ln) mediana per canal:',np.nanmedian(res,axis=0),'sectors sense solapament:',int(np.isnan(res[:,1]).sum()),'min px',npx.min())
print('prominències més fosques (>500 DN):',darker,'de',int(prom.sum()))
for x in rows: print({k:(round(v,1) if isinstance(v,float) else v) for k,v in x.items()})
# --- vistes ---
def png(a,name): Image.fromarray(np.rint(np.clip(a,0,1)*255).astype(np.uint8)).save(VIS/name)
png(v49,'S2_V49_ROI_1a1.png'); png(cand,'S2_candidat_ROI_1a1.png')
def crop3(img,cx,cy,w,h):
    a=img[cy-h//2:cy+h//2,cx-w//2:cx+w//2]; return np.repeat(np.repeat(a,3,0),3,1)
for name,(cx,cy) in dict(dalt=(700,246),baix=(700,1153),esquerra=(246,700),dreta=(1153,700),dalt_esq=(379,379),baix_dreta=(1020,1020)).items():
    w,h=(300,120) if name in('dalt','baix') else (120,300) if name in ('esquerra','dreta') else (200,200)
    a=crop3(v49,cx,cy,w,h); c=crop3(cand,cx,cy,w,h); sep=np.ones((a.shape[0],6,3))
    png(np.concatenate([a,sep,c],1),f'S2_{name}_V49_vs_candidat_x3.png')
print('vistes a',VIS)
