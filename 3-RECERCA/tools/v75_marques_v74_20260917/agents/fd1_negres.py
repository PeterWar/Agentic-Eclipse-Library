"""fd1: refutació de les afirmacions del lector A (punts negres, V74≡V71 a r≥459, bandes reals, solc W) amb mesures pròpies,
i contrast amb la nota del lector C (màscara 30 fora de la silueta a az 165–207)."""
import numpy as np, json
from scipy import ndimage as ndi
import fd_lib as F
c74=F.compo74(); c71=F.compo71()
C74,a74,P=c74.recompon(exclou=(222,),retorna_passos=True)
C71,a71=c71.recompon(exclou=(218,219,220))
ordre=[l['id'] for l in c74.IDX['layers'] if l['visible'] and l['id']!=222]
L74=F.Lstar(C74); L71=F.Lstar(C71); Lps=F.Lstar(F.compost_ps())
res={}
# ---- 1) V74 vs V71 per anells i sectors
d=L74-L71; rows={}
for r0,r1 in ((440,451),(451,456),(456,459),(459,470),(470,500)):
    rows[f'{r0}-{r1}']={}
    for s0 in range(0,360,30):
        m=F.anell(r0,r1)&F.sector(s0,s0+30); rows[f'{r0}-{r1}'][s0]=[round(float(np.median(d[m])),2),round(float(np.percentile(np.abs(d[m]),99)),2)]
