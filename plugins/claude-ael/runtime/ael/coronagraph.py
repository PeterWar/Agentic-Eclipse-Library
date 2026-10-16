"""Check an eclipse image against coronagraphs and solar imagers (K-Cor, SOHO/LASCO, SDO/AIA).

Two questions, kept apart because they fail in different ways:

1. **Structure.**  Do the rays and streamers sit where an independent instrument sees them?  Each image
   is unrolled in its *own* solar coordinates (r in solar radii as seen by its own observer; position
   angle, PA, from solar north through east), normalised radius by radius (a robust NRGF), and the
   angular profiles of the same ring are correlated at zero rotation and at the best rotation within a
   few degrees.  A null distribution comes from large rotations (30–330°), and a fine-detail version
   from an angular high-pass (< 12°), because whole profiles share the broad two-lobed shape of any
   corona.  The test compares *angles*: a radial tone curve ``a(r)·I + b(r)`` passes it unchanged, so it
   says nothing about brightness.

2. **Brightness**, in mean solar brightness (MSB: B/B☉, the mean brightness of the solar disc).  The
   level is compared in 1° cells inside rings, as a ratio of medians and a median of ratios, and judged
   against the photograph's own asymmetric uncertainty (:func:`ratio_band`).

What the 12 August 2026 data taught, and how it shaped this module (research notes 180 and 185):

* A plate solved on stars with the Sun 9° high was affine: solar north and east were 90.43° apart.
  Treating the axes as perpendicular moved points by 3 px at the limb and 20 px at 6 R☉.
  :class:`SolarFrame` inverts the 2×2 matrix exactly.
* SOHO, at L1, sees the Sun 1.1 % larger than an observer on the Earth.  R☉ in pixels must be that of
  each observer (:func:`rsun_arcsec`); readers of LASCO level-0.5 files may put the observer on the Earth.
* K-Cor measures polarised brightness, pB.  pB/p(r) is the K corona only; a photograph sees K + F.
  Comparing a photograph with pB/p gave a false 13–15 % excess (:func:`kcor_total_msb` adds the F corona).
  The public K-Cor GIFs are 8-bit and gamma-encoded: use the level-2 FITS for brightness.
* LASCO C2 has two calibrations whose levels differ by 13.5 % for August 2026
  (:func:`lasco_c2_msb_per_dn`).  Give both; the choice is not a detail.
* With the Sun low, correct differential extinction (:mod:`ael.extinction`) and fit the sky where the
  corona is negligible before any brightness comparison; otherwise an extinction dipole remains in the
  ratio.
* Exclude the lunar-motion band at the limb, prominences, the occulter pylon and annotation labels.
  Nothing is filled in their place.

Nothing invented: a sample whose interpolation support touches missing data is ``NaN``, and a cell
without data is ``NaN``.  One smoothing is declared: an angular profile is a normalised convolution
(Gaussian of 1.5° by default), so a gap narrower than the kernel takes the mean of its observed
neighbours where at least 60 % of the kernel saw data; wider gaps stay ``NaN``.
"""
from __future__ import annotations

import datetime as _dt
import json
import math
import numbers
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import ndimage as nd
from scipy.integrate import trapezoid as _trapezoid

from .geometry import EclipseGeometry, direction_of_pa

__all__ = ["AU_KM", "RSUN_KM", "rsun_arcsec", "SolarFrame", "Unrolled", "sample", "unroll", "nrgf_rows",
           "subtract_low_harmonics", "dark_sector", "angular_profile", "angular_highpass",
           "circular_correlation", "rotation_null", "compare_structure", "van_de_hulst_abcd", "DENSITY_MODELS",
           "k_corona_tb_pb", "thomson_polarization", "f_corona_van_de_hulst_1950", "k_corona_van_de_hulst_1950",
           "kcor_total_msb", "k_band_transfer", "LASCO_C2_CALIBRATIONS", "mjd", "lasco_c2_summing",
           "lasco_c2_msb_per_dn",
           "cell_medians", "level_ratios", "ratio_band", "structure_from_config"]

AU_KM = 149_597_870.7
RSUN_KM = 695_700.0            # IAU 2015 nominal solar radius


def rsun_arcsec(distance_au: float, radius_km: float = RSUN_KM) -> float:
    """Apparent radius of the photosphere, in arcsec, for an observer at ``distance_au`` from the Sun.

    959.23″ at 1 au.  On 12 August 2026 the Earth was at 1.0133 au (946.66″) and SOHO at 1.0021 au
    (957.22″).  Some instruments use 696 000 km instead (SDO's ``RSUN_REF``): pass ``radius_km``.
    """
    return math.degrees(math.asin(float(radius_km) / (float(distance_au) * AU_KM))) * 3600.0


