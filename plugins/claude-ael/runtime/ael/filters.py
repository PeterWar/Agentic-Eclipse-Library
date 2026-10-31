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

Structure-aware detail (since 1.4.1):

* Curvilinear weight – Frangi, Niessen, Vincken & Viergever (1998), MICCAI, LNCS 1496, 130.
* Steerable filters – Freeman & Adelson (1991), IEEE PAMI 13, 891; structure tensor as in Weickert (1999).
* Multiscale (pyramidal) median transform – Starck, Murtagh & Bijaoui (1998), *Image Processing and Data
  Analysis: The Multiscale Approach*, Cambridge University Press.
* Coherence-enhancing diffusion – Weickert (1999), Int. J. Computer Vision 31, 111.
* Fourier noise gating – DeForest (2017), ApJ 838, 155; the gain is the non-negative garrote of Breiman (1995),
  Technometrics 37, 373.
"""
from __future__ import annotations

import cv2
import numpy as np

from .geometry import EclipseGeometry

__all__ = ["gaussian", "normalized_gaussian", "local_mean_std", "nrgf", "mgn", "starlet", "wow",
           "noise_map", "noise_factors", "tangential_highpass", "STARLET_NOISE",
           "hessian", "hessian_eigen", "ridge_weight", "steerable_g2", "multiscale_median", "coherence_diffusion",
           "noise_gate"]

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
         bin_px: float = 1.0, robust: bool = True, min_count: int = 50, smooth_bins: float = 0.0,
         spread_about: str = "profile", partial_annuli: str = "observed"):
    """Normalising-radial-graded filter: ``(I − <I>(r)) / σ(r)`` over annuli around the centre.

    ``robust`` uses the median and 1.4826·MAD instead of mean and standard deviation (Morgan, Habbal and
    Woo 2006 use the mean and standard deviation: ``robust=False``).  Only observed pixels enter each
    annulus. Statistics are evaluated continuously in radius, not by a stepwise bin lookup; no image
    pixels are smoothed. Since 1.3.2 the spread is measured about the continuous mean profile at each
    pixel's own radius (``spread_about='profile'``), so a steep fall of brightness inside an annulus no
    longer inflates it; ``'bin'`` gives the 1.3.1 behaviour. ``NaN``: annuli with fewer than ``min_count``
    pixels, runs of fewer than four annuli, annuli where half the pixels share one value, and annuli without
    angular signal. ``smooth_bins`` smooths the annulus nodes with a local parabola (default 0, also in the
    filter bank); on a profile whose power-law index changes it bends the profile (see docs/VALIDATION_1.3.2.md).  The sky gradient is *not* removed by an NRGF (it is normalised along with the corona),
    and neither is the differential extinction of a low Sun: subtract a sky model first
    (:func:`ael.render.sky_background`) and correct the extinction (:mod:`ael.extinction`) if the field
    is large or the Sun was low. See docs/PAPER_AND_LIBRARY.md for how this differs from the layers of
    the paper's published image. ``partial_annuli='chain'`` (since 1.4.1; AEL's filter bank uses it) keeps the
    statistics of an annulus that the frame's edge or the Moon cut from jumping when a bright or a faint sector
    leaves it, which draws rings around the Sun (:func:`ael.radial.continuous_nrgf`).
    """
    from .radial import continuous_nrgf
    return continuous_nrgf(img, valid, geometry, center=center, bin_px=bin_px,
                           robust=robust, min_count=min_count, smooth_bins=smooth_bins,
                           spread_about=spread_about, partial_annuli=partial_annuli)


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
    ``h == 0``.  The result does not depend on the units of the input (until 1.3.5 an absolute floor of 1e-12
    on the local spread changed it when the input was scaled by 1e-8; found by Francisco Bitto).
    """
    a = np.asarray(img, np.float32)
    m = np.isfinite(a) if valid is None else (valid.astype(bool) & np.isfinite(a))
    w = np.ones(len(sigmas)) if weights is None else np.asarray(weights, float)
    acc = np.zeros(a.shape, np.float32)
    for s, wi in zip(sigmas, w):
        mu, sd = local_mean_std(a, m, s, min_support)
        c = np.full(a.shape, np.nan, np.float32)    # no absolute floor: the result must not depend on the units
        np.divide(a - mu, sd, out=c, where=np.isfinite(mu) & (sd > 0))
        acc += wi * np.arctan(k * c).astype(np.float32)
    acc /= float(np.sum(w))
    acc[~m] = np.nan
    if h <= 0:
        return acc
    if global_image is None:
        lo = np.nanmin(a[m]) if a0 is None else a0
        hi = np.nanmax(a[m]) if a1 is None else a1
        g = np.clip((a - lo) / (hi - lo if hi > lo else 1.0), 0, 1) ** (1.0 / gamma)
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


