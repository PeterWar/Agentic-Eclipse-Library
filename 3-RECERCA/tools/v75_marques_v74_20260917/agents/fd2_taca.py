"""fd2: refutació de les afirmacions del lector B (taca m6) i mesura pròpia de la candidata roi75_L30_candidata.npz."""
import numpy as np, json
from scipy.ndimage import gaussian_filter, median_filter
import fd_lib as F
c74=F.compo74()
C74,a74,P=c74.recompon(exclou=(222,),retorna_passos=True)
ordre=[l['id'] for l in c74.IDX['layers'] if l['visible'] and l['id']!=222]
m6=F.mask('m6'); e6=F.mask('ent_m6'); disc=F.RR<430
res={}
def lnr(A,mk=None):
    a=m6 if mk is None else m6&mk; b=e6 if mk is None else e6&mk
    return round(float(np.log(np.median(A[a])/np.median(A[b]))),4)
def s6(A,msk=disc):
    mm=msk.astype(float); return gaussian_filter(np.nan_to_num(A)*mm,6)/np.maximum(gaussian_filter(mm,6),1e-9)
def anells(A,msk=disc,rings=np.arange(170,412,4)):
    a=s6(A,msk); vals=[]
    for r0 in rings:
        ring=F.anell(r0,r0+4); md=m6&ring&msk; ed=e6&ring&msk
        if md.sum()<20 or ed.sum()<20: continue
        vals.append(np.log(np.median(a[md])/np.median(a[ed])))
    v=np.array(vals); n=len(v); return round(float(np.median(v)),4),[round(float(np.median(v[:n//3])),4),round(float(np.median(v[n//3:2*n//3])),4),round(float(np.median(v[2*n//3:])),4)]
# ---- 1) atribució capa a capa (L* i canal G del compost) — la taca és a la 30?
att={}
for lid in ordre:
    L=F.Lstar(P[lid][0]); G=P[lid][0][...,1]
    att[lid]=dict(nom=c74.LAYERS[lid]['name'][:22],dL=round(float(np.median(L[m6])-np.median(L[e6])),2),lnG=lnr(np.maximum(G,1e-4)),lnG_anells=anells(np.maximum(G,1e-4))[0])
    print('%4d %-22s dL %+5.2f  lnG %+.4f  anells %+.4f'%(lid,att[lid]['nom'],att[lid]['dL'],att[lid]['lnG'],att[lid]['lnG_anells']))
res['atribucio']=att
# ---- 2) la taca al RAW (disc normalitzat per anells) i a la LROC
raw=np.load(F.OLD+'/raw_disc_norm_2000.npy').astype(np.float64); vraw=np.isfinite(raw)&(raw>0)
res['raw_norm']=dict(shape=list(raw.shape),mediana_disc=float(np.nanmedian(raw[disc])),ln_masc=lnr(np.where(vraw,raw,np.nan)) if vraw[m6].all() and vraw[e6].all() else None)
rawf=np.where(vraw,raw,np.nanmedian(raw[disc&vraw]))
res['raw_norm']['anells']=anells(rawf,disc&vraw); res['raw_norm']['ln_masc_s6']=lnr(s6(rawf,disc&vraw))
L62d=np.load(F.S4+'/roi74p_L62.npz'); L62=np.dstack([L62d['c0'],L62d['c1'],L62d['c2']]).astype(np.float64).mean(-1); v62=L62d['c-1']>30000
res['lroc']=dict(anells=anells(np.maximum(L62,1),v62&disc),ln_masc=lnr(np.maximum(L62,1)))
print('RAW norm: masc %s, s6 masc %s, anells %s'%(res['raw_norm']['ln_masc'],res['raw_norm']['ln_masc_s6'],res['raw_norm']['anells']))
print('LROC: masc %s anells %s'%(res['lroc']['ln_masc'],res['lroc']['anells']))
# fotograma a fotograma? no disponible aquí; contrast RAW per terços i per meitats azimutals de la marca (robustesa)
half_a=F.AZ<255; half_b=~half_a
res['raw_norm']['anells_meitat_az_lt255']=anells(rawf,disc&vraw&half_a); res['raw_norm']['anells_meitat_az_ge255']=anells(rawf,disc&vraw&half_b)
# ---- 3) capa 30 V74 vs V69 (OLD roi_L30): factor?
d74=np.load(F.S4+'/roi74p_L30.npz'); d69=np.load(F.OLD+'/roi_L30.npz'); F71=np.load(F.OLD+'/vel_corr_final.npy').astype(np.float64)
G74=d74['c1'].astype(np.float64); G69=d69['c1'].astype(np.float64)
pred=np.clip(np.rint(G69*F71),0,65535); dd=(G74-pred)[disc&(G69>0)]
res['capa74_vs_capa69xF71']=dict(mediana=float(np.median(dd)),p99abs=float(np.percentile(np.abs(dd),99)),max=float(np.abs(dd).max()))
print('capa74 − capa69·F71:',res['capa74_vs_capa69xF71'])
# ---- 4) candidata
cd=np.load(F.S4+'/roi75_L30_candidata.npz'); Gc=cd['c1'].astype(np.float64)
res['candidata_fitxer']=dict(claus=cd.files,alfa_igual=bool((cd['c-1']==d74['c-1']).all()),masc_igual=bool((cd['c-2']==d74['c-2']).all()),
    canvis_r_gt_440=int(((cd['c0']!=d74['c0'])|(cd['c1']!=d74['c1'])|(cd['c2']!=d74['c2']))[F.RR>440].sum()),canvis_r_le_440=int((cd['c1']!=d74['c1'])[F.RR<=440].sum()))
fac={k:cd[k].astype(np.float64)/np.maximum(d74[k].astype(np.float64),1) for k in ('c0','c1','c2')}
mm=disc&(d74['c1']>500)
res['candidata_fitxer']['factor_canals_iguals_p99abs']=float(np.percentile(np.abs(fac['c0']-fac['c1'])[mm],99))
res['candidata_fitxer']['factor_p1_p50_p99']=[float(np.percentile(fac['c1'][mm],q)) for q in (1,50,99)]
res['candidata_fitxer']['factor_min_max']=[float(fac['c1'][mm].min()),float(fac['c1'][mm].max())]
print('candidata fitxer:',res['candidata_fitxer'])
# mètriques: taca (aparellada i amb màscares), abans/després
res['taca']=dict(capa74=dict(anells=anells(G74),masc=lnr(G74),masc_s6=lnr(s6(G74))),candidata=dict(anells=anells(Gc),masc=lnr(Gc),masc_s6=lnr(s6(Gc))))
print('taca capa74:',res['taca']['capa74']); print('taca candidata:',res['taca']['candidata'])
# canvi de gran escala σ60 (ln), fora i dins la taca
lnA=np.log(np.maximum(G74,1)); lnB=np.log(np.maximum(Gc,1)); dl=lnB-lnA
d60=(gaussian_filter(dl*disc,60))/np.maximum(gaussian_filter(disc.astype(float),60),1e-9)
fora=disc&~m6&~e6&(F.RR>60); res['s60']=dict(max_fora=float(np.abs(d60[fora]).max()),rms_fora=float(np.sqrt(np.mean(d60[fora]**2))),mediana_taca=float(np.median(d60[m6])),mediana_entorn=float(np.median(d60[e6])))
# per sectors de 10°: mediana de dl
sec=(F.AZ//10).astype(int); ps={int(s):round(float(np.median(dl[(sec==s)&(F.RR>100)&(F.RR<430)])),4) for s in range(36)}; res['dl_mediana_sector10']=ps
print('σ60:',res['s60']); print('Δln per sector 10°:',ps)
# correlació de la banda 12–60 amb la LROC, sectors parells/senars (10°) i (20°)
def band(a,lo,hi,msk):
    mmk=msk.astype(float); return (gaussian_filter(a*mmk,lo)/np.maximum(gaussian_filter(mmk,lo),1e-9))-(gaussian_filter(a*mmk,hi)/np.maximum(gaussian_filter(mmk,hi),1e-9))
vv=v62&disc&(F.RR>60); LR=np.log(np.maximum(L62,1)); bl=band(LR,12,60,vv)
cl={}
for w in (10,20):
    par=((F.AZ//w).astype(int)%2==0)
    for nom,A in (('capa74',lnA),('candidata',lnB)):
        bb=band(A,12,60,vv); cl[f'{nom}_w{w}']=dict(parells=round(float(np.corrcoef(bb[vv&par],bl[vv&par])[0,1]),3),senars=round(float(np.corrcoef(bb[vv&~par],bl[vv&~par])[0,1]),3),taca=round(float(np.corrcoef(bb[vv&(m6|e6)],bl[vv&(m6|e6)])[0,1]),3))
res['corr_lroc_12_60']=cl; print('corr LROC banda 12–60:',cl)
# el FACTOR de la candidata: correlació amb la LROC (és font?) i estructura per escales
bf=band(np.log(np.maximum(fac['c1'],1e-3)),12,60,vv)
res['factor_vs_lroc']=dict(corr_banda_12_60=round(float(np.corrcoef(bf[vv],bl[vv])[0,1]),3),corr_banda_12_60_taca=round(float(np.corrcoef(bf[vv&(m6|e6)],bl[vv&(m6|e6)])[0,1]),3))
esc={}
for lo,hi in ((3,8),(8,32),(32,120)):
    b0=band(lnA,lo,hi,disc); b1=band(lnB,lo,hi,disc); bfac=band(np.log(np.maximum(fac['c1'],1e-3)),lo,hi,disc); mk=disc&(F.RR<400)&(F.RR>60)
    esc[f'{lo}-{hi}']=dict(corr=round(float(np.corrcoef(b0[mk],b1[mk])[0,1]),4),amplitud=round(float(b1[mk].std()/b0[mk].std()),4),std_factor=round(float(bfac[mk].std()),4),std_capa74=round(float(b0[mk].std()),4))
res['retencio_escales']=esc; print('factor vs LROC:',res['factor_vs_lroc']); print('escales:',esc)
# el factor: de què depèn? correlació amb el RAW normalitzat (σ15) i amb la capa mateixa
rs=s6(rawf,disc&vraw); rs15=gaussian_filter(np.nan_to_num(np.where(vraw,raw-1,0))*disc,15)/np.maximum(gaussian_filter(disc.astype(float),15),1e-9)
mk=disc&(F.RR<400)&(F.RR>60)
res['factor_correlacions']=dict(amb_raw_s15=round(float(np.corrcoef(np.log(fac['c1'][mk]),rs15[mk])[0,1]),3),amb_ln_capa74_band12_60=round(float(np.corrcoef(bf[mk&vv],band(lnA,12,60,vv)[mk&vv])[0,1]),3))
print('factor correlacions:',res['factor_correlacions'])
F.dump('fd2_taca',res)
# vistes: taca capa74 / candidata / LROC / factor (mateix to), 1:1 i 2x
lo,hi=6300,10300; st=lambda A,l,h: np.clip((A-l)/(h-l),0,1)
sl=(slice(1157-230,1157+230),slice(828-230,828+230))
lroc=st(L62,np.percentile(L62[v62&disc],1),np.percentile(L62[v62&disc],99.5))*(v62&disc)
F.fila([F.retall(st(G74,lo,hi),*(sl[0].start,sl[0].stop,sl[1].start,sl[1].stop),Z=1),F.retall(st(Gc,lo,hi),sl[0].start,sl[0].stop,sl[1].start,sl[1].stop,Z=1),F.retall(lroc,sl[0].start,sl[0].stop,sl[1].start,sl[1].stop,Z=1),F.retall(np.clip(0.5+np.log(fac['c1'])/0.4,0,1)*disc,sl[0].start,sl[0].stop,sl[1].start,sl[1].stop,Z=1)],['capa 30 V74 (G)','candidata (G)','LROC (jutge)','ln factor ±0,2']).save(F.S4+'/v_fd_taca_capa74_candidata_lroc_factor.png')
sl=(slice(520,1480),slice(520,1480)); p2=np.percentile(G74[disc],2); p995=np.percentile(G74[disc],99.5)
F.fila([F.retall(st(G74,p2,p995)*disc,520,1480,520,1480,Z=1),F.retall(st(Gc,p2,p995)*disc,520,1480,520,1480,Z=1),F.retall(np.clip(0.5+dl/0.2,0,1)*disc,520,1480,520,1480,Z=1)],['capa 30 V74','candidata','Δln ±0,1']).save(F.S4+'/v_fd_lluna_capa74_candidata_dln.png')
print('fd2 fet')