# ------------------------------------------------------------------------------------------------
# Solar coordinates on an image
# ------------------------------------------------------------------------------------------------
class SolarFrame:
    """Solar coordinates on one image: ``(x, y)`` pixels ↔ ``(r, PA)``.

    ``north_px`` and ``east_px`` are the pixel offsets (x to the right, y down, as array columns and rows)
    of a point 1 R☉ from the Sun's centre towards solar north and towards solar east, as seen by this
    image's observer.  They need not be perpendicular nor of equal length: a plate solved on stars through
    a refracting atmosphere is affine.  Both conversions use the exact 2×2 inverse.
    """

    def __init__(self, center_xy, north_px, east_px, *, observer: str = "", time_utc: str = ""):
        self.cx, self.cy = float(center_xy[0]), float(center_xy[1])
        n = np.asarray(north_px, np.float64).reshape(2)
        e = np.asarray(east_px, np.float64).reshape(2)
        self.M = np.array([[n[0], e[0]], [n[1], e[1]]])
        det = float(np.linalg.det(self.M))
        if not np.isfinite(det) or abs(det) < 1e-9 * max(1.0, float(np.abs(self.M).max()) ** 2):
            raise ValueError("solar north and east axes are degenerate (parallel or zero)")
        self.Minv = np.linalg.inv(self.M)
        self.observer, self.time_utc = observer, time_utc

    # --- construction ---------------------------------------------------------------------------
    @classmethod
    def from_axes(cls, center_xy, rsun_px: float, north_dir, east_dir, **kw) -> "SolarFrame":
        """Frame from the solar radius in pixels and two directions (normalised here)."""
        n = np.asarray(north_dir, np.float64)
        e = np.asarray(east_dir, np.float64)
        return cls(center_xy, rsun_px * n / np.linalg.norm(n), rsun_px * e / np.linalg.norm(e), **kw)

    @classmethod
    def from_geometry(cls, geometry: EclipseGeometry, p_angle_deg: float, **kw) -> "SolarFrame":
        """From an :class:`ael.geometry.EclipseGeometry` (orthogonal axes; ``north_deg`` is *celestial* north).

        Solar north lies ``p_angle_deg`` (the solar P angle) east of celestial north.  It is required: in
        August the P angle is about 15°, and assuming 0 would rotate every position angle by that much.
        """
        n = direction_of_pa(p_angle_deg, geometry.north_deg, geometry.mirrored)
        e = direction_of_pa(p_angle_deg + 90.0, geometry.north_deg, geometry.mirrored)
        return cls.from_axes(geometry.sun_xy, geometry.sun_radius_px, n, e, **kw)

    @classmethod
    def from_celestial_plate(cls, center_xy, rsun_arcsec_: float, north_px_per_arcsec, east_px_per_arcsec,
                             p_angle_deg: float, **kw) -> "SolarFrame":
        """From an affine plate solution: the pixel offset of 1″ towards celestial north and celestial east.

        A sky direction at celestial PA θ maps to ``cos θ·N + sin θ·E``; solar north is at θ = P.
        """
        N = np.asarray(north_px_per_arcsec, np.float64)
        E = np.asarray(east_px_per_arcsec, np.float64)
        c, s = math.cos(math.radians(p_angle_deg)), math.sin(math.radians(p_angle_deg))
        return cls(center_xy, (c * N + s * E) * rsun_arcsec_, (-s * N + c * E) * rsun_arcsec_, **kw)

    @classmethod
    def from_pixel_points(cls, center_xy, north_xy, west_xy, offset_arcsec: float, rsun_arcsec_: float,
                          **kw) -> "SolarFrame":
        """From the pixel positions of the Sun's centre and of two points ``offset_arcsec`` due solar north
        and due solar west of it, as any WCS library returns them (helioprojective +y is solar north,
        +x is solar west)."""
        c = np.asarray(center_xy, np.float64)
        k = float(rsun_arcsec_) / float(offset_arcsec)
        n = (np.asarray(north_xy, np.float64) - c) * k
        e = -(np.asarray(west_xy, np.float64) - c) * k
        return cls(tuple(c), n, e, **kw)

    @classmethod
    def from_wcs_header(cls, header, *, rsun_arcsec_: float | None = None, **kw) -> "SolarFrame":
        """From a helioprojective FITS header (``HPLN``/``HPLT`` axes; K-Cor level 2, SDO/AIA level 1.5) with
        astropy.  R☉ comes from ``rsun_arcsec_``, else ``RSUN_OBS``, else ``DSUN_OBS``.

        The frame is linear about the Sun's centre; with a gnomonic (TAN) projection that is exact to about
        1e-5 in radius at 1 R☉ and 3e-4 at 6 R☉, far below the angular smoothing of the comparison.

        ⚠️ LASCO level-0.5 headers are not helioprojective; with sunpy, get the three pixel positions and use
        :meth:`from_pixel_points`, and give SOHO's own R☉ (:func:`rsun_arcsec` at SOHO's distance), because
        sunpy may assume an observer on the Earth for those files.
        """
        from astropy.wcs import WCS
        w = WCS(header).celestial
        if w.naxis != 2:
            raise ValueError("the header has no pair of celestial (helioprojective) axes")
        unit = str(w.wcs.cunit[0])
        one = {"deg": 1.0 / 3600.0, "arcsec": 1.0, "rad": math.pi / (180.0 * 3600.0)}.get(unit)
        if one is None:
            raise ValueError(f"unexpected WCS unit {unit!r}")
        d = 1000.0
        c = w.world_to_pixel_values(0.0, 0.0)
        n = w.world_to_pixel_values(0.0, d * one)
        wv = w.world_to_pixel_values(d * one, 0.0)
        if rsun_arcsec_ is None:
            if "RSUN_OBS" in header:
                rsun_arcsec_ = float(header["RSUN_OBS"])
            elif "DSUN_OBS" in header:
                rsun_arcsec_ = rsun_arcsec(float(header["DSUN_OBS"]) / (AU_KM * 1000.0))
            else:
                raise ValueError("give rsun_arcsec_: the header has neither RSUN_OBS nor DSUN_OBS")
        kw.setdefault("time_utc", str(header.get("DATE-OBS", "")))
        kw.setdefault("observer", str(header.get("TELESCOP", header.get("INSTRUME", ""))))
        return cls.from_pixel_points((float(c[0]), float(c[1])), (float(n[0]), float(n[1])),
                                     (float(wv[0]), float(wv[1])), d, rsun_arcsec_, **kw)

    # --- persistence ----------------------------------------------------------------------------
    def to_dict(self) -> dict:
        return dict(center_xy=[self.cx, self.cy], north_px=self.M[:, 0].tolist(), east_px=self.M[:, 1].tolist(),
                    observer=self.observer, time_utc=self.time_utc, rsun_px=self.rsun_px,
                    north_east_angle_deg=self.axis_angle_deg)

    @classmethod
    def from_dict(cls, d: dict) -> "SolarFrame":
        return cls(d["center_xy"], d["north_px"], d["east_px"], observer=d.get("observer", ""),
                   time_utc=d.get("time_utc", ""))

    def scaled(self, factor: float) -> "SolarFrame":
        """Frame of the same image resampled by ``factor`` (pixel centres: x' = (x + 0.5)·f − 0.5)."""
        f = float(factor)
        return SolarFrame(((self.cx + 0.5) * f - 0.5, (self.cy + 0.5) * f - 0.5), self.M[:, 0] * f,
                          self.M[:, 1] * f, observer=self.observer, time_utc=self.time_utc)

    # --- properties and conversions -------------------------------------------------------------
    @property
    def rsun_px(self) -> float:
        """Solar radius in pixels (geometric mean of the two axes)."""
        return float(math.sqrt(abs(np.linalg.det(self.M))))

    @property
    def axis_angle_deg(self) -> float:
        """Angle between solar north and solar east on the image (90° for an orthogonal plate)."""
        n, e = self.M[:, 0], self.M[:, 1]
        return float(np.degrees(np.arccos(np.clip(n @ e / (np.linalg.norm(n) * np.linalg.norm(e)), -1, 1))))

    def to_pixels(self, r, pa_deg):
        """``(r in R☉, PA in degrees)`` → ``(x, y)`` pixels."""
        pa = np.radians(np.asarray(pa_deg, np.float64))
        r = np.asarray(r, np.float64)
        a, b = r * np.cos(pa), r * np.sin(pa)
        return (self.cx + self.M[0, 0] * a + self.M[0, 1] * b,
                self.cy + self.M[1, 0] * a + self.M[1, 1] * b)

    def to_solar(self, x, y):
        """``(x, y)`` pixels → ``(r in R☉, PA in degrees 0–360)``: the exact inverse of :meth:`to_pixels`."""
        dx = np.asarray(x, np.float64) - self.cx
        dy = np.asarray(y, np.float64) - self.cy
        a = self.Minv[0, 0] * dx + self.Minv[0, 1] * dy
        b = self.Minv[1, 0] * dx + self.Minv[1, 1] * dy
        return np.hypot(a, b), np.mod(np.degrees(np.arctan2(b, a)), 360.0)

    def solar_maps(self, shape) -> tuple[np.ndarray, np.ndarray]:
        """``(r, PA)`` of every pixel centre of an image of ``shape``."""
        h, w = int(shape[0]), int(shape[1])
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
        return self.to_solar(xx, yy)


# ------------------------------------------------------------------------------------------------
# Unrolling and the structure test
# ------------------------------------------------------------------------------------------------
def _masked(image, valid=None, channel=None) -> np.ndarray:
    a = np.asarray(image, np.float64)
    if a.ndim == 3:
        if channel is None:
            raise ValueError("a colour image needs a channel (index) or a 2-D luminance")
        a = a[..., int(channel)]
    if a.ndim != 2:
        raise ValueError("expected a 2-D image")
    if valid is not None:
        v = np.asarray(valid, bool)
        if v.shape != a.shape:
            raise ValueError("valid mask does not match the image")
        a = np.where(v, a, np.nan)
    return a


def sample(image, frame: SolarFrame, r, pa_deg, *, valid=None, order: int = 1) -> np.ndarray:
    """Values of a 2-D image at solar coordinates ``(r, pa_deg)`` (arrays of one shape).

    ``order`` 0 (nearest) or 1 (bilinear).  A sample whose interpolation support touches a missing pixel
    (``NaN``, ``valid`` False, or outside the array) is ``NaN``.
    """
    if order not in (0, 1):
        raise ValueError("order must be 0 or 1 (higher orders spread missing data)")
    return _map(_masked(image, valid), frame, r, pa_deg, order)


