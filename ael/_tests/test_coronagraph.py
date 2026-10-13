"""Known-truth tests for the comparison with coronagraphs.  Synthetic scenes and published constants only.

The numbers checked against the 2026 work (the 90.43° plate, SOHO's larger Sun, the two LASCO C2
calibrations, the ratio band) are the ones research notes 180 and 185 report.
"""
import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from ael import coronagraph as cg
from ael.geometry import EclipseGeometry
from ael.synthetic import SyntheticScene


def _raises(error, fn):
    try:
        fn()
    except error:
        return
    raise AssertionError(f"expected {error.__name__}")


STREAMERS = ((40.0, 18.0, 2.5), (130.0, 25.0, 1.8), (230.0, 15.0, 2.2), (300.0, 20.0, 1.5))
OTHER_STREAMERS = ((85.0, 22.0, 2.0), (175.0, 16.0, 2.4), (265.0, 24.0, 1.6), (345.0, 14.0, 2.0))


def _scene(seed=7, north_deg=0.0, R=60.0, streamers=STREAMERS):
    return SyntheticScene(sun_radius_px=R, seed=seed, n_rays=260, sky_level=0.0, sky_gradient=(0, 0),
                          psf_sigma_px=0.0, north_deg=north_deg, streamers=streamers)


def _image(shape, sun_xy, R, north_deg, seed=7, scale=1.0, streamers=STREAMERS, noise=0.0):
    sc = _scene(seed, north_deg, R, streamers)
    img = sc.radiance(shape, sun_xy, with_moon=False).astype(np.float64) * scale
    if noise:
        img = img * (1.0 + noise * np.random.default_rng(seed + 100).standard_normal(img.shape))
    geo = EclipseGeometry(shape=shape, sun_xy=sun_xy, sun_radius_px=R, north_deg=north_deg)
    return img, geo


RADII = np.geomspace(1.1, 3.6, 120)
RINGS = [(1.2, 1.6), (1.6, 2.2), (2.2, 3.2)]


def test_rsun_arcsec_for_each_observer():
    assert abs(cg.rsun_arcsec(1.0) - 959.23) < 0.01
    earth, soho = cg.rsun_arcsec(1.01328), cg.rsun_arcsec(1.002097)
    assert abs(earth - 946.66) < 0.01 and abs(soho - 957.22) < 0.01
    assert 0.0110 < soho / earth - 1 < 0.0114          # SOHO sees the Sun 1.1 % larger


def test_affine_plate_exact_inverse_and_the_perpendicular_trap():
    R = 440.0
    a = math.radians(0.43)                            # north and east 90.43° apart, as on the 2026 plate
    n = np.array([0.0, -1.0]) * R
    e = np.array([-math.cos(a), math.sin(a)]) * R      # east to the left, tilted by 0.43°
    fr = cg.SolarFrame((3976.0, 2551.0), n, e)
    assert abs(fr.axis_angle_deg - 90.43) < 1e-9
    pa = np.linspace(0, 359.5, 720)
    for r in (1.0, 6.0):
        x, y = fr.to_pixels(np.full_like(pa, r), pa)
        r2, p2 = fr.to_solar(x, y)
        assert np.max(np.abs(r2 - r)) < 1e-12 and np.max(np.abs((p2 - pa + 180) % 360 - 180)) < 1e-9
        # the trap: treat east as perpendicular to north (a pure rotation) and map back to pixels
        e_perp = np.array([-1.0, 0.0]) * R
        th = np.radians(pa)
        xw = fr.cx + r * (np.cos(th) * n[0] + np.sin(th) * e_perp[0])
        yw = fr.cy + r * (np.cos(th) * n[1] + np.sin(th) * e_perp[1])
        err = np.hypot(xw - x, yw - y).max()
        assert (3.0 < err < 3.6) if r == 1.0 else (19.0 < err < 21.0), err   # 3.3 px at the limb, ~20 px at 6 R☉


def test_frame_from_geometry_uses_the_p_angle():
    P = 15.191
    for mirrored in (False, True):
        geo = EclipseGeometry(shape=(300, 400), sun_xy=(201.3, 148.7), sun_radius_px=50.0, north_deg=20.0,
                              mirrored=mirrored)
        fr = cg.SolarFrame.from_geometry(geo, P)
        r, pa = fr.solar_maps(geo.shape)
        assert np.allclose(r, geo.rsun_map(dtype=np.float64), atol=1e-9)
        d = (pa - (geo.pa_map(dtype=np.float64) - P) + 180) % 360 - 180
        assert np.nanmax(np.abs(d[r > 0.05])) < 1e-6      # solar PA = celestial PA − P


