"""Known-truth tests for differential extinction.  Synthetic scenes only; no observation is implied.

The scene mimics the geometry of a low Sun (apparent altitude 9.17°, k = 0.40 mag per air mass, the
zenith at position angle 48.4°) on a small canvas whose solar radius has its true angular size, so that
the field reaches beyond 8 R☉.
"""
import hashlib
import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from ael import extinction as ex
from ael import render
from ael.geometry import EclipseGeometry, direction_of_pa, image_angle_of_pa
from ael.synthetic import SyntheticScene, baumbach

R = 20.0                       # solar radius, px
SCALE = 946.66 / R             # arcsec per px: the Sun keeps its angular size
H_SUN = 9.17                   # apparent altitude of the Sun, deg
K = 0.40                       # mag per air mass
ZPA = 48.4                     # position angle of the zenith seen from the Sun, deg
RINGS = [(1.2, 1.6), (1.6, 2.2), (2.2, 3.0), (3.0, 4.0), (4.0, 5.0)]


def _raises(error, fn):
    try:
        fn()
    except error:
        return
    raise AssertionError(f"expected {error.__name__}")


def _geo(mirrored=False):
    return EclipseGeometry(shape=(360, 440), sun_xy=(219.6, 179.3), sun_radius_px=R, north_deg=20.0,
                           mirrored=mirrored, arcsec_per_px=SCALE)


def _scene(geo):
    X = ex.airmass_map(geo, H_SUN, zenith_pa_deg=ZPA)
    x_ref = float(ex.kasten_young(H_SUN))
    E = 10.0 ** (0.4 * K * (X - x_ref))     # written out here, independently of ex.extinction_factor
    r = geo.rsun_map(dtype=np.float64)
    return X, x_ref, E, r, r >= 1.1


def _sky_plane(geo, level=400.0):
    h, w = geo.shape
    yy, xx = np.mgrid[0:h, 0:w]
    return level + 30.0 * (xx - w / 2) / w - 50.0 * (yy - h / 2) / h


def _smooth_corona(r):
    return np.where(r >= 1, baumbach(r) / baumbach(1.0) * 2e5, 0.0)


def _structured_corona(geo):
    sc = SyntheticScene(sun_radius_px=R, seed=3, n_rays=150, sky_level=0.0, sky_gradient=(0, 0),
                        psf_sigma_px=0.0, north_deg=geo.north_deg)
    return sc.radiance(geo.shape, geo.sun_xy, with_moon=False).astype(np.float64)


def _log_ratio(net, truth, valid):
    return np.log(np.where((net > 0) & valid, net, np.nan) / truth)


def _alt_at(dx, dy, **kw):
    """Altitude of the single pixel at image offset (dx, dy) from the Sun."""
    g = EclipseGeometry(shape=(1, 1), sun_xy=(-dx, -dy), sun_radius_px=R, north_deg=kw.pop("north_deg", 0.0),
                        mirrored=kw.pop("mirrored", False), arcsec_per_px=SCALE)
    return float(ex.altitude_map(g, kw.pop("h", H_SUN), **kw)[0, 0])


# ------------------------------------------------------------------------------------------------
def test_kasten_young_reference_values_and_horizon():
    assert abs(ex.kasten_young(90.0) - 1.0) < 3e-4          # 0.9997: the formula is a fit
    assert abs(ex.kasten_young(0.0) - 37.92) < 0.01           # its value at the horizon
    assert abs(ex.kasten_young(30.0) - 1.9943) < 1e-3
    h = np.linspace(30, 90, 61)                                # plane-parallel limit high in the sky
    assert np.max(np.abs(ex.kasten_young(h) * np.sin(np.radians(h)) - 1.0)) < 3e-3
    hs = np.linspace(0, 90, 901)
    assert np.all(np.diff(ex.kasten_young(hs)) < 0)
    assert np.isnan(ex.kasten_young(-0.5))                    # no extrapolation below the horizon
    assert abs(ex.kasten_young(H_SUN) - 6.05) < 0.01          # the Sun of 2026 at mid-totality