def _map(img, frame, r, pa_deg, order):
    x, y = frame.to_pixels(r, pa_deg)
    out = nd.map_coordinates(img, [np.ravel(y), np.ravel(x)], order=order, mode="constant", cval=np.nan,
                             prefilter=False)
    return out.reshape(np.shape(x))


@dataclass
class Unrolled:
    """An image unrolled on a (radius × position angle) grid.  Row 0 is the smallest radius."""

    data: np.ndarray       # (n_r, n_pa)
    r: np.ndarray          # R☉ of each row
    pa: np.ndarray         # degrees of each column, from 0, uniform step

    @property
    def pa_step_deg(self) -> float:
        return float(360.0 / self.pa.size)


def _pa_grid(pa_step_deg: float) -> np.ndarray:
    n = 360.0 / float(pa_step_deg)
    if abs(n - round(n)) > 1e-9:
        raise ValueError("pa_step_deg must divide 360")
    return np.arange(int(round(n))) * float(pa_step_deg)


def unroll(image, frame: SolarFrame, radii_rsun, *, pa_step_deg: float = 0.5, valid=None,
           supersample: int = 1, order: int = 1) -> Unrolled:
    """Unroll ``image`` around the Sun in its own solar coordinates.

    ``supersample`` = n averages n × n samples spread over each output cell (in radius and angle), to avoid
    aliasing fine rays far from the Sun; a cell is ``NaN`` if any of its samples is.  Bin an image that is
    much sharper than the instrument it is compared with (and use :meth:`SolarFrame.scaled`).
    """
    r = np.asarray(radii_rsun, np.float64)
    if r.ndim != 1 or r.size < 2 or np.any(np.diff(r) <= 0):
        raise ValueError("radii must be a 1-D increasing array")
    pa = _pa_grid(pa_step_deg)
    n = int(supersample)
    if n < 1:
        raise ValueError("supersample must be >= 1")
    if order not in (0, 1):
        raise ValueError("order must be 0 or 1 (higher orders spread missing data)")
    img = _masked(image, valid)
    if n == 1:
        RR, PP = np.meshgrid(r, pa, indexing="ij")
        return Unrolled(_map(img, frame, RR, PP, order), r, pa)
    # sub-sample offsets: radius between neighbouring rows (geometric), angle within the column
    edges = np.empty(r.size + 1)
    edges[1:-1] = np.sqrt(r[1:] * r[:-1])
    edges[0] = r[0] ** 2 / edges[1]
    edges[-1] = r[-1] ** 2 / edges[-2]
    acc = np.zeros((r.size, pa.size))
    for i in range(n):
        t = (i + 0.5) / n
        ri = np.exp(np.log(edges[:-1]) + t * (np.log(edges[1:]) - np.log(edges[:-1])))
        for j in range(n):
            pj = pa + (j + 0.5) / n * pa_step_deg - 0.5 * pa_step_deg
            RR, PP = np.meshgrid(ri, pj, indexing="ij")
            acc += _map(img, frame, RR, PP, order)
    return Unrolled(acc / (n * n), r, pa)


def nrgf_rows(data) -> np.ndarray:
    """Robust NRGF of an unrolled image: each radius row minus its median, over 1.4826 × its MAD.

    The F corona and scattered light are close to radial, so this removes them the same way in every
    image.  Rows without spread are ``NaN``.
    """
    a = np.asarray(data.data if isinstance(data, Unrolled) else data, np.float64)
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            mu = np.nanmedian(a, axis=1, keepdims=True)
            sd = 1.4826 * np.nanmedian(np.abs(a - mu), axis=1, keepdims=True)
        out = (a - mu) / sd
    out[~np.isfinite(out)] = np.nan
    return out


def subtract_low_harmonics(data, m_max: int = 3, *, min_fraction: float = 0.5) -> np.ndarray:
    """Remove the angular harmonics m = 0…``m_max`` of each radius row (least squares on observed angles).

    For showing coronagraph images whose background (F corona, stray light) is not radial: the F corona
    of a LASCO level-0.5 image is flattened, so a plain NRGF leaves its m = 2 shape.  Rows with less than
    ``min_fraction`` of their angles observed are ``NaN``.
    """
    a = np.asarray(data.data if isinstance(data, Unrolled) else data, np.float64)
    n_pa = a.shape[1]
    th = np.radians(np.arange(n_pa) * 360.0 / n_pa)
    cols = [np.ones(n_pa)]
    for m in range(1, int(m_max) + 1):
        cols += [np.cos(m * th), np.sin(m * th)]
    B = np.stack(cols, axis=1)
    out = np.full_like(a, np.nan)
    for i in range(a.shape[0]):
        ok = np.isfinite(a[i])
        if ok.sum() < max(min_fraction * n_pa, B.shape[1] + 1):
            continue
        coef = np.linalg.lstsq(B[ok], a[i, ok], rcond=None)[0]
        out[i, ok] = a[i, ok] - B[ok] @ coef
    return out


def dark_sector(nrgf_data, radii_rsun, r_range, seed_pa_deg: float, *, threshold: float = -0.3,
                dilate_deg: float = 4.0) -> np.ndarray:
    """Boolean mask over position angle of the contiguous dark sector that contains ``seed_pa_deg``.

    Made for a coronagraph's occulter pylon: the median NRGF over ``r_range`` falls below ``threshold``
    along one contiguous run of angles.  Only the run containing the seed is returned (dilated by
    ``dilate_deg`` on both sides): a global threshold would also remove real coronal holes.  If the seed
    angle is not dark, nothing is masked.  Find the seed by looking at the unrolled image.
    """
    if dilate_deg < 0:
        raise ValueError("dilate_deg must be >= 0")
    a = np.asarray(nrgf_data.data if isinstance(nrgf_data, Unrolled) else nrgf_data, np.float64)
    r = np.asarray(radii_rsun, np.float64)
    sel = (r >= r_range[0]) & (r <= r_range[1])
    if not sel.any():
        raise ValueError("r_range selects no row")
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        med = np.nanmedian(a[sel], axis=0)
    dark = ~(med > threshold)                       # missing angles count as dark
    n = dark.size
    step = 360.0 / n
    s = int(round(seed_pa_deg / step)) % n
    out = np.zeros(n, bool)
    if not dark[s]:
        return out
    if dark.all():
        return np.ones(n, bool)
    k0 = int(np.flatnonzero(~dark)[0])              # start the circle on an angle that is not dark:
    lab, _ = nd.label(np.roll(dark, -k0))           # then no dark run wraps round the end of the array
    run = np.roll(lab == lab[(s - k0) % n], k0)
    k = int(math.ceil(dilate_deg / step - 1e-9))
    for d in range(-k, k + 1):
        out |= np.roll(run, d)
    return out


def _normalised_smooth(p, sigma_steps, min_cover):
    ok = np.isfinite(p)
    num = nd.gaussian_filter1d(np.where(ok, p, 0.0), sigma_steps, mode="wrap")
    den = nd.gaussian_filter1d(ok.astype(np.float64), sigma_steps, mode="wrap")
    with np.errstate(all="ignore"):
        return np.where(den > min_cover, num / np.maximum(den, 1e-12), np.nan)


def angular_profile(data, radii_rsun, r1: float, r2: float, *, sigma_deg: float = 1.5, min_cover: float = 0.6,
                    exclude=None) -> np.ndarray:
    """Mean over the rows r1 ≤ r ≤ r2 of an unrolled (normalised) image, smoothed in angle.

    Gaussian of ``sigma_deg`` by normalised convolution (missing angles do not count); an angle is ``NaN``
    where less than ``min_cover`` of the kernel saw data.  ``exclude``: boolean mask over PA set to ``NaN``
    before smoothing (pylon, labels).
    """
    a = np.asarray(data.data if isinstance(data, Unrolled) else data, np.float64)
    r = np.asarray(radii_rsun, np.float64)
    sel = (r >= r1) & (r <= r2)
    if not sel.any():
        raise ValueError(f"no row between {r1} and {r2} R☉")
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        p = np.nanmean(a[sel], axis=0)
    if exclude is not None:
        p = np.where(np.asarray(exclude, bool), np.nan, p)
    step = 360.0 / p.size
    return _normalised_smooth(p, sigma_deg / step, min_cover)