res['v74_menys_v71_L_mediana_p99abs']=rows
print('V74−V71 L* (mediana, p99|d|) per anell × sector de 30°'); [print(k,v) for k,v in rows.items()]
# recomposició vs compost Photoshop
dps=L74-Lps; m=F.anell(440,520); res['recomp_vs_ps_L']=dict(mediana=float(np.median(dps[m])),p99abs=float(np.percentile(np.abs(dps[m]),99)),max=float(np.abs(dps[m]).max()))
print('recomp − PS (L*, r 440–520):',res['recomp_vs_ps_L'])
# ---- 2) punts negres compactes: black-hat 5 i 11 px, L−mediana(21), sobre la recomposició i sobre el compost de Photoshop
def blackhat(L,k):
    se=np.zeros((k,k),bool); yy,xx=np.mgrid[:k,:k]; se[(yy-k//2)**2+(xx-k//2)**2<=(k//2)**2]=True
    return ndi.grey_closing(L,footprint=se)-L
bh5=blackhat(Lps,5); bh11=blackhat(Lps,11); dm21=Lps-ndi.median_filter(Lps,21); dm9=Lps-ndi.median_filter(Lps,9)
bh5r=blackhat(L74,5); dm21r=L74-ndi.median_filter(L74,21)
pts={}
for k in ('m2','m3','m4','m5','m7'):
    mm=F.mask(k); ee=F.mask('ent_'+k); q={}
    for nom,A,sg in (('bh5_ps',bh5,1),('bh11_ps',bh11,1),('dmed9_ps',dm9,-1),('dmed21_ps',dm21,-1),('bh5_rec',bh5r,1),('dmed21_rec',dm21r,-1)):
        v=A*sg  # positiu = fosc
        q[nom]=dict(marca_max=round(float(v[mm].max()),2),marca_p99=round(float(np.percentile(v[mm],99)),2),entorn_max=round(float(v[ee].max()),2),entorn_p99=round(float(np.percentile(v[ee],99)),2),
                    marca_n_gt3=int((v[mm]>3).sum()),marca_n_gt5=int((v[mm]>5).sum()),entorn_n_gt3=int((v[ee]>3).sum()),entorn_n_gt5=int((v[ee]>5).sum()),n_marca=int(mm.sum()),n_entorn=int(ee.sum()))
    # marca − entorn aparellat pel radi (anells de 2 px)
    dif=[]
    for r0 in np.arange(np.floor(F.RR[mm].min()),F.RR[mm].max(),2):
        a=mm&F.anell(r0,r0+2); b=ee&F.anell(r0,r0+2)
        if a.sum()>=3 and b.sum()>=3: dif.append(float(np.median(Lps[a])-np.median(Lps[b])))
    q['marca_menys_entorn_aparellat_L']=round(float(np.mean(dif)),2) if dif else None
    q['L_marca']=round(float(Lps[mm].mean()),1); q['L_entorn']=round(float(Lps[ee].mean()),1)
    # L* mínim absolut a la marca i entorn (percentil 1) i valor de gra: std de dm9
    q['L_p1_marca']=round(float(np.percentile(Lps[mm],1)),1); q['L_p1_entorn']=round(float(np.percentile(Lps[ee],1)),1)
    q['gra_std_dmed9_marca']=round(float(dm9[mm].std()),2); q['gra_std_dmed9_entorn']=round(float(dm9[ee].std()),2)
    pts[k]=q; print(k,json.dumps(q))
res['punts_negres']=pts
# ---- 3) bandes azimutals: fondària pròpia amb mediana azimutal (±8°) en comptes de gaussiana; per capa; i a l'HDR lineal Vixen
H=np.load(F.OLD+'/corona_hdr_3000.npy'); V=np.load(F.OLD+'/corona_valid_3000.npy')
Hroi=H[502:2502,501:2501].astype(np.float64); Vroi=V[502:2502,501:2501]&(Hroi>0)
azc=np.floor(F.AZ*2)/2
def perfil(A,band,cells,valid=None):
    out=[]
    for cc in cells:
        m=band&(azc==cc)
        if valid is not None: m&=valid
        out.append(float(np.median(A[m])) if m.sum()>0 else np.nan)
    return np.array(out)
def fond(p,cells,azc_,half):
    ref=ndi.median_filter(np.nan_to_num(p,nan=np.nanmedian(p)),size=33,mode='nearest')  # ±8° de mediana
    inm=(cells>=azc_-half)&(cells<=azc_+half); return float(np.nanmin((p-ref)[inm])), float(np.nanmean(p[inm])), float(np.nanmean(ref[inm]))
bandes={}
for nom,(azc_,r0,r1,w) in {'m2_az109':(109.0,465,471,1.0),'m3_az117':(117.0,470,474,1.0),'m4_az153':(153.5,476,480,1.5),'m5_az167':(167.0,474,481,1.5),'m7_az234':(234.0,459,470,3.0)}.items():
    band=F.anell(r0,r1+1); cells=np.arange(azc_-30,azc_+30,0.5)%360
    cells=np.arange(np.floor((azc_-30)*2)/2,azc_+30,0.5)
    per={}
    for lid in ordre:
        f,pm,pr=fond(perfil(F.Lstar(P[lid][0]),band,cells),cells,azc_,w); per[lid]=[round(f,2),round(pm,1)]
    pl=perfil(np.log(np.maximum(Hroi,1e-6)),band,cells,Vroi); fl,_,_=fond(pl,cells,azc_,w)
    bandes[nom]=dict(r=[r0,r1],per_capa=per,final_L=per[ordre[-1]],lineal_vixen_pct=round((np.exp(fl)-1)*100,1),n_valid_lineal=int(np.isfinite(pl).sum()))
    print(nom,'final dev %+.2f (L %.1f); lineal Vixen %+.1f %%'%(per[ordre[-1]][0],per[ordre[-1]][1],bandes[nom]['lineal_vixen_pct']),' per capa:',{k:v[0] for k,v in per.items()})
res['bandes']=bandes
# ---- 4) sector W (az 140–210) al limbe: atribució capa a capa a l'anell 457–467, amb la capa 30 inclosa; alfa efectiva de 30/76/96/204/206
azb=np.floor(F.AZ/3)*3; ring_in=F.anell(457,467); ring_out=F.anell(470,485)
W={}
for A0 in range(138,213,3):
    s=(azb==A0); q={}
    for lid in (56,30,76,96,204,206,202):
        L=F.Lstar(P[lid][0]); q['L_in_despres_%d'%lid]=round(float(np.median(L[s&ring_in])),1); q['L_out_despres_%d'%lid]=round(float(np.median(L[s&ring_out])),1)
    for lid in (30,76,96,204,206):
        rgb,al=c74.carrega(lid); q['alfa_in_%d'%lid]=round(float(al[s&ring_in].mean()),3); q['alfa_max_in_%d'%lid]=round(float(al[s&ring_in].max()),3); q['alfa_out_%d'%lid]=round(float(al[s&ring_out].mean()),3)
        if lid in (30,76,96): q['Lcapa_in_%d'%lid]=round(float(F.Lstar(rgb)[s&ring_in].mean()),1)
    # radi on l'alfa efectiva de la 30 cau al 50 % (perfil radial 1 px)
    rgb,al=c74.carrega(30); rb=np.arange(440,475); pa=np.array([float(al[s&F.anell(r,r+1)].mean()) if (s&F.anell(r,r+1)).any() else np.nan for r in rb])
    r50=None
    for i in range(len(pa)-1):
        if pa[i]>=0.5>pa[i+1]: r50=float(rb[i]+(pa[i]-0.5)/(pa[i]-pa[i+1])); break
    q['r50_alfa30']=round(r50,1) if r50 else None; q['alfa30_r457_460']=round(float(al[s&F.anell(457,460)].mean()),3); q['alfa30_r460_465']=round(float(al[s&F.anell(460,465)].mean()),3)
    W[A0]=q
print('sector W: az | L_in després de 56/30/76/96/final | alfa30 in, r50 alfa30, alfa30 457-460 | alfa76 in | alfa96 in')
for A0,q in W.items(): print('%3d | %5.1f %5.1f %5.1f %5.1f %5.1f | %.2f %s %.2f | %.2f | %.2f'%(A0,q['L_in_despres_56'],q['L_in_despres_30'],q['L_in_despres_76'],q['L_in_despres_96'],q['L_in_despres_202'],q['alfa_in_30'],q['r50_alfa30'],q['alfa30_r457_460'],q['alfa_in_76'],q['alfa_in_96']))
res['sector_W_limbe']=W
# perfil radial fi (1 px) a az 165–172 i 195–205 per capa
prof={}
for nomS,(a0,a1) in {'az165_172':(165,172),'az150_156':(150,156),'az195_205':(195,205)}.items():
    s=F.sector(a0,a1); rb=np.arange(450,480); pr={'r':rb.tolist()}
    for lid in (56,30,76,96,204,206,202): pr['despres_%d'%lid]=[round(float(np.median(F.Lstar(P[lid][0])[s&F.anell(r,r+1)])),1) for r in rb]
    for lid in (30,76,96): rgb,al=c74.carrega(lid); pr['alfa_%d'%lid]=[round(float(al[s&F.anell(r,r+1)].mean()),2) for r in rb]; pr['Lcapa_%d'%lid]=[round(float(F.Lstar(rgb)[s&F.anell(r,r+1)].mean()),1) for r in rb]
    pr['V71']=[round(float(np.median(L71[s&F.anell(r,r+1)])),1) for r in rb]
    prof[nomS]=pr; print('--',nomS); [print('%-12s'%k,' '.join('%5s'%v for v in pr[k])) for k in pr]
res['perfils_W']=prof
F.dump('fd1_negres',res)
# ---- vistes: sector W az 140–185, r 440–500 al 300 %: després de 56, després de 30, després de 76, després de 96, final V74, V71
y0,y1,x0,x1=760,1060,470,640
ims=[F.retall(P[56][0],y0,y1,x0,x1),F.retall(P[30][0],y0,y1,x0,x1),F.retall(P[76][0],y0,y1,x0,x1),F.retall(P[96][0],y0,y1,x0,x1),F.retall(C74,y0,y1,x0,x1),F.retall(C71,y0,y1,x0,x1)]
F.fila(ims,['després 56 (filtres)','després 30 (earthshine)','després 76','després 96','final V74','V71']).save(F.S4+'/v_fd_W_passos_x3.png')
# N: az 100–130 (m2,m3)
y0,y1,x0,x1=520,640,760,960
F.fila([F.retall(P[56][0],y0,y1,x0,x1),F.retall(P[30][0],y0,y1,x0,x1),F.retall(C74,y0,y1,x0,x1),F.retall(F.compost_ps(),y0,y1,x0,x1),F.retall(C71,y0,y1,x0,x1)],['després 56','després 30','final V74 (recomp)','V74 Photoshop','V71']).save(F.S4+'/v_fd_N_passos_x3.png')
# mapa de bh5 (punts foscos) al sector N i W sobre el compost PS
for nom,(y0,y1,x0,x1) in {'N':(520,640,760,960),'W':(760,1060,470,640),'SW':(1260,1460,560,860)}.items():
    F.fila([F.retall(F.compost_ps(),y0,y1,x0,x1),F.retall(bh5,y0,y1,x0,x1,lo=0,hi=6),F.retall(-dm21,y0,y1,x0,x1,lo=0,hi=8)],['V74 PS','black-hat 5 px (0–6 L*)','−(L−med21) (0–8 L*)']).save(F.S4+f'/v_fd_foscos_{nom}_x3.png')
print('fd1 fet')
