"""Structure-aware detail (since 1.4.1): the five filters of the survey of 30-10-2026, with null controls and injections.

Every claim a docstring makes is tested against the default detail layer, ACHF iso 04, on the same scene:
two noise realisations share nothing (null), a thin ray or loop at a per-pixel S/N of 1 is found, a star leaves no
dark ring in the median transform, the diffusion moves no light out of the data and the gate leaves clean data whole.
"""
import numpy as np
from ael import filters as F
from ael.develop import LAYER_LABELS, layer_alpha, layer_names
from ael.filterbank import DEFAULTS, EXTRA, NAMES, STRUCTURE, make_filter, radial_log_residual
from ael.geometry import EclipseGeometry


def scene(seed, size=320, noise=0.03, rays=0.0, loop=0.0, star=0.0):
    """A power-law corona around an off-centre Moon; thin rays every 12°, a thin loop off the Sun, one star."""
    geo = EclipseGeometry((size, size), (size / 2 + .3, size / 2 - .2), 32, (size / 2 + 1.5, size / 2), 33)
    r = geo.radius_map(); th = geo.pa_map()
    base = 100 * np.maximum(r / 32, 1) ** -3
    truth = rays * np.exp(-0.5 * ((th % 12 - 6) / 0.5) ** 2)
    yy, xx = np.mgrid[:size, :size]
    truth = truth + loop * np.exp(-0.5 * ((np.hypot(xx - size * .72, yy - size * .35) - 40) / 1.2) ** 2) * (r > 40)
    a = base * (1 + truth) * (1 + noise * np.random.default_rng(seed).standard_normal(base.shape))
    if star:
        a[int(size * .2), int(size * .25)] += star * base[int(size * .2), int(size * .25)]
    return a.astype(np.float32), ~geo.moon_mask(2), geo, truth, r / 32


def corr(x, y, sel):
    x = x[sel] - x[sel].mean(); y = y[sel] - y[sel].mean()
    return float((x * y).mean() / np.sqrt((x * x).mean() * (y * y).mean()))


def test_structure_filters_are_extra_layers_that_keep_the_observed_domain():
    assert len(NAMES) == 16 and not set(EXTRA) & set(NAMES) and not set(EXTRA) & set(DEFAULTS)
    assert set(LAYER_LABELS) == set(NAMES) | set(EXTRA) and set(STRUCTURE) <= set(EXTRA)
    assert layer_names(list(STRUCTURE)) == ['10 Hessian ridge', '11 Steerable G2', '12 Median transform', '13 Noise gating',
                                        '14 Coherence diffusion']
    geo = EclipseGeometry((110, 140), (65.2, 55.3), 18, (67, 55), 19)
    r = geo.radius_map(); theta = np.radians(geo.pa_map())
    a = (100 * np.maximum(r / 18, 1) ** -3 * (1 + .1 * np.sin(12 * theta))).astype(np.float32)
    m = ~geo.moon_mask(2); m[20:35, 105:120] = False
    alpha = np.where(m, np.clip((geo.radius_map('moon') - 21) / 5, 0, 1), 0)
    for name in STRUCTURE:
        layer, mode, info = make_filter(name, a, m, geo)
        assert mode == 'overlay', name
        assert np.isfinite(layer[m]).all(), name          # the rectangle rule: every observed pixel, edges included
        assert np.isnan(layer[~m]).all(), name
        al = layer_alpha(alpha, m, mode)
        assert np.array_equal(al[m], alpha.astype(np.float32)[m]) and (al[~m] == 0).all()


def test_structure_filters_null_control_two_noise_realisations_share_nothing():
    a1, m, geo, _, rs = scene(1); a2, *_ = scene(2)
    ring = m & (rs > 1.3) & (rs < 4)
    for name in ('achf_iso_04',) + STRUCTURE:
        q1 = make_filter(name, a1, m, geo)[0]; q2 = make_filter(name, a2, m, geo)[0]
        assert abs(corr(q1, q2, ring & np.isfinite(q1) & np.isfinite(q2))) < .15, name


