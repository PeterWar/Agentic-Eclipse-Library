"""Gates: checks a product must pass before anyone sees it.

A gate that never fails proves nothing.  Each gate here comes with its negative control (see the
tests): the same check run on a deliberately broken input must fail.
"""
from __future__ import annotations

import numpy as np

from .geometry import EclipseGeometry
from .polar import from_polar, to_polar

__all__ = ["nothing_outside_data", "polar_roundtrip", "summarize"]


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


def summarize(results: list[dict]) -> dict:
    return dict(passed=all(r.get("passed", False) for r in results), gates=results)
