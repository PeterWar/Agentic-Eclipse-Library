"""fb6b: què explica el model lineal complet; variants B (vel complet a través de la corba, substitueix S8+F71) i B′ (només la part azimutal a través de la corba, S8 intacte)."""
import sys, json, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad')
import fb6_candidata as B
from fb6_candidata import *
from scipy.ndimage import gaussian_filter, gaussian_filter1d, median as ndmed
lnr=lambda A: float(np.log(np.median(A[m6])/np.median(A[e6])))
f,finv,xc,yi=ajusta_f(RAWs,P); Vdev,ringmed,Vlin=vel_lineal(RAWs); kap=kappa(); disc=rr<430
c0=float(np.median(Vlin[(rr<256)&(rr>100)]))
out={}
# 1) què explica el model complet en lineal
resid=RAWs-Vlin+c0
out['lineal_ln_dins_entorn']=dict(RAW=lnr(RAWs),Vlin=lnr(Vlin),RAW_menys_Vlin=lnr(resid),ringmed_sol=lnr(ringmed),A_Gaz_dins=float(np.median(A_MODEL*Gaz[m6])),A_Gaz_entorn=float(np.median(A_MODEL*Gaz[e6])))
print('lineal ln(dins/entorn): RAW %.4f · Vlin (model) %.4f · RAW−Vlin %.4f · ringmed sol %.4f · A·Gaz dins %.4f entorn %.4f'%tuple(out['lineal_ln_dins_entorn'].values()))
# perfil sectorial del residu lineal (taca vs veïns) per veure si queda depressió
rb=np.arange(100,454,2); rc=rb[:-1]+1; NS=72
def perfils(Aa):
    ib=((rr-100)//2).astype(int); ok=(rr>=100)&(rr<452)&np.isfinite(Aa); lab=sec5[ok]*len(rc)+ib[ok]; cnt=np.bincount(lab,minlength=NS*len(rc)); med=ndmed(Aa[ok],labels=lab,index=np.arange(NS*len(rc)))
    return np.where(cnt>=6,med,np.nan).reshape(NS,len(rc))
T=list(range(48,54)); VV=list(range(42,48))+list(range(54,60)); g=lambda Aa,i: np.nanmedian(Aa[i],0)
PRr=perfils(resid); PRw=perfils(RAWs); PV=perfils(Vlin)
print(' r   ln RAW t/v | ln Vlin t/v | ln (RAW−Vlin) t/v'); rows=[]
for i in range(0,len(rc),20):
    rows.append(dict(r=int(rc[i]),RAW=round(float(np.log(g(PRw,T)[i]/g(PRw,VV)[i])),4),Vlin=round(float(np.log(g(PV,T)[i]/g(PV,VV)[i])),4),resid=round(float(np.log(g(PRr,T)[i]/g(PRr,VV)[i])),4))); print(f"{rows[-1]['r']:4d}  {rows[-1]['RAW']:+.4f} | {rows[-1]['Vlin']:+.4f} | {rows[-1]['resid']:+.4f}")
out['perfil_lineal_t_v']=rows
# 2) variants a través de la corba
lin=finv(P)
def blend(nou): return kap*nou+(1-kap)*G69
candA=blend(f(lin-Vdev))                                 # radial per sector (fb6)
candB=blend(f(lin-(Vlin-c0)))                            # vel complet (radial + azimutal), terra global
Vaz=Vlin-ringmed                                        # només la part azimutal del model (A·Gaz·ringmed)
candBp=blend(f(lin-Vaz))-0                               # B′: azimutal a través de la corba, S8 (W) restat com abans? no: aquí P−Vaz i després cal restar W_S8
candBp=blend(f(lin-Vaz)-Wdq)                             # B′ = (P amb l'azimutal tret a través de la corba) − W_S8 → substitueix F71, conserva S8
res={}
for nom,c in (('capa69',G69),('capa74 (=capa69·F71)',G74),('A radial/sector (fb6, sense refer F)',candA),('A·F71',candA*F71),('B vel complet',candB),('B·F71',candB*F71),('B′ azimutal+S8',candBp),('B′·F71',candBp*F71)):
    lnA=np.log(np.maximum(G74,1)); lnB=np.log(np.maximum(c,1)); d60=(gaussian_filter(lnB*disc,60)-gaussian_filter(lnA*disc,60))/np.maximum(gaussian_filter(disc.astype(float),60),1e-9)
    fac=c/np.maximum(G74,1); fr=fac[(rr<440)&(rr>100)]
    dl=lnB-lnA; ps=[float(np.median(dl[(sec5==s)&(rr>100)&(rr<430)])) for s in range(72)]
    res[nom]=dict(taca_ln=round(lnr(c),4),factor_vs_capa74_p1_p99=[round(float(np.percentile(fr,1)),3),round(float(np.percentile(fr,99)),3)],s60_max_fora=round(float(np.abs(d60[disc&~m6&~e6&(rr>60)]).max()),4),s60_rms_fora=round(float(np.sqrt(np.mean(d60[disc&~m6&~e6&(rr>60)]**2))),4),dsector_max_fora_210_300=round(max(abs(ps[s]) for s in range(72) if s<42 or s>=60),4),dsector_taca=[round(ps[s],3) for s in range(48,54)])
    print(nom,res[nom])
out['variants']=res
# correlació banda σ12–60 amb LROC per a B i B′
LR=np.log(np.maximum(L62,1)); vv=v62&disc&(rr>60)
def band(a,lo,hi,mask):
    m=mask.astype(float); return (gaussian_filter(a*m,lo)/np.maximum(gaussian_filter(m,lo),1e-9))-(gaussian_filter(a*m,hi)/np.maximum(gaussian_filter(m,hi),1e-9))
bl=band(LR,12,60,vv); par=((az//10).astype(int)%2==0); cb={}
for nom,c in (('capa74',G74),('B',candB),('B·F71',candB*F71),('Bp',candBp),('Bp·F71',candBp*F71)):
    ba=band(np.log(np.maximum(c,1)),12,60,vv); cb[nom]=dict(parells=round(float(np.corrcoef(ba[vv&par],bl[vv&par])[0,1]),3),senars=round(float(np.corrcoef(ba[vv&~par],bl[vv&~par])[0,1]),3),taca=round(float(np.corrcoef(ba[vv&(m6|e6)],bl[vv&(m6|e6)])[0,1]),3))
print('corr banda 12–60 amb LROC:',cb); out['corr_banda']=cb
np.savez_compressed(S4+'/fb6b_variants.npz',candB=candB.astype(np.float32),candBp=candBp.astype(np.float32),Vlin=Vlin.astype(np.float32),c0=c0)
json.dump(out,open(S4+'/fb6b_variants.json','w'),indent=1); print('fet')