def test_airmass_map_zenith_symmetry_and_orientation():
    up = ex.altitude_map(EclipseGeometry((1, 1), (0.0, 0.0), R, arcsec_per_px=SCALE), H_SUN, zenith_image_deg=0)
    assert abs(up[0, 0] - H_SUN) < 1e-12                       # the Sun's own line of sight
    for d in (10.0, 40.0, 150.0):                              # straight up: h = h☉ + atan(ξ), exactly
        expect = H_SUN + math.degrees(math.atan(d * SCALE * ex.ARCSEC))
        assert abs(_alt_at(0.0, -d, zenith_image_deg=0) - expect) < 1e-10
    a = math.radians(37.0)                                     # any orientation: mirror pairs across the vertical
    z = np.array([math.sin(a), -math.cos(a)])
    p = np.array([math.cos(a), math.sin(a)])
    for along, across in ((0.0, 60.0), (35.0, 80.0), (-50.0, 20.0)):
        o1, o2 = along * z + across * p, along * z - across * p
        assert abs(_alt_at(*o1, zenith_image_deg=37.0) - _alt_at(*o2, zenith_image_deg=37.0)) < 1e-12
    # Zenith side thinner, horizon side thicker; the 2026 figures at ±2 R☉.
    two = 2 * 946.66 / SCALE
    x_up = ex.kasten_young(_alt_at(0.0, -two, zenith_image_deg=0))
    x_dn = ex.kasten_young(_alt_at(0.0, two, zenith_image_deg=0))
    assert x_up < ex.kasten_young(H_SUN) < x_dn
    assert abs(x_up - 5.75) < 0.01 and abs(x_dn - 6.39) < 0.01, (x_up, x_dn)
    # Three equivalent ways to give the orientation, mirrored or not.
    for mirrored in (False, True):
        g = _geo(mirrored)
        by_pa = ex.airmass_map(g, H_SUN, zenith_pa_deg=ZPA)
        by_img = ex.airmass_map(g, H_SUN, zenith_image_deg=float(image_angle_of_pa(ZPA, g.north_deg, mirrored)))
        n = np.array(direction_of_pa(0.0, g.north_deg, mirrored)) / SCALE
        e = np.array(direction_of_pa(90.0, g.north_deg, mirrored)) / SCALE
        by_vec = ex.airmass_map(g, H_SUN, zenith_pa_deg=ZPA, north_px=n, east_px=e)
        assert np.max(np.abs(by_pa - by_img)) < 1e-10 and np.max(np.abs(by_pa - by_vec)) < 1e-10
    g = _geo()
    _raises(ValueError, lambda: ex.airmass_map(g, H_SUN, zenith_pa_deg=ZPA, zenith_image_deg=0))
    _raises(ValueError, lambda: ex.airmass_map(g, H_SUN))
    nos = EclipseGeometry(g.shape, g.sun_xy, R)
    _raises(ValueError, lambda: ex.airmass_map(nos, H_SUN, zenith_pa_deg=ZPA))