def test_frame_from_helioprojective_header():
    try:
        from astropy.io import fits
        from astropy.wcs import WCS
    except ImportError:
        raise unittest.SkipTest("astropy not installed")
    h = fits.Header()
    h["NAXIS"], h["NAXIS1"], h["NAXIS2"] = 2, 1024, 1024
    h["CTYPE1"], h["CTYPE2"] = "HPLN-TAN", "HPLT-TAN"
    h["CUNIT1"], h["CUNIT2"] = "arcsec", "arcsec"
    h["CRPIX1"], h["CRPIX2"] = 512.5, 520.25
    h["CRVAL1"], h["CRVAL2"] = 0.0, 0.0
    h["CDELT1"], h["CDELT2"] = 5.643, 5.643
    h["CROTA2"] = 12.0
    h["RSUN_OBS"] = 946.66
    fr = cg.SolarFrame.from_wcs_header(h)
    assert abs(fr.cx - 511.5) < 1e-6 and abs(fr.cy - 519.25) < 1e-6
    assert abs(fr.rsun_px - 946.66 / 5.643) < 3e-3 and abs(fr.axis_angle_deg - 90.0) < 1e-6   # TAN: ~1e-5
    w = WCS(h)
    for pa in (0.0, 90.0, 200.0):                     # 1 R☉ towards solar north (+HPLT) and east (−HPLN)
        lon = -946.66 * math.sin(math.radians(pa)) / 3600.0
        lat = 946.66 * math.cos(math.radians(pa)) / 3600.0
        xw, yw = w.world_to_pixel_values(lon, lat)
        x, y = fr.to_pixels(1.0, pa)
        assert math.hypot(x - xw, y - yw) < 0.02
    soho = cg.SolarFrame.from_wcs_header(h, rsun_arcsec_=957.22)
    assert abs(soho.rsun_px / fr.rsun_px - 957.22 / 946.66) < 1e-9


def _unrolled_pair(north_ref_true, north_ref_told, seed_ref=7, scale_ref=1.0, streamers_ref=STREAMERS):
    ours, g_o = _image((520, 560), (283.4, 255.1), 60.0, 20.0, noise=0.02)
    ref, g_r = _image((380, 380), (190.2, 187.7), 42.0, north_ref_true, seed=seed_ref, scale=scale_ref,
                      streamers=streamers_ref, noise=0.10)      # a noisier, coarser instrument
    f_o = cg.SolarFrame.from_geometry(g_o, 0.0)       # synthetic scenes: solar and celestial north coincide
    f_r = cg.SolarFrame.from_geometry(EclipseGeometry(shape=g_r.shape, sun_xy=g_r.sun_xy, sun_radius_px=42.0,
                                                      north_deg=north_ref_told), 0.0)
    return ours, f_o, ref, f_r


def test_structure_agreement_rotation_and_null():
    ours, f_o, ref, f_r = _unrolled_pair(-35.0, -35.0)
    u_o = cg.unroll(ours, f_o, RADII, supersample=2)
    u_r = cg.unroll(ref, f_r, RADII, supersample=2)
    res = cg.compare_structure(u_o, u_r, RINGS)
    for x in res:
        assert x["rho_0"] > 0.9 and x["rho_0"] > x["null_max"] + 0.2, x
        assert abs(x["shift_deg"]) <= 0.5
        assert x["fine_detail"]["rho_0"] > 0.8 and x["fine_detail"]["rho_0"] > x["fine_detail"]["null_max"], x
    # the reference sees every feature 5° less far round: the best rotation is +5°
    ours, f_o, ref, f_r = _unrolled_pair(-30.0, -35.0)
    rot = cg.compare_structure(cg.unroll(ours, f_o, RADII, supersample=2), cg.unroll(ref, f_r, RADII, supersample=2),
                               RINGS)
    for x in rot:
        assert abs(x["shift_deg"] - 5.0) <= 0.5 and x["rho_best"] > 0.9 and x["rho_0"] < x["rho_best"] - 0.1, x


