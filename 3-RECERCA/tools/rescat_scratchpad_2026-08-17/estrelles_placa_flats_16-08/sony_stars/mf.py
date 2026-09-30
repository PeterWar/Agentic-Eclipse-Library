import rawpy, numpy as np, pickle, sys
from astropy.stats import SigmaClip
from photutils.background import Background2D, MedianBackground
from scipy import ndimage
D="/Users/USUARI/Desktop/Eclipse 2026/300mm/"
GAIN=3.323
def prep(name,exp,md):
    with rawpy.imread(D+name+".ARW") as r:
        raw=r.raw_image_visible.astype(np.float32); col=r.raw_colors_visible
    sig=raw-md
    g=((col==1)|(col==3))
    # smooth background from green pixels only, via block medians
    Gm=np.where(g,sig,np.nan)
    bkg=Background2D(sig,(64,64),filter_size=(5,5),sigma_clip=SigmaClip(sigma=3.0),
                     bkg_estimator=MedianBackground(),exclude_percentile=20.0).background
    res=(sig-bkg).astype(np.float32)
    var=(np.maximum(bkg,1.0)/GAIN).astype(np.float32)      # pure shot noise, ADU^2
    valid=g & (raw<15600)
    bad=ndimage.binary_dilation(raw>=15600,iterations=8)
    valid&=~bad
    valid[:40]=False; valid[-40:]=False; valid[:,:40]=False; valid[:,-40:]=False
    return res,var,valid,bkg,raw,col

def mfilter(res,var,valid,sg):
    n=int(np.ceil(4*sg)); y,x=np.mgrid[-n:n+1,-n:n+1]
    K=np.exp(-(x*x+y*y)/(2*sg*sg)).astype(np.float32)
    w=np.where(valid,1.0/var,0.0).astype(np.float32)
    d=np.where(valid,res,0.0).astype(np.float32)*w
    num=ndimage.convolve(d,K,mode='constant')
    den=ndimage.convolve(w,(K*K).astype(np.float32),mode='constant')
    snr=np.where(den>0,num/np.sqrt(np.maximum(den,1e-12)),0.0)
    return snr.astype(np.float32)

name,exp=sys.argv[1],float(sys.argv[2])
md=np.load(f"masterdark_{int(exp)}s.npy")
res,var,valid,bkg,raw,col=prep(name,exp,md)
print(f"{name}: valid={valid.sum()/valid.size*100:.1f}%  bkg_med={np.median(bkg):.0f} sigma_pred={np.sqrt(np.median(bkg)/GAIN):.2f} ADU")
for sg in (0.7,1.0,1.3,1.7,2.2,3.0):
    snr=mfilter(res,var,valid,sg)
    s=snr[valid]
    # noise sanity: sigma of the SNR map should be ~1 if model is right
    q=np.percentile(s,[0.135,15.87,50,84.13,99.865])
    npk=int(((snr>5)&(snr==ndimage.maximum_filter(snr,7))).sum())
    print(f"  sig={sg:4.1f}  SNRmap: med={q[2]:+.2f} sig_lo={q[2]-q[1]:.2f} sig_hi={q[3]-q[2]:.2f} max={s.max():.1f}  peaks>5sig={npk}")
    np.save(f"snr_{name}_{sg}.npy",snr) if sg in (1.3,) else None
np.save(f"res2_{name}.npy",res); np.save(f"var2_{name}.npy",var); np.save(f"valid_{name}.npy",valid)
