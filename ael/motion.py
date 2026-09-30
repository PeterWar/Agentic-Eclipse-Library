"""Coronal motion during totality: epochs, Sun-frame merging, displacement vectors, animations.

A total eclipse lasts one to four minutes, long enough for the inner corona to change: plasma moves
along loops, jets and blobs travel outwards at tens to hundreds of km/s.  If the exposure ladder was
repeated during totality (or several observers along the path combine their data), images of the
same corona taken tens of seconds apart can be compared.

The traps, and what this module does about them:

* **Register on the Sun, not on the Moon.**  The Moon moves across the Sun by ~0.5″/s.  Every frame
  is shifted so that the *Sun's* centre lands on the same canvas point (``to_sun_frame``); the Moon
  then slides across the animation, as it really did.
* **Two kinds of false motion.**  In the Sun frame, anything fixed on the *sensor* (dust, flat-field
  errors, hot pixels, ghosts) moves with minus the telescope's drift, and anything tied to the
  *Moon* (the limb, prominences being covered or uncovered, lunar relief) moves with the Moon.
  ``classify`` rejects every vector consistent with either of those predicted velocities.
* **Brightness is not motion.**  The Sun sets during totality (the corona fades by ~5 % in a minute at
  low altitude) and the sky changes; epochs are photometrically matched before comparing
  (``match_epochs``).
* **Null test.**  Pairs of epochs a few seconds apart show the measurement noise (seeing, noise,
  different exposures); a motion is reported only if it stands out of that distribution.
* **No interpolated frames.**  Animations show only real epochs (with their times); nothing is
  morphed between them.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

from .filters import normalized_gaussian
from .geometry import EclipseGeometry, position_angle
from .polar import remap_valid

__all__ = ["Frame", "Epoch", "group_epochs", "to_sun_frame", "merge_epoch", "match_epochs", "highpass",
           "to_display", "measure_displacements", "classify", "confirm", "null_noise", "fit_global_affine", "Vector",
           "km_per_px", "candidate_sheet"]


@dataclass
class Frame:
    name: str
    t: float                                  # seconds (any origin, e.g. from second contact)
    exposure: float                           # seconds
    sun_xy: tuple[float, float]               # Sun centre in this frame's pixel coordinates
    moon_xy: tuple[float, float] | None = None
    data: np.ndarray | None = None            # calibrated linear signal (counts), 2-D
    saturated: np.ndarray | None = None       # True where the pixel is saturated / non-linear
    gain: float = 1.0                         # multiplicative correction (e.g. extinction)
    meta: dict = field(default_factory=dict)


@dataclass
class Epoch:
    name: str
    t: float                                  # exposure-weighted mean time
    t_min: float
    t_max: float
    data: np.ndarray                          # merged radiance (counts/s), Sun frame
    valid: np.ndarray
    geometry: EclipseGeometry                 # Sun at the reference point; Moon at the members' mean
    moon_xy: list = field(default_factory=list)
    members: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)


def group_epochs(frames: list[Frame], max_gap: float = 3.0, min_members: int = 3) -> list[list[Frame]]:
    """Split frames (sorted by time) wherever consecutive frames are more than ``max_gap`` s apart."""
    fr = sorted(frames, key=lambda f: f.t)
    groups, cur = [], []
    for f in fr:
        if cur and f.t - cur[-1].t > max_gap:
            groups.append(cur)
            cur = []
        cur.append(f)
    if cur:
        groups.append(cur)
    return [g for g in groups if len(g) >= min_members]


def to_sun_frame(data: np.ndarray, sun_xy, ref_xy, out_shape, *, valid: np.ndarray | None = None,
                 interp: str = "lanczos", rotation_deg: float = 0.0, scale: float = 1.0) -> np.ndarray:
    """Resample ``data`` so that the Sun's centre ``sun_xy`` lands on ``ref_xy`` of a canvas of
    ``out_shape``.  Optional rotation (deg, counter-clockwise on the display) and scale about the Sun.
    ``NaN`` where the source has no data."""
    h, w = out_shape
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = X - ref_xy[0], Y - ref_xy[1]
    if rotation_deg or scale != 1.0:
        c, s = np.cos(np.radians(rotation_deg)), np.sin(np.radians(rotation_deg))
        dx, dy = (c * dx - s * dy) / scale, (s * dx + c * dy) / scale
    Xs = (dx + sun_xy[0]).astype(np.float32)
    Ys = (dy + sun_xy[1]).astype(np.float32)
    return remap_valid(np.asarray(data, np.float32), Xs, Ys, interp, valid)


def merge_epoch(frames: list[Frame], ref_xy, out_shape, geometry_template: EclipseGeometry, *,
                sat_dilate: int = 2, moon_margin_px: float = 4.0, name: str = "",
                min_level: float = 0.0, interp: str = "lanczos") -> Epoch:
    """HDR merge of one epoch in the Sun frame.

    Radiance of each frame = ``data · gain / exposure``; weight = exposure (photon-noise optimal),
    zero where the pixel is saturated (dilated by ``sat_dilate``), below ``min_level`` counts, or inside
    that frame's Moon (+``moon_margin_px``).  Each pixel is the weighted mean of the frames that
    observed it cleanly; ``valid`` is False where none did.
    """
    h, w = out_shape
    num = np.zeros((h, w), np.float64)
    den = np.zeros((h, w), np.float64)
    moons, t_w = [], []
    for f in frames:
        d = np.asarray(f.data, np.float32)
        ok = np.isfinite(d) & (d > min_level)
        if f.saturated is not None:
            sat = f.saturated.astype(np.uint8)
            if sat_dilate > 0:
                sat = cv2.dilate(sat, np.ones((2 * sat_dilate + 1, 2 * sat_dilate + 1), np.uint8))
            ok &= sat == 0
        if f.moon_xy is not None and geometry_template.moon_radius_px is not None:
            yy, xx = np.ogrid[:d.shape[0], :d.shape[1]]
            ok &= np.hypot(xx - f.moon_xy[0], yy - f.moon_xy[1]) > geometry_template.moon_radius_px + moon_margin_px
        rad = np.where(ok, d * np.float32(f.gain / f.exposure), np.nan)
        rs = to_sun_frame(rad, f.sun_xy, ref_xy, out_shape, valid=ok, interp=interp)
        good = np.isfinite(rs)
        num[good] += f.exposure * rs[good]
        den[good] += f.exposure
        if f.moon_xy is not None:
            moons.append((f.moon_xy[0] - f.sun_xy[0] + ref_xy[0], f.moon_xy[1] - f.sun_xy[1] + ref_xy[1]))
        t_w.append((f.t, f.exposure))
    valid = den > 0
    data = np.where(valid, num / np.maximum(den, 1e-30), np.nan).astype(np.float32)
    tw = np.array(t_w)
    t_mean = float(np.average(tw[:, 0], weights=tw[:, 1])) if len(tw) else float("nan")
    geo = EclipseGeometry(shape=(h, w), sun_xy=tuple(map(float, ref_xy)),
                          sun_radius_px=geometry_template.sun_radius_px,
                          moon_xy=tuple(np.mean(moons, axis=0)) if moons else None,
                          moon_radius_px=geometry_template.moon_radius_px, north_deg=geometry_template.north_deg,
                          mirrored=geometry_template.mirrored, arcsec_per_px=geometry_template.arcsec_per_px)
    return Epoch(name=name or f"t{t_mean:.1f}", t=t_mean, t_min=float(tw[:, 0].min()), t_max=float(tw[:, 0].max()),
                 data=data, valid=valid, geometry=geo, moon_xy=moons, members=[f.name for f in frames],
                 meta=dict(exposures=[f.exposure for f in frames], times=[f.t for f in frames]))


def match_epochs(epochs: list[Epoch], ref: int = 0, ring_rsun=(1.1, 2.0), max_samples: int = 300_000,
                 seed: int = 0) -> list[dict]:
    """Photometric matching: fit ``E_k ≈ a·E_ref + b`` on common pixels of ``ring_rsun`` (robust, in
    log-spaced radius bins so the bright inner ring does not dominate) and rescale every epoch to the
    reference: ``E_k ← (E_k − b)/a``.  Returns the fitted (a, b) per epoch.  ``a`` below 1 for later
    epochs is the Sun setting (atmospheric extinction)."""
    R = epochs[ref]
    rs = R.geometry.rsun_map()
    rng = np.random.default_rng(seed)
    out = []
    for k, E in enumerate(epochs):
        if k == ref:
            out.append(dict(epoch=E.name, a=1.0, b=0.0, n=0))
            continue
        sel = R.valid & E.valid & (rs >= ring_rsun[0]) & (rs <= ring_rsun[1])
        idx = np.flatnonzero(sel)
        if idx.size > max_samples:
            idx = rng.choice(idx, max_samples, replace=False)
        x = R.data.ravel()[idx].astype(np.float64)
        y = E.data.ravel()[idx].astype(np.float64)
        wgt = 1.0 / np.maximum(x, 1e-9)            # relative residuals: every radius counts
        use = np.ones(len(x), bool)
        a, b = 1.0, 0.0
        for _ in range(8):
            A = np.stack([x[use], np.ones(use.sum())], 1) * wgt[use, None]
            (a, b), *_ = np.linalg.lstsq(A, y[use] * wgt[use], rcond=None)
            res = (y - (a * x + b)) * wgt
            s = 1.4826 * np.median(np.abs(res[use]))
            new = np.abs(res) < 3 * max(s, 1e-12)
            if (new == use).all():
                break
            use = new
        E.data = ((E.data - b) / a).astype(np.float32)
        out.append(dict(epoch=E.name, a=float(a), b=float(b), n=int(use.sum())))
    return out


def highpass(img: np.ndarray, valid: np.ndarray, sigma: float = 6.0, *, log: bool = True,
             min_support: float = 0.5) -> np.ndarray:
    """Unsharp mask in log space: ``ln I − ln(G_σ * I)`` from observed pixels only (NaN elsewhere)."""
    a = np.asarray(img, np.float32)
    m = valid.astype(bool) & np.isfinite(a) & ((a > 0) if log else True)
    x = np.where(m, np.log(np.where(m, a, 1.0)), np.nan) if log else np.where(m, a, np.nan)
    sm = normalized_gaussian(x, m, sigma, min_support)
    return (x - sm).astype(np.float32)


def to_display(hp: np.ndarray, gain: float, *, mid: float = 0.5, nan_value: float = 0.0) -> np.ndarray:
    """High-pass image → [0, 1] with mid-grey at zero detail (the "difference" look)."""
    y = np.clip(mid + gain * np.asarray(hp, np.float32), 0, 1)
    y[~np.isfinite(hp)] = nan_value
    return y


def km_per_px(arcsec_per_px: float, sun_distance_au: float = 1.0) -> float:
    """Projected kilometres per pixel at the Sun (1″ = 725.27 km at 1 AU)."""
    return arcsec_per_px * 725.27 * sun_distance_au


@dataclass
class Vector:
    x: float
    y: float
    dx: float
    dy: float
    peak: float          # normalised cross-correlation at the peak
    contrast: float      # std of the template (detail strength)
    r_rsun: float = float("nan")
    pa: float = float("nan")
    cls: str = ""        # 'coronal', 'sensor', 'lunar', 'still', 'aperture', 'unreliable'
    snr: float = float("nan")
    iso: float = float("nan")    # |λmin/λmax| of the correlation peak's curvature (1 = round peak)
    edge: bool = False           # peak on the border of the search area (true shift may be larger)
    prom: float = float("nan")   # peak minus the best correlation farther than 3 px from it
    rdx: float = float("nan")    # displacement after removing the global affine (see fit_global_affine)
    rdy: float = float("nan")
    weak_ux: float = float("nan")  # unit vector of the flattest direction of the correlation peak
    weak_uy: float = float("nan")


def _subpix(c: np.ndarray, i: int, j: int) -> tuple[float, float]:
    def para(a, b, d):
        den = a - 2 * b + d
        return 0.0 if den == 0 else float(np.clip(0.5 * (a - d) / den, -0.75, 0.75))
    oy = para(c[i - 1, j], c[i, j], c[i + 1, j]) if 0 < i < c.shape[0] - 1 else 0.0
    ox = para(c[i, j - 1], c[i, j], c[i, j + 1]) if 0 < j < c.shape[1] - 1 else 0.0
    return ox, oy


def measure_displacements(a: np.ndarray, b: np.ndarray, valid_a: np.ndarray, valid_b: np.ndarray,
                          geometry: EclipseGeometry, *, window: int = 41, step: int = 20, search: int = 24,
                          r_range_rsun=(1.05, 2.5), min_contrast: float = 0.0, min_peak: float = 0.5,
                          min_prom: float = 0.0, exclude: np.ndarray | None = None) -> list[Vector]:
    """Local displacement of ``b`` relative to ``a`` (two high-pass images in the same Sun frame).

    For every window of ``a`` fully inside the data (and outside ``exclude``), the normalised
    cross-correlation over ±``search`` px in ``b`` gives the displacement (sub-pixel by parabolas).
    Windows whose template is flatter than ``min_contrast`` or whose peak is below ``min_peak`` are
    kept but flagged 'unreliable' by :func:`classify`.
    """
    h, w = a.shape
    hw = window // 2
    rs = geometry.rsun_map()
    ok_a = valid_a & np.isfinite(a)
    ok_b = valid_b & np.isfinite(b)
    if exclude is not None:
        ok_a &= ~exclude
        ok_b &= ~exclude
    ia = cv2.integral(ok_a.astype(np.uint8))
    ib = cv2.integral(ok_b.astype(np.uint8))
    A = np.nan_to_num(a, nan=0.0).astype(np.float32)
    B = np.nan_to_num(b, nan=0.0).astype(np.float32)
    vecs = []
    cx, cy = geometry.sun_xy
    for y0 in range(hw + search, h - hw - search, step):
        for x0 in range(hw + search, w - hw - search, step):
            r = rs[y0, x0]
            if not (r_range_rsun[0] <= r <= r_range_rsun[1]):
                continue
            ya, yb, xa, xb = y0 - hw, y0 + hw + 1, x0 - hw, x0 + hw + 1
            na = ia[yb, xb] - ia[ya, xb] - ia[yb, xa] + ia[ya, xa]
            if na < window * window:
                continue
            ys0, ys1, xs0, xs1 = ya - search, yb + search, xa - search, xb + search
            nb_ = ib[ys1, xs1] - ib[ys0, xs1] - ib[ys1, xs0] + ib[ys0, xs0]
            if nb_ < (window + 2 * search) ** 2:
                continue
            T = A[ya:yb, xa:xb]
            S = B[ys0:ys1, xs0:xs1]
            con = float(T.std())
            if con <= 0:
                continue
            c = cv2.matchTemplate(S, T, cv2.TM_CCOEFF_NORMED)
            i, j = np.unravel_index(int(np.argmax(c)), c.shape)
            ox, oy = _subpix(c, i, j)
            dx = (j + ox) - search
            dy = (i + oy) - search
            edge = i in (0, c.shape[0] - 1) or j in (0, c.shape[1] - 1)
            iso = float("nan")
            wux = wuy = float("nan")
            if 0 < i < c.shape[0] - 1 and 0 < j < c.shape[1] - 1:
                cxx = c[i, j + 1] - 2 * c[i, j] + c[i, j - 1]
                cyy = c[i + 1, j] - 2 * c[i, j] + c[i - 1, j]
                cxy = 0.25 * (c[i + 1, j + 1] - c[i + 1, j - 1] - c[i - 1, j + 1] + c[i - 1, j - 1])
                w_, U_ = np.linalg.eigh(np.array([[cxx, cxy], [cxy, cyy]], float))
                ev = np.abs(w_)
                iso = float(ev.min() / max(ev.max(), 1e-12))
                k_ = int(np.argmin(ev))
                wux, wuy = float(U_[0, k_]), float(U_[1, k_])
            cc = c.copy()
            cc[max(0, i - 3):i + 4, max(0, j - 3):j + 4] = -1.0
            prom = float(c[i, j] - cc.max())
            pa = float(position_angle(x0 - cx, y0 - cy, geometry.north_deg, geometry.mirrored))
            vecs.append(Vector(x=float(x0), y=float(y0), dx=float(dx), dy=float(dy), peak=float(c[i, j]),
                               contrast=con, r_rsun=float(r), pa=pa, iso=iso, edge=bool(edge), prom=prom,
                               weak_ux=wux, weak_uy=wuy))
    for v in vecs:
        if v.peak < min_peak or v.contrast < min_contrast or v.edge or not (v.prom >= min_prom):
            v.cls = "unreliable"
    return vecs


def fit_global_affine(vecs: list[Vector], center_xy, *, classes=("coronal", "still", "unconfirmed", "aperture"),
                      min_peak: float = 0.5, clip: float = 3.0, n_iter: int = 12) -> dict:
    """Robust affine displacement field ``d = t + M·(x − c)`` over the reliable vectors, and residuals.

    Between two epochs of the same eclipse the whole field moves a little for reasons that are not
    coronal: registration drift of the Sun model, the change of atmospheric refraction as the Sun sets
    (a vertical compression of ~0.04 % per minute at 9° altitude), field rotation.  Coronal motions are
    local and sparse, so a robust global fit captures the systematics; each vector gets ``rdx, rdy``
    (displacement minus the fit).  Report the fit: it is a measurement of those systematics.
    """
    sel = [v for v in vecs if (v.cls in classes or v.cls != "unreliable" and "*" in classes or
                               (classes == ("",) and v.cls != "unreliable")) and v.peak >= min_peak]
    if len(sel) < 10:
        for v in vecs:
            v.rdx, v.rdy = v.dx, v.dy
        return dict(n=len(sel), params=None)
    cx, cy = center_xy
    X = np.array([[v.x - cx, v.y - cy] for v in sel]) / 1000.0
    D = np.array([[v.dx, v.dy] for v in sel])
    w = np.array([v.peak for v in sel])
    A = np.column_stack([np.ones(len(X)), X])
    use = np.ones(len(X), bool)
    for _ in range(n_iter):
        px, *_ = np.linalg.lstsq(A[use] * w[use, None], D[use, 0] * w[use], rcond=None)
        py, *_ = np.linalg.lstsq(A[use] * w[use, None], D[use, 1] * w[use], rcond=None)
        res = D - np.column_stack([A @ px, A @ py])
        s = 1.4826 * np.median(np.abs(res[use]), axis=0)
        new = (np.abs(res) < clip * np.maximum(s, 1e-6)).all(axis=1)
        if (new == use).all():
            break
        use = new
    for v in vecs:
        xx, yy = (v.x - cx) / 1000.0, (v.y - cy) / 1000.0
        v.rdx = v.dx - (px[0] + px[1] * xx + px[2] * yy)
        v.rdy = v.dy - (py[0] + py[1] * xx + py[2] * yy)
    return dict(n=int(use.sum()), params=dict(tx=float(px[0]), ty=float(py[0]),
                m=[[float(px[1]), float(px[2])], [float(py[1]), float(py[2])]], units="px, px per 1000 px"),
                residual_sigma=[float(s[0]), float(s[1])])


def classify(vecs: list[Vector], dt: float, *, sensor_velocity: tuple[float, float],
             moon_velocity: tuple[float, float] | None, noise_px: float, k_sigma: float = 3.0,
             min_px: float = 1.0, min_iso: float = 0.15, false_zone_frac: float = 0.25,
             false_zone_min_px: float = 3.0, aperture_iso: float = 0.6, aperture_cos: float = 0.8,
             aperture_min_peak: float = 0.8) -> dict:
    """Label each vector.

    * 'sensor' – consistent (within k·noise) with the drift of sensor-fixed patterns
      (``sensor_velocity`` = minus the Sun's drift on the sensor, px/s, in the Sun frame);
    * 'lunar'  – consistent with the Moon's motion relative to the Sun (``moon_velocity``, px/s);
    * 'still'  – smaller than max(k·noise, min_px);
    * 'aperture' – the correlation peak is a ridge (|λmin/λmax| < ``min_iso``), or the motion runs along
      the flattest direction of a moderately elongated peak (``iso < aperture_iso``, cosine > ``aperture_cos``)
      while the correlation is below ``aperture_min_peak``: a ray can slide along itself, so only the
      component across it is known.  (2026 data: noise made such slips look like 200 km/s outflows; a
      real blob on a ray, in the synthetic test, correlates at 0.84 and is kept);
    * 'coronal' – everything else that is reliable.
    ``noise_px`` comes from a null pair (two epochs a few seconds apart).  The zones around the two
    false-motion predictions are wide — ``max(k·noise, false_zone_min_px, false_zone_frac·|d_pred|)`` —
    because a window that mixes a fixed pattern with static corona lands *near*, not on, the prediction
    (seen on the 2026 data: residual flat-field spots 2 px off the sensor drift).  Returns counts.
    """
    thr = max(k_sigma * noise_px, min_px)
    ds = np.array(sensor_velocity, float) * dt
    dm = None if moon_velocity is None else np.array(moon_velocity, float) * dt
    counts: dict[str, int] = {}
    for v in vecs:
        if v.cls != "unreliable":
            d = np.array([v.dx, v.dy])
            r = np.array([v.rdx, v.rdy]) if np.isfinite(v.rdx) else d
            mag = float(np.hypot(*r))
            v.snr = mag / max(noise_px, 1e-9)
            zs = max(thr, false_zone_min_px, false_zone_frac * float(np.hypot(*ds)))
            zm = None if dm is None else max(thr, false_zone_min_px, false_zone_frac * float(np.hypot(*dm)))
            if np.hypot(*(d - ds)) < zs:
                v.cls = "sensor"
            elif dm is not None and np.hypot(*(d - dm)) < zm:
                v.cls = "lunar"
            elif mag < thr:
                v.cls = "still"
            elif not (v.iso >= min_iso) or (v.iso < aperture_iso and v.peak < aperture_min_peak and
                                            np.isfinite(v.weak_ux) and
                                            abs(r[0] * v.weak_ux + r[1] * v.weak_uy) > aperture_cos * mag):
                # a ridge-like peak, or — at modest correlation — a motion along the flattest direction of
                # the peak (a ray sliding along itself): only the component across it is measured
                v.cls = "aperture"
            else:
                v.cls = "coronal"
        counts[v.cls] = counts.get(v.cls, 0) + 1
    return counts


def null_noise(null_vecs: list[Vector]) -> dict:
    """Measurement noise from a null pair (two epochs a few seconds apart): robust σ per axis, and
    the 90th/99th percentiles of |d| (the tail shows windows where the correlation is ambiguous)."""
    d = np.array([[v.dx, v.dy] for v in null_vecs if v.cls != "unreliable"], float)
    if len(d) == 0:
        return dict(sigma=float("nan"), p90=float("nan"), p99=float("nan"), n=0)
    s = 1.4826 * np.median(np.abs(d - np.median(d, axis=0)), axis=0)
    mag = np.hypot(d[:, 0], d[:, 1])
    return dict(sigma=float(np.mean(s)), p50=float(np.percentile(mag, 50)), p90=float(np.percentile(mag, 90)),
                p99=float(np.percentile(mag, 99)), n=int(len(d)))


def confirm(long_vecs: list[Vector], dt_long: float, *, null_vecs: list[Vector] | None = None,
            null_max_px: float = 1.5, mid_vecs: list[Vector] | None = None, dt_mid: float | None = None,
            tol_px: float = 1.5, tol_frac: float = 0.3, min_neighbors: int = 0, neighbor_radius: float | None = None,
            neighbor_tol_px: float = 2.0) -> dict:
    """Confirm 'coronal' vectors with three independent tests; failures become 'unconfirmed'.

    1. **Local null**: at the same grid point, the displacement between two epochs a few seconds apart
       must be small (≤ ``null_max_px``) and reliable.  A large null displacement means the window's
       correlation is ambiguous (a ray sliding along itself), whatever the long pair says.
    2. **Proportional to time**: with a middle epoch, ``d_mid ≈ d_long·dt_mid/dt_long`` within
       ``tol_px + tol_frac·|d|`` (real motion accumulates; random slips do not).
    3. **Neighbours** (optional, off by default): at least ``min_neighbors`` other coronal vectors within
       ``neighbor_radius`` px (default 1.6 grid steps) with a displacement within ``neighbor_tol_px``.
       Useful for extended features; a small blob on static rays is seen by a single window.
    Vectors are matched by grid position (use the same window/step/search for every pair).
    """
    key = lambda v: (int(round(v.x)), int(round(v.y)))
    nul = {key(v): v for v in (null_vecs or [])}
    mid = {key(v): v for v in (mid_vecs or [])}
    cands = [v for v in long_vecs if v.cls == "coronal"]
    reasons: dict[str, int] = {}

    def fail(v, why):
        v.cls = "unconfirmed"
        reasons[why] = reasons.get(why, 0) + 1

    for v in cands:
        d = np.array([v.dx, v.dy])
        if null_vecs is not None:
            n = nul.get(key(v))
            if n is None or n.cls == "unreliable" or np.hypot(n.dx, n.dy) > null_max_px:
                fail(v, "null")
                continue
        if mid_vecs is not None and dt_mid:
            m = mid.get(key(v))
            if m is None or m.cls == "unreliable":
                fail(v, "mid_missing")
                continue
            dl = np.array([v.rdx, v.rdy]) if np.isfinite(v.rdx) else d
            dmid = np.array([m.rdx, m.rdy]) if np.isfinite(m.rdx) else np.array([m.dx, m.dy])
            pred = dl * (dt_mid / dt_long)
            if np.hypot(*(dmid - pred)) > tol_px + tol_frac * np.hypot(*dl):
                fail(v, "not_proportional")
                continue
    if min_neighbors > 0:
        cor = [v for v in long_vecs if v.cls == "coronal"]
        if cor:
            xs = np.array([[v.x, v.y] for v in cor])
            ds = np.array([[v.dx, v.dy] for v in cor])
            if neighbor_radius is None:
                steps = np.diff(np.unique(xs[:, 0]))
                neighbor_radius = 1.6 * (float(np.min(steps)) if len(steps) else 20.0)
            keep = []
            for i, v in enumerate(cor):
                dd = np.hypot(*(xs - xs[i]).T)
                close = (dd > 0) & (dd <= neighbor_radius)
                sim = np.hypot(*(ds[close] - ds[i]).T) <= neighbor_tol_px if close.any() else np.array([], bool)
                keep.append(int(sim.sum()) >= min_neighbors)
            for v, k in zip(cor, keep):
                if not k:
                    fail(v, "isolated")
    counts: dict[str, int] = {}
    for v in long_vecs:
        counts[v.cls] = counts.get(v.cls, 0) + 1
    return dict(counts=counts, failed=reasons)


def candidate_sheet(vecs: list[Vector], images: dict, *, half: int = 70, zoom: int = 2, max_rows: int = 24,
                    classes=("coronal",)) -> np.ndarray:
    """Contact sheet for the visual check that no gate replaces: for each candidate, the same crop of
    every image in ``images`` (e.g. {'early': hp0, 'late': hp1, 'early_B': ..., 'late_B': ...}) side by
    side, same grey scale per row, with the measured displacement drawn on the late crops.  Look at it:
    a real motion is a feature visibly displaced; a slip along a ray is not."""
    rows = []
    sel = [v for v in vecs if v.cls in classes][:max_rows]
    for v in sel:
        x, y = int(round(v.x)), int(round(v.y))
        ref = list(images.values())[0][y - half:y + half, x - half:x + half]
        g = 0.5 / max(float(np.nanpercentile(np.abs(ref), 99)), 1e-9)
        tiles = []
        for k, im in enumerate(images.values()):
            c = im[y - half:y + half, x - half:x + half]
            tt = np.clip(0.5 + g * np.nan_to_num(c), 0, 1)
            tt = cv2.resize(tt, (2 * half * zoom, 2 * half * zoom), interpolation=cv2.INTER_NEAREST)
            tt = np.repeat((tt * 255).astype(np.uint8)[..., None], 3, axis=2)
            if k % 2 == 1:
                c0 = (half * zoom, half * zoom)
                c1 = (int(c0[0] + zoom * v.dx), int(c0[1] + zoom * v.dy))
                cv2.arrowedLine(tt, c0, c1, (0, 200, 255), 2, cv2.LINE_AA, tipLength=0.25)
            tiles.append(np.pad(tt, ((3, 3), (3, 3), (0, 0)), constant_values=255))
        rows.append(np.hstack(tiles))
    return np.vstack(rows) if rows else np.zeros((10, 10, 3), np.uint8)
