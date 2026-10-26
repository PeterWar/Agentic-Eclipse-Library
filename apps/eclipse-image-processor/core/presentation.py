"""Native normalization and the shared AEL-style PSB presentation."""
import numpy as np
from .image_data import normalize_observed


def normalized_base(image, settings):
    """Linearly normalize with native working levels shared by both resolutions."""
    return normalize_observed(image, settings.get('normalization_range'))


def composition_settings(settings):
    """Only native normalization and transient comparison affect the working base."""
    return dict(blend=settings.get('blend', 1.),
                **({'normalization_range': settings['normalization_range']}
                   if 'normalization_range' in settings else {}))


def psb_presentation_settings(source, valid=None, *, rgb=None, params=None, exposure_ev=0.):
    """Our automatic scale heuristic; AEL supplies the curve, not automatic exposure.

    P99.5 of positive sampled luminance outside 1.2 lunar radii resists isolated
    bright pixels. Native sampling (at most about 1024 per side) is shared by
    fast/native previews and export. EV adjusts the scale, never input pixels.
    """
    if not np.isfinite(exposure_ev) or not -6 <= exposure_ev <= 6:
        raise ValueError('PSB exposure must be finite, between -6 and +6 EV')
    stride=max(1, int(np.ceil(max(source.shape)/1024)))
    sample=np.asarray(source[::stride, ::stride], dtype=float)
    good=np.isfinite(sample)
    if valid is not None:
        good &= valid[::stride, ::stride]
    if rgb is not None:
        colour=np.asarray(rgb[::stride, ::stride], dtype=float)
        good &= np.isfinite(colour).all(axis=-1)
        sample=colour @ np.array([.25, .5, .25])
    good &= sample > 0
    params=params or {}
    radius=float(params.get('sr', 0.))
    if radius > 0:
        yy,xx=np.ogrid[:sample.shape[0], :sample.shape[1]]
        good &= np.hypot(xx*stride-params['sx'], yy*stride-params['sy']) > 1.2*radius
    values=sample[good]
    automatic_scale=float(np.percentile(values,99.5)) if values.size else 1.
    scale=automatic_scale * 2.**(-exposure_ev)
    return dict(mode='ael_presentation', strength=10., blend=1., scale=scale,
                normalization_range=[0.,scale], highlight_ceiling=.9,
                automatic_scale=automatic_scale, exposure_ev=float(exposure_ev),
                sampled_pixels=int(values.size), sampling_stride=stride,
                scale_policy='P99.5 positive native luminance outside 1.2 lunar radii; application heuristic')


def ael_tone_map(image, valid, settings):
    """AEL curve: per-channel Asinh, then shared shoulder; no positive pre-clipping."""
    scale=float(settings['scale'])
    strength=float(settings.get('strength',10.))
    ceiling=float(settings.get('highlight_ceiling',.9))
    if not np.isfinite([scale,strength,ceiling]).all() or scale <= 0 or strength <= 0 or not 0 < ceiling <= 1-1/65535:
        raise ValueError('Invalid PSB presentation scale, Asinh or highlight ceiling')
    image=np.asarray(image)
    if image.ndim not in (2,3) or (image.ndim == 3 and image.shape[-1] != 3) or valid.shape != image.shape[:2]:
        raise ValueError('PSB presentation needs matching mono/RGB and validity canvases')
    result=np.empty(image.shape,np.float32)
    for first in range(0,image.shape[0],128):
        block=np.asarray(image[first:first+128],dtype=float)
        observed=valid[first:first+128]
        if not np.isfinite(block[observed]).all():
            raise ValueError('Nonfinite observed PSB presentation samples')
        mask=observed if image.ndim == 2 else observed[...,None]
        a=np.where(mask,np.maximum(block,0.),0.)
        with np.errstate(over='ignore',invalid='ignore'):
            u=np.arcsinh(a/scale*strength)/np.arcsinh(strength)
        if not np.isfinite(u).all():
            raise ValueError('PSB tone mapping overflow')
        peak=u if image.ndim == 2 else np.max(u,axis=-1)
        shoulder=ceiling*(-np.expm1(-peak/ceiling))
        factor=np.divide(shoulder,peak,out=np.zeros_like(peak),where=peak>0)
        result[first:first+128]=u*(factor if image.ndim == 2 else factor[...,None])
    return result


def psb_base(source, params, settings, rgb=None):
    """Quantized mono presentation base and optional top Color layer for both routes."""
    from .layer_export import to_u16
    valid=np.isfinite(source) & params.get('valid_mask',True)
    if rgb is None:
        return to_u16(ael_tone_map(source,valid,settings)).astype(float)/65535., None
    valid &= np.isfinite(rgb).all(axis=-1)
    colour=to_u16(ael_tone_map(rgb,valid,settings)).astype(float)/65535.
    base=to_u16(colour @ np.array([.30,.59,.11])).astype(float)/65535.
    return base, colour
