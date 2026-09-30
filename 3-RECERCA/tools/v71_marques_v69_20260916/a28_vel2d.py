"""A28: model 2D del vel (corona ⊗ ala de PSF) dins del disc lunar; ajust del nucli contra el disc RAW (LROC només com a covariable/jutge);
coeficient a la capa lunar per anell; correcció de la component AZIMUTAL del vel a la capa 30; validació contra LROC.
ús: a28_vel2d.py <font: base|hdr> """
import sys, json, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
from scipy.signal import fftconvolve
from scipy.ndimage import gaussian_filter, map_coordinates
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
FONT=sys.argv[1] if len(sys.argv)>1 else 'base'; RS=456.0; N=3000; c0=(1499.88,1500.41)
yy,xx=np.mgrid[0:N,0:N]; rr=np.hypot(xx-c0[0],yy-c0[1])
if FONT=='base':
    b=np.load(SP+'/base_3000.npz'); L=np.dstack([b['c0'],b['c1'],b['c2']]).astype(np.float32).mean(-1)/65535; sup=(b['c-1'].astype(np.float32)/65535)*(b['c-2'].astype(np.float32)/65535)
    C=np.where((rr>=RS)&(sup>0.5),10**(L/0.17),0.0).astype(np.float64); C[(rr>=RS)&(sup<=0.5)]=np.nan
    # forats sense suport fora del disc: omple amb la mediana de l'anell
    for k in range(int(RS),1500,4):
        m=(rr>=k)&(rr<k+4); v=C[m]; 
        if np.isnan(v).any(): C[m&np.isnan(C)]=np.nanmedian(v) if np.isfinite(v).any() else 0
    C=np.nan_to_num(C)
else:
    C=np.load(SP+'/corona_hdr_3000.npy').astype(np.float64); C[rr<RS]=0; C=np.nan_to_num(C)
C[rr>=1480]=0
# ROI (2000) ↔ finestra 3000: offset (x: 4377−3876=501, y: 2777−2275=502)
OX,OY=501,502
def a_roi(A3000): return A3000[OY:OY+2000,OX:OX+2000]
rr2=np.hypot(*np.mgrid[0:2000,0:2000][::-1]-np.array([[[998.88]],[[998.41]]]))
def ring_norm(A,mask,step=4):
    out=np.full(A.shape,np.nan); 
    for k in range(0,int(RS)+step,step):
        m=mask&(rr2>=k)&(rr2<k+step)
        if m.sum()>10: out[m]=A[m]/np.mean(A[m])-1
    return out
