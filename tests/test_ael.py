"""Tests with known truth (synthetic data).  Run with ``python tests/run_tests.py`` or ``pytest``.

Every gate is also tested on a deliberately broken input (negative control): a check that cannot
fail proves nothing.
"""
from __future__ import annotations

import numpy as np

from ael import filters, gates, motion, polar, render
from ael.geometry import EclipseGeometry, fit_limb, position_angle
from ael.synthetic import SyntheticScene, render_scene


# ------------------------------------------------------------------ geometry
def test_position_angle_conventions():
    # north up, east left (normal sky image)
    assert abs(position_angle(0, -1) - 0) < 1e-9          # up = N
    assert abs(position_angle(-1, 0) - 90) < 1e-9         # left = E
    assert abs(position_angle(0, 1) - 180) < 1e-9         # down = S
    assert abs(position_angle(1, 0) - 270) < 1e-9         # right = W
    # north rotated 45° clockwise (to the upper right)
    assert abs(position_angle(1, -1, north_deg=45) - 0) < 1e-9
    # mirrored image: east to the right of north
    assert abs(position_angle(1, 0, mirrored=True) - 90) < 1e-9


def test_fit_limb_recovers_moon():
    sc = SyntheticScene(60.0, seed=1, moon_radius_px=62.0)
    img = sc.radiance((300, 360), (180.4, 150.2), moon_xy=(183.1, 148.7))
    res = fit_limb(img, (180, 150), 62.0)
    assert abs(res["xy"][0] - 183.1) < 0.3 and abs(res["xy"][1] - 148.7) < 0.3, res
    assert abs(res["r"] - 62.0) < 0.6, res


# ------------------------------------------------------------------ polar
def _scene_geo(shape=(420, 520), R=80.0):
    geo = EclipseGeometry(shape=shape, sun_xy=(shape[1] / 2 + 0.3, shape[0] / 2 - 0.2), sun_radius_px=R,
                          moon_xy=(shape[1] / 2 + 3.0, shape[0] / 2 + 1.0), moon_radius_px=1.02 * R, north_deg=20.0)
    sc = SyntheticScene(R, seed=3, moon_radius_px=1.02 * R, north_deg=20.0, psf_sigma_px=1.5)
    img = sc.radiance(shape, geo.sun_xy, geo.moon_xy)
    return geo, img


def test_polar_roundtrip():
    geo, img = _scene_geo()
    R = geo.sun_radius_px
    g = gates.polar_roundtrip(np.log(img), geo, (1.1 * R, 2.4 * R), n_pa=2048, n_r=300)
    assert g["passed"], g


def test_polar_no_invention_and_negative_control():
    geo, img = _scene_geo()
    hole = np.zeros(img.shape, bool)
    hole[100:160, 300:360] = True
    im2 = img.copy()
    im2[hole] = np.nan
    R = geo.sun_radius_px
    P = polar.to_polar(im2, geo, r_range=(1.05 * R, 2.8 * R), n_pa=1500)
    back = polar.from_polar(P, img.shape)
    g = gates.nothing_outside_data(back, ~hole)
    assert g["passed"], g
    # negative control: a product that fills the hole must fail the gate
    filled = back.copy()
    filled[hole] = 1.0
    assert not gates.nothing_outside_data(filled, ~hole)["passed"]


def test_polar_antialias():
    # fine angular pattern far from the centre: 700 cycles around the circle (aliases to 20 on 360 columns)
    h = w = 801
    geo = EclipseGeometry(shape=(h, w), sun_xy=(400.0, 400.0), sun_radius_px=100.0)
    pa = geo.pa_map().astype(np.float64)
    img = (1 + 0.5 * np.cos(np.radians(pa) * 700)).astype(np.float32)
    kw = dict(r_range=(330.0, 370.0), n_pa=360, n_r=20)
    aa = polar.to_polar(img, geo, antialias=True, **kw).data
    na = polar.to_polar(img, geo, antialias=False, **kw).data
    # 700 cycles on 360 columns cannot be represented: the honest answer is the mean (≈ 1, flat)
    assert np.nanstd(aa) < 0.08, np.nanstd(aa)
    assert np.nanstd(na) > 0.2, np.nanstd(na)   # without anti-aliasing: false pattern


