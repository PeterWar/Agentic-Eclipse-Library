"""Boundary and adjacent-value sweeps for every numerical filter control."""
import unittest
import warnings

import numpy as np

from core.filters import FilterWorker


class FilterParameterBoundaryTests(unittest.TestCase):
    def test_secondary_controls_and_adjacent_values_are_finite(self):
        worker = FilterWorker()
        image = np.random.default_rng(23).uniform(.1, 1, (64, 64)).astype(np.float32)
        families = [
            ("MGN", dict(gamma_val=32, k_val=70, h_val=70, trunc_val=3),
             dict(gamma_val=(1, 2, 31, 32, 33, 99, 100), k_val=(1, 2, 69, 70, 71, 199, 200),
                  h_val=(0, 1, 69, 70, 71, 99, 100), trunc_val=(1, 2, 3, 4, 5, 6)),
             lambda p: worker.run_mgn_native(image, 50, **p)),
            ("RHEF", dict(app_radius_val=10, upsilon_val=35, bin_px=1),
             dict(app_radius_val=(0, 1, 9, 10, 11, 39, 40), upsilon_val=(1, 2, 34, 35, 36, 99, 100),
                  bin_px=(.5, .6, .9, 1, 1.1, 9.9, 10)),
             lambda p: worker.run_rhef_native(image, 50, sun_x=32, sun_y=32, sun_r=8, **p)),
            ("ACHF", dict(base_kernel_param=20, boost_param=20, intensity_threshold=10, background=10),
             dict(base_kernel_param=(5, 6, 9, 10, 11, 19, 20, 21, 199, 200),
                  boost_param=(10, 11, 19, 20, 21, 49, 50),
                  intensity_threshold=(0, 1, 9, 10, 11, 99, 100), background=(0, 1, 9, 10, 11, 98, 99)),
             lambda p: worker.run_achf(image, 50, sun_x=32, sun_y=32, sun_r=8, **p)),
            ("FNRGF", dict(order_fourier=21, angular_segments=64, cutoff_val=0, app_radius_val=10,
                           rmax_val=61, nbins_val=20, width_function="std", radial_binning="linear", apply_mask=0),
             dict(order_fourier=(19, 20, 21, 22, 23), angular_segments=(64, 128, 256),
                  cutoff_val=(0, 1, 20, 21, 22), app_radius_val=(5, 6, 9, 10, 11, 24, 25),
                  rmax_val=(26, 27, 59, 60, 61, 62), nbins_val=(1, 2, 19, 20, 21, 801, 802, 803, 2000),
                  width_function=("std", "mad"), radial_binning=("linear", "log"), apply_mask=(0, 1, 99, 100)),
             lambda p: worker.run_fnrgf_native(image, 32, sun_x=32, sun_y=32, sun_r=8, **p)),
        ]
        for family, base, controls, run in families:
            for control, values in controls.items():
                for value in values:
                    with self.subTest(filter=family, control=control, value=value), warnings.catch_warnings():
                        warnings.simplefilter("error", RuntimeWarning)
                        out = run(dict(base, **{control: value}))
                        self.assertEqual(out.shape, image.shape)
                        self.assertTrue(np.isfinite(out).all())
                        # All but ACHF map or clip their full effect to input units.
                        if family != "ACHF":
                            self.assertGreaterEqual(float(out.min()), float(image.min()) - 1e-6)
                            self.assertLessEqual(float(out.max()), float(image.max()) + 1e-6)
