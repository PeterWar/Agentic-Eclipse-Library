"""Polar ("unrolled") views of the corona and their exact inverse.

``to_polar`` resamples an image on a (radius × position-angle) grid around the Sun or the Moon.  The
unrolled view puts the limb on a straight line and the rays vertical, which is how the fine structure
of the inner corona is easiest to read (and a good way to judge a processing: any ring, seam or
azimuthal artefact becomes a horizontal or vertical line).

Two details matter for quality and are handled here:

* **Anti-aliasing.**  Far from the centre one column spans more than one input pixel along the arc
  (and, in log-radial mode, one row spans several pixels along the radius).  Sampling a single point
  per output pixel would alias the fine rays.  Each output pixel is the mean of enough sub-samples to
  keep the input spacing below ~0.7 px.
* **No invention.**  Output pixels whose interpolation support is not fully inside the valid data are
  ``NaN``; nothing is filled, extended or mirrored.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

from .geometry import EclipseGeometry, direction_of_pa, position_angle

__all__ = ["PolarImage", "to_polar", "from_polar", "remap_valid"]

_INTERP = {"nearest": cv2.INTER_NEAREST, "linear": cv2.INTER_LINEAR, "cubic": cv2.INTER_CUBIC,
           "lanczos": cv2.INTER_LANCZOS4}


@dataclass
class PolarImage:
    """Result of :func:`to_polar`.  Row 0 is the *smallest* radius; use :meth:`display` to flip."""

    data: np.ndarray
    r: np.ndarray                     # radius (px from the centre) of each row
    pa: np.ndarray                    # position angle (deg) of each column
    center_xy: tuple[float, float]
    center: str
    radial: str                       # 'linear' or 'log'
    pa_start: float
    pa_span: float
    geometry: EclipseGeometry
    meta: dict = field(default_factory=dict)

    def display(self) -> np.ndarray:
        """Data with the radius increasing upwards (limb at the bottom), as usually shown."""
        return self.data[::-1]

    def row_of_radius(self, r_px: float) -> float:
        """Fractional row index (in :attr:`data`, not flipped) of radius ``r_px``."""
        n = len(self.r) - 1
        if self.radial == "log":
            return (np.log(r_px) - np.log(self.r[0])) / (np.log(self.r[-1]) - np.log(self.r[0])) * n
        return (r_px - self.r[0]) / (self.r[-1] - self.r[0]) * n

    def column_of_pa(self, pa_deg: float) -> float:
        """Fractional column index of a position angle (column centres at pa_start + (j + ½)·Δ)."""
        d = self.pa_span / len(self.pa)
        return ((pa_deg - self.pa_start) % 360.0) / d - 0.5


def _radii(r0: float, r1: float, n: int, radial: str) -> np.ndarray:
    if radial == "linear":
        return np.linspace(r0, r1, n)
    if radial == "log":
        return np.exp(np.linspace(np.log(r0), np.log(r1), n))
    raise ValueError("radial must be 'linear' or 'log'")


class _Prepared:
    """Masked source ready for repeated remapping (mask as float, values zeroed outside the data)."""

    def __init__(self, src: np.ndarray, valid: np.ndarray):
        self.m = np.ascontiguousarray(valid.astype(np.float32))
        chans = [src] if src.ndim == 2 else [src[..., c] for c in range(src.shape[2])]
        self.v = [np.ascontiguousarray(np.where(valid, np.nan_to_num(c, nan=0.0, posinf=0.0, neginf=0.0), 0.0)
                                       .astype(np.float32)) for c in chans]
        self.multichannel = src.ndim == 3

    def remap(self, X: np.ndarray, Y: np.ndarray, interp: str = "cubic") -> np.ndarray:
        kw = dict(borderMode=cv2.BORDER_CONSTANT, borderValue=0.0)
        ml = cv2.remap(self.m, X, Y, cv2.INTER_LINEAR, **kw)
        full2x2 = ml >= 0.9999
        if interp not in ("linear", "nearest"):
            mh = cv2.remap(self.m, X, Y, _INTERP[interp], **kw)
            full_hi = full2x2 & (np.abs(mh - 1.0) < 1e-4)
        if interp == "nearest":
            mn = cv2.remap(self.m, X, Y, cv2.INTER_NEAREST, **kw) > 0.5
        outs = []
        for v in self.v:
            if interp == "nearest":
                o = np.where(mn, cv2.remap(v, X, Y, cv2.INTER_NEAREST, **kw), np.nan)
            else:
                lin = cv2.remap(v, X, Y, cv2.INTER_LINEAR, **kw)
                if interp == "linear":
                    o = np.where(full2x2, lin, np.nan)
                else:
                    hi = cv2.remap(v, X, Y, _INTERP[interp], **kw)
                    # Full kernel support: high-order value.  Only the 2x2 support valid (next to an
                    # edge of the data): bilinear from observed pixels.  Otherwise: no data.
                    o = np.where(full_hi, hi, np.where(full2x2, lin, np.nan))
            outs.append(o.astype(np.float32))
        return np.stack(outs, axis=-1) if self.multichannel else outs[0]


def remap_valid(src: np.ndarray, X: np.ndarray, Y: np.ndarray, interp: str = "cubic",
                valid: np.ndarray | None = None) -> np.ndarray:
    """``cv2.remap`` returning NaN wherever the interpolation support leaves the observed data."""
    if valid is None:
        valid = np.isfinite(src) if src.ndim == 2 else np.isfinite(src).all(axis=2)
    return _Prepared(src.astype(np.float32, copy=False), valid).remap(X.astype(np.float32), Y.astype(np.float32), interp)


def to_polar(img: np.ndarray, geometry: EclipseGeometry, *, center: str | tuple = "sun",
             r_range: tuple[float, float] | None = None, n_r: int | None = None, n_pa: int | None = None,
             pa_start: float = 0.0, pa_span: float = 360.0, radial: str = "linear",
             interp: str = "cubic", antialias: bool = True, valid: np.ndarray | None = None,
             max_subsample: int = 12, chunk_samples: int = 12_000_000) -> PolarImage:
    """Unroll ``img`` around the Sun (default) or the Moon.

    Parameters
    ----------
    r_range : (r_min, r_max) in pixels from the chosen centre.  Default: 0.9–3 solar radii.
    n_r, n_pa : output size.  Defaults give ~1 px steps at r_min (radius) and at the geometric mean
        radius (angle).
    pa_start, pa_span : first column and angular extent; columns run towards increasing PA
        (north → east → south → west).
    radial : 'linear' (equal pixels per radius step) or 'log' (equal ratios; more room for the inner
        corona).
    valid : boolean mask of observed pixels (default: finite pixels).
    """
    a = np.asarray(img)
    if a.ndim not in (2, 3):
        raise ValueError("img must be 2-D or 3-D (H, W, C)")
    a = a.astype(np.float32, copy=False)
    if valid is None:
        valid = np.isfinite(a) if a.ndim == 2 else np.isfinite(a).all(axis=2)
    cx, cy = center if isinstance(center, tuple) else geometry.center(center)
    cname = center if isinstance(center, str) else "custom"
    if r_range is None:
        r_range = (0.9 * geometry.sun_radius_px, 3.0 * geometry.sun_radius_px)
    r0, r1 = float(r_range[0]), float(r_range[1])
    if n_r is None:
        n_r = int(round(r1 - r0)) + 1 if radial == "linear" else int(round(np.log(r1 / r0) * r0)) + 1
    if n_pa is None:
        n_pa = int(round(np.radians(pa_span) * np.sqrt(r0 * r1)))
    rr = _radii(r0, r1, n_r, radial)
    dpa = pa_span / n_pa
    pa = pa_start + (np.arange(n_pa) + 0.5) * dpa

    # Sub-sampling factors per row: along the arc (tangential footprint) and along the radius.
    dr = np.gradient(rr) if n_r > 1 else np.array([1.0])
    s_t = np.ones(n_r, int)
    s_r = np.ones(n_r, int)
    if antialias:
        s_t = np.clip(np.ceil(rr * np.radians(dpa) / 0.7), 1, max_subsample).astype(int)
        s_r = np.clip(np.ceil(np.abs(dr) / 0.7), 1, max_subsample).astype(int)

    prep = _Prepared(a, valid)
    shape_out = (n_r, n_pa) + ((a.shape[2],) if a.ndim == 3 else ())
    out = np.full(shape_out, np.nan, np.float32)
    i = 0
    while i < n_r:
        st, sr = int(s_t[i]), int(s_r[i])
        max_rows = max(1, chunk_samples // (n_pa * st * sr))
        j = i
        while j + 1 < n_r and s_t[j + 1] == st and s_r[j + 1] == sr and (j + 1 - i) < max_rows:
            j += 1
        rows = np.arange(i, j + 1)
        off_r = (np.arange(sr) + 0.5) / sr - 0.5
        if radial == "log" and n_r > 1:
            lstep = (np.log(r1) - np.log(r0)) / (n_r - 1)
            rsub = np.exp(np.log(rr[rows])[:, None] + off_r[None, :] * lstep).reshape(-1)
        else:
            rsub = (rr[rows][:, None] + off_r[None, :] * dr[rows][:, None]).reshape(-1)
        off_t = ((np.arange(st) + 0.5) / st - 0.5) * dpa
        pasub = (pa[:, None] + off_t[None, :]).reshape(-1)
        ux, uy = direction_of_pa(pasub, geometry.north_deg, geometry.mirrored)
        X = (cx + rsub[:, None] * ux[None, :]).astype(np.float32)
        Y = (cy + rsub[:, None] * uy[None, :]).astype(np.float32)
        sub = prep.remap(X, Y, interp)
        if sr > 1 or st > 1:
            tail = sub.shape[2:]
            # NaN propagates: a cell is valid only if every sub-sample is (no partial averages at edges)
            sub = sub.reshape((len(rows), sr, n_pa, st) + tail).mean(axis=(1, 3))
        out[i:j + 1] = sub
        i = j + 1
    meta = dict(antialias=bool(antialias), interp=interp, max_subsample=int(max_subsample),
                s_t_max=int(s_t.max()), s_r_max=int(s_r.max()))
    return PolarImage(data=out, r=rr, pa=pa, center_xy=(float(cx), float(cy)), center=cname, radial=radial,
                      pa_start=float(pa_start), pa_span=float(pa_span), geometry=geometry, meta=meta)


def from_polar(p: PolarImage, shape: tuple[int, int] | None = None, interp: str = "cubic") -> np.ndarray:
    """Map a polar image back to the image plane (exact inverse of the :func:`to_polar` geometry).

    Pixels outside the polar grid (radius or angle) are ``NaN``.  Full-circle grids wrap in angle.
    """
    h, w = shape or p.geometry.shape
    cx, cy = p.center_xy
    y = (np.arange(h, dtype=np.float64) - cy)[:, None]
    x = (np.arange(w, dtype=np.float64) - cx)[None, :]
    r = np.hypot(x, y)
    pa = position_angle(x, y, p.geometry.north_deg, p.geometry.mirrored)
    n_r, n_pa = p.data.shape[:2]
    if p.radial == "log":
        ri = (np.log(np.maximum(r, 1e-9)) - np.log(p.r[0])) / (np.log(p.r[-1]) - np.log(p.r[0])) * (n_r - 1)
    else:
        ri = (r - p.r[0]) / (p.r[-1] - p.r[0]) * (n_r - 1)
    dpa = p.pa_span / n_pa
    ci = ((pa - p.pa_start) % 360.0) / dpa - 0.5
    data = p.data
    if abs(p.pa_span - 360.0) < 1e-9:
        pad = 4  # cyclic padding: enough for the cubic/Lanczos support on both sides
        data = np.concatenate([data[:, -pad:], data, data[:, :pad]], axis=1)
        ci = ci + pad
    valid = np.isfinite(data) if data.ndim == 2 else np.isfinite(data).all(axis=2)
    return remap_valid(data.astype(np.float32), ci.astype(np.float32), ri.astype(np.float32), interp, valid)
