"""C6: capa lunar V73 = V72 + (a) vora fosca als últims px de la cobertura (RGB × rampa, alfa intacta) perquè la barreja amb el taronja no dessaturi; (b) contrast d'albedo al voltant de la mitjana per anell: L' = m + k·(L − m), k tal que el pendent respecte de la LROC passi de 0,15 a ≈0,5 (meitat del contrast estirat de la LROC, ≈ albedo físic), r < 440 amb taper. Mesures: to de la transició al limbe (B/G per d), pendent, soroll 4–8 px, mitjana per anell."""
import sys, json, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'; S3='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
sys.path.insert(0,NEW)
import compo71; from compo71 import *
from scipy.ndimage import gaussian_filter, gaussian_filter1d, map_coordinates
CX,CY,RS=998.88,998.41,456.0; Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY); az=np.rad2deg(np.arctan2(-(Y-CY),X-CX))%360
d30=np.load(NEW+'/roi72_L30.npz'); rgb=np.dstack([d30['c0'],d30['c1'],d30['c2']]).astype(np.float64)/65535; A=d30['c-1'].astype(np.float64)/65535; M=d30['c-2'].astype(np.float64)/65535; cov=A*M
# vora de la cobertura (50 %) per θ, i distància cap endins
TH=np.deg2rad(np.arange(0,360,0.25)); RR=np.arange(430,480,0.25); xs=CX+RR[None,:]*np.cos(TH[:,None]); ys=CY-RR[None,:]*np.sin(TH[:,None])
P=map_coordinates(cov,[ys.ravel(),xs.ravel()],order=1).reshape(len(TH),len(RR)); Redge=np.full(len(TH),np.nan)
for i in range(len(TH)):
    j=np.nonzero(np.diff(np.sign(P[i]-0.5))!=0)[0]
    if len(j): k=j[-1]; Redge[i]=RR[k]+(0.5-P[i][k])/(P[i][k+1]-P[i][k]+1e-9)*0.25
ok=np.isfinite(Redge); Redge[~ok]=np.interp(np.nonzero(~ok)[0],np.nonzero(ok)[0],Redge[ok]); Redge=gaussian_filter1d(Redge,4,mode='wrap')
ia=np.clip((az/0.25).astype(int),0,len(TH)-1); din=Redge[ia]-rr   # >0 cap endins
# (a) vora fosca: factor 0,12 a la vora (din ≤ 0) → 1 a din ≥ 6 (smoothstep)
t=np.clip(din/6,0,1); fosc=0.12+0.88*t*t*(3-2*t)
# (b) contrast d'albedo: mitjana per anell m(r) (suau), k=3.3, taper 400→440
L=rgb.mean(-1); disc=rr<RS-6
m_r=np.zeros(2000); rad=np.arange(0,470,1.0); prof=np.array([L[disc&(rr>=k)&(rr<k+2)].mean() if (disc&(rr>=k)&(rr<k+2)).sum()>10 else np.nan for k in rad])
okp=np.isfinite(prof); prof[~okp]=np.interp(rad[~okp],rad[okp],prof[okp]); prof=gaussian_filter1d(prof,6); m_pix=np.interp(rr,rad,prof)
k=2.5; kt=1+(k-1)*np.clip((440-rr)/40,0,1)   # k a r ≤ 400, 1 a r ≥ 440
Lnew=m_pix+kt*(L-m_pix); gain=np.where(L>1e-4,Lnew/np.maximum(L,1e-4),1.0); gain=np.clip(gain,0.05,6.0)
rgb_new=np.clip(rgb*gain[...,None]*fosc[...,None],0,1)
# mesures
L62=np.dstack([np.load(NEW+'/roi71_L62.npz')[c] for c in ('c0','c1','c2')]).astype(np.float64).mean(-1)/65535; v62=np.load(NEW+'/roi71_L62.npz')['c-1']>30000
def ring_norm(Aa,mask,step=4):
    out=np.full(Aa.shape,np.nan)
    for kk in range(0,int(RS)+step,step):
        mm=mask&(rr>=kk)&(rr<kk+step)
        if mm.sum()>10: out[mm]=Aa[mm]/np.mean(Aa[mm])-1
    return out
mm=disc&v62&(rr<RS-40); Ln=rgb_new.mean(-1)
for nom,LL in (('V72',L),('V73',Ln)):
    s,b=np.polyfit(ring_norm(gaussian_filter(L62,12),disc&v62)[mm],ring_norm(gaussian_filter(LL,12),disc)[mm],1); b48=gaussian_filter(LL,4)-gaussian_filter(LL,8)
    print(f'{nom}: pendent vs LROC {s:.3f} · soroll 4–8 px rms {b48[rr<400].std()*1e4:.1f}e-4 · mitjana per anell r100/300/430: {LL[disc&(rr>=100)&(rr<120)].mean():.4f}/{LL[disc&(rr>=300)&(rr<320)].mean():.4f}/{LL[disc&(rr>=430)&(rr<436)].mean():.4f} · mín {LL[disc].min():.4f} · p0,5 {np.percentile(LL[disc],0.5):.4f}')