def angular_highpass(profile, *, sigma_deg: float = 12.0, min_cover: float = 0.6) -> np.ndarray:
    """Profile minus its normalised Gaussian smoothing of ``sigma_deg``: keeps detail narrower than that."""
    p = np.asarray(profile, np.float64)
    return p - _normalised_smooth(p, sigma_deg / (360.0 / p.size), min_cover)


def _pearson(a, b, min_points):
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < min_points:
        return np.nan
    x, y = a[m] - a[m].mean(), b[m] - b[m].mean()
    d = math.sqrt(float((x * x).sum() * (y * y).sum()))
    return float((x * y).sum() / d) if d > 0 else np.nan


def circular_correlation(p, q, *, max_shift_deg: float = 10.0, min_points: int = 60) -> dict:
    """Pearson correlation of two angular profiles at zero rotation and at the best rotation of ``q``.

    ``shift_deg`` is the rotation of ``q`` towards larger PA that maximises the correlation: if the
    reference sees a feature δ degrees further round than we do, ``shift_deg`` = −δ.  ``at_search_edge`` is
    True when the best rotation is the largest one searched: then it is not an orientation.
    """
    p = np.asarray(p, np.float64)
    q = np.asarray(q, np.float64)
    if p.shape != q.shape:
        raise ValueError("profiles must share the angle grid")
    step = 360.0 / p.size
    k = int(math.floor(max_shift_deg / step + 1e-9))
    shifts = np.arange(-k, k + 1)
    rho = np.array([_pearson(p, np.roll(q, s), min_points) for s in shifts])
    n0 = int((np.isfinite(p) & np.isfinite(q)).sum())
    if not np.isfinite(rho).any():
        return dict(rho_0=np.nan, rho_best=np.nan, shift_deg=np.nan, at_search_edge=False, n_angles=n0)
    i = int(np.nanargmax(rho))
    return dict(rho_0=float(rho[k]), rho_best=float(rho[i]), shift_deg=float(shifts[i] * step),
                at_search_edge=bool(k > 0 and abs(int(shifts[i])) == k), n_angles=n0)


def rotation_null(p, q, *, shifts_deg=None, min_points: int = 60) -> np.ndarray:
    """Correlations of ``p`` with ``q`` rotated by large angles (default 30°, 32°, …, 330°): the null."""
    p = np.asarray(p, np.float64)
    q = np.asarray(q, np.float64)
    step = 360.0 / p.size
    shifts = np.arange(30.0, 330.0 + 1e-9, 2.0) if shifts_deg is None else np.asarray(shifts_deg, np.float64)
    return np.array([_pearson(p, np.roll(q, int(round(s / step))), min_points) for s in shifts])


def _with_null(p, q, max_shift_deg, min_points, null_shifts):
    c = circular_correlation(p, q, max_shift_deg=max_shift_deg, min_points=min_points)
    z = rotation_null(p, q, shifts_deg=null_shifts, min_points=min_points)
    z = z[np.isfinite(z)]
    if z.size and np.isfinite(c["rho_0"]):
        c.update(null_mean=float(z.mean()), null_sd=float(z.std()), null_max=float(z.max()),
                 null_fraction_at_or_above_rho_0=float((z >= c["rho_0"]).mean()), null_n=int(z.size))
    else:
        c.update(null_mean=np.nan, null_sd=np.nan, null_max=np.nan, null_fraction_at_or_above_rho_0=np.nan,
                 null_n=int(z.size))
    return c


def compare_structure(ours: Unrolled, ref: Unrolled, rings, *, normalise_ours: bool = True,
                      normalise_ref: bool = True, exclude_ours=None, exclude_ref=None, sigma_deg: float = 1.5,
                      highpass_sigma_deg: float = 12.0, max_shift_deg: float = 10.0, min_cover: float = 0.6,
                      min_points: int = 60, null_shifts_deg=None) -> list[dict]:
    """Angular-profile comparison ring by ring, with its null and its fine-detail version.

    Both images must be unrolled on the same (r, PA) grid, each in its own solar coordinates.  With
    ``normalise_*`` the rows are normalised with :func:`nrgf_rows` (set False for an image that is already
    an NRGF, such as K-Cor's).  ``exclude_*``: masks over PA (see :func:`dark_sector`).

    Read the result as agreement in *angle* only: ``rho_0`` well above ``null_max`` says the rays and
    streamers are where the instrument sees them; it says nothing about brightness, and it does not
    exclude local artefacts.
    """
    if ours.data.shape != ref.data.shape or not (np.allclose(ours.r, ref.r) and np.allclose(ours.pa, ref.pa)):
        raise ValueError("unroll both images on the same (r, PA) grid")
    A = nrgf_rows(ours) if normalise_ours else np.asarray(ours.data, np.float64)
    B = nrgf_rows(ref) if normalise_ref else np.asarray(ref.data, np.float64)
    out = []
    for r1, r2 in rings:
        pA = angular_profile(A, ours.r, r1, r2, sigma_deg=sigma_deg, min_cover=min_cover, exclude=exclude_ours)
        pB = angular_profile(B, ref.r, r1, r2, sigma_deg=sigma_deg, min_cover=min_cover, exclude=exclude_ref)
        res = dict(r_rsun=[float(r1), float(r2)], **_with_null(pA, pB, max_shift_deg, min_points, null_shifts_deg))
        hA = angular_highpass(pA, sigma_deg=highpass_sigma_deg, min_cover=min_cover)
        hB = angular_highpass(pB, sigma_deg=highpass_sigma_deg, min_cover=min_cover)
        res["fine_detail"] = dict(highpass_sigma_deg=highpass_sigma_deg,
                                  **_with_null(hA, hB, max_shift_deg, min_points, null_shifts_deg))
        out.append(res)
    return out


# ------------------------------------------------------------------------------------------------
# K corona, F corona and the polarisation of Thomson scattering
# ------------------------------------------------------------------------------------------------
def van_de_hulst_abcd(r):
    """Coefficients A, B, C, D of van de Hulst (1950) for a scattering point at ``r`` R☉ from the centre
    (limb darkening enters as (1 − u)·A + u·B and (1 − u)·C + u·D)."""
    r = np.asarray(r, np.float64)
    s = 1.0 / r
    c = np.sqrt(np.clip(1.0 - s * s, 0.0, 1.0))
    L = np.log((1.0 + s) / np.maximum(c, 1e-12))
    A = c * s * s
    B = -(1.0 / 8.0) * (1.0 - 3.0 * s * s - (c * c / s) * (1.0 + 3.0 * s * s) * L)
    C = 4.0 / 3.0 - c - c ** 3 / 3.0
    D = (1.0 / 8.0) * (5.0 + s * s - (c * c / s) * (5.0 - s * s) * L)
    return A, B, C, D


DENSITY_MODELS = {
    # electron densities (units cancel in the polarisation degree); r in R☉
    "baumbach_allen": lambda r: 2.99 * r ** -16 + 1.55 * r ** -6 + 0.036 * r ** -1.5,
    "saito_equator": lambda r: 3.09 * r ** -16 + 1.58 * r ** -6 + 0.0251 * r ** -2.5,
    "power_minus4": lambda r: r ** -4.0,
}