M=np.load(SP+'/raw_disc_norm_2000.npy').astype(np.float64); Mv=np.isfinite(M)
rgb62,a62=carrega(62); L62=rgb62.mean(-1); v62=np.load(SP+'/roi_L62.npz')['c-1']>30000
LROC_az=ring_norm(gaussian_filter(L62,6),v62&(rr2<RS-8))
rgb30,a30=carrega(30); L30=rgb30.mean(-1); disc=(rr2<RS-8)
LAY_az=ring_norm(gaussian_filter(L30,6),disc)
fit_mask=Mv&(rr2>40)&(rr2<400)&np.isfinite(LROC_az)
Mz=np.where(Mv,M-1,np.nan); Mz=gaussian_filter(np.nan_to_num(Mz),6)   # el RAW és sorollós: suavitzat 6 px
def kernel(d0,q):
    d=np.hypot(*np.mgrid[-N//2:N//2,-N//2:N//2]); K=1/(1+(d/d0)**q); return K/K.sum()
res=[]
for d0 in (30,100,320,1000):
    for q in (1.0,1.5,2.0,2.5,3.0):
        G=fftconvolve(C,kernel(d0,q),mode='same'); Gr=a_roi(G); Gaz=ring_norm(Gr,disc)
        X=np.stack([Gaz[fit_mask],LROC_az[fit_mask],np.ones(fit_mask.sum())],1); y=Mz[fit_mask]
        coef,*_=np.linalg.lstsq(X,y,rcond=None); pred=X@coef; r2=1-np.var(y-pred)/np.var(y)
        coef1,*_=np.linalg.lstsq(X[:,[0,2]],y,rcond=None); r2_1=1-np.var(y-X[:,[0,2]]@coef1)/np.var(y)
        # control: nucli aplicat a la corona girada 90° (vel «equivocat»)
        Gc=ring_norm(a_roi(fftconvolve(np.rot90(C),kernel(d0,q),mode='same')),disc); Xc=np.stack([Gc[fit_mask],LROC_az[fit_mask],np.ones(fit_mask.sum())],1); cc,*_=np.linalg.lstsq(Xc,y,rcond=None); r2c=1-np.var(y-Xc@cc)/np.var(y)
        res.append(dict(d0=d0,q=q,A=float(coef[0]),B=float(coef[1]),R2=float(r2),A_sol=float(coef1[0]),R2_sol=float(r2_1),R2_control_girat=float(r2c),std_Gaz=float(np.nanstd(Gaz[fit_mask]))))
        print(f'd0={d0:5d} q={q:.1f}: A={coef[0]:+.3f} B={coef[1]:+.4f} R²={r2:.3f} | només vel: A={coef1[0]:+.3f} R²={r2_1:.3f} | control girat R²={r2c:.3f} | std Gaz {np.nanstd(Gaz[fit_mask]):.4f}',flush=True)
best=max(res,key=lambda r:r['R2']); print('MILLOR:',best)
json.dump(dict(font=FONT,ajustos=res,millor=best),open(SP+f'/a28_vel2d_{FONT}.json','w'),indent=1)
G=fftconvolve(C,kernel(best['d0'],best['q']),mode='same'); Gr=a_roi(G); Gaz=ring_norm(Gr,disc); np.save(SP+f'/vel_Gaz_{FONT}.npy',np.nan_to_num(Gaz).astype(np.float32)); np.save(SP+f'/vel_G_{FONT}.npy',Gr.astype(np.float32))
# coeficient a la CAPA lunar per anell (regressió LAY_az ~ c·Gaz + b·LROC_az)
bins=np.arange(20,RS-8,20); cs=[]; bs=[]; r2s=[]; corr_abans=[]
for k in bins:
    m=disc&(rr2>=k)&(rr2<k+20)&np.isfinite(LAY_az)&np.isfinite(LROC_az)&np.isfinite(Gaz)
    X=np.stack([Gaz[m],LROC_az[m],np.ones(m.sum())],1); y=LAY_az[m]; coef,*_=np.linalg.lstsq(X,y,rcond=None); cs.append(coef[0]); bs.append(coef[1]); r2s.append(1-np.var(y-X@coef)/np.var(y)); corr_abans.append(np.corrcoef(y,LROC_az[m])[0,1])
cs=np.array(cs); print('coeficient del vel a la capa per anell (r 20…440):',np.round(cs,2)); print('R² per anell:',np.round(r2s,2))
# c(r) suau i positiu (el vel afegeix llum: c ≥ 0), taper a 0 a r > 430
c_s=gaussian_filter(np.clip(cs,0,None),1.5); c_r=np.interp(rr2,bins+10,c_s); taper=np.clip((RS-8-rr2)/24,0,1); c_r=c_r*taper
corr=1.0/(1.0+c_r*np.nan_to_num(Gaz)); corr[rr2>=RS-8]=1.0
rgb_new=np.clip(rgb30*corr[...,None],0,1)
L30n=rgb_new.mean(-1); LAYn_az=ring_norm(gaussian_filter(L30n,6),disc)
corr_despres=[]
for k in bins:
    m=disc&(rr2>=k)&(rr2<k+20)&np.isfinite(LAYn_az)&np.isfinite(LROC_az); corr_despres.append(np.corrcoef(LAYn_az[m],LROC_az[m])[0,1])
print('correlació capa~LROC per anell ABANS :',np.round(corr_abans,2)); print('correlació capa~LROC per anell DESPRÉS:',np.round(corr_despres,2))
# la taca (marca 7)
m7=np.load(SP+'/marques_218.npz'); Mk=np.zeros((2000,2000),np.float32); mx,my=int(m7['x0'])-4377,int(m7['y0'])-2777; Mk[my:my+m7['A'].shape[0],mx:mx+m7['A'].shape[1]]=m7['A']/65535
R7=np.zeros((2000,2000),bool); R7[3896-2777:4137-2777,5224-4377:5447-4377]=Mk[3896-2777:4137-2777,5224-4377:5447-4377]>0.2
yb,xb=np.nonzero(R7); rb=np.hypot(xb-998.88,yb-998.41); anell=(rr2>=rb.min()-10)&(rr2<=rb.max()+10)&(~R7)&disc
for nom,LL in (('abans',L30),('després',L30n)): print(f'taca {nom}: dins {LL[R7].mean():.4f} anell {LL[anell].mean():.4f} → {100*(1-LL[R7].mean()/LL[anell].mean()):.1f} % sota l\'anell')
print('correcció: factor mín %.3f màx %.3f; píxels amb |canvi|>1 %%: %d'%(corr.min(),corr.max(),int((np.abs(corr-1)>0.01).sum())))
d30=np.load(SP+'/roi_L30_v70.npz'); out={k:d30[k] for k in d30.files}
for c,key in enumerate(('c0','c1','c2')): out[key]=(rgb_new[...,c]*65535+.5).astype(np.uint16)
np.savez_compressed(SP+f'/roi_L30_v71_{FONT}.npz',**out); np.save(SP+f'/vel_corr_{FONT}.npy',corr.astype(np.float32))
json.dump(dict(font=FONT,millor=best,c_per_anell=[float(x) for x in cs],r2_per_anell=[float(x) for x in r2s],corr_lroc_abans=[float(x) for x in corr_abans],corr_lroc_despres=[float(x) for x in corr_despres]),open(SP+f'/a28_capa_{FONT}.json','w'),indent=1)
# vistes: capa abans | capa després | LROC (passa-banda 6–60 px normalitzat, mateix estirament) i la taca
from PIL import Image
def pb(A,mask): h=gaussian_filter(A,3)-gaussian_filter(A,60); s=np.nanstd(h[mask]); v=np.clip(0.5+h/(4*s),0,1); v[~mask]=0.15; return v
pan=np.concatenate([pb(L30,disc),pb(L30n,disc),pb(L62,v62&disc)],1); Image.fromarray(np.uint8(pan*255)).save(SP+f'/v_A28_abans_despres_lroc_{FONT}.png')
lin=lambda A: np.clip((A-np.percentile(A[disc],1))/(np.percentile(A[disc],99.5)-np.percentile(A[disc],1)),0,1)
pan2=np.concatenate([lin(L30),lin(L30n),np.clip(c_r*np.nan_to_num(Gaz)*5+0.5,0,1)],1); Image.fromarray(np.uint8(pan2*255)).save(SP+f'/v_A28_lineal_{FONT}.png'); print('fet')
