"""S4 (V51) · Correcció A L'ORIGEN del forat de la base al limbe lunar: es recompon la fusió Vixen a la caixa lunar amb la
MATEIXA maquinària V38 (A1/B2: mateixos fotogrames, registre, pesos, offsets, phi, flat, correcció de vora lunar) però amb la
màscara lunar per fotograma al limbe APARENT (el disc modelat RL fa 2–2,5 px més que la silueta de 50 %) i sense guarda,
amb la correcció de vora estesa al perfil mesurat per A1 (V38) fins a 3,5 px dins del limbe modelat per als curts, i
entrada per classe d'exposició (curts D≥−3,5; mitjans D≥−1; llargs D≥+1). Després la recepta EXACTA de la base V42 (b4e)
sobre la fusió amb el suport ampliat. Guardarails: (1) amb la màscara vigent es reprodueix vixen_total_v38 a la caixa;
(2) la recepta reimplementada reprodueix base_corba_total_v42_u16 a la finestra."""
import sys, json, time, numpy as np
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE.parent/'v42_20260910')); sys.path.insert(0,str(HERE.parent/'v38_20260908'))
from comu42 import *            # cadena: comu, f2, RUNS, CAU36, REB36, CX, CY, RS, W, H, Q, cv2, gauss, CAU42, CAUF...
import comu38
from comu38 import upsample, CAU38, flat_ripple_correction, COMMON_TO_FINAL
from scipy.ndimage import gaussian_filter1d
CAU=HERE/'cau'; OUT=ROOT/'output/earthshine_v50_temporal_20260912'   # DESPRÉS dels imports: comu42 exporta CAU/OUT propis
Y0,Y1,X0,X1=[int(v) for v in np.load(CAU38/'franja_perfotograma.npz')['box']]
RX0,RY0,N=4677,3077,1400; CXr=699.568111973117; CYr=699.6475341408573
t00=time.time()
# --- correccions de vora: taula B2 (vigent) i perfil A1 estès ---
TAULA=json.loads((CAU38/'correccio_vora_lunar.json').read_text())['taula']
A1=json.loads((ROOT/'output/v38_20260908/4-rebuts/A1_franja_font.json').read_text())['perfil_biaix_vs_distancia_vora']
CLS={'curts':'curts (≤1/800)','mitjans':'mitjans (1/800–1/50)','llargs':'llargs (>1/50)'}
def classe(e): return 'curts' if e<=1/800 else ('mitjans' if e<=1/50 else 'llargs')
def corr_b2(D,e):
    tb=TAULA[classe(e)]; B=np.interp(D,np.asarray(tb['d_px'],np.float32),np.asarray(tb['B_ln'],np.float32),left=tb['B_ln'][0],right=0.0).astype(np.float32); return np.exp(-B,dtype=np.float32)
DMIN={'curts':-3.5,'mitjans':-1.0,'llargs':1.0}
TIERS=[dict(curts=0.0,mitjans=0.5,llargs=1.5),dict(curts=-2.0,mitjans=-0.5,llargs=None),dict(curts=-4.0,mitjans=None,llargs=None)]; GT=[0.02,4e-4,8e-6]
def corr_ext(D,e):
    c=classe(e); tb=TAULA[c]; prof=A1[CLS[c]]['perfil']; dd=np.array([p['d'] for p in prof]); ml=np.array([p['mediana_ln'] for p in prof])
    lo=dd<tb['d_px'][0]  # per sota del rang de la taula B2, el perfil A1 mesurat (mediana 3 no aplicada: bins d'1 px)
    d_all=np.r_[dd[lo],np.asarray(tb['d_px'])]; B_all=np.r_[ml[lo],np.asarray(tb['B_ln'])]
    B=np.interp(D,d_all.astype(np.float32),B_all.astype(np.float32),left=B_all[0],right=0.0).astype(np.float32); return np.exp(-B,dtype=np.float32)
def fl_tier(D,e,t):
    d0=TIERS[t][classe(e)]
    return np.zeros_like(D) if d0 is None else np.clip((D-d0)/1.0,0,1).astype(np.float32)
