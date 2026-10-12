"""Differential atmospheric extinction across an eclipse image.

With the Sun low, the air mass changes across the field of view.  In 2026 the Sun stood about 9° high
at mid-totality: the air mass was about 5.75 two solar radii above the Sun (towards the zenith), 6.05 at
the Sun and 6.39 two radii below.  With an extinction coefficient of 0.40 mag per air mass, the side of the
corona towards the horizon received about 9 % less light than the Sun's own line of sight at 1.5 R☉ and
about 23 % less at 4 R☉; the side towards the zenith about 9 % and 24 % more.  A global colour or
brightness scale cannot remove that: it is a dipole across the corona, growing with radius.

What is observed is

    I = C · 10^(−0.4·k·X) + S,

where ``C`` is the corona above the atmosphere, ``X`` the air mass along each pixel's line of sight,
``k`` the extinction coefficient (mag per air mass) and ``S`` the sky: light scattered *in* the
atmosphere, which is not extinguished like the corona.  The correction therefore works in **linear light
after subtracting the sky**:

    I_corr = (I − S) · 10^(0.4·k·(X − X_ref)),

which brings every pixel to the reference air mass ``X_ref`` — the air mass at the Sun, or the one at
which a photometric zero point was evaluated.  It is achromatic by default (one ``k`` for every channel,
so colour ratios are unchanged); a ``k`` per channel is optional and changes the colour.

Air mass: Kasten, F. & Young, A. T. (1989), "Revised optical air mass tables and approximation formula",
*Applied Optics* 28(22), 4735–4738, as a function of the **apparent** (refracted) altitude.

The lesson that comes with it (see ``docs/FIELD_LESSONS.md``): **sky and extinction are degenerate**.  A
sky plane fitted on uncorrected data where there is still corona absorbs the extinction dipole; a constant
sky estimated a few solar radii from the Sun contains corona.  Fit the sky where the corona is negligible
(e.g. r ≥ 8 R☉), measure ``k`` independently (for instance from the dimming of the corona during
totality: :func:`dimming_k`), and use the correction as a **consistency test** against a reference without
atmosphere (:func:`k_nulling_dipole`), not as a measurement of ``k``.

Nothing is invented: pixels without data, or whose line of sight is below the horizon, stay ``NaN``.
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from .geometry import EclipseGeometry, direction_of_pa

__all__ = ["kasten_young", "Site", "solar_horizontal", "altitude_map", "airmass_map", "airmass_map_from_site",
           "airmass_map_from_wcs", "extinction_factor", "correct_extinction", "ring_dipole", "k_nulling_dipole",
           "k_consistency", "dimming_k", "extinction_from_config"]

ARCSEC = math.pi / (180.0 * 3600.0)
LN10_04 = 0.4 * math.log(10.0)        # d ln(flux) / d mag, with the sign of an extinction correction


# ------------------------------------------------------------------------------------------------
# Air mass
# ------------------------------------------------------------------------------------------------
def kasten_young(altitude_deg):
    """Relative optical air mass of Kasten & Young (1989) for the **apparent** altitude in degrees.

    ``X = 1 / (sin h + 0.50572 · (h + 6.07995°)^−1.6364)``.  It is a fit to a model atmosphere, not an exact
    law: at the zenith it gives 0.9997, at the horizon 37.92.  Below the horizon the result is ``NaN``
    (no extrapolation).
    """
    h = np.asarray(altitude_deg, np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        x = 1.0 / (np.sin(np.radians(h)) + 0.50572 * np.power(h + 6.07995, -1.6364))
    return np.where(h >= 0.0, x, np.nan)


@dataclass(frozen=True)
class Site:
    """Observing site, with what refraction needs.

    ``lon_deg`` is positive to the east.  ``pressure_hpa=None`` uses the standard atmosphere at
    ``height_m`` (``1013.25·(1 − 2.25577e-5·h)^5.25588`` hPa); give the measured value if you have it.
    ``wavelength_um`` is the effective wavelength used for refraction (0.55 µm: green).
    """

    lat_deg: float
    lon_deg: float
    height_m: float = 0.0
    pressure_hpa: float | None = None
    temperature_c: float = 10.0
    relative_humidity: float = 0.0
    wavelength_um: float = 0.55

    def pressure(self) -> float:
        if self.pressure_hpa is not None:
            return float(self.pressure_hpa)
        return float(1013.25 * (1.0 - 2.25577e-5 * self.height_m) ** 5.25588)

    @classmethod
    def from_dict(cls, d: dict) -> "Site":
        unknown = set(d) - set(cls.__dataclass_fields__)
        if unknown:
            raise ValueError(f"unknown site keys: {sorted(unknown)}")
        return cls(**d)


def _astropy():
    try:
        import astropy.units as u
        from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_body
        from astropy.time import Time
    except ImportError as exc:  # pragma: no cover - depends on the installation
        raise ImportError("this function needs astropy: pip install -e '.[raw]'") from exc
    return u, AltAz, EarthLocation, SkyCoord, get_body, Time


def _altaz_frame(site: Site, time_utc, refraction: bool = True):
    u, AltAz, EarthLocation, _, _, Time = _astropy()
    loc = EarthLocation(lat=site.lat_deg * u.deg, lon=site.lon_deg * u.deg, height=site.height_m * u.m)
    t = Time(time_utc, scale="utc")
    if refraction:
        frame = AltAz(obstime=t, location=loc, pressure=site.pressure() * u.hPa, temperature=site.temperature_c * u.deg_C,
                      relative_humidity=site.relative_humidity, obswl=site.wavelength_um * u.micron)
    else:
        frame = AltAz(obstime=t, location=loc, pressure=0 * u.hPa)
    return frame, loc, t


def solar_horizontal(site: Site, time_utc: str, *, refraction: bool = True) -> dict:
    """The Sun seen from ``site`` at ``time_utc`` (ISO string, UTC), with astropy.

    Returns the apparent (refracted) and true altitude, the azimuth, the air mass at the Sun and the
    **position angle of the zenith** as seen from the Sun (degrees from celestial north through east, ICRS
    north): the direction in which the air mass falls fastest.  The zenith PA is obtained by moving a point
    one degree up the Sun's vertical in the horizontal frame and measuring its position angle on the sky;
    refraction moves points along verticals, so it does not change this direction.
    """
    u, _, _, SkyCoord, get_body, _ = _astropy()
    frame, loc, t = _altaz_frame(site, time_utc, refraction)
    sun = get_body("sun", t, loc)
    aa = sun.transform_to(frame)
    true = sun.transform_to(_altaz_frame(site, time_utc, False)[0])
    # Directions only (no distance): the Sun's parallax must not enter the position angle.
    here = SkyCoord(alt=aa.alt, az=aa.az, frame=frame)
    up = SkyCoord(alt=aa.alt + 1.0 * u.deg, az=aa.az, frame=frame)
    zpa = float(here.icrs.position_angle(up.icrs).deg) % 360.0
    alt = float(aa.alt.deg)
    return dict(time_utc=str(time_utc), apparent_altitude_deg=alt, true_altitude_deg=float(true.alt.deg),
                azimuth_deg=float(aa.az.deg), zenith_pa_deg=zpa, airmass=float(kasten_young(alt)),
                refraction=bool(refraction), pressure_hpa=site.pressure() if refraction else 0.0,
                temperature_c=site.temperature_c, wavelength_um=site.wavelength_um,
                site=asdict(site))


def _sky_axes(geometry: EclipseGeometry, north_px, east_px, arcsec_per_px):
    """2×2 matrix whose columns are the image displacements (px) of 1″ towards celestial north and east."""
    if (north_px is None) != (east_px is None):
        raise ValueError("give both north_px and east_px, or neither")
    if north_px is not None:
        m = np.array([[north_px[0], east_px[0]], [north_px[1], east_px[1]]], np.float64)
    else:
        s = arcsec_per_px if arcsec_per_px is not None else geometry.arcsec_per_px
        if s is None or not np.isfinite(s) or s <= 0:
            raise ValueError("the plate scale is needed: set geometry.arcsec_per_px, arcsec_per_px, or north_px/east_px")
        nx, ny = direction_of_pa(0.0, geometry.north_deg, geometry.mirrored)
        ex, ey = direction_of_pa(90.0, geometry.north_deg, geometry.mirrored)
        m = np.array([[nx, ex], [ny, ey]], np.float64) / float(s)
    if not np.isfinite(m).all() or abs(np.linalg.det(m)) < 1e-12:
        raise ValueError("north/east image vectors must be finite and not parallel")
    return m


def _zenith_sky_direction(m, zenith_pa_deg, zenith_image_deg):
    if (zenith_pa_deg is None) == (zenith_image_deg is None):
        raise ValueError("give exactly one of zenith_pa_deg (sky position angle) or zenith_image_deg (image direction)")
    if zenith_pa_deg is not None:
        q = math.radians(float(zenith_pa_deg))
        return math.cos(q), math.sin(q)
    a = math.radians(float(zenith_image_deg))
    n, e = np.linalg.solve(m, np.array([math.sin(a), -math.cos(a)]))
    norm = math.hypot(n, e)
    return n / norm, e / norm


def _altitude_rows(geometry, sun_altitude_deg, zenith_pa_deg, zenith_image_deg, north_px, east_px, arcsec_per_px,
                   block_rows):
    """Yield ``(y0, y1, altitude block in degrees, float64)`` over the canvas."""
    h0 = float(sun_altitude_deg)
    if not np.isfinite(h0) or not -1.0 < h0 <= 90.0:
        raise ValueError("sun_altitude_deg must be the apparent altitude of the Sun, in degrees")
    m = _sky_axes(geometry, north_px, east_px, arcsec_per_px)
    minv = np.linalg.inv(m)
    cn, ce = _zenith_sky_direction(m, zenith_pa_deg, zenith_image_deg)
    sx, sy = geometry.sun_xy
    h, w = geometry.shape
    sh0, ch0 = math.sin(math.radians(h0)), math.cos(math.radians(h0))
    dx = np.arange(w, dtype=np.float64) - sx
    for y0 in range(0, h, block_rows):
        y1 = min(h, y0 + block_rows)
        dy = (np.arange(y0, y1, dtype=np.float64) - sy)[:, None]
        n = (minv[0, 0] * dx[None, :] + minv[0, 1] * dy) * ARCSEC     # tangent-plane radians towards north
        e = (minv[1, 0] * dx[None, :] + minv[1, 1] * dy) * ARCSEC     # and towards east
        xi = n * cn + e * ce                                           # towards the zenith
        eta = -n * ce + e * cn                                         # across it
        s = (sh0 + xi * ch0) / np.sqrt(1.0 + xi * xi + eta * eta)
        yield y0, y1, np.degrees(np.arcsin(np.clip(s, -1.0, 1.0)))


def altitude_map(geometry: EclipseGeometry, sun_altitude_deg: float, *, zenith_pa_deg: float | None = None,
                 zenith_image_deg: float | None = None, north_px=None, east_px=None,
                 arcsec_per_px: float | None = None, block_rows: int = 256, dtype=np.float64) -> np.ndarray:
    """Apparent altitude (degrees) of the line of sight of every pixel.

    The image is taken as a gnomonic projection of the apparent sky with its tangent point at the Sun
    (``geometry.sun_xy``), which is exact to second order in the field angle for a small field.  The
    offset of each pixel is split into a component ``ξ`` towards the zenith and ``η`` across it; then
    ``sin h = (sin h☉ + ξ·cos h☉) / sqrt(1 + ξ² + η²)``.

    Orientation, in one of three ways:

    * ``zenith_pa_deg``: position angle of the zenith seen from the Sun (from :func:`solar_horizontal`),
      with the image's celestial north from ``geometry.north_deg``/``mirrored`` and its plate scale;
    * ``zenith_image_deg``: the direction of the zenith on the image, in degrees clockwise from image up
      (0 for a level camera on an alt-azimuth mount);
    * either of them with ``north_px``/``east_px``: image displacements (dx, dy) in pixels of one arcsecond
      towards celestial north and east, e.g. from a plate solution (they may be non-orthogonal).

    The plate scale is the optical one (arcsec of sky per pixel, from stars or the ephemeris), not the
    Sun's vertical diameter, which refraction compresses.  Computed in float64 by blocks of rows; ``dtype``
    is the type of the returned map.
    """
    out = np.empty(tuple(geometry.shape), dtype)
    for y0, y1, alt in _altitude_rows(geometry, sun_altitude_deg, zenith_pa_deg, zenith_image_deg, north_px,
                                      east_px, arcsec_per_px, block_rows):
        out[y0:y1] = alt
    return out


def airmass_map(geometry: EclipseGeometry, sun_altitude_deg: float, *, zenith_pa_deg: float | None = None,
                zenith_image_deg: float | None = None, north_px=None, east_px=None,
                arcsec_per_px: float | None = None, block_rows: int = 256, dtype=np.float64) -> np.ndarray:
    """Kasten–Young air mass of every pixel; same arguments as :func:`altitude_map`.  ``dtype=np.float32``
    halves the memory of a large canvas (relative precision 6·10⁻⁸, far below any use here)."""
    out = np.empty(tuple(geometry.shape), dtype)
    for y0, y1, alt in _altitude_rows(geometry, sun_altitude_deg, zenith_pa_deg, zenith_image_deg, north_px,
                                      east_px, arcsec_per_px, block_rows):
        out[y0:y1] = kasten_young(alt)
    return out


def airmass_map_from_site(geometry: EclipseGeometry, site: Site, time_utc: str, *, north_px=None, east_px=None,
                          arcsec_per_px: float | None = None, dtype=np.float64):
    """Air mass of every pixel from the site and the time: the Sun's apparent altitude and the zenith's
    position angle come from astropy (:func:`solar_horizontal`), the projection on the image from the
    geometry (celestial north and plate scale) or from ``north_px``/``east_px``.  Returns ``(X, info)``."""
    info = solar_horizontal(site, time_utc)
    X = airmass_map(geometry, info["apparent_altitude_deg"], zenith_pa_deg=info["zenith_pa_deg"],
                    north_px=north_px, east_px=east_px, arcsec_per_px=arcsec_per_px, dtype=dtype)
    info = dict(info, method="astropy Sun + gnomonic projection on the image", airmass_at_sun=info["airmass"])
    return X, info


def airmass_map_from_wcs(wcs, shape, site: Site, time_utc: str, *, step_px: int = 64, refraction: bool = True,
                         check_points: int = 200, seed: int = 0):
    """Air mass of every pixel from a plate solution (an astropy celestial WCS of the image).

    Every node of a grid (``step_px``) is taken through the WCS to the sky and into the horizontal frame
    with refraction; the apparent altitude is interpolated with a bicubic spline, and checked against the
    exact transformation at ``check_points`` random pixels (the maximum difference goes into ``info``; it
    includes the Sun's gravitational light deflection that astropy applies to catalogue directions,
    ≤ 1.75″ at the limb, i.e. ≤ 3·10⁻⁴ in air mass).  Returns ``(X, info)``.

    A plate solution fitted on stars in the same frames maps pixels to *true* sky positions; this route
    then applies refraction point by point.  :func:`airmass_map_from_site` instead treats pixel offsets as
    *apparent* offsets.  The two differ by the differential refraction (about 0.8 % of the vertical offset
    at 9° altitude: up to ~0.015 in air mass two degrees from the Sun).
    """
    from scipy.interpolate import RectBivariateSpline

    frame, _, _ = _altaz_frame(site, time_utc, refraction)
    h, w = shape

    def alt_of(x, y):
        sky = wcs.pixel_to_world(np.asarray(x, np.float64), np.asarray(y, np.float64))
        return np.asarray(sky.transform_to(frame).alt.deg, np.float64)

    rows = np.unique(np.r_[np.arange(0, h, step_px), h - 1]).astype(np.float64)
    cols = np.unique(np.r_[np.arange(0, w, step_px), w - 1]).astype(np.float64)
    yy, xx = np.meshgrid(rows, cols, indexing="ij")
    grid = alt_of(xx.ravel(), yy.ravel()).reshape(yy.shape)
    kx, ky = min(3, len(rows) - 1), min(3, len(cols) - 1)
    spline = RectBivariateSpline(rows, cols, grid, kx=kx, ky=ky)
    alt = spline(np.arange(h, dtype=np.float64), np.arange(w, dtype=np.float64), grid=True)
    rng = np.random.default_rng(seed)
    px, py = rng.uniform(0, w - 1, check_points), rng.uniform(0, h - 1, check_points)
    err = float(np.max(np.abs(spline.ev(py, px) - alt_of(px, py))))
    info = dict(method="astropy WCS -> AltAz, bicubic spline", step_px=int(step_px), refraction=bool(refraction),
                spline_max_error_deg=err, time_utc=str(time_utc), site=asdict(site),
                pressure_hpa=site.pressure() if refraction else 0.0)
    return kasten_young(alt), info


# ------------------------------------------------------------------------------------------------
# Correction
# ------------------------------------------------------------------------------------------------
def _k_vector(k, channels: int | None):
    kk = np.atleast_1d(np.asarray(k, np.float64))
    if not np.isfinite(kk).all() or (kk < 0).any():
        raise ValueError("k must be finite and non-negative (mag per air mass)")
    if kk.size == 1:
        return float(kk[0])
    if channels is None or kk.size != channels:
        raise ValueError(f"k has {kk.size} values; the image has {channels or 1} channel(s)")
    return kk


def extinction_factor(airmass, k, x_ref: float) -> np.ndarray:
    """``10^(0.4·k·(X − X_ref))``: multiply a sky-subtracted linear image by this to bring every pixel to
    ``X_ref``.  ``k`` scalar → (H, W); ``k`` per channel → (H, W, C)."""
    X = np.asarray(airmass)
    X = X if X.dtype == np.float32 else X.astype(np.float64)          # float32 in, float32 out
    if not np.isfinite(x_ref):
        raise ValueError("x_ref must be finite")
    kk = np.atleast_1d(np.asarray(k, np.float64))
    if not np.isfinite(kk).all() or (kk < 0).any():
        raise ValueError("k must be finite and non-negative (mag per air mass)")
    if kk.size == 1:
        return 10.0 ** (0.4 * float(kk[0]) * (X - float(x_ref)))
    return 10.0 ** (0.4 * kk.astype(X.dtype)[None, None, :] * (X[..., None] - float(x_ref)))


def correct_extinction(image, airmass, k, *, x_ref: float, sky, valid=None, keep_sky: bool = False,
                       block_rows: int = 512) -> np.ndarray:
    """Differential-extinction correction of a **linear** image: ``(image − sky)·10^(0.4·k·(X − x_ref))``.

    * ``image``: (H, W) or (H, W, C) linear data, sky included.
    * ``sky``: the sky to subtract first — a scalar, one value per channel, an (H, W) or (H, W, C) map.  Pass
      0 explicitly if the sky is already subtracted.  The sky is atmospheric light: it is not corrected.
    * ``k``: mag per air mass, one value (achromatic: colour ratios unchanged) or one per channel.
    * ``x_ref``: the reference air mass — at the Sun, or where a photometric zero point was evaluated.
    * ``keep_sky``: add the same sky back after the correction (for display pipelines that expect it).

    Returns float32 with ``NaN`` wherever there is no data (``valid`` False, non-finite input, line of sight
    below the horizon).  Nothing is filled.  Computed in float64 by blocks of rows.
    """
    a = np.asarray(image)
    X = np.asarray(airmass)
    if a.ndim not in (2, 3) or X.shape != a.shape[:2]:
        raise ValueError("airmass must be (H, W) and match the image")
    if not np.isfinite(x_ref):
        raise ValueError("x_ref must be finite")
    channels = a.shape[2] if a.ndim == 3 else None
    kk = _k_vector(k, channels)
    S = np.asarray(sky, np.float64) if np.ndim(sky) < 2 else np.asarray(sky)
    if S.ndim == 1:
        if channels is None or S.size != channels:
            raise ValueError("a sky vector needs one value per channel")
        S = S[None, None, :]
    elif S.ndim == 2:
        if S.shape != a.shape[:2]:
            raise ValueError("sky map does not match the image")
    elif S.ndim == 3 and S.shape != a.shape:
        raise ValueError("sky map does not match the image")
    v = None
    if valid is not None:
        v = np.asarray(valid, bool)
        if v.shape != a.shape[:2]:
            raise ValueError("valid mask does not match the image")
    out = np.empty(a.shape, np.float32)
    for y0 in range(0, a.shape[0], block_rows):
        sl = slice(y0, min(a.shape[0], y0 + block_rows))
        ab = np.asarray(a[sl], np.float64)
        Sb = np.asarray(S[sl] if S.ndim >= 2 else S, np.float64)
        if channels is not None and Sb.ndim == 2:
            Sb = Sb[..., None]
        Xb = np.asarray(X[sl], np.float64)
        Eb = extinction_factor(Xb, kk, x_ref)
        if channels is not None and Eb.ndim == 2:
            Eb = Eb[..., None]
        ob = (ab - Sb) * Eb + (Sb if keep_sky else 0.0)
        ok = np.isfinite(Xb)
        if v is not None:
            ok &= v[sl]
        ok = (ok[..., None] if channels is not None else ok) & np.isfinite(ob)
        out[sl] = np.where(ok, ob, np.nan)
    return out


# ------------------------------------------------------------------------------------------------
# Consistency tests
# ------------------------------------------------------------------------------------------------
def ring_dipole(values, valid, geometry: EclipseGeometry, rings_rsun, *, direction_pa_deg: float,
                n_sectors: int = 12, min_count: int = 50) -> list[dict]:
    """Dipole of ``values`` in rings around the Sun, along a direction (e.g. the zenith).

    In each ring ``values = c0 + a·cos(PA − PA_dir) + b·sin(PA − PA_dir)`` is fitted by least squares on the
    valid pixels; ``a`` is the dipole *along* the direction (positive: larger towards it) and ``b`` across it.
    Errors are jackknife errors over ``n_sectors`` angular sectors (neighbouring pixels are correlated, so a
    per-pixel error would be optimistic).  Use it on ``ln(image / reference)`` with a reference without
    atmosphere, or on ``ln E`` to see the dipole that extinction predicts.
    """
    v = np.asarray(values, np.float64)
    m = np.isfinite(v) if valid is None else (np.asarray(valid, bool) & np.isfinite(v))
    r = geometry.rsun_map(dtype=np.float64)
    pa = geometry.pa_map(dtype=np.float64)
    out = []
    for r0, r1 in rings_rsun:
        sel = m & (r >= r0) & (r < r1)
        if sel.sum() < max(min_count, 3 * n_sectors):
            out.append(dict(r0=float(r0), r1=float(r1), n=int(sel.sum()), c0=np.nan, along=np.nan, across=np.nan,
                            along_err=np.nan, across_err=np.nan))
            continue
        th = np.radians(pa[sel] - direction_pa_deg)
        A = np.stack([np.ones_like(th), np.cos(th), np.sin(th)], 1)
        z = v[sel]
        coef = np.linalg.lstsq(A, z, rcond=None)[0]
        sector = np.floor((np.degrees(th) % 360.0) / (360.0 / n_sectors)).astype(int)
        jk = []
        for s in range(n_sectors):
            keep = sector != s
            if keep.sum() >= 3 and np.unique(sector[keep]).size >= 3:
                jk.append(np.linalg.lstsq(A[keep], z[keep], rcond=None)[0])
        jk = np.asarray(jk)
        nj = len(jk)
        err = np.sqrt((nj - 1) / nj * np.sum((jk - jk.mean(0)) ** 2, axis=0)) if nj > 2 else np.full(3, np.nan)
        out.append(dict(r0=float(r0), r1=float(r1), n=int(sel.sum()), c0=float(coef[0]), along=float(coef[1]),
                        across=float(coef[2]), along_err=float(err[1]), across_err=float(err[2])))
    return out


def k_nulling_dipole(log_ratio_uncorrected, airmass, x_ref: float, valid, geometry: EclipseGeometry, rings_rsun, *,
                     zenith_pa_deg: float, n_sectors: int = 12) -> list[dict]:
    """The ``k`` that would cancel, ring by ring, the zenith dipole of ``ln(net / reference)``.

    ``log_ratio_uncorrected`` is ``ln((I − S) / R)`` with the sky subtracted but no extinction correction,
    and ``R`` a reference without atmosphere scaled to the same field.  The corrected ratio is
    ``ln((I − S)/R) + 0.4·ln10·k·(X − X_ref)``, so its dipole is linear in ``k`` and ``k_null = −D₀ / D_X``.

    Read the result as a **consistency test**: one ``k`` should cancel every ring.  A ``k_null`` that drifts
    with radius means the sky model and the extinction are being confused, not that ``k`` changes: a sky
    gradient that absorbed part of the dipole pulls it down, a sky level that contains corona (or a missing
    sky gradient) pushes it up, and the two can cancel.
    """
    lnE = LN10_04 * (np.asarray(airmass, np.float64) - float(x_ref))
    d0 = ring_dipole(log_ratio_uncorrected, valid, geometry, rings_rsun, direction_pa_deg=zenith_pa_deg,
                     n_sectors=n_sectors)
    dx = ring_dipole(lnE, valid, geometry, rings_rsun, direction_pa_deg=zenith_pa_deg, n_sectors=n_sectors)
    out = []
    for a, b in zip(d0, dx):
        kn = -a["along"] / b["along"] if np.isfinite(b["along"]) and abs(b["along"]) > 0 else np.nan
        ke = abs(a["along_err"] / b["along"]) if np.isfinite(kn) else np.nan
        out.append(dict(r0=a["r0"], r1=a["r1"], n=a["n"], dipole_uncorrected=a["along"],
                        dipole_uncorrected_err=a["along_err"], dipole_per_unit_k=b["along"], k_null=float(kn),
                        k_null_err=float(ke), across_uncorrected=a["across"], across_err=a["across_err"]))
    return out


def k_consistency(rows: list[dict], k: float, *, n_sigma: float = 3.0, min_err: float = 0.005) -> dict:
    """Gate on the rows of :func:`k_nulling_dipole`: does the declared ``k`` cancel the dipole in every ring?

    Passes if ``|k_null − k| ≤ n_sigma · max(k_null_err, min_err)`` in every ring with a defined ``k_null``
    **and** the weighted slope of ``k_null`` against ring radius is within ``n_sigma`` of zero (with three
    rings or more).  A significant slope is the signature of a sky model confused with the extinction
    (a plane that took part of the dipole, a sky level that contains corona, a missing sky gradient).
    The thresholds are inputs; do not relax them to obtain a pass.

    A pass is consistency, not proof: two sky errors can compensate (a plane fitted on a corona tail that
    absorbs part of the dipole, and the same tail raising the sky level), and the gate says nothing about
    the absolute level.  Declare the sky bias separately (pass a corona model through the same sky fit).
    """
    use = [r_ for r_ in rows if np.isfinite(r_["k_null"]) and np.isfinite(r_["k_null_err"])]
    if not use:
        return dict(passed=False, reason="no ring with a defined k_null", rows=rows)
    dev = [abs(r_["k_null"] - k) / max(r_["k_null_err"], min_err) for r_ in use]
    rc = np.array([0.5 * (r_["r0"] + r_["r1"]) for r_ in use])
    kn = np.array([r_["k_null"] for r_ in use])
    wt = 1.0 / np.maximum(np.array([r_["k_null_err"] for r_ in use]), min_err) ** 2
    slope = slope_err = np.nan
    if len(use) >= 3:
        A = np.stack([np.ones_like(rc), rc], 1)
        cov = np.linalg.inv(A.T @ (A * wt[:, None]))
        coef = cov @ (A.T @ (wt * kn))
        slope, slope_err = float(coef[1]), float(math.sqrt(cov[1, 1]))
    worst = float(max(dev))
    slope_ok = not np.isfinite(slope) or abs(slope) <= n_sigma * slope_err
    return dict(passed=bool(worst <= n_sigma and slope_ok), worst_sigma=worst, n_sigma=n_sigma, min_err=min_err,
                k=float(k), slope_per_rsun=slope, slope_err=slope_err, slope_ok=bool(slope_ok), n_rings=len(use))


def dimming_k(later, earlier, x_later: float, x_earlier: float, valid, geometry: EclipseGeometry, *,
              r_rsun=(1.05, 4.8), bin_rsun: float = 0.05, min_delta_airmass: float = 0.02, min_count: int = 30) -> dict:
    """Extinction coefficient from the dimming of the corona between two registered frames of totality.

    Use two frames with the **same exposure, ISO and position on the sensor**, taken as far apart in time
    as totality allows (the Sun's air mass changes as it sets or rises), registered on the Sun.  Median
    profiles in rings of ``bin_rsun`` are fitted as ``later = a·earlier + b`` (``b`` absorbs a change of sky);
    then ``k = −2.5·log10(a) / (X_later − X_earlier)``.  It measures *every* multiplicative change between
    the frames: it is the extinction only if the transparency was steady.  Repeat over several pairs and
    exposures and quote their scatter.  Pairs too close in air mass are refused.
    """
    dX = float(x_later) - float(x_earlier)
    if not np.isfinite(dX) or abs(dX) < min_delta_airmass:
        raise ValueError(f"air-mass difference {dX:.4f} is too small to measure k (minimum {min_delta_airmass})")
    a1 = np.asarray(later, np.float64)
    a0 = np.asarray(earlier, np.float64)
    m = np.isfinite(a1) & np.isfinite(a0)
    if valid is not None:
        m &= np.asarray(valid, bool)
    r = geometry.rsun_map(dtype=np.float64)
    edges = np.arange(r_rsun[0], r_rsun[1] + 0.5 * bin_rsun, bin_rsun)
    p1, p0 = [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = m & (r >= lo) & (r < hi)
        if sel.sum() >= min_count:
            p1.append(np.median(a1[sel]))
            p0.append(np.median(a0[sel]))
    if len(p0) < 4:
        raise ValueError("too few populated rings to fit the dimming")
    p0, p1 = np.asarray(p0), np.asarray(p1)
    A = np.stack([p0, np.ones_like(p0)], 1)
    (a, b), *_ = np.linalg.lstsq(A, p1, rcond=None)
    res = p1 - A @ np.array([a, b])
    dof = max(len(p0) - 2, 1)
    cov = np.linalg.inv(A.T @ A) * float(res @ res) / dof
    if a <= 0:
        raise ValueError("the fitted scale is not positive: the frames do not match")
    k = -2.5 * math.log10(a) / dX
    k_err = 2.5 / math.log(10.0) * math.sqrt(cov[0, 0]) / (a * abs(dX))
    return dict(k=float(k), k_err_fit=float(k_err), a=float(a), b=float(b), delta_airmass=dX, n_rings=int(len(p0)),
                r_rsun=list(r_rsun), bin_rsun=float(bin_rsun),
                note="fit error only; the scatter between pairs is the honest uncertainty")


# ------------------------------------------------------------------------------------------------
# Declared recipe (ael extinction --config ... --out ...)
# ------------------------------------------------------------------------------------------------
def _fit_sky(img, valid, geometry, spec):
    from .render import sky_background

    if set(spec) - {"r_min_rsun", "order"}:
        raise ValueError("sky.fit takes r_min_rsun and order")
    r_min = float(spec["r_min_rsun"])
    order = int(spec.get("order", 1))
    if not 0 <= order <= 3:
        raise ValueError("sky.fit.order must be 0–3")
    planes = img[..., None] if img.ndim == 2 else img
    models, infos = [], []
    for c in range(planes.shape[-1]):
        mdl, inf = sky_background(planes[..., c], valid, geometry, r_min_rsun=r_min, order=order)
        if inf["n_used"] < 1000:
            raise ValueError(f"sky fit kept only {inf['n_used']} pixels in channel {c}: check the data and r_min_rsun")
        models.append(mdl)
        infos.append(inf)
    sky = np.stack(models, -1)
    return (sky[..., 0] if img.ndim == 2 else sky), dict(method="robust polynomial fit", r_min_rsun=r_min, order=order,
                                                        channels=infos)


def extinction_from_config(config_path, out_dir, *, progress=print) -> dict:
    """Run a declared extinction recipe (see ``examples/extinction_config_template.json``).

    Inputs: a linear stack, its geometry and valid mask; how to obtain the sky (fitted far from the Sun, an
    array, or values); how to obtain the air mass (site and time with astropy, the Sun's altitude and the
    zenith direction, or an array); ``k`` (one value or one per channel) and ``x_ref`` (a number, or
    ``"sun"``).  Writes a new directory with the corrected linear image(s), the air-mass and factor maps,
    the sky used and a receipt.  The input files are never modified.
    """
    from . import io

    path = Path(config_path).resolve()
    root = path.parent
    cfg = json.loads(path.read_text())
    allowed = {"input", "geometry", "valid", "sky", "airmass", "k", "x_ref", "keep_sky", "note", "_comment"}
    if set(cfg) - allowed:
        raise ValueError(f"unknown recipe keys: {sorted(set(cfg) - allowed)}")
    for key in ("input", "geometry", "sky", "airmass", "k", "x_ref"):
        if key not in cfg:
            raise ValueError(f"missing recipe key: {key!r} (nothing is assumed)")

    def resolve(v):
        p = Path(v).expanduser()
        return p if p.is_absolute() else root / p

    a = np.asarray(io.load_array(resolve(cfg["input"])), np.float32)
    if a.ndim not in (2, 3):
        raise ValueError("input must be a linear (H, W) or (H, W, C) array")
    geo = EclipseGeometry.from_json(resolve(cfg["geometry"]))
    if tuple(a.shape[:2]) != tuple(geo.shape):
        raise ValueError("geometry does not match input canvas")
    valid = np.isfinite(a).all(axis=-1) if a.ndim == 3 else np.isfinite(a)
    if "valid" in cfg:
        vm = np.asarray(io.load_array(resolve(cfg["valid"])))
        if vm.shape != valid.shape:
            raise ValueError("valid does not match input canvas")
        valid &= vm.astype(bool)

    # --- sky -----------------------------------------------------------------------------------
    sk = cfg["sky"]
    if not isinstance(sk, dict) or len(sk) != 1 or next(iter(sk)) not in ("fit", "array", "value"):
        raise ValueError('sky must be one of {"fit": {...}}, {"array": path}, {"value": number or list}')
    kind, spec = next(iter(sk.items()))
    if kind == "fit":
        sky, sky_info = _fit_sky(a, valid, geo, spec)
    elif kind == "array":
        sky = np.asarray(io.load_array(resolve(spec)), np.float32)
        sky_info = dict(method="array", path=str(resolve(spec)))
    else:
        sky = np.asarray(spec, np.float64)
        sky_info = dict(method="declared value", value=spec)

    # --- air mass ------------------------------------------------------------------------------
    am = cfg["airmass"]
    if not isinstance(am, dict):
        raise ValueError("airmass must be an object")
    orient = {key: am[key] for key in ("north_px", "east_px", "arcsec_per_px") if key in am}
    if "array" in am:
        if set(am) != {"array"}:
            raise ValueError("airmass.array takes no other keys")
        X = np.asarray(io.load_array(resolve(am["array"])), np.float32)
        if X.shape != a.shape[:2]:
            raise ValueError("airmass array does not match input canvas")
        am_info = dict(method="array", path=str(resolve(am["array"])))
        x_sun = None
    elif "site" in am:
        if set(am) - {"site", "time_utc", "north_px", "east_px", "arcsec_per_px"} or "time_utc" not in am:
            raise ValueError("airmass from a site takes site, time_utc and optional north_px/east_px/arcsec_per_px")
        X, am_info = airmass_map_from_site(geo, Site.from_dict(am["site"]), am["time_utc"], dtype=np.float32, **orient)
        x_sun = am_info["airmass"]
    elif "sun_altitude_deg" in am:
        if set(am) - {"sun_altitude_deg", "zenith_pa_deg", "zenith_image_deg", "north_px", "east_px", "arcsec_per_px"}:
            raise ValueError("unknown airmass keys")
        X = airmass_map(geo, am["sun_altitude_deg"], zenith_pa_deg=am.get("zenith_pa_deg"),
                        zenith_image_deg=am.get("zenith_image_deg"), dtype=np.float32, **orient)
        x_sun = float(kasten_young(am["sun_altitude_deg"]))
        am_info = dict(method="declared Sun altitude and zenith direction", **am, airmass_at_sun=x_sun)
    else:
        raise ValueError("airmass needs site+time_utc, sun_altitude_deg+zenith direction, or array")

    # --- k and the reference -------------------------------------------------------------------
    k = cfg["k"]
    if cfg["x_ref"] == "sun":
        if x_sun is None:
            raise ValueError('x_ref "sun" needs the air mass computed from a site or a Sun altitude')
        x_ref = x_sun
    else:
        x_ref = float(cfg["x_ref"])
    keep_sky = bool(cfg.get("keep_sky", False))
    progress(f"extinction: k={k}, x_ref={x_ref:.4f}, X {np.nanmin(X):.3f}–{np.nanmax(X):.3f}")
    net = correct_extinction(a, X, k, x_ref=x_ref, sky=sky, valid=valid)
    E = extinction_factor(X, k, x_ref)

    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=False)
    outputs = {}
    for name, arr in (("corrected_net", net), ("airmass", X.astype(np.float32)), ("factor", E.astype(np.float32)),
                      ("sky", np.broadcast_to(np.asarray(sky, np.float32), a.shape).astype(np.float32))):
        p = out / f"{name}.npy"
        np.save(p, arr)
        outputs[name] = p
    if keep_sky:
        ws = correct_extinction(a, X, k, x_ref=x_ref, sky=sky, valid=valid, keep_sky=True)
        p = out / "corrected_with_sky.npy"
        np.save(p, ws)
        outputs["corrected_with_sky"] = p
    below = int(np.count_nonzero(~np.isfinite(X)))
    nan_in = ~valid
    nan_out = ~(np.isfinite(net).all(axis=-1) if net.ndim == 3 else np.isfinite(net))
    gates = dict(nothing_outside_data=bool(nan_out[nan_in].all()),
                 pixels_below_horizon=below,
                 achromatic=bool(np.atleast_1d(np.asarray(k)).size == 1))
    fin = np.isfinite(E) & (valid[..., None] if E.ndim == 3 else valid)
    rs = geo.rsun_map(dtype=np.float32)
    summary = {}
    for rr in (1.5, 2.0, 3.0, 4.0):
        ring = valid & np.isfinite(X) & (np.abs(rs - rr) < 0.05)
        if ring.any():
            summary[f"{rr:g}_rsun"] = dict(factor_min=float(np.min(E[ring] if E.ndim == 2 else E[ring].min(-1))),
                                           factor_max=float(np.max(E[ring] if E.ndim == 2 else E[ring].max(-1))))
    params = dict(recipe=cfg, k=k, x_ref=x_ref, keep_sky=keep_sky, sky=sky_info, airmass=am_info,
                  airmass_range=[float(np.nanmin(X)), float(np.nanmax(X))],
                  factor_range=[float(np.min(E[fin])), float(np.max(E[fin]))] if fin.any() else None,
                  factor_by_radius=summary, formula="(I - sky) * 10**(0.4*k*(X - x_ref))",
                  airmass_formula="Kasten & Young (1989), apparent altitude")
    inputs = {key: resolve(cfg[key]) for key in ("input", "geometry", "valid") if key in cfg}
    inputs["config"] = path
    receipt = io.write_receipt(out / "receipt.json", product="differential extinction correction", inputs=inputs,
                               outputs=outputs, parameters=params, gates=gates,
                               notes="Linear light; sky subtracted before the correction and never corrected itself. "
                                     "k is an input, not a result. Sky and extinction are degenerate: fit the sky "
                                     "where the corona is negligible and test the correction against a reference "
                                     "without atmosphere. Rebuild every filter layer from the corrected stack; do "
                                     "not compensate a finished image.")
    return dict(files={k_: str(v) for k_, v in outputs.items()}, receipt=str(receipt), gates=gates)
