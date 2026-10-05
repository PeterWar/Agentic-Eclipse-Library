"""Frozen 1.2.0 operators for negative controls only, never production recipes."""
from __future__ import annotations
import numpy as np
from scipy.stats import rankdata
from ael.geometry import EclipseGeometry

def nrgf(img: np.ndarray, valid: np.ndarray | None, geometry: EclipseGeometry, *, center="sun",
         bin_px: float = 1.0, robust: bool = True, min_count: int = 50, smooth_bins: float = 0.0):
    """Normalising-radial-graded filter: ``(I − <I>(r)) / σ(r)`` over annuli around the centre.

    ``robust`` uses the median and 1.4826·MAD instead of mean and standard deviation.  Only observed
    pixels enter each annulus; annuli with fewer than ``min_count`` pixels give ``NaN``.  The sky
    gradient is *not* removed by an NRGF (it is normalised along with the corona): subtract a sky
    model first (:func:`ael.render.sky_background`) if the field is large.
    """
    a = np.asarray(img, np.float32)
    m = np.isfinite(a) if valid is None else (valid.astype(bool) & np.isfinite(a))
    r = geometry.radius_map(center, np.float32)
    b = np.floor(r / bin_px).astype(np.int64)
    nb = int(b.max()) + 1
    bm, am = b[m], a[m]
    cnt = np.bincount(bm, minlength=nb)
    if robust:
        order = np.argsort(bm, kind="stable")
        bs, as_ = bm[order], am[order]
        starts = np.concatenate([[0], np.cumsum(cnt)[:-1]])
        mu = np.full(nb, np.nan)
        sd = np.full(nb, np.nan)
        for k in np.nonzero(cnt >= min_count)[0]:
            seg = as_[starts[k]:starts[k] + cnt[k]]
            med = np.median(seg)
            mu[k] = med
            sd[k] = 1.4826 * np.median(np.abs(seg - med))
    else:
        s1 = np.bincount(bm, weights=am, minlength=nb)
        s2 = np.bincount(bm, weights=am.astype(np.float64) ** 2, minlength=nb)
        with np.errstate(invalid="ignore", divide="ignore"):
            mu = s1 / cnt
            sd = np.sqrt(np.maximum(s2 / cnt - mu ** 2, 0))
        mu[cnt < min_count] = np.nan
        sd[cnt < min_count] = np.nan
    if smooth_bins > 0:
        from scipy.ndimage import gaussian_filter1d
        for arr in (mu, sd):
            ok = np.isfinite(arr)
            if ok.sum() > 3:
                num = gaussian_filter1d(np.where(ok, arr, 0.0), smooth_bins)
                den = gaussian_filter1d(ok.astype(float), smooth_bins)
                arr[ok] = (num / np.maximum(den, 1e-9))[ok]
    out = np.full(a.shape, np.nan, np.float32)
    with np.errstate(invalid="ignore", divide="ignore"):
        out[m] = ((am - mu[bm]) / sd[bm]).astype(np.float32)
    return out


def radial_rank(img, valid, geometry, sector_deg=None, bin_px=2):
    """Empirical radial histogram equalisation; local sectors blend continuously.

    Local CDFs are measured every quarter-sector and linearly blended in angle.
    Cells with fewer than 12 observations remain undefined, never extrapolated.
    """
    m=valid & np.isfinite(img)
    radius=geometry.radius_map(); ri=np.floor(radius/bin_px).astype(int)
    ids=np.flatnonzero(m); bins=ri.ravel()[ids]
    order=np.argsort(bins,kind='stable'); counts=np.bincount(bins); cuts=np.r_[0,np.cumsum(counts)]
    vals=img.ravel()[ids]
    angles=geometry.pa_map().ravel()[ids]
    out=np.full(len(ids),np.nan,np.float32)
    for b in np.flatnonzero(counts>=12):
        ix=order[cuts[b]:cuts[b+1]]; v=vals[ix]
        if sector_deg is None:
            out[ix]=(rankdata(v,method='average')-.5)/len(ix)
            continue
        step=sector_deg/4; k0=np.floor(angles[ix]/step).astype(int)
        blend=angles[ix]/step-k0; total=np.zeros(len(ix)); weight=np.zeros(len(ix))
        for k in np.unique(np.r_[k0,k0+1]):
            delta=(angles[ix]-k*step+180)%360-180
            sample=np.sort(v[np.abs(delta)<=sector_deg/2])
            if len(sample)<12: continue
            use=(k0==k)|(k0+1==k)
            wk=np.where(k0[use]==k,1-blend[use],blend[use])
            cdf=(np.searchsorted(sample,v[use],'left')+np.searchsorted(sample,v[use],'right'))/(2*len(sample))
            total[use]+=wk*cdf; weight[use]+=wk
        out[ix]=np.where(weight>.999,total/np.maximum(weight,1e-9),np.nan)
    result=np.full(img.shape,np.nan,np.float32); result.ravel()[ids]=out
    return result

