"""Colour neutralization, gamut handling and Photoshop Color layer composition."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import tifffile

from core.colour import neutralize_tse, colour_layer, set_luminosity
from core.filters import FilterWorker
from core.layer_export import export_layer_package, overlay, to_u16


class ColourTests(unittest.TestCase):
    def setUp(self):
        self.t = np.linspace(.02, .95, 80*100).reshape(80, 100)
        self.rgb = np.stack([.1+.6*self.t, .05+.3*self.t, .025+.15*self.t], axis=-1).astype(np.float32)
        self.mono = self.rgb @ np.array([.299, .587, .114])

    def test_gain_only_percentiles_and_integer_white_equivalence(self):
        a, report = neutralize_tse(self.rgb)
        np.testing.assert_allclose(report['ratios'], [1, .5, .25], atol=1e-6)
        np.testing.assert_allclose(a[..., 0], a[..., 1], atol=1e-6)
        np.testing.assert_allclose(a[..., 1], a[..., 2], atol=1e-6)
        # Independent expression: gains and a common scale, without additive offsets.
        sample = self.rgb[::10, ::10].astype(float)
        low, high = np.percentile(sample.reshape(-1, 3), [1, 99], axis=0)
        ratio = (high-low)/(high-low)[1]
        ratio /= ratio.max()
        expected = self.rgb.astype(float)/ratio
        expected /= max(expected.max(),1.)
        np.testing.assert_allclose(a, expected, atol=1e-7)
        scaled, _ = neutralize_tse(self.rgb*65535, 65535)
        np.testing.assert_allclose(a, scaled, atol=2e-7)
        np.testing.assert_array_equal(self.rgb, np.stack([.1+.6*self.t, .05+.3*self.t, .025+.15*self.t], axis=-1).astype(np.float32))

    def test_brightness_gradient_does_not_become_a_colour_gradient(self):
        brightness=np.geomspace(.001,.95,100*120).reshape(100,120)
        rgb=brightness[...,None]*np.array([.493,1.,.728])
        rgb[0,0]=0
        result,report=neutralize_tse(rgb)
        positive=brightness>0
        positive[0,0]=False
        chroma=result[positive]/result[positive].sum(axis=-1,keepdims=True)
        np.testing.assert_allclose(chroma,np.full_like(chroma,1/3),atol=1e-7)
        np.testing.assert_array_equal(result[0,0],0)
        self.assertFalse(report['background_subtracted'])
        self.assertGreaterEqual(report['highlight_scale'],1)
        # Gains estimated on an otherwise neutral ramp must also preserve the
        # chromaticity of a coloured control at two different brightnesses.
        controls=rgb.copy()
        controls[1,1]=[.001,.002,.004]
        controls[1,2]=[.1,.2,.4]
        actual,_=neutralize_tse(controls)
        np.testing.assert_allclose(actual[1,1]/actual[1,1].sum(),
                                   actual[1,2]/actual[1,2].sum(),atol=1e-7)
        self.assertTrue(np.all((actual>=0)&(actual<=1)))

    def test_calibration_excludes_missing_and_rejects_undetermined_balance(self):
        rgb = self.rgb.copy(); rgb[0, 0] = np.nan
        result, report = neutralize_tse(rgb)
        self.assertTrue(np.isnan(result[0, 0]).all())
        self.assertTrue(np.isfinite(result[1:]).all())
        with self.assertRaises(ValueError):
            neutralize_tse(np.ones((30, 30, 3))*.5)
        with self.assertRaises(ValueError):
            neutralize_tse(np.ones((30, 30, 3))*2)

    def test_float_hdr_uses_one_scale_and_is_invariant_to_input_units(self):
        rgb = (self.rgb.astype(float)*20000-1000).astype(np.float32)
        rgb[0,0] = np.nan
        original = rgb.copy()
        expected, report = neutralize_tse(rgb,white=None)
        self.assertIn('shared observed maximum',report['white_source'])
        self.assertGreater(report['sampled_pixels'],2)
        self.assertTrue(np.isnan(expected[0,0]).all())
        self.assertTrue(np.isfinite(expected[1:]).all())
        for scale in (1e-8, .1, 65535.):
            actual, scaled_report = neutralize_tse(rgb*scale,white=None)
            np.testing.assert_allclose(actual,expected,atol=3e-7)
            np.testing.assert_allclose(scaled_report['ratios'],report['ratios'],rtol=1e-6)
        np.testing.assert_array_equal(rgb,original)
        with self.assertRaises(ValueError):
            neutralize_tse(np.full((30,30,3),np.nan),white=None)
        with self.assertRaises(ValueError):
            neutralize_tse(np.zeros((30,30,3)),white=None)
        with self.assertRaises(ValueError):
            neutralize_tse(np.ones((30,30,3))*2,white=None)

    def test_colour_blend_preserves_luminosity_and_is_in_gamut(self):
        rng = np.random.default_rng(7)
        colours = rng.uniform(0, 1, (80, 100, 3))
        for target in (np.zeros((80, 100)), np.ones((80, 100)), rng.uniform(0, 1, (80, 100))):
            output = set_luminosity(colours, target)
            np.testing.assert_allclose(output @ [.30, .59, .11], target, atol=1e-14)
            self.assertTrue(np.all((output >= 0) & (output <= 1)))
        display = colour_layer(self.rgb, self.mono, dict(mode='asinh', strength=10))
        self.assertEqual(display.shape, self.rgb.shape)
        self.assertTrue(np.isfinite(display).all())

    def test_exported_color_layer_matches_combined_and_loader_mode(self):
        params = dict(sx=50., sy=40., sr=10., tangential_enabled=True, tangential_str=15, tangential_arc=10, tangential_gain=2)
        display = dict(mode='asinh', strength=10, blend=1)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/'layers'
            export_layer_package(FilterWorker(), self.mono, params, display, 'original.tif', output, rgb=self.rgb)
            recipe = json.loads((output/'recipe.json').read_text())
            self.assertEqual([r['mode'] for r in recipe['layers']], ['Normal', 'Normal', 'Overlay', 'Color'])
            self.assertEqual(recipe['layers'][-1]['file'], '04_RGB_Color.tif')
            base = tifffile.imread(output/recipe['layers'][1]['file'])[..., 0]/65535.
            detail = tifffile.imread(output/recipe['layers'][2]['file'])/65535.
            mono = overlay(base, detail[..., 0], detail[..., 3], recipe['layers'][2]['opacity_255']/255.)
            colour = tifffile.imread(output/recipe['layers'][3]['file'])[..., :3]/65535.
            expected = to_u16(set_luminosity(colour, mono.astype(np.float32)))
            np.testing.assert_array_equal(tifffile.imread(output/recipe['combined']), expected)
            self.assertIn('BlendMode.COLORBLEND', (output/'Load_layers_Photoshop.jsx').read_text())
