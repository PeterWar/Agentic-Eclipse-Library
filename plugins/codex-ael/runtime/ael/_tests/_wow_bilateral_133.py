"""WOW bilateral as it was up to 1.3.4 (range weights from the data being decomposed), kept only as the negative control
of the tests of issue #4. Not part of the public API."""
import numpy as np
from ael import filters as F


def wow_bilateral(img,valid,*,n_scales=6,noise_floor=3):
    """B3 starlet with bilateral range weights and symmetric observed pairs.

    Outside-image taps are absent. No reflected border and no copied missing
    pixels. Whitening is regularised by measured local noise at every scale.

    Known limitation (issue #4): the range weights are computed from the data being decomposed, so faint fine detail
    next to stronger structure can come out with the opposite sign. On real 2026 data, with two independent
    half-stacks (the layer of one against the band-pass of the other), its fine detail (1.5–6 px) correlated at only
    0.08–0.20 with the data's own, with 38–46 % of the clear detail inverted; Edu (@edu27) measured the same on his own
    frames. It is no longer a default layer (since 1.3.4); :func:`wow_measured` is.
    """
    a=np.asarray(img,np.float32); m=valid & np.isfinite(a)
    c=np.where(m,a,0); out=np.zeros_like(c)
    noise=np.nan_to_num(F.noise_map(a,m),nan=0)
    h,w=a.shape; kernel=np.array([1,4,6,4,1])/16
    def shifted(z,dy,dx):
        dest=np.zeros_like(z)
        if abs(dy)>=h or abs(dx)>=w: return dest
        yd=slice(max(0,-dy),min(h,h-dy)); xd=slice(max(0,-dx),min(w,w-dx))
        ys=slice(max(0,dy),min(h,h+dy)); xs=slice(max(0,dx),min(w,w+dx))
        dest[yd,xd]=z[ys,xs]
        return dest
    for j in range(n_scales):
        step=2**j
        _,sd=F.local_mean_std(np.where(m,c,np.nan),m,max(1,step),min_support=.01)
        variance=np.maximum(np.nan_to_num(sd)**2,noise**2+1e-12)
        num=np.zeros_like(c); den=np.zeros_like(c)
        for dy in range(-2,3):
            for dx in range(-2,3):
                pair=m & shifted(m,dy*step,dx*step) & shifted(m,-dy*step,-dx*step)
                v=shifted(c,dy*step,dx*step)
                wt=kernel[dy+2]*kernel[dx+2]*pair*np.exp(-.5*(v-c)**2/variance)
                num+=wt*(v-c); den+=wt
        nxt=c+num/np.maximum(den,1e-12)
        detail=c-nxt
        power=F.normalized_gaussian(np.where(m,detail**2,np.nan),m,max(1,2*step),min_support=.01)
        factor=F.STARLET_NOISE[min(j,len(F.STARLET_NOISE)-1)]
        scale=detail/np.sqrt(np.maximum(np.nan_to_num(power),0)+(noise_floor*noise*factor)**2+1e-12)
        # Remove the smooth range-weight bias inside each coarse-scale operator.
        if j>=3:
            scale-=np.nan_to_num(F.normalized_gaussian(np.where(m,scale,np.nan),m,4*step,min_support=.01))
        out+=scale; c=np.where(m,nxt,0)
    return np.where(m,out,np.nan).astype(np.float32)
