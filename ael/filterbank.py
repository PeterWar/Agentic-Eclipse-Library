"""Portable filter recipes, independent of the historical project directories.

These are explicit general-purpose parameterisations, not byte-identical replays
of the author's manually finished image. All outputs preserve the observed domain.
"""
from __future__ import annotations
import numpy as np
from scipy.interpolate import LSQUnivariateSpline
from scipy.stats import rankdata
from . import filters as F
from .geometry import EclipseGeometry

ISO = {'achf_iso_01': ((2,4,8,16,32),3), 'achf_iso_04': ((1,2,4,8,16),1.5),
       'achf_iso_05': ((2,4,8,16,32,48),3), 'achf_iso_06': ((4,8,16,32,64),3)}
NAMES = ('nrgf','nrgf_log','rhef','rhef_upsilon','rhef_local60','rhef_local30',
         'achf_angular','achf_angular4','achf_angular8',*ISO,'mgn','wow','wow_bilateral')
DEFAULTS = ('nrgf','wow_bilateral','achf_iso_04')


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
    residual, info=radial_log_residual(luminance,valid,geometry)
    m=np.isfinite(residual)
    detail=np.zeros(residual.shape,np.float32)
    for s in sigmas:
        detail += (residual-F.normalized_gaussian(residual,m,s,min_support=.01))/len(sigmas)
    if outer_sigma:
        detail=F.normalized_gaussian(detail,m,outer_sigma,min_support=.01)
    detail[~m]=np.nan
    return detail,dict(**info,sigmas_px=list(sigmas),outer_sigma_px=outer_sigma)


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


def wow_bilateral(img,valid,*,n_scales=6,noise_floor=3):
    """B3 starlet with bilateral range weights and symmetric observed pairs.

    Outside-image taps are absent. No reflected border and no copied missing
    pixels. Whitening is regularised by measured local noise at every scale.
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


def display_detail(detail, valid, *, noise_floor=1e-5):
    good=valid & np.isfinite(detail)
    if not good.any(): raise ValueError('filter produced no observed values')
    median=float(np.median(detail[good]))
    scale=max(float(1.4826*np.median(np.abs(detail[good]-median))),noise_floor)
    return np.where(good,.5+.5*np.tanh(detail/(2.5*scale)),np.nan).astype(np.float32),dict(scale=scale,tanh=2.5)


def make_filter(name,luminance,valid,geometry):
    """Return (display layer in [0,1], blend mode, effective parameters)."""
    a=np.asarray(luminance,np.float32); m=valid & np.isfinite(a) & (a>0)
    if name not in NAMES: raise ValueError(f'unknown filter {name!r}; choose from {NAMES}')
    if not m.any(): raise ValueError('no positive observed luminance')
    info={}
    if name in ('nrgf','nrgf_log'):
        q=F.nrgf(np.log(np.maximum(a,1e-30)) if name=='nrgf_log' else a,m,geometry,
                 bin_px=2,min_count=12,smooth_bins=3)
        result,info=display_detail(q,m)
        return result,'multiply',dict(**info,input='ln L' if name=='nrgf_log' else 'L',bin_px=2,smooth_bins=3)
    if name.startswith('rhef'):
        sector=60 if name.endswith('60') else 30 if name.endswith('30') else None
        q=radial_rank(a,m,geometry,sector)
        if name=='rhef_upsilon':
            q=np.where(q<.5,.5*np.maximum(2*q,0)**.35,1-.5*np.maximum(2-2*q,0)**.35)
        return q,'multiply',dict(sector_deg=sector,bin_px=2,upsilon=.35 if name=='rhef_upsilon' else 1)
    if name in ISO:
        sigmas,outer=ISO[name]
        q,info=achf_isotropic(a,m,geometry,sigmas=sigmas,outer_sigma=outer)
    elif name.startswith('achf_angular'):
        sr=4 if name.endswith('4') else 8 if name.endswith('8') else 0
        q=F.tangential_highpass(np.log(np.maximum(a,1e-30)),m,geometry,sigma_deg=1)
        if sr: q=F.normalized_gaussian(q,np.isfinite(q),sr,min_support=.01)
        info=dict(sigma_deg=1,smoothing_px=sr)
    elif name=='mgn':
        q=F.mgn(a,m,h=.7,min_support=.01)
        lo,hi=np.nanpercentile(q[m],[1,99])
        q=np.where(m,np.clip((q-lo)/max(float(hi-lo),1e-12),0,1),np.nan)
        return q,'overlay',dict(display_limits=[float(lo),float(hi)],h=.7,k=.7,gamma=3.2)
    else:
        residual,info=radial_log_residual(a,m,geometry)
        q=wow_bilateral(residual,m) if name=='wow_bilateral' else F.wow(residual,m,n_scales=6,min_support=.01)
        info.update(n_scales=6,noise_floor=3)
    q,display=display_detail(q,m)
    return q,'overlay',dict(**info,**display)