def test_structure_negative_control_and_blindness_to_radial_tone():
    ours, f_o, ref, f_r = _unrolled_pair(-35.0, -35.0, seed_ref=8, streamers_ref=OTHER_STREAMERS)
    u_o = cg.unroll(ours, f_o, RADII, supersample=2)
    res = cg.compare_structure(u_o, cg.unroll(ref, f_r, RADII, supersample=2), RINGS)
    for x in res:                                   # another corona: no agreement beyond the null
        assert x["rho_0"] < x["null_max"] and x["fine_detail"]["rho_0"] < x["fine_detail"]["null_max"], x
    # same streamers, other rays: whole profiles still agree (the broad shape); the fine detail much less
    ours, f_o, ref, f_r = _unrolled_pair(-35.0, -35.0, seed_ref=8)
    same = cg.compare_structure(u_o, cg.unroll(ref, f_r, RADII, supersample=2), RINGS)
    for x in same:
        assert x["rho_0"] > 0.8 and x["fine_detail"]["rho_0"] < x["rho_0"] - 0.25, x
    # a radial tone curve a(r)·I + b(r) leaves the test unchanged: it measures angles, not brightness
    geo = EclipseGeometry(shape=ours.shape, sun_xy=(283.4, 255.1), sun_radius_px=60.0, north_deg=20.0)
    r = geo.rsun_map(dtype=np.float64)
    toned = (0.3 + r ** 2) * ours + 50.0 * r
    ref_ok, f_ok = _unrolled_pair(-35.0, -35.0)[2:]
    u_ref = cg.unroll(ref_ok, f_ok, RADII, supersample=2)
    a = cg.compare_structure(u_o, u_ref, RINGS)
    b = cg.compare_structure(cg.unroll(toned, f_o, RADII, supersample=2), u_ref, RINGS)
    for x, y in zip(a, b):
        assert abs(x["rho_0"] - y["rho_0"]) < 0.01


def test_dark_sector_takes_only_the_seeded_run_and_wraps():
    rng = np.random.default_rng(1)
    pa = np.arange(720) * 0.5
    radii = np.linspace(2.3, 6.3, 40)
    a = rng.normal(0, 0.1, (40, 720))
    a[:, (pa >= 300) & (pa < 340)] = -1.0          # pylon
    a[:, (pa >= 100) & (pa < 120)] = -1.0          # a coronal hole: dark but not the pylon
    m = cg.dark_sector(a, radii, (2.5, 6.0), 320.0, dilate_deg=4.0)
    assert m[(pa >= 300) & (pa < 340)].all() and m[(pa >= 296) & (pa < 344)].all()
    assert not m[(pa >= 100) & (pa < 120)].any() and m.sum() == (344 - 296) * 2
    b = rng.normal(0, 0.1, (40, 720))
    b[:, (pa >= 350) | (pa < 10)] = -1.0           # a run across 0°, seeded on either side
    for seed in (5.0, 355.0):
        mb = cg.dark_sector(b, radii, (2.5, 6.0), seed, dilate_deg=0.0)
        assert mb[(pa >= 350) | (pa < 10)].all() and mb.sum() == 40
    assert not cg.dark_sector(a, radii, (2.5, 6.0), 200.0).any()     # seed not dark: nothing masked
    c = rng.normal(0, 0.1, (40, 720))
    c[:, (pa >= 100) & (pa < 330)] = -1.0          # a run reaching 220° past the seed
    mc = cg.dark_sector(c, radii, (2.5, 6.0), 110.0, dilate_deg=0.0)
    assert mc.sum() == 460 and mc[(pa >= 100) & (pa < 330)].all()
    _raises(ValueError, lambda: cg.dark_sector(a, radii, (2.5, 6.0), 320.0, dilate_deg=-1.0))


def test_low_harmonics_removed_rays_kept():
    pa = np.radians(np.arange(720) * 0.5)
    rng = np.random.default_rng(2)
    rays = np.zeros(720)
    for c in rng.uniform(0, 2 * np.pi, 40):
        d = np.angle(np.exp(1j * (pa - c)))
        rays += np.exp(-0.5 * (d / np.radians(1.0)) ** 2)
    row = 1.0 + 0.4 * np.cos(2 * pa) + 0.2 * np.sin(3 * pa) + 0.3 * rays
    data = np.vstack([row, row])
    data[1, 100:140] = np.nan
    out = cg.subtract_low_harmonics(data, 3)
    r0 = rays - rays.mean()
    assert np.corrcoef(out[0], r0)[0, 1] > 0.98
    assert abs(np.nanmean(out[0] * np.cos(2 * pa))) < 2e-3 and np.isnan(out[1, 100:140]).all()


