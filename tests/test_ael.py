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
