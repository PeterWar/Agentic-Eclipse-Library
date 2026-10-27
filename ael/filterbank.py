"""Portable filter recipes, independent of the historical project directories.

These are explicit general-purpose parameterisations, not byte-identical replays
of the author's manually finished image. All outputs preserve the observed domain.
"""
from __future__ import annotations
import numpy as np
from scipy.interpolate import LSQUnivariateSpline
from .radial import radial_quantile_rank
from . import filters as F
from .geometry import EclipseGeometry

ISO = {'achf_iso_01': ((2,4,8,16,32),3), 'achf_iso_04': ((1,2,4,8,16),1.5),
       'achf_iso_05': ((2,4,8,16,32,48),3), 'achf_iso_06': ((4,8,16,32,64),3)}
NAMES = ('nrgf','nrgf_log','rhef','rhef_upsilon','rhef_local60','rhef_local30',
         'achf_angular','achf_angular4','achf_angular8',*ISO,'mgn','wow','wow_bilateral')
DEFAULTS = ('nrgf','wow','achf_iso_04')


def radial_log_residual(luminance, valid, geometry):
    """Subtract a smooth cubic spline in ln r BEFORE isotropic high-pass.

    Ring medians are observations for a smooth fit, never a stepwise image to
    subtract. An off-centre Moon or a rectangular boundary cannot introduce a
    discontinuity in this profile. No output is produced outside observed data.

    A radially symmetric curve cannot follow a corona exactly: on the 2026 data it leaves ring-shaped residuals of
    about ±0.5 % in ln L between 3 and 9 R☉ (with its knots up to 6 R☉). Denser knots made it worse: the curve then
    follows the ripples of the ring medians and prints them on every angle. Layers that whiten coarse scales must
    therefore not turn such residuals into rings (see :func:`wow_measured`).
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
    """Continuous radial/sector quantile rank of positive observed luminance."""
    return radial_quantile_rank(img, valid, geometry, sector_deg, bin_px)


def wow_bilateral(img,valid,*,n_scales=6,noise_floor=3):
    """B3 starlet with bilateral range weights and symmetric observed pairs.

    Outside-image taps are absent. No reflected border and no copied missing
    pixels. Whitening is regularised by measured local noise at every scale.

    Known limitation (issue #4): the range weights are computed from the data being decomposed, so faint fine detail
    next to stronger structure can come out with the opposite sign. On real 2026 data, with two independent
    half-stacks, its fine detail (band-pass 1.5–6 px) correlated at only 0.08–0.20 with the data's own, with 38–47 %
    of the clear detail inverted; Edu (@edu27) measured the same on his own frames. It is no longer a default layer
    (since 1.3.4); :func:`wow_measured` is.
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


def upsilon(q, low=.35, high=.35):
    """Upsilon redistribution of Gilly & Cranmer (2025, eq. 2): a gamma-like curve below the median and an
    inverted one above it, with its own exponent for each side (``low`` below 0.5, ``high`` above). It pulls the
    extremes of a rank image towards mid grey; 0.35 on both sides is the example of their Figure 3, and their
    suggested defaults for SDO/AIA are asymmetric. Continuous at 0.5; maps 0 to 0 and 1 to 1."""
    if not (np.isfinite(low) and np.isfinite(high) and low > 0 and high > 0):
        raise ValueError('Upsilon exponents must be finite and positive')
    q = np.asarray(q, np.float32)
    with np.errstate(invalid='ignore'):
        u = np.where(q < .5, .5*np.maximum(2*q, 0)**low, 1-.5*np.maximum(2-2*q, 0)**high)
    return np.where(np.isfinite(q), u, np.nan).astype(np.float32)


def display_detail(detail, valid, *, noise_floor=1e-5, scale_region=None):
    """Map signed detail to a display layer centred on 0.5: ``0.5 + 0.5·tanh(detail / (2.5·scale))``.

    ``scale`` is one robust spread (1.4826·MAD) for the whole layer, measured over ``scale_region`` when it is given
    and holds at least 1000 observed pixels (else over every observed pixel). A whole-image spread is dominated by the
    faint outer field when the sky is in the frame; see :func:`display_detail_rings` for layers whose detail grows by
    an order of magnitude towards the limb."""
    good=valid & np.isfinite(detail)
    if not good.any(): raise ValueError('filter produced no observed values')
    sel=good if scale_region is None or (good & scale_region).sum()<1000 else good & scale_region
    median=float(np.median(detail[sel]))
    scale=max(float(1.4826*np.median(np.abs(detail[sel]-median))),noise_floor)
    return (np.where(good,.5+.5*np.tanh(detail/(2.5*scale)),np.nan).astype(np.float32),
            dict(scale=scale,tanh=2.5,scale_region='given' if sel is not good else 'all observed pixels'))


def display_detail_rings(detail, valid, geometry, *, width_px=2., min_count=50, smooth=3, noise_floor=1e-5):
    """Map signed detail to a display layer with a level and a spread measured ring by ring (issue #9, Edu).

    Median and 1.4826·MAD in annuli of ``width_px`` around the Sun (each with at least ``min_count`` pixels),
    averaged over ``smooth`` consecutive annuli and interpolated linearly in r: continuous curves, no ring staircase.
    Beyond the first and last populated annulus, the end value. Then ``0.5 + 0.5·tanh((detail - level) / (2.5·spread))``.
    It keeps the high-pass detail next to the limb from saturating when one global spread is dominated by the faint
    outer field, and it equalises the contrast across radius, which is a presentation choice, as in an NRGF."""
    good=valid & np.isfinite(detail)
    if not good.any(): raise ValueError('filter produced no observed values')
    r=geometry.radius_map()
    rv=r[good].astype(np.float64); dv=detail[good].astype(np.float64)
    k=np.floor(rv/width_px).astype(np.int64); order=np.argsort(k,kind='stable')
    ks,ds,rs=k[order],dv[order],rv[order]
    _,start,cnt=np.unique(ks,return_index=True,return_counts=True); sel=cnt>=min_count
    if sel.sum()<3: raise ValueError('ring display needs at least three populated annuli')
    med=[];mad=[];rm=[]
    for s0,c in zip(start[sel],cnt[sel]):
        seg=ds[s0:s0+c]; md=np.median(seg)
        med.append(md); mad.append(1.4826*np.median(np.abs(seg-md))); rm.append(rs[s0:s0+c].mean())
    med,mad,rm=np.array(med),np.array(mad),np.array(rm)
    if smooth>1:
        ker=np.ones(smooth); norm=np.convolve(np.ones(len(med)),ker,'same')
        med=np.convolve(med,ker,'same')/norm; mad=np.convolve(mad,ker,'same')/norm
    level=np.interp(r,rm,med); spread=np.maximum(np.interp(r,rm,mad),noise_floor)
    out=np.where(good,.5+.5*np.tanh((detail-level)/(2.5*spread)),np.nan).astype(np.float32)
    return out,dict(display='level and spread per ring',ring_width_px=width_px,ring_min_count=min_count,
                    ring_smooth_annuli=smooth,display_annuli=int(sel.sum()),tanh=2.5)


def _tangential_frame(valid, geometry, n_theta=1440):
    """Polar sampling around the Sun for :func:`_tangential_mean_removed` (computed once per layer)."""
    h,w=valid.shape; cx,cy=geometry.sun_xy; yy,xx=np.mgrid[0:h,0:w]
    r=np.hypot(xx-cx,yy-cy).astype(np.float32); ti=((np.arctan2(yy-cy,xx-cx)+np.pi)/(2*np.pi)*n_theta).astype(np.float32)
    del yy,xx
    nr=int(np.ceil(float(r[valid].max())))+2
    rr=np.arange(nr,dtype=np.float32)[:,None]; tt=np.linspace(-np.pi,np.pi,n_theta,endpoint=False,dtype=np.float32)[None,:]
    return dict(X=cx+rr*np.cos(tt),Y=cy+rr*np.sin(tt),r=r,ti=ti,n_theta=n_theta)


def _tangential_mean_removed(s, valid, frame, sigma_deg=10.):
    """``s`` minus its local mean along each circle around the Sun (Gaussian of ``sigma_deg`` degrees, normalised
    convolution over the observed pixels). A ring is constant along its circle and goes; a ray varies along it and
    stays."""
    from scipy import ndimage as ndi
    n=frame['n_theta']
    pv=ndi.map_coordinates(np.where(valid,s,0).astype(np.float32),[frame['Y'],frame['X']],order=1,mode='constant')
    pm=ndi.map_coordinates(valid.astype(np.float32),[frame['Y'],frame['X']],order=1,mode='constant')>.5
    sig=sigma_deg/360*n
    num=ndi.gaussian_filter1d(np.where(pm,pv,0).astype(np.float32),sig,axis=1,mode='wrap')
    den=ndi.gaussian_filter1d(pm.astype(np.float32),sig,axis=1,mode='wrap')
    mean=np.where(den>.2,num/np.maximum(den,1e-6),0).astype(np.float32)
    back=ndi.map_coordinates(np.concatenate([mean,mean[:,:1]],1),[frame['r'],frame['ti']],order=1,mode='nearest')
    return np.where(valid,s-back,0).astype(np.float32)


def wow_measured(img, valid, geometry, *, n_scales=6, noise_floor=3., noise_region_rsun=6., tangential_from=3,
                 tangential_sigma_deg=10., min_support=.01):
    """WOW (wavelet-optimised whitening, Auchère et al. 2023) for layers of real stacks; the default WOW layer since
    1.3.4.

    * Each starlet scale is divided by its local RMS, floored at ``noise_floor`` × the noise of that scale. The noise
      of each scale is MEASURED beyond ``noise_region_rsun`` (:func:`ael.filters.noise_factors`): stacks have
      correlated noise (on the 2026 fusion, scales 1–3 carried 6–15 times what white noise would), and white-noise
      floors whiten it into coarse blotches. With fewer than 20 000 pixels there, white-noise factors are used.
    * From scale ``tangential_from`` up, the local mean along each circle around the Sun is removed (Gaussian of
      ``tangential_sigma_deg``): the radial curve subtracted before (:func:`radial_log_residual`) leaves ring-shaped
      residuals that whitening would otherwise turn into rings; rays and loops vary along the circle and stay.
    Measured on 2026 data (two independent half-stacks): fine detail correlated at 0.82–0.86 with the data's own,
    0.6–1.6 % of it inverted; coarse detail (6–24 px) as plain WOW; no radial streaks in the noise (correlation
    lengths along and across the radius unchanged); ring level per 0.05 R☉ within ±0.005 where plain WOW made a ring
    of −0.036. Limits and gates: docs/VALIDATION_1.3.4.md."""
    a=np.asarray(img,np.float32); m=valid & np.isfinite(a)
    noise=F.noise_map(a,m)
    rs=geometry.rsun_map(); reg=m & (rs>noise_region_rsun)
    nf=F.noise_factors(a,m,reg,n_scales=n_scales) if reg.sum()>20000 else None
    details,_=F.starlet(a,m,n_scales,min_support)
    frame=_tangential_frame(m,geometry) if tangential_from<n_scales else None
    out=np.zeros(a.shape,np.float32)
    for j,d in enumerate(details):
        fj=nf[j] if nf is not None and j<len(nf) else F.STARLET_NOISE[min(j,len(F.STARLET_NOISE)-1)]
        p=F.normalized_gaussian(np.where(m,d*d,np.nan),m,2.*2**j,min_support)
        s=(d/np.maximum(np.sqrt(np.maximum(p,0)+(noise_floor*noise*fj)**2),1e-12)).astype(np.float32)
        if j>=tangential_from: s=_tangential_mean_removed(s,m,frame,tangential_sigma_deg)
        out+=np.where(m,s,0)
    out[~m]=np.nan
    return out,dict(noise_factors='measured' if nf is not None else 'white noise',
                    noise_factor_values=None if nf is None else [round(float(x),4) for x in nf],
                    noise_region_rsun=noise_region_rsun,tangential_from_scale=tangential_from,
                    tangential_sigma_deg=tangential_sigma_deg)


def make_filter(name,luminance,valid,geometry,*,upsilon_curve=None,achf_display='rings'):
    """Return (display layer in [0,1], blend mode, effective parameters).

    ``upsilon_curve`` (since 1.3.2): ``(low, high)`` exponents of the Upsilon curve of Gilly & Cranmer (2025) to
    apply to any RHEF layer, for example ``make_filter('rhef_local30', L, m, g, upsilon_curve=(.35, .35))``.
    ``'rhef_upsilon'`` is the whole-ring RHEF with ``(.35, .35)`` unless another curve is given. Any other filter
    with ``upsilon_curve`` is refused.

    ``achf_display`` (since 1.3.4): ``'rings'`` (default) maps every ACHF layer with a level and a spread per ring
    (:func:`display_detail_rings`, issue #9); ``'global'`` keeps the single whole-image spread of 1.3.3."""
    a=np.asarray(luminance,np.float32)
    m=valid & np.isfinite(a)                          # the values NRGF needs no positive pixels (a subtracted sky)
    if name!='nrgf': m=m & (a>0)
    if name not in NAMES: raise ValueError(f'unknown filter {name!r}; choose from {NAMES}')
    if upsilon_curve is not None:
        if not name.startswith('rhef'): raise ValueError('upsilon_curve applies to RHEF layers only')
        if len(upsilon_curve)!=2: raise ValueError('upsilon_curve is (low, high)')
    if not m.any(): raise ValueError('no observed luminance' if name=='nrgf' else 'no positive observed luminance')
    if achf_display not in ('rings','global'): raise ValueError("achf_display is 'rings' or 'global'")
    info={}
    if name in ('nrgf','nrgf_log'):
        q=F.nrgf(np.log(np.maximum(a,1e-30)) if name=='nrgf_log' else a,m,geometry,
                 bin_px=2,min_count=12,smooth_bins=0)
        result,info=display_detail(q,m)
        return result,'multiply',dict(**info,input='ln L' if name=='nrgf_log' else 'L',bin_px=2,smooth_bins=0,
                                           profile_evaluation='local cubic Hermite curve through nodes at the mean radius of each annulus')
    if name.startswith('rhef'):
        sector=60 if name.endswith('60') else 30 if name.endswith('30') else None
        q=radial_rank(a,m,geometry,sector)
        ups=upsilon_curve if upsilon_curve is not None else (.35,.35) if name=='rhef_upsilon' else None
        if ups is not None:
            q=upsilon(q,*ups)
        return q,'multiply',dict(sector_deg=sector,bin_px=2,upsilon=list(ups) if ups is not None else 1,
                                 quantiles=257,statistics='continuous log-quantiles in radius and angle',
                                 image_smoothing=False,
                                 note='Multiply with a layer centred on 0.5 = a uniform darkening (1 - a/2) times a '
                                      'modulation symmetric about mid grey; ranking gives a 0.5 % gap the same '
                                      'contrast as a 15 % one, and Upsilon tempers both tails (docs/PAPER_AND_LIBRARY.md)')
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
    elif name=='wow':
        residual,info=radial_log_residual(a,m,geometry)
        q,winfo=wow_measured(residual,m,geometry)
        rs=geometry.rsun_map()
        q,display=display_detail(q,m,scale_region=(rs>=1.1)&(rs<2.))
        return q,'overlay',dict(**info,**winfo,n_scales=6,noise_floor=3,**display,display_scale_rsun=[1.1,2.])
    else:
        residual,info=radial_log_residual(a,m,geometry)
        q=wow_bilateral(residual,m)
        info.update(n_scales=6,noise_floor=3)
        q,display=display_detail(q,m)
        return q,'overlay',dict(**info,**display)
    if achf_display=='rings':
        q,display=display_detail_rings(q,m,geometry)
    else:
        q,display=display_detail(q,m)
    return q,'overlay',dict(**info,**display)