def _density(model):
    if callable(model):
        return model
    try:
        return DENSITY_MODELS[model]
    except KeyError:
        raise ValueError(f"unknown density model {model!r}; known: {sorted(DENSITY_MODELS)}") from None


def _z_grid(z_max_rsun: float) -> np.ndarray:
    """Line-of-sight samples: every 0.001 R☉ up to 20 R☉, then geometric (4000 steps) up to ``z_max_rsun``."""
    near = np.linspace(0.0, min(20.0, float(z_max_rsun)), 20001)
    if z_max_rsun <= 20.0:
        return near
    return np.concatenate([near, np.geomspace(20.0, float(z_max_rsun), 4001)[1:]])


def k_corona_tb_pb(rho: float, density="baumbach_allen", *, u: float = 0.56,
                   z_max_rsun: float = 2000.0) -> tuple[float, float]:
    """Total and polarised brightness of the K corona at projected distance ``rho`` (R☉), in arbitrary
    units, integrated along the line of sight from the plane of the sky to ``z_max_rsun`` (Billings 1966).

    The 2026 research stopped at 20 R☉, which raised p by 0.1 % at 2 R☉ and by 6 % at 8 R☉; the default
    goes to 2000 R☉ (what is left beyond is below 1e-6).
    """
    rho = float(rho)
    if not rho > 1.0:
        raise ValueError("rho must be larger than 1 R☉ (outside the photosphere)")
    z = _z_grid(z_max_rsun)
    r = np.sqrt(rho ** 2 + z ** 2)
    A, B, C, D = van_de_hulst_abcd(r)
    n = _density(density)(r)
    it = _trapezoid(n * ((1 - u) * C + u * D), z)
    pb = _trapezoid(n * (rho / r) ** 2 * ((1 - u) * A + u * B), z)
    return float(2.0 * it - pb), float(pb)


_P_CACHE: dict = {}
_P_GRID = np.round(np.arange(1.02, 8.0 + 1e-9, 0.005), 4)


def thomson_polarization(rho, density="baumbach_allen", *, u: float = 0.56) -> np.ndarray:
    """Degree of polarisation p = pB/tB of the K corona at projected distance ``rho`` (R☉).

    Named density models are tabulated once on 1.02–8 R☉ (step 0.005) and interpolated; outside that
    range the result is ``NaN``.  A callable density is tabulated the same way over the requested range.
    """
    rho = np.asarray(rho, np.float64)
    if callable(density):
        out = np.full(rho.shape, np.nan)
        ok = np.isfinite(rho) & (rho > 1.0)
        if ok.any():
            lo, hi = float(rho[ok].min()), float(rho[ok].max())
            grid = np.append(np.arange(lo, hi, 0.005), hi)
            vals = np.array([(lambda t: t[1] / t[0])(k_corona_tb_pb(x, density, u=u)) for x in grid])
            out[ok] = np.interp(rho[ok], grid, vals) if grid.size > 1 else vals[0]
        return out
    key = (density, float(u))
    if key not in _P_CACHE:
        _density(density)
        _P_CACHE[key] = np.array([(lambda t: t[1] / t[0])(k_corona_tb_pb(x, density, u=u)) for x in _P_GRID])
    return np.interp(rho, _P_GRID, _P_CACHE[key], left=np.nan, right=np.nan)


def f_corona_van_de_hulst_1950(r) -> np.ndarray:
    """F corona of van de Hulst (1950), BAN 11, 135, eq. (7), in MSB: (14.86 r⁻⁷ + 4.99 r⁻²·⁵)·10⁻⁸.

    Spherically symmetric; the unit is 10⁻⁸ of the *mean* brightness of the solar disc.
    """
    r = np.asarray(r, np.float64)
    return (14.86 * r ** -7 + 4.99 * r ** -2.5) * 1e-8


def k_corona_van_de_hulst_1950(r, phase: str = "max") -> np.ndarray:
    """Equatorial K corona of van de Hulst (1950), eqs. (5) and (6), in MSB, at solar maximum or minimum."""
    r = np.asarray(r, np.float64)
    if phase == "max":
        return (355.6 * r ** -17 + 177.8 * r ** -7 + 0.708 * r ** -2.5) * 1e-8
    if phase == "min":
        return (200.0 * r ** -17 + 100.0 * r ** -7 + 0.398 * r ** -2.5) * 1e-8
    raise ValueError("phase is 'max' or 'min'")


def kcor_total_msb(pb_msb, r, *, density="baumbach_allen", u: float = 0.56,
                   f_model=f_corona_van_de_hulst_1950, f_scale: float = 1.0) -> np.ndarray:
    """What a photograph should see where K-Cor measured ``pb_msb``: K = pB/p(r), plus the F corona.

    ``pb_msb`` in MSB (K-Cor level-2 FITS, ``BUNIT`` 'Mean Solar Brightness'), ``r`` in R☉ (same shape).
    Vary ``density``, ``f_model`` and ``f_scale`` (e.g. 0.5–1.5) to bound the model, and report the range.
    """
    pb = np.asarray(pb_msb, np.float64)
    r = np.asarray(r, np.float64)
    with np.errstate(all="ignore"):
        return pb / thomson_polarization(r, density, u=u) + float(f_scale) * np.asarray(f_model(r), np.float64)


def k_band_transfer(rho, u_ours: float, u_ref: float, density="baumbach_allen") -> float:
    """K corona in MSB seen with limb darkening ``u_ours`` over the same seen with ``u_ref``.

    MSB divides by the *mean* disc brightness, so K(MSB) ∝ tB(u)/(1 − u/3).  Small (a few per cent) but
    one-sided between a green photograph and K-Cor's 735 nm.
    """
    a = k_corona_tb_pb(rho, density, u=u_ours)[0] / (1.0 - u_ours / 3.0)
    b = k_corona_tb_pb(rho, density, u=u_ref)[0] / (1.0 - u_ref / 3.0)
    return float(a / b)


# ------------------------------------------------------------------------------------------------
# LASCO C2 calibration
# ------------------------------------------------------------------------------------------------
LASCO_C2_CALIBRATIONS = {
    # MSB per (DN/s/pixel) = (a·MJD + b)·1e-12, Orange filter, after bias, exposure factor and vignetting
    "colaninno_howard_2015": (3.9e-5, 5.2),          # Colaninno & Howard 2015, Sol. Phys. 290, 997, eq. (8)
    "solarsoft": (4.60403e-5, 3.74116),              # SolarSoft c2_calfactor.pro (v1.9, 2007)
}


def mjd(when) -> float:
    """Modified Julian Date of an ISO time string (UTC), a datetime, or a number (returned as is)."""
    if isinstance(when, numbers.Real) and not isinstance(when, bool):
        return float(when)
    t = when if isinstance(when, _dt.datetime) else _dt.datetime.fromisoformat(str(when).replace("Z", "+00:00"))
    if t.tzinfo is not None:
        t = t.astimezone(_dt.timezone.utc).replace(tzinfo=None)
    return (t - _dt.datetime(1858, 11, 17)).total_seconds() / 86400.0


LASCO_C2_POLARIZER_DIVISOR = 0.25256          # SolarSoft c2_calfactor.pro: polariser images use factor / 0.25256


def lasco_c2_summing(header) -> int:
    """Pixel summing of a LASCO image: SUMCOL × SUMROW × LEBXSUM × LEBYSUM (0 or missing counts as 1)."""
    f = 1
    for key in ("SUMCOL", "SUMROW", "LEBXSUM", "LEBYSUM"):
        v = header.get(key, 1) if hasattr(header, "get") else 1
        f *= max(int(v or 1), 1)
    return f


