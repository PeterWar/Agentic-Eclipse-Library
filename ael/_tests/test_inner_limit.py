"""The inner limit (since 1.5.0): the single map, the estimators that lean less on an edge, the gates and the pipeline.

Every check has its negative control: a map with a margin, the plain mean at an edge, a ringed layer, a layer that starts
late. The figures of the real 2026 image are in docs/INNER_LIMIT.md; here the truth is synthetic and known."""
import json
import tempfile
from pathlib import Path

import numpy as np

from ael import filterbank as FB
from ael import filters as F
from ael import gates, synthetic
from ael.develop import filters_from_config
from ael.geometry import EclipseGeometry
from ael.radial import radial_quantile_rank
from ael.zones import inner_zones, zones_preview

_CACHE = {}


def _scene():
    if "scene" not in _CACHE:
        rgb, valid, geo, truth = synthetic.inner_scene(220.0, shape=(1000, 1000))
        _CACHE["scene"] = (rgb, valid, geo, truth, inner_zones(rgb, valid, geo))
    return _CACHE["scene"]


def _corona(size=520, rsun=90.0, moon_dx=5.0, noise=0.0, seed=1, hole=True):
    """A smooth corona (steep power law, two streamers) around an off-centre Moon. With ``hole=False`` the same
    corona goes on under the Moon: what an operator gives there is the truth for the scene with the hole."""
    geo = EclipseGeometry((size, size), (size / 2 + .3, size / 2 - .2), rsun, (size / 2 + .3 + moon_dx, size / 2 - .2), 1.03 * rsun)
    r = np.maximum(geo.rsun_map().astype(np.float64), 0.5); pa = np.radians(geo.pa_map().astype(np.float64))
    lum = 1e5 * r ** -4.5 * (1 + 1.5 * np.exp(-((pa - 0.9) / 0.4) ** 2) + 0.8 * np.exp(-((pa - 3.8) / 0.3) ** 2))
    if noise:
        lum = lum * (1 + noise * np.random.default_rng(seed).standard_normal(lum.shape))
    valid = ~geo.moon_mask(0) if hole else np.ones(lum.shape, bool)
    return lum.astype(np.float32), valid, geo


def raises(error, fn):
    try:
        fn()
    except error:
        return
    raise AssertionError(f"expected {error.__name__}")


# ---------------------------------------------------------------------------------------------- the map
def test_inner_zones_hold_the_emission_and_leave_the_corona_and_its_pocket():
    rgb, valid, geo, truth, z = _scene()
    g = gates.zones_against_truth(z.core, truth)
    assert g["passed"], g
    assert z.core.dtype == bool and z.core.shape == valid.shape and not (z.core & ~valid).any()
    assert z.info["pixels"]["prominence"] > 500 and z.info["pixels"]["chromosphere"] > 200
    assert any(p["px"] >= 0.9 * truth["pocket"].sum() for p in z.info["corona_pockets_inside_the_core"]), z.info["corona_pockets_inside_the_core"]
    # the input of the filters: identical outside the detected emission, redder light gone inside it
    changed = (z.clean != rgb).any(-1) & valid
    assert changed.sum() == z.info["filter_input"]["pixels_changed"] > 0
    assert not changed[truth["corona"] & (truth["share"] < 1e-4)].any()
    haze = changed & ~z.core
    assert haze.sum() > 100 and (z.clean[haze, 0] <= rgb[haze, 0]).all()
    assert zones_preview(z, rgb.mean(-1)).dtype == np.uint8


def test_a_map_with_a_margin_fails_against_the_truth():
    """The negative control of the gate that was missing: a core grown by 9 px passes the inner-limit gate whole and
    throws the pocket of corona away; only the truth sees it."""
    import cv2
    rgb, valid, geo, truth, z = _scene()
    grown = cv2.dilate(z.core.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (19, 19))) > 0
    g = gates.zones_against_truth(grown & valid, truth)
    assert not g["passed"] and any("pocket" in f for f in g["failures"]) and any("corona" in f for f in g["failures"]), g
    # and a map that misses the white rim fails on the other side
    g2 = gates.zones_against_truth(z.core & ~truth["rim"], truth)
    assert not g2["passed"] and any("rim" in f for f in g2["failures"]), g2


