"""Native levels anchor un-stretched previews without changing native values."""
import unittest
import numpy as np
from core.image_data import normalize_observed,observed_bounds,resize_observed
from core.presentation import normalized_base


class DisplayReferenceTests(unittest.TestCase):
    def test_shared_levels_remove_uniform_background_shift(self):
        full=np.full((128,160),100,np.float32)
        full[20:45,30:55]=5000;full[80,80]=0
        small=resize_observed(full,(40,32))
        display=dict(normalization_range=observed_bounds(full))
        fast=normalized_base(small,display)
        native=resize_observed(normalized_base(full,display),(40,32))
        sky=np.ones(small.shape,bool);sky[4:13,6:15]=False;sky[18:23,18:23]=False
        np.testing.assert_allclose(fast[sky],native[sky],atol=1e-7)
        old=normalized_base(small,{})
        self.assertGreater(abs(float(np.mean(old[sky])-np.mean(native[sky]))),.01)

    def test_native_normalization_preserves_shared_levels_and_missing_pixels(self):
        image=np.random.default_rng(9).uniform(-3,20,(60,80)).astype(np.float32)
        image[4,5]=np.nan
        np.testing.assert_array_equal(normalized_base(image,{}),
            normalized_base(image,dict(normalization_range=observed_bounds(image))))

    def test_range_validation_constant_images_and_display_clipping(self):
        for invalid in ((1,0),(0,np.inf),(np.nan,1),(0,)):
            with self.assertRaises(ValueError):normalize_observed(np.ones((3,3)),invalid)
        np.testing.assert_array_equal(normalize_observed(np.ones((3,3)),(1,1)),0)
        np.testing.assert_array_equal(normalize_observed(np.array([[-1,0,1,2]]),(0,1)),[[0,0,1,1]])
        self.assertEqual(observed_bounds(np.array([[0,65535]],np.uint16)),(0,65535))
