"""A29c: amplitud final del vel per anell: k(r) tal que corr(residu, Gaz) = corr(LROC, Gaz) en holdout (l'albedo real anticorrela amb el vel; LROC és jutge). Capa corregida final → roi_L30_v71.npz."""
import sys, json, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
from scipy.ndimage import gaussian_filter
from PIL import Image
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
FONT=sys.argv[1] if len(sys.argv)>1 else 'base'
RS=456.0; Y,X=np.mgrid[0:2000,0:2000]; rr2=np.hypot(X-998.88,Y-998.41); az=np.rad2deg(np.arctan2(-(Y-998.41),X-998.88))%360; disc=rr2<RS-8; sec=(az//10).astype(int); parell=sec%2==0
def ring_norm(A,mask,step=4):
    out=np.full(A.shape,np.nan)
    for k in range(0,int(RS)+step,step):
        m=mask&(rr2>=k)&(rr2<k+step)
        if m.sum()>10: out[m]=A[m]/np.mean(A[m])-1
    return out
Gaz=np.nan_to_num(np.load(SP+f'/vel_Gaz_{FONT}.npy').astype(np.float64)); rgb30,_=carrega(30); L30=rgb30.mean(-1); LAY=ring_norm(gaussian_filter(L30,6),disc)
rgb62,_=carrega(62); L62=rgb62.mean(-1); v62=np.load(SP+'/roi_L62.npz')['c-1']>30000; LROC=ring_norm(gaussian_filter(L62,6),v62&disc)
bins=np.arange(20,RS-8,20); c_lroc=np.array(json.load(open(SP+f'/a28_capa_{FONT}.json'))['c_per_anell'])
ks=np.arange(0,2.01,0.1); kfin=[]; obj=[]
for i,k in enumerate(bins):
    m=disc&(rr2>=k)&(rr2<k+20)&np.isfinite(LAY)&np.isfinite(LROC)&~parell; tgt=np.corrcoef(LROC[m],Gaz[m])[0,1]
    cc=[]
    for kf in ks:
        c=kf*max(c_lroc[i],0); Ln=ring_norm(gaussian_filter(L30/(1+c*Gaz),6),disc); cc.append(np.corrcoef(Ln[m],Gaz[m])[0,1])
    cc=np.array(cc); j=int(np.argmin(np.abs(cc-tgt))); kfin.append(ks[j]); obj.append((int(k),round(float(tgt),2),round(float(ks[j]),1),round(float(cc[j]),2)))
print('per anell (r, corr LROC~Gaz objectiu, k triat, corr residu~Gaz):',obj)
kfin=np.array(kfin); kf_s=gaussian_filter(np.clip(kfin,0.6,1.6),1.0); print('k suau per anell:',np.round(kf_s,2))
c_r=np.interp(rr2,bins+10,gaussian_filter(np.clip(c_lroc,0,None),1.5)*kf_s); taper=np.clip((RS-8-rr2)/24,0,1); c_r=c_r*taper
corr=1.0/(1.0+c_r*Gaz); corr[rr2>=RS-8]=1.0
rgb_new=np.clip(rgb30*corr[...,None],0,1); Ln=rgb_new.mean(-1); LAYn=ring_norm(gaussian_filter(Ln,6),disc)
cl=[]; 
for k in bins:
    m=disc&(rr2>=k)&(rr2<k+20)&np.isfinite(LAYn)&np.isfinite(LROC)&~parell; cl.append(round(float(np.corrcoef(LAYn[m],LROC[m])[0,1]),2))
print('correlació capa~LROC (holdout) DESPRÉS per anell:',cl)
m7=np.load(SP+'/marques_218.npz'); Mk=np.zeros((2000,2000),np.float32); mx,my=int(m7['x0'])-4377,int(m7['y0'])-2777; Mk[my:my+m7['A'].shape[0],mx:mx+m7['A'].shape[1]]=m7['A']/65535
R7=np.zeros((2000,2000),bool); R7[3896-2777:4137-2777,5224-4377:5447-4377]=Mk[3896-2777:4137-2777,5224-4377:5447-4377]>0.2
yb,xb=np.nonzero(R7); rb=np.hypot(xb-998.88,yb-998.41); anell=(rr2>=rb.min()-10)&(rr2<=rb.max()+10)&(~R7)&disc
print('taca: abans %.1f %% sota l\'anell → després %.1f %% ; LROC a la taca vs anell: %.1f %%'%(100*(1-L30[R7].mean()/L30[anell].mean()),100*(1-Ln[R7].mean()/Ln[anell].mean()),100*(1-L62[R7&v62].mean()/L62[anell&v62].mean())))
print('factor: mín %.3f màx %.3f'%(corr.min(),corr.max()))
d30=np.load(SP+'/roi_L30_v71.npz'); out={k:d30[k] for k in d30.files}   # màscara de a16d (vora de Pere intacta)
for c,key in enumerate(('c0','c1','c2')): out[key]=(rgb_new[...,c]*65535+.5).astype(np.uint16)
np.savez_compressed(SP+'/roi_L30_v71.npz',**out); np.save(SP+f'/vel_corr_final_{FONT}.npy',corr.astype(np.float32))
json.dump(dict(k_per_anell=[float(x) for x in kf_s],c_final=[float(x) for x in gaussian_filter(np.clip(c_lroc,0,None),1.5)*kf_s],corr_lroc_holdout_despres=cl,objectiu=obj,factor_min=float(corr.min()),factor_max=float(corr.max())),open(SP+f'/a29c_amplitud_{FONT}.json','w'),indent=1)
lin=lambda A: np.clip((A-np.percentile(A[disc],1))/(np.percentile(A[disc],99.5)-np.percentile(A[disc],1)),0,1)
pan=np.concatenate([lin(L30),lin(Ln),lin(np.where(v62,L62,np.nan)) if False else np.clip((L62-np.percentile(L62[v62&disc],1))/(np.percentile(L62[v62&disc],99.5)-np.percentile(L62[v62&disc],1)),0,1)*(v62&disc)],1)
Image.fromarray(np.uint8(pan*255)).save(SP+f'/v_A29c_lluna_abans_despres_lroc_{FONT}.png'); print('fet')
