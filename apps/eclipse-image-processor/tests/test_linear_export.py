import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import tifffile

from core.linear_export import export_linear_sources, split_source_channels


class LinearSourceExportTests(unittest.TestCase):
    def test_rgb_and_luminance_keep_units_and_missing_pixels(self):
        rgb = np.arange(180, dtype=np.float32).reshape(6, 10, 3)-30
        rgb[2, 3] = np.nan
        mono, colour = split_source_channels(rgb)
        np.testing.assert_array_equal(colour, rgb)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'sources'
            export_linear_sources(mono, colour, 'eclipse.tif', out, 'linear')
            np.testing.assert_array_equal(tifffile.imread(out/'eclipse_LINEAR_RGB_float32.tif'), np.nan_to_num(rgb))
            np.testing.assert_array_equal(tifffile.imread(out/'eclipse_LINEAR_L_float32.tif'), np.nan_to_num(mono))
            self.assertEqual(tifffile.imread(out/'eclipse_LINEAR_RGB_float32.tif').dtype, np.float32)
            report = json.loads((out/'sources.json').read_text())
            self.assertEqual(report['missing_pixels'], 1)
            self.assertEqual(report['stretch'], 'none')
            with self.assertRaises(FileExistsError):
                export_linear_sources(mono, colour, 'eclipse.tif', out, 'linear')

    def test_unknown_and_nonlinear_inputs_are_not_labelled_linear(self):
        mono = np.arange(60, dtype=np.float32).reshape(6, 10)
        with tempfile.TemporaryDirectory() as tmp:
            for state in ('unknown', 'nonlinear'):
                out = Path(tmp)/state
                export_linear_sources(mono, None, 'mono.tif', out, state)
                self.assertTrue((out/'mono_INPUT_L_float32.tif').is_file())
                self.assertEqual(list(out.glob('*LINEAR*')), [])
                np.testing.assert_array_equal(tifffile.imread(out/'mono_INPUT_L_float32.tif'), mono)

    def test_planar_rgb_and_alpha_exclusions(self):
        rgb = np.arange(180, dtype=np.float32).reshape(6, 10, 3)
        mono, colour = split_source_channels(np.moveaxis(rgb, -1, 0))
        np.testing.assert_array_equal(colour, rgb)
        rgba = np.concatenate([rgb, np.ones((6, 10, 1), np.float32)], axis=-1)
        rgba[1, 2, 3] = 0
        mono, colour = split_source_channels(rgba)
        self.assertTrue(np.isnan(mono[1, 2]))
        self.assertTrue(np.isnan(colour[1, 2]).all())
        gray_alpha = np.stack([np.ones((6, 10)), np.zeros((6, 10))], axis=-1)
        with self.assertRaises(ValueError):
            split_source_channels(gray_alpha)