def _shifted(z: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """``out[y, x] = z[y + dy, x + dx]``, zero where that falls outside the array (no wrap, no reflection)."""
    h, w = z.shape
    out = np.zeros_like(z)
    if abs(dy) >= h or abs(dx) >= w:
        return out
    out[max(0, -dy):min(h, h - dy), max(0, -dx):min(w, w - dx)] = z[max(0, dy):min(h, h + dy), max(0, dx):min(w, w + dx)]
    return out


def _atrous_pairs(c: np.ndarray, mf: np.ndarray, step: int):
    """B3 à-trous smoothing over symmetric observed pairs: a tap counts only if the tap opposite it through the
    centre is observed too, so a linear trend averages to the centre value even at an edge of the data.
    Returns ``(numerator, denominator)``."""
    k0 = _B3[2] * _B3[2]
    num = k0 * mf * c
    den = k0 * mf
    for dy in range(0, 3):
        for dx in range(-2, 3):
            if dy == 0 and dx <= 0:
                continue
            k = _B3[dy + 2] * _B3[dx + 2]
            sy, sx = dy * step, dx * step
            pair = mf * _shifted(mf, sy, sx) * _shifted(mf, -sy, -sx)
            num += k * pair * (_shifted(c, sy, sx) + _shifted(c, -sy, -sx))
            den += 2 * k * pair
    return num, den


def starlet(img: np.ndarray, valid: np.ndarray | None, n_scales: int = 6, min_support: float = 0.2, *,
            pairs: bool = False):
    """Masked isotropic undecimated wavelet (starlet, B3 spline) transform.

    Returns ``(details, coarse)`` where ``details[j]`` is scale ``j+1`` (``2**j`` px holes).  With a
    mask, each smoothing is a normalised convolution, so no invalid pixel leaks into the
    coefficients; outside the data every coefficient is ``NaN``.  ``sum(details) + coarse == img`` on
    the valid pixels (exact reconstruction).  With ``pairs=True`` (since 1.3.4) each smoothing uses
    symmetric observed pairs only: next to an edge of the data a one-sided kernel would tilt every
    coefficient towards the side that has data.
    """
    a = np.asarray(img, np.float32)
    m = np.isfinite(a) if valid is None else (valid.astype(bool) & np.isfinite(a))
    mf = m.astype(np.float32)
    c = np.where(m, a, 0.0).astype(np.float32)
    details = []
    for j in range(n_scales):
        step = 2 ** j
        if pairs:
            num, den = _atrous_pairs(c, mf, step)
        else:
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
    2026 fusion, scales 1–3 (counted from 0; 2–8 px) carried 6–15× the noise that white noise would put
    there, and whitening them with white-noise factors turned the outer corona into mottle.  Scale 0
    defines the pixel noise (it is taken as white).  Scales from ``trusted_scales`` up already contain
    faint corona, so their factor is extrapolated with ``decay`` per scale.  Pass the result as
    ``noise_factors`` to :func:`wow`.
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


# ------------------------------------------------------------------------------------------------
# Structure-aware detail (since 1.4.1): the five families of the survey of 30-10-2026 that AEL did not have
# ------------------------------------------------------------------------------------------------
# Every one of them reads only observed pixels and returns NaN where there is no data.  Second derivatives need
# a value on both sides of a pixel: next to the edge of the data the missing side is the nearest observed value,
# for the difference only (a flat continuation, never a trend), and the result there is NaN again.
def nearest_index(valid: np.ndarray):
    """Indices of the nearest observed pixel of every pixel (``scipy.ndimage.distance_transform_edt``)."""
    from scipy import ndimage as ndi
    return ndi.distance_transform_edt(~valid, return_distances=False, return_indices=True)


def _filled(a: np.ndarray, valid: np.ndarray, index) -> np.ndarray:
    a = np.asarray(a, np.float32)
    if valid.all():
        return a
    return np.where(valid, a, a[tuple(index)]).astype(np.float32)


_D2 = np.array([[1.0, -2.0, 1.0]], np.float32)
_DXY = np.array([[1.0, 0.0, -1.0], [0.0, 0.0, 0.0], [-1.0, 0.0, 1.0]], np.float32) / 4


def hessian(smoothed: np.ndarray):
    """``(h_xx, h_xy, h_yy)`` of a field already smoothed at the scale of interest, by central differences."""
    s = np.ascontiguousarray(smoothed, np.float32)
    hxx = cv2.filter2D(s, -1, _D2, borderType=cv2.BORDER_REPLICATE)
    hyy = cv2.filter2D(s, -1, _D2.T, borderType=cv2.BORDER_REPLICATE)
    hxy = cv2.filter2D(s, -1, _DXY, borderType=cv2.BORDER_REPLICATE)
    return hxx, hxy, hyy


def hessian_eigen(hxx, hxy, hyy):
    """Eigenvalues ``(big, small)`` of a 2×2 symmetric field, ordered by magnitude: ``|big| ≥ |small|``."""
    root = np.sqrt((hxx - hyy) ** 2 + 4 * hxy ** 2)
    a, b = (hxx + hyy + root) / 2, (hxx + hyy - root) / 2
    first = np.abs(a) >= np.abs(b)
    return np.where(first, a, b), np.where(first, b, a)


def ridge_weight(img: np.ndarray, valid: np.ndarray | None, *, sigmas=(1.5, 3.0, 6.0), beta: float = 0.5,
                 strength: float = 1.0, index=None):
    """Curvilinear-structure weight in [0, 1] (Frangi, Niessen, Vincken & Viergever 1998, the 'vesselness' of the
    scale-normalised Hessian), the maximum over ``sigmas``.

    With ``|λ1| ≥ |λ2|``: ``R_B = |λ2| / |λ1|`` (0 on a line, 1 on a blob) and ``S = √(λ1² + λ2²)``;
    ``V = exp(−R_B² / 2β²) · (1 − exp(−S² / 2c²))``.  Both signs count: a bright ray and a dark lane are both
    structures of the corona.  ``c`` is measured, ``strength`` times the median ``S`` of the observed pixels at
    that scale, so the weight does not depend on the units.  A weight never adds anything: multiplied into a
    detail layer it keeps elongated structure (rays, loops, cavity edges at any angle) and lowers isotropic grain.
    """
    a = np.asarray(img, np.float32)
    m = np.isfinite(a) if valid is None else (valid.astype(bool) & np.isfinite(a))
    index = nearest_index(m) if index is None else index
    best = np.zeros(a.shape, np.float32)
    used = []
    for s in sigmas:
        sm = normalized_gaussian(a, m, s, min_support=0.01)
        ok = m & np.isfinite(sm)
        hxx, hxy, hyy = (s * s * h for h in hessian(_filled(np.where(ok, sm, 0), ok, index)))
        big, small = hessian_eigen(hxx, hxy, hyy)
        rb2 = (small / np.where(big == 0, 1, big)) ** 2
        s2 = big * big + small * small
        c2 = float(np.median(s2[ok])) * strength ** 2
        if not np.isfinite(c2) or c2 <= 0:
            continue
        v = np.exp(-rb2 / (2 * beta * beta)) * (1 - np.exp(-s2 / (2 * c2)))
        best = np.maximum(best, np.where(ok, v, 0).astype(np.float32))
        used.append(dict(sigma_px=s, c=float(np.sqrt(c2))))
    best[~m] = np.nan
    return best, dict(method="Frangi vesselness of the scale-normalised Hessian, both signs, maximum over scales",
                      beta=beta, strength=strength, scales=used)


def steerable_g2(img: np.ndarray, valid: np.ndarray | None, *, sigmas=(1.5, 3.0, 6.0, 12.0),
                 integration: float = 2.0, index=None):
    """Second-derivative detail steered, pixel by pixel, across the local structure (Freeman & Adelson 1991,
    'The design and use of steerable filters', IEEE PAMI 13, 891).

    The G2 response at any angle θ is ``cos²θ·h_xx + 2 sinθ cosθ·h_xy + sin²θ·h_yy``: three base convolutions give
    every orientation.  The angle is the dominant gradient direction of the structure tensor smoothed over
    ``integration`` × σ (Weickert 1999), so it follows a ray, a loop or a cavity edge whatever its angle to the
    radius, and is not set by the noise of single pixels.  Returns ``−σ²·G2θ`` averaged over ``sigmas``: positive on
    a bright filament, negative on a dark lane.
    """
    a = np.asarray(img, np.float32)
    m = np.isfinite(a) if valid is None else (valid.astype(bool) & np.isfinite(a))
    index = nearest_index(m) if index is None else index
    acc = np.zeros(a.shape, np.float32)
    for s in sigmas:
        sm = normalized_gaussian(a, m, s, min_support=0.01)
        ok = m & np.isfinite(sm)
        f = _filled(np.where(ok, sm, 0), ok, index)
        gx = cv2.Sobel(f, cv2.CV_32F, 1, 0, ksize=1, borderType=cv2.BORDER_REPLICATE) / 2
        gy = cv2.Sobel(f, cv2.CV_32F, 0, 1, ksize=1, borderType=cv2.BORDER_REPLICATE) / 2
        rho = integration * s
        j11 = normalized_gaussian(gx * gx, ok, rho, min_support=0.01)
        j12 = normalized_gaussian(gx * gy, ok, rho, min_support=0.01)
        j22 = normalized_gaussian(gy * gy, ok, rho, min_support=0.01)
        theta = 0.5 * np.arctan2(2 * j12, j11 - j22)
        c, sn = np.cos(theta), np.sin(theta)
        hxx, hxy, hyy = hessian(f)
        g2 = c * c * hxx + 2 * c * sn * hxy + sn * sn * hyy
        acc += np.where(ok & np.isfinite(g2), -s * s * g2, 0).astype(np.float32) / len(sigmas)
    acc[~m] = np.nan
    return acc


def _masked_median5(c: np.ndarray) -> np.ndarray:
    """Median of the observed values (finite) of the 5×5 neighbourhood of every observed pixel; NaN elsewhere."""
    h, w = c.shape
    out = np.full(c.shape, np.nan, np.float32)
    rows = max(1, 6_000_000 // (25 * max(w, 1)))
    pad = np.pad(c, 2, mode="constant", constant_values=np.nan)
    for y0 in range(0, h, rows):
        y1 = min(h, y0 + rows)
        taps = np.stack([pad[y0 + dy:y1 + dy, dx:dx + w] for dy in range(5) for dx in range(5)], axis=-1)
        taps.sort(axis=-1)                                  # NaN sorts last
        n = np.isfinite(taps).sum(axis=-1)
        lo, hi = np.maximum((n - 1) // 2, 0), np.maximum(n // 2, 0)
        med = 0.5 * (np.take_along_axis(taps, lo[..., None], -1)[..., 0] + np.take_along_axis(taps, hi[..., None], -1)[..., 0])
        out[y0:y1] = np.where(np.isfinite(c[y0:y1]) & (n > 0), med, np.nan)
    return out


def _pad_to(c: np.ndarray, k: int) -> np.ndarray:
    """``c`` with rows and columns of NaN (no data) added at the bottom and the right up to multiples of ``k``.

    A pyramid that reduces by ``k`` and enlarges back must keep every block whole: cropping the odd row and
    stretching the reduced image over the full size moves each enlarged block by up to half a block, and the shift
    adds up scale after scale (up to 12 px across a 10,000-pixel canvas in a first, unpublished version). Padded, every block is enlarged
    back exactly where it came from; crop the result to the original size."""
    h, w = c.shape
    H, W = -(-h // k) * k, -(-w // k) * k
    if (H, W) == (h, w):
        return np.asarray(c, np.float32)
    out = np.full((H, W), np.nan, np.float32)
    out[:h, :w] = c
    return out


def _block_mean(c: np.ndarray, k: int) -> np.ndarray:
    """k×k block mean of the finite values; NaN where a block has none. The size must be a multiple of ``k``
    (:func:`_pad_to`)."""
    h, w = c.shape
    if h % k or w % k:
        raise ValueError(f'{c.shape} is not a multiple of {k}: pad it first')
    ok = np.isfinite(c)
    num = np.where(ok, c, 0).reshape(h // k, k, w // k, k).sum(axis=(1, 3))
    den = ok.reshape(h // k, k, w // k, k).sum(axis=(1, 3))
    return np.where(den > 0, num / np.maximum(den, 1), np.nan).astype(np.float32)


def _half(c: np.ndarray) -> np.ndarray:
    """2×2 block mean of the finite values (:func:`_block_mean`, after padding an odd size with no data)."""
    return _block_mean(_pad_to(c, 2), 2)


def _up(c: np.ndarray, shape) -> np.ndarray:
    """Normalised bilinear enlargement of ``c`` (NaN = no data) to ``shape``."""
    ok = np.isfinite(c)
    size = (shape[1], shape[0])
    num = cv2.resize(np.where(ok, c, 0).astype(np.float32), size, interpolation=cv2.INTER_LINEAR)
    den = cv2.resize(ok.astype(np.float32), size, interpolation=cv2.INTER_LINEAR)
    return np.where(den > 1e-3, num / np.maximum(den, 1e-3), np.nan).astype(np.float32)


def multiscale_median(img: np.ndarray, valid: np.ndarray | None, n_scales: int = 5):
    """Pyramidal median transform (Starck, Murtagh & Bijaoui 1998, *Image Processing and Data Analysis*, §1.5;
    Starck & Murtagh 2006, ch. 2): ``c_{j+1}`` = the 5×5 median of ``c_j`` reduced by two, ``w_j = c_j − c_{j+1}``
    enlarged back.  A median ignores a few extreme pixels, so a star, a prominence or the edge of the data does not
    spread a dark ring into the scales around it, and a coefficient cannot change sign because of its neighbours.
    The medians use observed pixels only.  The image is padded with no data up to a multiple of ``2^n_scales``
    (:func:`_pad_to`), so that every scale is enlarged back exactly where it came from (a first, unpublished version
    cropped an odd size and stretched it back, and the background of the coarse scales slid by up to 12 px).  Returns
    the list of the ``n_scales`` detail planes at full size (scale j ≈ 2^j px), NaN where there is no data."""
    a = np.asarray(img, np.float32)
    m = np.isfinite(a) if valid is None else (valid.astype(bool) & np.isfinite(a))
    h, w = a.shape
    c = _pad_to(np.where(m, a, np.nan), 2 ** n_scales)
    full = c.shape
    planes = []
    for _ in range(n_scales):
        nxt = _block_mean(_masked_median5(c), 2)
        detail = c - _up(nxt, c.shape)
        planes.append((detail if detail.shape == full else _up(detail, full))[:h, :w].copy())
        c = nxt
    for p in planes:
        p[~m] = np.nan
    return planes


def coherence_diffusion(img: np.ndarray, valid: np.ndarray | None, *, time: float = 8.0, tau: float = 0.15,
                        sigma: float = 1.0, rho: float = 4.0, alpha: float = 1e-3, refresh: int = 4):
    """Coherence-enhancing diffusion (Weickert 1999, IJCV 31, 111): ``∂u/∂t = div(D ∇u)``.

    ``D`` has the eigenvectors of the structure tensor ``J_ρ(∇u_σ)``: across the structure the diffusivity is
    ``alpha`` (nothing is widened), along it ``alpha + (1 − alpha)·exp(−C / (μ1 − μ2)²)``, so only where the
    orientation is coherent does the image smooth along it.  ``C`` is measured, the median ``(μ1 − μ2)²`` of the
    observed pixels.  Explicit steps of ``tau`` up to ``time`` (in pixels² of the image passed in); the tensor is
    recomputed every ``refresh`` steps.  No flux crosses into unobserved pixels: the data is never mixed with what
    is not data.  ⚠ It smooths only: on pure noise it organises the noise into flow-like strokes, so use it with a
    null control (see docs).  Returns the diffused image, NaN outside the data."""
    u = np.where(np.isfinite(img), img, 0).astype(np.float32)
    m = np.isfinite(img) if valid is None else (valid.astype(bool) & np.isfinite(img))
    u[~m] = 0
    mf = m.astype(np.float32)
    # A flux between two pixels only if both are observed.
    ex = (mf[:, 1:] * mf[:, :-1]).astype(np.float32)
    ey = (mf[1:, :] * mf[:-1, :]).astype(np.float32)
    cx = (mf[:, 2:] * mf[:, :-2]).astype(np.float32)
    cy = (mf[2:] * mf[:-2]).astype(np.float32)
    steps = max(1, int(np.ceil(time / tau)))
    C = None
    for k in range(steps):
        if k % refresh == 0:
            us = normalized_gaussian(np.where(m, u, np.nan), m, sigma, min_support=0.01)
            us = np.where(np.isfinite(us), us, 0).astype(np.float32)
            gx = np.zeros_like(us); gy = np.zeros_like(us)
            gx[:, 1:-1] = (us[:, 2:] - us[:, :-2]) / 2; gy[1:-1] = (us[2:] - us[:-2]) / 2
            j11 = normalized_gaussian(gx * gx, m, rho, min_support=0.01)
            j12 = normalized_gaussian(gx * gy, m, rho, min_support=0.01)
            j22 = normalized_gaussian(gy * gy, m, rho, min_support=0.01)
            j11, j12, j22 = (np.where(np.isfinite(j), j, 0) for j in (j11, j12, j22))
            gap = np.sqrt((j11 - j22) ** 2 + 4 * j12 ** 2)          # μ1 − μ2
            if C is None:
                C = max(float(np.median(gap[m] ** 2)), 1e-30)
            lam_along = alpha + (1 - alpha) * np.exp(-C / np.maximum(gap * gap, 1e-30))
            # v1 (across) = (cos φ, sin φ), φ the dominant gradient direction; v2 (along) ⟂ v1
            phi = 0.5 * np.arctan2(2 * j12, j11 - j22)
            c, s = np.cos(phi), np.sin(phi)
            d11 = (alpha * c * c + lam_along * s * s).astype(np.float32)
            d12 = ((alpha - lam_along) * c * s).astype(np.float32)
            d22 = (alpha * s * s + lam_along * c * c).astype(np.float32)
        # Fluxes on the half-grid: x-faces carry d11·u_x + d12·u_y, y-faces d12·u_x + d22·u_y (central y/x gradients).
        # The cross gradients count only where both neighbours are observed: no unobserved zero enters a flux.
        ux = (u[:, 1:] - u[:, :-1]) * ex
        uy_c = np.zeros_like(u); uy_c[1:-1] = (u[2:] - u[:-2]) / 2 * cy
        uy_x = 0.5 * (uy_c[:, 1:] + uy_c[:, :-1]) * ex
        fx = 0.5 * (d11[:, 1:] + d11[:, :-1]) * ux + 0.5 * (d12[:, 1:] + d12[:, :-1]) * uy_x
        uy = (u[1:] - u[:-1]) * ey
        ux_c = np.zeros_like(u); ux_c[:, 1:-1] = (u[:, 2:] - u[:, :-2]) / 2 * cx
        ux_y = 0.5 * (ux_c[1:] + ux_c[:-1]) * ey
        fy = 0.5 * (d12[1:] + d12[:-1]) * ux_y + 0.5 * (d22[1:] + d22[:-1]) * uy
        div = np.zeros_like(u)
        div[:, :-1] += fx; div[:, 1:] -= fx
        div[:-1] += fy; div[1:] -= fy
        u = (u + tau * div * mf).astype(np.float32)
    out = np.where(m, u, np.nan).astype(np.float32)
    return out, dict(method="coherence-enhancing diffusion (Weickert 1999), explicit, no flux into unobserved pixels",
                     time=time, tau=tau, steps=steps, sigma=sigma, rho=rho, alpha=alpha, C=C, refresh=refresh)


def noise_gate(img: np.ndarray, valid: np.ndarray | None, geometry: EclipseGeometry, *, tile: int = 32,
               step: int = 8, gamma: float = 3.0, high_k: float = 0.6, r_range: tuple[float, float] | None = None):
    """Fourier noise gating (DeForest 2017, ApJ 838, 155) on overlapping tiles of the corona unrolled in
    (ln r, position angle).

    In that plane a ray is nearly a line of constant angle, so its energy gathers on a narrow line of the tile's
    spectrum, while the noise spreads over all of it.  Each tile (Hann window, a quarter of its size apart) is
    transformed; the noise level of a row of tiles (one ln r) is the median, over the row, of the rms magnitude of
    the coefficients above ``high_k`` of the Nyquist frequency and off the two axes of the plane, where rays
    (k_ln r ≈ 0) and arcs (k_PA ≈ 0) put their energy (white noise); each coefficient is scaled by the
    non-negative garrote ``max(0, 1 − (γN)² / |F|²)`` (Breiman 1995), which keeps a strong coefficient whole and
    removes one at the noise level.  What the gate removes is mapped back to the image and subtracted from it: the
    rest of the image keeps its own pixels.  Unobserved cells of a tile count as zero in its transform (the input
    is a residual about zero) and the result is NaN there.  Returns (gated image, information)."""
    from .polar import from_polar, to_polar

    a = np.asarray(img, np.float32)
    m = np.isfinite(a) if valid is None else (valid.astype(bool) & np.isfinite(a))
    h, w = a.shape
    cx, cy = geometry.sun_xy
    yy, xx = np.nonzero(m)
    rr = np.hypot(xx - cx, yy - cy)
    del yy, xx
    if r_range is None:
        r_range = (max(float(rr.min()), 1.0), float(rr.max()) + 1.0)
    r0, r1 = r_range
    # ~1 px along the arc at 2 R☉ and along ln r at the same radius: fine detail kept where it can be measured.
    ref = min(max(2.0 * geometry.sun_radius_px, r0), r1)
    n_pa = int(np.ceil(2 * np.pi * ref / tile)) * tile
    n_r = int(np.ceil(np.log(r1 / r0) * ref))
    P = to_polar(np.where(m, a, np.nan), geometry, r_range=(r0, r1), n_r=n_r, n_pa=n_pa, radial="log",
                 interp="linear", antialias=False, valid=m)
    data = P.data
    ok = np.isfinite(data)
    z = np.where(ok, data, 0).astype(np.float32)
    win1 = np.sin(np.pi * (np.arange(tile) + 0.5) / tile) ** 2
    win = np.outer(win1, win1).astype(np.float32)
    k = np.fft.fftfreq(tile)
    kk = np.hypot(k[:, None], k[None, :]) / 0.5
    # A ray is a line of constant angle (all its energy at k_ln r ≈ 0) and an arc one of constant radius (k_PA ≈ 0):
    # the noise is measured off both axes, where only noise reaches the high frequencies.
    off_axes = (np.abs(k)[:, None] > 1.5 / tile) & (np.abs(k)[None, :] > 1.5 / tile)
    high = (kk >= high_k) & off_axes
    # Rows padded so every row of the plane is covered by full tiles; angles wrap.
    pad = tile
    zp = np.pad(z, ((pad, pad), (0, 0)))
    okp = np.pad(ok, ((pad, pad), (0, 0)))
    removed = np.zeros_like(zp)
    weight = np.zeros_like(zp)
    starts = range(0, zp.shape[0] - tile + 1, step)
    cols = np.arange(0, n_pa, step)
    noise_rows = []
    for y0 in starts:
        band = zp[y0:y0 + tile]
        bok = okp[y0:y0 + tile]
        ext = np.concatenate([band, band[:, :tile]], axis=1)
        eok = np.concatenate([bok, bok[:, :tile]], axis=1)
        tiles = np.stack([ext[:, x0:x0 + tile] for x0 in cols])
        share = np.stack([eok[:, x0:x0 + tile].mean() for x0 in cols])
        F_ = np.fft.fft2(tiles * win)
        mag = np.abs(F_)
        observed = share >= 0.5
        if not observed.any():
            continue
        level = float(np.median(np.sqrt(np.mean(mag[observed][:, high] ** 2, axis=1))))
        noise_rows.append(level)
        g = np.maximum(0.0, 1.0 - (gamma * level) ** 2 / np.maximum(mag ** 2, 1e-30))
        gone = np.real(np.fft.ifft2(F_ * (1 - g))).astype(np.float32) * win
        acc = np.zeros((tile, n_pa + tile), np.float32)
        wsum = np.zeros((tile, n_pa + tile), np.float32)
        for i, x0 in enumerate(cols):
            acc[:, x0:x0 + tile] += gone[i]
            wsum[:, x0:x0 + tile] += win * win
        acc[:, :tile] += acc[:, n_pa:n_pa + tile]; wsum[:, :tile] += wsum[:, n_pa:n_pa + tile]
        removed[y0:y0 + tile] += acc[:, :n_pa]
        weight[y0:y0 + tile] += wsum[:, :n_pa]
    removed = np.where(weight > 0, removed / np.maximum(weight, 1e-12), 0)[pad:pad + n_r]
    P.data = np.where(ok, removed, np.nan).astype(np.float32)
    back = from_polar(P, (h, w), interp="linear")
    out = np.where(m & np.isfinite(back), a - back, np.where(m, a, np.nan)).astype(np.float32)
    return out, dict(method="Fourier noise gating on (ln r, PA) tiles, non-negative garrote, removed part mapped "
                            "back and subtracted", tile=tile, step=step, gamma=gamma, high_k=high_k,
                     polar_shape=[n_r, n_pa], r_range_px=[r0, r1],
                     noise_levels=dict(min=float(min(noise_rows)) if noise_rows else None,
                                       max=float(max(noise_rows)) if noise_rows else None))