def test_correction_is_exact_with_true_sky_and_keeps_colour():
    g = _geo()
    X, x_ref, E, r, valid = _scene(g)
    colour = np.array([1.3, 1.0, 0.55])
    C = _structured_corona(g)[..., None] * colour
    S = np.stack([_sky_plane(g, lv) for lv in (300.0, 400.0, 250.0)], -1)
    I = C / E[..., None] + S
    out = ex.correct_extinction(I, X, K, x_ref=x_ref, sky=S, valid=valid)
    ok = valid & (r >= 1.1)
    assert ex.extinction_factor(x_ref + 0.5, K, x_ref) > 1 > ex.extinction_factor(x_ref - 0.5, K, x_ref)
    assert np.max(np.abs(out[ok] / C[ok] - 1.0)) < 1e-5
    assert np.isnan(out[~valid]).all()                          # nothing outside the data
    net = I - S                                                 # achromatic: colour ratios unchanged
    assert np.max(np.abs(out[ok][:, 0] / out[ok][:, 1] - net[ok][:, 0] / net[ok][:, 1])) < 1e-4
    kept = ex.correct_extinction(I, X, K, x_ref=x_ref, sky=S, valid=valid, keep_sky=True)
    assert np.allclose(kept[ok] - S[ok], out[ok], rtol=1e-5, atol=1e-3)
    # Chromatic extinction: one k per channel recovers it; a single k leaves a colour gradient with X.
    kc = (0.30, 0.40, 0.55)
    Ic = C * 10.0 ** (-0.4 * np.array(kc) * (X[..., None] - x_ref)) + S
    good = ex.correct_extinction(Ic, X, kc, x_ref=x_ref, sky=S, valid=valid)
    assert np.max(np.abs(good[ok] / C[ok] - 1.0)) < 1e-5
    bad = ex.correct_extinction(Ic, X, K, x_ref=x_ref, sky=S, valid=valid)
    rg = bad[..., 0] / bad[..., 1] / (colour[0] / colour[1])
    lo, hi = ok & (X < x_ref - 0.5), ok & (X > x_ref + 0.5)
    assert np.median(rg[hi]) - np.median(rg[lo]) > 0.03          # detected: red over-corrected towards the horizon
    # Below the horizon there is no air mass, hence no data.
    Xh = X.copy()
    Xh[:5] = np.nan
    assert np.isnan(ex.correct_extinction(I, Xh, K, x_ref=x_ref, sky=S)[:5]).all()
    _raises(ValueError, lambda: ex.correct_extinction(I, X, (0.3, 0.4), x_ref=x_ref, sky=S))
    _raises(ValueError, lambda: ex.correct_extinction(I, X, K, x_ref=x_ref, sky=[1.0, 2.0]))
    _raises(ValueError, lambda: ex.correct_extinction(I, X, -0.1, x_ref=x_ref, sky=S))
    _raises(ValueError, lambda: ex.correct_extinction(I, X[:-1], K, x_ref=x_ref, sky=S))


def test_extinction_recovered_when_sky_is_fitted_where_corona_is_negligible():
    """Positive control.  The synthetic corona is cut off beyond ~6 R☉ (declared) so that the sky region
    r ≥ 8 R☉ holds no corona: this isolates the extinction step; the sky bias is tested below."""
    g = _geo()
    X, x_ref, E, r, valid = _scene(g)
    C = _structured_corona(g) * np.exp(-(r / 5.0) ** 6)
    I = C / E + _sky_plane(g) + np.random.default_rng(1).normal(0, 3, C.shape)
    S, _ = render.sky_background(I, valid, g, r_min_rsun=8, order=1)
    corr = ex.correct_extinction(I, X, K, x_ref=x_ref, sky=S, valid=valid)
    injected = ex.ring_dipole(np.log(E), valid, g, RINGS, direction_pa_deg=ZPA)
    after = ex.ring_dipole(_log_ratio(corr, C, valid), valid, g, RINGS, direction_pa_deg=ZPA)
    before = ex.ring_dipole(_log_ratio(I - S, C, valid), valid, g, RINGS, direction_pa_deg=ZPA)
    for i, a, b in zip(injected, after, before):
        assert i["along"] < -0.08                               # the injected dipole: 0.08–0.27 in ln
        assert abs(a["c0"]) < 0.005 and abs(a["along"]) < 0.005, a
        assert abs(b["along"] + i["along"]) < 0.05 * abs(i["along"]), (b, i)
    rows = ex.k_nulling_dipole(_log_ratio(I - S, C, valid), X, x_ref, valid, g, RINGS, zenith_pa_deg=ZPA)
    assert ex.k_consistency(rows, K)["passed"]
    assert not ex.k_consistency(rows, 0.0)["passed"]            # negative: "no extinction" is rejected


