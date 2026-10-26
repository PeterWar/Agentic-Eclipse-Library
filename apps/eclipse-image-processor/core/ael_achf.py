"""AEL isotropic and angular ACHF variants. Copyright (c) 2026 Pere Guerra Serra.

Adapted from AEL filterbank.py and filters.py (MIT; docs/third-party/AEL-MIT.txt).
Log-luminance radial spline or angular residual, outer Gaussian and AEL
MAD/tanh encoding. Missing/nonpositive samples never enter the operator.
"""
import cv2
import numpy as np
from scipy.interpolate import LSQUnivariateSpline
from types import SimpleNamespace
from .cancellation import check_cancelled

def _blur(a: np.ndarray, sigma: float) -> np.ndarray:
    k = int(2 * np.ceil(4.0 * sigma) + 1)
    return cv2.GaussianBlur(a, (k, k), sigmaX=sigma, sigmaY=sigma, borderType=cv2.BORDER_CONSTANT)


def gaussian(a: np.ndarray, sigma: float) -> np.ndarray:
    """Gaussian blur with zero borders; large sigmas are computed on a decimated grid (fast, accurate
    for smooth backgrounds).  Input must be finite."""
    a = np.ascontiguousarray(a, dtype=np.float32)
    if sigma <= 0:
        return a.copy()
    if sigma < 12:
        return _blur(a, sigma)
    f = int(2 ** np.floor(np.log2(sigma / 4.0)))
    h, w = a.shape
    H, W = -(-h // f) * f, -(-w // f) * f
    p = np.zeros((H, W), np.float32)
    p[:h, :w] = a
    small = p.reshape(H // f, f, W // f, f).mean(axis=(1, 3))
    s_small = np.sqrt(max(sigma ** 2 - (f ** 2 - 1) / 12.0, 1e-6)) / f
    small = _blur(small, s_small)
    big = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)
    return big[:h, :w]


def normalized_gaussian(img: np.ndarray, valid: np.ndarray | None, sigma: float,
                        min_support: float = 0.25, return_support: bool = False):
    """Normalised-convolution Gaussian: mean of the *observed* pixels around each pixel.

    ``NaN`` where the local fraction of data (``G*m``) is below ``min_support`` or where the pixel
    itself has no data.
    """
    a = np.asarray(img, dtype=np.float32)
    m = np.isfinite(a) if valid is None else (valid.astype(bool) & np.isfinite(a))
    mf = m.astype(np.float32)
    num = gaussian(np.where(m, a, 0.0).astype(np.float32), sigma)
    den = gaussian(mf, sigma)
    out = np.where(m & (den >= min_support), num / np.maximum(den, 1e-12), np.nan).astype(np.float32)
    return (out, den) if return_support else out


def radial_log_residual(luminance, valid, geometry):
    """Subtract a smooth cubic spline in ln r BEFORE isotropic high-pass.

    Ring medians are observations for a smooth fit, never a stepwise image to
    subtract. An off-centre Moon or a rectangular boundary cannot introduce a
    discontinuity in this profile. No output is produced outside observed data.
    """
    a = np.asarray(luminance, np.float32)
    m = valid & np.isfinite(a) & (a>0)
    r = geometry.radius_map()
    m &= r>0
    if m.sum()<64: raise ValueError('not enough positive observed pixels for radial profile')
    ri = np.floor(r[m]).astype(int)
    order = np.argsort(ri,kind='stable'); cnt = np.bincount(ri); cuts=np.r_[0,np.cumsum(cnt)]
    values=np.log(a[m])[order]
    bins=np.flatnonzero(cnt>=12)
    if len(bins)<8: raise ValueError('radial spline needs at least eight populated annuli')
    med=np.array([np.median(values[cuts[i]:cuts[i+1]]) for i in bins])
    # Use the measured mean ln(r), not ln(bin+.5): exact for power-law nulls even
    # where only a small angular fraction of an annulus is observed.
    lr_values=np.log(r[m].astype(np.float64))[order]
    lr=np.array([np.mean(lr_values[cuts[i]:cuts[i+1]]) for i in bins])
    candidates=np.log(geometry.sun_radius_px*np.array([1.03,1.06,1.10,1.15,1.22,1.32,1.45,1.65,1.95,2.4,3,3.8,4.8,6]))
    knots=[v for v in candidates if lr[3]<v<lr[-4]]
    # Avoid overparameterised/singular splines on small images, preserving a
    # smooth cubic (never falling back to unsmoothed ring medians).
    while True:
        try:
            fit=LSQUnivariateSpline(lr,med,knots,w=np.sqrt(cnt[bins]),k=3)
            break
        except ValueError:
            if not knots: raise
            knots=knots[::2] if len(knots)>1 else []
    ln=np.zeros(a.shape,np.float32); ln[m]=np.log(a[m])
    profile=fit(np.log(np.clip(r,np.exp(lr[0]),np.exp(lr[-1]))))
    out=np.where(m,ln-profile,np.nan).astype(np.float32)
    return out,dict(method='cubic spline in ln r fitted to annular log-luminance medians',
                    knots_rsun=(np.exp(knots)/geometry.sun_radius_px).tolist(),
                    annuli=len(bins),fit_rms=float(np.sqrt(np.mean((med-fit(lr))**2))))


def achf_isotropic(luminance, valid, geometry, *, sigmas=(1,2,4,8,16), outer_sigma=1.5):
    check_cancelled()
    residual, info=radial_log_residual(luminance,valid,geometry)
    m=np.isfinite(residual)
    detail=np.zeros(residual.shape,np.float32)
    for s in sigmas:
        check_cancelled()
        detail += (residual-normalized_gaussian(residual,m,s,min_support=.01))/len(sigmas)
    if outer_sigma:
        detail=normalized_gaussian(detail,m,outer_sigma,min_support=.01)
    detail[~m]=np.nan
    return detail,dict(**info,sigmas_px=list(sigmas),outer_sigma_px=outer_sigma)


def display_detail(detail, valid, *, noise_floor=1e-5):
    good=valid & np.isfinite(detail)
    if not good.any(): raise ValueError('filter produced no observed values')
    median=float(np.median(detail[good]))
    scale=max(float(1.4826*np.median(np.abs(detail[good]-median))),noise_floor)
    return np.where(good,.5+.5*np.tanh(detail/(2.5*scale)),np.nan).astype(np.float32),dict(scale=scale,tanh=2.5)


AEL_PRESETS = {
    'ael_iso_01': dict(sigmas=(2.,4.,8.,16.,32.), outer_sigma=3., strength=10),
    'ael_iso_04': dict(sigmas=(1.,2.,4.,8.,16.), outer_sigma=1.5, strength=10),
    'ael_angular_4': dict(angular_sigma=1., outer_sigma=4., strength=10),
}


def ael_achf_layer(image, cx, cy, radius, valid=None, scale=1.,
                   variant='ael_iso_04', parameters=None):
    """AEL encoded Overlay layer; scales are native pixels times target/full scale."""
    a = np.asarray(image, dtype=np.float32)
    if a.ndim != 2 or not a.size:
        raise ValueError('AEL ACHF needs a nonempty 2D image')
    if not np.isfinite([cx, cy, radius, scale]).all() or radius <= 0 or scale <= 0:
        raise ValueError('AEL ACHF needs finite geometry and positive radius/scale')
    mask = np.isfinite(a) & (a > 0)
    if valid is not None:
        valid = np.asarray(valid, dtype=bool)
        if valid.shape != a.shape:
            raise ValueError('AEL ACHF validity must match image')
        mask &= valid
    y = (np.arange(a.shape[0], dtype=float)-cy)[:, None]
    x = (np.arange(a.shape[1], dtype=float)-cx)[None, :]
    r = np.hypot(x, y).astype(np.float32)
    geometry = SimpleNamespace(sun_radius_px=radius, radius_map=lambda: r)
    if variant not in AEL_PRESETS:
        raise ValueError('Unknown AEL ACHF variant')
    settings = dict(AEL_PRESETS[variant])
    settings.update(parameters or {})
    outer = float(settings['outer_sigma'])
    if not np.isfinite(outer) or not 0 <= outer <= 64:
        raise ValueError('AEL outer sigma must be in [0,64] native pixels')
    if variant == 'ael_angular_4':
        angular = float(settings['angular_sigma'])
        if not np.isfinite(angular) or not .1 <= angular <= 30:
            raise ValueError('AEL angular sigma must be in [0.1,30] degrees')
        logged = np.where(mask,np.log(np.maximum(a,1e-30)),np.nan)
        detail = angular_highpass(logged,mask,cx,cy,radius,angular)
        if outer:
            detail = normalized_gaussian(detail,np.isfinite(detail),outer*scale,min_support=.01)
        info = dict(angular_sigma=angular, native_outer_sigma=outer)
    else:
        sigmas = np.asarray(settings['sigmas'],dtype=float)
        if sigmas.shape != (5,) or not np.isfinite(sigmas).all() or np.any(sigmas<=0) or np.any(sigmas>128):
            raise ValueError('AEL isotropic needs five positive sigmas, at most 128 native pixels')
        detail, info = achf_isotropic(a, mask, geometry,
                                     sigmas=tuple(scale*sigmas), outer_sigma=outer*scale)
        info.update(native_sigmas=sigmas.tolist(), native_outer_sigma=outer)
    layer, display = display_detail(detail, mask)
    return layer, dict(info, **display, variant=variant, target_scale=scale)


def apply_ael_achf(image, strength, cx, cy, radius, valid=None, scale=1.,
                   variant='ael_iso_04', parameters=None):
    """Blend AEL's Overlay in normalized input units; preserve excluded samples."""
    a = np.asarray(image, dtype=np.float32)
    if not np.isfinite(strength) or not 0 <= strength <= 100:
        raise ValueError('AEL ACHF strength must be in [0, 100]')
    if strength == 0:
        return a.copy()
    layer, _ = ael_achf_layer(a, cx, cy, radius, valid, scale, variant, parameters)
    use = np.isfinite(layer)
    low, high = float(a[use].min()), float(a[use].max())
    if high == low:
        return a.copy()
    base = (a[use]-low)/(high-low)
    blend = np.where(base <= .5, 2*base*layer[use],
                     1-2*(1-base)*(1-layer[use]))
    result = a.copy()
    result[use] = a[use]+strength/100*(blend-base)*(high-low)
    return result


def angular_highpass(image, mask, cx, cy, radius, sigma_deg):
    """AEL's linear polar angular residual, tiled to bound temporary memory.

    PA sampling, complete bilinear support and inverse mapping follow AEL 1.3.3.
    """
    from scipy.ndimage import gaussian_filter1d
    h, w = image.shape
    r0 = .5*radius
    r1 = float(np.hypot(max(cx,w-cx),max(cy,h-cy)))
    nr = int(round(r1-r0))+1
    na = int(np.ceil(2*np.pi*r1/1.5))
    if nr < 2 or max(nr,na) >= 32767:
        raise ValueError('AEL angular polar grid is too small or exceeds OpenCV limits')
    radii = np.linspace(r0,r1,nr)
    pa = (np.arange(na)+.5)*(360/na)
    direction = np.radians((-pa)%360)
    ux,uy = np.sin(direction),-np.cos(direction)
    signal = np.where(mask,image,0).astype(np.float32)
    support = mask.astype(np.float32)
    polar = np.full((nr,na),np.nan,np.float32)
    def remap(values, weights, x, y):
        kw = dict(borderMode=cv2.BORDER_CONSTANT,borderValue=0.)
        observed = cv2.remap(weights,x,y,cv2.INTER_LINEAR,**kw)
        samples = cv2.remap(values,x,y,cv2.INTER_LINEAR,**kw)
        return np.where(observed>=.9999,samples,np.nan).astype(np.float32)
    for first in range(0,nr,64):
        check_cancelled()
        rs = radii[first:first+64,None]
        x = (cx+rs*ux).astype(np.float32)
        y = (cy+rs*uy).astype(np.float32)
        samples = remap(signal,support,x,y)
        ok = np.isfinite(samples)
        sigma = sigma_deg/(360/na)
        num = gaussian_filter1d(np.where(ok,samples,0),sigma,axis=1,mode='wrap')
        den = gaussian_filter1d(ok.astype(np.float32),sigma,axis=1,mode='wrap')
        smooth = np.where(ok & (den>=.3),num/np.maximum(den,1e-12),np.nan)
        polar[first:first+len(rs)] = samples-smooth
    padded = np.concatenate([polar[:,-4:],polar,polar[:,:4]],axis=1)
    weights = np.isfinite(padded).astype(np.float32)
    values = np.nan_to_num(padded)
    output = np.full(image.shape,np.nan,np.float32)
    for first in range(0,h,128):
        check_cancelled()
        y = (np.arange(first,min(h,first+128))-cy)[:,None]
        x = (np.arange(w)-cx)[None,:]
        r = np.hypot(x,y)
        pa = (-np.degrees(np.arctan2(x,-y)))%360
        ri = ((r-r0)/(r1-r0)*(nr-1)).astype(np.float32)
        ci = (pa/(360/na)-.5+4).astype(np.float32)
        output[first:first+len(y)] = remap(values,weights,ci,ri)
    output[~mask] = np.nan
    return output
