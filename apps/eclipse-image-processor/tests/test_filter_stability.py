"""Cross-filter regressions for unit scaling, finite output and bypasses."""
import unittest
import warnings

import numpy as np

from core.filters import FilterWorker
from core.image_data import normalize_observed


def filter_calls(worker, strength=50):
    return {
        "FNRGF": lambda a: worker.run_fnrgf_native(a, strength, 21, 64, 0, 10, 61, 20, 32, 32, 8),
        "RHEF": lambda a: worker.run_rhef_native(a, strength, 10, 35, 32, 32, 8),
        "MGN": lambda a: worker.run_mgn_native(a, strength, 32, 70, 70, 3),
        "WOW": lambda a: worker.run_wow_native(a, strength, 3),
        "tangential": lambda a: worker.run_tangential(a, strength, 32, 32, 8),
        "ACHF": lambda a: worker.run_achf(a, strength, 20, 20, 32, 32, 8),
    }


class FilterStabilityTests(unittest.TestCase):
    def setUp(self):
        self.worker = FilterWorker()
        self.image = np.random.default_rng(73).uniform(.1, 1, (64, 64)).astype(np.float32)

    def test_same_image_in_different_intensity_units(self):
        for name, run in filter_calls(self.worker).items():
            expected = run(self.image)
            for scale in (1e-25, 1e-8, 65535., 1e25):
                with self.subTest(filter=name, scale=scale), warnings.catch_warnings():
                    warnings.simplefilter("error", RuntimeWarning)
                    actual = run(self.image * scale) / scale
                    self.assertTrue(np.isfinite(actual).all())
                    np.testing.assert_allclose(actual, expected, rtol=3e-4, atol=3e-4)

    def test_integer_input_matches_floating_point_without_mutation(self):
        image = (self.image * 50000).astype(np.uint16)
        original = image.copy()
        for name, run in filter_calls(self.worker).items():
            with self.subTest(filter=name):
                actual = run(image)
                expected = run(image.astype(np.float32))
                np.testing.assert_allclose(actual, expected, rtol=2e-5, atol=.02)
                np.testing.assert_array_equal(image, original)

    def test_nonfinite_active_input_is_rejected(self):
        for value in (np.nan, np.inf, -np.inf):
            image = self.image.copy()
            image[15, 15] = value
            for name, run in filter_calls(self.worker).items():
                with self.subTest(filter=name, value=value), self.assertRaises(ValueError):
                    run(image)

    def test_zero_strength_is_an_exact_independent_copy(self):
        for name, run in filter_calls(self.worker, strength=0).items():
            with self.subTest(filter=name):
                actual = run(self.image)
                np.testing.assert_array_equal(actual, self.image)
                self.assertIsNot(actual, self.image)

    def test_constant_and_zero_images_remain_spatially_constant(self):
        for value in (0., 7., -3.):
            image = np.full((64, 64), value, np.float32)
            for name, run in filter_calls(self.worker).items():
                with self.subTest(filter=name, value=value), warnings.catch_warnings():
                    warnings.simplefilter("error", RuntimeWarning)
                    actual = run(image)
                    self.assertTrue(np.isfinite(actual).all())
                    self.assertEqual(float(np.ptp(actual)), 0.)

    def test_display_normalization_has_no_absolute_epsilon(self):
        expected = normalize_observed(self.image)
        for scale in (1e-25, 1e-8, 65535., 1e25):
            np.testing.assert_allclose(normalize_observed(self.image * scale), expected, atol=1e-7)
        np.testing.assert_array_equal(normalize_observed(np.ones((3, 3))), 0)




    def test_finite_output_with_denoising_and_bilateral_wow(self):
        for image in (self.image, self.image - .5, np.eye(64, dtype=np.float32)):
            for bilateral in (None, 1):
                for levels in ([0, 0, 0], [1, 2, 3], [10, 10, 10]):
                    with self.subTest(bilateral=bilateral, levels=levels), warnings.catch_warnings():
                        warnings.simplefilter("error", RuntimeWarning)
                        out = self.worker.run_wow_native(
                            image, 100, 3, denoise_coefficients=levels, bilateral=bilateral)
                        self.assertTrue(np.isfinite(out).all())

    def test_combined_pipeline_does_not_mutate_or_emit_nonfinite_output(self):
        params = dict(
            pre_stretch_enabled=True, pre_stretch_mode="log", pre_stretch_val=1,
            noise_gate_enabled=True, noise_gate_str=20, noise_gate_thr=10,
            bilateral_enabled=True, bilateral_str=20, bilateral_d=10, bilateral_sc=30, bilateral_ss=50,
            fnrgf_enabled=True, fnrgf_str=32, fnrgf_ord=21, fnrgf_seg=64,
            fnrgf_cut=0, fnrgf_rad=10, fnrgf_rmax=61, fnrgf_nbins=20,
            mgn_enabled=True, mgn_str=10, mgn_gam=32,
            wow_enabled=True, wow_str=10, wow_scales=3, wow_denoise=[1, 2, 3],
            rhef_enabled=True, rhef_str=10, rhef_rad=10, rhef_upsilon=35,
            tangential_enabled=True, tangential_str=10, tangential_arc=10, tangential_gain=2,
            achf_enabled=True, achf_str=10, achf_kernel=20, achf_boost=20,
            sx=32, sy=32, sr=8,
        )
        results, errors = [], []
        self.worker.finished.connect(results.append)
        self.worker.failed.connect(errors.append)
        original = self.image.copy()
        self.worker.process_pipeline(self.image, params)
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 1)
        self.assertTrue(np.isfinite(results[0]).all())
        np.testing.assert_array_equal(self.image, original)