def test_thomson_polarization_regression_and_limits():
    rho = np.array([1.1, 1.2, 1.4, 1.7])
    p = cg.thomson_polarization(rho)
    assert np.allclose(p, [0.301738, 0.381844, 0.475112, 0.537091], atol=2e-5), p
    from scipy.integrate import quad                 # the line of sight to infinity, by another quadrature
    ba = cg.DENSITY_MODELS["baumbach_allen"]

    def integrand(z, rho, which):
        r = math.hypot(rho, z)
        A, B, C, D = cg.van_de_hulst_abcd(r)
        return float(ba(r) * ((0.44 * C + 0.56 * D) if which == "t" else (rho / r) ** 2 * (0.44 * A + 0.56 * B)))
    for rho_ in (2.0, 6.0):
        it = quad(integrand, 0, np.inf, args=(rho_, "t"), limit=400, epsrel=1e-10)[0]
        pb = quad(integrand, 0, np.inf, args=(rho_, "p"), limit=400, epsrel=1e-10)[0]
        tb, pb2 = cg.k_corona_tb_pb(rho_)
        assert abs((pb2 / tb) / (pb / (2 * it - pb)) - 1) < 1e-5
    grid = cg.thomson_polarization(np.linspace(1.05, 1.8, 40))
    assert np.all(np.diff(grid) > 0) and np.all((grid > 0) & (grid < 1))
    assert np.isnan(cg.thomson_polarization(np.array([1.0, 9.0]))).all()     # outside the table: nothing
    A, B, C, D = cg.van_de_hulst_abcd(1000.0)
    assert abs(A / (2 * C - A) - 1.0) < 1e-3        # far from the Sun, 90° scattering is fully polarised
    cal = cg.thomson_polarization(np.array([1.3]), lambda r: 2.99 * r ** -16 + 1.55 * r ** -6 + 0.036 * r ** -1.5)
    assert abs(cal[0] - cg.thomson_polarization(np.array([1.3]))[0]) < 3e-4


def test_kcor_total_adds_the_f_corona():
    r = np.linspace(1.15, 1.7, 12)
    K = cg.k_corona_van_de_hulst_1950(r)
    pB = K * cg.thomson_polarization(r)
    tot = cg.kcor_total_msb(pB, r)
    F = cg.f_corona_van_de_hulst_1950(r)
    assert np.allclose(tot, K + F, rtol=1e-9, atol=0)
    frac = F / (K + F)                               # what pB/p alone misses: grows outwards
    assert np.all(np.diff(frac) > 0) and 0.03 < frac[0] < frac[-1] < 0.35
    t = cg.k_band_transfer(1.3, 0.62, 0.48)
    assert abs(t - 0.9926) < 3e-4                     # independent quadrature by the 1.3.0 verifier
    assert cg.k_band_transfer(1.3, 0.55, 0.55) == 1.0
    assert abs(t * cg.k_band_transfer(1.3, 0.48, 0.62) - 1) < 1e-12


def test_lasco_c2_calibrations_differ_in_level():
    m = cg.mjd("2026-08-12T18:24:00Z")
    assert abs(m - 61264.7667) < 1e-3
    ch = cg.lasco_c2_msb_per_dn(m, "colaninno_howard_2015")
    ss = cg.lasco_c2_msb_per_dn("2026-08-12T18:24:00", "solarsoft")
    assert abs(ch / 7.589e-12 - 1) < 1e-3 and abs(ss / 6.562e-12 - 1) < 1e-3
    assert 0.130 < 1 - ss / ch < 0.140 and abs(ch / ss - 1 - 0.1565) < 0.002
    m13 = cg.mjd("2013-07-02T00:00:00")
    ch13, ss13 = cg.lasco_c2_msb_per_dn(m13), cg.lasco_c2_msb_per_dn(m13, "solarsoft")
    assert abs(ch13 / 7.40e-12 - 1) < 0.005 and abs(ch13 / ss13 - 1 - 0.167) < 0.003   # already there in 2013
    _raises(ValueError, lambda: cg.lasco_c2_msb_per_dn(m, "made_up"))
    assert cg.lasco_c2_msb_per_dn(np.int64(61264)) == cg.lasco_c2_msb_per_dn(61264.0)
    h = dict(SUMCOL=2, SUMROW=2, LEBXSUM=1, LEBYSUM=0)
    assert cg.lasco_c2_summing(h) == 4 and cg.lasco_c2_summing({}) == 1
    assert abs(cg.lasco_c2_msb_per_dn(m, summing=4) * 4 / ch - 1) < 1e-12        # a summed pixel holds 4 pixels' DN
    pol = cg.lasco_c2_msb_per_dn(61264.0, "solarsoft", polarizer="+60 deg")
    assert abs(pol / 2.5981e-11 - 1) < 2e-4                                       # SolarSoft: factor / 0.25256
    _raises(ValueError, lambda: cg.lasco_c2_msb_per_dn(m, polarizer="0 deg"))     # C&H: Clear only
    _raises(ValueError, lambda: cg.lasco_c2_msb_per_dn(m, filter_name="Blue"))
    _raises(ValueError, lambda: cg.lasco_c2_msb_per_dn(m, summing=0))


