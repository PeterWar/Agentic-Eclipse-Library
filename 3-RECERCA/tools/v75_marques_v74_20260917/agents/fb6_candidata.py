"""fb6: correcció a l'origen de la taca (m6): substitueix el vel S8 (per sector, monòton, en unitats de P) per «f⁻¹ → resta del vel lineal 2D → f»;
W_S8 desquantitzat als nodes del PNG; factor azimutal (recepta a28/V71) refet; candidata per a la capa 30 de V74 i mètriques (d)."""
import sys, json, numpy as np
from scipy.ndimage import gaussian_filter, gaussian_filter1d, map_coordinates, median as ndmed, mean as ndmean
from scipy.optimize import isotonic_regression
S4='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
R='/Users/USUARI/Desktop/Eclipse 2026'
CX,CY,RS=998.88,998.41,456.0; A_MODEL=0.1222   # a28 'hdr': A amb LROC de covariable
Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY); az=(np.degrees(np.arctan2(-(Y-CY),X-CX)))%360; sec5=(az//5).astype(int)
# marc S8 (1400², centre 699.57/699.65, angle horari amb y avall) col·locat a la ROI a (300,300)
CXs,CYs=699.568111973117+300,699.6475341408573+300
angS8=np.arctan2(Y-CYs,X-CXs)%(2*np.pi); rS8=np.hypot(X-CXs,Y-CYs)
edge=np.load(R+'/3-RECERCA/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy'); f4s=gaussian_filter1d(edge,3.0,mode='wrap'); th=np.linspace(0,2*np.pi,1440,endpoint=False)
F4=np.interp(angS8,np.append(th,2*np.pi),np.append(f4s,f4s[0])); d=rS8-F4
secS8=(angS8*72/(2*np.pi)).astype(int)
# --- 1) W_S8 desquantitzat: mostra el PNG als nodes (angle 5k°, ±0,5°) per bins de 2 px en d, suavitza en d, reinterpola bilinealment com l'S8
V=np.load(S4+'/fb2_vel_s8.npz'); Wpng=np.zeros((2000,2000)); Wpng[300:1700,300:1700]=V['W2']
dc=np.arange(-299,3,2.); ib=np.floor((d+300)/2).astype(int)
node=np.round(angS8*72/(2*np.pi))%72; wedge=np.abs(((angS8*72/(2*np.pi)-node+36)%72)-36)<0.1   # ±0,5°
ok=wedge&(ib>=0)&(ib<len(dc))&(rr>150); lab=node[ok].astype(int)*len(dc)+ib[ok]
cnt=np.bincount(lab,minlength=72*len(dc)); mu=ndmean(Wpng[ok],labels=lab,index=np.arange(72*len(dc))); Wt=np.where(cnt>=3,mu,np.nan).reshape(72,len(dc))
for k in range(72):
    okk=np.isfinite(Wt[k]); Wt[k]=np.interp(dc,dc[okk],Wt[k,okk])
Wt=gaussian_filter1d(Wt,1.0,axis=1); Wt[:,dc<-262]=0; Wt=np.maximum(Wt,0)
si=angS8*72/(2*np.pi); di=np.interp(d,dc,np.arange(len(dc)))
Wdq=map_coordinates(np.r_[Wt,Wt[:1]],[si,di],order=1,mode='nearest'); Wdq[d<-300]=0; Wdq[rr>RS+20]=0
inter=(d<-70)&(d>-262); print('W desquantitzat vs PNG (d −262…−70): dif mediana %.0f, p99 |dif| %.0f, màx %.0f DN16'%(np.median(Wdq[inter]-Wpng[inter]),np.percentile(np.abs(Wdq-Wpng)[inter],99),np.abs(Wdq-Wpng)[inter].max()))
np.save(S4+'/fb6_W_s8_dq.npy',Wdq.astype(np.float32))
# --- 2) capes
d69=np.load(OLD+'/roi_L30.npz'); G69=d69['c1'].astype(np.float64); P=G69+Wdq
d74=np.load(S4+'/roi74p_L30.npz'); G74=d74['c1'].astype(np.float64); F71=np.load(OLD+'/vel_corr_final.npy').astype(np.float64)
RAW=np.load(S4+'/fb5_raw10s_abs_roi.npy').astype(np.float64); RAWs=gaussian_filter(np.nan_to_num(RAW),3)
Gaz=np.nan_to_num(np.load(OLD+'/vel_Gaz_hdr.npy').astype(np.float64))
L62d=np.load(S4+'/roi74p_L62.npz'); L62=np.dstack([L62d['c0'],L62d['c1'],L62d['c2']]).astype(np.float64).mean(-1); v62=L62d['c-1']>30000
M=np.load(S4+'/marques74_masks.npz'); m6=M['m6']; e6=M['ent_m6']
def ajusta_f(RAWs,P):
    disc=(rr<430)&np.isfinite(RAW); Ps=gaussian_filter(P,3); x=RAWs[disc]; y=Ps[disc]; o=np.argsort(x); xs=x[o]; ys=y[o]
    edges=np.quantile(xs,np.linspace(0,1,301)); xc=np.array([xs[(xs>=a)&(xs<=b)].mean() for a,b in zip(edges[:-1],edges[1:])]); yc=np.array([np.median(ys[(xs>=a)&(xs<=b)]) for a,b in zip(edges[:-1],edges[1:])])
    yi=isotonic_regression(yc).x; yi=np.maximum.accumulate(yi+np.arange(len(yi))*1e-6)   # estrictament creixent per poder invertir
    # extrapolació lineal amb el pendent dels extrems
    sl0=(yi[5]-yi[0])/(xc[5]-xc[0]); sl1=(yi[-1]-yi[-6])/(xc[-1]-xc[-6])
    def f(v): return np.where(v<xc[0],yi[0]+(v-xc[0])*sl0,np.where(v>xc[-1],yi[-1]+(v-xc[-1])*sl1,np.interp(v,xc,yi)))
    def finv(w): return np.where(w<yi[0],xc[0]+(w-yi[0])/sl0,np.where(w>yi[-1],xc[-1]+(w-yi[-1])/sl1,np.interp(w,yi,xc)))
    return f,finv,xc,yi
def vel_lineal(RAWs):
    """vel lineal 2D: mediana azimutal del RAW per anell (suau) × (1 + A·Gaz); desviació respecte al terra per sector S8 (d −260…−200) amb taper com l'S8."""
    rb=np.arange(0,470,2); prof=np.array([np.nanmedian(RAWs[(rr>=a)&(rr<a+2)&np.isfinite(RAW)]) for a in rb]); prof=gaussian_filter1d(np.nan_to_num(prof,nan=np.nanmedian(prof)),2)
    ringmed=np.interp(rr,rb+1,prof); Vlin=ringmed*(1+A_MODEL*Gaz)
    base=(d>=-260)&(d<=-200)&(rr>100); lab=secS8[base]; fl=ndmed(Vlin[base],labels=lab,index=np.arange(72))
    fls=gaussian_filter1d(fl,1.0,mode='wrap'); floor=np.interp(si,np.arange(73),np.r_[fls,fls[0]])
    Vdev=(Vlin-floor)*np.clip((d+260)/60,0,1); Vdev[d<-260]=0
    return Vdev,ringmed,Vlin
def kappa(): 
    t=np.clip((d+70)/30,0,1); return 1-(t*t*(3-2*t))   # 1 a d ≤ −100, 0 a d ≥ −70
def factor_azimutal(Gcapa):
    """recepta a28/V71: per anell de 20 px, regressió de la capa (ring-norm, σ6) sobre [Gaz, LROC_az]; c(r) ≥ 0 suau; factor 1/(1+c·Gaz), taper a 448."""
    disc=rr<RS-8
    def ring_norm(A,mask):
        out=np.full(A.shape,np.nan)
        for k in range(0,int(RS)+4,4):
            m=mask&(rr>=k)&(rr<k+4)
            if m.sum()>10: out[m]=A[m]/np.mean(A[m])-1
        return out
    LAY=ring_norm(gaussian_filter(Gcapa,6),disc); LROC_az=ring_norm(gaussian_filter(L62,6),v62&disc)
    bins=np.arange(20,RS-8,20); cs=[]
    for k in bins:
        m=disc&(rr>=k)&(rr<k+20)&np.isfinite(LAY)&np.isfinite(LROC_az)
        Xm=np.stack([Gaz[m],LROC_az[m],np.ones(m.sum())],1); coef,*_=np.linalg.lstsq(Xm,LAY[m],rcond=None); cs.append(coef[0])
    cs=np.array(cs); c_s=gaussian_filter1d(np.clip(cs,0,None),1.5); c_r=np.interp(rr,bins+10,c_s)*np.clip((RS-8-rr)/24,0,1)
    corr=1.0/(1.0+c_r*Gaz); corr[rr>=RS-8]=1.0; return corr,cs
def candidata(RAWs,P,G69):
    f,finv,xc,yi=ajusta_f(RAWs,P); Vdev,ringmed,Vlin=vel_lineal(RAWs); kap=kappa()
    lin=finv(P); nou_int=f(lin-Vdev); cand69=kap*nou_int+(1-kap)*G69
    Fn,cs=factor_azimutal(cand69); cand74=cand69*Fn
    return dict(f=f,finv=finv,Vdev=Vdev,cand69=cand69,cand74=cand74,Fn=Fn,cs=cs,ringmed=ringmed,xc=xc,yi=yi)
if __name__=='__main__':
    C=candidata(RAWs,P,G69); cand69=C['cand69']; cand74=C['cand74']; Vdev=C['Vdev']
    np.savez_compressed(S4+'/fb6_candidata.npz',cand69=cand69.astype(np.float32),cand74=cand74.astype(np.float32),Vdev=Vdev.astype(np.float32),Fn=C['Fn'].astype(np.float32))
    out={}
    lnr=lambda A: float(np.log(np.median(A[m6])/np.median(A[e6])))
    print('Vdev (lineal, DN14): taca mediana %.1f entorn %.1f ; RAW dins/entorn ln %.4f'%(np.median(Vdev[m6]),np.median(Vdev[e6]),float(np.log(np.median(RAWs[m6])/np.median(RAWs[e6])))))
    out['taca_ln_dins_entorn']=dict(P=lnr(P),capa69=lnr(G69),capa74=lnr(G74),cand69=lnr(cand69),cand74=lnr(cand74),cand69_x_F71=lnr(cand69*F71),LROC=float(np.log(np.median(L62[m6&v62])/np.median(L62[e6&v62]))))
    print('taca ln(dins/entorn):',{k:round(v,4) for k,v in out['taca_ln_dins_entorn'].items()})
    # canvi respecte a V74: factor
    fac=cand74/np.maximum(G74,1); fac[G74<=0]=1
    out['factor']=dict(min=float(fac[rr<440].min()),max=float(fac[rr<440].max()),p1=float(np.percentile(fac[rr<440],1)),p99=float(np.percentile(fac[rr<440],99)),r_gt_440_max_abs_dev=float(np.abs(fac[rr>440]-1).max()))
    print('factor cand74/capa74 dins r<440: min %.3f p1 %.3f p99 %.3f max %.3f ; r>440 màx |f−1| %.4f'%(out['factor']['min'],out['factor']['p1'],out['factor']['p99'],out['factor']['max'],out['factor']['r_gt_440_max_abs_dev']))
    # gran escala σ60 (ln) abans/després, dins i fora de la taca; per sector
    disc=(rr<430); lnA=np.log(np.maximum(G74,1)); lnB=np.log(np.maximum(cand74,1))
    def sm(a,s): return gaussian_filter(a*disc,s)/np.maximum(gaussian_filter(disc.astype(float),s),1e-9)
    d60=sm(lnB,60)-sm(lnA,60); d60[~disc]=0
    out['gran_escala_s60']=dict(max_abs_dins_taca=float(np.abs(d60[m6]).max()),max_abs_fora_taca=float(np.abs(d60[disc&~m6&~e6]).max()),rms_fora=float(np.sqrt(np.mean(d60[disc&~m6&~e6]**2))),p99_abs_fora=float(np.percentile(np.abs(d60[disc&~m6&~e6]),99)))
    print('σ60 ln canvi: màx |Δ| a la taca %.4f ; fora: màx %.4f p99 %.4f rms %.4f'%(out['gran_escala_s60']['max_abs_dins_taca'],out['gran_escala_s60']['max_abs_fora_taca'],out['gran_escala_s60']['p99_abs_fora'],out['gran_escala_s60']['rms_fora']))
    # per sector de 5° (r 100–430): mediana de Δln
    dl=lnB-lnA; ps=[float(np.median(dl[(sec5==s)&(rr>100)&(rr<430)])) for s in range(72)]
    out['delta_ln_mediana_per_sector_az5']=[round(x,4) for x in ps]; print('Δln mediana per sector (az 0,5,…): taca 240–270 =',[round(ps[s],3) for s in range(48,54)],'| màx |Δ| fora de 210–300:',round(max(abs(ps[s]) for s in range(72) if s<42 or s>=60),4))
    # banda mitjana (σ12–σ60) en ln contra LROC: correlació per sectors parells/senars de 10°
    LR=np.log(np.maximum(L62,1)); vv=v62&disc&(rr>60)
    def band(a,lo,hi,mask): 
        m=mask.astype(float); return (gaussian_filter(a*m,lo)/np.maximum(gaussian_filter(m,lo),1e-9))-(gaussian_filter(a*m,hi)/np.maximum(gaussian_filter(m,hi),1e-9))
    bl=band(LR,12,60,vv); par=((az//10).astype(int)%2==0)
    corr={}
    for nom,a in (('capa74',lnA),('cand74',lnB),('capa69',np.log(np.maximum(G69,1))),('cand69',np.log(np.maximum(cand69,1)))):
        ba=band(a,12,60,vv); corr[nom]=dict(parells=float(np.corrcoef(ba[vv&par],bl[vv&par])[0,1]),senars=float(np.corrcoef(ba[vv&~par],bl[vv&~par])[0,1]),taca=float(np.corrcoef(ba[vv&(m6|e6)],bl[vv&(m6|e6)])[0,1]))
    out['corr_banda_12_60_amb_LROC']=corr; print('corr banda σ12–60 amb LROC:',{k:{kk:round(x,3) for kk,x in v.items()} for k,v in corr.items()})
    # bandes fines: retenció
    for lo,hi in ((3,8),(8,32)):
        b0=band(lnA,lo,hi,disc); b1=band(lnB,lo,hi,disc); m=disc&(rr<400); out[f'retencio_{lo}_{hi}']=dict(corr=float(np.corrcoef(b0[m],b1[m])[0,1]),amplitud=float(b1[m].std()/b0[m].std()))
    print('retenció bandes fines:',{k:v for k,v in out.items() if k.startswith('retencio')})
    out['c_azimutal']=dict(V71_c_final_a29c='vegeu OLD/a29c_amplitud.json',refet=[round(float(x),3) for x in C['cs']])
    out['corba_f']=dict(raw=[round(float(v),1) for v in C['xc'][::15]],P=[round(float(v),1) for v in C['yi'][::15]])
    json.dump(out,open(S4+'/fb6_candidata.json','w'),indent=1)
    # candidata per a la capa 30 de V74: mateix factor als tres canals, alfa i màscara intactes, cap canvi a r>440
    fac=np.where(rr>440,1.0,fac); outnpz={k:d74[k] for k in d74.files}
    for key in ('c0','c1','c2'): outnpz[key]=np.clip(np.rint(d74[key].astype(np.float64)*fac),0,65535).astype(np.uint16)
    np.savez_compressed(S4+'/roi75_L30_candidata.npz',**outnpz); np.save(S4+'/fb6_factor.npy',fac.astype(np.float32))
    # vistes: retall 700×700 al voltant de la taca, mateix to: capa74 | candidata | LROC ; i ×2 de la taca
    from PIL import Image
    y0,x0=1157-230,828-230; sl=(slice(y0,y0+700),slice(x0,x0+700))
    st=lambda A,lo,hi: np.clip((A-lo)/(hi-lo),0,1)
    lroc=st(L62,np.percentile(L62[v62&disc],1),np.percentile(L62[v62&disc],99.5))*(v62&disc)
    pan=np.concatenate([st(G74,6300,10300)[sl],st(cand74,6300,10300)[sl],lroc[sl]],1); Image.fromarray(np.uint8(pan*255)).save(S4+'/v_fb6_taca_capa74_candidata_lroc_x1.png')
    from scipy.ndimage import zoom
    sl2=(slice(1157-160,1157+160),slice(828-160,828+160)); pan2=np.concatenate([zoom(st(G74,6300,10300)[sl2],2,order=1),zoom(st(cand74,6300,10300)[sl2],2,order=1)],1); Image.fromarray(np.uint8(pan2*255)).save(S4+'/v_fb6_taca_abans_despres_x2.png')
    # lluna sencera amb el terra restat (p2 → negre) abans/després
    lo=np.percentile(G74[disc],2); hi=np.percentile(G74[disc],99.5); pan3=np.concatenate([st(G74,lo,hi)*disc,st(cand74,lo,hi)*disc,st(Vdev+ (hi-lo)/2*0+np.median(Vdev[disc]),np.percentile(Vdev[disc],1),np.percentile(Vdev[disc],99))*disc],1)
    Image.fromarray(np.uint8(pan3[500:1500]*255)).save(S4+'/v_fb6_lluna_abans_despres_vdev.png'); print('fet')
