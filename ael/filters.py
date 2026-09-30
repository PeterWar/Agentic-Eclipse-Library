"""Coronal detail filters that read only observed pixels.

Every filter takes ``valid`` (boolean: where there is data) and uses *normalised convolution*
(Knutsson & Westin 1993): a smoothed value is ``G*(I·m) / G*m``, so pixels without data never enter a
sum, and the result is ``NaN`` where too little data supports it.  This is what keeps a filter from
inventing structure at the lunar limb or at the edge of the field (the project's hardest lesson).

Implemented from the papers (cite them if you publish):

* NRGF – Morgan, Habbal & Woo (2006), Solar Physics 236, 263.
* MGN  – Morgan & Druckmüller (2014), Solar Physics 289, 2945.
* WOW  – Auchère, Soubrié, Pelouze & Buchlin (2023), A&A 670, A66 (wavelet-optimised whitening),
  here with a local noise floor so that noise-dominated scales are not amplified.
* Starlet (isotropic undecimated wavelet, B3 spline) – Starck, Fadili & Murtagh (2007), IEEE TIP 16, 297.
* Tangential high-pass – a circular (along the limb) high-pass in the spirit of the adaptive circular
  filters of Druckmüller, Rušin & Minarovjech (2006), Contrib. Astron. Obs. Skalnaté Pleso 36, 131.
"""
from __future__ import annotations

import cv2
import numpy as np

from .geometry import EclipseGeometry

__all__ = ["gaussian", "normalized_gaussian", "local_mean_std", "nrgf", "mgn", "starlet", "wow",
           "noise_map", "noise_factors", "tangential_highpass", "STARLET_NOISE"]

# Standard deviation of the B3-starlet detail coefficients for unit white Gaussian noise (scales 1..9).
STARLET_NOISE = np.array([0.8908, 0.2007, 0.0856, 0.0413, 0.0205, 0.0103, 0.0052, 0.0026, 0.0013])


# ------------------------------------------------------------------------------------------------
# Smoothing
# ------------------------------------------------------------------------------------------------
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


def local_mean_std(img: np.ndarray, valid: np.ndarray | None, sigma: float, min_support: float = 0.25):
    """Local mean and standard deviation (normalised convolution)."""
    mu = normalized_gaussian(img, valid, sigma, min_support)
    m = np.isfinite(mu)
    d = np.where(m, np.asarray(img, np.float32) - mu, np.nan)
    var = normalized_gaussian(d * d, m, sigma, min_support)
    return mu, np.sqrt(np.maximum(var, 0.0))


# ------------------------------------------------------------------------------------------------
# NRGF
# ------------------------------------------------------------------------------------------------
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


# ------------------------------------------------------------------------------------------------
# MGN
# ------------------------------------------------------------------------------------------------
def mgn(img: np.ndarray, valid: np.ndarray | None = None, *, sigmas=(1.25, 2.5, 5, 10, 20, 40), k: float = 0.7,
        weights=None, h: float = 0.0, gamma: float = 3.2, global_image: np.ndarray | None = None,
        a0: float | None = None, a1: float | None = None, min_support: float = 0.25):
    """Multi-scale Gaussian normalisation (Morgan & Druckmüller 2014).

    Local part: for each scale, ``C = (I − B)/sqrt(G*(I − B)²)`` with ``B = G*I``, then ``arctan(k·C)``,
    averaged over scales (optionally weighted).  With ``h > 0`` it is mixed with a global
    gamma-transformed image, as in the paper; pass ``global_image`` (already in [0, 1]) to use your own
    tone-mapped base instead.  Returns an image in radians-like units (local part in [−π/2, π/2]) if
    ``h == 0``.
    """
    a = np.asarray(img, np.float32)
    m = np.isfinite(a) if valid is None else (valid.astype(bool) & np.isfinite(a))
    w = np.ones(len(sigmas)) if weights is None else np.asarray(weights, float)
    acc = np.zeros(a.shape, np.float32)
    for s, wi in zip(sigmas, w):
        mu, sd = local_mean_std(a, m, s, min_support)
        c = np.where(np.isfinite(mu) & (sd > 0), (a - mu) / np.maximum(sd, 1e-12), np.nan)
        acc += wi * np.arctan(k * c).astype(np.float32)
    acc /= float(np.sum(w))
    acc[~m] = np.nan
    if h <= 0:
        return acc
    if global_image is None:
        lo = np.nanmin(a[m]) if a0 is None else a0
        hi = np.nanmax(a[m]) if a1 is None else a1
        g = np.clip((a - lo) / max(hi - lo, 1e-12), 0, 1) ** (1.0 / gamma)
    else:
        g = np.asarray(global_image, np.float32)
    return (h * g + (1 - h) * acc).astype(np.float32)


# ------------------------------------------------------------------------------------------------
# Starlet and WOW
# ------------------------------------------------------------------------------------------------
_B3 = (1 / 16, 4 / 16, 6 / 16, 4 / 16, 1 / 16)


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