def test_cell_medians_and_level_ratios_recover_a_known_scale():
    a, g_a = _image((520, 560), (283.4, 255.1), 60.0, 20.0)
    b, g_b = _image((380, 380), (190.2, 187.7), 42.0, -35.0, scale=1.3)
    f_a, f_b = cg.SolarFrame.from_geometry(g_a, 0.0), cg.SolarFrame.from_geometry(g_b, 0.0)
    rings = [(1.2, 1.5), (1.5, 2.0), (2.0, 3.0)]
    ca = cg.cell_medians(a, f_a, rings)
    band = np.abs(g_a.rsun_map() - 1.6) < 0.03       # an excluded band: its cells lose pixels, nothing is filled
    cb = cg.cell_medians(b, f_b, rings)
    for x in cg.level_ratios(cb, ca):
        assert abs(x["ratio_of_medians"] - 1.3) < 0.04 and abs(x["median_of_ratios"] - 1.3) < 0.04, x
    ce = cg.cell_medians(a, f_a, [(1.58, 1.62)], exclude=band)
    assert np.isnan(ce).all()
    spot = np.zeros(a.shape, bool)
    spot[255, 283 + 105] = True                       # one pixel at r = 1.75, PA ≈ 290°: its whole cell goes
    cd = cg.cell_medians(a, f_a, rings, drop_touching=spot)
    lost = np.isfinite(ca) & ~np.isfinite(cd)
    assert lost.sum() == 1 and lost[1].sum() == 1 and np.array_equal(cd[np.isfinite(cd)], ca[np.isfinite(cd)])
    _raises(ValueError, lambda: cg.cell_medians(a, f_a, [(1.2, 2.0), (1.5, 2.2)]))   # overlapping rings
    tiny = np.zeros((5, 5))
    tiny[1, 2], tiny[2, 1] = 1.0, 3.0                # PA 0 (up) and PA 90 (left): two pixels in the first 180° cell
    f_t = cg.SolarFrame((2.0, 2.0), (0.0, -1.0), (-1.0, 0.0))
    ct = cg.cell_medians(tiny, f_t, [(0.9, 1.1)], cell_deg=180.0)
    assert ct[0, 0] == 2.0 and ct[0, 1] == 0.0      # the median of an even count, not its upper element
    holed = a.copy()
    holed[:, :280] = np.nan                           # half the field missing: those cells are NaN
    ch = cg.cell_medians(holed, f_a, rings)
    assert 100 < np.isfinite(ch[0]).sum() < 260
    assert cg.level_ratios(ch[:, :10], ca[:, :10], min_cells=20)[0]["n_cells"] < 20


def test_ratio_band_is_asymmetric():
    lo, hi = cg.ratio_band(0.20, 0.11)
    assert abs(lo - 1 / 1.11) < 1e-12 and abs(hi - 1.25) < 1e-12      # 0.90–1.25, not 0.80–1.11
    _raises(ValueError, lambda: cg.ratio_band(1.0, 0.1))


