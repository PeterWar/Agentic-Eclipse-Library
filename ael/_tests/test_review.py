"""Controls added in 1.3.2 after an external review of the paper draft (October 2026).

No private image fixtures: every scene is synthetic and has a known answer.
"""
import numpy as np
from scipy.ndimage import gaussian_filter1d
from ael.geometry import EclipseGeometry
from ael.filterbank import radial_rank, make_filter, display_detail, upsilon
from ael import filters as F
from . import _radial_legacy as legacy


def _steep_scene(R=200., N=1100, eps=0.02):
    g = EclipseGeometry((N, N), (N/2-.37, N/2+.21), R)
    r = g.radius_map().astype(np.float64); th = np.radians(g.pa_map().astype(np.float64))
    m = (r >= 1.05*R) & (r <= 2.6*R)
    return g, r, m, (r**-3*(1+eps*np.cos(5*th))).astype(np.float32)


def _ripple(q, r, m, R, lo=1.05, hi=1.6):
    """Std of the azimuthal mean in 0.25-px radial steps, after removing anything slower than ~6 px."""
    sel = m & np.isfinite(q) & (r >= lo*R) & (r < hi*R)
    k = np.floor(r[sel]*4).astype(int); k -= k.min(); c = np.bincount(k)
    prof = (np.bincount(k, weights=q[sel])/np.maximum(c, 1))[c > 30]
    return float(np.std((prof-gaussian_filter1d(prof, 24))[30:-30]))


def test_faint_structure_on_a_steep_profile_leaves_only_the_sampling_floor():
    """A corona falling as r^-3 with 2 % angular structure. Each ring layer may carry no more concentric ripple than
    the same layer computed on the exactly flattened input (the sampling floor of the pixel grid). Negative controls
    that must fail: the 1.2.0 operators (hard radial bins) and the 1.3.1 NRGF (its profile smoothed with a plain
    Gaussian, which biases a steep, curved profile)."""
    g, r, m, img = _steep_scene(); R = g.sun_radius_px; flat = (img*r**3).astype(np.float32)
    for sector in (None, 30):
        floor = _ripple(radial_rank(flat, m, g, sector), r, m, R)
        new = _ripple(radial_rank(img, m, g, sector), r, m, R)
        old = _ripple(legacy.radial_rank(img, m, g, sector), r, m, R)
        assert new <= 1.3*floor, (sector, new, floor)
        assert old >= 3*floor, ('negative control', sector, old, floor)

    def nrgf(a, **kw):
        return display_detail(F.nrgf(a, m, g, bin_px=2, min_count=12, smooth_bins=3, **kw), m)[0]
    floor = _ripple(nrgf(flat), r, m, R); new = _ripple(nrgf(img), r, m, R)
    old = _ripple(display_detail(legacy.nrgf(img, m, g, bin_px=2, min_count=12, smooth_bins=3), m)[0], r, m, R)
    v131 = _ripple(nrgf(img, spread_about='bin'), r, m, R)
    assert new <= 1.3*floor, (new, floor)
    assert old >= 3*floor and v131 >= 1.5*floor, ('negative controls', old, v131, floor)


def test_multiply_is_a_uniform_darkening_times_a_modulation_symmetric_about_mid_grey():
    """1 − a + a·s = (1 − a/2)·[1 + a/(2 − a)·(2s − 1)]. On a base no brighter than mid grey, Overlay at a/(2 − a)
    gives the same structure as Multiply at a and differs only by the level 1/(1 − a/2). Negative control: Overlay at
    the same opacity is not equivalent. (Above mid grey, Overlay follows its screen branch and the tone differs.)"""
    s = np.linspace(0, 1, 1001)[None, :]; b = np.linspace(.02, .5, 49)[:, None]
    def overlay(base, layer, op):
        return (1-op)*base+op*np.where(base <= .5, 2*base*layer, 1-2*(1-base)*(1-layer))
    for a in (.03, .12, .14, .39):
        assert np.allclose(1-a+a*s, (1-a/2)*(1+a/(2-a)*(2*s-1)), atol=1e-12, rtol=0)
        mul = b*(1-a+a*s)
        assert np.allclose(mul/(1-a/2), overlay(b, s, a/(2-a)), atol=1e-12, rtol=0)
        assert np.abs(mul/(1-a/2)-overlay(b, s, a)).max() > 1e-3
    bright = np.linspace(.6, .95, 8)[:, None]
    assert np.abs(bright*(1-.12+.12*s)/(1-.06)-overlay(bright, s, .12/1.88)).max() > 1e-3


