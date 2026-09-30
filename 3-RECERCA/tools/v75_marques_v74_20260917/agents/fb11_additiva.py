"""fb11: correcció ADDITIVA a través de la corba (D = f(RAW_s) − f(RAW_s − v), camp suau, textura de Pere intacta). Variants, criteris (d), candidata i vistes."""
import sys, json, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad')
from fb6_candidata import *
from scipy.ndimage import gaussian_filter
V=np.load(S4+'/fb6b_variants.npz'); Vlin=V['Vlin']; c0=float(V['c0'])
disc=rr<430; kap=kappa()
def pipeline(RAWs_,P_,variant='A'):
    f,finv,xc,yi=ajusta_f(RAWs_,P_); Vdev,ringmed,Vl=vel_lineal(RAWs_)
    v={'A':Vdev,'B':Vl-float(np.median(Vl[(rr<256)&(rr>100)])),'Bp':Vl-ringmed}[variant]
    D=gaussian_filter(f(RAWs_)-f(RAWs_-v),6)   # camp suau en unitats de P
    return D,f
F71=np.load(OLD+'/vel_corr_final.npy').astype(np.float64)
DA,f=pipeline(RAWs,P,'A'); DB,_=pipeline(RAWs,P,'B'); DBp,_=pipeline(RAWs,P,'Bp')
candA=(G69+kap*(Wdq-DA))            # S8 substituït (radial/sector, terra per sector)
candA74=candA*F71                    # + F71 tal qual (estat acceptat)
candB=(G69+kap*(Wdq-DB))             # S8 substituït pel vel complet (radial+azimutal, terra global), sense F71
candBp=(G69-kap*DBp)                 # S8 conservat, F71 substituït per l'azimutal additiu
np.savez_compressed(S4+'/fb11_variants.npz',DA=DA.astype(np.float32),DB=DB.astype(np.float32),DBp=DBp.astype(np.float32),candA74=candA74.astype(np.float32),candB=candB.astype(np.float32),candBp=candBp.astype(np.float32))
# --- mètriques
rings=np.arange(170,412,4)
def s6(A): m=disc.astype(float); return gaussian_filter(np.nan_to_num(A)*m,6)/np.maximum(gaussian_filter(m,6),1e-9)
def c_anells(A,mk=None):
    a=s6(A); vals=[]
    for r0 in rings:
        ring=(rr>=r0)&(rr<r0+4); md=m6&ring; ed=e6&ring
        if mk is not None: md&=mk; ed&=mk
        if md.sum()<20 or ed.sum()<20: continue
        vals.append(np.log(np.median(a[md])/np.median(a[ed])))
    v=np.array(vals); n=len(v); return round(float(np.median(v)),4),[round(float(np.median(v[:n//3])),4),round(float(np.median(v[n//3:2*n//3])),4),round(float(np.median(v[2*n//3:])),4)]
lnr=lambda A: round(float(np.log(np.median(A[m6])/np.median(A[e6]))),4)
LR=np.log(np.maximum(L62,1)); vv=v62&disc&(rr>60)
def band(a,lo,hi,mask):
    m=mask.astype(float); return (gaussian_filter(a*m,lo)/np.maximum(gaussian_filter(m,lo),1e-9))-(gaussian_filter(a*m,hi)/np.maximum(gaussian_filter(m,hi),1e-9))
bl=band(LR,12,60,vv); par=((az//10).astype(int)%2==0)
# pendent d'albedo de la capa respecte a LROC (banda 12–60) → objectiu de contrast de la taca
ba74=band(np.log(np.maximum(G74,1)),12,60,vv); s_alb=float(np.cov(ba74[vv],bl[vv],bias=True)[0,1]/np.var(bl[vv])); c_lroc=c_anells(L62,v62)
print('pendent d\'albedo capa74/LROC (banda 12–60): %.3f ; LROC contrast aparellat %.4f → objectiu a la capa ≈ %.4f'%(s_alb,c_lroc[0],s_alb*c_lroc[0]))
out=dict(pendent_albedo=s_alb,contrast_LROC=c_lroc,objectiu_capa=s_alb*c_lroc[0],variants={})
lnA=np.log(np.maximum(G74,1))
for nom,c in (('capa69',G69),('capa74',G74),('A_add·F71 (S8→corba, F71 igual)',candA74),('A_add sense F71',candA),('B_add (vel complet, sense F71)',candB),('B_add·F71',candB*F71),('Bp_add (S8 + azimutal per corba)',candBp)):
    lnB=np.log(np.maximum(c,1)); d60=(gaussian_filter(lnB*disc,60)-gaussian_filter(lnA*disc,60))/np.maximum(gaussian_filter(disc.astype(float),60),1e-9)
    fac=c/np.maximum(G74,1); fr=fac[(rr<440)&(rr>60)]; dl=lnB-lnA; ps=[float(np.median(dl[(sec5==s)&(rr>100)&(rr<430)])) for s in range(72)]
    ret={}
    for lo,hi in ((3,8),(8,32)):
        b0=band(lnA,lo,hi,disc); b1=band(lnB,lo,hi,disc); m=disc&(rr<400)&(rr>60); ret[f'{lo}-{hi}']=[round(float(np.corrcoef(b0[m],b1[m])[0,1]),4),round(float(b1[m].std()/b0[m].std()),4)]
    bb=band(lnB,12,60,vv); cl=dict(parells=round(float(np.corrcoef(bb[vv&par],bl[vv&par])[0,1]),3),senars=round(float(np.corrcoef(bb[vv&~par],bl[vv&~par])[0,1]),3),taca=round(float(np.corrcoef(bb[vv&(m6|e6)],bl[vv&(m6|e6)])[0,1]),3))
    row=dict(taca_anells=c_anells(c),taca_masc_pere=lnr(c),factor_p1_p99=[round(float(np.percentile(fr,1)),3),round(float(np.percentile(fr,99)),3)],s60_max_fora=round(float(np.abs(d60[disc&~m6&~e6&(rr>60)]).max()),4),s60_rms_fora=round(float(np.sqrt(np.mean(d60[disc&~m6&~e6&(rr>60)]**2))),4),s60_taca=round(float(np.median(d60[m6])),4),dsector_max_fora_210_300=round(max(abs(ps[s]) for s in range(72) if s<42 or s>=60),4),dsector_taca=[round(ps[s],3) for s in range(48,54)],retencio_corr_amplitud=ret,corr_LROC_12_60=cl)
    out['variants'][nom]=row; print(nom,json.dumps(row,ensure_ascii=False))
json.dump(out,open(S4+'/fb11_additiva.json','w'),indent=1,ensure_ascii=False)
# candidata: A_add·F71 → factor sobre la capa 30 de V74 (mateix factor als tres canals; alfa/màscara intactes; r>440 intacte)
fac=candA74/np.maximum(G74,1); fac[(G74<=0)|(rr>440)]=1.0; d74=np.load(S4+'/roi74p_L30.npz'); o={k:d74[k] for k in d74.files}
for key in ('c0','c1','c2'): o[key]=np.clip(np.rint(d74[key].astype(np.float64)*fac),0,65535).astype(np.uint16)
np.savez_compressed(S4+'/roi75_L30_candidata.npz',**o); np.save(S4+'/fb11_factor_A_add_F71.npy',fac.astype(np.float32))
chk=np.load(S4+'/roi75_L30_candidata.npz'); print('candidata escrita: claus',chk.files,'; c-1/c-2 idèntics:',bool((chk['c-1']==d74['c-1']).all() and (chk['c-2']==d74['c-2']).all()),'; canvis a r>440:',int((chk['c1']!=d74['c1'])[rr>440].sum()),'; factor min/max r<440: %.3f %.3f'%(fac[rr<440].min(),fac[rr<440].max()))
# vistes (mateix to abans/després): retall 700 ×1 [capa74 | candidata | LROC], ×2 de la marca, i Lluna sencera amb el terra restat (p2→negre)
from PIL import Image; from scipy.ndimage import zoom
st=lambda A,lo,hi: np.clip((A-lo)/(hi-lo),0,1)
y0,x0=1157-230,828-230; sl=(slice(y0,y0+700),slice(x0,x0+700)); lo,hi=6300,10300
lroc=st(L62,np.percentile(L62[v62&disc],1),np.percentile(L62[v62&disc],99.5))*(v62&disc)
Image.fromarray(np.uint8(np.concatenate([st(G74,lo,hi)[sl],st(candA74,lo,hi)[sl],lroc[sl]],1)*255)).save(S4+'/v_fb_taca_capa74_candidata_lroc_x1.png')
sl2=(slice(1157-170,1157+170),slice(828-170,828+170)); Image.fromarray(np.uint8(np.concatenate([zoom(st(G74,lo,hi)[sl2],2,order=1),zoom(st(candA74,lo,hi)[sl2],2,order=1)],1)*255)).save(S4+'/v_fb_taca_abans_despres_x2.png')
p2=np.percentile(G74[disc],2); p995=np.percentile(G74[disc],99.5); ims=[st(G74,p2,p995)*disc,st(candA74,p2,p995)*disc,st(candB,p2,p995)*disc,lroc]
Image.fromarray(np.uint8(np.concatenate([im[520:1480,520:1480] for im in ims],1)*255)).save(S4+'/v_fb_lluna_capa74_Aadd_Badd_lroc_p2negre.png')
# mapa de la correcció (ln) ×1 sencer: (candA74/capa74)
dl=np.log(np.maximum(candA74,1))-lnA; Image.fromarray(np.uint8(np.clip(0.5+dl/0.2,0,1)[520:1480,520:1480]*disc[520:1480,520:1480]*255)).save(S4+'/v_fb_mapa_correccio_Aadd_ln_pm0.1.png'); print('fet')
