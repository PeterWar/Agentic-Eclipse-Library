"""Coronal-motion GIFs without waves: every frame with the same recipe at every radius, and the same grain.

An animation shows every difference between its frames, and the eye reads any difference that follows the
corona's isophotes — or that circles the Sun — as a *wave*.  On the 12 Aug 2026 data the waves came from the
way the frames were built, not from the corona and not from working in colour (rings per frame were 7 % of
the detail both in green only and in R+2G+B).  Four causes, the first two inside a single instrument:

1. **The Moon's edge.**  The detail filter makes the limb bright.  If different sources reach the limb in
   different epochs, the rim changes thickness from frame to frame and pulses.
2. **Alternating exposure ladders.**  Each ladder has its own saturation boundaries — they follow isophotes —
   and its own grain; between 1.4 and 2.1 R☉ the grain jumped up to 1.35× from one frame to the next.
3. **A second instrument whose frames saturate at different radii in different epochs.**  At every saturation
   isophote the sharpness (the second camera is softer) and the grain change.
4. **Different grain in each final frame.**

One rule cures them: **every frame with the same recipe at every radius, and the same grain.**

* :func:`ael.motion.merge_epoch` with ``feather_px``: saturation and Moon boundaries enter with smooth
  weights, so no boundary is a step.
* :func:`equalize_fine_grain`: epochs cleaner than the noisiest mix their *fine* part towards a noisier version
  of themselves (the same epoch without its longest exposure, or without the second instrument) until the
  grain matches, point by point.  Nothing is added: data are only given less weight.
* :func:`add_fine_detail`: a second instrument adds only its *fine* detail (log high-pass), only beyond the
  radius where all its frames are free of saturation (:func:`saturation_free_radius`), through the same smooth
  window in every epoch.  The large scale always comes from the main instrument, so no level step can appear.
* :func:`uniform_moon_edge`: the same rim profile, tied to the Moon, in every frame.
* Gates :func:`ael.gates.grain_uniformity` and :func:`ael.gates.no_concentric_bands` before anything is shown.

The price is signal-to-noise in each frame (2026: −11 % at 1.2 R☉ to −54 % at 2 R☉ against the version with
waves); in an animation a constant grain is much less visible than one that changes.  The best cure is at
capture: repeat the *same* exposure series regularly through totality.

:func:`two_site_change` compares the start-to-end change of two independent series (two instruments or two
sites) and gives the zones where both see the same change — the white arrows of the 2026 GIF.  An arrow marks
a place, not a direction: it cannot tell a displacement from a change of brightness.
"""
from __future__ import annotations

import cv2
import numpy as np

from .filters import normalized_gaussian
from .geometry import EclipseGeometry

__all__ = ["smoothstep", "feather", "saturation_free_radius", "ring_noise", "add_fine_detail", "display_detail",
           "equalize_fine_grain", "uniform_moon_edge", "common_noise_filter", "render_frames", "output_matrix",
           "draw_zone_arrows", "two_site_change", "fine_band"]


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def feather(valid: np.ndarray, px: float, smooth: bool = True, edges: bool = True) -> np.ndarray:
    """Weights in [0, 1]: 0 outside ``valid``, rising to 1 at ``px`` pixels from the nearest unusable pixel
    (and, with ``edges``, from the border of the array: a sensor edge is a boundary too)."""
    v = np.asarray(valid, bool)
    if px <= 0:
        return v.astype(np.float32)
    if edges:
        d = cv2.distanceTransform(np.pad(v, 1).astype(np.uint8), cv2.DIST_L2, 5)[1:-1, 1:-1]
    else:
        d = cv2.distanceTransform(v.astype(np.uint8), cv2.DIST_L2, 5)
    t = np.clip(d / float(px), 0.0, 1.0)
    return (smoothstep(t) if smooth else t).astype(np.float32)


def _log(img: np.ndarray, valid: np.ndarray | None = None):
    a = np.asarray(img, np.float32)
    m = np.isfinite(a) & (a > 0)
    if valid is not None:
        m &= np.asarray(valid, bool)
    return np.where(m, np.log(np.where(m, a, 1.0)), np.nan).astype(np.float32), m


