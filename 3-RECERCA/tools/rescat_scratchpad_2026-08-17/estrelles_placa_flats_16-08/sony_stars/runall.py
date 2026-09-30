import rawpy, numpy as np, sys, pickle, os
from astropy.stats import SigmaClip
from photutils.background import Background2D, MedianBackground
from scipy import ndimage
D="/Users/USUARI/Desktop/Eclipse 2026/300mm/"
GAIN=3.323; SG=1.3
FR=[('DSC06984',2.0),('DSC06985',1.0),('DSC06987',8.0),('DSC06988',1.0),
    ('DSC06991',1.0),('DSC06993',8.0),('DSC06996',2.0),('DSC06999',2.0)]
def green_interp(sig,col):
    g=((col==1)|(col==3))
    G=np.where(g,sig,0.0).astype(np.float32); W=g.astype(np.float32)
    s=np.zeros_like(G); n=np.zeros_like(W)
    for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
        s+=np.roll(np.roll(G,dy,0),dx,1); n+=np.roll(np.roll(W,dy,0),dx,1)
    return np.where(g,sig,s/np.maximum(n,1)).astype(np.float32), g
n=int(np.ceil(4*SG)); yy,xx=np.mgrid[-n:n+1,-n:n+1]
K=np.exp(-(xx*xx+yy*yy)/(2*SG*SG)).astype(np.float32)
peaks={}
for name,exp in FR:
    md=np.load(f"masterdark_{int(exp)}s.npy")
    with rawpy.imread(D+name+".ARW") as r:
        raw=r.raw_image_visible.astype(np.float32); col=r.raw_colors_visible
    sig=raw-md
    Gi,g=green_interp(sig,col)
    bkg=Background2D(Gi,(32,32),filter_size=(3,3),sigma_clip=SigmaClip(sigma=3.0),
                     bkg_estimator=MedianBackground(),exclude_percentile=30.0).background
    res=(sig-bkg).astype(np.float32); var=(np.maximum(bkg,1.0)/GAIN).astype(np.float32)
    valid=g&(raw<15600)&(~ndimage.binary_dilation(raw>=15600,iterations=8))
    valid[:40]=False; valid[-40:]=False; valid[:,:40]=False; valid[:,-40:]=False
    w=np.where(valid,1.0/var,0.0).astype(np.float32); d=np.where(valid,res,0.0).astype(np.float32)*w
    num=ndimage.convolve(d,K,mode='constant'); den=ndimage.convolve(w,(K*K).astype(np.float32),mode='constant')
    snr=np.where(den>0,num/np.sqrt(np.maximum(den,1e-12)),0.0).astype(np.float32)
    amp=np.where(den>0,num/np.maximum(den,1e-12),0.0).astype(np.float32)   # fitted peak amplitude, ADU
    lm=(snr>4.5)&(snr==ndimage.maximum_filter(snr,9))
    ys,xs=np.nonzero(lm)
    peaks[name]=dict(exp=exp,x=xs.astype(np.float32),y=ys.astype(np.float32),
                     snr=snr[ys,xs],amp=amp[ys,xs],bkg=bkg[ys,xs])
    np.save(f"res_{name}.npy",res); np.save(f"bkg_{name}.npy",bkg); np.save(f"valid_{name}.npy",np.packbits(valid))
    print(f"{name} {exp}s: peaks>4.5sig = {len(xs)}   max={snr.max():.0f}"); sys.stdout.flush()
    del res,var,valid,w,d,num,den,snr,amp,raw,sig,Gi,bkg
pickle.dump(peaks,open("peaks.pkl","wb"))