def test_inner_zones_mono_other_holes_and_refusals():
    rgb, valid, geo, truth, z = _scene()
    mono = inner_zones(rgb.mean(-1), valid, geo)
    assert mono.info["pixels"]["prominence"] == 0 and any("mono" in w for w in mono.info["warnings"])
    assert mono.core[truth["rim"]].mean() > 0.6                 # brightness still finds the limb's rim
    star = valid.copy(); star[100:106, 480:486] = False          # a masked star, far from the limb
    z2 = inner_zones(rgb, star, geo)
    near = np.zeros(valid.shape, bool); near[97:109, 477:489] = True
    assert not (z2.core & near).any()                            # a hole elsewhere is no lunar limb
    raises(ValueError, lambda: inner_zones(rgb, valid, EclipseGeometry(valid.shape, geo.sun_xy, geo.sun_radius_px)))
    raises(ValueError, lambda: inner_zones(rgb, valid, geo, share=0.0))
    raises(ValueError, lambda: inner_zones(rgb[:10], valid, geo))


# ---------------------------------------------------------------------------------------------- estimators
def test_local_fit_is_the_plain_mean_where_whole_and_unbiased_at_an_edge():
    yy, xx = np.mgrid[0:200, 0:240].astype(np.float64)
    img = 5 + 0.3 * xx - 0.2 * yy + 0.004 * xx * xx + 0.003 * xx * yy - 0.002 * yy * yy       # a quadratic surface
    hole = np.hypot(xx - 120, yy - 100) < 30
    valid = ~hole
    k = F.gaussian_kernel(4.0)
    truth, _ = F.local_fit(img, np.ones(img.shape, bool), k, 0)                              # mean with the kernel whole
    inner = np.zeros(img.shape, bool); inner[20:-20, 20:-20] = True                           # away from the frame
    edge = valid & inner & (np.hypot(xx - 120, yy - 100) < 36)
    plain, s0 = F.local_fit(img, valid, k, 0); fit2, _ = F.local_fit(img, valid, k, 2); fit1, _ = F.local_fit(img, valid, k, 1)
    assert (s0[edge] < .95).all()
    assert np.abs(plain[edge] - truth[edge]).max() > 1.0                                      # negative control: the plain mean leans
    # on an exactly quadratic surface order 2 is exact but for its ridge (0.2 % of the plain mean's error here)
    assert np.abs(fit2[edge] - truth[edge]).max() < 5e-3 * np.abs(plain[edge] - truth[edge]).max()
    assert np.abs(fit1[edge] - truth[edge]).max() < 0.05 * np.abs(plain[edge] - truth[edge]).max()  # order 1: gradient only
    far = valid & inner & (np.hypot(xx - 120, yy - 100) > 50)
    for b in (fit1, fit2):
        assert np.abs(b[far] - plain[far]).max() < 1e-6 * np.abs(plain[far]).max()            # kernel whole: the plain mean
    ng = F.normalized_gaussian_fit(img.astype(np.float32), valid, 4.0)
    assert np.isnan(ng[hole]).all() and np.isfinite(ng[edge]).all()
    raises(ValueError, lambda: F.local_fit(img, valid, k, 3))


def test_mgn_order_2_draws_no_halo_along_the_limb():
    """Truth: the MGN of the same corona without the hole. Next to the limb the plain mean is far from it (the halo a
    person marked on the 2026 layer); the local fit of order 2 is several times closer, and order 1 in between."""
    lum, valid, geo = _corona(size=700, rsun=150.0, moon_dx=8.0)
    full, _, _ = _corona(size=700, rsun=150.0, moon_dx=8.0, hole=False)
    truth = F.mgn(full, None, min_support=.01)
    d = geo.radius_map("moon") - geo.moon_radius_px
    err = {o: np.abs(F.mgn(lum, valid, min_support=.01, order=o) - truth) for o in (0, 1, 2)}
    for lo, hi in ((0.5, 3), (3, 6), (6, 12)):
        near = valid & (d > lo) & (d < hi)
        e0, e1, e2 = (float(err[o][near].mean()) for o in (0, 1, 2))
        assert e0 > 0.15, (lo, e0)                                       # negative control: the plain mean is off
        assert e2 < 0.45 * e0 and e2 < e1 < e0, (lo, hi, e0, e1, e2)


