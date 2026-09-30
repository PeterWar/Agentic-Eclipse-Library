"""fd1b: punts negres compactes NOMÉS sobre la recomposició sense la capa 222 (el compost de Photoshop porta les marques de Pere pintades
i contamina qualsevol mesura dins de les marques); també sobre la versió quantitzada a 8 bits (el que mostra la pantalla)."""
import numpy as np, json
from scipy import ndimage as ndi
import fd_lib as F
c74=F.compo74(); C74,a74=c74.recompon(exclou=(222,)); C71,_=F.compo71().recompon(exclou=(218,219,220))
L74=F.Lstar(C74); L8=F.Lstar(np.round(C74*255)/255); L71=F.Lstar(C71)
def blackhat(L,k):
    se=np.zeros((k,k),bool); yy,xx=np.mgrid[:k,:k]; se[(yy-k//2)**2+(xx-k//2)**2<=(k//2)**2]=True
    return ndi.grey_closing(L,footprint=se)-L
maps={'bh5':blackhat(L74,5),'bh11':blackhat(L74,11),'dmed9':ndi.median_filter(L74,9)-L74,'dmed21':ndi.median_filter(L74,21)-L74,'bh5_8bit':blackhat(L8,5),'dmed21_8bit':ndi.median_filter(L8,21)-L8}
res={}
for k in ('m1','m2','m3','m4','m5','m7'):
    mm=F.mask(k); ee=F.mask('ent_'+k); q={}
    for nom,v in maps.items():
        q[nom]=dict(marca_max=round(float(v[mm].max()),2),marca_p99=round(float(np.percentile(v[mm],99)),2),entorn_max=round(float(v[ee].max()),2),entorn_p99=round(float(np.percentile(v[ee],99)),2),
                    marca_n_gt3=int((v[mm]>3).sum()),marca_n_gt5=int((v[mm]>5).sum()),entorn_n_gt3=int((v[ee]>3).sum()),entorn_n_gt5=int((v[ee]>5).sum()))
    dif=[]
    for r0 in np.arange(np.floor(F.RR[mm].min()),F.RR[mm].max(),2):
        a=mm&F.anell(r0,r0+2); b=ee&F.anell(r0,r0+2)
        if a.sum()>=3 and b.sum()>=3: dif.append(float(np.median(L74[a])-np.median(L74[b])))
    q['marca_menys_entorn_aparellat_L']=round(float(np.mean(dif)),2) if dif else None
    q['L_marca']=round(float(L74[mm].mean()),1); q['L_entorn']=round(float(L74[ee].mean()),1); q['L_p1_marca']=round(float(np.percentile(L74[mm],1)),1); q['L_p1_entorn']=round(float(np.percentile(L74[ee],1)),1)
    q['gra_std_dmed9_marca']=round(float(maps['dmed9'][mm].std()),2); q['gra_std_dmed9_entorn']=round(float(maps['dmed9'][ee].std()),2)
    q['n_marca']=int(mm.sum()); q['n_entorn']=int(ee.sum()); q['V74_menys_V71_marca_mediana']=round(float(np.median((L74-L71)[mm])),2); q['V74_menys_V71_marca_p99abs']=round(float(np.percentile(np.abs(L74-L71)[mm],99)),2)
    res[k]=q; print(k,json.dumps(q))
# on són els píxels més foscos (dmed21 > 5) de tot l'anell 457–500? components i posició
v=maps['dmed21']; sel=(v>5)&F.anell(457,500); lab,n=ndi.label(sel); comps=[]
for i in range(1,n+1):
    cc=lab==i; comps.append(dict(n=int(cc.sum()),r=[round(float(F.RR[cc].min()),1),round(float(F.RR[cc].max()),1)],az=[round(float(F.AZ[cc].min()),1),round(float(F.AZ[cc].max()),1)],max=round(float(v[cc].max()),1)))
comps.sort(key=lambda q:-q['n']); res['components_dmed21_gt5_r457_500']=dict(n=n,top=comps[:15]); print('components dmed21>5 a 457–500:',n); [print(q) for q in comps[:15]]
F.dump('fd1b_negres_rec',res); print('fd1b fet')
