"""fb13: A_add·F71 amb D calculat sobre un nivell suau (σ15) del RAW (sense soroll fotònic amplificat); criteris finals, candidata, injeccions i vistes; rebut fb_rebut.json."""
import sys, json, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad')
sys.path.insert(0,'/Users/USUARI/Desktop/Eclipse 2026/3-RECERCA/tools/earthshine_broad_lroc_20260914')
from fb6_candidata import *
from s8_operator import s8_eval
from scipy.ndimage import gaussian_filter, zoom
from PIL import Image
disc=rr<430; kap=kappa(); F71=np.load(OLD+'/vel_corr_final.npy').astype(np.float64)
RAW0=np.load(S4+'/fb5_raw10s_abs_roi.npy').astype(np.float64); m=np.isfinite(RAW0)
def suau(A,s): mm=m.astype(float); return gaussian_filter(np.nan_to_num(A)*mm,s)/np.maximum(gaussian_filter(mm,s),1e-9)
def pipeline_A(RAWs_,P_):
    f,finv,xc,yi=ajusta_f(RAWs_,P_); Vdev,ringmed,Vl=vel_lineal(RAWs_); L0=suau(RAWs_,15); D=f(L0)-f(L0-Vdev)
    return (P_-Wdq+kap*(Wdq-D)), f, D
cand,f0,D=pipeline_A(RAWs,P); cand74=cand*F71
rings=np.arange(170,412,4)
def s6(A): mm=disc.astype(float); return gaussian_filter(np.nan_to_num(A)*mm,6)/np.maximum(gaussian_filter(mm,6),1e-9)
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
    mm=mask.astype(float); return (gaussian_filter(a*mm,lo)/np.maximum(gaussian_filter(mm,lo),1e-9))-(gaussian_filter(a*mm,hi)/np.maximum(gaussian_filter(mm,hi),1e-9))
