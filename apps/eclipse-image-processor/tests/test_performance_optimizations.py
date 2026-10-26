"""Equivalence, support boundaries, ordered parallel reductions and cancellation."""
import unittest
from unittest.mock import patch
from threading import Event, Thread
import numpy as np
from scipy.ndimage import convolve1d
from core.filters import FilterWorker, mgn_normalize
from core.masked_filters import MaskedWorker
from core.cancellation import cancellation_scope, ProcessingCancelled
from core.tangential import tangential_detail


class OptimizationTests(unittest.TestCase):
    def test_sparse_starlet_matches_dense_with_reflection_and_dtype_rounding(self):
        rng = np.random.default_rng(418)
        for shape in ((3, 5), (17, 23)):
            for dtype in (np.float32, np.float64):
                a = rng.uniform(-100, 500, shape).astype(dtype)
                valid = rng.random(shape) > .3
                a[~valid] = np.nan
                worker = MaskedWorker(FilterWorker(), valid)
                for step in (1, 4, 8, 16, 128):
                    kernel = np.zeros(4*step+1)
                    kernel[::step] = np.array([1, 4, 6, 4, 1])/16
                    signal = np.where(valid, a, 0)
                    support = valid.astype(float)
                    for axis in (0, 1):
                        signal = convolve1d(signal, kernel, axis=axis, mode='reflect')
                        support = convolve1d(support, kernel, axis=axis, mode='reflect')
                    expected = np.divide(signal, support, out=np.zeros_like(signal), where=support > 0)
                    actual = worker.starlet_blur(a, step, None)
                    np.testing.assert_allclose(actual, expected, rtol=2e-7, atol=1e-12)
                    self.assertEqual(actual.dtype, expected.dtype)

    def test_mgn_parallel_reduction_equals_serial_with_and_without_mask(self):
        a = np.random.default_rng(3).uniform(.1, 9, (512, 512)).astype(np.float32)
        valid = np.ones(a.shape, bool)
        valid[100:150, 120:180] = False
        for masked in (False, True):
            def run():
                if masked:
                    return MaskedWorker(FilterWorker(), valid).run_mgn_native(a, 37, 32, 70, 70, 3, (1., 2., 4.))
                return mgn_normalize(a, sigma=(1., 2., 4.))
            with patch('core.filters.filter_cpu_budget', return_value=1):
                expected = run()
            with patch('core.filters.filter_cpu_budget', return_value=4):
                actual = run()
            np.testing.assert_array_equal(actual, expected)

    def test_mgn_helper_threads_inherit_cancellation(self):
        entered, release, cancel = Event(), Event(), Event()
        a = np.ones((512, 512), np.float32)
        from core.filters import gaussian_filter
        def slow(*args, **kwargs):
            entered.set()
            if not release.wait(3):
                raise AssertionError('Convolution not released')
            return gaussian_filter(*args, **kwargs)
        outcomes = []
        def run():
            try:
                with cancellation_scope(cancel):
                    mgn_normalize(a)
            except ProcessingCancelled:
                outcomes.append('cancelled')
        with patch('core.filters.filter_cpu_budget', return_value=4), patch('core.filters.gaussian_filter', side_effect=slow):
            thread = Thread(target=run)
            thread.start()
            try:
                self.assertTrue(entered.wait(3))
                cancel.set()
            finally:
                release.set()
                thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(outcomes, ['cancelled'])

    def test_masked_mgn_helper_threads_cancel_before_the_next_blur(self):
        entered, release, cancel = Event(), Event(), Event()
        a = np.ones((512, 512), np.float32)
        a[100, 100] = 2
        valid = np.ones(a.shape, bool)
        valid[:2] = False
        from core.masked_filters import gaussian_filter
        def slow(*args, **kwargs):
            entered.set()
            if not release.wait(3):
                raise AssertionError('Support blur not released')
            return gaussian_filter(*args, **kwargs)
        outcomes = []
        def run():
            try:
                with cancellation_scope(cancel):
                    MaskedWorker(FilterWorker(), valid).run_mgn_native(a, 100, 32, 70, 70, 3, (1., 2., 4.))
            except ProcessingCancelled:
                outcomes.append('cancelled')
        with patch('core.filters.filter_cpu_budget', return_value=4), patch('core.masked_filters.gaussian_filter', side_effect=slow):
            thread = Thread(target=run)
            thread.start()
            try:
                self.assertTrue(entered.wait(3))
                cancel.set()
            finally:
                release.set()
                thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(outcomes, ['cancelled'])

    def test_angular_fft_matches_direct_finite_kernel_with_masks(self):
        rng = np.random.default_rng(82)
        for angle in (.1, 3., 30.):
            a = rng.uniform(.1, 3., (65, 81))
            valid = np.ones(a.shape, bool)
            valid[:10, :15] = False
            valid[25:35, 55:60] = False
            for constant in (False, True):
                image = np.full_like(a, 7) if constant else a
                args = (image, 39.3, 31.8, 8)
                with patch('core.tangential.FFT_MIN_RADIUS', 10**9):
                    expected = tangential_detail(*args, arc_sigma_deg=angle, valid=valid)
                with patch('core.tangential.FFT_MIN_RADIUS', 0):
                    actual = tangential_detail(*args, arc_sigma_deg=angle, valid=valid)
                np.testing.assert_allclose(actual, expected, rtol=3e-6, atol=3e-7)