def test_dense_starlet_reconstructs_and_equals_the_atrous_one_away_from_edges():
    lum, valid, geo = _corona(noise=0.02)
    x = np.log(lum)
    det, coarse = F.starlet(x, valid, 4, kernel="dense")
    total = np.sum(det, axis=0) + coarse
    assert np.allclose(total[valid], x[valid], atol=2e-5)
    ref, _ = F.starlet(x, valid, 4)
    d = geo.radius_map("moon") - geo.moon_radius_px
    h, w = lum.shape; yy, xx = np.mgrid[0:h, 0:w]
    far = valid & (d > 70) & (np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)) > 70)
    assert far.sum() > 20000
    for j in range(4):
        assert np.abs(det[j][far] - ref[j][far]).max() < 1e-4, j         # kernels whole: the same transform
    # truth: the same coefficients without the hole. Next to it the à-trous ones lean; the dense ones with a plane less
    full, _, _ = _corona(noise=0.02, hole=False)
    true, _ = F.starlet(np.log(full), None, 4)
    near = valid & (d > 0.5) & (d < 4)
    for j in (2, 3):
        e_dense, e_atrous = (float(np.abs(c[j][near] - true[j][near]).mean()) for c in (det, ref))
        assert e_dense < 0.6 * e_atrous, (j, e_dense, e_atrous)
    raises(ValueError, lambda: F.starlet(x, valid, 3, kernel="other"))


def test_radial_profile_in_chain_follows_the_whole_annuli_up_to_an_offcentre_limb():
    """Truth: the residual of the same corona without the hole (every annulus whole). The annuli the Moon cuts lose a
    sector, their medians move, and the curve fitted to them drags the residual; in chain it stays closer to the truth."""
    kw = dict(size=800, rsun=150.0, moon_dx=14.0)
    lum, valid, geo = _corona(**kw); full, everywhere, _ = _corona(hole=False, **kw)
    true, _ = FB.radial_log_residual(full, everywhere, geo)
    seen, _ = FB.radial_log_residual(lum, valid, geo)
    chained, info = FB.radial_log_residual(lum, valid, geo, partial_annuli="chain")
    assert info["partial_annuli"] == "chain" and info["chained_annuli"] >= 20, info
    r = geo.radius_map(); first = info["first_whole_annulus_px"]
    rms = lambda res, lo, hi: float(np.sqrt(np.mean((res - true)[valid & (r >= lo) & (r < hi)] ** 2)))
    inner = (first - 24, first - 16)                                     # the most cut annuli
    assert rms(seen, *inner) > 0.08, rms(seen, *inner)                   # negative control: observed medians drag the curve
    assert rms(chained, *inner) < 0.5 * rms(seen, *inner), (rms(chained, *inner), rms(seen, *inner))
    for lo, hi in ((first - 16, first - 8), (first - 8, first - 2)):     # never worse on the way out
        assert rms(chained, lo, hi) < 1.05 * rms(seen, lo, hi), (lo, rms(chained, lo, hi), rms(seen, lo, hi))
    whole = valid & (r > first + 60)
    assert np.abs(chained[whole] - seen[whole]).max() < 0.02             # away from the cut annuli: the same curve
    # no annulus whole (a strip of data): the medians as observed, and that is said
    strip = valid.copy(); strip[:, :420] = False
    _, info2 = FB.radial_log_residual(lum, strip, geo, partial_annuli="chain")
    assert info2["chained_annuli"] == 0 and "note" in info2
    raises(ValueError, lambda: FB.radial_log_residual(lum, valid, geo, partial_annuli="other"))