def fine_band(detail: np.ndarray, px: float = 1.4) -> np.ndarray:
    """What is finer than ``px``: the band where a coronal image is almost only noise (grain)."""
    m = np.isfinite(detail)
    return np.where(m, detail - normalized_gaussian(np.where(m, detail, 0.0), m, px, 0.05), np.nan).astype(np.float32)


def saturation_free_radius(usable: list[np.ndarray], geometry: EclipseGeometry, *, coverage: np.ndarray | None = None,
                           frac: float = 0.995, step: float = 0.02, run: int = 10, r_range=(1.0, 4.0),
                           feather_px: float = 12.0) -> list[float]:
    """For each frame's usable mask (on the common canvas), the smallest radius (R☉) from which at least
    ``frac`` of every ring is usable — with full weight after ``feather_px`` — for ``run`` consecutive rings.
    The window of :func:`add_fine_detail` must start beyond the largest of them."""
    rs = geometry.rsun_map()
    rr = np.arange(r_range[0], r_range[1], step)
    out = []
    for u in usable:
        w = feather(u, feather_px)
        cov = np.ones(u.shape, bool) if coverage is None else np.asarray(coverage, bool)
        good = []
        for r0 in rr:
            ring = cov & (rs >= r0) & (rs < r0 + step)
            good.append((w[ring] >= 0.99).mean() if ring.sum() > 200 else np.nan)
        good = np.array(good)
        r_ok = np.nan
        for i in range(len(rr) - run):
            seg = good[i:i + run]
            if np.all(np.isfinite(seg)) and np.all(seg >= frac):
                r_ok = float(rr[i])
                break
        out.append(r_ok)
    return out


def ring_noise(img: np.ndarray, geometry: EclipseGeometry, *, valid: np.ndarray | None = None, fine_px: float = 1.5,
               step: float = 0.05, r_range=(1.0, 3.6), min_pixels: int = 200) -> np.ndarray:
    """Map of the noise of ``ln img`` per ring: 1.4826·MAD of what is finer than ``fine_px``, interpolated in
    radius.  Inverse squares of it are the weights of :func:`add_fine_detail`."""
    lg, m = _log(img, valid)
    hp = np.where(m, lg - normalized_gaussian(np.where(m, lg, 0.0), m, fine_px, 0.05), np.nan)
    rs = geometry.rsun_map()
    rr = np.arange(r_range[0], r_range[1], step)
    s = []
    for r0 in rr:
        k = m & (rs >= r0) & (rs < r0 + step) & np.isfinite(hp)
        s.append(1.4826 * np.median(np.abs(hp[k] - np.median(hp[k]))) if k.sum() > min_pixels else np.nan)
    s = np.array(s)
    ok = np.isfinite(s) & (s > 0)
    if not ok.any():
        raise ValueError("ring_noise: no ring with enough data")
    return np.interp(rs, rr[ok] + step / 2, s[ok]).astype(np.float32)


def add_fine_detail(base: np.ndarray, base_weight: np.ndarray, extras: list[tuple[np.ndarray, np.ndarray]],
                    geometry: EclipseGeometry, *, window_rsun=(2.15, 2.65), fine_px: float = 15.0):
    """Add a second instrument's fine detail to ``base`` (same canvas, both linear and photometrically matched).

    ``ln out = ln base + Σ w_s·HP(ln x_s − ln base) / (W_base + Σ w_s)``, where HP removes what is coarser than
    ``fine_px`` and every ``w_s`` is multiplied by the same smooth radial window (0 below ``window_rsun[0]``,
    1 beyond ``window_rsun[1]``).  ``base_weight`` and each ``w_s`` are inverse variances of the fine detail
    (e.g. ``feather(usable)/ring_noise(...)**2``), 0 where unusable.  The large scale is the base's: a level or
    gradient difference between the instruments can never make a step.  Returns ``(out, total_weight)``."""
    lb, mb = _log(base)
    rs = geometry.rsun_map()
    win = smoothstep((rs - window_rsun[0]) / max(window_rsun[1] - window_rsun[0], 1e-6)).astype(np.float32)
    acc = np.zeros(base.shape, np.float64)
    den = np.where(mb, np.asarray(base_weight, np.float64), 0.0)
    for img, w in extras:
        lx, mx = _log(img)
        both = mb & mx & np.isfinite(w) & (w > 0)
        dl = np.where(both, lx - lb, 0.0).astype(np.float32)
        hp = np.where(both, dl - normalized_gaussian(dl, both, fine_px, 0.05), 0.0)
        ww = np.where(both, np.asarray(w, np.float64) * win, 0.0)
        acc += ww * np.nan_to_num(hp)
        den += ww
    out = np.where(mb, np.exp(lb + acc / np.maximum(den, 1e-30)), np.nan).astype(np.float32)
    return out, den.astype(np.float32)