def test_coronagraph_command_declared_recipe():
    ours, f_o, ref, f_r = _unrolled_pair(-35.0, -35.0)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        np.save(td / "ours.npy", np.dstack([ours, ours, ours]).astype(np.float32))
        np.save(td / "ref.npy", ref.astype(np.float32))
        EclipseGeometry(shape=ours.shape, sun_xy=(283.4, 255.1), sun_radius_px=60.0,
                        north_deg=20.0).to_json(td / "ours_geometry.json")
        cfg = dict(radii_rsun=dict(min=1.1, max=3.6, n=120, spacing="log"), pa_step_deg=0.5,
                   ours=dict(image="ours.npy", channel="luminance", supersample=2,
                             frame=dict(geometry="ours_geometry.json", p_angle_deg=0.0)),
                   references=[dict(name="Synthetic C2", image="ref.npy", supersample=2, frame=f_r.to_dict(),
                                    rings=[[1.6, 2.2], [2.2, 3.2]])])
        (td / "recipe.json").write_text(json.dumps(cfg))
        out = cg.structure_from_config(td / "recipe.json", td / "out", progress=lambda *_: None)
        rec = json.loads((td / "out" / "coronagraph_structure.json").read_text())
        assert all(x["rho_0"] > 0.9 for x in rec["references"][0]["rings"])
        assert (td / "out" / "unrolled_ours_over_Synthetic_C2.png").is_file() and out["results"][0]["rings"]
        _raises(FileExistsError, lambda: cg.structure_from_config(td / "recipe.json", td / "out"))
        bad = dict(cfg, ours=dict(cfg["ours"], frame=dict(geometry="ours_geometry.json")))
        (td / "bad.json").write_text(json.dumps(bad))
        _raises(ValueError, lambda: cg.structure_from_config(td / "bad.json", td / "out2"))
        (td / "bad2.json").write_text(json.dumps(dict(cfg, colour="gold")))
        _raises(ValueError, lambda: cg.structure_from_config(td / "bad2.json", td / "out3"))
        assert not (td / "out2").exists() and not (td / "out3").exists()


def test_celestial_plate_frame_uses_p_and_east():
    N = np.array([0.10, -0.45])                       # px per arcsec towards celestial north and east (affine)
    E = np.array([-0.46, -0.08])
    c, R, P = (812.3, 640.9), 946.66, 15.191
    fr = cg.SolarFrame.from_celestial_plate(c, R, N, E, P)
    th = np.array([0.0, 37.0, 90.0, 200.0, 315.0])
    x, y = fr.to_pixels(2.0, th)
    t = np.radians(th + P)                            # solar PA θ is celestial PA θ + P, at 2 R☉
    xs = c[0] + 2 * R * (np.cos(t) * N[0] + np.sin(t) * E[0])
    ys = c[1] + 2 * R * (np.cos(t) * N[1] + np.sin(t) * E[1])
    assert np.allclose(x, xs, atol=1e-9) and np.allclose(y, ys, atol=1e-9)
    geo = EclipseGeometry(shape=(1300, 1600), sun_xy=c, sun_radius_px=440.0, north_deg=-30.0)
    a = math.radians(-30.0)                           # the same, for an orthogonal plate: agrees with from_geometry
    s = 440.0 / R
    fo = cg.SolarFrame.from_celestial_plate(c, R, (s * math.sin(a), -s * math.cos(a)),
                                            (-s * math.cos(a), -s * math.sin(a)), P)
    fg = cg.SolarFrame.from_geometry(geo, P)
    assert np.allclose(fo.M, fg.M, atol=1e-9)


def test_van_de_hulst_1950_published_constants():
    r = np.array([1.2, 2.0, 4.0])                     # eqs. (5)–(7), written out here
    kmax = (355.6 * r ** -17 + 177.8 * r ** -7 + 0.708 * r ** -2.5) * 1e-8
    kmin = (200.0 * r ** -17 + 100.0 * r ** -7 + 0.398 * r ** -2.5) * 1e-8
    f = (14.86 * r ** -7 + 4.99 * r ** -2.5) * 1e-8
    assert np.allclose(cg.k_corona_van_de_hulst_1950(r), kmax, rtol=1e-12, atol=0)    # atol=0: values are ~1e-8
    assert np.allclose(cg.k_corona_van_de_hulst_1950(r, "min"), kmin, rtol=1e-12, atol=0)
    assert np.allclose(cg.f_corona_van_de_hulst_1950(r), f, rtol=1e-12, atol=0)
    _raises(ValueError, lambda: cg.k_corona_tb_pb(1.0))


