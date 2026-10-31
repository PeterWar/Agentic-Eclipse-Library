"""Geometry of an eclipse image: centres, radii, orientation and position angles.

Conventions (used everywhere in the package):

* Pixel coordinates are ``(x, y)`` with ``x`` to the right and ``y`` down; the centre of the first
  pixel is ``(0, 0)``.
* ``north_deg`` is the direction of celestial north on the image, in degrees **clockwise from image
  up**.  An image with north up has ``north_deg = 0``; north pointing to the upper right at 45° has
  ``north_deg = 45``.
* Position angle (PA) is measured from celestial north through east, as solar astronomers do.  On a
  normal (not mirrored) sky image east is 90° *counter-clockwise* from north; set ``mirrored=True``
  for images flipped by the optics or by software. An odd number of reflections mirrors the image (a star
  diagonal; a camera at the prime focus of a single mirror with no secondary); an even number does not (a camera
  lens, a refractor or refractor astrograph, a Newtonian, a Cassegrain straight through). Camera software can
  deliver bottom-up frames (rows in reverse order); a FITS header may say so with ``ROWORDER``, which
  :func:`ael.io.load_array` does not read (it keeps the rows as stored).  Never assume ``mirrored=False`` for a new
  camera: take the mirror state from stars, a landscape or an annotated frame, or test it against a
  coronagraph with :func:`ael.coronagraph.scan_mirror`.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

__all__ = ["EclipseGeometry", "position_angle", "image_angle_of_pa", "fit_limb", "find_disc", "measure_geometry"]


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


# --- geometry measured on the image -------------------------------------------------------------------
def _circle(points: np.ndarray) -> tuple[float, float, float, float]:
    """Circle through ``points`` (N, 2): algebraic start, then a geometric fit with a robust loss.  Returns
    ``(cx, cy, r, rms)``."""
    from scipy.optimize import least_squares

    origin = points.mean(axis=0)
    x, y = points[:, 0] - origin[0], points[:, 1] - origin[1]
    sol = np.linalg.lstsq(np.column_stack([x, y, np.ones_like(x)]), -(x * x + y * y), rcond=None)[0]
    cx, cy = -sol[0] / 2, -sol[1] / 2
    r = float(np.sqrt(max(cx * cx + cy * cy - sol[2], 1.0)))
    fit = least_squares(lambda q: np.hypot(x - q[0], y - q[1]) - q[2], (cx, cy, r), loss="soft_l1", f_scale=0.5)
    cx, cy, r = fit.x
    resid = np.hypot(x - cx, y - cy) - r
    return float(cx + origin[0]), float(cy + origin[1]), float(r), float(np.sqrt(np.mean(resid ** 2)))


def _luminance_and_valid(image, valid):
    img = np.asarray(image)
    ok = None
    if img.ndim == 3 and img.shape[-1] == 4:            # RGBA: the alpha marks the observed pixels
        ok = np.asarray(img[..., 3], np.float32) > 0
        img = img[..., :3]
    lum = np.asarray(img, np.float32).mean(axis=2) if img.ndim == 3 else np.asarray(img, np.float32)
    finite = np.isfinite(lum)
    ok = finite if ok is None else ok & finite
    if valid is not None:
        ok &= np.asarray(valid, bool)
    return lum, ok


def _region_without_data(empty: np.ndarray):
    """The largest closed, nearly round region without data that does not touch the frame, or None."""
    import cv2

    h, w = empty.shape
    # Every connected region without data, also one that lies inside the observed field while that field lies
    # inside a frame-wide border without data (the outer boundaries of a two-level hierarchy).
    contours, hierarchy = cv2.findContours(empty.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if hierarchy is None:
        return None
    outer = [c for c, link in zip(contours, hierarchy[0]) if link[3] < 0]
    min_r = max(8.0, 0.01 * min(h, w))
    for contour in sorted(outer, key=cv2.contourArea, reverse=True):
        area = cv2.contourArea(contour)
        if area < np.pi * min_r ** 2:
            break
        pts = contour[:, 0].astype(np.float64)
        if pts[:, 0].min() <= 0 or pts[:, 1].min() <= 0 or pts[:, 0].max() >= w - 1 or pts[:, 1].max() >= h - 1:
            continue
        cx, cy, r, rms = _circle(pts)
        fill = area / (np.pi * r * r)
        if rms <= 0.03 * r and 0.85 <= fill <= 1.1:
            # The contour runs through the centres of the outermost empty pixels: the edge of the data is half a
            # pixel further out.
            return dict(xy=(cx, cy), r=r + 0.5, rms=rms, n_points=int(len(pts)), method="region without data")
    return None


def _dark_disc_candidates(lum: np.ndarray, ok: np.ndarray, max_side: int):
    """Circles of a Hough search on a robustly stretched copy reduced to ``max_side``, ranked by how much darker the
    disc is than a ring just outside it and by how much of its edge goes from dark to bright."""
    import cv2

    h, w = lum.shape
    values = lum[ok]
    if values.size < 1000:
        raise RuntimeError("find_disc: fewer than 1000 observed pixels")
    lo, hi = np.percentile(values, [1.0, 99.8])
    if not hi > lo:
        raise RuntimeError("find_disc: the image has no contrast")
    s = np.where(ok, np.clip((lum - lo) / (hi - lo), 0, 1), 0).astype(np.float32)
    s = (np.arcsinh(10 * s) / np.arcsinh(10)).astype(np.float32)
    f = min(1.0, max_side / max(h, w))
    small = cv2.resize(s, (max(1, round(w * f)), max(1, round(h * f))), interpolation=cv2.INTER_AREA) if f < 1 else s
    hs, ws = small.shape
    u8 = cv2.GaussianBlur(np.clip(255 * small, 0, 255).astype(np.uint8), (0, 0), 1.5)
    rmin, rmax = max(6, int(0.01 * min(hs, ws))), int(0.5 * min(hs, ws))
    found = []
    for method, p1, p2, dp in ((cv2.HOUGH_GRADIENT, 100, 30, 1.2), (cv2.HOUGH_GRADIENT, 100, 18, 1.2),
                               (cv2.HOUGH_GRADIENT_ALT, 300, 0.5, 1.5)):
        circles = cv2.HoughCircles(u8, method, dp=dp, minDist=max(4, min(hs, ws) // 8), param1=p1, param2=p2,
                                   minRadius=rmin, maxRadius=rmax)
        if circles is not None:
            found += [tuple(map(float, c[:3])) for c in circles[0]]
    theta = np.linspace(0, 2 * np.pi, 180, endpoint=False)
    ranked = []
    for cx, cy, r in found:
        x0, x1 = max(0, int(cx - 1.3 * r)), min(ws, int(cx + 1.3 * r) + 1)
        y0, y1 = max(0, int(cy - 1.3 * r)), min(hs, int(cy + 1.3 * r) + 1)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d = np.hypot(xx - cx, yy - cy)
        box = small[y0:y1, x0:x1]
        inner, ring = d < 0.8 * r, (d > 1.05 * r) & (d < 1.25 * r)
        if inner.sum() < 20 or ring.sum() < 20:
            continue
        contrast = float(box[ring].mean() - box[inner].mean())
        xi, yi = cx + 0.9 * r * np.cos(theta), cy + 0.9 * r * np.sin(theta)
        xo, yo = cx + 1.1 * r * np.cos(theta), cy + 1.1 * r * np.sin(theta)
        inside = (np.minimum(xi, xo) >= 0) & (np.maximum(xi, xo) <= ws - 1) & (np.minimum(yi, yo) >= 0) & \
                 (np.maximum(yi, yo) <= hs - 1)
        if inside.sum() < 30:
            continue
        sample = lambda x, y: small[np.clip(np.round(y).astype(int), 0, hs - 1), np.clip(np.round(x).astype(int), 0, ws - 1)]
        rise = (sample(xo, yo) - sample(xi, yi))[inside]
        complete = float(np.mean(rise > 0.05))
        ranked.append(dict(xy=((cx + 0.5) / f - 0.5, (cy + 0.5) / f - 0.5), r=r / f, contrast=contrast,
                           complete=complete, in_frame=float(inside.mean()), score=contrast * complete))
    ranked.sort(key=lambda c: c["score"], reverse=True)
    return ranked, (float(lo), float(hi))


def find_disc(image, valid=None, *, max_side: int = 1600) -> dict:
    """Where the lunar disc is on an eclipse image, measured with no input at all: any eclipse, camera or scale.

    Two ways, after the lunar detection of Francisco Bitto's *Eclipse Image Processor*:

    * **A region without data** (NaN, outside ``valid`` or an alpha channel, or exactly zero) that is closed, nearly
      round and does not touch the frame.  AEL stacks leave the Moon without data.  In a stack registered on the Sun
      over the whole totality, only what the Moon covered all along stays without data, and that is close to the
      solar disc; in a single frame it is the Moon.
    * Otherwise **the dark lunar disc**: among the circles of a Hough search on a robustly stretched copy, the one
      that is darkest inside against a bright ring just outside, with the most of its edge rising from dark to
      bright; then :func:`fit_limb` on the full image, wide and fine.

    Returns ``dict(xy, r, method, rms, ...)``.  Raises ``RuntimeError`` when nothing qualifies: there is never a
    default circle.
    """
    lum, ok = _luminance_and_valid(image, valid)
    h, w = lum.shape
    hole = _region_without_data(~ok | (lum == 0))
    if hole is not None:
        return dict(hole, shape=(h, w))
    ranked, stretch = _dark_disc_candidates(lum, ok, max_side)
    good = [c for c in ranked if c["contrast"] > 0.05 and c["complete"] >= 0.6 and c["in_frame"] >= 0.5]
    if not good:
        raise RuntimeError("find_disc: no dark lunar disc with a bright ring around it was found; "
                           f"{len(ranked)} candidate circles, none qualifies")
    best = good[0]
    # fit_limb counts only positive samples: the image goes above zero, and a pixel without data counts as the
    # darkest one, so that the edge between a Moon without data and the corona is measured where the frame cuts it.
    floor = float(np.percentile(lum[ok], 0.1))
    tiny = 1e-6 * max(float(np.percentile(lum[ok], 99.8)) - floor, 1e-12)
    work = (np.where(ok, np.maximum(lum - floor, 0.0), 0.0) + tiny).astype(np.float32)
    wide = fit_limb(work, best["xy"], best["r"], n_rays=720, search_frac=0.15, smooth_px=1.1, n_iter=4)
    fine = fit_limb(work, wide["xy"], wide["r"], n_rays=1440, search_frac=0.05, smooth_px=1.1, n_iter=6)
    cx, cy, r = fine["xy"][0], fine["xy"][1], fine["r"]
    moved = float(np.hypot(cx - best["xy"][0], cy - best["xy"][1]))
    problems = []
    if fine["n_used"] < 0.35 * fine["n_rays"]:
        problems.append(f"only {fine['n_used']} of {fine['n_rays']} limb rays used")
    # A single frame gives a round limb (0.3–2 px); a stack registered on the Sun blurs it over the lunar motion.
    if fine["rms"] > max(3.0, 0.015 * r):
        problems.append(f"limb rms {fine['rms']:.2f} px")
    if moved > 0.15 * best["r"] or abs(r - best["r"]) > 0.15 * best["r"]:
        problems.append(f"the limb fit moved {moved:.1f} px and changed the radius {r - best['r']:+.1f} px")
    yy, xx = np.mgrid[max(0, int(cy - 1.2 * r)):min(h, int(cy + 1.2 * r) + 1),
                      max(0, int(cx - 1.2 * r)):min(w, int(cx + 1.2 * r) + 1)]
    d = np.hypot(xx - cx, yy - cy)
    sub, sub_ok = lum[yy, xx], ok[yy, xx]
    inside, ring = sub[(d < 0.9 * r) & sub_ok], sub[(d > 1.0 * r) & (d < 1.1 * r) & sub_ok]
    if inside.size >= 50 and ring.size >= 50:
        # A short exposure shows little more than a thin bright rim: the ring has to stand above the noise of the disc.
        sigma = 1.4826 * float(np.median(np.abs(inside - np.median(inside))))
        if not float(np.median(ring) - np.median(inside)) > 2 * max(sigma, tiny):
            problems.append("the disc is not darker than the ring around it")
    if problems:
        raise RuntimeError("find_disc: the lunar limb does not hold: " + "; ".join(problems))
    return dict(xy=(cx, cy), r=r, rms=fine["rms"], n_used=fine["n_used"], n_rays=fine["n_rays"],
                method="lunar limb", hough=dict(xy=best["xy"], r=best["r"], contrast=best["contrast"],
                complete=best["complete"]), stretch=stretch, shape=(h, w))


def measure_geometry(image, valid=None, *, sun_xy=None, sun_radius_px=None, north_deg=None, mirrored=None,
                     arcsec_per_px=None) -> tuple["EclipseGeometry", dict]:
    """:class:`EclipseGeometry` of an eclipse image measured on the image itself, with :func:`find_disc`.

    What is not given is taken from the measured circle and said in the note:

    * the Sun is placed at the centre of the circle, with its radius.  On a single frame the circle is the Moon, and
      the true Sun can be off by up to the difference of the radii (in a total eclipse the Moon looks up to about 8 %
      larger than the Sun); on a stack registered on the Sun over the totality the region without data is close to
      the solar disc;
    * north unknown: ``north_deg = 0``, so position angles are counted from the top of the image;
    * parity unknown: not mirrored; plate scale unknown.

    Returns ``(geometry, report)``.
    """
    disc = find_disc(image, valid)
    h, w = disc["shape"]
    measured = (f"region without data measured, circle rms {disc['rms']:.2f} px" if disc["method"] == "region without data"
                else f"lunar limb measured, rms {disc['rms']:.2f} px over {disc['n_used']} of {disc['n_rays']} rays")
    assumed = []
    if sun_xy is None:
        assumed.append("Sun centre = centre of the measured circle")
    if sun_radius_px is None:
        assumed.append("Sun radius = radius of the measured circle")
    if north_deg is None:
        assumed.append("north unknown: position angles from the top of the image")
    if mirrored is None:
        assumed.append("parity unknown: not mirrored")
    if arcsec_per_px is None:
        assumed.append("plate scale unknown")
    geometry = EclipseGeometry(shape=(int(h), int(w)), sun_xy=tuple(map(float, sun_xy or disc["xy"])),
                               sun_radius_px=float(sun_radius_px or disc["r"]),
                               moon_xy=tuple(map(float, disc["xy"])), moon_radius_px=float(disc["r"]),
                               north_deg=float(north_deg or 0.0), mirrored=bool(mirrored),
                               arcsec_per_px=None if arcsec_per_px is None else float(arcsec_per_px),
                               note="Measured on the image (ael.geometry.measure_geometry): " + measured +
                                    (". Assumed: " + "; ".join(assumed) if assumed else ""))
    lum, ok = _luminance_and_valid(image, valid)
    sample = lum[ok][::max(1, int(ok.sum()) // 2_000_000)]
    report = dict(method=disc["method"], disc={k: v for k, v in disc.items() if k != "shape"},
                  measured=measured, assumed=assumed,
                  display_stretch=dict(zip(("low", "high"), map(float, np.percentile(sample, [1.0, 99.8])))))
    return geometry, report
