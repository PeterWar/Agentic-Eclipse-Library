"""NAFE, the SWAP filter and the Larson–Sekanina gradient (since 1.4.2), the three layers the author tried on his 2026 image.

Each one against what its paper says it does, with a control that fails where it should: NAFE against the paper's sum
over the neighbours; SWAP against a corona with no angular structure, a narrow ray and a broad one; Larson–Sekanina
against the rotational difference worked out by hand, a ray narrower than Δθ and a prominence left out of its input.
All of them on the ring-free scene of the other filters, and through a recipe.
"""
import json
import tempfile
from pathlib import Path
import numpy as np
from ael import filters
from ael.develop import DEFAULT_OPACITY, LAYER_LABELS, filters_from_config, layer_names
from ael.filterbank import DEFAULTS, EXTRA, LARSON_SEKANINA, NAMES, make_filter, red_excess_mask
from ael.geometry import EclipseGeometry
from .test_lessons import _ZONES, _period2, _ring_band, _ring_free_scene, _old_layer
from .test_structure import corr, scene

NEW = ('nafe', 'swap', 'larson_sekanina_1', 'larson_sekanina_0.4')


def _refused(fn):
    try:
        fn()
    except ValueError:
        return True
    return False


def test_new_layers_are_extra_named_and_keep_the_observed_domain():
    """Outside "all" and the defaults (the connectors do not offer them); named after the author's files, within the
    31 bytes of a legacy layer name; each with a starting opacity. NAFE and SWAP give a value at every observed pixel,
    edges and the hole included (the rectangle rule); Larson–Sekanina only where it has its two partners, and never
    in the band of 0.035 R☉ next to the Moon. Nothing outside the data."""
    assert set(NEW) <= set(EXTRA) and not set(NEW) & set(NAMES) and not set(NEW) & set(DEFAULTS)
    assert len(NAMES) == 16 and set(LAYER_LABELS) == set(NAMES) | set(EXTRA)
    labels = layer_names(list(NEW))
    assert labels == ['09 NAFE', '16 SWAP filter', '15a Larson-Sekanina 1°', '15b Larson-Sekanina 0.4°'], labels
    assert all(len(x.split()) <= 9 and len(x.encode('mac_roman')) <= 31 for x in labels)
    assert {n: DEFAULT_OPACITY[n] for n in NEW} == {'nafe': .79, 'swap': 1., 'larson_sekanina_1': .2,
                                                     'larson_sekanina_0.4': .2}
    geo = EclipseGeometry((150, 180), (85.2, 75.3), 30, (87, 75), 31)
    r = geo.radius_map(); theta = np.radians(geo.pa_map())
    a = (100 * np.maximum(r / 30, 1) ** -3 * (1 + .1 * np.sin(12 * theta))).astype(np.float32)
    m = geo.radius_map('moon') > 31; m[20:35, 140:160] = False
    for name, mode in (('nafe', 'overlay'), ('swap', 'normal')):
        layer, got, _ = make_filter(name, a, m, geo)
        assert got == mode and np.isfinite(layer[m]).all() and np.isnan(layer[~m]).all(), name
        assert np.nanmin(layer) >= 0 and np.nanmax(layer) <= 1, name
    band = m & (geo.radius_map('moon') - 31 < .035 * 30)
    assert band.sum() > 50
    for name in LARSON_SEKANINA:
        layer, got, info = make_filter(name, a, m, geo)
        assert got == 'overlay' and np.isnan(layer[~m]).all() and np.isnan(layer[band]).all(), name
        assert info['limb_band_pixels'] == int(band.sum()), (name, info['limb_band_pixels'])
        inner = m & (r > 40) & (r < 60)
        assert np.isfinite(layer[inner]).mean() > .95, name
    assert _refused(lambda: make_filter('mgn', a, m, geo, exclude=~m))
    assert _refused(lambda: make_filter('swap', a, m, geo, nafe_sigma=1.))
    assert _refused(lambda: make_filter('larson_sekanina_2', a, m, geo))


# ---- NAFE, Druckmüller (2013), added after the author's 2026 test layer (written 28-10-2026) ----------------------

