import rawpy, numpy as np, pickle, sys
from scipy import ndimage
D="/Users/USUARI/Desktop/Eclipse 2026/300mm/"
GAIN=3.323
EXP={'DSC06984':2.0,'DSC06985':1.0,'DSC06987':8.0,'DSC06988':1.0,
     'DSC06991':1.0,'DSC06993':8.0,'DSC06996':2.0,'DSC06999':2.0}
OFF=pickle.load(open("offsets3.pkl","rb"))['off']
SI=0.6
t=np.arange(-2,3); k=np.exp(-t*t/(2*SI*SI))
def sep(a,kk): return ndimage.convolve1d(ndimage.convolve1d(a,kk.astype(np.float32),0,mode='constant'),kk.astype(np.float32),1,mode='constant')
ACC=None
for n,e in EXP.items():
    md=np.load(f"masterdark_{int(e)}s.npy"); bkg=np.load(f"bkg_{n}.npy")
    with rawpy.imread(D+n+".ARW") as r:
        raw=r.raw_image_visible.astype(np.float32); col=r.raw_colors_visible
    g=((col==1)|(col==3))
    res=(raw-md-bkg).astype(np.float32)
    valid=g&(raw<15600)&(~ndimage.binary_dilation(raw>=15600,iterations=8))
    valid[:40]=False; valid[-40:]=False; valid[:,:40]=False; valid[:,-40:]=False
    v=valid.astype(np.float32)
    I=sep(np.where(valid,res,0.0).astype(np.float32),k)/np.maximum(sep(v,k),1e-6)/e   # ADU/s, gap-filled
    W=(sep(v,k)>0.05).astype(np.float32)*(e*e/np.maximum(np.median(bkg[valid])/GAIN,1e-6))
    dx,dy=OFF[n]
    if abs(dx)+abs(dy)>0:
        I=ndimage.shift(I,(-dy,-dx),order=1,mode='constant',cval=0.0)
        W=ndimage.shift(W,(-dy,-dx),order=1,mode='constant',cval=0.0)
    if ACC is None: ACC=np.zeros_like(I); WT=np.zeros_like(W)
    ACC+=I*W; WT+=W
    print("img-stacked",n); sys.stdout.flush()
    del raw,res,valid,v,I,W,bkg
IMG=np.where(WT>0,ACC/np.maximum(WT,1e-20),0.0).astype(np.float32)
np.save("IMG.npy",IMG); np.save("WT.npy",WT.astype(np.float32))
print("IMG done", IMG.shape, "median",np.median(IMG[WT>0]))