def test_upsilon_is_the_published_curve():
    """Gilly & Cranmer (2025), eq. 2: 0.5·(2q)^low below the median and 1 − 0.5·(2 − 2q)^high above it."""
    q = np.linspace(0, 1, 10001)
    for lo, hi in ((.35, .35), (.7, .35), (1., 1.)):
        u = upsilon(q, lo, hi)
        ref = np.where(q < .5, .5*(2*q)**lo, 1-.5*(2-2*q)**hi)
        assert np.allclose(u, ref, atol=2e-6, rtol=0)
        assert np.all(np.diff(u) >= -1e-6) and u[0] == 0 and abs(u[-1]-1) < 1e-6
        assert abs(float(upsilon(np.float32(.5-1e-5), lo, hi)[()])-.5) < 1e-3
    assert np.allclose(upsilon(q, 1, 1), q, atol=1e-6)
    assert np.std(upsilon(q)) < .7*np.std(q)                         # the tails move towards mid grey
    assert np.isnan(upsilon(np.array([np.nan, .2], np.float32))[0])   # no value is made where there was none
    for bad in ((0, .35), (.35, -1), (np.nan, .35)):
        try:
            upsilon(q, *bad)
        except ValueError:
            continue
        raise AssertionError(('exponents accepted', bad))


def _null_scene(seed, rings=0., seam=0.):
    """A corona with no structure: a smooth r^-3 profile with photon noise, an off-centre Moon, a straight edge."""
    R, N = 120., 760
    g = EclipseGeometry((N, N), (379.7, 380.3), R, (388.2, 377.1), 124.)
    r = g.radius_map(); th = np.radians(g.pa_map())
    m = (g.radius_map('moon') > 126) & (r <= 2.6*R)
    m[:, 640:] = False                                               # a straight coverage edge, inside the measured zone
    lam = 4000*(np.maximum(r, 1)/R)**-3*(1+rings*np.sin(2*np.pi*r/9))*(1+seam*np.cos(24*th))
    img = np.random.default_rng(seed).poisson(lam).astype(np.float32)/4000
    return g, r, th, m, np.where(m, np.maximum(img, 1e-6), 0).astype(np.float32)


def _ring_profile(q, r, m, lo, hi):
    sel = m & np.isfinite(q) & (r >= lo) & (r < hi)
    k = np.floor((r[sel]-lo)*4).astype(int); c = np.bincount(k)
    p = np.bincount(k, weights=q[sel])/np.maximum(c, 1)
    return p-gaussian_filter1d(p, 24)


def _angle_profile(q, th, r, m, lo, hi):
    sel = m & np.isfinite(q) & (r >= lo) & (r < hi)
    k = np.floor(np.degrees(th[sel]) % 360/0.5).astype(int); c = np.bincount(k, minlength=720)
    p = np.bincount(k, weights=q[sel], minlength=720)/np.maximum(c, 1)
    f = np.fft.rfft(p-p.mean()); f[:12] = 0                          # keep 12 cycles per turn and faster
    return np.fft.irfft(f, n=720)


def test_structureless_corona_gets_no_rings_or_sector_seams_from_the_ring_filters():
    """Pipeline-only control. On two independent noise realisations of a corona with no structure, whatever the
    pipeline itself prints is the same in both, and the noise is not: the concentric profile (2–16 px) and the angular
    profile (12 cycles per turn and faster, which includes the 24 and 48 of the quarter-sector nodes of the local
    RHEF) must not correlate between the two. Positive controls, which must correlate: rings of 9 px, a quarter of each layer's
    pixel scatter, added to both outputs (a ring-normalising filter removes true rings from its input by design, so
    the ring control tests the detector), and a 1 % modulation at 24 cycles per turn added to both inputs."""
    names = (('nrgf', None), ('rhef', None), ('rhef_local60', None), ('rhef_local30', None),
             ('rhef_local60', (.35, .35)), ('rhef_local30', (.35, .35)))
    lo, hi = 1.25*120, 2.4*120
    scenes = {k: (_null_scene(1, **kw), _null_scene(2, **kw)) for k, kw in
              (('clean', {}), ('seam', dict(seam=.01)))}
    for name, ups in names:
        prof = {}
        for k, (s1, s2) in scenes.items():
            g, r, th, m, a1 = s1; a2 = s2[4]
            q1 = make_filter(name, a1, m, g, upsilon_curve=ups)[0]; q2 = make_filter(name, a2, m, g, upsilon_curve=ups)[0]
            prof[k] = (np.corrcoef(_ring_profile(q1, r, m, lo, hi), _ring_profile(q2, r, m, lo, hi))[0, 1],
                       np.corrcoef(_angle_profile(q1, th, r, m, lo, hi), _angle_profile(q2, th, r, m, lo, hi))[0, 1])
            if k == 'clean':
                zone = m & (r >= lo) & (r < hi)
                ring = .25*float(np.nanstd(q1[zone]))*np.sin(2*np.pi*r/9)     # a quarter of the layer's own pixel scatter
                prof['rings'] = (np.corrcoef(_ring_profile(q1+ring, r, m, lo, hi), _ring_profile(q2+ring, r, m, lo, hi))[0, 1], None)
        assert abs(prof['clean'][0]) < .3 and abs(prof['clean'][1]) < .3, (name, ups, prof['clean'])
        assert prof['rings'][0] > .8, (name, ups, 'ring control', prof['rings'])
        assert prof['seam'][1] > .8, (name, ups, 'seam control', prof['seam'])