def test_fnrgf_normalises_per_angle_and_bridges_cut_annuli():
    lum, valid, geo = _corona(moon_dx=6.0, noise=0.01)
    q, info = F.fnrgf(lum, valid, geo, return_info=True)
    assert info["chained_annuli"] >= 3 and info["first_annulus_px"] < info["first_whole_annulus_px"], info
    r = geo.radius_map(); ok = np.isfinite(q)
    inside = valid & (r < info["first_whole_annulus_px"]) & (r > info["first_annulus_px"] + 2)
    assert ok[inside].mean() > 0.95                                     # the cut annuli do get a layer
    ring = ok & (r > info["first_whole_annulus_px"] + 10) & (r < 200)
    assert abs(float(q[ring].mean())) < 0.1 and 0.3 < float(q[ring].std()) < 5
    # the Fourier curves follow the streamers: the bright sector is not lifted as a whole, as an NRGF lifts it
    pa = np.radians(geo.pa_map()); bright = ring & (np.abs(pa - 0.9) < 0.2)
    n = F.nrgf(lum, valid, geo, bin_px=2, min_count=12)
    assert abs(float(q[bright].mean())) < 0.25 * abs(float(n[bright & np.isfinite(n)].mean()))
    assert not np.isfinite(q[~valid]).any()
    strip = valid.copy(); strip[:, :250] = False
    raises(ValueError, lambda: F.fnrgf(lum, strip, geo))               # no whole annulus to anchor on


def test_local_rank_in_chain_is_the_usual_one_where_windows_are_whole():
    lum, valid, geo = _corona(moon_dx=0.0, noise=0.01)                  # a centred Moon cuts no window; the frame does
    a = radial_quantile_rank(lum, valid, geo, 30); b = radial_quantile_rank(lum, valid, geo, 30, partial_windows="chain")
    assert np.array_equal(a, b, equal_nan=True)                         # windows the frame cuts are left as observed
    lum, valid, geo = _corona(size=800, rsun=150.0, moon_dx=14.0, noise=0.01)
    a = radial_quantile_rank(lum, valid, geo, 30); b = radial_quantile_rank(lum, valid, geo, 30, partial_windows="chain")
    r = geo.radius_map(); both = np.isfinite(a) & np.isfinite(b)
    assert np.array_equal(np.isfinite(a), np.isfinite(b))
    changed = both & (a != b)
    assert changed.sum() > 1000 and r[changed].max() < geo.moon_radius_px + 14 + 6   # only the annuli the Moon cuts
    assert np.abs(a[changed] - b[changed]).max() > 0.02
    raises(ValueError, lambda: radial_quantile_rank(lum, valid, geo, 30, partial_windows="other"))


def test_make_filter_edges_changes_layers_only_near_an_edge():
    lum, valid, geo = _corona(size=800, rsun=150.0, moon_dx=14.0, noise=0.01)
    d = geo.radius_map("moon") - geo.moon_radius_px
    h, w = lum.shape; yy, xx = np.mgrid[0:h, 0:w]
    frame = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    near = valid & (d > 0.5) & (d < 6)
    for name, reach in (("mgn", 165), ("achf_iso_04", 70), ("rhef_local30", 40)):
        new = FB.filter_detail(name, lum, valid, geo)[0]; old = FB.filter_detail(name, lum, valid, geo, edges="classic")[0]
        far = valid & (d > reach) & (frame > reach) & np.isfinite(new) & np.isfinite(old); spread = float(np.std(old[far]))
        assert far.sum() > 500 and np.abs(new[far] - old[far]).max() < 0.05 * spread, (name, float(np.abs(new[far] - old[far]).max()), spread)
        k = near & np.isfinite(new) & np.isfinite(old)
        assert np.abs(new[k] - old[k]).max() > 0.05 * spread, name       # and it does change next to the limb
    for name in ("wow_edge_aware", "wow", "achf_angular", "nrgf"):     # not cured: the same in both
        new = FB.filter_detail(name, lum, valid, geo)[0]; old = FB.filter_detail(name, lum, valid, geo, edges="classic")[0]
        assert np.array_equal(new, old, equal_nan=True), name
    raises(ValueError, lambda: FB.make_filter("mgn", lum, valid, geo, edges="other"))
    q, mode, info = FB.make_filter("fnrgf", lum, valid, geo)
    assert mode == "multiply" and np.nanmin(q) >= 0 and np.nanmax(q) <= 1 and "fnrgf" in FB.EXTRA and "fnrgf" not in FB.NAMES


