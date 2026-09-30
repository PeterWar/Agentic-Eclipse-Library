import rawpy, numpy as np, pickle, sys
from scipy import ndimage
D="/Users/USUARI/Desktop/Eclipse 2026/300mm/"
GAIN=3.323
OFF=pickle.load(open("offsets6.pkl","rb"))['off']
USE={'DSC06984':2.0,'DSC06985':1.0,'DSC06987':8.0,
     'DSC06991':1.0,'DSC06993':8.0,'DSC06996':2.0,'DSC06999':2.0}
NUM=None
for n,e in USE.items():
    N=np.load(f"N_{n}.npy"); Dn=np.load(f"D_{n}.npy"); dx,dy=OFF[n]
    if abs(dx)+abs(dy)>0:
        N=ndimage.shift(N,(-dy,-dx),order=1,mode='constant',cval=0.0)
        Dn=ndimage.shift(Dn,(-dy,-dx),order=1,mode='constant',cval=0.0)
    if NUM is None: NUM=np.zeros_like(N); DEN=np.zeros_like(Dn); COV=np.zeros_like(Dn)
    NUM+=N*e; DEN+=Dn*e*e; COV+=(Dn>0)*e; del N,Dn
SNR=np.where(DEN>0,NUM/np.sqrt(np.maximum(DEN,1e-30)),0).astype(np.float32)
np.save("F_SNR.npy",SNR); np.save("F_DEN.npy",DEN.astype(np.float32)); np.save("F_COV.npy",COV.astype(np.float32))
m=DEN>0; q=np.percentile(SNR[m],[15.87,50,84.13])
print(f"FINAL STACK (7 frames, 24 s): SNR med={q[1]:+.3f} sd=({q[1]-q[0]:.3f},{q[2]-q[1]:.3f}) max={SNR[m].max():.0f}")
deep=COV>23.5
print(f"deep area={deep.sum()/1e6:.1f} Mpx ; 1sigma peak amplitude={1/np.sqrt(np.median(DEN[deep])):.3f} ADU/s")
# stacked flux image
SI=0.6; t=np.arange(-2,3); k=np.exp(-t*t/(2*SI*SI))
def sep(a,kk): return ndimage.convolve1d(ndimage.convolve1d(a,kk.astype(np.float32),0,mode='constant'),kk.astype(np.float32),1,mode='constant')
ACC=None
for n,e in USE.items():
    md=np.load(f"masterdark_{int(e)}s.npy"); bkg=np.load(f"bkg_{n}.npy")
    with rawpy.imread(D+n+".ARW") as r:
        raw=r.raw_image_visible.astype(np.float32); col=r.raw_colors_visible
    g=((col==1)|(col==3)); res=(raw-md-bkg).astype(np.float32)
    valid=g&(raw<15600)&(~ndimage.binary_dilation(raw>=15600,iterations=8))
    valid[:40]=False; valid[-40:]=False; valid[:,:40]=False; valid[:,-40:]=False
    v=valid.astype(np.float32); cw=sep(v,k)
    I=sep(np.where(valid,res,0.).astype(np.float32),k)/np.maximum(cw,1e-6)/e
    W=(cw>0.05).astype(np.float32)*(e*e/(np.median(bkg[valid])/GAIN))
    dx,dy=OFF[n]
    if abs(dx)+abs(dy)>0:
        I=ndimage.shift(I,(-dy,-dx),order=1,mode='constant',cval=0.)
        W=ndimage.shift(W,(-dy,-dx),order=1,mode='constant',cval=0.)
    if ACC is None: ACC=np.zeros_like(I); WT=np.zeros_like(W)
    ACC+=I*W; WT+=W; print("img",n); sys.stdout.flush()
    del raw,res,valid,v,I,W,bkg,cw
np.save("F_IMG.npy",np.where(WT>0,ACC/np.maximum(WT,1e-20),0).astype(np.float32))
np.save("F_WT.npy",WT.astype(np.float32))
print("done")