def test_local_rhef_with_upsilon_keeps_the_sign_of_faint_detail_and_tempers_its_gain():
    """The local RHEF with the authors' Upsilon (0.35 both sides) must return a faint injected pattern with its own
    sign, at a lower gain than without it (it pulls the extremes back towards mid grey). Measured on the scene of
    test_lessons on 15-10-2026: 2.83 → 1.67 at 60°, 5.47 → 2.70 at 30° (±25 %)."""
    from .test_lessons import _ring_free_scene
    g, r, pa, theta, m, a = _ring_free_scene()
    rng = np.random.default_rng(20261005)
    signal = .005*np.sin(37*theta+rng.uniform(-np.pi, np.pi))*np.exp(-((r-160)/65)**4)
    noise = (1+.003*np.random.default_rng(1).standard_normal(a.shape)).astype(np.float32)
    clean = (a*noise).astype(np.float32); injected = (a*np.exp(signal)*noise).astype(np.float32)
    sel = m & (r > 90) & (r < 260)
    for name, plain, tempered in (('rhef_local60', 2.83, 1.67), ('rhef_local30', 5.47, 2.70)):
        for ups, expected in ((None, plain), ((.35, .35), tempered)):
            change = make_filter(name, injected, m, g, upsilon_curve=ups)[0]-make_filter(name, clean, m, g, upsilon_curve=ups)[0]
            ok = sel & np.isfinite(change)
            corr = float(np.corrcoef(change[ok], signal[ok])[0, 1]); gain = float(np.sum(change[ok]*signal[ok])/np.sum(signal[ok]**2))
            assert corr > .5 and abs(gain/expected-1) < .25, (name, ups, corr, gain)


def test_nrgf_constants_gaps_short_runs_and_a_single_outlier():
    """Counterexamples found in review of 1.3.2 (October 2026). A constant input has no spread: no output. Next to a
    gap in the data, on a steep profile, the profile on both sides follows its own curvature into the end annuli (the
    1.3.1 operator, used as a negative control, holds the end of the profile flat and sends the median several sigma
    away). The local polynomial (used only when the nodes are smoothed)
    returns constants, straight lines, parabolas and cubics unchanged on runs of 1 to 5 nodes. One pixel 10,000 times too
    bright does not move the rest of its annulus."""
    from ael.radial import _local_quadratic
    g = EclipseGeometry((320, 320), (159.63, 160.21), 60)
    r = g.radius_map().astype(np.float64); th = np.radians(g.pa_map().astype(np.float64)); m = (r >= 64) & (r < 150)
    kw = dict(bin_px=2, min_count=12, smooth_bins=3)
    for c in (3., 1e-3, 1e4):
        for robust in (True, False):
            assert not np.isfinite(F.nrgf(np.full((320, 320), c, np.float32), m, g, robust=robust, **kw)).any(), (c, robust)
    img = ((r/60)**-3*(1+.02*np.cos(5*th))).astype(np.float32); gap = m & ~((r >= 100) & (r < 104))
    new = F.nrgf(img, gap, g, **kw); old = F.nrgf(img, gap, g, spread_about='bin', **kw)
    for lo, hi in ((96, 100), (104, 108)):
        side = gap & (r >= lo) & (r < hi)
        assert abs(np.median(new[side])) < .1, (lo, np.median(new[side]))
        assert abs(np.median(old[side])) > 1, ('negative control', lo, np.median(old[side]))
    for n in range(1, 6):
        t = np.arange(n, dtype=float)
        for y in (np.full(n, 2.5), 1.5+.7*t, .3+.2*t-.05*t*t, .1-.3*t+.02*t**3):
            assert np.allclose(_local_quadratic(y, 3), y, atol=1e-9) and np.allclose(_local_quadratic(y, 1), y, atol=1e-9), (n, y)
    yy, xx = np.nonzero(m & (r >= 120) & (r < 122)); spike = img.copy(); spike[yy[0], xx[0]] *= 1e4
    a = F.nrgf(img, m, g, **kw); b = F.nrgf(spike, m, g, **kw)
    ring = m & (r >= 120) & (r < 122); ring[yy[0], xx[0]] = False
    assert np.median(np.abs(a[ring]-b[ring])) < .01 and np.mean(np.sign(a[ring]) != np.sign(b[ring])) < .005