def _nafe_direct(a, m, y, x, sigma):
    """E at one pixel by the paper's own sum over the 129 × 129 neighbours (eq. 11–14): the reference of the fast levels."""
    from scipy.special import ndtr
    L = filters.nafe_neighbourhood(); H = 64; h, w = a.shape
    y0, y1, x0, x1 = max(y - H, 0), min(y + H + 1, h), max(x - H, 0), min(x + H + 1, w)
    lk = L[y0 - y + H:y1 - y + H, x0 - x + H:x1 - x + H] * m[y0:y1, x0:x1]
    return float(np.sum(lk * ndtr((float(a[y, x]) - a[y0:y1, x0:x1].astype(np.float64)) / sigma)) / lk.sum())


def test_nafe_follows_the_paper_and_does_not_invent_on_a_flat_input():
    """(1) The neighbourhood of eq. 12–14 is 1 at the centre and half of its weight lies beyond 32 px (eq. 13 as printed
    weights the wide Gaussians by 1/√σ; normalised Gaussians would keep two thirds within 16 px). (2) The fast levels
    agree with the paper's sum over the neighbours within 0.01, on a corona with noise, a hole and an edge of the field,
    with a narrow and a wide gate. (3) A flat input gives 0.5 everywhere: the NAFE of 25-08-2026, another operator that
    divided by a local spread, painted a whole field there (skills/postprocessat-corona/references/trampes.md).
    (4) Nothing outside the data."""
    L = filters.nafe_neighbourhood(); k = np.arange(129) - 64; rr = np.hypot(k[:, None], k[None, :])
    assert abs(L[64, 64] - 1) < 1e-12 and .5 < L[rr > 32].sum() / L.sum() < .57
    g = EclipseGeometry((200, 240), (110.3, 95.7), 20, (111, 96), 21)
    r = g.radius_map(); th = np.radians(g.pa_map())
    rng = np.random.default_rng(2013)
    a = (400 + 3000 * np.maximum(r / 20, 1) ** -3 * (1 + .2 * np.cos(9 * th)) + rng.standard_normal(r.shape)).astype(np.float32)
    m = g.radius_map('moon') > 22; m[150:175, 30:70] = False; m[:, 225:] = False
    ys, xs = np.nonzero(m); pick = rng.choice(len(ys), 150, replace=False)
    for sigma in (1., 12.):
        E, info = filters.nafe(a, m, sigma)
        err = max(abs(float(E[y, x]) - _nafe_direct(a, m, y, x, sigma)) for y, x in zip(ys[pick], xs[pick]))
        assert err < .01, (sigma, err, info['levels'])
        assert np.isnan(E[~m]).all() and np.isfinite(E[m]).all() and np.nanmin(E) >= 0 and np.nanmax(E) <= 1
    flat, _ = filters.nafe(np.full(a.shape, 7., np.float32), m, 2.)
    assert np.allclose(flat[m], .5, atol=1e-6) and np.isnan(flat[~m]).all()


def test_nafe_gate_quiets_pure_noise_and_hardly_touches_a_contrasted_scene():
    """The noise gate, with its control. On pure noise an almost closed gate (sigma = sigma_A/100) is plain fuzzy
    equalization: it spreads the noise over the whole range (rms about mid grey near 0.289, the uniform value). The
    default gate, 12 sigma_A, brings it below a third of that. Where the scene has contrast (here 200 sigma_A) the gate
    changes the layer little, as the paper says ('negligible in the contrasty parts of the image')."""
    rng = np.random.default_rng(2013)
    noise = (500 + rng.standard_normal((180, 200))).astype(np.float32); m = np.ones(noise.shape, bool)
    rms = lambda e: float(np.sqrt(np.nanmean((e - .5) ** 2)))
    closed, gated = filters.nafe(noise, m, .01)[0], filters.nafe(noise, m, 12.)[0]
    assert rms(closed) > .25 and rms(gated) < rms(closed) / 3, (rms(closed), rms(gated))
    yy, xx = np.mgrid[:180, :200]
    scene_ = (noise + 200 * np.sin(xx / 9.) * np.cos(yy / 13.)).astype(np.float32)
    d = filters.nafe(scene_, m, 12.)[0] - filters.nafe(scene_, m, .01)[0]
    assert float(np.sqrt(np.mean(d ** 2))) < .1 * rms(filters.nafe(scene_, m, 12.)[0]), float(np.sqrt(np.mean(d ** 2)))


