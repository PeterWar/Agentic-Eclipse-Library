import unittest
import numpy as np
import limb_qa as q


class QAContract(unittest.TestCase):
    def test_phase_reversal_must_fail_even_relative_to_reversed_interior(self):
        h, w = 80, 128
        yy, xx = np.mgrid[:h, :w]
        signal = np.sin(xx*.53)
        distance = yy*.5
        theta = np.zeros_like(distance)+90
        result = q.phase_transfer(signal, -signal, np.ones((h, w), bool), distance, theta)
        bands = result["top"]["bands"]
        supported = [b for b in bands if b["gain"] is not None]
        self.assertTrue(supported)
        self.assertTrue(all(abs(b["gain"]+1) < 1e-12 for b in supported))
        self.assertTrue(all(b["relative_gate_0p90_1p10"] is False for b in supported))

    def test_phase_gain_and_offset(self):
        yy, xx = np.mgrid[:80, :128]
        signal = np.sin(xx*.53)
        dist, theta = yy*.5, np.zeros_like(yy)+90
        result = q.phase_transfer(signal, .5*signal+.123, np.ones_like(yy, bool), dist, theta)
        interior = result["top"]["interior_reference"]
        self.assertAlmostEqual(interior["gain"], .5)
        self.assertAlmostEqual(interior["offset"], .123)

    def test_gradient_excludes_neighbors_of_holes(self):
        valid = np.ones((20, 20), bool)
        valid[10, 10] = False
        lum = np.ones((20, 20)); lum[10, 10] = 1e9
        radial, tangent, support = q.gradients(lum, valid, np.ones_like(lum), np.zeros_like(lum))
        self.assertFalse(support[10, 11])
        self.assertFalse(support[10, 9])
        self.assertTrue(np.all(radial[support] == 0))

    def test_null_shift_does_not_wrap(self):
        mask = q.shifted(np.ones((10, 12), bool), 2, -3)
        self.assertFalse(mask[:2].any())
        self.assertFalse(mask[:, -3:].any())
        self.assertEqual(mask.sum(), 8*9)

    def test_radial_cuts_exclude_fractionally_invalid_bilinear_stencil(self):
        lum = np.ones((40, 40)); valid = np.ones_like(lum, bool)
        valid[19:22, 25:28] = False
        r = q.radial_cuts(lum, valid, (0, 0, 40, 40), (20, 20, 6.5),
                          sectors=[("right", -1, 1)], distances=[0])
        self.assertEqual(r["right"]["valid_cuts"][0], 0)
        self.assertIsNone(r["right"]["median"][0])


if __name__ == "__main__":
    unittest.main()