def test_nrgf_keeps_faint_annuli_beside_bright_ones_and_upsilon_options_are_explicit():
    """Review of 1.3.2: the test for a spread that is zero to rounding uses each annulus' own level, so a run that
    spans six decades keeps its faintest annuli. And the Upsilon option is explicit: an explicit curve applies to
    rhef_upsilon too, and any other filter refuses it."""
    g = EclipseGeometry((320, 320), (159.63, 160.21), 60)
    r = g.radius_map().astype(np.float64); th = np.radians(g.pa_map().astype(np.float64)); m = (r >= 64) & (r < 150)
    img = (np.exp(-(r-64)*np.log(1e6)/86)*(1+1e-4*np.cos(5*th))).astype(np.float32)
    q = F.nrgf(img, m, g, bin_px=2, min_count=12, smooth_bins=3)
    assert np.isfinite(q[m & (r >= 140) & (r < 148)]).mean() > .99
    a = (np.maximum(r, 1)**-3*(1+.1*np.cos(5*th))).astype(np.float32)
    default = make_filter('rhef_upsilon', a, m, g)[0]; same = make_filter('rhef_upsilon', a, m, g, upsilon_curve=(.35, .35))[0]
    other = make_filter('rhef_upsilon', a, m, g, upsilon_curve=(.7, .35))[0]
    assert np.allclose(default, same, equal_nan=True) and not np.allclose(default, other, equal_nan=True)
    for name in ('nrgf', 'mgn', 'achf_iso_04'):
        try:
            make_filter(name, a, m, g, upsilon_curve=(.35, .35))
        except ValueError:
            continue
        raise AssertionError(('upsilon_curve accepted by', name))


def _annulus_means(q, r, m, coverage=.99):
    """Azimuthal mean of q in each 2-px annulus; the layer must also cover the data (an annulus lost is a failure)."""
    k = np.floor(r[m]/2).astype(int); v = q[m]; f = np.isfinite(v)
    assert f.mean() >= coverage, ('coverage', f.mean())
    s, c = np.bincount(k[f], v[f]), np.bincount(k[f])
    return s[c > 0]/c[c > 0]


def _baumbach(rho):
    """The K corona of Baumbach (1937), in units of the mean solar brightness times 1e6."""
    return .0532*rho**-2.5+1.425*rho**-7+2.565*rho**-17


