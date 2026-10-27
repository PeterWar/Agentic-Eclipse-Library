"""Gates: checks a product must pass before anyone sees it.

A gate that never fails proves nothing.  Each gate here comes with its negative control (see the
tests): the same check run on a deliberately broken input must fail.
"""
from __future__ import annotations

import cv2
import numpy as np

from .geometry import EclipseGeometry
from .polar import from_polar, to_polar

__all__ = ["nothing_outside_data", "polar_roundtrip", "grain_uniformity", "no_concentric_bands",
           "fine_detail_fidelity", "summarize"]


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


def fine_detail_fidelity(layer_a: np.ndarray, layer_b: np.ndarray, lum_a: np.ndarray, lum_b: np.ndarray,
                         valid: np.ndarray, geometry: EclipseGeometry, *,
                         rings=((1.2, 1.3), (1.3, 1.5), (1.5, 2.0)), sigmas=(1.5, 6.0), guard_px: float = 6.0,
                         rho_min: float = 0.5, inversions_max_pct: float = 10.0, reference_rho_min: float = 0.5,
                         rotation_null_deg: float = 30.0, rotation_null_max: float = 0.1, sectors: int = 8) -> dict:
    """Real-data gate for a detail layer, proposed by Edu (@edu27) in issue #4: does the layer follow the fine detail
    of the data, with its sign?

    Needs two INDEPENDENT stacks of the same eclipse (``lum_a``, ``lum_b``: for example the frames of two pointings,
    or ramp-up against ramp-down) on one canvas, and the layer made from each (``layer_a``, ``layer_b``).
    The reference is the data's own fine detail without any filter: a band-pass of ln L (``sigmas``, normalised
    convolution). It is accredited ring by ring only if the two stacks agree (rho >= ``reference_rho_min``) and a
    rotation of ``rotation_null_deg`` about the Sun kills the agreement (|rho| <= ``rotation_null_max``); a ring that
    fails is reported as not judgeable (next to the Moon an edge bias can fake agreement).
    The layer gets the same band-pass and is compared CROSSWISE (the layer from A with the reference from B and vice
    versa, so the noise of one stack cannot agree with itself): rho with the reference, % of sign inversions where the
    reference detail is clear (|ref| > 1 sigma) and rho between the two layers in every accredited ring, and the first
    two also in its worst ``sectors``-th sector. PASS if all of that holds; ``passed`` is None when no ring is
    accredited. The guard of ``guard_px`` keeps the band-pass away from every edge of the data, the frame included.
    On 2026 data (Sony, two pointings, 1.2–2 R☉): WOW bilateral rho 0.08–0.20 with 38–46 % inverted (fails); the WOW of
    1.3.4 rho 0.77–0.84 with 1.3–2.9 % inverted, worst sector rho 0.65 and 9.2 % (passes). Fine scales only by default:
    coarse structure needs its own band (``sigmas``)."""
    from scipy import ndimage as ndi
    from .filters import normalized_gaussian
    m = np.asarray(valid, bool)
    ma = m & np.isfinite(lum_a) & (lum_a > 0); mb = m & np.isfinite(lum_b) & (lum_b > 0)
    def bp(img, k):
        k = k & np.isfinite(img)
        return (normalized_gaussian(img, k, sigmas[0], 0.25) - normalized_gaussian(img, k, sigmas[1], 0.25)).astype(np.float32)
    ref_a = bp(np.where(ma, np.log(np.where(ma, lum_a, 1.0)), np.nan).astype(np.float32), ma)
    ref_b = bp(np.where(mb, np.log(np.where(mb, lum_b, 1.0)), np.nan).astype(np.float32), mb)
    la = bp(np.asarray(layer_a, np.float32), np.isfinite(layer_a)); lb = bp(np.asarray(layer_b, np.float32), np.isfinite(layer_b))
    both = ma & mb & np.isfinite(layer_a) & np.isfinite(layer_b)
    dom = both & (ndi.distance_transform_edt(np.pad(both, 1))[1:-1, 1:-1] >= guard_px)   # the frame is an edge too
    rs = geometry.rsun_map(); pa = geometry.pa_map(); cx, cy = geometry.sun_xy
    h, w = m.shape; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); t_ = np.deg2rad(rotation_null_deg)
    xs = cx + np.cos(t_) * (xx - cx) + np.sin(t_) * (yy - cy); ys = cy - np.sin(t_) * (xx - cx) + np.cos(t_) * (yy - cy)
    ref_b_rot = ndi.map_coordinates(ref_b, [ys, xs], order=1, mode="constant", cval=np.nan); del yy, xx, xs, ys

    def rho(x, y, k):
        k = k & np.isfinite(x) & np.isfinite(y)
        if k.sum() < 100: return None
        a = x[k].astype(np.float64) - x[k].mean(); b = y[k].astype(np.float64) - y[k].mean()
        return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum()))

    def inv(layer, ref, k):
        k = k & np.isfinite(layer) & np.isfinite(ref)
        if k.sum() < 100: return None
        s = float(np.std(ref[k])); clear = k & (np.abs(ref) > s)
        return float(100 * np.mean(np.sign(layer[clear]) != np.sign(ref[clear]))) if clear.any() else None

    def cross(k):
        r_ = [rho(la, ref_b, k), rho(lb, ref_a, k)]; i_ = [inv(la, ref_b, k), inv(lb, ref_a, k)]
        if None in r_ or None in i_: return None, None
        return float(np.mean(r_)), float(np.mean(i_))

    out, verdicts = [], []
    for lo, hi in rings:
        k = dom & (rs >= lo) & (rs < hi)
        rc, rn = rho(ref_a, ref_b, k), rho(ref_a, ref_b_rot, k)
        accredited = rc is not None and rn is not None and rc >= reference_rho_min and abs(rn) <= rotation_null_max
        r_ref, inv_pct = cross(k); r_ab = rho(la, lb, k)
        worst_r, worst_i = None, None
        for s in range(sectors):
            c = (s + 0.5) * 360 / sectors
            rr, ii = cross(k & (np.abs((pa - c + 180) % 360 - 180) < 180 / sectors))
            if rr is not None:
                worst_r = rr if worst_r is None else min(worst_r, rr); worst_i = ii if worst_i is None else max(worst_i, ii)
        ok = (None not in (r_ref, inv_pct, r_ab, worst_r, worst_i) and r_ref >= rho_min and inv_pct <= inversions_max_pct
              and r_ab >= rho_min and worst_r >= rho_min and worst_i <= inversions_max_pct)
        if accredited: verdicts.append(bool(ok))
        out.append(dict(ring_rsun=(lo, hi), reference_rho=rc, reference_rotation_null=rn, accredited=bool(accredited),
                        rho_reference=r_ref, inversions_pct=inv_pct, rho_ab=r_ab, worst_sector_rho=worst_r,
                        worst_sector_inversions_pct=worst_i, passed=bool(ok) if accredited else None))
    return dict(gate="fine_detail_fidelity", passed=(all(verdicts) if verdicts else None), rings=out,
                thresholds=dict(rho_min=rho_min, inversions_max_pct=inversions_max_pct, reference_rho_min=reference_rho_min,
                                rotation_null_deg=rotation_null_deg, rotation_null_max=rotation_null_max, sigmas=list(sigmas),
                                guard_px=guard_px, sectors=sectors))


def summarize(results: list[dict]) -> dict:
    return dict(passed=all(r.get("passed", False) for r in results), gates=results)
