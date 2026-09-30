"""fd3: refutació de les afirmacions del lector C (m1, limbe de dalt) amb mesures pròpies."""
import numpy as np, json
from scipy import ndimage as ndi
import fd_lib as F
c74=F.compo74(); c71=F.compo71()
C74,a74,P=c74.recompon(exclou=(222,),retorna_passos=True); C71,_=c71.recompon(exclou=(218,219,220))
L74=F.Lstar(C74); L71=F.Lstar(C71); Lps=F.Lstar(F.compost_ps())
res={}
def r_cross(prof,rb,val,down=True):
    for i in range(len(prof)-1):
        if down and prof[i]>=val>prof[i+1]: return float(rb[i]+(prof[i]-val)/(prof[i]-prof[i+1]))
        if (not down) and prof[i]<val<=prof[i+1]: return float(rb[i]+(val-prof[i])/(prof[i+1]-prof[i]))
    return None
rb=np.arange(436,476)
def prof(A,s,stat=np.median): return np.array([stat(A[s&F.anell(r,r+1)]) if (s&F.anell(r,r+1)).any() else np.nan for r in rb])
# ---- 1) vores per sector de 4°: alfa efectiva 30 (r50), base 3 L* r50 (V74 i V71), foto 96 L* r50 (contingut), alfa 76 màx dins silueta, alfa 96/204/206 màx dins
rgb30,al30=c74.carrega(30); rgb3,al3=c74.carrega(3); rgb96,al96=c74.carrega(96); rgb204,al204=c74.carrega(204); rgb206,al206=c74.carrega(206); rgb76,al76=c74.carrega(76)
L3=F.Lstar(rgb3); L96=F.Lstar(rgb96); L204=F.Lstar(rgb204); L206=F.Lstar(rgb206)
rgb30_71,al30_71=c71.carrega(30); rgb3_71,al3_71=c71.carrega(3); rgb76_71,al76_71=c71.carrega(76); L3_71=F.Lstar(rgb3_71)
vores={}
for A0 in list(range(0,132,4))+list(range(160,212,4))+list(range(296,360,4)):
    s=F.sector(A0,A0+4); q={}
    pa=prof(al30,s,np.mean); q['r50_alfa30']=r_cross(pa,rb,0.5); q['alfa30_r456_460']=round(float(al30[s&F.anell(456,460)].mean()),3); q['alfa30_r460_465']=round(float(al30[s&F.anell(460,465)].mean()),3)
    pa71=prof(al30_71,s,np.mean); q['r50_alfa30_V71']=r_cross(pa71,rb,0.5)
    for nom,LL,down in (('base3',L3,False),('base3_V71',L3_71,False),('foto96',L96,False),('foto204',L204,False),('foto206',L206,False),('L74',L74,False),('L71',L71,False)):
        p=prof(LL,s); d=np.nanmedian(p[(rb>=440)&(rb<448)]); c=np.nanmedian(p[(rb>=462)&(rb<470)])
        if not np.isfinite(d) or not np.isfinite(c) or c<=d+2: q[nom]=None; continue
        r10=r_cross(p,rb+0.5,d+0.1*(c-d),False); r50=r_cross(p,rb+0.5,d+0.5*(c-d),False); r90=r_cross(p,rb+0.5,d+0.9*(c-d),False)
        q[nom]=dict(r50=round(r50,2) if r50 else None,amplada=round(r90-r10,2) if (r10 and r90) else None,L_disc=round(float(d),1),L_cor=round(float(c),1))
    dins=s&F.anell(440,456)
    q['alfa76_max_dins']=round(float(al76[dins].max()),4); q['alfa76_max_dins_V71']=round(float(al76_71[dins].max()),4)
    q['alfa96_max_dins']=round(float(al96[dins].max()),3); q['alfa204_max_dins']=round(float(al204[dins].max()),3); q['alfa206_max_dins']=round(float(al206[dins].max()),3)
    vores[A0]=q
print('az | r50 alfa30 V74/V71 | base3 r50 (ampl) V74 | V71 | foto96 r50 (ampl) | foto204 | foto206 | L74 r50 (ampl) | L71 | alfa76 max dins V74/V71')
for A0,q in vores.items():
    g=lambda k: ('%6.2f (%4.2f)'%(q[k]['r50'],q[k]['amplada']) if q.get(k) and q[k]['r50'] and q[k]['amplada'] else '     -      ')
    print('%3d | %s / %s | %s | %s | %s | %s | %s | %s | %s | %.3f/%.3f'%(A0,q['r50_alfa30'] and '%.1f'%q['r50_alfa30'],q['r50_alfa30_V71'] and '%.1f'%q['r50_alfa30_V71'],g('base3'),g('base3_V71'),g('foto96'),g('foto204'),g('foto206'),g('L74'),g('L71'),q['alfa76_max_dins'],q['alfa76_max_dins_V71']))
res['vores']=vores
# ---- 2) marca m1 (traç llarg): nivell marca vs mateix r fora de la marca (az 60–125), i textura azimutal per radi
m1=F.mask('m1'); ll=m1&(F.RR<455); cur=m1&(F.RR>=457)
def marca_vs_r(L,mk,a0,a1):
    dif=[]
    for r0 in np.arange(np.floor(F.RR[mk].min()),F.RR[mk].max()+1,1):
        a=mk&F.anell(r0,r0+1); b=(~mk)&F.anell(r0,r0+1)&F.sector(a0,a1)
        if a.sum()>=3 and b.sum()>=3: dif.append((float(np.median(L[a])),float(np.median(L[b]))))
    return dif