def display_detail(img: np.ndarray, geometry: EclipseGeometry, *, valid: np.ndarray | None = None,
                   fine=(0.7, 4.0), coarse=(1.3, 6.0), blend_rsun=(1.6, 2.0)) -> np.ndarray:
    """Detail shown in the animation: difference of Gaussians of ``ln img`` (from observed pixels only), fine
    near the Sun and coarser outwards, where the signal-to-noise ratio is lower."""
    lg, m = _log(img, valid)
    x = np.where(m, lg, 0.0)
    g = lambda s: normalized_gaussian(x, m, s, 0.5)
    a = g(fine[0]) - g(fine[1])
    b = g(coarse[0]) - g(coarse[1])
    w = np.clip((geometry.rsun_map() - blend_rsun[0]) / max(blend_rsun[1] - blend_rsun[0], 1e-6), 0, 1)
    d = np.where(np.isfinite(a) & np.isfinite(b), (1 - w) * a + w * b, np.where(np.isfinite(a), a, b))
    return np.where(m, d, np.nan).astype(np.float32)


def _grain(img: np.ndarray, geometry: EclipseGeometry, detail, fine_px: float, measure: str) -> np.ndarray:
    """The grain to equalize.  ``"detail"`` (default): the band finer than ``fine_px`` of ``detail(img)``, the grain
    as shown on screen; it contains a little real fine structure, so an epoch with sharper seeing looks slightly
    noisier (2026: a residual of ≤ 1.11× per ring).  ``"pixel"``: differences between neighbouring pixels of
    ``ln img``.  ⛔ Fails on registered stacks: the noise at the pixel scale depends on each frame's sub-pixel
    shift (interpolation smooths it), not on the noise seen on screen (2026: 1.63× instead of 1.11×)."""
    if measure == "detail":
        return fine_band(detail(img, geometry), fine_px)
    lg, _ = _log(img)
    dx = np.full(lg.shape, np.nan, np.float32); dy = np.full(lg.shape, np.nan, np.float32)
    dx[:, :-1] = (lg[:, 1:] - lg[:, :-1]) / np.sqrt(2.0)
    dy[:-1, :] = (lg[1:, :] - lg[:-1, :]) / np.sqrt(2.0)
    return np.where(np.isfinite(dx) & np.isfinite(dy), (dx + dy) / np.sqrt(2.0), np.where(np.isfinite(dx), dx, dy)).astype(np.float32)


def _local_var(x: np.ndarray, mask: np.ndarray, px: float) -> np.ndarray:
    m = mask & np.isfinite(x)
    return normalized_gaussian(np.where(m, x * x, 0.0), m, px, 0.05)