def _varying_index_scene(R=40.0, seed=4, hole=True):
    """A power-law corona whose index changes with position angle (-3 ± 0.8 cos PA) around an off-centre Moon, the
    data excluded within 1.25 R of it, 1 % noise. Without ``hole`` the data go on under the Moon: the truth."""
    n = int(12.8 * R); g = EclipseGeometry((n, n), (n / 2, n / 2), R, (n / 2 + 0.2 * R, n / 2), R + 4)
    r = g.radius_map(); th = np.radians(g.pa_map())
    a = ((np.maximum(r, 1) / R) ** (-3 + .8 * np.cos(th))).astype(np.float32)
    a = a * (1 + .01 * np.random.default_rng(seed).standard_normal(a.shape)).astype(np.float32)
    return g, (g.radius_map("moon") > 1.25 * R) if hole else (r > 0.3 * R), a, g.radius_map("moon") - 1.25 * R


def test_unbiased_layers_are_closer_to_the_truth_next_to_the_hole_and_the_plain_wow_is_left_alone():
    """Truth: each layer made with the data whole (the corona going on under the Moon). Next to the hole the unbiased
    ACHF and Hessian layers are several times closer to it than the 1.4.2 operators. The dense-kernel variant of the
    plain WOW is not: it is further from the truth than the 1.3.4 WOW, which is why `make_filter` does not use it."""
    g, m, a, d = _varying_index_scene(); _, whole, _, _ = _varying_index_scene(hole=False)
    def errors(layer, truth, spread):
        return [float(np.sqrt(np.mean((layer - truth)[m & np.isfinite(layer) & np.isfinite(truth) & (d >= lo) & (d < hi)] ** 2)) / spread)
                for lo, hi in ((0, 6), (6, 16))]
    for name in ("achf_iso_04", "hessian_ridge"):
        truth = FB.filter_detail(name, a, whole, g, edges="classic")[0]
        k = m & np.isfinite(truth) & (d > 40); spread = float(1.4826 * np.median(np.abs(truth[k] - np.median(truth[k]))))
        old = errors(FB.filter_detail(name, a, m, g, edges="classic")[0], truth, spread)
        new = errors(FB.filter_detail(name, a, m, g)[0], truth, spread)
        assert old[0] > 2.0, (name, old)                                # negative control: the 1.4.2 operator is far off
        assert new[0] < 0.4 * old[0] and new[1] < 0.4 * old[1], (name, new, old)
    res_whole, _ = FB.radial_log_residual(a, whole, g); truth, _ = FB.wow_measured(res_whole, whole, g)
    k = m & np.isfinite(truth) & (d > 40); spread = float(1.4826 * np.median(np.abs(truth[k] - np.median(truth[k]))))
    res, _ = FB.radial_log_residual(a, m, g)
    default = errors(FB.wow_measured(res, m, g)[0], truth, spread)
    dense = errors(FB.wow_measured(res, m, g, starlet_kernel="dense", edge_completeness=None)[0], truth, spread)
    assert dense[0] > 1.5 * default[0] and dense[1] > 1.5 * default[1], (dense, default)
    assert np.array_equal(FB.filter_detail("wow", a, m, g)[0], FB.wow_measured(res, m, g)[0], equal_nan=True)


# ---------------------------------------------------------------------------------------------- gates
def test_false_hole_gate_tells_the_cure_from_the_plain_mean():
    lum, valid, geo = _corona(size=640, rsun=70.0, noise=0.01)
    plain = lambda L, m: np.where(m, F.mgn(L, m, min_support=.01), np.nan)
    cured = lambda L, m: np.where(m, F.mgn(L, m, min_support=.01, order=2), np.nan)
    a = gates.false_hole(plain, lum, valid, geo, grow_px=40); b = gates.false_hole(cured, lum, valid, geo, grow_px=40)
    assert a["absolute"] == "FAIL" and a["failures"], a["bands"]          # the plain mean leans on the false edge
    for band in ("3-6", "6-12", "12-20"):
        assert b["bands"][band]["difference"] < 0.5 * a["bands"][band]["difference"], (band, b["bands"][band], a["bands"][band])
    assert gates.false_hole_regression(b, b)["passed"]
    worse = gates.false_hole_regression(a, b)
    assert not worse["passed"] and any(w.startswith("3-6") for w in worse["worse"]), worse   # the cure undone is a regression
    # (40 px beyond the real hole the "truth" still feels it at the two coarsest scales of the MGN, and the cure reaches
    #  further than the plain mean: bands beyond 36 px need a larger false hole, as the gate's own text says)
    lost = dict(b, bands=dict(b["bands"], **{"6-12": dict(b["bands"]["6-12"], px=1)}))
    assert not gates.false_hole_regression(lost, b)["passed"]             # losing coverage is a failure too
    raises(ValueError, lambda: gates.false_hole(plain, lum, valid, geo, hole="other"))
    raises(ValueError, lambda: gates.false_hole(plain, lum[:100, :100], valid[:100, :100],
                                                EclipseGeometry((100, 100), (50, 50), 20.0, (51, 50), 21.0)))


