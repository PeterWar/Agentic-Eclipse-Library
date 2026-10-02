"""Gates: checks a product must pass before anyone sees it.

A gate that never fails proves nothing.  Each gate here comes with its negative control (see the
tests): the same check run on a deliberately broken input must fail.
"""
from __future__ import annotations

import cv2
import numpy as np

from .geometry import EclipseGeometry
from .polar import from_polar, to_polar

__all__ = ["nothing_outside_data", "polar_roundtrip", "grain_uniformity", "no_concentric_bands", "summarize"]


def nothing_outside_data(product: np.ndarray, valid: np.ndarray) -> dict:
    """PASS if the product has no finite value where there was no data (nothing invented)."""
    p = np.asarray(product)
    fin = np.isfinite(p) if p.ndim == 2 else np.isfinite(p).any(axis=2)
    bad = int((fin & ~valid.astype(bool)).sum())
    return dict(gate="nothing_outside_data", passed=bad == 0, invented_pixels=bad)


def polar_roundtrip(img: np.ndarray, geometry: EclipseGeometry, r_range, *, center="sun", tol: float = 0.01,
                    **kw) -> dict:
    """to_polar → from_polar must return the image (relative rms error ≤ ``tol`` inside the annulus,
    away from its edges).  Needs a finely sampled grid (defaults oversample the arc)."""
    P = to_polar(img, geometry, center=center, r_range=r_range, antialias=False, **kw)
    back = from_polar(P, img.shape[:2])
    r = geometry.radius_map(center)
    sel = (r > r_range[0] + 3) & (r < r_range[1] - 3) & np.isfinite(back) & np.isfinite(img)
    err = back[sel] - img[sel]
    rel = float(np.sqrt(np.mean(err ** 2)) / max(float(np.sqrt(np.mean(img[sel] ** 2))), 1e-30))
    return dict(gate="polar_roundtrip", passed=rel <= tol, rel_rms=rel, n=int(sel.sum()))


def grain_uniformity(frames: list[np.ndarray], geometry: EclipseGeometry, *, valid: np.ndarray | None = None,
                     r_range=(1.1, 2.7), step: float = 0.1, fine_px: float = 1.5, tol: float = 1.10) -> dict:
    """Animation frames: the grain (spread of what is finer than ``fine_px``) per ring in every frame.  PASS if,
    at every ring, the grainiest frame is at most ``tol`` times the cleanest.  A grain that changes from one
    frame to the next at some radius is seen as a wave.  ``geometry`` is the frames' own (output) geometry."""
    rs = geometry.rsun_map()
    step = max(step, 10.0 / geometry.sun_radius_px)      # rings at least 10 px wide: enough pixels per estimate
    rr = np.arange(r_range[0], r_range[1] - 1e-9, step)
    tab = []
    for f in frames:
        f = np.asarray(f, np.float32)
        m = np.isfinite(f) if valid is None else (np.asarray(valid, bool) & np.isfinite(f))
        fine = f - cv2.GaussianBlur(np.nan_to_num(f), (0, 0), fine_px)
        tab.append([float(np.std(fine[m & (rs >= r0) & (rs < r0 + step)])) if (m & (rs >= r0) & (rs < r0 + step)).sum() > 200
                    else np.nan for r0 in rr])
    tab = np.array(tab)
    worst = np.nanmax(tab, axis=0) / np.nanmin(tab, axis=0)
    ok = np.isfinite(worst)
    return dict(gate="grain_uniformity", passed=bool(ok.any() and np.all(worst[ok] <= tol)), tol=tol,
                worst_ratio=float(np.nanmax(worst)), r=[float(x) for x in rr + step / 2],
                max_over_min=[float(x) for x in worst])


def no_concentric_bands(frames: list[np.ndarray], geometry: EclipseGeometry, *, valid: np.ndarray | None = None,
                        r_range=(1.2, 2.6), step: float = 0.01, tol_sigma: float = 0.35) -> dict:
    """Animation frames: in every frame-to-frame difference, the mean of each thin ring (what unrolled around
    the Sun is a row) over the spread of the difference.  PASS if no ring exceeds ``tol_sigma``: a ring that
    appears and disappears is a wave.  (A wave of grain is caught by :func:`grain_uniformity`.)"""
    rs = geometry.rsun_map()
    step = max(step, 2.0 / geometry.sun_radius_px)       # rings at least 2 px wide
    nb = int(np.ceil((r_range[1] - r_range[0]) / step))
    worst, where = 0.0, None
    per_pair = []
    for i in range(len(frames) - 1):
        d = np.asarray(frames[i + 1], np.float32) - np.asarray(frames[i], np.float32)
        m = np.isfinite(d) & (rs >= r_range[0]) & (rs < r_range[1])
        if valid is not None:
            m &= np.asarray(valid, bool)
        s = float(np.std(d[m])) if m.any() else 0.0
        idx = ((rs[m] - r_range[0]) / step).astype(int)
        sm = np.bincount(idx, d[m], minlength=nb)
        n = np.bincount(idx, minlength=nb)
        prof = np.where(n > 100, sm / np.maximum(n, 1), 0.0) / max(s, 1e-12)
        k = int(np.argmax(np.abs(prof)))
        per_pair.append(dict(pair=(i, i + 1), max_sigma=float(abs(prof[k])), r=float(r_range[0] + (k + 0.5) * step)))
        if abs(prof[k]) > worst:
            worst, where = float(abs(prof[k])), per_pair[-1]["r"]
    return dict(gate="no_concentric_bands", passed=worst <= tol_sigma, tol_sigma=tol_sigma, worst_sigma=worst,
                worst_r=where, pairs=per_pair)


def summarize(results: list[dict]) -> dict:
    return dict(passed=all(r.get("passed", False) for r in results), gates=results)