bl=band(LR,12,60,vv); par=((az//10).astype(int)%2==0); lnA=np.log(np.maximum(G74,1))
def metr(c):
    lnB=np.log(np.maximum(c,1)); d60=(gaussian_filter(lnB*disc,60)-gaussian_filter(lnA*disc,60))/np.maximum(gaussian_filter(disc.astype(float),60),1e-9)
    fac=c/np.maximum(G74,1); fr=fac[(rr<440)&(rr>60)]; dl=lnB-lnA; ps=[float(np.median(dl[(sec5==s)&(rr>100)&(rr<430)])) for s in range(72)]
    ret={}
    for lo,hi in ((3,8),(8,32)):
        b0=band(lnA,lo,hi,disc); b1=band(lnB,lo,hi,disc); mm=disc&(rr<400)&(rr>60); ret[f'{lo}-{hi}']=[round(float(np.corrcoef(b0[mm],b1[mm])[0,1]),4),round(float(b1[mm].std()/b0[mm].std()),4)]
    bb=band(lnB,12,60,vv); cl=dict(parells=round(float(np.corrcoef(bb[vv&par],bl[vv&par])[0,1]),3),senars=round(float(np.corrcoef(bb[vv&~par],bl[vv&~par])[0,1]),3),taca=round(float(np.corrcoef(bb[vv&(m6|e6)],bl[vv&(m6|e6)])[0,1]),3))
    return dict(taca_anells=c_anells(c),taca_masc_pere=lnr(c),factor_vs_capa74_p1_p99=[round(float(np.percentile(fr,1)),3),round(float(np.percentile(fr,99)),3)],factor_min_max=[round(float(fr.min()),3),round(float(fr.max()),3)],s60_max_fora=round(float(np.abs(d60[disc&~m6&~e6&(rr>60)]).max()),4),s60_rms_fora=round(float(np.sqrt(np.mean(d60[disc&~m6&~e6&(rr>60)]**2))),4),s60_taca=round(float(np.median(d60[m6])),4),dsector_max_fora_210_300=round(max(abs(ps[s]) for s in range(72) if s<42 or s>=60),4),dsector_taca=[round(ps[s],3) for s in range(48,54)],retencio_corr_amplitud=ret,corr_LROC_12_60=cl)
out=dict(capa74=metr(G74),candidata_A_add_F71=metr(cand74))
print('capa74:',json.dumps(out['capa74'],ensure_ascii=False)); print('candidata:',json.dumps(out['candidata_A_add_F71'],ensure_ascii=False))
# injeccions amb aquest pipeline
edge=np.load(R+'/3-RECERCA/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy'); inj=[]
for (cx,cy,nom) in ((828,1157,'taca az255 r289'),(1250,1050,'est az~350 r~255'),(900,700,'nord-oest az~110 r~315')):
    e=np.exp(-((X-cx)**2+(Y-cy)**2)/(2*50.0**2)); use=(e>0.05)&(rr<430)
    for amp in (-0.03,0.03):
        g=amp*e; Pi=P+(f0(RAWs*(1+g))-f0(RAWs)); ci,_,_=pipeline_A(RAWs*(1+g),Pi); resp=ci-cand; esp=Pi-P
        gain=float(np.sum(resp[use]*esp[use])/np.sum(esp[use]**2)); inj.append(dict(posicio=nom,amplitud=amp,sigma=50,gain=round(gain,3),passa=bool(0.9<=gain<=1.1)))
print('injeccions:',inj); out['injeccions']=inj
# candidata (mateix factor als tres canals; alfa/màscara intactes; r>440 intacte)
fac=cand74/np.maximum(G74,1); fac[(G74<=0)|(rr>440)]=1.0; d74=np.load(S4+'/roi74p_L30.npz'); o={k:d74[k] for k in d74.files}
for key in ('c0','c1','c2'): o[key]=np.clip(np.rint(d74[key].astype(np.float64)*fac),0,65535).astype(np.uint16)
np.savez_compressed(S4+'/roi75_L30_candidata.npz',**o); np.save(S4+'/fb13_factor.npy',fac.astype(np.float32)); np.savez_compressed(S4+'/fb13_candidata.npz',cand69=cand.astype(np.float32),cand74=cand74.astype(np.float32),D=D.astype(np.float32))
chk=np.load(S4+'/roi75_L30_candidata.npz'); out['candidata_fitxer']=dict(ruta=S4+'/roi75_L30_candidata.npz',claus=chk.files,alfa_mascara_intactes=bool((chk['c-1']==d74['c-1']).all() and (chk['c-2']==d74['c-2']).all()),canvis_r_gt_440=int((chk['c1']!=d74['c1'])[rr>440].sum()),mateix_factor_3_canals=True)
print(out['candidata_fitxer'])
# vistes, mateix to abans/després
st=lambda A,lo,hi: np.clip((A-lo)/(hi-lo),0,1); lo,hi=6300,10300
y0,x0=1157-230,828-230; sl=(slice(y0,y0+700),slice(x0,x0+700)); lroc=st(L62,np.percentile(L62[v62&disc],1),np.percentile(L62[v62&disc],99.5))*(v62&disc)
Image.fromarray(np.uint8(np.concatenate([st(G74,lo,hi)[sl],st(cand74,lo,hi)[sl],lroc[sl]],1)*255)).save(S4+'/v_fb_taca_capa74_candidata_lroc_x1.png')
sl2=(slice(1157-170,1157+170),slice(828-170,828+170)); Image.fromarray(np.uint8(np.concatenate([zoom(st(G74,lo,hi)[sl2],2,order=1),zoom(st(cand74,lo,hi)[sl2],2,order=1),zoom(lroc[sl2],2,order=1)],1)*255)).save(S4+'/v_fb_taca_abans_despres_lroc_x2.png')
p2=np.percentile(G74[disc],2); p995=np.percentile(G74[disc],99.5); ims=[st(G74,p2,p995)*disc,st(cand74,p2,p995)*disc,lroc]
Image.fromarray(np.uint8(np.concatenate([im[520:1480,520:1480] for im in ims],1)*255)).save(S4+'/v_fb_lluna_capa74_candidata_lroc_p2negre.png')
dl=np.log(np.maximum(cand74,1))-lnA; Image.fromarray(np.uint8(np.clip(0.5+dl/0.2,0,1)[520:1480,520:1480]*disc[520:1480,520:1480]*255)).save(S4+'/v_fb_mapa_correccio_ln_pm0.1.png')
json.dump(out,open(S4+'/fb13_final.json','w'),indent=1,ensure_ascii=False); print('fet')