# ------------------------------------------------------------------ filters
def test_normalized_gaussian_does_not_leak():
    rng = np.random.default_rng(0)
    img = rng.normal(100, 5, (200, 200)).astype(np.float32)
    valid = np.ones_like(img, bool)
    valid[:, 120:] = False
    a = img.copy(); a[~valid] = 0.0
    b = img.copy(); b[~valid] = 1e6
    for s in (3.0, 30.0):
        ra = filters.normalized_gaussian(a, valid, s)
        rb = filters.normalized_gaussian(b, valid, s)
        assert np.nanmax(np.abs(ra - rb)) == 0.0
        assert np.isnan(ra[:, 120:]).all()


def test_starlet_exact_reconstruction_with_mask():
    rng = np.random.default_rng(1)
    img = rng.normal(0, 1, (160, 180)).astype(np.float32) + np.linspace(0, 5, 180)[None, :]
    valid = np.ones_like(img, bool)
    valid[40:90, 60:100] = False
    d, c = filters.starlet(img, valid, n_scales=5)
    rec = np.sum(d, axis=0) + c
    assert np.nanmax(np.abs(rec - img)[valid]) < 1e-4
    assert np.isnan(rec[~valid]).all()


def test_wow_noise_floor_limits_noise_gain():
    rng = np.random.default_rng(2)
    noise = rng.normal(0, 1, (256, 256)).astype(np.float32)
    free = filters.wow(noise, None, n_scales=5, noise=1.0, noise_floor=0.0)
    floored = filters.wow(noise, None, n_scales=5, noise=1.0, noise_floor=3.0)
    assert np.nanstd(floored) < 0.4 * np.nanstd(free), (np.nanstd(floored), np.nanstd(free))


def test_structure_image_respects_domain():
    geo, img = _scene_geo()
    valid = geo.radius_map("moon") > geo.moon_radius_px + 1
    valid[:, :30] = False
    im = np.where(valid, img, np.nan)
    out = render.structure_image(im, valid, geo, detail="wow", wow_scales=5)
    g = gates.nothing_outside_data(out, valid)
    assert g["passed"], g
    assert np.isfinite(out[valid]).mean() > 0.95


# ------------------------------------------------------------------ motion
def _motion_setup(seed=5):
    """Frames of a synthetic eclipse: Sun drifting on the sensor, Moon crossing, dust on the sensor,
    one blob moving outwards at PA 60°."""
    shape = (360, 440)
    R = 60.0
    v_sun = np.array([0.10, -0.08])          # px/s on the sensor
    v_moon_rel = np.array([-0.15, -0.05])    # px/s relative to the Sun
    blob_v = 0.0016                          # R_sun/s  → 0.096 px/s
    sc = SyntheticScene(R, seed=seed, moon_radius_px=61.5, psf_sigma_px=1.2, n_rays=500,
                        blobs=[dict(pa=60.0, r0_rsun=1.45, v_rsun_s=blob_v, size_px=2.2, amp=4.0),
                               dict(pa=200.0, r0_rsun=1.35, v_rsun_s=0.0, size_px=2.2, amp=4.0)])
    s0 = np.array([220.0, 180.0])
    m0 = np.array([226.0, 182.0])
    dust = [(170.0, 120.0, 3.0, 0.25), (265.0, 245.0, 2.5, 0.3)]
    frames = []
    k = 0
    for t0 in (0.0, 5.0, 40.0, 80.0):
        for i, e in enumerate((0.002, 0.008, 0.032, 0.128)):
            t = t0 + 0.9 * i
            sun = s0 + v_sun * t
            moon = m0 + (v_sun + v_moon_rel) * t
            d, sat = render_scene(sc, shape, tuple(sun), tuple(moon), t, e, full_well=15000, seed=100 + k, sensor_dust=dust)
            frames.append(motion.Frame(name=f"f{k}", t=t, exposure=e, sun_xy=tuple(sun), moon_xy=tuple(moon),
                                       data=d, saturated=sat))
            k += 1
    geo = EclipseGeometry(shape=shape, sun_xy=tuple(s0), sun_radius_px=R, moon_radius_px=61.5)
    return frames, geo, v_sun, v_moon_rel, blob_v * R