def test_sky_plane_fitted_on_uncorrected_data_absorbs_extinction_dipole():
    """Negative test.  A symmetric corona has no dipole of its own; extinction gives its faint tail one,
    and a sky plane fitted on uncorrected data takes it as a sky gradient towards the zenith."""
    g = _geo()
    X, x_ref, E, r, valid = _scene(g)
    C = _smooth_corona(r)
    uz = direction_of_pa(ZPA, g.north_deg, g.mirrored)

    def zenith_gradient(model):                                # counts per R☉ along the zenith direction
        cx, cy = g.sun_xy
        at = lambda t: model[int(round(cy + t * R * uz[1])), int(round(cx + t * R * uz[0]))]
        return (at(3.0) - at(-3.0)) / 6.0

    fit = lambda img: render.sky_background(img, valid, g, r_min_rsun=8, order=1)[0]
    g_control = zenith_gradient(fit(C))                         # no extinction: no gradient taken
    absorbed_model = fit(C / E)
    g_absorbed = zenith_gradient(absorbed_model)                # extinguished tail: a gradient taken
    assert abs(g_control) < 0.01 and g_absorbed > 0.3, (g_control, g_absorbed)
    sky = _sky_plane(g)
    I = C / E + sky + np.random.default_rng(2).normal(0, 3, C.shape)
    S = fit(I)
    bias = zenith_gradient(S) - zenith_gradient(sky)
    assert 0.5 * g_absorbed < bias < 1.5 * g_absorbed, (bias, g_absorbed)   # detected in the data fit
    # The same tail also raises the sky level; the level bias is predictable with a corona model passed
    # through the same estimator, and it is NOT caught by the consistency gate (the two errors compensate).
    corr = ex.correct_extinction(I, X, K, x_ref=x_ref, sky=S, valid=valid)
    got = ex.ring_dipole(_log_ratio(corr, C, valid), valid, g, RINGS, direction_pa_deg=ZPA)
    pred = ex.ring_dipole(np.log(np.clip(1.0 - absorbed_model * E / np.where(C > 0, C, np.nan), 1e-6, None)),
                          valid, g, RINGS, direction_pa_deg=ZPA)
    assert got[-1]["c0"] < -0.05                                # 4–5 R☉ recovered >5 % too low
    for a, b in zip(got, pred):
        assert abs(a["c0"] - b["c0"]) < 0.02, (a, b)
    rows = ex.k_nulling_dipole(_log_ratio(I - S, C, valid), X, x_ref, valid, g, RINGS, zenith_pa_deg=ZPA)
    assert ex.k_consistency(rows, K)["passed"]                  # a pass is consistency, not proof of the level


def test_consistency_gate_rejects_sky_models_that_contain_corona_or_miss_the_gradient():
    """Same gate, same thresholds: the right sky passes; three wrong ones fail."""
    g = _geo()
    X, x_ref, E, r, valid = _scene(g)
    C = _smooth_corona(r) * np.exp(-(r / 5.0) ** 6)            # sky region free of corona (declared)
    rng = np.random.default_rng(4)

    def gate(I, S):
        rows = ex.k_nulling_dipole(_log_ratio(I - S, C, valid), X, x_ref, valid, g, RINGS, zenith_pa_deg=ZPA)
        return ex.k_consistency(rows, K), rows

    flat = C / E + 400.0 + rng.normal(0, 3, C.shape)            # constant true sky
    ok, _ = gate(flat, render.sky_background(flat, valid, g, r_min_rsun=8, order=0)[0])
    assert ok["passed"], ok
    near, rows = gate(flat, float(np.median(flat[valid & (r >= 3) & (r < 4)])))   # constant sky at 3–4 R☉
    assert not near["passed"] and near["worst_sigma"] > 5
    kn = [x["k_null"] for x in rows if np.isfinite(x["k_null"])]
    assert kn[-1] > kn[0] + 0.2                                 # k_null rises outwards: sky holds corona
    lsq, _ = gate(flat, render.sky_background(flat, valid, g, r_min_rsun=3, order=1, clip_sigma=1e9)[0])
    assert not lsq["passed"]                                    # plane fitted where there is corona
    tilted = C / E + _sky_plane(g) + rng.normal(0, 3, C.shape)  # sky with a gradient
    plane, _ = gate(tilted, render.sky_background(tilted, valid, g, r_min_rsun=8, order=1)[0])
    const, _ = gate(tilted, render.sky_background(tilted, valid, g, r_min_rsun=8, order=0)[0])
    assert plane["passed"] and not const["passed"], (plane, const)


