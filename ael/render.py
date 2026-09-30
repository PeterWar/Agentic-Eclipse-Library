"""From linear data to a picture: sky model, radial normalisation, structure images and colour.

The "structure image" is the kind of picture that shows the corona's fine filaments from the limb to
the edge of the field (the look made famous by Miloslav Druckmüller's composites).  It is built from
two parts, both computed from observed pixels only:

1. a **base**: the logarithm of the sky-subtracted luminance with its large-scale radial fall-off
   compressed (so that 1 and 4 solar radii fit in the same display range), and
2. a **detail** term: whitened multi-scale detail (:func:`ael.filters.wow`) or MGN, whose gain follows
   the local signal-to-noise ratio.

Colour is handled separately and never invents hue: the chromosphere and prominences keep the colour
measured in the data (after a white balance on the corona), the corona can be left neutral, keep its
measured colour, or receive a declared display tint.
"""
from __future__ import annotations

import numpy as np

from .filters import gaussian, mgn, noise_map, normalized_gaussian, wow
from .geometry import EclipseGeometry

__all__ = ["luminance", "sky_background", "radial_profile", "radial_trend", "soft_log", "structure_image",
           "white_balance_on_corona", "chromosphere_weight", "local_chromaticity", "compose_color", "stretch01", "to_uint"]


def luminance(rgb: np.ndarray, weights=(0.25, 0.5, 0.25)) -> np.ndarray:
    """Weighted luminance of a linear RGB image (default (R + 2G + B)/4, as in the project)."""
    w = np.asarray(weights, np.float32)
    return (rgb[..., 0] * w[0] + rgb[..., 1] * w[1] + rgb[..., 2] * w[2]).astype(np.float32)


def sky_background(img: np.ndarray, valid: np.ndarray | None, geometry: EclipseGeometry, *,
                   r_min_rsun: float = 6.0, order: int = 2, clip_sigma: float = 2.5, n_iter: int = 5,
                   max_samples: int = 400_000, seed: int = 0):
    """Robust 2-D polynomial model of the sky, fitted where the corona is faint (r ≥ ``r_min_rsun``).

    The model is only a background to subtract; it is smooth by construction (``order`` ≤ 3).  Returns
    ``(model, info)``.  If the field does not reach ``r_min_rsun`` a ValueError tells you so: then pass
    a smaller radius, knowing that some corona will be taken for sky (declare it).
    """
    a = np.asarray(img, np.float32)
    m = np.isfinite(a) if valid is None else (valid.astype(bool) & np.isfinite(a))
    r = geometry.rsun_map()
    sel = m & (r >= r_min_rsun)
    idx = np.flatnonzero(sel)
    if idx.size < 1000:
        raise ValueError(f"only {idx.size} valid pixels beyond {r_min_rsun} R_sun: choose a smaller r_min_rsun")
    rng = np.random.default_rng(seed)
    if idx.size > max_samples:
        idx = rng.choice(idx, max_samples, replace=False)
    h, w = a.shape
    yy, xx = np.divmod(idx, w)
    xn, yn = (xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)
    terms = [(i, j) for i in range(order + 1) for j in range(order + 1 - i)]
    A = np.stack([xn ** i * yn ** j for i, j in terms], axis=1)
    z = a.reshape(-1)[idx].astype(np.float64)
    use = np.ones(len(z), bool)
    coef = None
    for _ in range(n_iter):
        coef, *_ = np.linalg.lstsq(A[use], z[use], rcond=None)
        res = z - A @ coef
        s = 1.4826 * np.median(np.abs(res[use] - np.median(res[use])))
        new = np.abs(res - np.median(res[use])) < clip_sigma * s
        if (new == use).all():
            break
        use = new
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    Xn, Yn = (X - w / 2) / (w / 2), (Y - h / 2) / (h / 2)
    model = np.zeros((h, w), np.float32)
    for c, (i, j) in zip(coef, terms):
        model += np.float32(c) * Xn ** i * Yn ** j
    info = dict(r_min_rsun=r_min_rsun, order=order, n_used=int(use.sum()), rms=float(np.std(res[use])),
                coef=[float(c) for c in coef], terms=terms)
    return model, info


