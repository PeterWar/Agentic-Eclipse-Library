"""fb1: la taca m6 capa a capa (atribució), perfils radials per sector de 5° i mapes polars (capa 30 V69/V74, LROC, RAW, factor V71)."""
import sys, json, numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image
S4='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
sys.path.insert(0,S4); import compo74 as c
CX,CY,RS=998.88,998.41,456.0
Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY); az=(np.degrees(np.arctan2(-(Y-CY),X-CX)))%360
M=np.load(S4+'/marques74_masks.npz'); m6=M['m6']; e6=M['ent_m6']
def lum(rgb): return rgb.mean(-1)
def ratio(L,m,e): return float(np.log(np.median(L[m])/np.median(L[e]))), float(np.log(L[m].mean()/L[e].mean()))
out={}
# 1) atribució capa a capa al compost V74 (sense la 222)
C,a,passos=c.recompon(exclou=(222,),retorna_passos=True)
seq=[l['id'] for l in c.IDX['layers'] if l['visible'] and l['id']!=222]
out['atribucio_compost']=[]
for lid in seq:
    Cb,ab=passos[lid]; L=lum(Cb); r_med,r_mean=ratio(L,m6,e6)
    out['atribucio_compost'].append(dict(id=lid,nom=c.LAYERS[lid]['name'][:32],ln_dins_entorn_mediana=round(r_med,4),ln_dins_entorn_mitjana=round(r_mean,4)))
    print(lid,c.LAYERS[lid]['name'][:32],'ln(dins/entorn) med %.4f mean %.4f'%(r_med,r_mean))
# 2) capes soles
rgb30,a30=c.carrega(30); L74=lum(rgb30)
d69=np.load(OLD+'/roi_L30.npz'); L69=np.dstack([d69['c0'],d69['c1'],d69['c2']]).astype(np.float32).mean(-1)/65535
rgb62,a62=c.carrega(62); L62=lum(rgb62); v62=np.load(S4+'/roi74p_L62.npz')['c-1']>30000
RAW=np.load(OLD+'/raw_disc_norm_2000.npy').astype(np.float64); vraw=np.isfinite(RAW)
FV71=np.load(OLD+'/vel_corr_final.npy').astype(np.float64)
for nom,L,v in (('capa30_V69',L69,None),('capa30_V74',L74,None),('LROC_62',L62,v62),('RAW_disc_norm',RAW,vraw),('factor_V71',FV71,None)):
    mm=m6 if v is None else m6&v; ee=e6 if v is None else e6&v
    out['taca_'+nom]=dict(ln_med=round(float(np.log(np.median(L[mm])/np.median(L[ee]))),4),ln_mean=round(float(np.log(L[mm].mean()/L[ee].mean())),4),n_dins=int(mm.sum()),n_entorn=int(ee.sum()))
    print(nom,out['taca_'+nom])
# 3) perfils per sector de 5° (mediana en bins de 2 px, r 100–440) en ln, relatius a la mediana azimutal de cada anell
rb=np.arange(100,442,2); rc=rb[:-1]+1; NS=72; sec=(az//5).astype(int)
def perfils(L,v=None):
    P=np.full((NS,len(rc)),np.nan); ib=((rr-100)//2).astype(int); ok=(rr>=100)&(rr<440)&(L>0)
    if v is not None: ok&=v
    lab=sec[ok]*len(rc)+ib[ok]; vals=np.log(L[ok])
    from scipy.ndimage import median as ndmed
    cnt=np.bincount(lab,minlength=NS*len(rc)); med=ndmed(vals,labels=lab,index=np.arange(NS*len(rc)))
    P=np.where(cnt>=6,med,np.nan).reshape(NS,len(rc)); return P
PR={}
for nom,L,v in (('capa30_V69',L69,None),('capa30_V74',L74,None),('LROC_62',L62,v62),('RAW_disc_norm',RAW,vraw),('factor_V71',FV71,None)):
    P=perfils(L,v); PR[nom]=P
np.savez_compressed(S4+'/fb1_perfils.npz',rc=rc,**PR)
# quocients: taca (az 240–270 → sectors 48–53) contra veïns (210–240: 42–47; 270–300: 54–59)
T=list(range(48,54)); V1=list(range(42,48)); V2=list(range(54,60))
res={}
for nom,P in PR.items():
    t=np.nanmedian(P[T],0); v=np.nanmedian(P[V1+V2],0); v1=np.nanmedian(P[V1],0); v2=np.nanmedian(P[V2],0)
    q=t-v; res[nom]=dict(r=[int(x) for x in rc[::10]],ln_taca_menys_veins=[None if not np.isfinite(x) else round(float(x),4) for x in q[::10]],ln_taca_menys_v210_240=[None if not np.isfinite(x) else round(float(x),4) for x in (t-v1)[::10]],ln_taca_menys_v270_300=[None if not np.isfinite(x) else round(float(x),4) for x in (t-v2)[::10]])
    print(nom,'ln(taca/veïns) r=',rc[::20].tolist()); print('   ',np.round(q[::20],3).tolist())
out['quocients_sector']=res
# desviació de cada sector respecte a la mediana azimutal (mapa polar) per a la vista
def polar_png(P,nom,scale):
    D=P-np.nanmedian(P,0)[None,:]; D=np.nan_to_num(D); im=np.clip(0.5+D/(2*scale),0,1)
    im=np.kron(im,np.ones((6,2))); return im
tiles=[]
for nom,scale in (('capa30_V69',0.10),('capa30_V74',0.10),('LROC_62',0.30),('RAW_disc_norm',0.10),('factor_V71',0.10)):
    tiles.append(polar_png(PR[nom],nom,scale))
pan=np.concatenate(tiles,0); Image.fromarray(np.uint8(pan*255)).save(S4+'/v_fb1_polar_sectors.png')
json.dump(out,open(S4+'/fb1_perfils.json','w'),indent=1,ensure_ascii=False); print('fet')