def test_dimming_k_recovers_injected_extinction_and_refuses_small_airmass_change():
    g = _geo()
    r = g.rsun_map(dtype=np.float64)
    valid = r >= 1.1
    C = _structured_corona(g)
    h1, h2 = 9.23, 8.92                                         # the Sun sets during totality
    X1 = ex.airmass_map(g, h1, zenith_pa_deg=ZPA)
    X2 = ex.airmass_map(g, h2, zenith_pa_deg=ZPA)
    x1, x2 = float(ex.kasten_young(h1)), float(ex.kasten_young(h2))
    rng = np.random.default_rng(6)
    f1 = C * 10 ** (-0.4 * K * X1) + 30 + rng.normal(0, 0.3, C.shape)
    f2 = C * 10 ** (-0.4 * K * X2) + 33 + rng.normal(0, 0.3, C.shape)   # the sky changed too
    d = ex.dimming_k(f2, f1, x2, x1, valid, g)
    assert abs(d["k"] - K) < 0.01, d
    # A 3 % drop of transparency is indistinguishable from extinction: the limit is documented, not hidden.
    dc = ex.dimming_k(0.97 * (f2 - 33) + 33, f1, x2, x1, valid, g)
    assert abs(dc["k"] - (K - 2.5 * math.log10(0.97) / (x2 - x1))) < 0.01, dc
    _raises(ValueError, lambda: ex.dimming_k(f2, f1, x1 + 0.01, x1, valid, g))


def test_solar_horizontal_and_plate_solution_route():
    try:
        import astropy.units as u
        from astropy.coordinates import TETE, SkyCoord, get_body
        from astropy.wcs import WCS
    except ImportError:
        raise unittest.SkipTest("astropy is not installed")
    site = ex.Site(42.299407, -5.02503, 798.0, pressure_hpa=930.0, temperature_c=20.0)
    t = "2026-08-12T18:29:34"
    info = ex.solar_horizontal(site, t)
    assert 0.05 < info["apparent_altitude_deg"] - info["true_altitude_deg"] < 0.12      # refraction at 9°
    assert abs(info["airmass"] - 6.053) < 0.005
    frame, loc, time = ex._altaz_frame(site, t)
    te = get_body("sun", time, loc).transform_to(TETE(obstime=time, location=loc))
    H = (time.sidereal_time("apparent", longitude=loc.lon) - te.ra).wrap_at(180 * u.deg).rad
    q = math.degrees(math.atan2(math.sin(H), math.tan(loc.lat.rad) * math.cos(te.dec.rad)
                                - math.sin(te.dec.rad) * math.cos(H)))           # parallactic angle
    assert abs(((info["zenith_pa_deg"] - q) + 180) % 360 - 180) < 0.3, (info["zenith_pa_deg"], q)
    s = 946.66 / 15.0
    geo = EclipseGeometry(shape=(120, 150), sun_xy=(74.3, 59.6), sun_radius_px=15.0, arcsec_per_px=s)
    for refraction, lo, hi in ((False, 0.0, 2e-3), (True, 1e-3, 0.03)):
        hor = ex.solar_horizontal(site, t, refraction=refraction)
        fr = ex._altaz_frame(site, t, refraction)[0]
        sun = get_body("sun", time, loc).transform_to(fr)
        c = SkyCoord(alt=sun.alt, az=sun.az, frame=fr).icrs
        w = WCS(naxis=2)
        w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
        w.wcs.crpix = [geo.sun_xy[0] + 1, geo.sun_xy[1] + 1]
        w.wcs.crval = [c.ra.deg, c.dec.deg]
        w.wcs.cd = [[-s / 3600, 0], [0, -s / 3600]]                       # north up, east left
        Xw, iw = ex.airmass_map_from_wcs(w, geo.shape, site, t, step_px=16, refraction=refraction, check_points=50)
        Xa = ex.airmass_map(geo, hor["apparent_altitude_deg"], zenith_pa_deg=hor["zenith_pa_deg"])
        diff = float(np.max(np.abs(Xw - Xa)))
        # Without refraction the two routes are the same geometry; with it they differ by the
        # differential refraction (true vs apparent offsets), as documented.
        assert lo <= diff < hi, (refraction, diff, iw)
    Xs, si = ex.airmass_map_from_site(geo, site, t)
    assert abs(Xs[int(round(geo.sun_xy[1])), int(round(geo.sun_xy[0]))] - si["airmass"]) < 5e-3


