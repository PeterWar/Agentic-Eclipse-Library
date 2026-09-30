import rawpy, numpy as np, os, sys, pickle
from astropy.stats import SigmaClip
from photutils.background import Background2D, MedianBackground
from photutils.detection import DAOStarFinder
from scipy import ndimage

D="/Users/USUARI/Desktop/Eclipse 2026/300mm/"
FR=[('DSC06984',2.0),('DSC06985',1.0),('DSC06987',8.0),('DSC06988',1.0),
    ('DSC06991',1.0),('DSC06993',8.0),('DSC06996',2.0),('DSC06999',2.0)]
PED=512.0
md={e:np.load(f"masterdark_{int(e)}s.npy") for e in (1.0,2.0,8.0)}

def green_full(v, col):
    """Full-res green: true G samples kept, R/B sites = mean of 4 orthogonal G neighbours."""
    g=(col==1)|(col==3)
    G=np.where(g, v, 0.0).astype(np.float32)
    W=g.astype(np.float32)
    s=np.zeros_like(G); n=np.zeros_like(W)
    for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
        s+=np.roll(np.roll(G,dy,0),dx,1); n+=np.roll(np.roll(W,dy,0),dx,1)
    interp=np.divide(s,np.maximum(n,1))
    return np.where(g, v, interp).astype(np.float32), g

results={}
for name,exp in FR:
    with rawpy.imread(D+name+".ARW") as r:
        raw=r.raw_image_visible.astype(np.float32); col=r.raw_colors_visible
    sig=raw-md[exp]                      # removes pedestal + dark current
    Gi,gmask=green_full(sig,col)
    bkg=Background2D(Gi,(64,64),filter_size=(5,5),
                     sigma_clip=SigmaClip(sigma=3.0),bkg_estimator=MedianBackground(),
                     exclude_percentile=20.0)
    res=Gi-bkg.background
    snr=res/np.maximum(bkg.background_rms,1e-3)
    # masks: near-saturation (dilated), borders
    hot=(raw>=15800)
    hot=ndimage.binary_dilation(hot,iterations=6)
    snr[hot]=0.0
    snr[:32,:]=0; snr[-32:,:]=0; snr[:,:32]=0; snr[:,-32:]=0
    dao=DAOStarFinder(fwhm=3.0,threshold=4.0,sharplo=0.05,sharphi=1.2,roundlo=-1.0,roundhi=1.0)
    t=dao(snr)
    print(f"{name} exp={exp}s  bkg_med={np.median(bkg.background):.0f} rms_med={np.median(bkg.background_rms):.1f} "
          f"masked={hot.sum()/hot.size*100:.1f}%  raw_detections={0 if t is None else len(t)}")
    sys.stdout.flush()
    np.save(f"res_{name}.npy",res); np.save(f"rms_{name}.npy",bkg.background_rms.astype(np.float32))
    np.save(f"bkg_{name}.npy",bkg.background.astype(np.float32))
    results[name]=dict(exp=exp,tab=None if t is None else
        np.array([t['xcentroid'],t['ycentroid'],t['peak'],t['flux'],t['sharpness'],t['roundness1'],t['roundness2']]).T)
pickle.dump(results,open("det_raw.pkl","wb"))