def test_nafe_layer_measures_its_gate_from_the_noise():
    """make_filter('nafe') measures the pixel noise where the corona is faint and opens the gate at 12 times it; a given
    sigma is used as given, and only by NAFE."""
    g = EclipseGeometry((400, 400), (200.4, 199.6), 30, (201, 200), 31)
    r = g.radius_map(); th = np.radians(g.pa_map())
    a = (450 + 5000 * np.maximum(r / 30, 1) ** -3 * (1 + .2 * np.cos(7 * th))
         + 1.5 * np.random.default_rng(7).standard_normal(r.shape)).astype(np.float32)
    m = g.radius_map('moon') > 33
    q, mode, info = make_filter('nafe', a, m, g)
    assert mode == 'overlay' and info['noise_region'] == 'r >= 4 R_sun' and abs(info['sigma_A'] / 1.5 - 1) < .1, info
    assert abs(info['sigma'] - 12 * info['sigma_A']) < 1e-9 and np.isnan(q[~m]).all() and np.isfinite(q[m]).all()
    assert make_filter('nafe', a, m, g, nafe_sigma=5.)[2]['sigma'] == 5.
    assert _refused(lambda: make_filter('mgn', a, m, g, nafe_sigma=5.))


# ---- the SWAP filter above the limb, Seaton et al. (2023) --------------------------------------------------------

def _swap_scene(angular):
    """A corona of 120 px per solar radius around a Moon slightly off the Sun, with ``angular`` (a function of the
    position angle in degrees) multiplying it; no noise."""
    g = EclipseGeometry((640, 700), (350.4, 320.3), 120, (352, 321), 122)
    r = g.radius_map(); pa = g.pa_map()
    a = (1000 * np.maximum(r / 120, 1) ** -3 * angular(pa)).astype(np.float32)
    return g, r / 120, pa, a, g.radius_map('moon') > 123


def test_swap_divides_by_the_angular_median_and_invents_no_angle():
    """(1) With no angular structure the median along the circle is the corona itself, so the filtered image is
    I/(I + t0)^0.75 pixel by pixel: within 2 % where the 4 px blur of the filter changes little (1.3–2.5 R☉), and the
    same along every circle (the spread of the ratio between the two along a thin ring below 1e-4; 1e-5 measured). (2) A ray 2° wide, narrower than the
    ±15° median, keeps at least 90 % of its contrast; a broad modulation (a period of 180°) goes into the filter, as
    the paper intends: less than half of its contrast remains (0.44 measured; the 0.75 crush, and t0 where the corona
    is not much brighter than it, leave that much)."""
    g, rs, pa, a, m = _swap_scene(lambda p: np.ones_like(p))
    ratio, info = filters.swap_filter(a, m, g)
    assert info['c0'] == .75 and info['half_width_deg'] == 15 and info['blur_px'] == 4
    assert np.isnan(ratio[~m]).all() and np.isfinite(ratio[m]).all()
    expected = a / (a + info['t0']) ** .75
    band = m & (rs > 1.3) & (rs < 2.5)
    assert float(np.max(np.abs(ratio[band] / expected[band] - 1))) < .02
    for lo in np.arange(1.3, 2.4, .1):
        ring = m & (rs >= lo) & (rs < lo + .01)
        assert float(np.std(ratio[ring] / expected[ring])) < 1e-4, lo

    ray = lambda p: 1 + .2 * np.exp(-.5 * (((p - 100 + 180) % 360 - 180) / 1.) ** 2)
    broad = lambda p: 1 + .2 * np.cos(np.radians(2 * p))
    for shape, check in ((ray, lambda kept: kept > .9), (broad, lambda kept: kept < .5)):
        g, rs, pa, a, m = _swap_scene(shape)
        ratio, _ = filters.swap_filter(a, m, g)
        ring = m & (rs > 1.5) & (rs < 2.)
        at = lambda p0: ring & (np.abs((pa - p0 + 180) % 360 - 180) < .3)
        if shape is ray:
            kept = (float(np.mean(ratio[at(100)])) / float(np.mean(ratio[at(110)])) - 1) / .2
        else:
            kept = (float(np.mean(ratio[at(0)])) / float(np.mean(ratio[at(90)])) - 1) / (1.2 / .8 - 1)
        assert check(kept), (shape, kept)