def test_extinction_command_declared_recipe():
    g = EclipseGeometry(shape=(200, 240), sun_xy=(119.4, 99.7), sun_radius_px=12.0, north_deg=0.0,
                        arcsec_per_px=946.66 / 12.0)
    r = g.rsun_map(dtype=np.float64)
    X = ex.airmass_map(g, H_SUN, zenith_image_deg=0)
    x_ref = float(ex.kasten_young(H_SUN))
    C = (_smooth_corona(r) * np.exp(-(r / 5.0) ** 6))[..., None] * np.array([1.2, 1.0, 0.6])
    noise = np.random.default_rng(8).normal(0, 1.0, C.shape)
    I = (C * 10.0 ** (-0.4 * K * (X - x_ref))[..., None] + 300.0 + noise).astype(np.float32)
    valid = r >= 1.1
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        np.save(td / "linear.npy", I)
        np.save(td / "valid.npy", valid)
        g.to_json(td / "geometry.json")
        before = hashlib.sha256((td / "linear.npy").read_bytes()).hexdigest()
        cfg = {"input": "linear.npy", "valid": "valid.npy", "geometry": "geometry.json",
               "sky": {"fit": {"r_min_rsun": 8, "order": 1}},
               "airmass": {"sun_altitude_deg": H_SUN, "zenith_image_deg": 0},
               "k": K, "x_ref": "sun", "keep_sky": True}
        (td / "ext.json").write_text(json.dumps(cfg))
        res = ex.extinction_from_config(td / "ext.json", td / "run", progress=lambda *_: None)
        net = np.load(res["files"]["corrected_net"])
        ok = valid & (r < 3)
        assert np.median(np.abs(net[ok] / C[ok] - 1)) < 0.005         # per pixel the noise dominates
        prof = ex.ring_dipole(np.log(np.where(net[..., 1] > 0, net[..., 1], np.nan) / C[..., 1]), valid, g,
                              [(1.2, 2.0), (2.0, 3.0), (3.0, 4.0)], direction_pa_deg=0.0)
        assert all(abs(p["c0"]) < 0.01 and abs(p["along"]) < 0.01 for p in prof), prof
        assert np.isnan(net[~valid]).all() and res["gates"]["nothing_outside_data"]
        withsky = np.load(res["files"]["corrected_with_sky"])
        sky = np.load(res["files"]["sky"])
        assert np.allclose(withsky[valid] - sky[valid], net[valid], atol=1e-2)
        rec = json.loads(Path(res["receipt"]).read_text())
        assert rec["parameters"]["formula"].startswith("(I - sky)") and rec["parameters"]["x_ref"] == x_ref
        assert hashlib.sha256((td / "linear.npy").read_bytes()).hexdigest() == before   # input untouched
        _raises(FileExistsError, lambda: ex.extinction_from_config(td / "ext.json", td / "run"))
        for broken in ({k: v for k, v in cfg.items() if k != "x_ref"}, dict(cfg, extra=1),
                       dict(cfg, sky={"fit": {"r_min_rsun": 8}, "value": 3})):
            (td / "bad.json").write_text(json.dumps(broken))
            _raises(ValueError, lambda: ex.extinction_from_config(td / "bad.json", td / "never"))
            assert not (td / "never").exists()
        from ael.__main__ import main
        assert main(["extinction", "--config", str(td / "ext.json"), "--out", str(td / "cli")]) == 0
        assert (td / "cli" / "receipt.json").is_file()


