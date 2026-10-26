import unittest
import numpy as np
from scipy.ndimage import gaussian_filter1d

from core.radial_continuous import rhef_continuous_normalize
from core.filters import FilterWorker, rhef_normalize


class ContinuousRHEFTests(unittest.TestCase):
    def test_interpolated_quantiles_match_independent_scalar_reference(self):
        r = np.linspace(.1, 3.9, 80).reshape(8, 10)
        a = np.random.default_rng(17).uniform(1, 100, r.shape)
        actual = rhef_continuous_normalize(a, r, 2, min_count=2)
        probability = np.linspace(0, 1, 257)
        tables = [np.quantile(np.log(a[(r // 2) == k]), probability) for k in (0, 1)]
        for index in np.ndindex(a.shape):
            weight = np.clip(r[index] / 2 - .5, 0, 1)
            curve = tables[0] * (1 - weight) + tables[1] * weight
            z = np.log(a[index])
            ties = np.flatnonzero(curve == z)
            expected = ties.mean() / 256 if ties.size else np.interp(z, curve, probability)
            self.assertAlmostEqual(actual[index], expected)

    def test_ties_constants_and_scalar_reference(self):
        a = np.array([[1., 1., 2., 3., 4.]])
        q = rhef_continuous_normalize(a, np.ones_like(a), 2, min_count=2)
        curve = np.quantile(np.log(a[0]), np.linspace(0, 1, 257))
        for i, z in enumerate(np.log(a[0])):
            equal = np.flatnonzero(curve == z)
            expected = equal.mean() / 256 if equal.size else np.interp(z, curve, np.linspace(0, 1, 257))
            self.assertAlmostEqual(q[0, i], expected)
        q = rhef_continuous_normalize(np.ones((3, 9)), np.ones((3, 9)), 2)
        np.testing.assert_array_equal(q, .5)

    def test_mask_nonfinite_nonpositive_sparse_and_gap(self):
        r = np.broadcast_to(np.arange(7)[:, None] * 2 + 1., (7, 16)).copy()
        a = np.broadcast_to(np.linspace(1, 5, 16), r.shape).copy()
        valid = np.ones(r.shape, bool)
        valid[2] = False
        valid[4, 2:] = False
        a[0, :3] = [np.nan, 0, -1]
        q = rhef_continuous_normalize(a, r, 2, valid=valid)
        self.assertTrue(np.isnan(q[2]).all())
        self.assertTrue(np.isnan(q[4]).all())
        self.assertTrue(np.isnan(q[0, :3]).all())
        altered = a.copy()
        altered[~valid] = 1e20
        np.testing.assert_allclose(q, rhef_continuous_normalize(altered, r, 2, valid=valid), equal_nan=True)
        # Changes beyond an empty ring cannot influence the run before it.
        altered[3:] *= 100
        np.testing.assert_allclose(q[:2], rhef_continuous_normalize(altered, r, 2, valid=valid)[:2], equal_nan=True)

    def test_units_and_application_bypass(self):
        y, x = np.indices((120, 144))
        r = np.hypot(x - 70.3, y - 59.7)
        a = np.random.default_rng(4).uniform(100, 5000, r.shape).astype(np.float32)
        expected = rhef_continuous_normalize(a, r, 2, application_radius=20)
        for scale in (1e-25, 1e-8, 65535., 1e25):
            q = rhef_continuous_normalize(a * scale, r, 2, application_radius=20)
            np.testing.assert_allclose(q, expected, atol=2e-5, equal_nan=True)
        worker = FilterWorker()
        out = worker.run_rhef_native(a, 50, 10, 35, 70.3, 59.7, 20, bin_px=2, mode="continuous")
        np.testing.assert_array_equal(out[r < 20], a[r < 20])
        np.testing.assert_array_equal(worker.run_rhef_native(a, 0, 10, 35, 70, 60, 20, mode="continuous"), a)
        self.assertTrue(np.isfinite(out).all())

    def test_continuous_ranks_reduce_rings_and_recover_injected_detail(self):
        y, x = np.indices((660, 660), dtype=float)
        r = np.hypot(x - 329.63, y - 330.21)
        theta = np.arctan2(y - 330.21, x - 329.63)
        valid = (r >= 126) & (r <= 312)
        a = (np.maximum(r, 1) ** -3 * (1 + .02 * np.cos(5 * theta))).astype(np.float32)
        def ripple(q):
            use = valid & np.isfinite(q) & (r < 192)
            bins = np.floor(r[use] * 4).astype(int)
            bins -= bins.min()
            counts = np.bincount(bins)
            prof = (np.bincount(bins, q[use]) / np.maximum(counts, 1))[counts > 30]
            return np.std((prof - gaussian_filter1d(prof, 24))[30:-30])
        old = rhef_normalize(a, r, np.arange(0, r.max() + 4, 2), valid=valid, upsilon=None)
        new = rhef_continuous_normalize(a, r, 2, valid=valid)
        flat = rhef_continuous_normalize(a * r ** 3, r, 2, valid=valid)
        self.assertLess(ripple(new), .2 * ripple(old))
        self.assertLess(ripple(new), 1.3 * ripple(flat))
        # Positive control: the metric must detect deliberately added rings.
        self.assertGreater(ripple(new + .1 * np.sin(2 * np.pi * r / 4)), 2 * ripple(new))
        signal = .005 * np.sin(37 * theta) * np.exp(-((r - 200) / 60) ** 4)
        change = rhef_continuous_normalize(a * np.exp(signal), r, 2, valid=valid) - new
        use = valid & np.isfinite(change)
        self.assertGreater(np.corrcoef(change[use], signal[use])[0, 1], .5)

    def test_invalid_configuration(self):
        a = np.ones((4, 4))
        for kwargs in (dict(bin_px=0), dict(min_count=1), dict(quantile_count=2), dict(valid=np.ones((2, 2)))):
            with self.assertRaises(ValueError):
                rhef_continuous_normalize(a, a, **kwargs)
