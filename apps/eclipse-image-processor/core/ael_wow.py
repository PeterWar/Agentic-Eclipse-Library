"""AEL bilateral WOW. Copyright (c) 2026 Pere Guerra Serra.

Adapted from AEL 1.3.3 filters.py/filterbank.py (MIT; docs/third-party/AEL-MIT.txt).
Signed log-luminance radial residual, observed symmetric starlet pairs, measured
noise regularization and AEL MAD/tanh display encoding. No reflected samples.
"""
from types import SimpleNamespace
import numpy as np
from .ael_achf import normalized_gaussian, radial_log_residual, display_detail
from .cancellation import check_cancelled

STARLET_NOISE = np.array([.8908,.2007,.0856,.0413,.0205,.0103,.0052,.0026,.0013])
_B3 = (1/16,4/16,6/16,4/16,1/16)


def local_mean_std(img, valid, sigma, min_support=.25):
    mu = normalized_gaussian(img, valid, sigma, min_support)
    mask = np.isfinite(mu)
    detail = np.where(mask, np.asarray(img,np.float32)-mu, np.nan)
    variance = normalized_gaussian(detail*detail, mask, sigma, min_support)
    return mu, np.sqrt(np.maximum(variance,0.))


def _atrous_axis(a: np.ndarray, step: int, axis: int) -> np.ndarray:
    """One B3 à-trous pass along ``axis`` with holes of ``step`` and zero outside the array."""
    out = a * _B3[2]
    n = a.shape[axis]
    for k, c in ((1, _B3[1]), (2, _B3[0])):
        s = k * step
        if s >= n:
            continue
        sl_dst = [slice(None)] * a.ndim
        sl_src = [slice(None)] * a.ndim
        sl_dst[axis], sl_src[axis] = slice(s, None), slice(None, n - s)
        out[tuple(sl_dst)] += c * a[tuple(sl_src)]
        sl_dst[axis], sl_src[axis] = slice(None, n - s), slice(s, None)
        out[tuple(sl_dst)] += c * a[tuple(sl_src)]
    return out


def _atrous(a: np.ndarray, step: int) -> np.ndarray:
    return _atrous_axis(_atrous_axis(a, step, 0), step, 1)


def starlet(img: np.ndarray, valid: np.ndarray | None, n_scales: int = 6, min_support: float = 0.2):
    """Masked isotropic undecimated wavelet (starlet, B3 spline) transform.

    Returns ``(details, coarse)`` where ``details[j]`` is scale ``j+1`` (``2**j`` px holes).  With a
    mask, each smoothing is a normalised convolution, so no invalid pixel leaks into the
    coefficients; outside the data every coefficient is ``NaN``.  ``sum(details) + coarse == img`` on
    the valid pixels (exact reconstruction).
    """
    a = np.asarray(img, np.float32)
    m = np.isfinite(a) if valid is None else (valid.astype(bool) & np.isfinite(a))
    mf = m.astype(np.float32)
    c = np.where(m, a, 0.0).astype(np.float32)
    details = []
    for j in range(n_scales):
        check_cancelled()
        step = 2 ** j
        num = _atrous(c * mf, step)
        den = _atrous(mf, step)
        c_next = np.where(den > min_support, num / np.maximum(den, 1e-12), c).astype(np.float32)
        # (where support is too thin the smoothed value is the value itself: detail 0, no invention)
        d = np.where(m, c - c_next, np.nan).astype(np.float32)
        details.append(d)
        c = np.where(m, c_next, 0.0).astype(np.float32)
    coarse = np.where(m, c, np.nan).astype(np.float32)
    return details, coarse


def noise_map(img: np.ndarray, valid: np.ndarray | None, sigma: float = 6.0) -> np.ndarray:
    """Local standard deviation of the white noise, estimated from the finest starlet scale.

    Assumes the optical PSF is at least ~2 px FWHM, so that the finest scale is mostly noise (true for
    well-sampled eclipse data).  Returns a map in the units of ``img``.
    """
    d, _ = starlet(img, valid, n_scales=1)
    w1 = d[0]
    ok = np.isfinite(w1)
    p = normalized_gaussian(np.where(ok, w1 * w1, np.nan), ok, sigma)
    return (np.sqrt(np.maximum(p, 0)) / STARLET_NOISE[0]).astype(np.float32)