def test_sky_background_keeps_noise_free_data():
    """Regression: with noise-free data the robust scale is 0 and a strict "<" clipped every pixel,
    returning a zero sky without warning."""
    g = EclipseGeometry(shape=(200, 240), sun_xy=(119.4, 99.7), sun_radius_px=12.0)
    model, info = render.sky_background(np.full(g.shape, 300.0, np.float32), None, g, r_min_rsun=8, order=1)
    assert info["n_used"] > 1000 and np.allclose(model, 300.0, atol=1e-3)


def test_correction_by_row_blocks_for_every_sky_form():
    """Regression: a constant sky given as one value per channel was sliced by rows like a map, so every
    block after the first got an empty sky and the call failed on any image taller than ``block_rows``.
    Every sky form must give the same, exact result whatever the block size."""
    rng = np.random.default_rng(11)
    h, w = 600, 40                                   # taller than the default block of 512 rows
    yy, xx = np.mgrid[0:h, 0:w]
    X = 5.7 + 0.7 * yy / h + 0.01 * xx / w
    x_ref = 6.05
    E = 10.0 ** (0.4 * K * (X - x_ref))              # written out here, independently of ex.extinction_factor
    grey = rng.uniform(100.0, 5000.0, (h, w))
    rgb = grey[..., None] * np.array([1.2, 1.0, 0.6])
    plane = 300.0 + 0.05 * yy - 0.2 * xx
    cases = [("scalar, grey", grey, 300.0), ("2-D map, grey", grey, plane),
             ("scalar, RGB", rgb, 300.0), ("one value per channel", rgb, [300.0, 310.0, 320.0]),
             ("2-D map, RGB", rgb, plane), ("3-D map", rgb, plane[..., None] * np.array([1.0, 1.03, 1.07]))]
    for label, truth, sky in cases:
        S = np.asarray(sky, np.float64)
        Sfull = np.broadcast_to(S[..., None] if (S.ndim == 2 and truth.ndim == 3) else S, truth.shape)
        I = truth / (E[..., None] if truth.ndim == 3 else E) + Sfull
        ref = None
        for block_rows in (512, 64, 7, h):          # the default, small, not a divisor of h, a single block
            out = ex.correct_extinction(I, X, K, x_ref=x_ref, sky=sky, block_rows=block_rows)
            assert out.shape == truth.shape and out.dtype == np.float32, (label, block_rows)
            assert np.max(np.abs(out / truth - 1.0)) < 1e-5, (label, block_rows)
            ref = out if ref is None else ref
            assert np.max(np.abs(out / ref - 1.0)) < 1e-6, (label, block_rows)
            kept = ex.correct_extinction(I, X, K, x_ref=x_ref, sky=sky, block_rows=block_rows, keep_sky=True)
            assert np.allclose(kept - Sfull, out, rtol=1e-5, atol=1e-2), (label, block_rows)
    # Skies that do not fit the image are refused before any work.
    for sky in (plane[:-1], np.zeros((h, w, 2)), np.zeros((1, h, w, 3)), [300.0, 310.0], [300.0, np.nan, 320.0],
                np.nan, ["300", "310", "320"]):
        _raises(ValueError, lambda: ex.correct_extinction(rgb, X, K, x_ref=x_ref, sky=sky, block_rows=64))
    _raises(ValueError, lambda: ex.correct_extinction(grey, X, K, x_ref=x_ref, sky=[300.0, 310.0, 320.0]))
    _raises(ValueError, lambda: ex.correct_extinction(grey, X, K, x_ref=x_ref, sky=rgb))