# --- recomposició A1/B2 a la caixa ---
path=RUNS['vixen']; run=comu.Run.obre(str(path)); ctx=f2.Ctx(run)
pos=json.loads((path/'4-rebuts/F1.3_registre.json').read_text())['fotogrames']; kq=json.loads((path/'4-rebuts/F2.2_coherencia.json').read_text())['k']
meta=json.loads((CAU36/'vixen_meta.json').read_text())['frames']; names=[m['name'] for m in meta]
phis={c:np.load(CAU36/f'vixen_{c}_phi.npy',mmap_mode='r') for c in ('R','G','B')}; fcorr,_=flat_ripple_correction(ctx,'vixen')
inv=cv2.invertAffineTransform(COMMON_TO_FINAL); yy,xx=np.mgrid[Y0:Y1,X0:X1].astype(np.float32)
qx=inv[0,0]*xx+inv[0,1]*yy+inv[0,2]; qy=inv[1,0]*xx+inv[1,1]*yy+inv[1,2]; dx=(qx-ctx.CX)*ctx.k; dy=(qy-ctx.CY)*ctx.k
h,w=Y1-Y0,X1-X0; numO=np.zeros((h,w,3),np.float32); denO=np.zeros((h,w,3),np.float32); numN=np.zeros((h,w,3),np.float32); denN=np.zeros((h,w,3),np.float32); numT=[np.zeros((h,w,3),np.float32) for _ in TIERS]; denT=[np.zeros((h,w,3),np.float32) for _ in TIERS]
Dmin=np.full((h,w),99.,np.float32); info=[]
NC=sum(1 for n in names if pos[n]['exp']<=1/800); VT=[np.full((NC,h,w,3),np.nan,np.float32) for _ in (1,2)]; jc=0
for j,n in enumerate(names):
    v=pos[n]; k=kq.get(n,1.0); m=meta[j]
    rx=(ctx.ca*dx+ctx.sa*dy+v['sol_x']).astype(np.float32); ry=(-ctx.sa*dx+ctx.ca*dy+v['sol_y']).astype(np.float32)
    mlx=v['sol_x']+float(v['lluna_dx']); mly=v['sol_y']+float(v['lluna_dy']); D=(np.hypot(rx-mlx,ry-mly)-ctx.RL).astype(np.float32)
    flO=f2.mascara_lluna(ctx,v,rx,ry); cO=corr_b2(D,v['exp']); cN=corr_ext(D,v['exp']); flT=[fl_tier(D,v['exp'],t) for t in range(len(TIERS))]
    Dmin=np.minimum(Dmin,np.where(flT[-1]>0,D,99.))
    plans=ctx.plans(n,v['exp'])
    for i,(pl,wgt) in plans.items():
        c=comu.IDX_CANAL[i]; oy,ox=ctx.orig[i]
        if fcorr is not None: pl=pl*fcorr[i]
        mx=((rx-ox)*.5).astype(np.float32); my=((ry-oy)*.5).astype(np.float32)
        dd=cv2.remap(wgt,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT); nn=cv2.remap(pl*wgt*k,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
        b=float(m['offset_RGB'][c])
        if b!=0.0: nn=nn+b*dd
        phi=upsample(phis[{0:'R',1:'G',2:'B'}[c]][j])[Y0:Y1,X0:X1]; nn=nn*np.exp(-phi)
        numO[...,c]+=nn*flO*cO; denO[...,c]+=dd*flO
        for t in range(len(TIERS)):
            wT=flT[t]/np.maximum(cN,1e-6)**2   # inversa de variància dins del nivell
            numT[t][...,c]+=nn*wT*cN; denT[t][...,c]+=dd*wT
            if t>=1 and v['exp']<=1/800:
                VT[t-1][jc,...,c]=np.where((dd>0)&(flT[t]>0),nn*cN/np.maximum(dd,1e-20),np.nan)
    if v['exp']<=1/800: jc+=1
    info.append(dict(name=n,t=m['t'],exp=v['exp'],classe=classe(v['exp'])))
    if j%10==0 or j==len(names)-1: print(f'fotograma {j+1}/{len(names)} ({time.time()-t00:.0f}s)',flush=True)
    del plans,rx,ry,flO,flT,cO,cN
camO=np.where(denO>0,numO/np.maximum(denO,1e-20),np.nan); _,totO=comu.lluminancia(camO,run.matriu,run.color['guany']); totO=totO.astype(np.float32)
numN=numO.copy()+GT[0]*numT[0]; denN=denO.copy()+GT[0]*denT[0]
for t in (1,2):   # nivells 3–4: valor central = mediana entre curts (≥3 fotogrames), pes = den del nivell
    med=np.nanmedian(VT[t-1],axis=0); nv=np.sum(np.isfinite(VT[t-1][...,1]),axis=0)
    ok=(nv>=3)&np.all(np.isfinite(med),-1); numN+=np.where(ok[...,None],GT[t]*med*denT[t],0); denN+=np.where(ok[...,None],GT[t]*denT[t],0)
del VT
camN=np.where(denN>0,numN/np.maximum(denN,1e-20),np.nan); _,totN=comu.lluminancia(camN,run.matriu,run.color['guany']); totN=totN.astype(np.float32)
ref=np.asarray(np.load(CAU38/'vixen_total_v38.npy',mmap_mode='r')[Y0:Y1,X0:X1])
good=np.all(np.isfinite(totO)&(totO>0),2)&np.all(np.isfinite(ref)&(ref>0),2); rel=np.abs(totO[good]-ref[good])/ref[good]
g1=dict(px=int(good.sum()),rel_max=float(rel.max()),rel_p999=float(np.percentile(rel,99.9)),suport_vell=int(np.all(denO>0,2).sum()),suport_ref=int(np.all(np.isfinite(ref)&(ref>0),2).sum()))
print('GUARDARAIL 1 (màscara vigent → vixen_total_v38):',g1,flush=True)
np.savez(CAU/'s4_recomposicio_box.npz',totO=totO,totN=totN,denO=denO,denN=denN,Dmin=Dmin,box=np.array([Y0,Y1,X0,X1]))
# --- recepta exacta de la base V42 (b4e, k=1) sobre la finestra ---
M=100; wY0,wY1,wX0,wX1=Y0-M,Y1+M,X0-M,X1+M
VA=70736.46875; PEND,ANC,TERRA=0.22,0.74,0.045
def base_srgb_k1(tot,mf,q_fix=None):
    """Recepta b4e (k=1). Amb q_fix: el camp de color suavitzat (24 px) es pren del càlcul de referència (V42), de manera que
    fora de l'anell no canvia cap píxel; dins de l'anell el to ve de la lluminància nova per píxel i el color del camp V42."""
    den=gauss(mf,24); data=np.nan_to_num(tot.astype(np.float32))
    L=(data[...,0]+2*data[...,1]+data[...,2])/4; tone=comu.corba_to(L,mf>0,VA,pend=PEND,anc=ANC,terra=TERRA)
    if q_fix is None:
        ls=gauss(L*mf,24)/np.maximum(den,1e-8); q=np.stack([gauss(data[...,i]*mf,24)/np.maximum(den,1e-8)/np.maximum(ls,1e-8) for i in range(3)],axis=2)
    else: q=q_fix
    ylin=comu.a_lineal(tone); qmax=q.max(axis=2)
    with np.errstate(divide='ignore',invalid='ignore'): wmax=np.where(qmax>1,(1/np.maximum(ylin,1e-8)-1)/(qmax-1),1)
    wg=np.clip(np.nan_to_num(wmax,nan=0,posinf=1),0,1); srgb=comu.a_srgb(ylin[...,None]*(1+wg[...,None]*(q-1)))*mf[...,None]
    return np.clip(np.nan_to_num(srgb),0,1).astype(np.float32),q
tot=np.array(np.load(CAU42/'fusion_total_v42_sense_estrelles.npy',mmap_mode='r')[wY0:wY1,wX0:wX1]); mS=np.array(np.load(CAU42/'support_v42.npy',mmap_mode='r')[wY0:wY1,wX0:wX1]).astype(np.float32)
uref=np.array(np.load(CAU42/'base_corba_total_v42_u16.npy',mmap_mode='r')[wY0:wY1,wX0:wX1]).astype(np.int32)
s0,q_ref=base_srgb_k1(tot,mS); u0=np.round(s0*65535).astype(np.int32)
inner=(slice(M,-M),slice(M,-M)); d0=np.abs(u0-uref)[inner]; g2=dict(max_DN16=int(d0.max()),p999=float(np.percentile(d0,99.9)),mitjana=float(d0.mean()))
print('GUARDARAIL 2 (recepta b4e reimplementada → base V42 u16 a la caixa):',g2,flush=True)
supN=np.all(denN>0,2)&np.all(np.isfinite(totN),2)   # valors ≤0 (matriu de color a píxels saturats) els retalla la recepta, com a la V42
tot2=tot.copy(); m2=mS.copy(); bx=(slice(M,M+h),slice(M,M+w))
tot2[bx][supN]=totN[supN]; m2[bx]=np.maximum(m2[bx],supN.astype(np.float32))
s1_,_=base_srgb_k1(tot2,m2,q_fix=q_ref); u1=np.round(s1_*65535).astype(np.int32)
np.save(CAU/'s4_base_new_box_u16.npy',u1[bx].astype(np.uint16)); np.save(CAU/'s4_base_ref_box_u16.npy',uref[bx].astype(np.uint16)); np.save(CAU/'s4_support_new_box.npy',supN)
# --- diferències per distància a F4 (coordenades ROI) ---
f4=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy'); th=np.linspace(0,2*np.pi,1440,endpoint=False); f4s=gaussian_filter1d(f4,3.0,mode='wrap')
yb,xb=np.mgrid[Y0:Y1,X0:X1]; xr=xb-RX0; yr=yb-RY0; r=np.hypot(xr-CXr,yr-CYr); ang=np.arctan2(yr-CYr,xr-CXr)%(2*np.pi)
F4=np.interp(ang,np.append(th,2*np.pi),np.append(f4s,f4s[0])); d=r-F4; sec=(ang/(2*np.pi)*12).astype(int)
dif=(u1-uref)[bx]; supO=mS[bx]>0
rows=[]
for lo,hi in ((-3,-1),(-1,0),(0,1),(1,2),(2,4),(4,8),(8,16),(16,40),(40,80),(80,200)):
    mm=(d>=lo)&(d<hi)&supO; nn=(d>=lo)&(d<hi)&supN&~supO
    rows.append(dict(d=[lo,hi],px_ja_amb_dada=int(mm.sum()),max_diff_on_hi_havia_dada=int(np.abs(dif[mm]).max()) if mm.any() else None,p99_diff=float(np.percentile(np.abs(dif[mm]),99)) if mm.any() else None,px_nous=int(nn.sum())))
print('diferències per banda de d (DN16):'); [print(x) for x in rows]
far=(d>=8)&(d<40)&supO&supN; relT=[float(np.median(np.abs(totN[far][:,c]-tot[bx][far][:,c])/np.maximum(tot[bx][far][:,c],1e-6))) for c in range(3)]
print('totN vs fusió V42 a d 8–40 (rel mediana per canal):',relT,' u1-uref mediana per canal:',[float(np.median(dif[far][:,c])) for c in range(3)])
# vora de dada nova i vella per sector (50 % del den G respecte del nivell a d 6–10)
edge={}
for tag,den in (('vella',denO[...,1]),('nova',denN[...,1])):
    e=[]
    for s in range(12):
        m=sec==s; full=np.median(den[m&(d>=6)&(d<10)])
        prof=[float(np.median(den[m&(d>=k)&(d<k+0.5)]))/full for k in np.arange(-4,6,0.5)]
        k50=next((float(-4+0.5*i) for i,pv in enumerate(prof) if pv>=0.5),None); e.append(k50)
    edge[tag]=e
print('vora de dada (50 % del pes) − F4 per sector, vella:',edge['vella']); print('                                          nova:',edge['nova'])
G=lambda u:u[...,1]
profs=[]
for s in range(12):
    m=sec==s; profs.append(dict(sector=s,ref=[int(np.median(uref[bx][...,1][m&(d>=k)&(d<k+1)])) for k in range(-3,9)],nova=[int(np.median(u1[bx][...,1][m&(d>=k)&(d<k+1)])) for k in range(-3,9)]))
for p in profs: print(p)
savejson(OUT/'S4_origen.json',dict(guardarail_1_vixen_total_v38=g1,guardarail_2_recepta_b4e=g2,box=[Y0,Y1,X0,X1],finestra_marge=M,classes_entrada_D=dict(nivell1='màscara vigent V38 (D≥2, rampa 2 px, correcció B2)',nivells=TIERS,pes_per_nivell=GT),
    correccio='B2 vigent per D≥−1,75; perfil A1 mesurat (mediana ln fotograma/compost net) per D<−1,75; 0 més enllà de 30 px',diff_per_banda=rows,vora_dada_menys_F4_per_sector=edge,perfils_G=profs,fotogrames=info))
print('S4 fet',f'{time.time()-t00:.0f}s')