for nom,L in (('V74',L74),('V74_PS',Lps),('V71',L71)):
    d1=marca_vs_r(L,ll,60,126); d2=marca_vs_r(L,cur,60,126)
    res[f'm1_llarg_{nom}']=dict(L_marca=round(float(np.mean([a for a,b in d1])),2),L_mateix_r=round(float(np.mean([b for a,b in d1])),2),n_anells=len(d1))
    res[f'm1_curt_{nom}']=dict(L_marca=round(float(np.mean([a for a,b in d2])),2),L_mateix_r=round(float(np.mean([b for a,b in d2])),2),n_anells=len(d2))
    print(nom,'traç llarg',res[f'm1_llarg_{nom}'],'traç curt',res[f'm1_curt_{nom}'])
# textura azimutal: a cada radi enter 444–458, std de L al llarg de l'azimut (az 63–123, cel·les de 0,5°) després de treure la tendència (mediana ±5°)
azc=np.floor(F.AZ*2)/2; cells=np.arange(63,123,0.5)
def tex(L,r):
    ring=F.anell(r,r+1); p=np.array([float(np.median(L[ring&(azc==cc)])) for cc in cells]); return float((p-ndi.median_filter(p,21,mode='nearest')).std()), p
tx={}
L30c=F.Lstar(rgb30)
for r in range(444,460):
    tx[r]=dict(V74=round(tex(L74,r)[0],2),V74_PS=round(tex(Lps,r)[0],2),V71=round(tex(L71,r)[0],2),capa30_contingut=round(tex(L30c,r)[0],2),base3=round(tex(L3,r)[0],2),alfa30_mitjana=round(float(al30[F.anell(r,r+1)&F.sector(63,123)].mean()),3))
print('textura azimutal (std L* residual, az 63–123) per radi:'); [print(r,v) for r,v in tx.items()]
res['textura_azimutal']=tx
# ---- 3) ressalt a la vora de la màscara 30: per cel·la de 2°, perfil L74 r 446–458; desviació al r50 de l'alfa30 respecte a la recta entre r50−2,5 i r50+2,5; i el mateix a V71 al seu r50
azb=np.floor(F.AZ/2)*2; rr1=np.arange(444,462)
ress={}
for A0 in range(60,126,2):
    s=(azb==A0); pa=np.array([float(al30[s&F.anell(r,r+1)].mean()) for r in rr1]); r50=r_cross(pa,rr1+0.5,0.5)
    p=np.array([float(np.median(L74[s&F.anell(r,r+1)])) for r in rr1]); pp=np.array([float(np.median(Lps[s&F.anell(r,r+1)])) for r in rr1])
    if r50 is None: continue
    x=rr1+0.5; f=lambda P_: float(np.interp(r50,x,P_)-0.5*(np.interp(r50-2.5,x,P_)+np.interp(r50+2.5,x,P_)))
    ress[A0]=dict(r50_alfa30=round(r50,2),ressalt_V74=round(f(p),2),ressalt_PS=round(f(pp),2),perfil_L74=[round(v,1) for v in p])
print('ressalt a la vora de la màscara 30 (V74 recomp / PS):',{k:(v['r50_alfa30'],v['ressalt_V74'],v['ressalt_PS']) for k,v in ress.items()})
res['ressalt_vora_mask30']=ress
# la mateixa desviació avaluada a r50+1.5 i r50−1.5 (control: és un ressalt local o el trànsit?)
# ---- 4) contingut de la capa 30 a r 446–458 a dalt: hi ha vora clara?
for nomS,(a0,a1) in {'az80_100':(80,100),'az100_120':(100,120),'az0_20':(0,20),'az300_320':(300,320)}.items():
    s=F.sector(a0,a1); rr2=np.arange(444,462)
    res[f'capa30_perfil_{nomS}']=dict(r=rr2.tolist(),L_capa30=[round(float(np.median(L30c[s&F.anell(r,r+1)])),1) for r in rr2],alfa30=[round(float(al30[s&F.anell(r,r+1)].mean()),2) for r in rr2],L_base3=[round(float(np.median(L3[s&F.anell(r,r+1)])),1) for r in rr2],L74=[round(float(np.median(L74[s&F.anell(r,r+1)])),1) for r in rr2],L71=[round(float(np.median(L71[s&F.anell(r,r+1)])),1) for r in rr2],alfa30_V71=[round(float(al30_71[s&F.anell(r,r+1)].mean()),2) for r in rr2])
    print('--',nomS); [print('%-10s'%k,' '.join('%5s'%v for v in res[f'capa30_perfil_{nomS}'][k])) for k in res[f'capa30_perfil_{nomS}']]
F.dump('fd3_limbe',res)
# ---- vistes: limbe N az 80–110 al 400 % (V74 recomp, V74 PS, V71), to normal i to ×3 sobre el disc
y0,y1,x0,x1=520,580,880,1000
def to3(C): return np.clip(C*3,0,1)
F.fila([F.retall(C74,y0,y1,x0,x1,Z=4),F.retall(F.compost_ps(),y0,y1,x0,x1,Z=4),F.retall(C71,y0,y1,x0,x1,Z=4)],['V74 recomp','V74 Photoshop','V71']).save(F.S4+'/v_fd_limbeN_az80-110_x4.png')
F.fila([F.retall(to3(C74),y0,y1,x0,x1,Z=4),F.retall(to3(F.compost_ps()),y0,y1,x0,x1,Z=4),F.retall(to3(C71),y0,y1,x0,x1,Z=4),F.retall(to3(P[30][0]),y0,y1,x0,x1,Z=4),F.retall(to3(rgb30),y0,y1,x0,x1,Z=4)],['V74 ×3','V74 PS ×3','V71 ×3','després 30 ×3','contingut capa 30 ×3']).save(F.S4+'/v_fd_limbeN_az80-110_to3_x4.png')
print('fd3 fet')