def radial_profile(img: np.ndarray, valid: np.ndarray | None, geometry: EclipseGeometry, *, center="sun",
                   bin_px: float = 2.0, stat: str = "median", min_count: int = 30):
    """Radial profile (median or mean per annulus) of the observed pixels.  Returns (r_px, value)."""
    a = np.asarray(img, np.float32)
    m = np.isfinite(a) if valid is None else (valid.astype(bool) & np.isfinite(a))
    r = geometry.radius_map(center)
    b = np.floor(r[m] / bin_px).astype(np.int64)
    v = a[m]
    nb = int(b.max()) + 1
    cnt = np.bincount(b, minlength=nb)
    if stat == "mean":
        prof = np.bincount(b, weights=v, minlength=nb) / np.maximum(cnt, 1)
    else:
        order = np.argsort(b, kind="stable")
        bs, vs = b[order], v[order]
        starts = np.concatenate([[0], np.cumsum(cnt)[:-1]])
        prof = np.full(nb, np.nan)
        for k in np.nonzero(cnt >= min_count)[0]:
            prof[k] = np.median(vs[starts[k]:starts[k] + cnt[k]])
    prof = prof.astype(np.float64)
    prof[cnt < min_count] = np.nan
    rc = (np.arange(nb) + 0.5) * bin_px
    return rc, prof


def radial_trend(img_log: np.ndarray, valid: np.ndarray | None, geometry: EclipseGeometry, *, center="sun",
                 bin_px: float = 2.0, smooth_rsun: float = 0.08) -> np.ndarray:
    """Smooth radial trend of a (log) image: median per annulus, smoothed in radius, mapped back.

    Outside the radii where the profile is defined the result is ``NaN`` (no extrapolation).
    """
    from scipy.ndimage import gaussian_filter1d

    rc, prof = radial_profile(img_log, valid, geometry, center=center, bin_px=bin_px)
    ok = np.isfinite(prof)
    s = smooth_rsun * geometry.sun_radius_px / bin_px
    num = gaussian_filter1d(np.where(ok, prof, 0.0), s)
    den = gaussian_filter1d(ok.astype(float), s)
    sm = np.where(ok & (den > 0.2), num / np.maximum(den, 1e-9), np.nan)
    r = geometry.radius_map(center)
    out = np.interp(r.ravel(), rc[np.isfinite(sm)], sm[np.isfinite(sm)], left=np.nan, right=np.nan)
    return out.reshape(r.shape).astype(np.float32)


def stretch01(x: np.ndarray, lo: float, hi: float, gamma: float = 1.0) -> np.ndarray:
    y = np.clip((np.asarray(x, np.float32) - lo) / max(hi - lo, 1e-12), 0, 1)
    return y ** (1.0 / gamma) if gamma != 1.0 else y


def soft_log(signal: np.ndarray, floor: float) -> np.ndarray:
    """``log(S/2 + sqrt(S²/4 + ε²))``: equal to ``log S`` where ``S ≫ ε``, flat at ``log ε`` where the
    signal is at or below the noise (also for negative values after sky subtraction).  No holes, no
    clipping, and the noise-dominated sky stays dark and smooth."""
    s = np.asarray(signal, np.float32)
    return np.log(0.5 * s + np.sqrt(0.25 * s * s + np.float32(floor) ** 2)).astype(np.float32)


