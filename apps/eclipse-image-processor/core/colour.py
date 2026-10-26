"""Optional gain-only neutralization derived from tse-tools and display-only RGB/mono composition."""
import numpy as np
from .presentation import normalized_base


def neutralize_tse(rgb, white=1.):
    """Gain-only display neutralization using sampled P99-P1 channel spans.

    Derived from tse-tools color_calibrate, revision
    14ae3f7d823d0ac66688a32bf27d0c4b9b8a0391 (MIT), with NaN exclusion.
    Unlike that recipe, do not subtract channel backgrounds or add a pedestal:
    additive offsets can turn intensity gradients into chromatic gradients.
    A single global highlight scale preserves positive channel ratios.
    white=None uses a shared HDR working scale, not measured sensor saturation.
    This assumes neutral sky/corona statistics; it is not ICC calibration.
    """
    a = np.asarray(rgb, dtype=float)
    if a.ndim != 3 or a.shape[-1] != 3:
        raise ValueError('Colour calibration needs an RGB image')
    valid = np.isfinite(a).all(axis=-1)
    automatic = white is None
    if automatic:
        if not valid.any():
            raise ValueError('Colour calibration needs finite RGB observations')
        # One common scale preserves channel ratios and arbitrary input units.
        maximum = float(np.max(a,where=valid[...,None],initial=-np.inf))
        white = maximum * (1 + 1e-6)
    if not np.isfinite(white) or white <= 0:
        raise ValueError('Colour calibration needs a positive input white or positive HDR observations')
    a = a/white
    small = a[::10, ::10]
    selected = small[np.isfinite(small).all(axis=-1) & (small > 0).all(axis=-1) & (small < 1).all(axis=-1)]
    if len(selected) < 2:
        raise ValueError('Not enough sampled RGB pixels strictly between 0 and 1 for calibration')
    background, foreground = np.percentile(selected, [1, 99], axis=0)
    span = foreground-background
    if np.any(span <= np.finfo(float).eps):
        raise ValueError('Colour calibration needs nonconstant sampled channels')
    ratios = span/span[1]
    ratios /= ratios.max()
    gains=1/ratios
    corrected=np.maximum(a,0)*gains
    # One common factor avoids independent channel clipping in bright pixels.
    highlight_scale=max(float(np.max(corrected[valid])),1.)
    corrected=np.where(valid[...,None],corrected/highlight_scale,np.nan)
    report = dict(method='gain-only P1/P99-span neutralization', reference_revision='14ae3f7d823d0ac66688a32bf27d0c4b9b8a0391',
                  white=float(white), white_source=('shared observed maximum with headroom' if automatic else 'declared input white'),
                  sample_p1=background.tolist(), sample_p99=foreground.tolist(),
                  ratios=ratios.tolist(), gains=gains.tolist(), highlight_scale=highlight_scale,
                  background_subtracted=False, sampled_pixels=len(selected), stride=10,
                  assumption='Declared linear input; neutral channel spans; not photometric/ICC calibration')
    return corrected.astype(np.float32), report


def colour_layer(rgb, source, display):
    """Match the normalized base luminance with an equal factor on R/G/B.

    Negative values are clipped for display only. A shared highlight factor keeps
    channels in gamut. Numerical source and optional balanced float remain separate.
    """
    a = np.asarray(rgb, dtype=float)
    if a.shape != (*source.shape, 3):
        raise ValueError('RGB and luminance must share a canvas')
    valid = np.isfinite(source) & np.isfinite(a).all(axis=-1)
    a = np.where(valid[..., None], np.maximum(a, 0), 0)
    luminance = a @ np.array([.299, .587, .114])
    target = normalized_base(source, display)
    factor = np.divide(target, luminance, out=np.zeros_like(target), where=luminance > 0)
    a *= factor[..., None]
    a /= np.maximum(a.max(axis=-1), 1)[..., None]
    return a


def set_luminosity(colour, luminance):
    """Nonseparable Color blend over mono, using SetLum/ClipColor equations.

    Legacy display-number coefficients (.30,.59,.11); native Photoshop colour
    management can differ, so its rendering still needs verification.
    """
    c = np.asarray(colour, dtype=float)
    weights = np.array([.30, .59, .11])
    c = c + (luminance-c@weights)[..., None]
    low, high = c.min(axis=-1), c.max(axis=-1)
    low_factor = np.divide(luminance, luminance-low, out=np.ones_like(luminance), where=luminance != low)
    c = np.where((low < 0)[..., None], luminance[..., None]+(c-luminance[..., None])*low_factor[..., None], c)
    high_factor = np.divide(1-luminance, high-luminance, out=np.ones_like(luminance), where=high != luminance)
    c = np.where((high > 1)[..., None], luminance[..., None]+(c-luminance[..., None])*high_factor[..., None], c)
    return np.clip(c, 0, 1)