def test_scaled_frame_and_rsun_from_dsun():
    fr = cg.SolarFrame((101.3, 77.6), (3.0, -40.0), (-40.0, -3.0))
    g = fr.scaled(0.5)
    x, y = fr.to_pixels(1.7, 123.0)
    x2, y2 = g.to_pixels(1.7, 123.0)
    assert abs(x2 - ((x + 0.5) * 0.5 - 0.5)) < 1e-12 and abs(y2 - ((y + 0.5) * 0.5 - 0.5)) < 1e-12
    try:
        from astropy.io import fits
    except ImportError:
        raise unittest.SkipTest("astropy not installed")
    h = fits.Header()
    h["NAXIS"], h["NAXIS1"], h["NAXIS2"] = 2, 512, 512
    h["CTYPE1"], h["CTYPE2"], h["CUNIT1"], h["CUNIT2"] = "HPLN-TAN", "HPLT-TAN", "arcsec", "arcsec"
    h["CRPIX1"], h["CRPIX2"], h["CRVAL1"], h["CRVAL2"], h["CDELT1"], h["CDELT2"] = 256.5, 256.5, 0.0, 0.0, 4.0, 4.0
    h["DSUN_OBS"] = 1.01328 * cg.AU_KM * 1000.0      # metres, as in FITS
    assert abs(cg.SolarFrame.from_wcs_header(h).rsun_px - 946.66 / 4.0) < 3e-3


def test_unroll_supersampling_is_centred_and_nrgf_rows_are_unit():
    geo = EclipseGeometry(shape=(401, 401), sun_xy=(200.0, 200.0), sun_radius_px=50.0, north_deg=0.0)
    fr = cg.SolarFrame.from_geometry(geo, 0.0)
    r, pa = fr.solar_maps(geo.shape)
    d = (pa - 100.0 + 180) % 360 - 180
    img = np.where(r > 1.0, 1.0 + np.exp(-0.5 * (d / 0.3) ** 2), np.nan)     # one narrow ray at PA 100°
    u = cg.unroll(img, fr, np.linspace(2.0, 3.0, 11), supersample=4)
    prof = np.nanmean(u.data, axis=0)
    i = int(np.argmax(prof))
    assert u.pa[i] == 100.0 and abs(prof[i - 1] - prof[i + 1]) < 0.02 * (prof[i] - 1)
    rng = np.random.default_rng(4)
    z = cg.nrgf_rows(rng.lognormal(0, 0.5, (30, 720)) * np.linspace(1, 50, 30)[:, None])
    assert np.allclose(np.nanmedian(z, axis=1), 0, atol=1e-12)
    assert np.allclose(1.4826 * np.nanmedian(np.abs(z), axis=1), 1, atol=1e-9)


def test_circular_correlation_flags_the_edge_of_the_search():
    pa = np.radians(np.arange(720) * 0.5)
    p = np.cos(2 * pa) + 0.3 * np.sin(5 * pa)
    edge = cg.circular_correlation(p, np.roll(p, 40), max_shift_deg=10.0)      # 20° apart: beyond ±10°
    inside = cg.circular_correlation(p, np.roll(p, 8), max_shift_deg=10.0)     # 4° apart
    assert edge["at_search_edge"] and abs(edge["shift_deg"]) == 10.0
    assert not inside["at_search_edge"] and inside["shift_deg"] == -4.0


