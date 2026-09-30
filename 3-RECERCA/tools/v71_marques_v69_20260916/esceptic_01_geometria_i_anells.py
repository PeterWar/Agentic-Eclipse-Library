"""esceptic_01: (1) geometria LROC↔capa 30; (4) capa 30 vs RAW 10 s a σ40; (2) cunya o taca: perfils per anells i radial del sector; (1b) residu de la taca després de treure l'albedo LROC."""
import sys, json, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from esceptic_comu import *
from compo import carrega
from scipy.ndimage import gaussian_filter, rotate
out={}
rr,az=graella(); R7=marca7()
rgb30,a30=carrega(30); L30=rgb30.mean(-1); al30=np.load(SP+'/roi_L30.npz')['c-1']/65535.
rgb62,a62=carrega(62); L62=rgb62.mean(-1); al62=np.load(SP+'/roi_L62.npz')['c-1']/65535.
print('capa30 alfa>0.5 dins r<0.95:',float((al30[rr<0.95]>0.5).mean()),' LROC alfa>0.5 dins r<0.95:',float((al62[rr<0.95]>0.5).mean()))
hp=lambda im,s1,s2: gaussian_filter(im,s1)-gaussian_filter(im,s2)
K=(rr<0.88)&(al30>0.5)&(al62>0.5)
# ---- (1) geometria LROC ↔ capa 30: passa-alt σ2–12, correlació global amb cerca de desplaçament i gir
H30=hp(L30,2,12); H62=hp(L62,2,12)
def norm0(h,k): h=np.where(k,h,0.0); h=h-h[k].mean(); return h/ (h[k].std()+1e-12)
h30=norm0(H30,K); h62=norm0(H62,K)
dx,dy,cmax,c0=xcorr_pic(h30,h62,20); out['LROC_vs_capa30_global']=dict(dx=dx,dy=dy,c_pic=round(cmax,3),c_0=round(c0,3),pearson_0=round(pearson(H30,H62,K),3))
print('global LROC↔capa30 (σ2–12):',out['LROC_vs_capa30_global'])
# gir: rotar LROC al voltant del centre físic
girs=[]
for g in np.arange(-3,3.01,0.5):
    r62=rotate(np.where(K,L62,np.nan_to_num(L62)),g,reshape=False,order=1,cval=0.0); r62=rotate(L62,g,reshape=False,order=1,cval=0.0)
    girs.append((float(g),round(pearson(hp(r62,2,12),H30,K&(rr<0.85)),4)))
out['LROC_vs_capa30_gir']=girs; print('gir (°, Pearson σ2–12):',girs)
# per tessel·les (240 px), centres a r<0.72 R + la marca 7
tess=[]; cent=[(954,1233,'MARCA7')]
for i in range(-3,4):
    for j in range(-3,4):
        x=CX+i*200; y=CY+j*200
        if np.hypot(x-CX,y-CY)<0.72*RS: cent.append((x,y,f'{i:+d},{j:+d}'))
for x,y,nom in cent:
    x0,y0=int(x-120),int(y-120); ta=h30[y0:y0+240,x0:x0+240]; tb=h62[y0:y0+240,x0:x0+240]; km=K[y0:y0+240,x0:x0+240]
    if km.mean()<0.9: continue
    w=np.outer(np.hanning(240),np.hanning(240)); ddx,ddy,cm,cz=xcorr_pic(ta*w,tb*w,15)
    tess.append(dict(nom=nom,x=int(x),y=int(y),r=round(float(np.hypot(x-CX,y-CY)/RS),2),az=round(float(np.rad2deg(np.arctan2(-(y-CY),x-CX))%360)),dx=ddx,dy=ddy,c_pic=round(cm,3),c_0=round(cz,3)))
out['LROC_vs_capa30_tesselles']=tess
print('tessel·les LROC↔capa30:'); [print('  ',t) for t in tess]
# ---- RAW 10 s ×3 → marc del compost: cerca del gir phi contra la capa 30 (passa-alt σ3–20)
raws={}
for f in ('572A2982','572A2983','572A2984'):
    d=llegeix(f); Y=d['Y']; cx,cy,R,rms=troba_lluna(Y); n=norm_anells(Y,cx,cy,R,0.97); raws[f]=(n,cx,cy,R,rms); print(f,'Lluna (%.2f,%.2f) R %.2f rms %.2f'%(cx,cy,R,rms))
def apilat(phi):
    S=[cap_al_compost(n,cx,cy,R,phi) for (n,cx,cy,R,rms) in raws.values()]; return np.mean(S,0)
