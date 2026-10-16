"""Geometry of an eclipse image: centres, radii, orientation and position angles.

Conventions (used everywhere in the package):

* Pixel coordinates are ``(x, y)`` with ``x`` to the right and ``y`` down; the centre of the first
  pixel is ``(0, 0)``.
* ``north_deg`` is the direction of celestial north on the image, in degrees **clockwise from image
  up**.  An image with north up has ``north_deg = 0``; north pointing to the upper right at 45° has
  ``north_deg = 45``.
* Position angle (PA) is measured from celestial north through east, as solar astronomers do.  On a
  normal (not mirrored) sky image east is 90° *counter-clockwise* from north; set ``mirrored=True``
  for images flipped by a diagonal mirror.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

__all__ = ["EclipseGeometry", "position_angle", "image_angle_of_pa", "fit_limb"]


@dataclass
class EclipseGeometry:
    """Where things are on one image (or canvas)."""

    shape: tuple[int, int]
    sun_xy: tuple[float, float]
    sun_radius_px: float
    moon_xy: tuple[float, float] | None = None
    moon_radius_px: float | None = None
    north_deg: float = 0.0
    mirrored: bool = False
    arcsec_per_px: float | None = None
    note: str = ""

    # --- construction / persistence -------------------------------------------------------------
    def to_json(self, path: str | Path | None = None) -> str:
        d = asdict(self)
        txt = json.dumps(d, indent=1, ensure_ascii=False)
        if path is not None:
            Path(path).write_text(txt, encoding="utf-8")
        return txt

    @classmethod
    def from_json(cls, src: str | Path | dict) -> "EclipseGeometry":
        if isinstance(src, dict):
            d = dict(src)
        elif isinstance(src, str) and src.lstrip().startswith("{"):
            d = json.loads(src)
        else:
            d = json.loads(Path(src).read_text(encoding="utf-8"))
        d["shape"] = tuple(d["shape"])
        d["sun_xy"] = tuple(d["sun_xy"])
        if d.get("moon_xy") is not None:
            d["moon_xy"] = tuple(d["moon_xy"])
        return cls(**d)

    def scaled(self, factor: float) -> "EclipseGeometry":
        """Geometry of the same image resampled by ``factor`` (e.g. 0.25 for a quarter-size view).

        Uses the pixel-centre convention of ``cv2.resize``: x' = (x + 0.5)·f − 0.5.
        """
        f = float(factor)
        tr = lambda xy: None if xy is None else ((xy[0] + 0.5) * f - 0.5, (xy[1] + 0.5) * f - 0.5)
        h, w = self.shape
        return EclipseGeometry(
            shape=(int(round(h * f)), int(round(w * f))),
            sun_xy=tr(self.sun_xy), sun_radius_px=self.sun_radius_px * f,
            moon_xy=tr(self.moon_xy),
            moon_radius_px=None if self.moon_radius_px is None else self.moon_radius_px * f,
            north_deg=self.north_deg, mirrored=self.mirrored,
            arcsec_per_px=None if self.arcsec_per_px is None else self.arcsec_per_px / f,
            note=(self.note + f" | scaled x{f:g}").strip(" |"),
        )

    def shifted(self, dx: float, dy: float, shape: tuple[int, int] | None = None) -> "EclipseGeometry":
        """Geometry after a crop/pad that moves every pixel by ``(dx, dy)``."""
        mv = lambda xy: None if xy is None else (xy[0] + dx, xy[1] + dy)
        return EclipseGeometry(shape=shape or self.shape, sun_xy=mv(self.sun_xy),
                               sun_radius_px=self.sun_radius_px, moon_xy=mv(self.moon_xy),
                               moon_radius_px=self.moon_radius_px, north_deg=self.north_deg,
                               mirrored=self.mirrored, arcsec_per_px=self.arcsec_per_px, note=self.note)

    # --- maps -----------------------------------------------------------------------------------
    def center(self, which: str | tuple[float, float] = "sun") -> tuple[float, float]:
        if isinstance(which, tuple):
            return which
        if which == "sun":
            return self.sun_xy
        if which == "moon":
            if self.moon_xy is None:
                raise ValueError("moon_xy is not set in this geometry")
            return self.moon_xy
        raise ValueError(f"unknown centre {which!r}")

    def radius_map(self, which="sun", dtype=np.float32) -> np.ndarray:
        """Distance of every pixel to the chosen centre, in pixels."""
        cx, cy = self.center(which)
        h, w = self.shape
        y = (np.arange(h, dtype=np.float64) - cy)[:, None]
        x = (np.arange(w, dtype=np.float64) - cx)[None, :]
        return np.hypot(x, y).astype(dtype)

    def rsun_map(self, which="sun", dtype=np.float32) -> np.ndarray:
        """Distance in solar radii."""
        return (self.radius_map(which, np.float64) / self.sun_radius_px).astype(dtype)

    def pa_map(self, which="sun", dtype=np.float32) -> np.ndarray:
        """Position angle (deg, 0–360, north through east) of every pixel around the chosen centre."""
        cx, cy = self.center(which)
        h, w = self.shape
        y = (np.arange(h, dtype=np.float64) - cy)[:, None]
        x = (np.arange(w, dtype=np.float64) - cx)[None, :]
        return position_angle(x, y, self.north_deg, self.mirrored).astype(dtype)

    def moon_mask(self, margin_px: float = 0.0) -> np.ndarray:
        """True inside the lunar disc enlarged by ``margin_px``."""
        if self.moon_xy is None or self.moon_radius_px is None:
            raise ValueError("moon geometry is not set")
        return self.radius_map("moon", np.float32) <= (self.moon_radius_px + margin_px)


def position_angle(dx, dy, north_deg: float = 0.0, mirrored: bool = False):
    """PA (deg, 0–360) of the vector ``(dx, dy)`` (image coordinates, y down)."""
    a = np.degrees(np.arctan2(dx, -dy))  # clockwise from image up
    pa = (a - north_deg) if mirrored else (north_deg - a)
    return np.mod(pa, 360.0)


def image_angle_of_pa(pa_deg, north_deg: float = 0.0, mirrored: bool = False):
    """Image direction (deg clockwise from up) of a position angle.  Inverse of :func:`position_angle`."""
    pa = np.asarray(pa_deg, dtype=np.float64)
    return np.mod((north_deg + pa) if mirrored else (north_deg - pa), 360.0)


def direction_of_pa(pa_deg, north_deg: float = 0.0, mirrored: bool = False):
    """Unit vector ``(ux, uy)`` in image coordinates pointing towards position angle ``pa_deg``."""
    a = np.radians(image_angle_of_pa(pa_deg, north_deg, mirrored))
    return np.sin(a), -np.cos(a)


def fit_limb(image: np.ndarray, approx_xy: tuple[float, float], approx_r: float, *,
             n_rays: int = 1440, search_frac: float = 0.06, smooth_px: float = 1.2,
             valid: np.ndarray | None = None, exclude_pa: list[tuple[float, float]] | None = None,
             north_deg: float = 0.0, mirrored: bool = False, clip_sigma: float = 2.5,
             n_iter: int = 6, use_log: bool = False) -> dict:
    """Fit a circle to the lunar limb (dark disc on bright corona).

    Along ``n_rays`` rays the edge is the maximum of the outward derivative of the (lightly smoothed)
    intensity within ``approx_r·(1 ± search_frac)``, refined to sub-pixel with a parabola.  The linear
    intensity is the default: with ``log`` the maximum slides into the dark tail of the blurred edge
    (measured: 3 px inside a 62 px Moon with a 1.1 px PSF).  A geometric circle fit with
    iterative sigma clipping follows.  Prominences and Baily's beads make local outliers: they are
    clipped, and whole PA ranges can be excluded with ``exclude_pa=[(pa0, pa1), ...]``.

    Returns ``dict(xy, r, rms, n_used, n_rays, points)``.  The residual rms is the honest measure of
    how circular the observed limb is; with a real Moon (relief, refraction) expect 0.3–2 px.
    """
    import cv2
    from scipy.optimize import least_squares

    img = np.asarray(image, dtype=np.float32)
    if img.ndim == 3:
        img = img.mean(axis=2)
    ok = np.isfinite(img) & (img > 0)
    if valid is not None:
        ok &= valid.astype(bool)
    lg = np.where(ok, np.log(np.where(ok, img, 1.0)) if use_log else img, 0.0).astype(np.float32)
    wt = ok.astype(np.float32)
    if smooth_px > 0:
        k = int(2 * np.ceil(3 * smooth_px) + 1)
        num = cv2.GaussianBlur(lg * wt, (k, k), smooth_px, borderType=cv2.BORDER_CONSTANT)
        den = cv2.GaussianBlur(wt, (k, k), smooth_px, borderType=cv2.BORDER_CONSTANT)
        lg = np.where(den > 0.5, num / np.maximum(den, 1e-6), np.nan).astype(np.float32)
    else:
        lg[~ok] = np.nan

    cx0, cy0 = approx_xy
    theta = np.linspace(0, 2 * np.pi, n_rays, endpoint=False)
    rr = np.arange(approx_r * (1 - search_frac), approx_r * (1 + search_frac), 0.25)
    X = (cx0 + rr[None, :] * np.sin(theta)[:, None]).astype(np.float32)
    Y = (cy0 - rr[None, :] * np.cos(theta)[:, None]).astype(np.float32)
    prof = cv2.remap(np.nan_to_num(lg, nan=0.0), X, Y, cv2.INTER_LINEAR, borderValue=0.0)
    good = cv2.remap(np.isfinite(lg).astype(np.float32), X, Y, cv2.INTER_LINEAR, borderValue=0.0) > 0.999
    d = np.gradient(prof, axis=1)
    d[~good] = -np.inf
    i = np.argmax(d, axis=1)
    pts, keep = [], []
    pa_ray = position_angle(np.sin(theta), -np.cos(theta), north_deg, mirrored)
    for k in range(n_rays):
        j = i[k]
        if not np.isfinite(d[k, j]) or j <= 0 or j >= len(rr) - 1 or not good[k, j - 1:j + 2].all():
            continue
        y0, y1, y2 = d[k, j - 1], d[k, j], d[k, j + 1]
        den_ = (y0 - 2 * y1 + y2)
        off = 0.5 * (y0 - y2) / den_ if den_ != 0 else 0.0
        r = rr[j] + np.clip(off, -1, 1) * (rr[1] - rr[0])
        if exclude_pa:
            pa = pa_ray[k]
            if any((a0 <= pa <= a1) if a0 <= a1 else (pa >= a0 or pa <= a1) for a0, a1 in exclude_pa):
                continue
        pts.append((cx0 + r * np.sin(theta[k]), cy0 - r * np.cos(theta[k])))
    pts = np.asarray(pts, dtype=np.float64)
    if len(pts) < 20:
        raise RuntimeError(f"fit_limb: only {len(pts)} edge points found; check approx_xy/approx_r")

    use = np.ones(len(pts), bool)
    p = np.array([cx0, cy0, approx_r], dtype=np.float64)
    for _ in range(n_iter):
        res = least_squares(lambda q: np.hypot(pts[use, 0] - q[0], pts[use, 1] - q[1]) - q[2], p, loss="soft_l1")
        p = res.x
        resid = np.hypot(pts[:, 0] - p[0], pts[:, 1] - p[1]) - p[2]
        s = 1.4826 * np.median(np.abs(resid[use] - np.median(resid[use])))
        new = np.abs(resid - np.median(resid[use])) <= clip_sigma * max(s, 0.05)
        if (new == use).all():
            break
        use = new
    resid = np.hypot(pts[:, 0] - p[0], pts[:, 1] - p[1]) - p[2]
    return dict(xy=(float(p[0]), float(p[1])), r=float(p[2]), rms=float(np.sqrt(np.mean(resid[use] ** 2))),
                n_used=int(use.sum()), n_rays=int(n_rays), points=pts[use])
