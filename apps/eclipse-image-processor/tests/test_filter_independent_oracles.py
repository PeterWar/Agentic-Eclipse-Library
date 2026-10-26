"""Independent, slow spatial oracles for signed ACHF.

Small deterministic inputs keep the scalar implementation independent of the
vectorized shift/slice machinery and exercise partial support at image borders.
"""
import math
import unittest

import numpy as np

from core.filters import adaptive_circular_highpass


def scalar_achf(image, radius, threshold, gain, background, labels, scale=1.):
    output = np.empty(image.shape, dtype=np.float64)
    sigma = max(radius/3, .25*scale)
    for y, x in np.ndindex(image.shape):
        center = float(image[y, x])
        weighted_sum, total_weight = center, 1.
        for dy in range(-math.ceil(radius), math.ceil(radius)+1):
            for dx in range(-math.ceil(radius), math.ceil(radius)+1):
                if (dx == 0 and dy == 0) or dx*dx+dy*dy > radius*radius:
                    continue
                yp, xp, ym, xm = y+dy, x+dx, y-dy, x-dx
                if not (0 <= yp < image.shape[0] and 0 <= ym < image.shape[0]
                        and 0 <= xp < image.shape[1] and 0 <= xm < image.shape[1]):
                    continue
                if labels[yp, xp] != labels[y, x] or labels[ym, xm] != labels[y, x]:
                    continue
                if abs(float(image[yp, xp])-center) > threshold or abs(float(image[ym, xm])-center) > threshold:
                    continue
                weight = math.exp(-(dx*dx+dy*dy)/(2*sigma*sigma))
                weighted_sum += weight*float(image[yp, xp])
                total_weight += weight
        output[y, x] = background*center+gain*(center-weighted_sum/total_weight)
    return output


def explicit_gaussian(image, sigma):
    """Direct separable summation with half-sample symmetric boundary extension."""
    radius = int(4*sigma+.5)
    offsets = np.arange(-radius, radius+1)
    kernel = np.exp(-.5*(offsets/sigma)**2)
    kernel /= kernel.sum()
    padded = np.pad(image.astype(float), radius, mode="symmetric")
    output = np.zeros(image.shape)
    for y, x in np.ndindex(image.shape):
        patch = padded[y:y+2*radius+1, x:x+2*radius+1]
        output[y, x] = np.sum(patch*kernel[:, None]*kernel[None, :])
    return output


class IndependentOracleTests(unittest.TestCase):
    def test_achf_scalar_reference_at_borders_regions_and_fractional_support(self):
        rng = np.random.default_rng(193)
        for shape in ((1, 1), (1, 9), (8, 1), (8, 11)):
            image = rng.normal(2, 3, shape)
            labels = np.indices(shape)[1] > shape[1]//2
            original = image.copy()
            for radius in (.5, .75, 1., 1.5, 2.3, 5.):
                for threshold in (0., 2., 100.):
                    with self.subTest(shape=shape, radius=radius, threshold=threshold):
                        expected = scalar_achf(image, radius, threshold, 2., .1, labels)
                        actual = adaptive_circular_highpass(image, radius, threshold, regions=labels)
                        np.testing.assert_allclose(actual, expected, atol=2e-6, rtol=2e-6)
            np.testing.assert_array_equal(image, original)

    def test_achf_scaled_minimum_width_matches_scalar_reference(self):
        image = np.random.default_rng(74).normal(size=(7, 8))
        labels = np.zeros(image.shape)
        for scale in (.5, 1., 4.):
            expected = scalar_achf(image, 1.2, 100., 3., .2, labels, scale)
            actual = adaptive_circular_highpass(image, 1.2, 100., gain=3., background=.2, spatial_scale=scale)
            np.testing.assert_allclose(actual, expected, atol=1e-6, rtol=1e-6)
