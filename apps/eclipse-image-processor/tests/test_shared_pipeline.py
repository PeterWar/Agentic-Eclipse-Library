import unittest
from unittest.mock import Mock
import numpy as np

from core.filters import FilterWorker
from core.pipeline import apply_filter, execute_pipeline, prepare_parameters


class SharedPipelineTests(unittest.TestCase):
    def test_rectangular_pixel_centres_and_resolution_units(self):
        source = dict(sx=103.7, sy=58.1, sr=20., bilateral_d=10, tangential_arc=20,
                      achf_kernel=30, rhef_bin_px=2, fnrgf_nbins=80, rhef_mode="continuous")
        preview = prepare_parameters(source, (121, 207), (60, 103), (60, 103))
        full = prepare_parameters(source, (121, 207), (60, 103), (121, 207))
        self.assertAlmostEqual(preview["sx"], (103.7 + .5) * 103 / 207 - .5)
        self.assertAlmostEqual(preview["sy"], (58.1 + .5) * 60 / 121 - .5)
        self.assertEqual(preview["rhef_bin_px"], 2)
        self.assertAlmostEqual(full["rhef_bin_px"], 2 * np.sqrt(121 / 60 * 207 / 103))
        self.assertEqual(full["rhef_mode"], "continuous")
        self.assertEqual(source["sr"], 20)
        self.assertNotIn("mgn_sigmas", source)

    def test_numerical_dispatch_rejects_chaining_before_calling_any_filter(self):
        image=np.ones((32,32),np.float32)
        worker=Mock()
        with self.assertRaisesRegex(ValueError,'only one filter'):
            apply_filter(worker,image,dict(fnrgf_enabled=True,mgn_enabled=True))
        worker.run_fnrgf_native.assert_not_called()
        worker.run_mgn_native.assert_not_called()
        np.testing.assert_array_equal(image,1.)

    def test_qt_preview_and_synchronous_export_have_identical_results(self):
        image = np.random.default_rng(45).uniform(1, 100, (80, 100)).astype(np.float32)
        worker = FilterWorker()
        params = dict(sx=50, sy=40, sr=10, rhef_enabled=True, rhef_mode="continuous",
                      rhef_str=50, rhef_rad=10, rhef_upsilon=35, rhef_bin_px=2,
                      mgn_enabled=True, mgn_str=10, mgn_gam=32)
        emitted, failed = [], []
        worker.finished.connect(emitted.append)
        worker.failed.connect(failed.append)
        worker.process_pipeline(image, params)
        self.assertEqual(failed, [])
        np.testing.assert_array_equal(emitted[0], execute_pipeline(worker, image, params))

    def test_invalid_resolution_and_missing_input(self):
        with self.assertRaises(ValueError):
            prepare_parameters({}, (0, 100), (50, 50), (100, 100))
        with self.assertRaises(ValueError):
            execute_pipeline(FilterWorker(), None, {})