def test_swap_reaches_every_observed_pixel_and_says_how():
    """The rectangle rule on a ragged field: isolated observed pixels in a region with no data (one in seven), which a
    polar grid can miss. Each one gets the same median taken at its own radius and angle; none is left without a
    value, none outside the data has one. The layer is a Normal view in [0, 1], the fourth root shown from 0.5 to 2."""
    g, rs, pa, a, m = _swap_scene(lambda p: 1 + .1 * np.sin(np.radians(9 * p)))
    yy, xx = np.mgrid[:640, :700]
    patch = (yy > 40) & (yy < 140) & (xx > 520) & (xx < 680)
    m = m & (~patch | ((yy * 3 + xx) % 7 == 0))
    ratio, info = filters.swap_filter(a, m, g)
    assert np.isfinite(ratio[m]).all() and np.isnan(ratio[~m]).all(), info
    layer, mode, linfo = make_filter('swap', a, m, g)
    assert mode == 'normal' and np.isfinite(layer[m]).all() and np.isnan(layer[~m]).all()
    assert 0 <= np.nanmin(layer) and np.nanmax(layer) <= 1 and linfo['display'].startswith('fourth root')
    u = (ratio / linfo['renormalised_by']) ** .25
    assert np.allclose(layer[m], np.clip((u[m] - .5) / 1.5, 0, 1), atol=1e-6)


# ---- the rotational gradient, Larson & Sekanina (1984) ------------------------------------------------------------

def _ls_scene(angular=lambda p: np.ones_like(p), sun=(250.3, 249.6)):
    """150 px per solar radius, the Sun near the middle of 500 × 500 px, the Moon covering it; ``angular`` multiplies."""
    g = EclipseGeometry((500, 500), sun, 150, (sun[0] + 1.2, sun[1] + .4), 153)
    r = g.radius_map(); pa = g.pa_map()
    a = (1000 * np.maximum(r / 150, 1) ** -3 * angular(pa)).astype(np.float32)
    return g, r / 150, pa, a, g.radius_map('moon') > 153


def test_larson_sekanina_is_the_rotational_difference_of_ln_l():
    """(1) A corona with no angular structure gives LS = 0 (below 1e-4 in ln L at 1.1–1.6 R☉): nothing rotates into
    view. (2) For ln L = f(r) + A cos(kθ) the paper's difference is A cos(kθ)·(2 − 2 cos kΔθ): with k = 12 and Δθ = 1°,
    the gradient matches it (correlation above 0.99, amplitude within 6 %, where the smoothing is 1.5 px)."""
    g, rs, pa, a, m = _ls_scene()
    ls, info = filters.larson_sekanina(np.log(np.where(m, a, 1)), m, g, 1.)
    ring = np.isfinite(ls) & (rs > 1.1) & (rs < 1.6)
    assert ring.sum() > 10000 and float(np.max(np.abs(ls[ring]))) < 1e-4, float(np.max(np.abs(ls[ring])))
    assert info['delta_deg'] == 1. and info['smoothing_px'] == [1.5, 3., 6., 12.]
    A, k = .2, 12
    g, rs, pa, a, m = _ls_scene(lambda p: np.exp(A * np.cos(np.radians(k * p))))
    ls, _ = filters.larson_sekanina(np.log(np.where(m, a, 1)), m, g, 1.)
    expected = A * np.cos(np.radians(k * pa)) * (2 - 2 * np.cos(np.radians(k * 1.)))
    ring = np.isfinite(ls) & (rs > 1.1) & (rs < 1.5)
    assert corr(ls, expected, ring) > .99
    gain = float(np.sum(ls[ring] * expected[ring]) / np.sum(expected[ring] ** 2))
    assert abs(gain - 1) < .06, gain


def test_larson_sekanina_copies_a_narrow_ray_at_plus_and_minus_delta():
    """The property the author was warned of: a ray narrower than Δθ comes out bright, with two dark copies at ±Δθ of
    about half its peak (between 0.35 and 0.65), and nothing a few Δθ away. Δθ = 1°, a ray 0.3° wide at 1.2–1.5 R☉."""
    g, rs, pa, a, m = _ls_scene(lambda p: 1 + .3 * np.exp(-.5 * (((p - 100 + 180) % 360 - 180) / .3) ** 2))
    ls, _ = filters.larson_sekanina(np.log(np.where(m, a, 1)), m, g, 1.)
    ring = np.isfinite(ls) & (rs > 1.2) & (rs < 1.5)
    at = lambda p0: float(np.mean(ls[ring & (np.abs((pa - p0 + 180) % 360 - 180) < .15)]))
    peak, plus, minus, far = at(100), at(101), at(99), at(104)
    assert peak > 0 and -.65 < plus / peak < -.35 and -.65 < minus / peak < -.35, (peak, plus, minus)
    assert abs(far) < .02 * peak, far


