import unittest
import numpy as np
from core.continuous_fnrgf import continuous_fnrgf
from core.filters import FilterWorker
from core.filters import fnrgf_normalize


class ContinuousFNRGFTests(unittest.TestCase):
    def test_analytic_mean_and_log_width(self):
        theta = (np.arange(64)+.5)*2*np.pi/64
        mean, width = 10+2*np.cos(theta), np.exp(.5+.2*np.sin(theta))
        image = np.stack([mean-width, mean+width])
        angles = np.broadcast_to(theta, image.shape)
        radii = np.full(image.shape, 1.5)
        for scale in (1e-25, 1., 1e25):
            actual = continuous_fnrgf(image*scale, radii, angles, [1, 2], order=3, segments=64,
                                      ridge=0, smooth_px=0, robust_iterations=0, mean_tail=1, width_tail=1)
            np.testing.assert_allclose(actual, np.stack([-np.ones(64), np.ones(64)]), atol=3e-12)

    def test_partial_support_constant_and_missing_sector_values_do_not_enter(self):
        theta = (np.arange(64)+.5)*2*np.pi/64
        a = np.broadcast_to(10+np.cos(theta), (4, 64)).copy()
        valid = np.ones_like(a, dtype=bool); valid[:, :20] = False
        r = np.full(a.shape, 1.5); t = np.broadcast_to(theta, a.shape)
        a += np.arange(4)[:, None]*.1
        expected = continuous_fnrgf(a, r, t, [1, 2], segments=64, valid=valid)
        a[~valid] = 1e30
        actual = continuous_fnrgf(a, r, t, [1, 2], segments=64, valid=valid)
        np.testing.assert_array_equal(actual, expected)
        self.assertTrue(np.isfinite(actual[valid]).all())
        self.assertTrue(np.isnan(actual[~valid]).all())
        flat = continuous_fnrgf(np.ones_like(a), r, t, [1, 2], segments=64, valid=valid)
        np.testing.assert_array_equal(flat[valid], 0.)

    def test_radial_interpolation_has_no_annulus_steps_on_affine_background(self):
        yy, xx = np.indices((220, 240), dtype=float)
        r = np.hypot(xx-118.3, yy-109.7)
        theta = np.arctan2(yy-109.7, xx-118.3)
        a = 100+.2*r+np.cos(9*theta)
        out = continuous_fnrgf(a, r, theta, np.arange(10, 160, 4), segments=64,
                               smooth_px=4, ridge=.01, mean_tail=0)
        use = (r > 30) & (r < 95)
        self.assertGreater(np.corrcoef(out[use], np.cos(9*theta[use]))[0, 1], .95)
        # No missing models in fully covered rings.
        self.assertTrue(np.isfinite(out[use]).all())

    def test_wrapper_blend_domain_and_fade(self):
        y, x = np.indices((80, 96)); a=(10+x*.1+y*.2).astype(np.float32)
        worker=FilterWorker(); args=(3, 32, 0, 10, 30, 12, 48, 40, 10)
        out=worker.run_fnrgf_native(a, 100, *args, mode='continuous', boundary_fade=5)
        mix=worker.run_fnrgf_native(a, 37, *args, mode='continuous', boundary_fade=5)
        np.testing.assert_allclose(mix, .63*a+.37*out, atol=1e-5)
        r=np.hypot(x-48,y-40)
        np.testing.assert_array_equal(out[(r <= 10) | (r >= 30)], a[(r <= 10) | (r >= 30)])

    def test_radial_step_metric_rejects_independent_ring_baseline(self):
        theta=(np.arange(64)+.5)*2*np.pi/64
        r=np.broadcast_to(np.linspace(20.01,99.99,1000)[:,None],(1000,64))
        t=np.broadcast_to(theta,r.shape)
        a=100+.2*r+np.sin(9*t)
        edges=np.arange(10,111,4)
        continuous=continuous_fnrgf(a,r,t,edges,segments=64,smooth_px=4,ridge=.01,
                                    mean_tail=1,width_tail=1,robust_iterations=0)
        independent=fnrgf_normalize(a,r,t,edges,segments=64,order=6,application_radius=10,
                                    mean_attenuation_range=(1,1),std_attenuation_range=(1,1))
        step=float(np.max(np.abs(np.diff(continuous,axis=0))[50:-50]))
        baseline=float(np.max(np.abs(np.diff(independent,axis=0))[50:-50]))
        self.assertLess(step,.05)
        self.assertGreater(baseline,10*step)

    def test_invalid_parameters(self):
        a=np.ones((8,8))
        for extra in (dict(ridge=-1), dict(width_floor=2), dict(smooth_px=-1), dict(segments=4), dict(valid=np.ones((2,2)))):
            with self.assertRaises(ValueError):
                continuous_fnrgf(a,a,a,[0,2],**extra)

    def test_single_sample_sectors_do_not_invent_near_zero_widths(self):
        theta=((np.arange(64)+.5)*2*np.pi/64)[None,:]
        image=10+np.cos(theta)
        out=continuous_fnrgf(image,np.full(image.shape,1.5),theta,[1,2],segments=64)
        self.assertTrue(np.isnan(out).all())