def test_motion_pipeline_finds_blob_and_rejects_false_motion():
    frames, geo, v_sun, v_moon_rel, blob_speed = _motion_setup()
    groups = motion.group_epochs(frames, max_gap=1.5, min_members=3)
    assert len(groups) == 4
    ref = (220.0, 180.0)
    E = [motion.merge_epoch(g, ref, geo.shape, geo, name=f"E{i}") for i, g in enumerate(groups)]
    motion.match_epochs(E, ref=0, ring_rsun=(1.1, 1.8))
    hp = [motion.highpass(e.data, e.valid, sigma=4.0) for e in E]
    kw = dict(window=21, step=6, search=12, r_range_rsun=(1.12, 1.9))
    null = motion.measure_displacements(hp[0], hp[1], E[0].valid, E[1].valid, E[0].geometry, **kw)
    noise = motion.null_noise(null)["sigma"]
    vec = motion.measure_displacements(hp[0], hp[3], E[0].valid, E[3].valid, E[0].geometry, **kw)
    mid = motion.measure_displacements(hp[0], hp[2], E[0].valid, E[2].valid, E[0].geometry, **kw)
    dt = E[3].t - E[0].t
    motion.classify(vec, dt, sensor_velocity=tuple(-v_sun), moon_velocity=tuple(v_moon_rel), noise_px=noise)
    motion.confirm(vec, dt, null_vecs=null, mid_vecs=mid, dt_mid=E[2].t - E[0].t)
    cor = [v for v in vec if v.cls == "coronal"]
    # the blob: PA 60°, r ≈ 1.45–1.6 R_sun; expected displacement ≈ 0.096 px/s × dt, outwards
    ux, uy = np.sin(np.radians(-60.0)), -np.cos(np.radians(-60.0))
    near = [v for v in cor if abs(((v.pa - 60 + 180) % 360) - 180) < 6 and 1.35 < v.r_rsun < 1.75]
    assert near, "blob not detected"
    best = max(near, key=lambda v: v.peak)
    exp = blob_speed * dt
    got = best.dx * ux + best.dy * uy
    assert abs(got - exp) < 0.35 * exp + 1.0, (got, exp)
    # false positives: coronal vectors far from the moving blob
    far = [v for v in cor if abs(((v.pa - 60 + 180) % 360) - 180) > 20]
    assert len(far) <= 0.03 * max(len(vec), 1) + 1, len(far)
    # the dust on the sensor must never be called coronal
    for v in vec:
        for (xd, yd) in ((170.0, 120.0), (265.0, 245.0)):
            xs, ys = xd - (np.array(frames[0].sun_xy) - ref)[0], yd - (np.array(frames[0].sun_xy) - ref)[1]
            if np.hypot(v.x - xs, v.y - ys) < 4 and v.cls == "coronal":
                raise AssertionError("sensor dust classified as coronal")


def test_classify_negative_control():
    # a vector equal to the sensor drift must be 'sensor', one equal to the Moon's motion 'lunar'
    vs = [motion.Vector(0, 0, -8.0, 6.4, 0.9, 1.0, iso=0.8), motion.Vector(0, 0, -12.0, -4.0, 0.9, 1.0, iso=0.8),
          motion.Vector(0, 0, 5.0, 5.0, 0.9, 1.0, iso=0.8), motion.Vector(0, 0, 5.0, 5.0, 0.9, 1.0, iso=0.02)]
    motion.classify(vs, 80.0, sensor_velocity=(-0.10, 0.08), moon_velocity=(-0.15, -0.05), noise_px=0.3)
    assert [v.cls for v in vs] == ["sensor", "lunar", "coronal", "aperture"], [v.cls for v in vs]