def test_larson_sekanina_leaves_a_prominence_and_the_limb_band_out_of_its_input():
    """A prominence (a compact, bright, red object next to the limb) in the input gives saturated copies at ±Δθ;
    :func:`red_excess_mask` finds it by its red and, left out of the input, it leaves no value over itself nor over the
    places where its copies would fall. Negative control: without the mask the copies are there (the layer within 0.1
    of black at 1° from it). The band of 0.035 R☉ next to the Moon never enters."""
    g, rs, pa, a, m = _ls_scene()
    yy, xx = np.mgrid[:500, :500]
    x0, y0 = g.sun_xy[0] + 1.3 * 150 * np.sin(np.radians(60)), g.sun_xy[1] - 1.3 * 150 * np.cos(np.radians(60))
    blob = np.hypot(xx - x0, yy - y0) < 1.5                    # 0.5° wide: narrower than Δθ
    lum = a * np.where(blob, 6., 1.).astype(np.float32)
    rgb = np.stack([lum * np.where(blob, 2., 1.), lum, lum], axis=-1).astype(np.float32)
    lum = (rgb[..., 0] + 2 * rgb[..., 1] + rgb[..., 2]) / 4
    prom = red_excess_mask(rgb, m, g)
    assert prom[blob & m].all() and prom.sum() < 3 * blob.sum() + 400, int(prom.sum())
    copies = lambda layer: [float(np.nanmin(layer[(np.abs((pa - p0 + 180) % 360 - 180) < .4) & (np.abs(rs - 1.3) < .02)]))
                            for p0 in (pa[int(y0), int(x0)] + 1, pa[int(y0), int(x0)] - 1)]
    without = make_filter('larson_sekanina_1', lum, m, g)[0]
    assert max(copies(without)) < .1, copies(without)
    layer, _, info = make_filter('larson_sekanina_1', lum, m, g, exclude=prom)
    assert np.isnan(layer[prom]).all() and info['excluded_pixels'] == int((prom & m).sum())
    assert all(np.isnan(c) or c > .3 for c in copies(layer)), copies(layer)
    band = m & (g.radius_map('moon') - 153 < .035 * 150)
    assert np.isnan(layer[band]).all() and info['limb_band_pixels'] == int(band.sum())


def test_larson_sekanina_null_control_two_noise_realisations_share_nothing():
    a1, m, geo, _, rs = scene(1); a2, *_ = scene(2)
    ring = m & (rs > 1.3) & (rs < 4)
    for name in LARSON_SEKANINA:
        q1 = make_filter(name, a1, m, geo)[0]; q2 = make_filter(name, a2, m, geo)[0]
        assert abs(corr(q1, q2, ring & np.isfinite(q1) & np.isfinite(q2))) < .15, name


# ---- all three on the scenes of the other filters ----------------------------------------------------------------

def test_new_layers_make_no_rings_on_a_ring_free_input():
    """The ring test of the other filters (test_lessons), on its scene and with its thresholds: two-pixel grooves,
    rings of 2–16 px over whole rings in three zones and in every 45° sector of the middle and outer zones, and the
    support band by band from the lunar limb and from the straight edge. Larson–Sekanina keeps a value only where
    both partners at ±Δθ are inside the data, so its support is checked from 3 px past the band it leaves out at the
    limb, and away from the straight edge by the length of its rotation there."""
    g, r, pa, theta, m, a = _ring_free_scene()
    rm = g.radius_map('moon'); yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]]
    old2 = _old_layer('nrgf', a, m, g)

    def sector(lo, hi, c):
        return m & (r >= lo) & (r < hi) & (np.abs((pa - c + 180) % 360 - 180) < 22.5)
    sectors = [(lo, hi, c) for lo, hi in _ZONES[1:] for c in range(0, 360, 45)]
    for name in NEW:
        layer = make_filter(name, a, m, g)[0]
        assert np.isnan(layer[~m]).all(), name
        ls = name in LARSON_SEKANINA
        for d in range(3 if ls else 0, 20):
            assert np.isfinite(layer[m & (rm >= 63 + d) & (rm < 64 + d)]).mean() >= .99, (name, 'limb', d)
            if not ls:
                assert np.isfinite(layer[m & (yy > 150) & (yy < 470) & (xx == 699 - d)]).mean() >= .99, (name, 'edge', d)
        for lo, hi, c in sectors:
            assert np.isfinite(layer[sector(lo, hi, c)]).mean() >= .99, (name, 'sector', lo, hi, c)
        assert _period2(layer, r, m) < .15 * _period2(old2, r, m), name
        whole = [_ring_band(layer, r, m, lo, hi) for lo, hi in _ZONES]
        assert max(whole) < .005, (name, whole)
        values = [_ring_band(layer, r, m, lo, hi, pa, c) for lo, hi, c in sectors]
        assert max(values) < .005, (name, max(values))