def test_extinction_command_sky_forms_and_refusals_before_writing():
    """Regression: a 2-D sky array with an RGB stack failed after the output directory had been created,
    leaving it empty and blocking a re-run.  Every sky form must work, and every refusal must come before
    anything is written."""
    import contextlib
    import io as _io

    from ael.__main__ import main

    g = EclipseGeometry(shape=(200, 240), sun_xy=(119.4, 99.7), sun_radius_px=12.0, north_deg=0.0,
                        arcsec_per_px=946.66 / 12.0)
    r = g.rsun_map(dtype=np.float64)
    X = ex.airmass_map(g, H_SUN, zenith_image_deg=0)
    x_ref = float(ex.kasten_young(H_SUN))
    C = (_smooth_corona(r) * np.exp(-(r / 5.0) ** 6))[..., None] * np.array([1.2, 1.0, 0.6])
    h, w = g.shape
    yy, xx = np.mgrid[0:h, 0:w]
    plane = 300.0 + 0.1 * yy - 0.05 * xx
    sky3 = plane[..., None] * np.array([1.0, 1.05, 0.9])
    valid = r >= 1.1
    ok = valid & (r < 4)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        g.to_json(td / "geometry.json")
        np.save(td / "valid.npy", valid)
        np.save(td / "sky2d.npy", plane.astype(np.float32))
        np.save(td / "sky3d.npy", sky3.astype(np.float32))
        np.save(td / "sky_bad.npy", plane[:-1].astype(np.float32))
        base = {"geometry": "geometry.json", "valid": "valid.npy",
                "airmass": {"sun_altitude_deg": H_SUN, "zenith_image_deg": 0}, "k": K, "x_ref": "sun",
                "keep_sky": True}
        skies = [("2-D array", plane, {"array": "sky2d.npy"}), ("3-D array", sky3, {"array": "sky3d.npy"}),
                 ("one value per channel", np.array([300.0, 310.0, 320.0]), {"value": [300.0, 310.0, 320.0]}),
                 ("scalar", np.array(300.0), {"value": 300.0})]
        for i, (label, S, spec) in enumerate(skies):
            Sfull = np.broadcast_to(S[..., None] if S.ndim == 2 else S, C.shape)
            np.save(td / f"linear{i}.npy", (C * 10.0 ** (-0.4 * K * (X - x_ref))[..., None] + Sfull).astype(np.float32))
            (td / f"ext{i}.json").write_text(json.dumps(dict(base, input=f"linear{i}.npy", sky=spec)))
            res = ex.extinction_from_config(td / f"ext{i}.json", td / f"run{i}", progress=lambda *_: None)
            net = np.load(res["files"]["corrected_net"])
            sky = np.load(res["files"]["sky"])
            assert sky.shape == C.shape and np.allclose(sky, Sfull, rtol=1e-6), label
            assert np.max(np.abs(net[ok] / C[ok] - 1.0)) < 1e-4, label
            withsky = np.load(res["files"]["corrected_with_sky"])
            assert np.allclose(withsky[valid] - sky[valid], net[valid], atol=1e-2), label
        # Refusals: a sky of the wrong shape, a sky vector or a k vector of the wrong length.  Nothing written.
        for j, change in enumerate(({"sky": {"array": "sky_bad.npy"}}, {"sky": {"value": [300.0, 310.0]}},
                                    {"k": [0.3, 0.4]})):
            bad = dict(base, input="linear0.npy", sky={"array": "sky2d.npy"})
            bad.update(change)
            (td / f"bad{j}.json").write_text(json.dumps(bad))
            _raises(ValueError, lambda: ex.extinction_from_config(td / f"bad{j}.json", td / f"never{j}",
                                                                  progress=lambda *_: None))
            assert not (td / f"never{j}").exists(), change
            with contextlib.redirect_stderr(_io.StringIO()):
                _raises(SystemExit, lambda: main(["extinction", "--config", str(td / f"bad{j}.json"),
                                                  "--out", str(td / f"never_cli{j}")]))
            assert not (td / f"never_cli{j}").exists(), change
        # An existing output directory is refused before any work, and left as it was.
        (td / "taken").mkdir()
        (td / "taken" / "keep.txt").write_text("x")
        _raises(FileExistsError, lambda: ex.extinction_from_config(td / "ext0.json", td / "taken"))
        assert [p.name for p in (td / "taken").iterdir()] == ["keep.txt"]