def equalize_fine_grain(primary: list[np.ndarray], noisier: list[np.ndarray], geometry: EclipseGeometry, *,
                        detail=display_detail, fine_px: float = 1.4, window_px: float = 15.0, hp_px: float = 10.0,
                        smooth_px: float = 3.0, min_excess: float = 0.02, passes: int = 2,
                        target: np.ndarray | None = None, measure: str = "detail"):
    """The same grain in every epoch, point by point, without adding anything.

    ``noisier[i]`` must be a version of ``primary[i]`` made from a *subset of the same data* (the epoch without
    its longest exposure, or without the second instrument): then Cov(primary, noisier) = Var(primary), and
    ``z = (1−u)·primary + u·noisier`` has variance ``Vp + u²(Vn − Vp)``.  The variances are measured where the
    grain lives — the band finer than ``fine_px`` of ``detail(img)`` — in windows of ``window_px``; the target is
    the noisiest epoch's.  Only the fine part (finer than ``hp_px``) is mixed, in log: the large scale is never
    touched (mixing whole images makes boiling blotches).  ⛔ Do not measure the grain at coarser scales: there
    the variance is real sharpness (seeing changes from instant to instant), and the equalization goes wrong.

    The local variances are estimates; ``passes`` > 1 measures again and tops up where the first pass fell short
    (where it already reached the target nothing changes, so the covariance rule still holds).

    Returns ``(equalized list, report)``; the report gives, per epoch, the mean mixing fraction ``u`` and the
    share of points where even the noisier version cannot reach the target (that grain difference remains)."""
    if passes > 1:
        cur, reps, T0 = list(primary), [], target
        for _ in range(passes):
            cur, rep = equalize_fine_grain(cur, noisier, geometry, detail=detail, fine_px=fine_px, window_px=window_px,
                                           hp_px=hp_px, smooth_px=smooth_px, min_excess=min_excess, passes=1, target=T0,
                                           measure=measure)
            T0 = rep["target"]            # the target is fixed once, from the original epochs: no ratchet
            reps.append(rep)
        return cur, dict(epochs=reps[-1]["epochs"], passes=[r["epochs"] for r in reps])
    n = len(primary)
    if len(noisier) != n:
        raise ValueError("one noisier version per epoch")
    ok = np.ones(primary[0].shape, bool)
    for p, q in zip(primary, noisier):
        ok &= np.isfinite(p) & (p > 0) & np.isfinite(q) & (q > 0)
    Vp = [_local_var(_grain(p, geometry, detail, fine_px, measure), ok, window_px) for p in primary]
    Vn = [_local_var(_grain(q, geometry, detail, fine_px, measure), ok, window_px) for q in noisier]
    if target is None:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)   # all-NaN where no epoch has data
            T = np.nanmax(np.stack(Vp), axis=0)
    else:
        T = target
    out, rep = [], []
    for p, q, vp, vn in zip(primary, noisier, Vp, Vn):
        dd = vn - vp
        good = ok & np.isfinite(dd) & (dd > min_excess * np.nan_to_num(vp, nan=0.0))
        u2 = np.where(good, np.clip((T - vp) / np.where(good, dd, 1.0), 0.0, 1.0), 0.0)
        # smooth u² (a variance fraction), not u: local estimates fluctuate and clipping would bias u low
        u = np.sqrt(np.clip(cv2.GaussianBlur(np.nan_to_num(u2).astype(np.float32), (0, 0), smooth_px), 0.0, 1.0))
        lp, _ = _log(p)
        lq, _ = _log(q)
        dl = np.where(ok, lq - lp, 0.0).astype(np.float32)
        hp = dl - normalized_gaussian(dl, ok, hp_px, 0.05)
        z = np.where(ok, np.asarray(p, np.float32) * np.exp(u * np.nan_to_num(hp)), p).astype(np.float32)
        out.append(z)
        short = ok & np.isfinite(vn) & (vn < 0.98 * T)
        rep.append(dict(mean_u=float(np.mean(u[ok])) if ok.any() else 0.0,
                        share_cannot_reach=float(short[ok].mean()) if ok.any() else 0.0))
    return out, dict(epochs=rep, target=T)