def structure_image(lum: np.ndarray, valid: np.ndarray | None, geometry: EclipseGeometry, *,
                    sky: np.ndarray | float | None = None, b_limb: float = 0.78, b_slope: float = 0.28,
                    sky_level: float = 0.06, fade_decades: float = 1.1, angular_gain: float = 0.12,
                    detail: str = "wow", detail_amount: float = 0.35, detail_gamma: float = 0.7,
                    wow_scales: int = 8, wow_weights=None, noise_floor: float = 3.0,
                    mgn_sigmas=(1.25, 2.5, 5, 10, 20, 40, 80), detail_clip: float = 3.0, center="sun",
                    noise: np.ndarray | None = None, floor: float | None = None, noise_region_rsun: float | None = 6.0,
                    soft_threshold: float = 0.0, return_parts: bool = False):
    """Mono "structure" rendering in [0, 1] (``NaN`` where there is no data).

    The picture is built from three terms, each documented so that it can be declared::

        out = B(r) + angular_gain·(ℓ − ⟨ℓ⟩(r)) + detail_amount·d·B(r)**detail_gamma

    * ``ℓ`` is the soft-log of the sky-subtracted luminance (:func:`soft_log`) and ``⟨ℓ⟩(r)`` its smooth
      median per annulus: their difference is the observed large-scale angular structure (streamers,
      holes) — data.
    * ``B(r)`` is a **designed display profile** that replaces the corona's steep radial fall-off:
      ``b_limb − b_slope·ln(r/R☉)``, faded to ``sky_level`` where the median corona sinks into the noise
      floor (over ``fade_decades`` natural-log units above ``ln ε``).  It changes brightness per radius
      only (monotonic), never structure; say so in the caption ("radial gradient compressed").
    * ``d`` ∈ [−1, 1] is the whitened multi-scale detail (WOW with a noise floor, or MGN) — data, with
      its gain following the local signal-to-noise ratio.  The noise of each scale is *measured* beyond
      ``noise_region_rsun`` (correlated noise; see :func:`ael.filters.noise_factors`); ``None`` assumes
      white noise.
    """
    L = np.asarray(lum, np.float32)
    m = np.isfinite(L) if valid is None else (valid.astype(bool) & np.isfinite(L))
    if sky is not None:
        L = L - sky
    if floor is None:
        rs = geometry.rsun_map()
        sel = m & (rs > 6.0)
        if sel.sum() < 1000:
            sel = m
        v = L[sel]
        dd = np.diff(v[: min(v.size, 2_000_000)]) / np.sqrt(2)   # neighbour differences: pixel noise only
        floor = float(2.0 * 1.4826 * np.median(np.abs(dd - np.median(dd))))
    lg = np.where(m, soft_log(np.where(m, L, 0.0), floor), np.nan).astype(np.float32)
    trend = radial_trend(lg, m, geometry, center=center)
    ok = m & np.isfinite(trend)
    r = np.maximum(geometry.rsun_map(center), 1e-3)
    design = b_limb - b_slope * np.log(r)
    fade = np.clip((np.nan_to_num(trend, nan=-1e9) - np.log(floor)) / max(fade_decades, 1e-6), 0, 1)
    B = (sky_level + (design - sky_level) * fade).astype(np.float32)
    ang = np.where(ok, lg - trend, 0.0).astype(np.float32)
    parts = dict(profile=B, floor=floor)
    out = B + angular_gain * ang
    if detail != "none" and detail_amount > 0:
        if detail == "wow":
            lgv = np.where(ok, lg, np.nan)
            nz = noise if noise is not None else noise_map(lgv, ok)
            nf = None
            if noise_region_rsun is not None:
                reg = ok & (geometry.rsun_map(center) > noise_region_rsun)
                if reg.sum() > 20000:
                    from .filters import noise_factors as _nf
                    nf = _nf(lgv, ok, reg, n_scales=wow_scales)
                    parts["noise_factors"] = nf.tolist()
            d = wow(lgv, ok, n_scales=wow_scales, weights=wow_weights, noise=nz, noise_floor=noise_floor,
                    noise_factors=nf, soft_threshold=soft_threshold)
            d = d / float(np.sum(np.ones(wow_scales) if wow_weights is None else wow_weights)) * 2.0
        elif detail == "mgn":
            d = mgn(np.where(ok, lg, np.nan), ok, sigmas=mgn_sigmas, k=0.7) / (np.pi / 2)
        else:
            raise ValueError("detail must be 'wow', 'mgn' or 'none'")
        d = np.clip(np.nan_to_num(d, nan=0.0), -detail_clip, detail_clip) / detail_clip
        parts["detail"] = d
        out = out + detail_amount * d * np.power(np.clip(B, 0, 1), detail_gamma)
    out = np.where(ok, np.clip(out, 0, 1), np.nan).astype(np.float32)
    return (out, parts) if return_parts else out


# ------------------------------------------------------------------------------------------------
# Colour
# ------------------------------------------------------------------------------------------------
def white_balance_on_corona(rgb: np.ndarray, valid: np.ndarray | None, geometry: EclipseGeometry, *,
                            ring_rsun=(1.15, 1.6), exclude_sat: float | None = None):
    """Factors that make the median corona in ``ring_rsun`` neutral.  Returns (balanced_rgb, factors)."""
    m = np.isfinite(rgb).all(axis=2) if valid is None else valid.astype(bool)
    r = geometry.rsun_map()
    sel = m & (r >= ring_rsun[0]) & (r <= ring_rsun[1])
    if exclude_sat is not None:
        sel &= (rgb < exclude_sat).all(axis=2)
    med = np.array([np.median(rgb[..., c][sel]) for c in range(3)], np.float64)
    f = med[1] / med
    return (rgb * f.astype(np.float32)[None, None, :]).astype(np.float32), f


def chromosphere_weight(rgb_bal: np.ndarray, valid: np.ndarray | None, geometry: EclipseGeometry, *,
                        band_rsun=(0.95, 1.2), ratio_lo: float = 1.15, ratio_hi: float = 1.6,
                        smooth_px: float = 1.0) -> np.ndarray:
    """Soft weight (0–1) of chromospheric/prominence emission, from the data's own colour.

    After :func:`white_balance_on_corona` the corona is neutral, and H-alpha emission makes the
    chromosphere and prominences red/pink: the weight rises from ``ratio_lo`` to ``ratio_hi`` of
    R/G, restricted to a band near the limb (measured from the Moon's centre when available).
    """
    m = np.isfinite(rgb_bal).all(axis=2) if valid is None else valid.astype(bool)
    R, G = rgb_bal[..., 0], rgb_bal[..., 1]
    with np.errstate(divide="ignore", invalid="ignore"):
        q = np.where(m & (G > 0), R / G, 0.0)
    wgt = np.clip((q - ratio_lo) / (ratio_hi - ratio_lo), 0, 1).astype(np.float32)
    which = "moon" if geometry.moon_xy is not None else "sun"
    rad = geometry.radius_map(which) / geometry.sun_radius_px
    wgt[(rad < band_rsun[0]) | (rad > band_rsun[1]) | ~m] = 0
    if smooth_px > 0:
        wgt = np.clip(gaussian(wgt, smooth_px), 0, 1)
    return wgt