# ------------------------------------------------------------------ Photoshop
def test_photoshop_16bit_layers_roundtrip():
    import importlib.util
    import tempfile
    import unittest
    from pathlib import Path

    if importlib.util.find_spec("psd_tools") is None:
        raise unittest.SkipTest('psd-tools not installed (pip install -e ".[photoshop]")')
    from ael import photoshop as ps

    rng = np.random.default_rng(3)
    h, w = 48, 64
    base = rng.integers(0, 65536, (h, w, 3), dtype=np.uint16)
    nrgf = rng.integers(0, 65536, (h, w), dtype=np.uint16)
    alpha = np.zeros((h, w), np.uint16)
    alpha[8:40, 10:50] = 65535                      # no data outside: transparent
    doc = ps.new_document(w, h, psb=True)
    ps.add_layer(doc, "Black background", np.zeros((h, w, 3), np.uint16), rle=True)
    ps.add_layer(doc, "Display base · stretched stack", base)
    ps.add_layer(doc, "NRGF", nrgf, alpha, mode="multiply", opacity=0.39, visible=False)
    expected = [dict(name="Black background", mode="normal", opacity=1.0, visible=True, rgb16=np.zeros((h, w, 3), np.uint16)),
                dict(name="Display base · stretched stack", mode="normal", opacity=1.0, visible=True, rgb16=base),
                dict(name="NRGF", mode="multiply", opacity=0.39, visible=False, rgb16=nrgf, alpha16=alpha)]
    with tempfile.TemporaryDirectory() as tmp:
        path = ps.save(doc, Path(tmp) / "test.psb", base)
        rep = ps.verify(path, expected)
        assert rep["ok"] and rep["depth"] == 16 and rep["layers"] == 3, rep
        # negative control: one changed pixel and a wrong opacity must be caught
        broken = [dict(e) for e in expected]
        changed = nrgf.copy()
        changed[20, 20] ^= 4096
        broken[2]["rgb16"] = changed
        broken[1]["opacity"] = 0.5
        bad = ps.verify(path, broken)
        assert not bad["ok"] and len(bad["mismatches"]) == 2, bad
        # never overwrite: a second save to the same path must refuse
        try:
            ps.save(doc, path, base)
            raise AssertionError("save overwrote an existing file")
        except FileExistsError:
            pass


# ------------------------------------------------------------------ animations without waves
def _anim_scene(shape=(280, 280), R=40.0, seed=11):
    # structure wider than a pixel, as in real stacks (the PSF spans several pixels): the finest band is grain
    sc = SyntheticScene(R, seed=seed, moon_radius_px=41.5, psf_sigma_px=2.5, sky_level=50.0, n_rays=40)
    geo = EclipseGeometry(shape=shape, sun_xy=(shape[1] / 2, shape[0] / 2), sun_radius_px=R,
                          moon_xy=(shape[1] / 2 + 1.0, shape[0] / 2), moon_radius_px=41.5)
    return geo, sc.radiance(shape, geo.sun_xy, geo.moon_xy)


