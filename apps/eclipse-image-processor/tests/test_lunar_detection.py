import unittest

import numpy as np

from gui.app import EclipseProcessorApp


class LunarDetectionTests(unittest.TestCase):
    def test_off_center_disk_at_full_resolution(self):
        # Fractional limb coordinates on a non-square image larger than preview.
        y, x = np.indices((1601, 2203), dtype=np.float32)
        cx, cy, radius = 1037.4, 763.7, 281.2
        distance = np.hypot(x - cx, y - cy)
        image = np.clip((distance - radius) / 2 + 0.5, 0, 1)
        actual = EclipseProcessorApp.detect_lunar_limb(image)
        np.testing.assert_allclose(actual, (cx, cy, radius), atol=1)

    def test_uniform_and_nonfinite_images(self):
        image = np.zeros((240, 320), dtype=np.float32)
        image[0, :3] = (np.nan, np.inf, -np.inf)
        actual = EclipseProcessorApp.detect_lunar_limb(image)
        self.assertEqual(actual, (160, 120, 60))

    def test_linear_hdr_limb_is_not_lost_to_saturated_outliers(self):
        y, x = np.indices((801, 1003), dtype=np.float32)
        cx, cy, radius = 467.4, 413.7, 112.2
        distance = np.hypot(x-cx, y-cy)
        edge = np.clip((distance-radius)/2+.5, 0, 1)
        image = edge*(.003+.02*(radius/np.maximum(distance, radius))**4)
        image[40:43, 50:53] = 1000  # Saturated source far brighter than corona.
        before = image.copy()
        for scale, offset in ((1., 0.), (65535., -3.), (1e-8, 0.)):
            with self.subTest(scale=scale, offset=offset):
                actual = EclipseProcessorApp.detect_lunar_limb(image*scale+offset)
                np.testing.assert_allclose(actual, (cx, cy, radius), atol=1)
        np.testing.assert_array_equal(image, before)

    def test_bright_outer_arc_does_not_pull_center_away_from_limb(self):
        y, x = np.indices((801, 1003), dtype=np.float32)
        cx, cy, radius = 467.4, 413.7, 112.2
        distance = np.hypot(x-cx, y-cy)
        image = .2*np.clip((distance-radius)/3+.5, 0, 1)
        # A sharp bright arc outside the upper limb competes with the true edge.
        angle = np.arctan2(y-cy, x-cx)
        arc = (angle > -2.2) & (angle < -1.0)
        image += arc*np.clip((distance-radius-10)/.6+.5, 0, 1)*.8
        actual = EclipseProcessorApp.detect_lunar_limb(image)
        np.testing.assert_allclose(actual, (cx, cy, radius), atol=1)

    def test_missing_disk_is_enclosed_about_returned_integer_center(self):
        y, x = np.indices((401, 503), dtype=np.float32)
        for rx, ry in ((70., 70.), (70., 72.)):
            with self.subTest(rx=rx, ry=ry):
                hole = ((x-247.4)/rx)**2 + ((y-193.7)/ry)**2 <= 1
                image = np.ones(x.shape, dtype=np.float32)
                image[hole] = np.nan
                # Separate defects and frame-edge gaps must not enlarge the disk.
                image[10, 10] = np.inf
                image[:2] = np.nan
                before = image.copy()
                cx, cy, radius = EclipseProcessorApp.detect_lunar_limb(image)
                np.testing.assert_allclose((cx, cy), (247.4, 193.7), atol=1)
                maximum_distance = np.hypot(x[hole]-cx, y[hole]-cy).max()
                self.assertGreaterEqual(radius, maximum_distance)
                self.assertLess(radius-maximum_distance, 1)
                np.testing.assert_array_equal(image, before)