def local_chromaticity(rgb: np.ndarray, valid: np.ndarray | None, sigma: float = 24.0) -> np.ndarray:
    """Colour of each pixel averaged over its neighbourhood (normalised convolution per channel): the
    usual chroma noise reduction — luminance keeps full resolution, colour is measured at ``sigma``."""
    from .filters import normalized_gaussian as _ng
    m = np.isfinite(rgb).all(axis=2) if valid is None else valid.astype(bool)
    return np.stack([_ng(rgb[..., c], m, sigma) for c in range(3)], -1).astype(np.float32)


def _display_chroma(rgb_lin: np.ndarray, chroma_gamma: float, limit=(0.2, 3.0)) -> np.ndarray:
    """Linear RGB → display-space chromaticity with unit luminance.  Ratios are taken in linear light,
    limited to ``limit`` (noise can make them explode), then raised to ``1/chroma_gamma``: multiplying a
    gamma-encoded grey by this is the same as multiplying the linear light by the linear ratios."""
    x = np.maximum(np.nan_to_num(np.asarray(rgb_lin, np.float32), nan=0.0), 0)
    lum = luminance(x)
    with np.errstate(divide="ignore", invalid="ignore"):
        c = np.where(lum[..., None] > 0, x / lum[..., None], 1.0)
    c = np.clip(np.nan_to_num(c, nan=1.0, posinf=1.0), limit[0], limit[1]) ** (1.0 / chroma_gamma)
    c = c / np.maximum(luminance(c), 1e-6)[..., None]
    return c.astype(np.float32)


def compose_color(mono: np.ndarray, *, chroma_rgb: np.ndarray | None = None, chroma_weight: np.ndarray | None = None,
                  corona_rgb: np.ndarray | None = None, corona_color_strength: float = 0.0,
                  tint: tuple[float, float, float] | None = None, tint_weight: np.ndarray | float = 0.0,
                  chroma_gamma: float = 2.2, nan_color=(0.0, 0.0, 0.0)) -> np.ndarray:
    """Colour a mono (display-encoded) structure image without inventing hue.

    * ``corona_rgb`` + ``corona_color_strength``: the *measured* colour of the data (linear RGB, e.g.
      from :func:`local_chromaticity`) — 0 is neutral grey, 1 the measured chromaticity.  With a low Sun
      this is the golden corona and the blue-grey sky, as seen.
    * ``chroma_rgb`` + ``chroma_weight``: where the weight is > 0 (chromosphere, prominences) the pixel
      takes the measured chromaticity of ``chroma_rgb`` (linear RGB).
    * ``tint`` + ``tint_weight``: a declared display tint (display-space RGB, e.g. a cool grey for the
      sky).  It is a presentation choice, not data: say so in the caption.
    Ratios measured in linear light are converted with ``chroma_gamma`` (see :func:`_display_chroma`).
    """
    y = np.asarray(mono, np.float32)
    out = np.repeat(y[..., None], 3, axis=2)
    if corona_rgb is not None and corona_color_strength > 0:
        c = _display_chroma(corona_rgb, chroma_gamma)
        out = out * (1.0 + corona_color_strength * (c - 1.0))
    if tint is not None:
        tt = np.asarray(tint, np.float32)
        tt = tt / luminance(tt[None, None, :])[0, 0]
        tw = np.asarray(tint_weight, np.float32)
        if tw.ndim == 2:
            tw = tw[..., None]
        out = out * (1.0 + tw * (tt[None, None, :] - 1.0))
    if chroma_rgb is not None and chroma_weight is not None:
        c = _display_chroma(chroma_rgb, chroma_gamma)
        w = np.asarray(chroma_weight, np.float32)[..., None]
        out = out * (1 - w) + (y[..., None] * c) * w
    bad = ~np.isfinite(y)
    out[bad] = nan_color
    return np.clip(out, 0, 1).astype(np.float32)


def to_uint(x01: np.ndarray, bits: int = 16, srgb_gamma: bool = False) -> np.ndarray:
    """[0, 1] float → uint8/uint16.  ``srgb_gamma`` applies the sRGB transfer curve first."""
    x = np.clip(np.nan_to_num(np.asarray(x01, np.float32), nan=0.0), 0, 1)
    if srgb_gamma:
        x = np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)
    mx = 255 if bits == 8 else 65535
    return np.round(x * mx).astype(np.uint8 if bits == 8 else np.uint16)