def test_nrgf_is_unbiased_on_clean_curved_profiles_and_gives_nothing_without_angular_signal():
    """Reviews of 1.3.2, with the filter bank's parameters (2-px annuli, no node smoothing). (1) A structureless r^-3
    corona from a very clean stack (noise 10^-4 of the brightness): every annulus averages within 0.2 sigma; a node
    that kept the profile's curvature inside its annulus left 1.6 sigma. (2) A profile with a dip (a parabola above
    zero) and the same corona sky-subtracted to zero: the run keeps the model that fits it (modelled on the logarithm
    the dip left 10 sigma). (3) Faint structure (10^-4) over six decades, and 10^-3 on r^-3, is recovered. (4) No
    output where nothing varies with angle: straight profiles through zero at several positions and scales (float32
    and exact radii), noiseless r^-3 and Baumbach coronae (curved, so the profile model leaves a residual that is a
    function of radius only), radial steps, a kink and a ripple, and the same at subnormal scale. A narrow ring of structure: the spread profile is
    shape-preserving and held at the end nodes, so it never dips towards zero (a cubic spline there gave |q| = 50).
    The model is chosen the same way at any scale of the data (at 1e-28 it was not). (5) Strong streamers on a clean stack: with the robust
    statistic every annulus keeps a median of q near zero, because the slope inside an annulus comes from the
    neighbouring nodes; the two halves of the annulus see different angles and gave up to 1.3 sigma."""
    kw = dict(bin_px=2, min_count=12)
    rng = np.random.default_rng(7)
    g = EclipseGeometry((700, 700), (349.63, 350.21), 120)
    r = g.radius_map().astype(np.float64); m = (r >= 126) & (r <= 312)
    img = ((r/120)**-3*(1+1e-4*rng.standard_normal(r.shape))).astype(np.float32)
    for robust in (True, False):
        mq = _annulus_means(F.nrgf(img, m, g, robust=robust, **kw), r, m)
        assert np.abs(mq).max() < .2, ('clean corona', robust, np.abs(mq).max())
    g = EclipseGeometry((320, 320), (159.63, 160.21), 60)
    r = g.radius_map().astype(np.float64); th = np.radians(g.pa_map().astype(np.float64)); m = (r >= 64) & (r < 150)
    noise = rng.standard_normal(r.shape)
    dip = (((r-101)**2+1)*(1+1e-3*noise)).astype(np.float32)
    sky = ((r/60)**-3*(1+1e-4*noise)-2.5**-3).astype(np.float32)          # some outer pixels are below zero
    for name, a in (('dip', dip), ('sky-subtracted', sky)):
        for robust in (True, False):
            mq = _annulus_means(F.nrgf(a, m, g, robust=robust, **kw), r, m)
            assert np.abs(mq).max() < .3, (name, robust, np.abs(mq).max())
    for prof, amp, least in ((np.exp(-(r-64)*np.log(1e6)/86), 1e-4, .95), ((r/60)**-3, 1e-3, .99)):
        q = F.nrgf((prof*(1+amp*np.cos(5*th))).astype(np.float32), m, g, **kw); f = np.isfinite(q) & m
        assert f.sum() > .99*m.sum() and np.corrcoef(q[f], np.cos(5*th[f]))[0, 1] > least, amp
    exact = g.radius_map('sun', np.float64)
    flat = [scale*(rr-zero) for rr in (r, exact) for zero in (101., 101.3) for scale in (1e-6, -1., 1e6)]
    curved = [(exact/60)**-3, _baumbach(exact/60), 1e-40*(exact-101), 1e-43*(exact/60)**-3,
              (exact/60)**-3*(1+.01/(1+np.exp(-(exact-100.7)/.3))),                        # a 1 % step 0.3 px wide
              (exact/60)**-3*(1+.02*np.sin(2*np.pi*exact/6)),                              # a radial ripple, 6 px
              (exact/60)**-3*(1+.2/(1+np.exp(-(exact-101)/1.))),                           # a 20 % step 1 px wide
              np.where(exact < 100.7, (exact/60)**-3, (100.7/60)**-3*(exact/100.7)**-2)]   # r^-3 turning into r^-2
    for a in flat+curved:
        for robust in (True, False):
            assert not np.isfinite(F.nrgf(a.astype(np.float32), m, g, robust=robust, **kw)[m]).any(), robust
    local = ((r/60)**-3*(1+.02*np.exp(-(r-101)**2/2)*np.cos(5*th))).astype(np.float32)   # a narrow ring of structure
    for robust in (True, False):
        assert np.nanmax(np.abs(F.nrgf(local, m, g, robust=robust, **kw)[m])) < 5, robust
    six = (np.exp(-(r-64)*np.log(1e6)/86)*(1+1e-4*np.cos(5*th)))
    for scale in (1e-28, 1e28):                                  # the choice of model does not depend on units
        q = F.nrgf((six*scale).astype(np.float32), m, g, **kw); f = np.isfinite(q) & m
        assert np.corrcoef(q[f], np.cos(5*th[f]))[0, 1] > .99, scale
    streamers = 1+.3*np.exp(-.5*(np.angle(np.exp(1j*(th-np.pi/2)))/np.radians(15))**2)+.3*np.exp(-.5*(np.angle(np.exp(1j*(th+np.pi/3)))/np.radians(10))**2)
    img = ((r/60)**-3*streamers*(1+1e-4*rng.standard_normal(r.shape))).astype(np.float32)
    q = F.nrgf(img, m, g, robust=True, **kw)
    k = np.floor(r[m]/2).astype(int); v = q[m]
    worst = max(abs(float(np.median(v[k == i]))) for i in np.unique(k))
    assert worst < .3, ('streamers', worst)


def test_filter_bank_nrgf_has_no_node_smoothing():
    """A smoothing window of three annuli bends a profile whose power-law index changes: on a 15-px Sun it left a ring
    of 2.3 sigma (noise 10^-3), and 2.5 sigma on a Baumbach corona. The filter bank does not smooth the nodes, whose
    noise is a few hundredths of sigma. On so small a Sun a noiseless, structureless corona gives no output."""
    g = EclipseGeometry((160, 160), (79.63, 80.21), 15)
    r = g.radius_map().astype(np.float64); m = (r >= 15.75) & (r <= 39)
    a = ((r/15)**-3*(1+1e-3*np.random.default_rng(3).standard_normal(r.shape))).astype(np.float32)
    flat = (g.radius_map('sun', np.float64)/15)**-3
    assert not np.isfinite(F.nrgf(flat.astype(np.float32), m, g, bin_px=2, min_count=12)[m]).any()   # no structure
    layer, mode, info = make_filter('nrgf', a, m, g)
    z = np.arctanh(np.clip(2*layer.astype(np.float64)-1, -1+1e-9, 1-1e-9))      # the layer is 0.5 + 0.5 tanh(q / s)
    z /= 1.4826*np.median(np.abs(z[m]-np.median(z[m])))
    assert info['smooth_bins'] == 0 and np.abs(_annulus_means(z, r, m)).max() < .5


