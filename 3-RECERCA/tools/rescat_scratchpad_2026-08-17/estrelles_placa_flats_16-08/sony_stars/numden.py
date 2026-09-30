import rawpy, numpy as np, pickle, sys
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
pk={}
for name,exp in FR:
    md=np.load(f"masterdark_{int(exp)}s.npy")
    with rawpy.imread(D+name+".ARW") as r:
        raw=r.raw_image_visible.astype(np.float32); col=r.raw_colors_visible
    sig=raw-md; Gi,g=green_interp(sig,col)
    bkg=Background2D(Gi,(32,32),filter_size=(3,3),sigma_clip=SigmaClip(sigma=3.0),
                     bkg_estimator=MedianBackground(),exclude_percentile=30.0).background
    res=(sig-bkg).astype(np.float32); var=(np.maximum(bkg,1.0)/GAIN).astype(np.float32)
    valid=g&(raw<15600)&(~ndimage.binary_dilation(raw>=15600,iterations=8))
    valid[:40]=False; valid[-40:]=False; valid[:,:40]=False; valid[:,-40:]=False
    w=np.where(valid,1.0/var,0.0).astype(np.float32); d=np.where(valid,res,0.0).astype(np.float32)*w
    num=ndimage.convolve(d,K,mode='constant').astype(np.float32)
    den=ndimage.convolve(w,(K*K).astype(np.float32),mode='constant').astype(np.float32)
    snr=np.where(den>0,num/np.sqrt(np.maximum(den,1e-12)),0.0).astype(np.float32)
    np.save(f"num_{name}.npy",num); np.save(f"den_{name}.npy",den)
    np.save(f"bkg_{name}.npy",bkg); np.save(f"validbits_{name}.npy",np.packbits(valid))
    lm=(snr>4.5)&(snr==ndimage.maximum_filter(snr,9))
    ys,xs=np.nonzero(lm)
    # sub-pixel by parabolic fit on snr
    fx=np.zeros(len(xs)); fy=np.zeros(len(ys))
    for i,(Y,X) in enumerate(zip(ys,xs)):
        a=snr[Y,X-1];b=snr[Y,X];c=snr[Y,X+1]; den_=(a-2*b+c); fx[i]=0.5*(a-c)/den_ if den_!=0 else 0
        a=snr[Y-1,X];c=snr[Y+1,X]; den_=(a-2*b+c); fy[i]=0.5*(a-c)/den_ if den_!=0 else 0
    fx=np.clip(fx,-1,1); fy=np.clip(fy,-1,1)
    pk[name]=dict(exp=exp,x=xs+fx,y=ys+fy,snr=snr[ys,xs],
                  amp=np.where(den[ys,xs]>0,num[ys,xs]/np.maximum(den[ys,xs],1e-12),0.0),
                  bkg=bkg[ys,xs],ix=xs,iy=ys)
    print(f"{name} {exp}s  peaks={len(xs)}"); sys.stdout.flush()
    del raw,sig,Gi,bkg,res,var,valid,w,d,num,den,snr
pickle.dump(pk,open("peaks2.pkl","wb"))