def noise_factors(img: np.ndarray, valid: np.ndarray | None, region: np.ndarray, n_scales: int = 8,
                  trusted_scales: int = 4, decay: float = 0.5, margin: int = 64) -> np.ndarray:
    """Empirical noise of each starlet scale relative to the pixel noise, measured in ``region``
    (a boolean mask where the noise dominates, e.g. the far field).

    Real stacks have *correlated* noise (registration, drizzle, warping, demosaicing): measured on the
    2026 data, scales 2–4 carried 6–14× the noise that white noise would put there, and whitening them
    with white-noise factors turned the outer corona into mottle.  Scales beyond ``trusted_scales``
    already contain faint corona, so their factor is extrapolated with ``decay`` per scale.  Pass the
    result as ``noise_factors`` to :func:`wow`.
    """
    a = np.asarray(img, np.float32)
    m = np.isfinite(a) if valid is None else (valid.astype(bool) & np.isfinite(a))
    d, _ = starlet(a, m, n_scales=min(n_scales, trusted_scales))
    reg = region.astype(bool) & m
    if margin > 0:
        import cv2 as _cv2
        k = np.ones((2 * margin + 1, 2 * margin + 1), np.uint8)
        reg &= _cv2.erode(m.astype(np.uint8), k).astype(bool)
    sig = [1.4826 * float(np.median(np.abs(x[reg] - np.median(x[reg])))) for x in d]
    pix = sig[0] / STARLET_NOISE[0]
    f = [s / pix for s in sig]
    while len(f) < n_scales:
        f.append(f[-1] * decay)
    return np.asarray(f[:n_scales], np.float64)


def wow(img: np.ndarray, valid: np.ndarray | None = None, *, n_scales: int = 7, weights=None,
        power_sigma_factor: float = 2.0, noise: np.ndarray | float | None = None, noise_floor: float = 3.0,
        soft_threshold: float = 0.0, include_coarse: bool = False, min_support: float = 0.2,
        noise_factors: np.ndarray | None = None):
    """Wavelet-optimised whitening (Auchère et al. 2023) with a noise floor.

    Each starlet scale ``w_j`` is divided by its local RMS ``sqrt(G_j * w_j²)`` (``G_j`` a Gaussian of
    ``power_sigma_factor·2**j`` px), which equalises the contrast of structures of every size — the
    "Druckmüller look" — and the scales are summed.  To keep the noise from being whitened up to the
    signal level, the local RMS is floored at ``noise_floor × σ_noise,j`` (``noise`` is a map or a
    number in image units; if ``None`` it is estimated with :func:`noise_map`).  Where a scale is
    dominated by noise its gain therefore stays low: the resolution follows the signal-to-noise ratio.

    ``soft_threshold`` (in units of σ_noise,j) removes small coefficients before whitening.
    ``noise_factors`` (from :func:`noise_factors`) replaces the white-noise scale factors when the
    noise is correlated — measure them: real stacks are rarely white.
    Returns the whitened sum (``NaN`` outside the data).
    """
    a = np.asarray(img, np.float32)
    m = np.isfinite(a) if valid is None else (valid.astype(bool) & np.isfinite(a))
    if noise is None:
        noise = noise_map(a, m)
    wts = np.ones(n_scales) if weights is None else np.asarray(weights, float)
    details, coarse = starlet(a, m, n_scales, min_support)
    out = np.zeros(a.shape, np.float32)
    for j, d in enumerate(details):
        fj = (noise_factors[j] if noise_factors is not None and j < len(noise_factors)
              else STARLET_NOISE[min(j, len(STARLET_NOISE) - 1)])
        sn = noise * fj
        dj = d
        if soft_threshold > 0:
            t = soft_threshold * sn
            dj = np.sign(d) * np.maximum(np.abs(d) - t, 0)
        p = normalized_gaussian(np.where(m, dj * dj, np.nan), m, power_sigma_factor * 2 ** j, min_support)
        rms = np.sqrt(np.maximum(p, 0) + (noise_floor * sn) ** 2)
        out += (wts[j] * dj / np.maximum(rms, 1e-12)).astype(np.float32)
    if include_coarse:
        out += coarse
    out[~m] = np.nan
    return out


# ------------------------------------------------------------------------------------------------
# Tangential high-pass (along circles around the Sun)
# ------------------------------------------------------------------------------------------------
def tangential_highpass(img: np.ndarray, valid: np.ndarray | None, geometry: EclipseGeometry, *,
                        sigma_deg: float = 1.0, r_range: tuple[float, float] | None = None,
                        center="sun", n_pa: int | None = None, min_support: float = 0.3):
    """High-pass along the arc: ``I − <I>_arc`` with a Gaussian of ``sigma_deg`` in position angle.

    It removes everything that is smooth along the limb (the radial gradient, broad streamers) and
    keeps the rays.  Computed in polar coordinates and mapped back; ``NaN`` outside the data.
    """
    from scipy.ndimage import gaussian_filter1d
    from .polar import from_polar, to_polar

    a = np.asarray(img, np.float32)
    m = np.isfinite(a) if valid is None else (valid.astype(bool) & np.isfinite(a))
    if r_range is None:
        h, w = a.shape
        cx, cy = geometry.center(center)
        rmax = float(np.hypot(max(cx, w - cx), max(cy, h - cy)))
        r_range = (0.5 * geometry.sun_radius_px, rmax)
    if n_pa is None:
        n_pa = int(np.ceil(2 * np.pi * r_range[1] / 1.5))
    P = to_polar(a, geometry, center=center, r_range=r_range, n_pa=n_pa, radial="linear",
                 interp="linear", antialias=False, valid=m)
    s_cols = sigma_deg / (360.0 / n_pa)
    ok = np.isfinite(P.data)
    num = gaussian_filter1d(np.where(ok, P.data, 0.0), s_cols, axis=1, mode="wrap")
    den = gaussian_filter1d(ok.astype(np.float32), s_cols, axis=1, mode="wrap")
    smooth = np.where(ok & (den >= min_support), num / np.maximum(den, 1e-12), np.nan)
    P.data = (P.data - smooth).astype(np.float32)
    out = from_polar(P, a.shape, interp="linear")
    out[~m] = np.nan
    return out