def wow_bilateral(img,valid,*,n_scales=6,noise_floor=3):
    """B3 starlet with bilateral range weights and symmetric observed pairs.

    Outside-image taps are absent. No reflected border and no copied missing
    pixels. Whitening is regularised by measured local noise at every scale.
    """
    a=np.asarray(img,np.float32); m=valid & np.isfinite(a)
    c=np.where(m,a,0); out=np.zeros_like(c)
    noise=np.nan_to_num(noise_map(a,m),nan=0)
    h,w=a.shape; kernel=np.array([1,4,6,4,1])/16
    def shifted(z,dy,dx):
        dest=np.zeros_like(z)
        if abs(dy)>=h or abs(dx)>=w: return dest
        yd=slice(max(0,-dy),min(h,h-dy)); xd=slice(max(0,-dx),min(w,w-dx))
        ys=slice(max(0,dy),min(h,h+dy)); xs=slice(max(0,dx),min(w,w+dx))
        dest[yd,xd]=z[ys,xs]
        return dest
    for j in range(n_scales):
        check_cancelled()
        step=2**j
        _,sd=local_mean_std(np.where(m,c,np.nan),m,max(1,step),min_support=.01)
        variance=np.maximum(np.nan_to_num(sd)**2,noise**2+1e-12)
        num=np.zeros_like(c); den=np.zeros_like(c)
        for dy in range(-2,3):
            for dx in range(-2,3):
                check_cancelled()
                pair=m & shifted(m,dy*step,dx*step) & shifted(m,-dy*step,-dx*step)
                v=shifted(c,dy*step,dx*step)
                wt=kernel[dy+2]*kernel[dx+2]*pair*np.exp(-.5*(v-c)**2/variance)
                num+=wt*(v-c); den+=wt
        nxt=c+num/np.maximum(den,1e-12)
        detail=c-nxt
        power=normalized_gaussian(np.where(m,detail**2,np.nan),m,max(1,2*step),min_support=.01)
        factor=STARLET_NOISE[min(j,len(STARLET_NOISE)-1)]
        scale=detail/np.sqrt(np.maximum(np.nan_to_num(power),0)+(noise_floor*noise*factor)**2+1e-12)
        # Remove the smooth range-weight bias inside each coarse-scale operator.
        if j>=3:
            scale-=np.nan_to_num(normalized_gaussian(np.where(m,scale,np.nan),m,4*step,min_support=.01))
        out+=scale; c=np.where(m,nxt,0)
    return np.where(m,out,np.nan).astype(np.float32)

def ael_wow_layer(image, params, valid=None):
    """Encoded Overlay layer. wow_scales is adapted to target resolution upstream."""
    a = np.asarray(image,dtype=np.float32)
    if a.ndim != 2 or not a.size:
        raise ValueError('AEL WOW requires a nonempty 2D image')
    cx,cy,radius = params['sx'],params['sy'],params['sr']
    if not np.isfinite([cx,cy,radius]).all() or radius <= 0:
        raise ValueError('AEL WOW requires finite geometry and positive radius')
    count=params.get('wow_scales',6) or 6
    floor=float(params.get('wow_noise_floor',3.))
    if isinstance(count,bool) or not isinstance(count,(int,np.integer)) or not 1 <= count <= 10:
        raise ValueError('AEL WOW requires 1 to 10 scales')
    if not np.isfinite(floor) or not 0 <= floor <= 10:
        raise ValueError('AEL WOW noise floor must be between 0 and 10')
    mask=np.isfinite(a) & (a>0)
    if valid is not None:
        if np.shape(valid) != a.shape:
            raise ValueError('AEL WOW validity must match image')
        mask &= np.asarray(valid,bool)
    y,x=np.ogrid[:a.shape[0],:a.shape[1]]
    r=np.hypot(x-cx,y-cy).astype(np.float32)
    geometry=SimpleNamespace(radius_map=lambda:r,sun_radius_px=radius)
    check_cancelled()
    residual,info=radial_log_residual(a,mask,geometry)
    detail=wow_bilateral(residual,np.isfinite(residual),n_scales=count,noise_floor=floor)
    encoded,mapping=display_detail(detail,mask)
    return encoded,dict(info,**mapping,operator='AEL bilateral WOW',input='ln L minus radial spline',
                         n_scales=count,noise_floor=floor)