def test_nrgf_bad_pixels_partial_annuli_and_short_runs():
    """Fourth review of 1.3.2. (1) One zero or negative pixel no longer switches a whole run from the logarithmic to
    the linear model (it changed the layer by 7.9 sigma far away). (2) With the robust statistic, one pixel 10^7 times
    too bright no longer raises the numerical floor of its annulus (the floor uses the median size of the values). (3) Data that start
    inside an annulus: the node sits at the mean radius of its own pixels, not extrapolated to the annulus' centre
    (that left up to 4 sigma). (4) Runs of one to three annuli give no output (the end nodes need the cubic through
    four nodes; with three, a Baumbach corona kept correlation 0.27); runs of four and five annuli keep faint
    structure, on r^-3 and on a Baumbach corona."""
    kw = dict(bin_px=2, min_count=12, smooth_bins=3)
    g = EclipseGeometry((320, 320), (159.63, 160.21), 60)
    r = g.radius_map().astype(np.float64); th = np.radians(g.pa_map().astype(np.float64)); m = (r >= 64) & (r < 150)
    c5 = np.cos(5*th)
    six = (np.exp(-(r-64)*np.log(1e6)/86)*(1+1e-4*c5)).astype(np.float32); base = F.nrgf(six, m, g, **kw)
    yy, xx = np.nonzero(m & (r >= 70.5) & (r < 71.5))
    for bad in (0., -1e-3):
        im = six.copy(); im[yy[0], xx[0]] = bad; q = F.nrgf(im, m, g, **kw)
        far = m & (r > 100)
        assert np.isfinite(q[far]).all() and np.sqrt(np.mean((q[far]-base[far])**2)) < .01, bad
    law = ((r/60)**-3*(1+1e-4*c5)).astype(np.float32)
    yy, xx = np.nonzero(m & (r >= 120) & (r < 122)); spike = law.copy(); spike[yy[0], xx[0]] *= 1e7
    ring = m & (r >= 120) & (r < 122); ring[yy[0], xx[0]] = False
    assert np.isfinite(F.nrgf(spike, m, g, robust=True, **kw)[ring]).mean() > .99       # (the mean statistic is not robust)
    baum = (_baumbach(r/60)*(1+1e-4*c5)).astype(np.float32)
    for n in range(1, 6):
        sel = (r >= 64) & (r < 64+2*n)
        for a, least in ((law, .99), (baum, .95)):                   # measured: 0.9996 or more on r^-3, 0.98 on Baumbach
            for robust in (True, False):
                q = F.nrgf(a, sel, g, robust=robust, **kw); f = sel & np.isfinite(q)
                if n < 4:
                    assert not f.any(), (n, robust)
                else:
                    assert f.sum() == sel.sum() and np.corrcoef(q[f], c5[f])[0, 1] > least, (n, robust)
    G = EclipseGeometry((700, 700), (349.63, 350.21), 120); R = G.radius_map().astype(np.float64)
    img = ((R/120)**-3*(1+1e-4*np.random.default_rng(34).standard_normal(R.shape))).astype(np.float32)
    for start in (127.5, 127.9):
        M = (R >= start) & (R <= 312)
        assert np.abs(_annulus_means(F.nrgf(img, M, G, **kw), R, M)).max() < .3, start


