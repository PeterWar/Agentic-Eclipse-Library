import unittest

from utils.helpers import recommended_radial_bins


class RadialBinTests(unittest.TestCase):
    def test_linear_resolution_scaling(self):
        self.assertEqual(recommended_radial_bins(100, 900), 200)
        self.assertEqual(recommended_radial_bins(400, 3600), 800)

    def test_logarithmic_inner_ring_width(self):
        for scale in (1, 4):
            inner, outer = 100 * scale, 900 * scale
            count = recommended_radial_bins(inner, outer, logarithmic=True)
            self.assertLessEqual(inner * ((outer / inner) ** (1 / count) - 1), 4)

    def test_invalid_bounds(self):
        for inner, outer in ((0, 100), (10, 10), (100, 10)):
            with self.assertRaises(ValueError):
                recommended_radial_bins(inner, outer)