H30b=hp(L30,3,20); Kc=(rr<0.85)&(al30>0.5)
scan=[]
for phi in np.arange(0,360,3):
    A=apilat(phi); scan.append((phi,pearson(hp(A,3,20),H30b,Kc)))
phi0=max(scan,key=lambda t:t[1])[0]
fine=[]
for phi in np.arange(phi0-4,phi0+4.01,0.25):
    A=apilat(phi); fine.append((float(phi),round(pearson(hp(A,3,20),H30b,Kc),4)))
PHI=max(fine,key=lambda t:t[1])[0]; cfi=max(fine,key=lambda t:t[1])[1]
nul=[c for p,c in scan if abs(((p-PHI+180)%360)-180)>20]
out['gir_RAW_compost']=dict(phi=PHI,pearson=cfi,nul_mitjana=round(float(np.mean(nul)),4),nul_std=round(float(np.std(nul)),4)); print('gir RAW→compost:',out['gir_RAW_compost'])
A=apilat(PHI); np.save(SP+'/esceptic_raw10s_compost.npy',A.astype(np.float32))
# la mateixa detecció contra LROC (albedo real): passa-alt σ3–20
H62b=hp(L62,3,20); K2=Kc&(al62>0.5)
c_lroc=pearson(hp(A,3,20),H62b,K2); nul2=[pearson(hp(apilat(p),3,20),H62b,K2) for p in (PHI+60,PHI+120,PHI+180,PHI+240,PHI+300)]
out['RAW10s_vs_LROC_hp3_20']=dict(pearson=round(c_lroc,4),nuls=[round(x,4) for x in nul2]); print('RAW 10 s apilat vs LROC (σ3–20):',out['RAW10s_vs_LROC_hp3_20'])
# ---- (4) capa 30 vs RAW a escales grans: passa-baix σ40 dels dos mapes normalitzats per anells, dins r<0.85
n30=norm_anells(L30,CX,CY,RS,0.95,mask=al30>0.5); nA=A.copy()
lp30=gaussian_filter(np.nan_to_num(n30,nan=1.0),40); lpA=gaussian_filter(np.nan_to_num(nA,nan=1.0),40)
out['capa30_vs_RAW_lp40']=dict(pearson=round(pearson(lp30,lpA,rr<0.85),4),pearson_lp12=round(pearson(gaussian_filter(np.nan_to_num(n30,nan=1.0),12),gaussian_filter(np.nan_to_num(nA,nan=1.0),12),rr<0.85),4),
    amplitud_rms_capa30_pct=round(100*float(np.nanstd(lp30[rr<0.85])),3),amplitud_rms_RAW_pct=round(100*float(np.nanstd(lpA[rr<0.85])),3))
print('(4) capa30 vs RAW σ40:',out['capa30_vs_RAW_lp40'])
# profunditat de la taca a cada mapa
for nom,mp in (('RAW10s_norm',nA),('RAW10s_lp12',gaussian_filter(np.nan_to_num(nA,nan=1.0),12)),('capa30_norm',n30),('capa30_lp12',gaussian_filter(np.nan_to_num(n30,nan=1.0),12)),('LROC_norm',norm_anells(L62,CX,CY,RS,0.95,mask=al62>0.5))):
    out['profunditat_marca7_'+nom+'_pct']=round(profunditat_taca(mp,R7,rr,az),3)
print('profunditats marca 7 (%, + = més fosc que l\'anell):',{k:v for k,v in out.items() if k.startswith('profunditat')})
# ---- (2) cunya o taca: perfils azimutals (36 sectors) a 4 anells, RAW / capa30 / LROC
def prof_az(mp,r0,r1):
    return [float(np.nanmedian(mp[(rr>=r0)&(rr<r1)&(az>=s)&(az<s+10)])) for s in range(0,360,10)]