def uniform_moon_edge(details: list[np.ndarray], moon_xy: list[tuple[float, float]], moon_radius_px: float,
                      geometry: EclipseGeometry, *, inner_rsun: float = 0.012, outer_rsun: float = 0.30,
                      step_rsun: float = 0.005, taper_rsun: float = 0.05) -> list[np.ndarray]:
    """The same rim in every frame: nothing inside ``inner_rsun`` of each frame's Moon, and each frame's mean
    profile against the distance to its Moon's edge replaced by the mean profile of all frames (tapered to
    zero at ``outer_rsun``).  The rim still moves with the Moon, as it really did; it no longer pulses."""
    R = geometry.sun_radius_px
    yy, xx = np.mgrid[0:details[0].shape[0], 0:details[0].shape[1]]
    dd = np.arange(0.0, outer_rsun, step_rsun)
    dms, profs, outs = [], [], []
    for D, (mx, my) in zip(details, moon_xy):
        dm = ((np.hypot(xx - mx, yy - my) - moon_radius_px) / R).astype(np.float32)
        D = np.where(dm < inner_rsun, np.nan, D).astype(np.float32)
        p = np.array([np.nanmedian(D[(dm >= d0) & (dm < d0 + step_rsun)]) if np.isfinite(D[(dm >= d0) & (dm < d0 + step_rsun)]).any()
                      else np.nan for d0 in dd])
        p = np.where(np.isfinite(p), p, 0.0)
        p = np.convolve(np.r_[p[:1], p, p[-1:]], [0.25, 0.5, 0.25], "same")[1:-1]
        dms.append(dm); profs.append(p); outs.append(D)
    pm = np.mean(profs, axis=0)
    res = []
    for D, dm, p in zip(outs, dms, profs):
        corr = np.interp(dm, dd + step_rsun / 2, p - pm, left=0.0, right=0.0) * np.clip((outer_rsun - dm) / taper_rsun, 0, 1)
        res.append((D - np.where(dm < outer_rsun, corr, 0.0)).astype(np.float32))
    return res


def common_noise_filter(details: list[np.ndarray], geometry: EclipseGeometry, pairs: list[tuple[int, int]], *,
                        r_range=(1.02, 3.4), step: float = 0.04, max_gain: float = 2.5, ref_rsun: float = 1.05) -> dict:
    """One Wiener factor and one contrast gain per ring for *all* frames, from pairs of epochs a few seconds
    apart (their difference is noise).  The same filter in every frame cannot make anything move."""
    rs = geometry.rsun_map()
    rr = np.arange(r_range[0], r_range[1], step)
    wien, sig_l, ref = [], [], None
    for r0 in rr:
        m = (rs >= r0) & (rs < r0 + step)
        for i, j in pairs:
            m &= np.isfinite(details[i]) & np.isfinite(details[j])
        if m.sum() < 300:
            wien.append(np.nan); sig_l.append(np.nan); continue
        nv = np.mean([np.var(details[i][m] - details[j][m]) / 2 for i, j in pairs])
        tv = np.mean([np.var((details[i][m] + details[j][m]) / 2) for i, j in pairs])
        sv = max(tv - nv / 2, 0.0)
        wien.append(sv / (sv + nv) if sv + nv > 0 else 0.0)
        sig = np.sqrt(sv)
        if ref is None and r0 >= ref_rsun:
            ref = sig
        sig_l.append(sig)
    wien = np.where(np.isfinite(wien), wien, 0.0)
    g = np.array(sig_l, float)
    g = np.clip(ref / np.where(g > 0, g, np.nan), 1.0, max_gain) if ref else np.ones_like(g)
    g = np.where(np.isfinite(g), g, max_gain)
    i0, j0 = pairs[0]
    first = (details[i0] + details[j0]) / 2
    sel = (rs > ref_rsun) & (rs < 1.6) & np.isfinite(first)
    G0 = 0.5 / float(np.nanpercentile(np.abs(first[sel]), 99.5)) if sel.any() else 1.0
    return dict(r=(rr + step / 2).tolist(), wiener=wien.tolist(), gain=g.tolist(), G0=G0,
                snr=[float(np.sqrt(w / (1 - w))) if 0 < w < 1 else (float("inf") if w >= 1 else 0.0) for w in wien])


