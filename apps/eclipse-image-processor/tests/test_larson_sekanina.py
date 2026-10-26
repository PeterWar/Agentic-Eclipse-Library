"""Classic residual, observed support, resolution and Photoshop reconstruction."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import tifffile

from core.filters import FilterWorker, larson_sekanina_residual
from core.pipeline import apply_filter, prepare_parameters
from core.layer_export import export_layer_package, linear_light, linear_detail_layer, to_u16


class LarsonSekaninaTests(unittest.TestCase):
    def test_classic_formula_at_exact_quarter_turns(self):
        a = np.arange(81, dtype=float).reshape(9, 9)**2
        original = a.copy()
        d = larson_sekanina_residual(a, 4, 4, 1, 0, 90)
        self.assertAlmostEqual(d[4, 7], 2*a[4, 7]-a[1, 4]-a[7, 4])
        # dr=1 samples the same inward radius for BOTH angular shifts.
        d = larson_sekanina_residual(a, 4, 4, 1, 1, 90)
        self.assertAlmostEqual(d[4, 7], 2*a[4, 7]-a[2, 4]-a[6, 4])
        np.testing.assert_array_equal(a, original)

    def test_constant_radial_null_and_harmonic_response(self):
        y, x = np.indices((161, 161))
        r = np.hypot(x-80.3, y-79.8)
        angle = np.arctan2(y-79.8, x-80.3)
        d = larson_sekanina_residual(np.full(r.shape, 7.), 80.3, 79.8, 8, 2, 5)
        np.testing.assert_allclose(d, 0, atol=1e-14)
        radial = 10+.01*r
        d = larson_sekanina_residual(radial, 80.3, 79.8, 8, 0, 5)
        use = (r > 30) & (r < 65)
        np.testing.assert_allclose(d[use], 0, atol=.0001)
        a = 10+np.cos(6*angle)
        d = larson_sekanina_residual(a, 80.3, 79.8, 8, 0, 10)
        expected = 2*(1-np.cos(6*np.deg2rad(10)))*np.cos(6*angle)
        np.testing.assert_allclose(d[use], expected[use], atol=.012)

    def test_missing_data_disk_edges_and_rotational_symmetry(self):
        a = np.random.default_rng(10).uniform(1, 3, (65, 65))
        valid = np.ones(a.shape, bool)
        valid[:15, :25] = False
        altered = a.copy()
        altered[~valid] = np.nan
        y, x = np.indices(a.shape)
        disk = np.hypot(x-32, y-32) <= 8
        altered[disk] = 1e20
        first = larson_sekanina_residual(a, 32, 32, 8, 1, 17, valid)
        second = larson_sekanina_residual(altered, 32, 32, 8, 1, 17, valid)
        np.testing.assert_array_equal(first, second)
        np.testing.assert_array_equal(first[~valid | disk], 0)
        rotated = larson_sekanina_residual(np.rot90(a), 32, 32, 8, 1, 17, np.rot90(valid))
        np.testing.assert_allclose(rotated, np.rot90(first), atol=1e-12)
        # A rotation sends this corner beyond the frame: no reflected/wrapped signal.
        self.assertEqual(first[0, -1], 0)

    def test_pipeline_strength_bypass_and_statistics_adapter(self):
        a = np.random.default_rng(3).uniform(1, 2, (65, 65)).astype(np.float32)
        p = dict(sx=32., sy=32., sr=8., larson_sekanina_enabled=True,
                 larson_sekanina_str=37, larson_sekanina_radial=1., larson_sekanina_angular=5.)
        expected = a+.37*larson_sekanina_residual(a, 32, 32, 8, 1, 5)
        np.testing.assert_allclose(apply_filter(FilterWorker(), a, p), expected, atol=1e-7)
        np.testing.assert_allclose(apply_filter(FilterWorker(), a, dict(p,larson_sekanina_str=200)),
                                   a+2*larson_sekanina_residual(a,32,32,8,1,5),atol=1e-6)
        for gain in (-1,201,np.nan):
            with self.assertRaises(ValueError):
                apply_filter(FilterWorker(),a,dict(p,larson_sekanina_str=gain))
        for params in (dict(p, larson_sekanina_str=0), dict(p, larson_sekanina_radial=0., larson_sekanina_angular=0.), dict(p, larson_sekanina_enabled=False)):
            np.testing.assert_array_equal(apply_filter(FilterWorker(), a, params), a)
        valid = np.ones(a.shape, bool)
        valid[5:9, 5:9] = False
        image = np.where(valid, a, np.nan)
        for exclusions in ({}, dict(statistics_exclude_lunar=True, statistics_guard_px=2)):
            out = apply_filter(FilterWorker(), image, dict(p, valid_mask=valid, **exclusions))
            self.assertTrue(np.isnan(out[~valid]).all())
            self.assertTrue(np.isfinite(out[valid]).all())

    def test_resolution_and_invalid_parameters(self):
        p = dict(sx=10., sy=12., sr=3., larson_sekanina_radial=1.5, larson_sekanina_angular=7.)
        scaled = prepare_parameters(p, (80, 80), (40, 40), (80, 80))
        self.assertEqual(scaled['larson_sekanina_radial'], 3.)
        self.assertEqual(scaled['larson_sekanina_angular'], 7.)
        a = np.ones((16, 16))
        for extra in (dict(radial_increment=-1), dict(angular_increment=181), dict(cx=np.nan), dict(radius=0), dict(valid=np.ones((2, 2)))):
            args = dict(cx=8, cy=8, radius=2, **{})
            args.update(extra)
            with self.assertRaises(ValueError):
                larson_sekanina_residual(a, **args)
        a[0, 0] = np.nan
        with self.assertRaises(ValueError):
            larson_sekanina_residual(a, 8, 8, 2)

    def test_layered_gain_200_and_default_three_degree_residual(self):
        from core.layer_engine import LayerEngine
        a=np.random.default_rng(18).uniform(1,2,(48,64)).astype(np.float32)
        p=dict(sx=32.,sy=24.,sr=5.,larson_sekanina_enabled=True,
               larson_sekanina_str=100,larson_sekanina_opacity=75,layered_model=True)
        worker=FilterWorker();engine=LayerEngine()
        normal=engine.layer(worker,a,p,'larson_sekanina')
        amplified=engine.layer(worker,a,dict(p,larson_sekanina_str=200),'larson_sekanina')
        expected=to_u16(.5+2*(normal['image'].astype(float)/65535-.5))
        np.testing.assert_allclose(amplified['image'],expected,atol=2,rtol=0)
        np.testing.assert_array_equal(larson_sekanina_residual(a,32,24,5),
                                      larson_sekanina_residual(a,32,24,5,0,3))
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'layers'
            export_layer_package(worker,a,dict(p,larson_sekanina_str=200),{},'test.tif',out)
            manifest=json.loads((out/'recipe.json').read_text())
            self.assertTrue(any(layer['mode']=='Linear Light' for layer in manifest['layers']))
            self.assertTrue((out/manifest['combined']).is_file())

    def test_linear_light_signed_addition_and_quantized_export(self):
        base = np.array([[.2, .5, .8]])
        detail = np.array([[-.1, 0., .1]])
        valid = np.ones(base.shape, bool)
        layer, report = linear_detail_layer(detail, valid, 1.)
        self.assertEqual(report['center'], 0)
        np.testing.assert_allclose(linear_light(base, layer, 1, 1), base+detail)
        np.testing.assert_allclose(linear_light(base, .5, 1, 1), base)
        np.testing.assert_allclose(linear_light(base, layer, 0, 1), base)
        np.testing.assert_allclose(linear_light(base, layer, 1, 0), base)
        y, x = np.indices((48, 64))
        a = (2+np.exp(-np.hypot(x-32, y-24)/10)+.03*np.sin(x)).astype(np.float32)
        p = dict(sx=32., sy=24., sr=5., larson_sekanina_enabled=True,
                 larson_sekanina_str=200, larson_sekanina_radial=1., larson_sekanina_angular=5.)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'layers'
            export_layer_package(FilterWorker(), a, p, {}, 'test.tif', out)
            manifest = json.loads((out/'recipe.json').read_text())
            self.assertEqual(len(manifest['layers']), 3)
            record = manifest['layers'][2]
            self.assertEqual(record['mode'], 'Linear Light')
            self.assertEqual(record['file'], '03_LARSON_SEKANINA_LinearLight.tif')
            self.assertEqual(record['normalization']['center'], 0)
            base = tifffile.imread(out/manifest['layers'][1]['file'])[..., 0]/65535.
            rgba = tifffile.imread(out/record['file'])
            self.assertEqual(rgba.dtype, np.uint16)
            self.assertEqual(rgba.shape, (48, 64, 4))
            self.assertEqual(rgba[24, 32, 3], 0)
            expected = to_u16(linear_light(base, rgba[..., 0]/65535., rgba[..., 3]/65535., record['opacity_255']/255.).astype(np.float32))
            combined = tifffile.imread(out/manifest['combined'])
            np.testing.assert_array_equal(combined[..., 0], expected)
            self.assertIn('BlendMode.LINEARLIGHT', (out/'Load_layers_Photoshop.jsx').read_text())
