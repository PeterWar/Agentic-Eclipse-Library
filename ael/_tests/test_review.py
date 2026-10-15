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
    gap in the data, on a steep profile, the annuli on both sides keep their own slope (the 1.3.1 operator, used as a
    negative control, holds the end of the profile flat and sends the median several sigma away). The local polynomial
    returns constants, straight lines and parabolas unchanged on runs of 1 to 5 nodes. One pixel 10,000 times too
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
        for y in (np.full(n, 2.5), 1.5+.7*t, .3+.2*t-.05*t*t):
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
