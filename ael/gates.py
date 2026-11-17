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
           "fine_detail_fidelity", "gramophone", "inner_limit", "inner_limit_between", "inner_limit_selfcheck", "false_hole",
           "false_hole_regression", "zones_against_truth", "summarize"]


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
    """Real-data gate for a detail layer, proposed by Eduardo Piñas (@edu27) in issue #4: does the layer follow the fine detail
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


# ------------------------------------------------------------------------------------------------
# Gate D: gramophone grooves (fine concentric rings in a layer)
# ------------------------------------------------------------------------------------------------
_D_ZONES = ((1.16, 1.5), (1.5, 3.0), (3.0, 5.0), (5.0, 8.0), (8.0, 12.0))
_D_WINDOWS = {False: (("fine", 31), ("broad", 101)), True: (("fine", 67), ("broad", 217))}
_D_FAIL, _D_WARN, _D_SECTORS = 0.10, 0.05, 12


def _sector_profiles(x, valid, cx, cy, sectors=_D_SECTORS, chunk=512):
    h, w = x.shape; nr = int(np.ceil(np.hypot(max(cx, w - cx), max(cy, h - cy)))) + 2
    n = np.zeros(sectors * nr); s1 = np.zeros(sectors * nr); s2 = np.zeros(sectors * nr); xs = (np.arange(w) - cx)[None, :]
    for y0 in range(0, h, chunk):
        y1 = min(h, y0 + chunk); dy = (np.arange(y0, y1) - cy)[:, None]; blk = x[y0:y1]
        ok = valid[y0:y1] & np.isfinite(blk)
        if not ok.any():
            continue
        r = np.hypot(xs, dy)[ok]; th = np.arctan2(np.broadcast_to(dy, ok.shape)[ok], np.broadcast_to(xs, ok.shape)[ok])
        idx = (((th + np.pi) / (2 * np.pi) * sectors).astype(np.int64) % sectors) * nr + r.astype(np.int64)
        v = blk[ok].astype(np.float64)
        n += np.bincount(idx, minlength=sectors * nr); s1 += np.bincount(idx, v, sectors * nr); s2 += np.bincount(idx, v * v, sectors * nr)
    return n.reshape(sectors, nr), s1.reshape(sectors, nr), s2.reshape(sectors, nr)


def _detrend_mean(p, w):
    from scipy.ndimage import uniform_filter1d
    ok = np.isfinite(p); num = uniform_filter1d(np.where(ok, p, 0.0), w, mode="nearest"); den = uniform_filter1d(ok.astype(float), w, mode="nearest")
    return np.where(ok & (den > 0.8), p - num / np.maximum(den, 1e-12), np.nan)


def _detrend_parabola(p, w):
    from scipy.signal import savgol_filter
    out = np.full(p.shape, np.nan); ok = np.isfinite(p); i = 0; n = len(p)
    while i < n:
        if not ok[i]:
            i += 1; continue
        j = i
        while j < n and ok[j]:
            j += 1
        if j - i >= w:
            out[i:j] = p[i:j] - savgol_filter(p[i:j], w, 2, mode="interp")
        i = j
    return out


def _ring_coherence(n, s1, s2, rsun_px, image, nmin=20, pairs_min=100):
    def stats(n_, s1_, s2_, least):
        with np.errstate(invalid="ignore", divide="ignore"):
            mu = np.where(n_ >= least, s1_ / np.maximum(n_, 1), np.nan)
            var = np.where(n_ >= least, s2_ / np.maximum(n_, 1) - mu * mu, np.nan)
        return mu, np.log(np.sqrt(np.maximum(var, 1e-30)))
    S, nr = n.shape; mu_s, lg_s = stats(n, s1, s2, nmin); mu_t, lg_t = stats(n.sum(0), s1.sum(0), s2.sum(0), nmin * S)
    detrend = _detrend_parabola if image else _detrend_mean
    rr = np.arange(nr) + 0.5; out = {}
    for a, b in _D_ZONES:
        z = (rr >= a * rsun_px) & (rr < b * rsun_px)
        for label, w in _D_WINDOWS[image]:
            for name, ps, pt in (("level", mu_s, mu_t), ("grain", lg_s, lg_t)):
                d_s = np.stack([detrend(ps[i], w) for i in range(S)])[:, z]; d_t = detrend(pt, w)[z]; cors = []
                for i in range(S):
                    for j in range(i + 1, S):
                        k = np.isfinite(d_s[i]) & np.isfinite(d_s[j])
                        if k.sum() >= pairs_min and d_s[i][k].std() > 0 and d_s[j][k].std() > 0:
                            cors.append(float(np.corrcoef(d_s[i][k], d_s[j][k])[0, 1]))
                kt = np.isfinite(d_t)
                out[f"{a}-{b}|{label}|{name}"] = dict(coherence=(float(np.mean(cors)) if len(cors) >= 3 else None),
                                                      sector_pairs=len(cors), window_px=w,
                                                      amplitude=(float(d_t[kt].std()) if kt.sum() >= pairs_min else None))
    return out


def _gramophone_measure(x, valid, centre, rsun_px, image, extra_centres=()):
    cx, cy = centre
    if image:
        x = np.log(np.maximum(np.asarray(x, np.float32), 1e-4)).astype(np.float32)
    res = {"centre": _ring_coherence(*_sector_profiles(x, valid, cx, cy), rsun_px, image)}
    nulls = [_ring_coherence(*_sector_profiles(x, valid, cx + dx * rsun_px, cy + dy * rsun_px), rsun_px, image)
             for dx, dy in ((0.6, -0.45), (-0.6, 0.45), (0.45, 0.6), (-0.45, -0.6))]
    res["null"] = {}
    for k in res["centre"]:
        v = [nl[k]["coherence"] for nl in nulls if nl[k]["coherence"] is not None]
        res["null"][k] = dict(coherence=(float(np.mean(v)) if v else None), spread=(float(np.std(v)) if len(v) >= 2 else None))
    for i, (ex, ey) in enumerate(extra_centres):
        res[f"centre_extra_{i}"] = _ring_coherence(*_sector_profiles(x, valid, ex, ey), rsun_px, image)
    return res


def gramophone(layer: np.ndarray, valid: np.ndarray | None, geometry: EclipseGeometry, *, control: np.ndarray | None = None,
               image: bool = False, extra_centres=()) -> dict:
    """Gate D, "gramophone grooves" (since 1.5.0): fine concentric rings around the Sun in a layer, of level (the mean
    of each 1 px annulus goes up and down from one radius to the next) or of grain (its spread does).

    The layer is cut into twelve sectors. In each, the profile along the radius without its trend: the *fine* rings
    (running mean of 31 px) and the *broad* ones (101 px). The **coherence** is the mean correlation between the
    profiles of the 66 pairs of sectors: noise and the corona (which is radial) do not agree from one sector to the
    next (≈ 0); a concentric ring does (up to 1). The **null** is the same measure about four centres 0.75 R☉ away
    from the Sun: a ring of the Sun is wiped out there and noise gives the same. No model is needed.

    ``image=True`` for a layer that carries the brightness profile of the corona (a display base, a finished image):
    its logarithm is measured and the trend is a parabola (Savitzky–Golay of 67 and 217 px).
    ``control``: the same layer made the plain way (same recipe, without the new step); then a failure also needs the
    coherence to exceed the control's, so the gate finds the rings the new step adds and not those the data carry.
    ``extra_centres``: other centres rings may have (a flat with a ripple is centred on the sensor).

    FAIL: in some zone (1.16–1.5, 1.5–3, 3–5, 5–8, 8–12 R☉) the coherence of the fine rings exceeds the null's by more
    than 0.10. WARN above 0.05, and for broad rings. ``passed`` is ``None`` when no zone holds enough radii to judge.
    Calibrated on the author's 2026 image (440 px per solar radius): layers a person saw as grooved read 0.76–0.96,
    clean ones about 0; injected rings of 1e-3 (level) or 1 % (grain) in a smooth layer fail. The windows are in
    pixels: rings are a matter of sampling. Where they are born when there are some: a yardstick (level or spread per
    annulus) measured on a noisy layer and applied to a clean one prints the noise of its own estimate as rings
    (:func:`ael.filterbank.frozen_display`). Cure them there, never on the layer.

    A filter with **local sectors** (the local RHEF) can draw arcs that differ from sector to sector; this gate compares
    sectors with each other and does not see them."""
    x = np.asarray(layer, np.float32)
    if x.ndim != 2 or x.shape != tuple(geometry.shape):
        raise ValueError("layer must be a 2-D array on the geometry's canvas")
    m = np.isfinite(x) if valid is None else (np.asarray(valid, bool) & np.isfinite(x))
    meas = _gramophone_measure(x, m, geometry.sun_xy, geometry.sun_radius_px, image, extra_centres)
    mc = None
    if control is not None:
        c = np.asarray(control, np.float32)
        mc = _gramophone_measure(c, (np.isfinite(c) if valid is None else (np.asarray(valid, bool) & np.isfinite(c))),
                                 geometry.sun_xy, geometry.sun_radius_px, image, extra_centres)
    fail, warn, judged = [], [], 0
    for key in [k for k in meas if k.startswith("centre")]:
        for k, v in meas[key].items():
            c, c0 = v["coherence"], meas["null"][k]["coherence"]
            if c is None or c0 is None:
                continue
            judged += 1
            cc = mc[key][k]["coherence"] if (mc is not None and key in mc and mc[key][k]["coherence"] is not None) else None
            excess = c - c0; over_control = (c - cc) if cc is not None else None
            row = dict(where=key, measure=k, coherence=round(c, 3), null=round(c0, 3)) | ({"control": round(cc, 3)} if cc is not None else {})
            if "|fine|" in k and excess > _D_FAIL and (over_control is None or over_control > _D_FAIL):
                fail.append(row)
            elif excess > _D_WARN and (over_control is None or over_control > _D_WARN):
                warn.append(row)
    verdict = "NOT JUDGED" if not judged else "FAIL" if fail else "WARN" if warn else "PASS"
    return dict(gate="gramophone", passed=None if not judged else not fail, verdict=verdict, failures=fail, warnings=warn,
                kind="image" if image else "detail", measures_judged=judged, fail_above=_D_FAIL, warn_above=_D_WARN,
                measure=meas, control=mc)


# ------------------------------------------------------------------------------------------------
# Gate L: the inner limit (every layer starts where the one map says, and none carries detail inside the core)
# ------------------------------------------------------------------------------------------------
_L_DMAX, _L_SECTORS, _L_PLATEAU = 40, 12, (16, 40)
_L1_ABS, _L1_ALL, _L1_SECTOR, _L2_PX, _L2_MEDIAN, _L2_SECTORS, _L3_PX, _L_STREAK = 0.3, 0.10, 0.20, 4.0, 2.0, 10, 4.0, 5.0


def _inner_limit_frame(core, valid, geometry):
    if geometry.moon_xy is None or geometry.moon_radius_px is None:
        raise ValueError("the inner-limit gate needs the Moon in the geometry")
    H, W = core.shape; cx, cy, r = geometry.moon_xy[0], geometry.moon_xy[1], geometry.moon_radius_px
    half = int(r + 260); x0, y0 = max(0, int(cx - half)), max(0, int(cy - half)); x1, y1 = min(W, int(cx - half) + 2 * half), min(H, int(cy - half) + 2 * half)
    sl = (slice(y0, y1), slice(x0, x1)); w = core[sl].astype(np.float32)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32); dm = np.hypot(xx - cx, yy - cy) - r
    out = (w >= .999) | (dm < 0)
    if valid is not None:
        out |= ~np.asarray(valid, bool)[sl] & (dm < 200)          # the void next to the limb counts as the limit too
    d = cv2.distanceTransform((~out).astype(np.uint8), cv2.DIST_L2, 5)
    inside = (w >= .999) & (dm >= 0)
    sec = (np.degrees(np.arctan2(yy - cy, xx - cx)) % 360 // (360 / _L_SECTORS)).astype(int)
    zone = (dm >= 0) & (d <= _L_DMAX) & (dm < 200)
    db = np.clip(np.floor(d).astype(int), 0, _L_DMAX)
    return dict(sl=sl, w=w, d=d, db=db, inside=inside, sec=sec, zone=zone, visible=~out, e50=[1.0] * _L_SECTORS)


def _inner_limit_measure(g, a, z):
    g = np.asarray(g, np.float32); a = np.nan_to_num(np.asarray(a, np.float32), nan=0.0)
    seen = (np.isfinite(g) & (a > 0)).astype(np.float32); g = np.nan_to_num(g, nan=0.5)
    # the detail one sees: the layer minus its own local mean OVER THE PIXELS IT HAS (a plain blur would read the step
    # between the layer's level and the void beside it as detail, and pass a layer that is flat at the limit)
    det = (g - cv2.GaussianBlur(g * seen, (0, 0), 8.) / np.maximum(cv2.GaussianBlur(seen, (0, 0), 8.), 1e-6)) * a
    # INSIDE the core the detail is that of the fine band (layer − a 2 px Gaussian), measured with the pixels of the
    # core only (a Gaussian normalised over the core): a plain 8 px Gaussian mixes in the texture outside, and the
    # level of a Multiply layer, smooth but sloped, would count as detail (the core is a few pixels wide).
    D = z["inside"].astype(np.float32)
    det_in = (g - cv2.GaussianBlur(g * D, (0, 0), 2.) / np.maximum(cv2.GaussianBlur(D, (0, 0), 2.), 1e-6)) * a
    fine = (g - cv2.GaussianBlur(g, (0, 0), 2.)) * a
    d50, in_s, alt_s = [], [], []
    for s in range(_L_SECTORS):
        m = z["zone"] & (z["sec"] == s); mo = m & ~z["inside"]
        prof = np.sqrt(np.bincount(z["db"][mo], weights=det[mo].astype(float) ** 2, minlength=_L_DMAX + 1)
                       / np.maximum(np.bincount(z["db"][mo], minlength=_L_DMAX + 1), 1))
        alt = float(np.median(prof[_L_PLATEAU[0]:_L_PLATEAU[1] + 1])); alt_s.append(alt)
        ps = np.convolve(prof, np.ones(3) / 3, mode="same"); ps[0] = prof[0]
        i = np.flatnonzero(ps >= .5 * alt)
        d50.append(float(max(i[0], 1)) if len(i) and alt * 255 > _L1_ABS else float("nan"))   # a plateau nobody sees is not judged
        md = m & z["inside"]; mf = mo & (z["db"] >= _L_PLATEAU[0])
        altf = float(np.sqrt(np.mean(fine[mf] ** 2))) if mf.sum() > 20 else 0.0
        in_s.append(float(np.sqrt(np.mean(det_in[md] ** 2)) / altf) if md.sum() > 20 and altf > 0 else 0.0)
    md = z["zone"] & z["inside"]; mf = z["zone"] & ~z["inside"] & (z["db"] >= _L_PLATEAU[0])
    altf_all = float(np.sqrt(np.mean(fine[mf] ** 2))) if mf.any() else 0.0
    in_abs = float(np.sqrt(np.mean(det_in[md] ** 2))) if md.any() else 0.0
    in_all = in_abs / altf_all if altf_all > 0 else 0.0
    vis = z["zone"] & ~z["inside"] & (a > .5)
    med = np.full(_L_DMAX + 1, np.nan)
    for k in range(_L_DMAX + 1):
        v = g[vis & (z["db"] == k)]
        if len(v) > 200:
            med[k] = np.median(v)
    x = np.arange(_L_DMAX + 1); f = np.isfinite(med) & (x >= 12); streak = None
    if f.sum() > 8:
        p = np.polyfit(x[f], med[f], 1); res = med - np.polyval(p, x)
        sd = 1.4826 * np.median(np.abs(res[f] - np.median(res[f]))) + 1e-6; first = np.isfinite(res) & (x < 12)
        if first.any():
            streak = dict(largest_residual_levels_8bit=float(np.nanmax(np.abs(res[first])) * 255),
                          at_px=int(x[first][np.nanargmax(np.abs(res[first]))]),
                          times_the_spread=float(np.nanmax(np.abs(res[first])) / sd), spread_levels_8bit=float(sd * 255))
    return dict(d50_per_sector=d50, detail_inside_core_levels_8bit=in_abs * 255, detail_inside_core_over_plateau=in_all,
                detail_inside_worst_sector=float(max(in_s)), plateau_levels_8bit=float(np.median(alt_s)) * 255,
                streak_along_the_limb=streak)


def _inner_limit_verdict(m, z):
    err = np.array(m["d50_per_sector"]) - np.array(z["e50"]); good = np.isfinite(err); fail, warn = [], []
    if ((m["detail_inside_core_over_plateau"] > _L1_ALL or m["detail_inside_worst_sector"] > _L1_SECTOR)
            and m["detail_inside_core_levels_8bit"] > _L1_ABS):
        fail.append(f"L1: detail inside the core ({m['detail_inside_core_over_plateau']:.2f} of the plateau outside; "
                    f"worst sector {m['detail_inside_worst_sector']:.2f})")
    within = int((np.abs(err[good]) <= _L2_PX).sum()); med = float(np.median(np.abs(err[good]))) if good.any() else float("nan")
    if good.sum() >= _L2_SECTORS and (within < _L2_SECTORS or not med <= _L2_MEDIAN):
        fail.append(f"L2: starts {np.nanmedian(err):+.1f} px (median) from where the map says; {within} of {_L_SECTORS} "
                    f"sectors within ±{_L2_PX:g} px")
    r = m["streak_along_the_limb"]
    if r and r["times_the_spread"] > _L_STREAK:
        warn.append(f"a streak follows the limb: {r['largest_residual_levels_8bit']:.1f} levels at {r['at_px']} px "
                    f"({r['times_the_spread']:.1f} times the spread)")
    m["d50_error_per_sector_px"] = [None if not np.isfinite(e) else round(float(e), 1) for e in err]
    m["d50_error_median_px"] = med; m["sectors_judged"] = int(good.sum())
    if good.sum() < _L2_SECTORS:
        warn.append(f"only {int(good.sum())} of {_L_SECTORS} sectors hold enough layer to say where it starts (L2 not judged)")
    return ("FAIL" if fail else "WARN" if warn else "PASS"), fail, warn


def inner_limit(layers: dict, core: np.ndarray, geometry: EclipseGeometry, *, valid: np.ndarray | None = None) -> dict:
    """Gate L, the inner limit (since 1.5.0): every filter layer starts where the one map says
    (:func:`ael.zones.inner_zones`), all at the same place, and none carries detail inside the core.

    ``layers``: ``{name: (layer, alpha)}``, display layers in [0, 1] with the alpha they will have in the file (an
    Overlay layer is transparent in the core; a Multiply layer carries only its level there). ``core``: the boolean
    core of the map. ``valid``: the observed pixels (the void next to the limb then counts as part of the limit).

    With *d* the distance of each pixel to the core (or the Moon), and in each of twelve 30° sectors around the Moon:

    * **L1, nothing inside.** Inside the core the fine detail one would see (layer − its 2 px Gaussian, × alpha) is at
      most 10 % of the fine detail outside (*d* = 16–40 px) over all sectors and 20 % in any one — or below 0.3 levels
      of 255, which nobody sees.
    * **L2, it starts where the map says.** The first *d* at which the detail (layer − its 8 px mean over the pixels
      the layer has, × alpha) reaches half its plateau (*d* = 16–40 px) is within 4 px of the first pixel outside the
      core in at least 10 of the 12 sectors, median ≤ 2 px. A sector whose plateau is below 0.3 levels of 255 is not
      judged.
    * **L3, all alike** (two layers or more): per sector, the starts of the layers differ by at most 4 px (10 of 12).
    * WARN, not a failure (it is not calibrated): **a streak that follows the limb** — the median of the layer along
      the whole contour against *d*, minus its straight line over 12–40 px, exceeds 5 spreads in the first 12 px.
      Look at the layer there before using it.

    This gate cannot tell a core that is *too large*: a map with a safety margin passes it whole. That is what
    :func:`zones_against_truth` is for. Thresholds were set on one image; do not move them to pass a layer."""
    core = np.asarray(core, bool)
    z = _inner_limit_frame(core, valid, geometry)
    out = dict(gate="inner_limit", layers={}); worst = "PASS"; starts = []
    for name, (g, a) in layers.items():
        m = _inner_limit_measure(np.asarray(g, np.float32)[z["sl"]], np.asarray(a, np.float32)[z["sl"]], z)
        verdict, fail, warn = _inner_limit_verdict(m, z); starts.append(m["d50_per_sector"])
        out["layers"][name] = dict(verdict=verdict, failures=fail, warnings=warn, measure=m)
        worst = "FAIL" if "FAIL" in (verdict, worst) else "WARN" if "WARN" in (verdict, worst) else "PASS"
    if len(starts) > 1:
        out["between_layers"] = inner_limit_between(list(zip(out["layers"], starts)))
        if out["between_layers"]["verdict"] == "FAIL":
            worst = "FAIL"
    out["verdict"] = worst; out["passed"] = worst != "FAIL"
    return out


def inner_limit_between(starts: list) -> dict:
    """L3 of gate L: ``[(name, start per sector), …]`` of two layers or more → do they all start at the same place?"""
    D = np.array([s for _, s in starts], np.float64)
    spread = np.max(D, 0) - np.min(D, 0)             # a sector where some layer has no start is not judged (NaN)
    judged = np.isfinite(spread); ok = int((spread[judged] <= _L3_PX).sum())
    verdict = "PASS" if (ok >= _L2_SECTORS or judged.sum() < _L2_SECTORS) else "FAIL"
    return dict(layers=[n for n, _ in starts], verdict=verdict, sectors_within_tolerance=ok, sectors_judged=int(judged.sum()),
                start_spread_per_sector_px=[None if not np.isfinite(x) else round(float(x), 1) for x in spread])


def inner_limit_selfcheck(core: np.ndarray, geometry: EclipseGeometry, *, valid: np.ndarray | None = None, seed: int = 11) -> dict:
    """Five synthetic layers on the given map, three good and two bad: the gate must pass the first and fail the
    others. Run it on your own map before believing a PASS (a gate that never fails proves nothing)."""
    z = _inner_limit_frame(np.asarray(core, bool), valid, geometry)
    rng = np.random.default_rng(seed); sh = z["w"].shape
    tex = np.clip(.5 + .12 * cv2.GaussianBlur(rng.standard_normal(sh).astype(np.float32), (0, 0), 2.) / .14, 0, 1)
    w = z["w"]; vis = z["visible"].astype(np.float32) + w * 0; seen = np.clip(vis + w, 0, 1); level = np.full(sh, .5, np.float32)
    late = np.clip((z["d"] - 15) / 6, 0, 1)
    yy, xx = np.mgrid[0:sh[0], 0:sh[1]].astype(np.float32); slope = np.clip(.5 + .25 * np.sin(xx / 25.) * np.cos(yy / 31.), 0, 1)
    cases = dict(good_overlay=(tex, vis, "PASS"), good_multiply=(w * level + (1 - w) * tex, seen, "PASS"),
                 good_multiply_sloped_level=(w * slope + (1 - w) * tex, seen, "PASS"),
                 detail_inside_the_core=(tex, seen, "FAIL"), starts_15_px_late=(tex, vis * late, "FAIL"))
    res = {}; allok = True
    for name, (g, a, expected) in cases.items():
        m = _inner_limit_measure(g.astype(np.float32), a.astype(np.float32), z); verdict, fail, _ = _inner_limit_verdict(m, z)
        ok = (verdict == "FAIL") == (expected == "FAIL"); allok &= ok
        res[name] = dict(expected=expected, verdict=verdict, failures=fail, correct=bool(ok))
    return dict(gate="inner_limit_selfcheck", passed=bool(allok), cases=res)


# ------------------------------------------------------------------------------------------------
# Gate F: the false hole (what an operator does next to an edge, with the truth known)
# ------------------------------------------------------------------------------------------------
_F_BANDS = ((1, 3), (3, 6), (6, 12), (12, 20), (20, 36), (36, 70), (70, 110))
_F_LIMIT = 0.5


def false_hole(operator, luminance: np.ndarray, valid: np.ndarray, geometry: EclipseGeometry, *, grow_px: int = 80,
               hole: str = "grown", shift_px: int = 700) -> dict:
    """Gate F, the false hole (since 1.5.0): what a filter *operator* does next to an edge of the data, with the truth
    known. It does not look at a layer: it tests the operator.

    Bands and streaks parallel to the limb in a filter layer cannot be told from corona by measuring the image. So,
    on the corona further out, where all the data are there, pretend the hole (the Moon and the protected core) is
    ``grow_px`` larger, and run ``operator(luminance, valid) -> detail`` twice: with the real hole (the truth) and with
    the false one. Outside the false hole every difference between the two outputs is an effect of the edge, not
    corona. Nothing is invented and nothing enters a product: it is a measurement.

    Per band of distance to the false hole: the rms of the difference over the rms of the fine detail of the truth
    (a 12 px high-pass, measured at 60–160 px), and the part of it that runs parallel to the edge (mean along 10° of
    arc). ``absolute`` is PASS if the difference is at most 0.5 in every band from 3 px on — an inventory of the debt
    more than a bar: on the 2026 image, with the hole grown by 80 px, only the local part of the MGN with a fit of
    order 2 passed it, and nearly every layer of the library fails it. Read the bands, not the word. For a cure, what counts is
    :func:`false_hole_regression` (the new operator against the one it replaces). ``detail_over_spread`` (fine detail
    over the robust spread of the output) turns a difference into units of the layer's range, which is what one sees
    in a smooth layer (NRGF, FNRGF, RHEF).

    ``hole='shifted'``: the real hole, with its irregular edge, moved ``shift_px`` up onto clean corona; only its left
    and right flanks more than 250 px from the real hole are judged. It sees what the smooth grown edge cannot (a cure
    that passed with the grown hole drew rows of dots along the real, irregular one). For operators with statistics per
    annulus around the Sun (NRGF, FNRGF, RHEF, radial profiles) the shifted hole is not the Moon's geometry: use the
    grown one.

    Limits: the "truth" is that of ``grow_px`` further out (at 80 px, scales above 64 px still feel the real hole:
    repeat with 160 and 240); this gate measures the sensitivity to the hole, not that the corona is kept — compare
    the new layer with the old one away from every edge for that. Work on a crop a few solar radii wide: the operator
    runs twice."""
    from scipy import ndimage as ndi
    if hole not in ("grown", "shifted"):
        raise ValueError("hole must be 'grown' or 'shifted'")
    if geometry.moon_xy is None or geometry.moon_radius_px is None:
        raise ValueError("the false-hole gate needs the Moon in the geometry")
    L = np.asarray(luminance, np.float32); m = np.asarray(valid, bool) & np.isfinite(L)
    H, W = L.shape; mx, my = geometry.moon_xy
    dmoon = geometry.radius_map("moon")
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    th = (np.degrees(np.arctan2(yy - my, xx - mx)) + 360) % 360
    real = ~m & (dmoon < geometry.moon_radius_px + 200)
    if not real.any():
        raise ValueError("no hole in the data around the Moon: the false hole needs the real one to grow or to move")
    dist = ndi.distance_transform_edt(~real).astype(np.float32)
    judge = np.ones(m.shape, bool)
    if hole == "grown":
        mf = m & (dist > grow_px); rho = np.where(mf, dist - grow_px, 0).astype(np.float32)
    else:
        if not 0 < shift_px < H:
            raise ValueError("shift_px must be inside the canvas")
        fake = np.zeros_like(real); fake[:H - shift_px] = real[shift_px:]
        mf = m & ~fake; rho = np.where(mf, ndi.distance_transform_edt(~fake), 0).astype(np.float32)
        th = (np.degrees(np.arctan2(yy - (my - shift_px), xx - mx)) + 360) % 360
        edge = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy))
        judge = (dist > 250) & (np.abs(np.sin(np.radians(th))) < np.sin(np.radians(50.))) & (edge > 150)
    del yy, xx
    truth = np.asarray(operator(L, m), np.float32); test = np.asarray(operator(L, mf), np.float32)
    ok = mf & judge & np.isfinite(truth) & np.isfinite(test)
    d = np.where(ok, test - truth, 0); t = np.where(ok, truth, 0)
    okf = ok.astype(np.float32)
    hp = t - cv2.GaussianBlur(t, (0, 0), 12) / np.maximum(cv2.GaussianBlur(okf, (0, 0), 12), 1e-6)
    z = ok & (rho > 60) & (rho < 160)
    if z.sum() < 1000:
        raise ValueError("fewer than 1000 judged pixels 60–160 px from the false hole: use a larger crop or a smaller grow_px")
    ref = float(np.sqrt(np.mean(hp[z] ** 2))); spread = float(1.4826 * np.median(np.abs(truth[z] - np.median(truth[z]))))
    nt = 720; it = (th / 360 * nt).astype(np.int64) % nt; prof = []
    for r in range(1, _F_BANDS[-1][1]):
        k = ok & (rho >= r) & (rho < r + 1)
        if k.sum() < 200:
            prof.append((r, None, None, int(k.sum()))); continue
        num = np.bincount(it[k], weights=d[k].astype(np.float64), minlength=nt); den = np.bincount(it[k], minlength=nt).astype(np.float64)
        arc = ndi.uniform_filter1d(num, 20, mode="wrap") / np.maximum(ndi.uniform_filter1d(den, 20, mode="wrap"), 1e-9)
        prof.append((r, float(np.sqrt(np.mean(d[k] ** 2))) / max(ref, 1e-30), float(np.sqrt(np.mean(arc[den > 0] ** 2))) / max(ref, 1e-30), int(k.sum())))
    bands = {}
    for lo, hi in _F_BANDS:
        x = [p for p in prof if lo <= p[0] < hi and p[1] is not None]; npx = int(sum(p[3] for p in prof if lo <= p[0] < hi))
        bands[f"{lo}-{hi}"] = None if not x else dict(difference=round(float(np.mean([p[1] for p in x])), 3),
                                                      parallel=round(float(np.mean([p[2] for p in x])), 3), px=npx)
    judged = [k for (lo, hi), k in zip(_F_BANDS, bands) if lo >= 3 and bands[k] is not None]
    empty = [k for (lo, hi), k in zip(_F_BANDS, bands) if lo >= 3 and bands[k] is None]
    fail = [f"{k} px: {bands[k]['difference']:.2f}" for k in judged if bands[k]["difference"] > _F_LIMIT] + [f"{k} px: no output next to the edge" for k in empty]
    return dict(gate="false_hole", hole=hole, grow_px=grow_px if hole == "grown" else None, shift_px=shift_px if hole == "shifted" else None,
                absolute="FAIL" if fail else "PASS", passed=not fail, failures=fail, bands=bands, limit=_F_LIMIT, judged_from_px=3,
                detail_rms=ref, layer_spread=spread, detail_over_spread=round(ref / max(spread, 1e-30), 3))


def false_hole_regression(new: dict, old: dict) -> dict:
    """A cure against what it replaces, with the SAME yardstick (two results of :func:`false_hole` on the same data
    and the same hole): FAIL if in any band from 3 px on the new operator is worse than the old one by more than 10 %
    and 0.03 — its difference put over the *old* operator's detail, so that a candidate that inflates its own detail
    is not favoured — or if it gives output on fewer pixels. A new or changed operator that fails this does not go
    into a product. An improvement that does not yet pass the absolute verdict does, and that is said."""
    worse = []
    for (lo, _), k in zip(_F_BANDS, new["bands"]):
        if lo < 3:
            continue
        x, y = new["bands"][k], old["bands"][k]
        if x is None and y is not None:
            worse.append(f"{k} px: the new operator gives no output there"); continue
        if x is None or y is None:
            continue
        xd = x["difference"] * new["detail_rms"] / max(old["detail_rms"], 1e-30)
        if x["px"] < 0.999 * y["px"]:
            worse.append(f"{k} px: the new operator loses coverage ({y['px']} → {x['px']} px)")
        if xd > 1.1 * y["difference"] and xd > y["difference"] + 0.03:
            worse.append(f"{k} px: {y['difference']:.2f} → {xd:.2f} (over the old operator's detail)")
    return dict(gate="false_hole_regression", passed=not worse, regression="FAIL" if worse else "PASS", worse=worse)


# ------------------------------------------------------------------------------------------------
# The map of the inner limit against a scene with the truth known (too little AND too much protection)
# ------------------------------------------------------------------------------------------------
def zones_against_truth(core: np.ndarray, truth: dict, *, min_core: float = 0.95, min_corona: float = 0.995,
                        min_pocket: float = 0.95, min_rim: float = 0.90, min_beads: float = 0.90) -> dict:
    """A map of the inner limit judged on :func:`ael.synthetic.inner_scene`, where the truth is known (since 1.5.0).

    The other gates cannot see a core that is too large: a map with a "safety" margin passes the inner-limit gate
    whole, and on the author's 2026 image it took a person to find that such a map had thrown away the corona inside
    a prominence arch. Here both sides are counted: PASS if the core holds at least ``min_core`` of the clear emission,
    ``min_rim`` of the white rim and ``min_beads`` of the beads, **and** leaves to the filters at least ``min_corona``
    of the plain corona and ``min_pocket`` of the pocket of corona enclosed by the arch. A map dilated by a few pixels
    fails the last two."""
    core = np.asarray(core, bool)
    share = lambda a, b: float((a & b).sum() / max(int(a.sum()), 1))
    got = dict(emission_core_in_core=share(truth["emission_core"], core), rim_in_core=share(truth["rim"], core),
               beads_in_core=share(truth["beads"], core), corona_left_to_filters=share(truth["corona"], ~core),
               pocket_left_to_filters=share(truth["pocket"], ~core))
    need = dict(emission_core_in_core=min_core, rim_in_core=min_rim, beads_in_core=min_beads,
                corona_left_to_filters=min_corona, pocket_left_to_filters=min_pocket)
    counts = {k: int(truth[k].sum()) for k in ("emission_core", "rim", "beads", "corona", "pocket")}
    fail = [f"{k}: {got[k]:.3f} < {need[k]:g}" for k in got if got[k] < need[k]]
    fail += [f"the scene has no {k} to judge" for k, n in counts.items() if n == 0]
    return dict(gate="zones_against_truth", passed=not fail, failures=fail, measured={k: round(v, 4) for k, v in got.items()},
                required=need, truth_pixels=counts)


def summarize(results: list[dict]) -> dict:
    return dict(passed=all(r.get("passed", False) for r in results), gates=results)