def test_equalize_fine_grain_same_grain_nothing_added():
    from ael import animation
    import cv2
    geo, T = _anim_scene()
    rng = np.random.default_rng(0)
    s = 0.06
    prim, noisy = [], []
    for i in range(4):
        y = (T * np.exp(rng.normal(0, s, T.shape))).astype(np.float32)
        if i % 2 == 0:   # cleaner epochs: the optimal mean of y and an independent z (noise s/√2)
            z = (T * np.exp(rng.normal(0, s, T.shape))).astype(np.float32)
            prim.append(np.exp((np.log(y) + np.log(z)) / 2).astype(np.float32))
        else:
            prim.append(y)
        noisy.append(y)
    rs = geo.rsun_map()
    frames = lambda xs: [animation.display_detail(x, geo) for x in xs]
    ring = dict(r_range=(1.2, 2.8), step=0.4)        # rings ~16 px wide: enough pixels for a 10 % tolerance
    g0 = gates.grain_uniformity(frames(prim), geo, **ring)
    assert not g0["passed"] and g0["worst_ratio"] > 1.25, g0["worst_ratio"]          # negative control: a grain wave
    eq, rep = animation.equalize_fine_grain(prim, noisy, geo, hp_px=6.0)
    g1 = gates.grain_uniformity(frames(eq), geo, **ring)
    assert g1["passed"], g1["worst_ratio"]
    # nothing added: the cleaner epochs end with the noise of the noisier ones, not more
    k = (rs > 1.3) & (rs < 2.8)
    fine = lambda a: (a - cv2.GaussianBlur(a.astype(np.float32), (0, 0), 1.5))[k]
    target = np.std(fine(np.log(noisy[0]) - np.log(T)))
    got = np.std(fine(np.log(eq[0]) - np.log(T)))
    assert got <= 1.08 * target, (got, target)
    # the large scale is never touched
    G = lambda a: cv2.GaussianBlur(a.astype(np.float32), (0, 0), 15)
    assert np.max(np.abs((G(np.log(eq[0])) - G(np.log(prim[0])))[k])) < 0.004


def test_add_fine_detail_keeps_large_scale_and_no_ring():
    from ael import animation
    import cv2
    geo, T = _anim_scene(shape=(300, 300))
    rng = np.random.default_rng(1)
    s = 0.05
    rs = geo.rsun_map()
    base = (T * np.exp(rng.normal(0, s, T.shape))).astype(np.float32)
    xx = np.tile(np.arange(300, dtype=np.float32) / 300.0, (300, 1))
    extra = (T * (1.08 + 0.10 * xx) * np.exp(rng.normal(0, s, T.shape))).astype(np.float32)  # other level and gradient
    usable = rs > 1.3                                                                     # "saturated" inside 1.3
    wb = np.full(T.shape, 1.0 / s ** 2, np.float32)
    ws = animation.feather(usable, 6) / s ** 2
    out, _ = animation.add_fine_detail(base, wb, [(np.where(usable, extra, np.nan), ws)], geo, window_rsun=(1.6, 2.1))
    G = lambda a: cv2.GaussianBlur(a.astype(np.float32), (0, 0), 12)
    m = (rs > 1.25) & (rs < 3.0)
    assert np.max(np.abs((G(np.log(out)) - G(np.log(base)))[m])) < 0.004        # the large scale is the base's
    k = (rs > 2.3) & (rs < 3.0)
    fine = lambda a: (a - cv2.GaussianBlur(a.astype(np.float32), (0, 0), 1.5))[k]
    assert np.std(fine(np.log(out) - np.log(T))) < 0.8 * np.std(fine(np.log(base) - np.log(T)))  # less noise
    # negative control: a plain weighted mean through the same window makes a ring at the window
    win = animation.smoothstep((rs - 1.6) / 0.5)
    naive = ((base * wb + np.nan_to_num(extra) * ws * win) / (wb + ws * win)).astype(np.float32)
    det = lambda x: animation.display_detail(x, geo)
    bad = gates.no_concentric_bands([det(base), det(naive)], geo, r_range=(1.35, 2.6), step=0.02)
    good = gates.no_concentric_bands([det(base), det(out)], geo, r_range=(1.35, 2.6), step=0.02)
    assert not bad["passed"] and good["passed"], (bad["worst_sigma"], good["worst_sigma"])


def test_feathered_merge_softens_saturation_boundary():
    from ael import animation
    geo, T = _anim_scene(shape=(260, 260))
    rs = geo.rsun_map()
    sat_long = rs < 1.5                     # the long frame is 2 % brighter (extinction, sky): a step at its boundary
    f_long = motion.Frame("long", 0.0, 1.0, geo.sun_xy, None, (1.02 * T).astype(np.float32), sat_long)
    f_short = motion.Frame("short", 1.0, 0.25, geo.sun_xy, None, (0.25 * T).astype(np.float32), np.zeros(T.shape, bool))
    d_true = animation.display_detail(T, geo)
    def ring(feather_px):
        e = motion.merge_epoch([f_long, f_short], geo.sun_xy, geo.shape, geo, sat_dilate=0, feather_px=feather_px)
        d = animation.display_detail(e.data, geo) - d_true
        return max(abs(np.nanmean(d[(rs >= r0) & (rs < r0 + 0.02)])) for r0 in np.arange(1.36, 1.66, 0.02))
    hard, soft = ring(0.0), ring(16.0)
    assert soft < 0.5 * hard, (hard, soft)