def test_nrgf_ties_zeros_clipping_and_a_sky_below_zero():
    """Second adversarial check of 1.3.2. (1) Exact ties: a zero-padded frame, a clipped inner corona and 8-bit data
    whose noise is below one grey level. When half an annulus' pixels share one value its robust spread (MAD) is
    zero and its node is that value, not the corona: no output there (such annuli reached |q| = 10^37, and 8-bit
    data with half a grey level of noise |q| = 500). With one grey level of noise the data are measurable and kept. (2) A sky
    subtracted too deep takes the far corona below zero; the run is then modelled on asinh(I/s), logarithmic where
    the corona is bright and linear near zero, and the limb stays unbiased (on the values it kept 0.6 sigma).
    (3) make_filter('nrgf') keeps the pixels below zero (it used to drop them, leaving holes in a subtracted sky)."""
    kw = dict(bin_px=2, min_count=12)
    g = EclipseGeometry((320, 320), (159.63, 160.21), 60)
    r = g.radius_map().astype(np.float64); th = np.radians(g.pa_map().astype(np.float64)); m = (r >= 64) & (r < 150)
    rng = np.random.default_rng(12); noise = rng.standard_normal(r.shape)
    img = ((r/60)**-3*(1+1e-3*noise)).astype(np.float32)
    pad = img.copy(); pad[r > 120] = 0
    q = F.nrgf(pad, m, g, **kw)
    assert not np.isfinite(q[m & (r >= 122)]).any() and np.isfinite(q[m & (r < 116)]).mean() > .99
    clip = np.minimum(img, np.float32((72/60)**-3))
    q = F.nrgf(clip, m, g, **kw)
    assert not np.isfinite(q[m & (r < 70)]).any() and np.nanmax(np.abs(q[m])) < 10
    for sigma, least in ((.15, 0.), (.5, 0.), (1., .99), (2., .99)):        # noise in grey levels of 8-bit data
        grey = np.clip(np.round(30*(r/60)**-3+20+sigma*noise), 0, 255).astype(np.uint8)
        q = F.nrgf(grey, m, g, **kw)
        assert not (np.abs(q[m]) >= 10).any() and np.isfinite(q[m]).mean() >= least, sigma
    baum = _baumbach(r/60)*(1+1e-4*noise)
    deep = (baum-1.2*baum[m].min()).astype(np.float32)
    for robust in (True, False):
        assert np.abs(_annulus_means(F.nrgf(deep, m, g, robust=robust, **kw), r, m)).max() < .15, robust
    sky = ((r/60)**-3*(1+.02*np.cos(5*th))-2.2**-3+3e-4*noise).astype(np.float32)
    assert (sky[m] <= 0).mean() > .05
    layer = make_filter('nrgf', sky, m, g)[0]
    assert np.isfinite(layer[m]).mean() > .99



def test_nrgf_is_in_units_of_the_spread_and_keeps_every_measurable_annulus():
    """Second adversarial check of 1.3.2. (1) q is in units of the annulus spread: on structureless noise its robust
    spread (or standard deviation, with the mean statistic) is 1 in every annulus; a spread ten times too large, or a
    MAD without its 1.4826, passed every other test. (2) An annulus holding exactly min_count pixels gives output.
    (3) The numerical floor sits at one float32 step: angular structure of 10⁻⁶ of the brightness on r⁻³ survives
    (a floor three times higher passed every other test)."""
    g = EclipseGeometry((320, 320), (159.63, 160.21), 60)
    r = g.radius_map().astype(np.float64); th = np.radians(g.pa_map().astype(np.float64)); m = (r >= 64) & (r < 150)
    img = ((r/60)**-3*(1+1e-3*np.random.default_rng(21).standard_normal(r.shape))).astype(np.float32)
    k = np.floor(r/2).astype(int)
    for robust in (True, False):
        q = F.nrgf(img, m, g, bin_px=2, min_count=12, robust=robust)
        for i in np.unique(k[m]):
            v = q[m & (k == i)]
            s = 1.4826*np.median(np.abs(v-np.median(v))) if robust else np.std(v)
            assert .9 < s < 1.1, (robust, i, s)
    sel = m.copy(); yy, xx = np.nonzero(m & (k == 50)); sel[m & (k == 50)] = False; sel[yy[:12], xx[:12]] = True
    q = F.nrgf(img, sel, g, bin_px=2, min_count=12)
    assert np.isfinite(q[yy[:12], xx[:12]]).all()
    exact = g.radius_map('sun', np.float64)
    q = F.nrgf(((exact/60)**-3*(1+1e-6*np.cos(5*th))).astype(np.float32), m, g, bin_px=2, min_count=12)
    assert np.isfinite(q[m]).mean() > .99



def test_nrgf_keeps_symmetric_structure_on_a_centred_grid_and_all_negative_input():
    """Ninth review of 1.3.2. (1) With the Sun's centre on the pixel grid, pixels at one radius are mirror images of
    each other and carry the same value of a 4-fold structure; a detector of angular signal that compared each pixel
    with its neighbours in radius took that structure for a radial profile and dropped 73 % of the data. Every
    structure must be kept, whatever the centre and the symmetry. (2) make_filter('nrgf') accepts an input that is
    negative everywhere (it refused it before building its own mask)."""
    for centre in ((160., 160.), (160.5, 160.5), (159.63, 160.21)):
        g = EclipseGeometry((320, 320), centre, 60)
        r = g.radius_map().astype(np.float64); th = np.radians(g.pa_map().astype(np.float64)); m = (r >= 64) & (r < 150)
        for n in (2, 4, 8):
            a = ((np.maximum(r, 1)/60)**-3*(1+.02*np.cos(n*th))).astype(np.float32)
            q = F.nrgf(a, m, g, bin_px=2, min_count=12); f = np.isfinite(q) & m
            assert f.sum() > .99*m.sum() and np.corrcoef(q[f], np.cos(n*th[f]))[0, 1] > .99, (centre, n)
    neg = ((r/60)**-3*(1+.02*np.cos(5*th))-1).astype(np.float32)
    layer = make_filter('nrgf', neg, m, g)[0]
    assert np.isfinite(layer[m]).mean() > .99