def test_coronagraph_command_uses_p_bin_valid_and_the_pylon():
    P = 15.0
    sc = _scene(7, 20.0 - P, 60.0)                   # solar north drawn P degrees east of celestial north (20°)
    ours = sc.radiance((520, 560), (283.4, 255.1), with_moon=False).astype(np.float64)
    ref, g_r = _image((380, 380), (190.2, 187.7), 42.0, -35.0, noise=0.05)
    f_r = cg.SolarFrame.from_geometry(g_r, 0.0)
    _, pa_r = f_r.solar_maps(ref.shape)
    pyl = ref.copy()
    pyl[(pa_r >= 120) & (pa_r < 150)] *= 0.05      # an occulter pylon, across a bright streamer, on a copy
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        np.save(td / "ours.npy", ours.astype(np.float32))
        np.save(td / "ref.npy", ref.astype(np.float32))
        np.save(td / "pylon.npy", pyl.astype(np.float32))
        geo_o = EclipseGeometry(shape=ours.shape, sun_xy=(283.4, 255.1), sun_radius_px=60.0, north_deg=20.0)
        geo_o.to_json(td / "geo.json")
        geo_o.scaled(2.0).to_json(td / "geo_x2.json")
        g_o = geo_o
        r_o = g_o.rsun_map(dtype=np.float64)
        _, pa_o = cg.SolarFrame.from_geometry(g_o, P).solar_maps(ours.shape)
        np.save(td / "valid.npy", ~((pa_o >= 0) & (pa_o < 90)) | (r_o < 1.0))
        rings = [[1.6, 2.2], [2.2, 3.2]]
        base = dict(radii_rsun=dict(min=1.1, max=3.6, n=120), pa_step_deg=0.5,
                    ours=dict(image="ours.npy", bin=2, supersample=2, frame=dict(geometry="geo.json", p_angle_deg=P)),
                    references=[dict(name="Synthetic C2", image="ref.npy", supersample=2, frame=f_r.to_dict(),
                                     rings=rings),
                                dict(name="With pylon", image="pylon.npy", supersample=2, frame=f_r.to_dict(), rings=rings,
                                     dark_sector=dict(r_range=[2.0, 3.5], seed_pa_deg=135.0, dilate_deg=2.0))])

        def run(cfg, out):
            (td / "r.json").write_text(json.dumps(cfg))
            return cg.structure_from_config(td / "r.json", td / out, progress=lambda *_: None)

        run(base, "a")
        txt = (td / "a" / "coronagraph_structure.json").read_text()
        rec = json.loads(txt, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))   # strict: no NaN
        good, pylon = rec["references"]
        assert all(x["rho_0"] > 0.9 and x["fine_detail"]["rho_0"] > x["fine_detail"]["null_max"] for x in good["rings"])
        assert rec["ours"]["bin"] == 2 and abs(rec["ours"]["frame_used"]["rsun_px"] - 30.0) < 1e-9
        ex = np.array(pylon["excluded_pa_deg"])
        assert ex.min() >= 117.5 and ex.max() < 152.5 and ex.size >= 60
        assert all(x["rho_0"] > 0.9 for x in pylon["rings"])
        assert all(rec["gates"]["Synthetic C2"]["fine_detail_above_its_null"])
        inputs = json.loads((td / "a" / "receipt.json").read_text())["inputs"]
        assert "recipe" in inputs and any("geo.json" in k for k in inputs) and "sha256" in inputs["recipe"]
        wrong_p = json.loads(json.dumps(base))
        wrong_p["ours"]["frame"]["p_angle_deg"] = 0.0      # forgetting P puts every feature 15° further round
        wrong_p["max_shift_deg"] = 20.0
        run(wrong_p, "b")
        rb = json.loads((td / "b" / "coronagraph_structure.json").read_text())["references"][0]["rings"]
        assert all(abs(x["shift_deg"] - P) <= 0.5 and x["rho_0"] < x["rho_best"] - 0.1 for x in rb), rb
        masked = json.loads(json.dumps(base))
        masked["ours"]["valid"] = "valid.npy"
        run(masked, "c")
        rc = json.loads((td / "c" / "coronagraph_structure.json").read_text())["references"][0]["rings"]
        assert all(x["n_angles"] < 600 for x in rc)       # a quarter of ours masked: those angles are not used
        hole = ref.copy()
        hole[f_r.solar_maps(ref.shape)[0] > 2.0] = np.nan   # a reference without data beyond 2 R☉
        np.save(td / "hole.npy", hole.astype(np.float32))
        empty = dict(base, references=[dict(base["references"][0], name="Hole", image="hole.npy")])
        run(empty, "d")
        txt = (td / "d" / "coronagraph_structure.json").read_text()
        rd = json.loads(txt, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))["references"][0]["rings"]
        assert rd[1]["rho_0"] is None and "NaN" not in txt          # no data: null, never a number
        bad = [dict(base, ours=dict(base["ours"], frame=dict(geometry="geo_x2.json", p_angle_deg=P))),  # wrong canvas
               dict(base, ours=dict(base["ours"], vaild="valid.npy")),                               # misspelt key
               dict(base, radii_rsun=dict(min=1.1, max=3.6, n=120, spacing="logarithmic")),
               dict(base, references=[base["references"][0], dict(base["references"][1], name="Synthetic-C2")]),
               dict(base, ours=dict(base["ours"], valid="missing.npy")),
               dict(base, references=[dict(base["references"][1], dark_sector=dict(r_range=[2, 3], seed=320))])]
        for i, cfg in enumerate(bad):
            _raises(ValueError, lambda: run(cfg, f"bad{i}"))
            assert not (td / f"bad{i}").exists()