def test_gramophone_gate_finds_injected_rings_and_spares_those_of_the_control():
    import cv2
    geo = EclipseGeometry((720, 720), (360.3, 359.6), 100.0)
    rng = np.random.default_rng(4)
    smooth = (0.5 + 0.05 * cv2.GaussianBlur(rng.standard_normal((720, 720)).astype(np.float32), (0, 0), 2.0) / 0.14).astype(np.float32)
    clean = gates.gramophone(smooth, None, geo)
    assert clean["passed"] and clean["verdict"] in ("PASS", "WARN"), clean["failures"]
    r = geo.radius_map()
    ringed = (smooth + 1e-2 * np.sin(2 * np.pi * r / 7.0)).astype(np.float32)     # rings of level, a fifth of the texture
    bad = gates.gramophone(ringed, None, geo)
    assert bad["verdict"] == "FAIL" and not bad["passed"] and any("level" in f["measure"] for f in bad["failures"]), bad["verdict"]
    grain = (0.5 + (smooth - 0.5) * (1 + 0.3 * np.sin(2 * np.pi * r / 9.0))).astype(np.float32)   # rings of grain
    bad2 = gates.gramophone(grain, None, geo)
    assert bad2["verdict"] == "FAIL" and any("grain" in f["measure"] for f in bad2["failures"])
    same = gates.gramophone(ringed, None, geo, control=ringed)
    assert same["verdict"] != "FAIL"                                      # the rings the control already carries
    off = gates.gramophone(ringed, None, EclipseGeometry((720, 720), (300.0, 420.0), 100.0))
    assert off["verdict"] != "FAIL"                                       # rings about another centre are not the Sun's
    tiny = gates.gramophone(smooth[:200, :200], None, EclipseGeometry((200, 200), (100, 100), 100.0))
    assert tiny["passed"] is None and tiny["verdict"] == "NOT JUDGED"


def test_inner_limit_gate_passes_good_layers_and_fails_bad_ones():
    rgb, valid, geo, truth, z = _scene()
    check = gates.inner_limit_selfcheck(z.core, geo, valid=valid)
    assert check["passed"], check
    assert check["cases"]["detail_inside_the_core"]["verdict"] == "FAIL" and check["cases"]["starts_15_px_late"]["verdict"] == "FAIL"
    raises(ValueError, lambda: gates.inner_limit({}, z.core, EclipseGeometry(valid.shape, geo.sun_xy, geo.sun_radius_px)))
    # a layer that is flat over its first 15 px must fail whatever its level: the step between a level and the void
    # beside it is not detail (a plain blur read it as such and passed the layer)
    import cv2
    f = gates._inner_limit_frame(z.core, valid, geo)
    d = np.zeros(valid.shape, np.float32); d[f["sl"]] = f["d"]; vis = np.zeros(valid.shape, np.float32); vis[f["sl"]] = f["visible"]
    tex = np.clip(.5 + .12 * cv2.GaussianBlur(np.random.default_rng(1).standard_normal(valid.shape).astype(np.float32), (0, 0), 2.) / .14, 0, 1)
    good = gates.inner_limit({"x": (np.where(vis > 0, tex, np.nan), vis)}, z.core, geo, valid=valid)
    assert good["passed"] and good["layers"]["x"]["measure"]["d50_error_median_px"] <= 1
    for level in (0.3, 0.7):
        flat = np.where(vis > 0, np.where(d < 15, level, level - .5 + tex), np.nan).astype(np.float32)
        r = gates.inner_limit({"x": (flat, vis)}, z.core, geo, valid=valid)["layers"]["x"]
        assert r["verdict"] == "FAIL" and r["failures"][0].startswith("L2"), (level, r["failures"])
        const = gates.inner_limit({"x": (np.where(vis > 0, level, np.nan).astype(np.float32), vis)}, z.core, geo, valid=valid)["layers"]["x"]
        assert const["verdict"] == "WARN" and const["measure"]["sectors_judged"] == 0      # nothing to judge is said, not passed
    # L3: layers that start in different places fail together; a sector without a start in one of them is not judged
    same = [("a", [1.0] * 12), ("b", [2.0] * 12)]
    assert gates.inner_limit_between(same)["verdict"] == "PASS"
    apart = [("a", [1.0] * 12), ("b", [1.0] * 8 + [12.0] * 4)]
    assert gates.inner_limit_between(apart)["verdict"] == "FAIL"
    holes = gates.inner_limit_between([("a", [1.0] * 12), ("b", [float("nan")] * 3 + [1.0] * 9)])
    assert holes["sectors_judged"] == 9 and holes["start_spread_per_sector_px"][0] is None