def test_nrgf_mean_statistic_keeps_a_bright_pixel_to_its_own_neighbourhood():
    """With the mean statistic (robust=False, the form of Morgan, Habbal and Woo), one pixel 1000 times too bright
    moves its own annulus' mean. The profile through the nodes is local, and the slope and curvature come from median
    nodes, so three annuli away the layer does not change (a global spline carried it there at about 1 sigma). With the
    median it moves nothing beyond its own annulus."""
    g = EclipseGeometry((320, 320), (159.63, 160.21), 60)
    r = g.radius_map().astype(np.float64); m = (r >= 64) & (r < 150); k = np.floor(r/2).astype(int)
    img = ((r/60)**-3*(1+1e-3*np.random.default_rng(3).standard_normal(r.shape))).astype(np.float32)
    yy, xx = np.nonzero(m & (k == 60)); hot = img.copy(); hot[yy[0], xx[0]] *= 1e3
    for robust, j, limit in ((False, 3, .05), (True, 1, .01)):
        d = np.abs(F.nrgf(img, m, g, bin_px=2, min_count=12, robust=robust)-F.nrgf(hot, m, g, bin_px=2, min_count=12, robust=robust))
        for i in np.unique(k[m & (np.abs(k-60) >= j)]):           # annulus by annulus: an aggregate could dilute one
            ring = m & (k == i)
            assert (np.nanmax(d[ring]) if robust else np.nanmean(d[ring])) < limit, (robust, i)


def test_nrgf_gives_nothing_for_noiseless_radial_profiles_on_a_small_grid():
    """Eleventh review of 1.3.2. A noiseless radial profile has no angular signal, so it must give no output. On a
    small Sun (25 px, centre on a pixel corner), a 2 % radial ripple 6 px long gave output over a quarter of the field:
    0.1-px bands held only one or two different radii, where a parabola is not determined, and the profile's own kinks
    stayed in the residuals. Each band now holds four radii or more, and a second function of radius is fitted to the
    values themselves. A steep exponential on a 15-px Sun needs the residuals."""
    for R, c, profile in ((25, 80.5, lambda r: (r/25)**-3*(1+.02*np.sin(2*np.pi*r/6))),
                          (15, 80.5, lambda r: np.exp(-(r-15)/3))):
        g = EclipseGeometry((160, 160), (c, c), R)
        r = g.radius_map().astype(np.float64); m = (r >= 1.05*R) & (r < 2.6*R)
        a = profile(np.maximum(r, 1)).astype(np.float32)
        for robust in (True, False):
            q = F.nrgf(a, m, g, bin_px=2, min_count=12, robust=robust)
            assert not np.isfinite(q[m]).any(), (R, robust, np.isfinite(q[m]).mean())
    # Ninth and tenth reviews: a strong ripple (20 %, 4 px) around a 100-px Sun. A float32 radius is off by up to half a
    # step; times the ripple's own slope, that looked like angular signal (output on 95 % of the field). The radii are
    # now exact. Raising the floor instead dropped real structure of 10^-5 on the same ripple, so that is the positive
    # control. The input is made on exact radii: one made on float32 radii carries that rounding as real jitter.
    # With the mean statistic that ripple still gives some output (the smooth function of radius cannot follow it to
    # rounding; a declared limit). Pixels mirrored about the diagonal share a radius, so their difference in q
    # cancels the rings and keeps the structure.
    g = EclipseGeometry((560, 560), (280., 280.), 100)
    r = g.radius_map('sun', np.float64); th = np.radians(g.pa_map().astype(np.float64)); m = (r >= 105) & (r < 260)
    ripple = (r/100)**-3*(1+.2*np.sin(2*np.pi*r/4+.7))
    assert not np.isfinite(F.nrgf(ripple.astype(np.float32), m, g, bin_px=2, min_count=12)[m]).any()
    q = F.nrgf((ripple*(1+1e-5*np.cos(2*th))).astype(np.float32), m, g, bin_px=2, min_count=12)
    f = np.isfinite(q) & np.isfinite(q.T) & m; c = np.cos(2*th)
    assert f.sum() > .97*m.sum() and np.corrcoef((q-q.T)[f], (c-c.T)[f])[0, 1] > .9, f.sum()/m.sum()   # 98 %: all
    # but the partial outer annulus (258-260 px)
