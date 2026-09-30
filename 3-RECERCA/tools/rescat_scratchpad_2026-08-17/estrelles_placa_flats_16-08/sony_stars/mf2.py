import rawpy, numpy as np, sys
from astropy.stats import SigmaClip
from photutils.background import Background2D, MedianBackground
from scipy import ndimage
D="/Users/USUARI/Desktop/Eclipse 2026/300mm/"
GAIN=3.323
def green_interp(sig,col):
    g=((col==1)|(col==3))
    G=np.where(g,sig,0.0).astype(np.float32); W=g.astype(np.float32)
    s=np.zeros_like(G); n=np.zeros_like(W)
    for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
        s+=np.roll(np.roll(G,dy,0),dx,1); n+=np.roll(np.roll(W,dy,0),dx,1)
    return np.where(g,sig,s/np.maximum(n,1)).astype(np.float32), g
name,exp,box=sys.argv[1],float(sys.argv[2]),int(sys.argv[3])
md=np.load(f"masterdark_{int(exp)}s.npy")
with rawpy.imread(D+name+".ARW") as r:
    raw=r.raw_image_visible.astype(np.float32); col=r.raw_colors_visible
sig=raw-md
Gi,g=green_interp(sig,col)
b2=Background2D(Gi,(box,box),filter_size=(3,3),sigma_clip=SigmaClip(sigma=3.0),
                bkg_estimator=MedianBackground(),exclude_percentile=30.0)
bkg=b2.background
res=(sig-bkg).astype(np.float32)
var=(np.maximum(bkg,1.0)/GAIN).astype(np.float32)
valid=g&(raw<15600)&(~ndimage.binary_dilation(raw>=15600,iterations=8))
valid[:40]=False; valid[-40:]=False; valid[:,:40]=False; valid[:,-40:]=False
print(f"{name} box={box} valid={valid.sum()/valid.size*100:.1f}% bkg_med={np.median(bkg):.0f} pred_sigma={np.sqrt(np.median(bkg)/GAIN):.2f}")
# raw single-pixel residual sanity in a far corner (low corona)
for lbl,sl in [("TL",(slice(100,700),slice(100,700))),("BR",(slice(-700,-100),slice(-700,-100))),
               ("TR",(slice(100,700),slice(-700,-100)))]:
    m=valid[sl]; rr=res[sl][m]; vv=np.sqrt(var[sl][m])
    q=np.percentile(rr/vv,[15.87,50,84.13])
    print(f"  {lbl}: normalised residual med={q[1]:+.3f} sigma=({q[1]-q[0]:.3f},{q[2]-q[1]:.3f})")
def mfilter(sg):
    n=int(np.ceil(4*sg)); y,x=np.mgrid[-n:n+1,-n:n+1]
    K=np.exp(-(x*x+y*y)/(2*sg*sg)).astype(np.float32)
    w=np.where(valid,1.0/var,0.0).astype(np.float32)
    d=np.where(valid,res,0.0).astype(np.float32)*w
    num=ndimage.convolve(d,K,mode='constant'); den=ndimage.convolve(w,(K*K).astype(np.float32),mode='constant')
    return np.where(den>0,num/np.sqrt(np.maximum(den,1e-12)),0.0).astype(np.float32)
for sg in (0.8,1.1,1.5,2.0):
    s=mfilter(sg); sv=s[valid]
    q=np.percentile(sv,[15.87,50,84.13])
    pk=(s>5)&(s==ndimage.maximum_filter(s,9))&valid
    print(f"  sig={sg:3.1f} SNR med={q[1]:+.2f} sd=({q[1]-q[0]:.2f},{q[2]-q[1]:.2f}) max={sv.max():.1f} peaks>5={pk.sum()} peaks>8={((s>8)&(s==ndimage.maximum_filter(s,9))&valid).sum()}")
    np.save(f"snr_{name}_s{sg}.npy",s)
np.save(f"res_{name}.npy",res); np.save(f"var_{name}.npy",var); np.save(f"valid_{name}.npy",valid); np.save(f"bkg_{name}.npy",bkg)