def output_matrix(geometry: EclipseGeometry, out_size=(1320, 1044), rsun_out_px: float = 242.0,
                  rotation_deg: float = 0.0) -> np.ndarray:
    """2×3 matrix canvas → output frame: Sun at the centre, ``rsun_out_px`` per solar radius, rotated by
    ``rotation_deg`` (counter-clockwise on the display)."""
    W, H = out_size
    s = rsun_out_px / geometry.sun_radius_px
    M = cv2.getRotationMatrix2D(tuple(map(float, geometry.sun_xy)), rotation_deg, s)
    M[0, 2] += W / 2 - geometry.sun_xy[0]
    M[1, 2] += H / 2 - geometry.sun_xy[1]
    return M


def render_frames(details: list[np.ndarray], geometry: EclipseGeometry, flt: dict, *, K: float = 2.2,
                  moon_xy: list | None = None, moon_radius_px: float | None = None, out_size=(1320, 1044),
                  rsun_out_px: float = 242.0, rotation_deg: float = 0.0) -> list[np.ndarray]:
    """Frames in [0, 1]: mid-grey = no detail, ``0.5 + 0.5·tanh(K·G0·D·wiener·gain)`` with the common filter of
    :func:`common_noise_filter`, resampled to the output frame, the Moon of each epoch in black."""
    rs = geometry.rsun_map()
    prof = np.interp(rs, np.array(flt["r"]), np.array(flt["wiener"]) * np.array(flt["gain"])).astype(np.float32)
    M = output_matrix(geometry, out_size, rsun_out_px, rotation_deg)
    W, H = out_size
    yo, xo = np.mgrid[0:H, 0:W]
    s = rsun_out_px / geometry.sun_radius_px
    frames = []
    for i, D in enumerate(details):
        v = (0.5 + 0.5 * np.tanh(K * flt["G0"] * np.nan_to_num(D, nan=0.0) * prof)).astype(np.float32)
        w = cv2.warpAffine(v, M, (W, H), flags=cv2.INTER_CUBIC, borderValue=0.5)
        if moon_xy is not None and moon_radius_px:
            px, py = M @ np.array([moon_xy[i][0], moon_xy[i][1], 1.0])
            w[np.hypot(xo - px, yo - py) < moon_radius_px * s + 1.0] = 0.0
        frames.append(np.clip(w, 0, 1))
    return frames


def draw_zone_arrows(img8: np.ndarray, zones: list[dict], center_xy, *, length: float = 74, gap: float = 16,
                     width: float = 11, head: float = 30, color=(255, 255, 255)) -> np.ndarray:
    """Radial arrows that point at each zone (``x``, ``y`` in the image) from outside.  They mark a place."""
    from .annotate import draw_arrow
    cx, cy = center_xy
    for z in zones:
        u = np.array([z["x"] - cx, z["y"] - cy], float)
        L = np.hypot(*u)
        if L < 1e-6:
            continue
        u /= L
        tip = np.array([z["x"], z["y"]]) + u * gap
        draw_arrow(img8, tip + u * length, tip, color=color, width=width, head_len=head, head_width=1.1 * head)
    return img8


