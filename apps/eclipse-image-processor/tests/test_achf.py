import unittest
import numpy as np
from core.filters import adaptive_circular_highpass, FilterWorker


class AdaptiveFilterTests(unittest.TestCase):
    def test_constant_background(self):
        a = np.full((21, 21), 7.0)
        np.testing.assert_allclose(adaptive_circular_highpass(a, 4, 1, background=.1), .7)

    def test_regions_and_threshold_prevent_edge_leakage(self):
        a = np.ones((21, 21)); a[:, 10:] = 100
        labels = a > 1
        for threshold, regions in [(200, labels), (10, None)]:
            result = adaptive_circular_highpass(a, 4, threshold, background=0, regions=regions)
            np.testing.assert_array_equal(result, 0)

    def test_impulse_symmetry_and_frequency_response(self):
        a = np.zeros((41, 41)); a[20, 20] = 1
        kernel = adaptive_circular_highpass(a, 5, 2, gain=2, background=.1)
        np.testing.assert_allclose(kernel, kernel[::-1, ::-1])
        np.testing.assert_allclose(kernel, kernel.T)
        spectrum = np.fft.fft2(np.fft.ifftshift(kernel))
        self.assertLess(np.max(np.abs(spectrum.imag)), 1e-6)
        self.assertAlmostEqual(spectrum[0, 0].real, .1, places=6)
        self.assertGreater(spectrum[20, 20].real, 1)
        self.assertLess(kernel.min(), 0)

    def test_rotation_with_adaptive_rejection(self):
        a = np.random.default_rng(4).random((23, 23))
        result = adaptive_circular_highpass(a, 4, .3)
        rotated = adaptive_circular_highpass(np.rot90(a), 4, .3)
        np.testing.assert_allclose(rotated, np.rot90(result), atol=1e-6)

    def test_strength_zero(self):
        a = np.arange(81, dtype=np.float32).reshape(9, 9)
        result = FilterWorker().run_achf(a, 0, 20, 20, 4, 4, 2)
        np.testing.assert_array_equal(result, a)
        self.assertIsNot(result, a)

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            adaptive_circular_highpass(np.full((3, 3), np.nan), 2, 1)


if __name__ == '__main__':
    unittest.main()