def test_curvilinear_filters_find_thin_rays_and_loops_better_than_the_isotropic_achf():
    for kind in ('rays', 'loop'):
        a, m, geo, truth, rs = scene(3, rays=.03 if kind == 'rays' else 0, loop=.03 if kind == 'loop' else 0)
        target = truth - F.normalized_gaussian(truth, m, 16)
        ring = m & (rs > 1.3) & (rs < 4) & np.isfinite(target)
        baseline = corr(make_filter('achf_iso_04', a, m, geo)[0], target, ring)
        assert baseline > .2, kind
        for name in ('hessian_ridge', 'steerable_g2', 'mmt'):
            assert corr(make_filter(name, a, m, geo)[0], target, ring) > baseline, (kind, name)


def test_median_transform_leaves_no_dark_ring_around_a_star_where_the_achf_does():
    a, m, geo, truth, rs = scene(4, star=50.0)
    yy, xx = np.mgrid[:320, :320]; d = np.hypot(xx - 80, yy - 64)
    ring = (d >= 5) & (d <= 12) & m; far = (d > 30) & (d < 45) & m
    depth = {name: float(np.mean(make_filter(name, a, m, geo)[0][ring]) - np.mean(make_filter(name, a, m, geo)[0][far]))
             for name in ('achf_iso_04', 'mmt')}
    assert depth['achf_iso_04'] < -.05 and depth['mmt'] > -.01, depth


def test_coherence_diffusion_moves_no_light_out_of_the_data():
    a, m, geo, truth, rs = scene(3)
    residual, _ = radial_log_residual(a, m, geo); ok = np.isfinite(residual)
    diffused, info = F.coherence_diffusion(residual, ok)
    assert np.isnan(diffused[~ok]).all() and np.isfinite(diffused[ok]).all()
    assert abs(float(np.sum(diffused[ok])) - float(np.sum(residual[ok]))) < 1e-3 * float(np.sum(np.abs(residual[ok])))
    assert float(np.std(diffused[ok])) < float(np.std(residual[ok]))          # it smooths, never sharpens
    assert info['steps'] == 54


def test_noise_gate_removes_noise_and_leaves_clean_data_almost_whole():
    for noise, check in ((0.0, lambda kept, removed: removed < .1), (0.03, lambda kept, removed: kept < .9)):
        a, m, geo, truth, rs = scene(3, noise=noise, rays=.03 if not noise else 0)
        residual, _ = radial_log_residual(a, m, geo); ok = np.isfinite(residual)
        gated, info = F.noise_gate(residual, ok, geo)
        ring = ok & (rs > 1.3) & (rs < 4)
        assert np.isnan(gated[~ok]).all() and np.isfinite(gated[ok]).all()
        kept = float(np.std(gated[ring]) / np.std(residual[ring]))
        removed = float(np.std((residual - gated)[ring]) / np.std(residual[ring]))
        assert check(kept, removed), (noise, kept, removed)