def two_site_change(a: list[np.ndarray], b: list[np.ndarray], geometry: EclipseGeometry, *, start=(0, 1), end=(-2, -1),
                    valid: np.ndarray | None = None, rings=((1.15, 1.5), (1.5, 2.0), (2.0, 2.6)),
                    rotations=(-12, -9, -6, -3, 3, 6, 9, 12), hp_px: float = 10.0, smooth_px: float = 22.0,
                    min_area_px: int = 900, r_min_rsun: float = 1.12, ring_step: float = 0.05) -> dict:
    """Do two independent series see the same change between their start and end epochs?

    ``a`` and ``b``: frames of the two series (display frames or details) on the *same* canvas.  For each,
    change = HP(mean(end) − mean(start)); its part proportional to the structure in every ring (fading
    contrast: the Sun sets) and a global affine deformation (refraction) are removed.  Correlation per ring,
    against a null made by rotating series b about the Sun.  Local correlation (Gaussian ``smooth_px``), with
    the threshold at the 99th percentile of the rotated control; the zones are its connected areas.  A zone
    marks a place where both see a change; it does not say whether something moved or brightened."""
    hp = lambda x: (x - cv2.GaussianBlur(x, (0, 0), hp_px)).astype(np.float32)
    mean = lambda s, idx: np.mean([s[i] for i in idx], axis=0).astype(np.float32)
    rs = geometry.rsun_map()
    H, W = rs.shape
    cx, cy = geometry.sun_xy
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
    m = np.ones((H, W), bool) if valid is None else np.asarray(valid, bool)
    for s in (a, b):
        for f in s:
            m &= np.isfinite(f)
    m &= (rs > rings[0][0]) & (rs < rings[-1][1])
    xn, yn = (X - cx) / geometry.sun_radius_px, (Y - cy) / geometry.sun_radius_px

    def change(s):
        d = hp(np.nan_to_num(mean(s, end) - mean(s, start)))
        st = hp(np.nan_to_num(mean(s, list(start) + list(end))))
        gx = cv2.Sobel(st, cv2.CV_32F, 1, 0, ksize=3) / 8
        gy = cv2.Sobel(st, cv2.CV_32F, 0, 1, ksize=3) / 8
        cols = [gx, gx * xn, gx * yn, gy, gy * xn, gy * yn]
        cols += [st * ((rs >= lo) & (rs < lo + ring_step)) for lo in np.arange(rings[0][0], rings[-1][1], ring_step)]
        A = np.stack([c[m] for c in cols], 1)
        coef, *_ = np.linalg.lstsq(A, d[m], rcond=None)
        out = np.zeros_like(d)
        out[m] = d[m] - A @ coef
        return out

    ra, rb = change(a), change(b)
    corr = lambda u, v, k: float(np.corrcoef(u[k], v[k])[0, 1])
    rot = lambda img, ang: cv2.warpAffine(img, cv2.getRotationMatrix2D((float(cx), float(cy)), ang, 1.0), (W, H))
    per_ring = []
    for lo, hi in rings:
        k = m & (rs > lo) & (rs < hi)
        v = corr(ra, rb, k)
        nul = [corr(ra, rot(rb, g), k) for g in rotations]
        sd = float(np.std(nul))
        per_ring.append(dict(r=(lo, hi), corr=v, null_mean=float(np.mean(nul)), null_sd=sd,
                             sigma=float((v - np.mean(nul)) / sd) if sd > 0 else float("nan")))
    mf = m.astype(np.float32)
    G = lambda x: cv2.GaussianBlur(x, (0, 0), smooth_px)
    w = G(mf)
    aa = G(ra * ra * mf)
    lc = np.where(w > 0.3, G(ra * rb * mf) / np.sqrt(np.maximum(aa * G(rb * rb * mf), 1e-12)), 0.0)
    rbr = rot(rb, 8.0)
    lcn = np.where(w > 0.3, G(ra * rbr * mf) / np.sqrt(np.maximum(aa * G(rbr * rbr * mf), 1e-12)), 0.0)
    inside = (w > 0.3)
    thr = float(np.percentile(lcn[inside], 99)) if inside.any() else float("nan")
    zone = ((lc > thr) & (rs > r_min_rsun)).astype(np.uint8)
    nlab, lab, st, _ = cv2.connectedComponentsWithStats(zone)
    zones = []
    for k in range(1, nlab):
        area = int(st[k, cv2.CC_STAT_AREA])
        if area < min_area_px:
            continue
        mm = lab == k
        ww = lc[mm]
        zx, zy = float((X[mm] * ww).sum() / ww.sum()), float((Y[mm] * ww).sum() / ww.sum())
        zones.append(dict(x=zx, y=zy, area=area, score=float(area * ww.mean()),
                          r_rsun=float(np.hypot(zx - cx, zy - cy) / geometry.sun_radius_px)))
    zones.sort(key=lambda z: -z["score"])
    return dict(rings=per_ring, threshold=thr, area_share=float(((lc > thr) & inside).mean() / max(inside.mean(), 1e-9)),
                control_share=float(((lcn > thr) & inside).mean() / max(inside.mean(), 1e-9)), zones=zones, local=lc)