# transició al limbe: compost sense filtres, B/G per d (abans/després), sectors E/N/S
compo71.OVERRIDE.clear()
for lid in (3,55,56,76,96,204): compo71.OVERRIDE[lid]=NEW+f'/roi72_L{lid}.npz'
compo71.OVERRIDE[30]=NEW+'/roi72_L30.npz'; Cb,ab=recompon(exclou=(219,220,41,42,47,49,51,53,45,46,55,56))
out={kk:d30[kk] for kk in d30.files}
for c,key in enumerate(('c0','c1','c2')): out[key]=(rgb_new[...,c]*65535+.5).astype(np.uint16)
np.savez_compressed(S3+'/roi73_L30.npz',**out); compo71.OVERRIDE[30]=S3+'/roi73_L30.npz'; Ca,aa=recompon(exclou=(219,220,41,42,47,49,51,53,45,46,55,56))
D=np.arange(-4,8,1.0)
def polar_d(F,Re): xs2=CX+(Re[:,None]+D[None,:])*np.cos(TH[:,None]); ys2=CY-(Re[:,None]+D[None,:])*np.sin(TH[:,None]); return map_coordinates(F,[ys2.ravel(),xs2.ravel()],order=1).reshape(len(TH),len(D))
for nom,C in (('V72',Cb),('V73',Ca)):
    bg=polar_d(C[...,2]/np.maximum(C[...,1],1e-4),Redge); rg=polar_d(C[...,0]/np.maximum(C[...,1],1e-4),Redge); Lc=polar_d(C.mean(-1),Redge)
    print(f'{nom} transició (d des de la vora lunar, −4 dins … +7 fora): B/G '+' '.join(f'{x:4.2f}' for x in np.median(bg,0))+' · R/G '+' '.join(f'{x:4.2f}' for x in np.median(rg,0))+' · L '+' '.join(f'{x:4.2f}' for x in np.median(Lc,0)))
np.savez_compressed(S3+'/roi73_compost_sensefiltres.npz',C=(np.clip(Ca,0,1)*65535+.5).astype(np.uint16),a=(np.clip(aa,0,1)*65535+.5).astype(np.uint16))
# compost complet V73 i dentat
compo71.OVERRIDE[30]=S3+'/roi73_L30.npz'; Cf,af=recompon(exclou=(219,220)); np.savez_compressed(S3+'/roi73_compost.npz',C=(np.clip(Cf,0,1)*65535+.5).astype(np.uint16),a=(np.clip(af,0,1)*65535+.5).astype(np.uint16))
F71=np.load(NEW+'/roi71_recomp.npz'); C71=F71['C'].astype(np.float32)/65535; a71=F71['a'].astype(np.float32)/65535
def vora(C,a):
    Lq=(C*a[...,None]).mean(-1); Pq=map_coordinates(Lq,[ys.ravel(),xs.ravel()],order=1).reshape(len(TH),len(RR)); lo=np.median(Pq[:,RR<440],1); hi=np.median(Pq[:,RR>470],1); mid=(lo+hi)/2; o=np.full(len(TH),np.nan)
    for i in range(len(TH)):
        j=np.nonzero(np.diff(np.sign(Pq[i]-mid[i]))!=0)[0]
        if len(j): kq=j[0]; o[i]=RR[kq]+(mid[i]-Pq[i][kq])/(Pq[i][kq+1]-Pq[i][kq]+1e-9)*0.25
    okq=np.isfinite(o); o[~okq]=np.interp(np.nonzero(~okq)[0],np.nonzero(okq)[0],o[okq]); return o
for nom,(C,a) in (('V71 Pere',(C71,a71)),('V73',(Cf,af))):
    e=vora(C,a); hp=e-gaussian_filter1d(e,4,mode='wrap'); sec=(np.rad2deg(TH)//10).astype(int); s=[float(np.std(hp[sec==q])) for q in range(36)]; print(f'{nom}: dentat 60–120 {np.mean(s[6:12]):.3f} · 270–300 {np.mean(s[27:30]):.3f} · 150–210 {np.mean(s[15:21]):.3f}')
print('píxels canviats a la capa 30:',int((np.abs(rgb_new-rgb).max(-1)>1/65535).sum()),'· factor vora mín %.2f · guany contrast mín %.2f màx %.2f'%(fosc[rr<RS].min(),gain[rr<400].min(),gain[rr<400].max()))