def lasco_c2_msb_per_dn(when, calibration: str = "colaninno_howard_2015", *, filter_name: str = "Orange",
                        polarizer: str = "Clear", summing: int = 1) -> float:
    """LASCO C2 calibration factor, MSB per DN/s/pixel, for a date (ISO string, datetime or MJD).

    For 12 August 2026 the two calibrations give 7.589e-12 (Colaninno & Howard) and 6.562e-12
    (SolarSoft): 13.5 % apart in level, a difference already present in 2013, inside the period both were
    fitted on.  Report results with both.  Apply after ``(DN − bias) / (exposure time × exposure factor)``
    and the vignetting correction (``c2vig_final.fts``, multiplicative).

    Only the Orange filter is calibrated here.  A summed image (``summing`` = :func:`lasco_c2_summing` of its
    header) divides the factor, as SolarSoft does.  A polariser image divides the SolarSoft factor by
    0.25256; Colaninno & Howard (2015) calibrate unpolarised (Clear) images only, so that case is refused.
    """
    try:
        a, b = LASCO_C2_CALIBRATIONS[calibration]
    except KeyError:
        raise ValueError(f"unknown calibration {calibration!r}; known: {sorted(LASCO_C2_CALIBRATIONS)}") from None
    if str(filter_name).strip().lower() != "orange":
        raise ValueError(f"filter {filter_name!r}: only the Orange filter is calibrated here")
    if int(summing) != summing or int(summing) < 1:
        raise ValueError("summing must be a positive integer (SUMCOL x SUMROW x LEBXSUM x LEBYSUM)")
    f = (a * mjd(when) + b) * 1e-12 / int(summing)
    if str(polarizer).strip().lower() != "clear":
        if calibration != "solarsoft":
            raise ValueError("Colaninno & Howard (2015) calibrate unpolarised (Clear) images only")
        f /= LASCO_C2_POLARIZER_DIVISOR
    return f