def test_pyramids_put_a_ramp_back_in_place_on_a_canvas_of_odd_size():
    """A filter that reduces and enlarges must enlarge every block back where it came from. A linear ramp has no
    detail at any scale, so on a canvas of odd size (389 × 515) every plane of the median transform, and the copy
    reduced by 2 or 3 and enlarged back that the coherence layer uses, must stay at zero inside the data (measured:
    5e-7, the float precision). Negative control: cropping the odd row and stretching back, as a first unpublished version did, leaves
    the ramp in the planes (measured: 6e-3 to 1e-2, a shift of 0.8–3.2 px of this ramp, depending on the plane and the axis)."""
    h, w = 389, 515
    yy, xx = np.mgrid[:h, :w].astype(np.float32)
    ramp = (0.004 * xx + 0.003 * yy).astype(np.float32)
    inner = (slice(80, h - 80), slice(80, w - 80))
    planes = F.multiscale_median(ramp, np.ones((h, w), bool), 5)
    assert all(p.shape == (h, w) for p in planes)
    assert max(float(np.nanmax(np.abs(p[inner]))) for p in planes) < 1e-5
    for f in (2, 3):
        padded = F._pad_to(ramp, f)
        back = F._up(F._block_mean(padded, f), padded.shape)[:h, :w]
        assert float(np.abs(back - ramp)[inner].max()) < 1e-5, f

    def cropped_half(c):                                      # the reduction of that first version
        hh, ww = (c.shape[0] // 2) * 2, (c.shape[1] // 2) * 2
        return F._block_mean(c[:hh, :ww], 2)

    c, old = ramp.copy(), []
    for _ in range(5):
        nxt = cropped_half(F._masked_median5(c)); d = c - F._up(nxt, c.shape)
        old.append(d if d.shape == ramp.shape else F._up(d, ramp.shape)); c = nxt
    assert max(float(np.nanmax(np.abs(p[inner]))) for p in old) > 1e-3



def test_nrgf_chain_leaves_whole_annuli_exactly_as_observed_beyond_a_cut_inner_edge():
    """Since 1.5.0. With the Moon off the Sun's centre the innermost annuli are cut; up to 1.4.2 the chain summed its
    terms from the first annulus of the run, and whatever the bridging added on those cut annuli shifted the profile
    of every whole annulus beyond (on the author's 2026 canvas the layer read −18 spreads from 1.5 R☉ outwards; in
    this scene, up to 17 spreads). The scene is large enough for 1° cells to tell a missing angle (R☉ = 250 px)."""
    import numpy as np
    from ael import filters as F
    from ael.geometry import EclipseGeometry
    from ael.radial import _covered_cells, _anchored_chain
    h, w, R = 1500, 1900, 250.0
    cx, cy = 950.0, 750.0
    mx = cx + 16.0
    g = EclipseGeometry((h, w), (cx, cy), R, moon_xy=(mx, cy), moon_radius_px=258.0)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    rp = np.hypot(xx - cx, yy - cy)
    pa = np.arctan2(yy - cy, xx - cx)
    rng = np.random.default_rng(5)
    # a steep corona with one very bright sector next to the cut: a cut annulus loses a bright angle
    I = 2e5 * np.maximum(rp / R, .5) ** -6 * (1 + 3.0 * np.exp(-((pa - 0.4) / 0.35) ** 2) + 0.2 * np.cos(3 * pa)) + 300.0
    I = (I * (1 + 0.01 * rng.standard_normal(I.shape))).astype(np.float32)
    valid = np.hypot(xx - mx, yy - cy) > 258.0                            # data up to the limb of the off-centre Moon
    seen = F.nrgf(I, valid, g, bin_px=2, min_count=12, partial_annuli='observed')
    chained = F.nrgf(I, valid, g, bin_px=2, min_count=12, partial_annuli='chain')
    covered, _ = _covered_cells(g, 'sun', valid, 2)
    flags = covered.all(axis=1)
    assert (~flags[115:140]).sum() >= 10                                  # the Moon does cut annuli in this scene
    first_whole = int(np.flatnonzero(flags & (np.arange(len(flags)) > 125))[0])
    inscribed = int(min(cx, w - cx, cy, h - cy) // 2)
    ring = np.floor(rp / 2).astype(int)
    # five annuli away from the cut ones: the curve through the nodes takes its slope from the five nearest
    whole = valid & (ring > first_whole + 5) & (ring < inscribed - 5) & np.isfinite(seen) & np.isfinite(chained)
    assert whole.sum() > 500000
    assert np.max(np.abs(chained[whole] - seen[whole])) < 2e-3, float(np.max(np.abs(chained[whole] - seen[whole])))
    cut = valid & (ring <= first_whole) & np.isfinite(seen) & np.isfinite(chained)
    assert np.max(np.abs(chained[cut] - seen[cut])) > 0.05                # the cut annuli are still bridged
    # the anchor itself: zero on whole annuli, counted from the nearest one, and the plain sum when there is none
    terms = np.array([0., .3, -.1, 0., 0., .2, 0., 0., -.4])
    whole_flags = np.array([0, 0, 0, 1, 1, 0, 1, 1, 0], bool)
    out = _anchored_chain(terms, whole_flags)
    assert np.allclose(out[whole_flags], 0) and np.allclose(out[:3], [-.2, .1, 0.]) and np.isclose(out[5], .1) and np.isclose(out[8], -.4)
    assert np.allclose(_anchored_chain(terms, np.zeros(9, bool)), np.cumsum(terms))