# Transfer of the faint injected pattern of test_lessons by each new layer (display units per unit ln I), measured
# with the code of 1.4.2 when they entered (02-11-2026); NAFE's, 0.82, was measured when it was written (28-10-2026)
# and holds. A regression check against these values, not an independent measure.
_DETAIL_GAIN_142 = {'nafe': .82, 'swap': .151, 'larson_sekanina_1': 29.05, 'larson_sekanina_0.4': 29.62}


def test_new_layers_keep_injected_fine_detail_with_its_sign_and_strength():
    """The sign-and-strength test of the other filters: a faint angular pattern (period 9.7°) must come out with its own
    sign and its measured strength (±25 %)."""
    g, r, pa, theta, m, a = _ring_free_scene()
    rng = np.random.default_rng(20261005)
    signal = .005 * np.sin(37 * theta + rng.uniform(-np.pi, np.pi)) * np.exp(-((r - 160) / 65) ** 4)
    noise = (1 + .003 * np.random.default_rng(1).standard_normal(a.shape)).astype(np.float32)
    clean = (a * noise).astype(np.float32); injected = (a * np.exp(signal) * noise).astype(np.float32)
    sel = m & (r > 90) & (r < 260)
    for name, expected in _DETAIL_GAIN_142.items():
        change = make_filter(name, injected, m, g)[0] - make_filter(name, clean, m, g)[0]
        ok = sel & np.isfinite(change)
        c = float(np.corrcoef(change[ok], signal[ok])[0, 1])
        gain = float(np.sum(change[ok] * signal[ok]) / np.sum(signal[ok] ** 2))
        assert c > .5 and abs(gain / expected - 1) < .25, (name, c, gain)


def test_recipe_makes_the_new_layers_hidden_with_their_opacities_and_keeps_a_prominence_out():
    """Through a recipe: listed by name, the three come as hidden layers with their starting opacities, and the recipe
    finds the prominence by its red and keeps it out of the Larson–Sekanina input only (NAFE still covers it)."""
    g, rs, pa, a, m = _ls_scene()
    a = a * (1 + .01 * np.random.default_rng(3).standard_normal(a.shape))       # the NRGF needs a spread
    yy, xx = np.mgrid[:500, :500]
    x0, y0 = g.sun_xy[0] - 1.1 * 150, g.sun_xy[1]
    blob = np.hypot(xx - x0, yy - y0) < 4
    lum = a * np.where(blob, 6., 1.)
    rgb = np.stack([lum * np.where(blob, 2., 1.), lum, lum], axis=-1).astype(np.float32)
    rgb[~m] = np.nan
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        np.save(root / 'input.npy', rgb); g.to_json(root / 'geometry.json')
        cfg = dict(input='input.npy', geometry='geometry.json', display=dict(scale=1000, asinh=20),
                   filters=['nrgf', 'nafe', 'swap', 'larson_sekanina_1'], moon_margin_px=0)
        (root / 'filters.json').write_text(json.dumps(cfg))
        result = filters_from_config(root / 'filters.json', root / 'out', progress=lambda *_: None)
        rec = json.loads(Path(result['receipt']).read_text())
        layers = {x['name']: x for x in rec['parameters']['layers']}
        assert [x['layer'] for x in rec['parameters']['layers']] == ['01 NRGF', '09 NAFE', '16 SWAP filter',
                                                                     '15 Larson-Sekanina 1°']
        assert {n: (x['mode'], x['opacity'], x['visible']) for n, x in layers.items()} == {
            'nrgf': ('multiply', .39, True), 'nafe': ('overlay', .79, False), 'swap': ('normal', 1., False),
            'larson_sekanina_1': ('overlay', .2, False)}
        assert layers['larson_sekanina_1']['parameters']['excluded_pixels'] >= int((blob & m).sum())
        ls = np.load(root / 'out' / 'larson_sekanina_1_layer.npy'); nafe = np.load(root / 'out' / 'nafe_layer.npy')
        assert np.isnan(ls[blob]).all() and np.isfinite(nafe[blob & m]).all()
        assert rec['gates']['nothing_outside_data']