# ------------------------------------------------------------------------------------------------
# Brightness levels in cells
# ------------------------------------------------------------------------------------------------
def cell_medians(image, frame: SolarFrame, rings, *, cell_deg: float = 1.0, valid=None, exclude=None,
                 drop_touching=None, channel=None) -> np.ndarray:
    """Median of the observed pixels in every (ring, angle cell), each image in its own frame.

    Returns an array (n_rings, 360/cell_deg); a cell without data is ``NaN``.  Rings are [r1, r2) in R☉;
    cells [k·cell_deg, (k + 1)·cell_deg) in PA.  No resampling: pixel centres decide the cell.

    ``exclude``: boolean image of pixels to leave out (labels, pylon).  ``drop_touching``: boolean image;
    a cell that contains even one of these pixels is dropped whole (``NaN``).  Use it for the lunar-motion
    band, the gap at the limb and prominences: the rest of such a cell is biased by the same cause.
    """
    a = _masked(image, valid, channel)
    for name, m_ in (("exclude", exclude), ("drop_touching", drop_touching)):
        if m_ is not None and np.shape(m_) != a.shape:
            raise ValueError(f"{name} mask does not match the image")
    if exclude is not None:
        a = np.where(np.asarray(exclude, bool), np.nan, a)
    n_cells = 360.0 / float(cell_deg)
    if abs(n_cells - round(n_cells)) > 1e-9:
        raise ValueError("cell_deg must divide 360")
    n_cells = int(round(n_cells))
    rings = [(float(r1), float(r2)) for r1, r2 in rings]
    if any(not 0.0 <= r1 < r2 for r1, r2 in rings):
        raise ValueError("each ring needs 0 <= r1 < r2")
    srt = sorted(rings)
    if any(b2[0] < b1[1] for b1, b2 in zip(srt, srt[1:])):
        raise ValueError("rings overlap: a pixel would be counted in one ring only")
    r, pa = frame.solar_maps(a.shape)
    ok = np.isfinite(a)
    label = np.full(a.shape, -1, np.int64)
    for i, (r1, r2) in enumerate(rings):
        m = (r >= r1) & (r < r2)
        label[m] = i * n_cells + np.minimum((pa[m] / cell_deg).astype(np.int64), n_cells - 1)
    dropped = np.unique(label[np.asarray(drop_touching, bool) & (label >= 0)]) if drop_touching is not None else []
    label[~ok] = -1
    out = np.full(len(rings) * n_cells, np.nan)
    sel = label >= 0
    if sel.any():
        lab, val = label[sel], a[sel]
        order = np.lexsort((val, lab))                   # grouped median: sort by cell, then by value
        lab, val = lab[order], val[order]
        starts = np.r_[0, np.nonzero(np.diff(lab))[0] + 1]
        counts = np.diff(np.r_[starts, lab.size])
        out[lab[starts]] = 0.5 * (val[starts + (counts - 1) // 2] + val[starts + counts // 2])
    out[np.asarray(dropped, np.int64)] = np.nan
    return out.reshape(len(rings), n_cells)


def level_ratios(ours_cells, ref_cells, *, min_cells: int = 20) -> list[dict]:
    """Ours over the reference, ring by ring, on the cells both observed (and the reference > 0).

    ``ratio_of_medians`` = median(ours)/median(reference); ``median_of_ratios`` = median of the per-cell
    ratios.  Both are given because they react differently to a few bright structures.
    """
    A = np.asarray(ours_cells, np.float64)
    B = np.asarray(ref_cells, np.float64)
    if A.shape != B.shape:
        raise ValueError("cell arrays differ in shape")
    out = []
    for i in range(A.shape[0]):
        m = np.isfinite(A[i]) & np.isfinite(B[i]) & (B[i] > 0)
        k = int(m.sum())
        if k < min_cells:
            out.append(dict(n_cells=k, ratio_of_medians=np.nan, median_of_ratios=np.nan))
            continue
        out.append(dict(n_cells=k, ratio_of_medians=float(np.median(A[i, m]) / np.median(B[i, m])),
                        median_of_ratios=float(np.median(A[i, m] / B[i, m]))))
    return out


def ratio_band(sigma_lo: float, sigma_hi: float) -> tuple[float, float]:
    """1σ band of (our value / an exact reference) when the true value lies in [m(1 − σ_lo), m(1 + σ_hi)].

    The band is [1/(1 + σ_hi), 1/(1 − σ_lo)]: for −20 %/+11 %, 0.90–1.25, not 0.80–1.11.
    """
    if not (0.0 <= sigma_lo < 1.0 and sigma_hi >= 0.0):
        raise ValueError("need 0 <= sigma_lo < 1 and sigma_hi >= 0")
    return 1.0 / (1.0 + sigma_hi), 1.0 / (1.0 - sigma_lo)


# ------------------------------------------------------------------------------------------------
# Declared structure comparison (python -m ael coronagraph)
# ------------------------------------------------------------------------------------------------
_FITS_SUFFIXES = (".fits", ".fit", ".fts")
_SPEC_KEYS = {"image", "frame", "hdu", "channel", "valid", "bin", "supersample", "normalise", "_comment"}
_REF_KEYS = _SPEC_KEYS | {"name", "rings", "dark_sector"}
_DARK_KEYS = {"r_range", "seed_pa_deg", "threshold", "dilate_deg", "_comment"}
_RADII_KEYS = {"min", "max", "n", "spacing", "_comment"}
_TOP_KEYS = {"ours", "references", "radii_rsun", "pa_step_deg", "sigma_deg", "highpass_sigma_deg", "max_shift_deg",
             "note", "_comment"}


def _is_fits(path: Path) -> bool:
    suf = [x.lower() for x in Path(path).suffixes]
    return bool(suf) and (suf[-1] in _FITS_SUFFIXES or (len(suf) > 1 and suf[-1] == ".gz" and suf[-2] in _FITS_SUFFIXES))


def _fits_hdu(hl, hdu):
    """The requested HDU, or the first one that holds an image (AIA level 1.5 keeps it in HDU 1)."""
    if hdu is not None:
        return hl[int(hdu)]
    for h in hl:
        if h.data is not None and np.ndim(h.data) >= 2:
            return h
    raise ValueError("no image HDU in this FITS file")


def _json_safe(x):
    """NaN and infinities become null, so that any JSON reader can read the receipt."""
    if isinstance(x, dict):
        return {k: _json_safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_json_safe(v) for v in x]
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (numbers.Integral, np.integer)):
        return int(x)
    if isinstance(x, (numbers.Real, np.floating)):
        return float(x) if math.isfinite(float(x)) else None
    return x


def _frame_from_spec(spec, root: Path, image_path: Path, hdu, shape) -> tuple[SolarFrame, list]:
    """Frame of one image from its recipe, and the extra files it read (for the receipt)."""
    if not isinstance(spec, dict):
        raise ValueError("a frame must be a JSON object")
    keys = set(spec) - {"_comment"}
    if {"center_xy", "north_px", "east_px"} <= keys:
        kind, allowed = "explicit", {"center_xy", "north_px", "east_px", "observer", "time_utc", "rsun_px",
                                     "north_east_angle_deg"}
    elif {"center_xy", "rsun_px", "north_dir", "east_dir"} <= keys:
        kind, allowed = "axes", {"center_xy", "rsun_px", "north_dir", "east_dir"}
    elif "geometry" in keys:
        kind, allowed = "geometry", {"geometry", "p_angle_deg"}
    elif spec.get("wcs") is True:
        kind, allowed = "wcs", {"wcs", "rsun_arcsec"}
    else:
        raise ValueError(f"cannot build a frame from keys {sorted(keys)}")
    if keys - allowed:
        raise ValueError(f"unknown keys in a {kind} frame: {sorted(keys - allowed)}")
    if kind == "explicit":
        return SolarFrame.from_dict(spec), []
    if kind == "axes":
        return SolarFrame.from_axes(spec["center_xy"], spec["rsun_px"], spec["north_dir"], spec["east_dir"]), []
    if kind == "geometry":
        if "p_angle_deg" not in spec:
            raise ValueError("a frame from a geometry needs p_angle_deg (the solar P angle; nothing is assumed)")
        gp = Path(spec["geometry"]).expanduser()
        gp = gp if gp.is_absolute() else root / gp
        if not gp.is_file():
            raise ValueError(f"geometry not found: {gp}")
        geo = EclipseGeometry.from_json(gp)
        if tuple(geo.shape) != tuple(shape):
            raise ValueError(f"the geometry is for a {tuple(geo.shape)} canvas, the image is {tuple(shape)}")
        return SolarFrame.from_geometry(geo, float(spec["p_angle_deg"])), [gp]
    if not _is_fits(image_path):
        raise ValueError("frame 'wcs' needs a FITS image")
    from astropy.io import fits
    with fits.open(image_path) as hl:
        h = _fits_hdu(hl, hdu)
        if tuple(np.shape(h.data)[-2:]) != tuple(shape):
            raise ValueError("the FITS image and the array read from it differ in shape")
        return SolarFrame.from_wcs_header(h.header, rsun_arcsec_=spec.get("rsun_arcsec")), []


def _load_image(path: Path, hdu, channel) -> np.ndarray:
    """A 2-D image: one plane of a FITS cube (planes first) or one channel of an RGB array (channels last)."""
    from . import io as aio
    if _is_fits(path):
        from astropy.io import fits
        with fits.open(path) as hl:
            a = np.asarray(_fits_hdu(hl, hdu).data, np.float64)
        planes_first = True
    else:
        if hdu is not None:
            raise ValueError(f"{path.name}: 'hdu' applies to FITS files only")
        a = np.asarray(aio.load_array(path), np.float64)
        planes_first = False
    if a.ndim == 3:
        if channel == "luminance":
            from .render import luminance
            a = luminance(np.moveaxis(a, 0, -1) if planes_first else a).astype(np.float64)
        elif channel is None:
            raise ValueError(f"{path.name} has several planes: give 'channel' (an index or 'luminance')")
        else:
            a = a[int(channel)] if planes_first else a[..., int(channel)]
    elif channel is not None:
        raise ValueError(f"{path.name} has a single plane: remove 'channel'")
    if a.ndim != 2:
        raise ValueError(f"{path.name}: expected an image, got shape {a.shape}")
    return a


def structure_from_config(config_path, out_dir, *, progress=print) -> dict:
    """Run a declared structure comparison (see ``examples/coronagraph_config_template.json``).

    Every key of the recipe is checked, and every input is read and checked (canvas sizes, masks, frames)
    before the output directory is created.  Writes ``coronagraph_structure.json`` (results, frames, gates
    and limits), ``receipt.json`` (inputs with SHA-256, the recipe included) and, per reference, an 8-bit PNG
    with the two unrolled, normalised images one above the other for the visual check.
    """
    from . import CREDIT, __version__, io as aio

    path = Path(config_path).resolve()
    root = path.parent
    cfg = json.loads(path.read_text())
    if not isinstance(cfg, dict) or set(cfg) - _TOP_KEYS:
        raise ValueError(f"unknown recipe keys: {sorted(set(cfg) - _TOP_KEYS) if isinstance(cfg, dict) else cfg}")
    for key in ("ours", "references", "radii_rsun"):
        if key not in cfg:
            raise ValueError(f"missing recipe key: {key!r} (nothing is assumed)")
    out = Path(out_dir).resolve()
    if out.exists():
        raise FileExistsError(f"output directory already exists: {out} (nothing is overwritten)")

    def resolve(v):
        q = Path(v).expanduser()
        return q if q.is_absolute() else root / q

    rr = cfg["radii_rsun"]
    if not isinstance(rr, dict) or set(rr) - _RADII_KEYS or not {"min", "max", "n"} <= set(rr):
        raise ValueError("radii_rsun needs min, max and n (and optionally spacing)")
    spacing = rr.get("spacing", "log")
    if spacing not in ("log", "linear"):
        raise ValueError("radii_rsun.spacing is 'log' or 'linear'")
    r0, r1, nr = float(rr["min"]), float(rr["max"]), int(rr["n"])
    if not (0.0 < r0 < r1 and nr >= 2):
        raise ValueError("radii_rsun needs 0 < min < max and n >= 2")
    radii = np.geomspace(r0, r1, nr) if spacing == "log" else np.linspace(r0, r1, nr)
    step = float(cfg.get("pa_step_deg", 0.5))
    _pa_grid(step)

    def check_spec(spec, label, allowed):
        if not isinstance(spec, dict):
            raise ValueError(f"{label}: expected a JSON object")
        if set(spec) - allowed:
            raise ValueError(f"{label}: unknown keys {sorted(set(spec) - allowed)}")
        for key in ("image", "frame"):
            if key not in spec:
                raise ValueError(f"{label}: missing {key!r} (nothing is assumed)")
        for key in ("bin", "supersample"):
            v = spec.get(key, 1)
            if not isinstance(v, int) or isinstance(v, bool) or v < 1:
                raise ValueError(f"{label}: {key} must be an integer >= 1")
        if not isinstance(spec.get("normalise", True), bool):
            raise ValueError(f"{label}: normalise is true or false")

    def prepare(spec, label):
        ip = resolve(spec["image"])
        if not ip.is_file():
            raise ValueError(f"{label}: image not found: {ip}")
        a = _load_image(ip, spec.get("hdu"), spec.get("channel"))
        valid = np.isfinite(a)
        files = [ip]
        if "valid" in spec:
            vp = resolve(spec["valid"])
            if not vp.is_file():
                raise ValueError(f"{label}: valid mask not found: {vp}")
            vm = np.asarray(aio.load_array(vp)).astype(bool)
            if vm.shape != a.shape:
                raise ValueError(f"{label}: valid mask {vm.shape} does not match the image {a.shape}")
            valid &= vm
            files.append(vp)
        fr, extra = _frame_from_spec(spec["frame"], root, ip, spec.get("hdu"), a.shape)
        files += extra
        native, b = fr, int(spec.get("bin", 1))
        if b > 1:
            h, w = (a.shape[0] // b) * b, (a.shape[1] // b) * b
            blk = np.where(valid, a, np.nan)[:h, :w].reshape(h // b, b, w // b, b)
            a = blk.mean(axis=(1, 3))          # a block with any missing pixel is missing
            valid = np.isfinite(a)
            fr = fr.scaled(1.0 / b)
        u = unroll(a, fr, radii, pa_step_deg=step, valid=valid, supersample=int(spec.get("supersample", 1)))
        return dict(files=files, native=native, frame=fr, bin=b, unrolled=u)

    check_spec(cfg["ours"], "ours", _SPEC_KEYS)
    refs = cfg["references"]
    if not isinstance(refs, list) or not refs:
        raise ValueError("references must be a non-empty list")
    names, safes = set(), set()
    for i, ref in enumerate(refs):
        label = f"references[{i}]"
        check_spec(ref, label, _REF_KEYS)
        if "name" not in ref or "rings" not in ref:
            raise ValueError(f"{label}: needs a name and rings (nothing is assumed)")
        name = str(ref["name"])
        safe = "".join(ch if ch.isalnum() else "_" for ch in name)
        if name in names or safe in safes or name == "ours":
            raise ValueError(f"{label}: the name {name!r} is used twice (or clashes once made a file name)")
        names.add(name)
        safes.add(safe)
        rings = ref["rings"]
        if not isinstance(rings, list) or not rings or any(len(x) != 2 or not 0 < float(x[0]) < float(x[1])
                                                            for x in rings):
            raise ValueError(f"{label}: rings are [r1, r2] pairs with 0 < r1 < r2")
        ds = ref.get("dark_sector")
        if ds is not None:
            if not isinstance(ds, dict) or set(ds) - _DARK_KEYS or not {"r_range", "seed_pa_deg"} <= set(ds):
                raise ValueError(f"{label}: dark_sector needs r_range and seed_pa_deg "
                                 f"(and optionally threshold, dilate_deg)")
            if float(ds.get("dilate_deg", 4.0)) < 0:
                raise ValueError(f"{label}: dark_sector.dilate_deg must be >= 0")

    ours = prepare(cfg["ours"], "ours")              # every input is read and checked before anything is written
    progress(f"ours unrolled: R☉ = {ours['frame'].rsun_px:.2f} px, axes {ours['frame'].axis_angle_deg:.3f}° apart")
    prepared = [(ref, prepare(ref, str(ref["name"]))) for ref in refs]
    N_o = nrgf_rows(ours["unrolled"]) if cfg["ours"].get("normalise", True) else ours["unrolled"].data
    pa = ours["unrolled"].pa
    results, sheets, gates = [], [], {}
    for ref, pr in prepared:
        name = str(ref["name"])
        N_r = nrgf_rows(pr["unrolled"]) if ref.get("normalise", True) else pr["unrolled"].data
        excl = None
        if ref.get("dark_sector"):
            ds = ref["dark_sector"]
            excl = dark_sector(N_r, radii, ds["r_range"], float(ds["seed_pa_deg"]),
                               threshold=float(ds.get("threshold", -0.3)), dilate_deg=float(ds.get("dilate_deg", 4.0)))
        res = compare_structure(Unrolled(N_o, radii, pa), Unrolled(N_r, radii, pa), [tuple(x) for x in ref["rings"]],
                                normalise_ours=False, normalise_ref=False, exclude_ref=excl,
                                sigma_deg=float(cfg.get("sigma_deg", 1.5)),
                                highpass_sigma_deg=float(cfg.get("highpass_sigma_deg", 12.0)),
                                max_shift_deg=float(cfg.get("max_shift_deg", 10.0)))
        for x in res:
            progress(f"{name} r {x['r_rsun'][0]:.2f}–{x['r_rsun'][1]:.2f}: rho(0) {x['rho_0']:+.3f} "
                     f"(best {x['rho_best']:+.3f} at {x['shift_deg']:+.1f}°; null max {x['null_max']:+.2f}); "
                     f"detail {x['fine_detail']['rho_0']:+.3f} (null max {x['fine_detail']['null_max']:+.2f})")

        def to8(a):                          # NRGF −2…+4, smallest radius at the bottom
            t = np.clip((a + 2.0) / 6.0, 0, 1)
            return np.where(np.isfinite(t), (255 * t).round(), 0).astype(np.uint8)[::-1]
        sheet = np.vstack([to8(N_o), np.full((4, N_o.shape[1]), 255, np.uint8), to8(N_r)])
        safe = "".join(ch if ch.isalnum() else "_" for ch in name)
        sheets.append((name, f"unrolled_ours_over_{safe}.png", sheet))
        gates[name] = dict(
            rings_with_enough_angles=[bool(x["n_angles"] >= 60) for x in res],
            fine_detail_above_its_null=[bool(np.isfinite(x["fine_detail"]["rho_0"]) and
                                             x["fine_detail"]["rho_0"] > x["fine_detail"]["null_max"]) for x in res],
            best_rotation_at_search_edge=[bool(x["at_search_edge"]) for x in res])
        results.append(dict(name=name, frame_native=pr["native"].to_dict(), bin=pr["bin"], frame_used=pr["frame"].to_dict(),
                            excluded_pa_deg=None if excl is None else [float(pa[i]) for i in np.nonzero(excl)[0]],
                            rings=res))
    out.mkdir(parents=True)
    files = {}
    for name, fname, sheet in sheets:
        files[name] = str(aio.save_png(out / fname, sheet, description=(
            f"ours (top) and {name} (bottom), NRGF -2..+4, PA 0-360 left to right, smallest radius at the bottom")))
    inputs = {"recipe": str(path)}
    for label, pr in [("ours", ours)] + [(str(ref["name"]), pr) for ref, pr in prepared]:
        for j, f in enumerate(pr["files"]):
            inputs[label if j == 0 else f"{label} ({Path(f).name})"] = str(f)
    limits = ("Agreement in position angle only. A radial tone curve a(r)*I + b(r) leaves every number unchanged; "
              "nothing here measures brightness or excludes local artefacts. A best rotation at the edge of the "
              "search window is not an orientation.")
    rec = dict(product="coronagraph structure comparison", library=f"ael {__version__}", credit=CREDIT,
               recipe=str(path), radii_rsun=[float(radii[0]), float(radii[-1]), int(radii.size), spacing],
               pa_step_deg=step, ours=dict(frame_native=ours["native"].to_dict(), bin=ours["bin"],
                                           frame_used=ours["frame"].to_dict()),
               references=results, gates=gates, sheets=files, limits=limits)
    aio.write_receipt(out / "receipt.json", product="coronagraph structure comparison", inputs=inputs,
                      outputs=files, parameters=_json_safe(cfg), gates=_json_safe(gates), notes=limits)
    (out / "coronagraph_structure.json").write_text(json.dumps(_json_safe(rec), indent=1, ensure_ascii=False),
                                                    encoding="utf-8")
    return _json_safe(dict(results=[dict(name=x["name"], rings=[dict(r=y["r_rsun"], rho_0=y["rho_0"],
                                                                     null_max=y["null_max"],
                                                                     fine_rho_0=y["fine_detail"]["rho_0"])
                                                                for y in x["rings"]]) for x in results],
                           gates=gates, out=str(out / "coronagraph_structure.json")))