anells=[(0.15,0.35),(0.35,0.55),(0.55,0.75),(0.75,0.90)]
n62=norm_anells(L62,CX,CY,RS,0.95,mask=al62>0.5)
out['perfils_anells']={}
for r0,r1 in anells:
    pa=prof_az(nA,r0,r1); p3=prof_az(n30,r0,r1); p6=prof_az(n62,r0,r1)
    out['perfils_anells'][f'{r0}-{r1}']=dict(RAW=[round(x,4) for x in pa],capa30=[round(x,4) for x in p3],LROC=[round(x,3) for x in p6],
        corr_RAW_capa30=round(float(np.corrcoef(pa,p3)[0,1]),3),corr_RAW_LROC=round(float(np.corrcoef(pa,p6)[0,1]),3),
        amplitud_RAW_pct=round(100*float(np.std(pa)),3),sector_min_RAW=int(10*int(np.argmin(pa))),sector_max_RAW=int(10*int(np.argmax(pa))))
    print(f'anell {r0}-{r1}: corr RAW·capa30 %.3f · RAW·LROC %.3f · amplitud RAW %.3f %% · min RAW sector %d · max %d'%(out['perfils_anells'][f'{r0}-{r1}']['corr_RAW_capa30'],out['perfils_anells'][f'{r0}-{r1}']['corr_RAW_LROC'],out['perfils_anells'][f'{r0}-{r1}']['amplitud_RAW_pct'],out['perfils_anells'][f'{r0}-{r1}']['sector_min_RAW'],out['perfils_anells'][f'{r0}-{r1}']['sector_max_RAW']))
    print('   RAW   ',' '.join('%5.3f'%x for x in pa)); print('   capa30',' '.join('%5.3f'%x for x in p3)); print('   LROC  ',' '.join('%5.2f'%x for x in p6))
# perfil radial del sector 244–274° (normalitzat per anells) vs la resta: mínim local?
sec=(np.abs(((az-259+180)%360)-180)<15)
def prof_r(mp,k):
    return [float(np.nanmedian(mp[k&(rr>=r)&(rr<r+0.05)])) for r in np.arange(0.1,0.95,0.05)]
out['radial_sector_259']=dict(r=[round(float(r),2) for r in np.arange(0.1,0.95,0.05)],RAW=[round(x,4) for x in prof_r(nA,sec)],capa30=[round(x,4) for x in prof_r(n30,sec)],LROC=[round(x,3) for x in prof_r(n62,sec)])
print('radial sector 259±15 (normalitzat per anell):'); print('  r     ',' '.join('%5.2f'%x for x in out['radial_sector_259']['r'])); print('  RAW   ',' '.join('%5.3f'%x for x in out['radial_sector_259']['RAW'])); print('  capa30',' '.join('%5.3f'%x for x in out['radial_sector_259']['capa30'])); print('  LROC  ',' '.join('%5.2f'%x for x in out['radial_sector_259']['LROC']))
# ---- (1b) residu després de treure l'albedo: coeficient a partir del passa-alt (estructura fina), aplicat al passa-baix
kk=K2&(rr<0.85); hA=hp(A,3,20); h62b=H62b
a_hp=float(np.sum(hA[kk]*h62b[kk])/np.sum(h62b[kk]**2))
lpA12=gaussian_filter(np.nan_to_num(nA,nan=1.0),12); lp62=gaussian_filter(np.nan_to_num(n62,nan=1.0),12)
# LROC lineal normalitzat: la regressió al passa-alt dona a (RAW per unitat de L62); pel passa-baix cal L62 en les mateixes unitats
lp62L=gaussian_filter(L62,12); resid=lpA12-a_hp*(lp62L-np.nanmean(lp62L[kk]))
out['albedo']=dict(a_hp=a_hp,profunditat_marca7_RAW_lp12_pct=round(profunditat_taca(lpA12,R7,rr,az),3),profunditat_marca7_residu_sense_albedo_pct=round(profunditat_taca(resid,R7,rr,az),3),
   contribucio_albedo_a_la_marca7_pct=round(100*float(a_hp*(np.nanmean(lp62L[R7])-np.nanmean(lp62L[kk]))),3),
   amplitud_albedo_predita_lp12_rms_pct=round(100*float(a_hp*np.nanstd(lp62L[kk])),3),amplitud_RAW_lp12_rms_pct=round(100*float(np.nanstd(lpA12[kk])),3))
print('(1b) albedo:',out['albedo'])
json.dump(out,open(SP+'/esceptic_01.json','w'),indent=1,default=float)
# vista: RAW apilat normalitzat (lp12), capa30 lp12, LROC, residu
from PIL import Image
def vis(mp,lo,hi): return np.uint8(np.clip((np.nan_to_num(mp,nan=lo)-lo)/(hi-lo),0,1)*255)
pan=np.concatenate([vis(lpA12,0.97,1.03),vis(gaussian_filter(np.nan_to_num(n30,nan=1.0),12),0.8,1.2),vis(resid,0.97,1.03),vis(gaussian_filter(L62,12),np.nanpercentile(gaussian_filter(L62,12)[kk],1),np.nanpercentile(gaussian_filter(L62,12)[kk],99))],1)
Image.fromarray(pan[500:1500,:]).save(SP+'/esceptic_v01_raw_capa30_residu_lroc.png'); print('fet')