# ---------------------------------------------------------------------------------------------- the pipeline
def test_filters_pipeline_uses_the_map_and_switches_off_a_layer_that_fails():
    rgb, valid, geo, truth, z = _scene()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        np.save(tmp / "linear.npy", np.nan_to_num(rgb, nan=0.0)); np.save(tmp / "valid.npy", valid); geo.to_json(tmp / "geometry.json")
        base = dict(input="linear.npy", geometry="geometry.json", valid="valid.npy", moon_margin_px=0,
                    display=dict(scale=float(np.nanpercentile(rgb, 99.5))))
        names = ["nrgf", "wow_edge_aware", "achf_iso_04", "larson_sekanina_1"]
        (tmp / "new.json").write_text(json.dumps(dict(base, filters=names, visible=names)))
        said = []
        r = filters_from_config(tmp / "new.json", tmp / "new", progress=said.append)
        rec = json.loads(Path(r["receipt"]).read_text())
        assert r["inner_limit"]["used"] and Path(r["inner_limit"]["map"]).is_file()
        core = np.load(tmp / "new/inner_limit_core.npy"); assert np.array_equal(core, z.core)
        # an Overlay layer is transparent in the core; a Multiply layer carries its level there, and no detail
        assert (np.load(tmp / "new/wow_edge_aware_alpha.npy")[core] == 0).all() and np.isnan(np.load(tmp / "new/wow_edge_aware_layer.npy")[core]).all()
        nrgf = np.load(tmp / "new/nrgf_layer.npy"); assert (np.load(tmp / "new/nrgf_alpha.npy")[core] > 0).all() and np.isfinite(nrgf[core]).all()
        for name in names[:3]:
            assert r["gates"]["layers"][name]["inner_limit"] in ("PASS", "WARN"), (name, rec["gates"]["layers"][name])
        # the negative control: a layer with a rule of its own at the limb starts late, fails and is switched off
        assert r["gates"]["layers"]["larson_sekanina_1"]["inner_limit"] == "FAIL" and r["gates"]["verdict"] == "FAIL"
        assert r["gates"]["switched_off_by_a_gate"] == ["larson_sekanina_1"] == r["gates"]["failed"]
        assert r["gates"]["between_layers"] in ("PASS", "FAIL")
        layer = {p["name"]: p for p in rec["parameters"]["layers"]}
        assert layer["larson_sekanina_1"]["visible"] is False and layer["nrgf"]["visible"] is True
        assert any("written switched off" in s for s in said) and rec["gates"]["enforced"] is True
        assert rec["gates"]["nothing_outside_data"] and rec["parameters"]["inner_limit"]["used"]
        # "gates": "report" leaves it on and says the gate was not enforced
        (tmp / "report.json").write_text(json.dumps(dict(base, filters=["larson_sekanina_1"], visible=["larson_sekanina_1"], gates="report")))
        r2 = filters_from_config(tmp / "report.json", tmp / "report", progress=lambda m: None)
        rec2 = json.loads(Path(r2["receipt"]).read_text())
        assert r2["gates"]["verdict"] == "FAIL" and r2["gates"]["switched_off_by_a_gate"] == [] and rec2["gates"]["enforced"] is False
        assert rec2["parameters"]["layers"][0]["visible"] is True
        # the 1.4.2 layers on request: no map, classic edges, the same arrays as the operators give directly
        (tmp / "old.json").write_text(json.dumps(dict(base, filters=["achf_iso_04", "nrgf"], inner_limit=False, edges="classic")))
        r3 = filters_from_config(tmp / "old.json", tmp / "old", progress=lambda m: None)
        assert r3["gates"]["verdict"] == "NOT JUDGED" and not r3["inner_limit"]["used"] and "why_not" in r3["inner_limit"]
        lum = (rgb[..., 0] + 2 * rgb[..., 1] + rgb[..., 2]) / 4; ok = valid & np.isfinite(lum) & (lum > 0)
        direct = FB.make_filter("achf_iso_04", np.nan_to_num(lum), ok, geo, edges="classic")[0]
        assert np.array_equal(np.load(tmp / "old/achf_iso_04_layer.npy"), np.where(ok & np.isfinite(direct), direct, np.nan), equal_nan=True)
        # refusals
        (tmp / "bad.json").write_text(json.dumps(dict(base, edges="other")))
        raises(ValueError, lambda: filters_from_config(tmp / "bad.json", tmp / "bad"))
        nomoon = EclipseGeometry(valid.shape, geo.sun_xy, geo.sun_radius_px); nomoon.to_json(tmp / "nomoon.json")
        (tmp / "must.json").write_text(json.dumps(dict(base, geometry="nomoon.json", inner_limit=True)))
        raises(ValueError, lambda: filters_from_config(tmp / "must.json", tmp / "must"))
        (tmp / "auto.json").write_text(json.dumps(dict(base, geometry="nomoon.json", filters=["achf_iso_04"])))
        r4 = filters_from_config(tmp / "auto.json", tmp / "auto", progress=lambda m: None)
        assert not r4["inner_limit"]["used"] and "no Moon" in r4["inner_limit"]["why_not"]
        rec4 = json.loads(Path(r4["receipt"]).read_text())
        assert rec4["gates"]["verdict"] == "NOT JUDGED" and "no Moon" in rec4["gates"]["why_not_judged"]
        for wrong in (0, 1, "yes"):                                # JSON 0 and 1 are not false and true
            (tmp / "wrong.json").write_text(json.dumps(dict(base, inner_limit=wrong)))
            raises(ValueError, lambda: filters_from_config(tmp / "wrong.json", tmp / "wrong"))
        # "auto" goes on when the map cannot be measured (a Moon outside the canvas), and says why; true stops
        away = EclipseGeometry(valid.shape, geo.sun_xy, geo.sun_radius_px, (5000.0, 5000.0), geo.moon_radius_px); away.to_json(tmp / "away.json")
        (tmp / "away_auto.json").write_text(json.dumps(dict(base, geometry="away.json", filters=["achf_iso_04"])))
        r5 = filters_from_config(tmp / "away_auto.json", tmp / "away_auto", progress=lambda m: None)
        assert not r5["inner_limit"]["used"] and "could not be measured" in r5["inner_limit"]["why_not"]
        (tmp / "away_true.json").write_text(json.dumps(dict(base, geometry="away.json", filters=["achf_iso_04"], inner_limit=True)))
        raises(ValueError, lambda: filters_from_config(tmp / "away_true.json", tmp / "away_true"))
        # a mono input: the map is made without colour, and the command says so
        lum = np.nan_to_num((rgb[..., 0] + 2 * rgb[..., 1] + rgb[..., 2]) / 4, nan=0.0)
        np.save(tmp / "mono.npy", lum)
        (tmp / "mono.json").write_text(json.dumps(dict(base, input="mono.npy", filters=["achf_iso_04"])))
        r6 = filters_from_config(tmp / "mono.json", tmp / "mono", progress=lambda m: None)
        assert r6["inner_limit"]["used"] and any("mono" in w for w in r6["inner_limit"]["warnings"])
        assert r6["inner_limit"]["pixels"]["prominence"] == 0
        # a failing layer that was not visible is named in `failed`, not in `switched_off_by_a_gate`
        (tmp / "hid.json").write_text(json.dumps(dict(base, filters=["achf_iso_04", "larson_sekanina_1"])))
        r7 = filters_from_config(tmp / "hid.json", tmp / "hid", progress=lambda m: None)
        assert r7["gates"]["verdict"] == "FAIL" and r7["gates"]["failed"] == ["larson_sekanina_1"] and r7["gates"]["switched_off_by_a_gate"] == []