def test_two_site_change_finds_common_change_and_control():
    from ael import animation
    geo, T = _anim_scene(shape=(300, 300))
    rs, pa = geo.rsun_map(), geo.pa_map()
    def blob(pa0, r0=1.7):
        d = (pa - pa0 + 180) % 360 - 180
        return 0.25 * np.exp(-0.5 * ((d / 3.0) ** 2 + ((rs - r0) / 0.06) ** 2))
    def series(seed, change):
        rng = np.random.default_rng(seed)
        return [animation.display_detail((T * (1 + (change if k >= 2 else 0)) * np.exp(rng.normal(0, 0.03, T.shape))).astype(np.float32), geo)
                for k in range(4)]
    kw = dict(start=(0, 1), end=(2, 3), rings=((1.3, 2.1),), hp_px=6.0, smooth_px=8.0, min_area_px=30, r_min_rsun=1.2,
              rotations=(-60, -45, -30, -20, 20, 30, 45, 60))
    a = series(1, blob(60.0))
    same = animation.two_site_change(a, series(2, blob(60.0)), geo, **kw)
    other = animation.two_site_change(a, series(3, blob(240.0)), geo, **kw)
    assert same["rings"][0]["sigma"] > 5, same["rings"]
    assert other["rings"][0]["sigma"] < 3, other["rings"]
    z = same["zones"][0]
    zpa = float(geo.pa_map()[int(round(z["y"])), int(round(z["x"]))])
    assert abs(((zpa - 60 + 180) % 360) - 180) < 15 and 1.45 < z["r_rsun"] < 1.95, z


def test_motion_gif_pipeline_refuses_waves():
    import tempfile
    from ael import pipelines
    geo, T = _anim_scene(shape=(240, 300), R=36.0)
    rng = np.random.default_rng(4)
    s = 0.06
    epochs, noisy = [], []
    for i in range(4):
        y = (T * np.exp(rng.normal(0, s, T.shape))).astype(np.float32)
        z = (T * np.exp(rng.normal(0, s, T.shape))).astype(np.float32)
        d = np.exp((np.log(y) + np.log(z)) / 2).astype(np.float32) if i % 2 == 0 else y
        mx = geo.sun_xy[0] + 1.0 - 0.3 * i
        g = EclipseGeometry(shape=geo.shape, sun_xy=geo.sun_xy, sun_radius_px=geo.sun_radius_px,
                            moon_xy=(mx, geo.sun_xy[1]), moon_radius_px=geo.moon_radius_px)
        epochs.append(motion.Epoch(name=f"E{i}", t=6.0 * i, t_min=6.0 * i, t_max=6.0 * i, data=d,
                                   valid=np.isfinite(d), geometry=g, moon_xy=[(mx, geo.sun_xy[1])]))
        noisy.append(y)
    kw = dict(out_size=(300, 240), rsun_out_px=36.0, noise_pairs=[(0, 1), (2, 3)])
    with tempfile.TemporaryDirectory() as tmp:
        try:   # negative control: alternating grain is a wave, the pipeline must refuse
            pipelines.motion_gif(epochs, tmp, **kw)
            raise AssertionError("waves not caught")
        except RuntimeError as e:
            assert "gates failed" in str(e), e
        r = pipelines.motion_gif(epochs, tmp, noisier=noisy, **kw)
        assert r["gates"]["grain_uniformity"]["passed"] and r["gates"]["no_concentric_bands"]["passed"]
        import os
        assert os.path.getsize(r["files"]["gif"]) > 1000
