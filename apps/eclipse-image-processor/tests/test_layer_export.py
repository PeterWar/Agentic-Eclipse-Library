"""Independent branches, neutral contrast and round-trip of an editable stack."""
import json
import re
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

import numpy as np
import tifffile

from core.filters import FilterWorker
from core.layer_export import branch_domain, export_layer_package, neutral_layer, overlay, to_u16, photoshop_loader
from core.presentation import ael_tone_map


class LayerExportTests(unittest.TestCase):
    def test_invalid_canvas_mask_and_rgb_are_rejected_before_writing(self):
        source=np.ones((8,10),np.float32)
        with tempfile.TemporaryDirectory() as tmp:
            destination=Path(tmp)/'layers'
            cases=((np.ones(8),{},None), (source,{'valid_mask':np.ones((1,1),bool)},None),
                   (source,{},np.ones((8,10,2))), (source,{},np.full((8,10,3),np.nan)))
            for image,params,rgb in cases:
                with self.subTest(shape=image.shape), self.assertRaises(ValueError):
                    export_layer_package(FilterWorker(),image,params,{},'source.tif',destination,rgb=rgb)
                self.assertFalse(destination.exists())

    def test_loader_uses_photoshop_extendscript_layer_blend_constants(self):
        # ExtendScript Layer.blendMode uses COLORBLEND, unlike ColorBlendMode.COLOR.
        script = photoshop_loader([dict(file='RGB.tif', mode='Color', opacity_255=255, visible=True)])
        self.assertEqual(set(re.findall(r'BlendMode\.(\w+)', script)),
                         {'NORMAL', 'OVERLAY', 'COLORBLEND', 'LINEARLIGHT', 'MULTIPLY'})

    def test_radial_application_and_outer_limit_are_exported_as_alpha_domain(self):
        p = dict(sx=10., sy=10., sr=2., fnrgf_rad=15, fnrgf_rmax=30, rhef_rad=20)
        fnrgf = branch_domain((21, 21), p, 'fnrgf')
        self.assertFalse(fnrgf[10, 12])
        self.assertTrue(fnrgf[10, 13])
        self.assertTrue(fnrgf[10, 15])
        self.assertFalse(fnrgf[10, 16])
        rhef = branch_domain((21, 21), p, 'rhef')
        self.assertFalse(rhef[10, 13])
        self.assertTrue(rhef[10, 14])

    def test_signed_mapping_constant_bypass_mask_and_units(self):
        values = np.arange(-24., 25.).reshape(7, 7)
        mask = np.ones(values.shape, bool)
        mask[0] = False
        mapped, report = neutral_layer(values, mask)
        rescaled, _ = neutral_layer(values * 1e-20, mask)
        np.testing.assert_allclose(mapped, rescaled)
        self.assertTrue(np.all(mapped[~mask] == .5))
        self.assertEqual(np.median(mapped[mask]), .5)
        self.assertTrue(np.all(np.diff(mapped[mask]) > 0))
        self.assertGreater(report['scale'], 0)
        flat, _ = neutral_layer(np.full((7, 7), 3.), mask)
        np.testing.assert_array_equal(flat, .5)
        empty, _ = neutral_layer(values, np.zeros_like(mask))
        np.testing.assert_array_equal(empty, .5)
        with self.assertRaises(ValueError):
            neutral_layer(np.array([[np.nan]]), np.ones((1, 1), bool))

    def test_overlay_neutral_and_zero_opacity_are_identity(self):
        a = np.linspace(0, 1, 45).reshape(5, 9)
        np.testing.assert_array_equal(overlay(a, np.full_like(a, .5), np.ones_like(a), 1), a)
        np.testing.assert_array_equal(overlay(a, 0, np.ones_like(a), 0), a)
        np.testing.assert_array_equal(overlay(a, 0, np.zeros_like(a), 1), a)

    def test_independent_full_strength_branches_from_single_preparation(self):
        source = np.linspace(1, 5, 64).reshape(8, 8).astype(np.float32)
        worker = Mock()
        worker.run_mgn_native.side_effect = lambda a, *args, **kw: a ** 2
        worker.run_tangential.side_effect = lambda a, *args, **kwargs: a + np.arange(64).reshape(8, 8) % 3
        p = dict(sx=4., sy=4., sr=1., mgn_enabled=True, mgn_str=20, mgn_gam=32,
                 tangential_enabled=True, tangential_str=30, tangential_arc=10, tangential_gain=1.)
        with tempfile.TemporaryDirectory() as tmp:
            export_layer_package(worker, source, p, {}, 'Original name.NEF', Path(tmp) / 'layers')
        for method in (worker.run_mgn_native, worker.run_tangential):
            np.testing.assert_array_equal(method.call_args.args[0], source)
            self.assertEqual(method.call_args.args[1], 100)
        np.testing.assert_array_equal(source, np.linspace(1, 5, 64).reshape(8, 8).astype(np.float32))
        self.assertEqual(p['mgn_str'], 20)

    def test_disk_alpha_finite_files_and_quantized_recomposition(self):
        yy, xx = np.mgrid[:64, :80]
        source = (1 + np.exp(-np.hypot(xx-40, yy-32)/10) + .001*np.sin(xx)).astype(np.float32)
        p = dict(sx=40., sy=32., sr=8., tangential_enabled=True, tangential_str=25,
                 tangential_arc=10, tangential_gain=2., mgn_enabled=True, mgn_str=10, mgn_gam=32)
        display = dict(mode='asinh', strength=10., blend=.8)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'layers'
            export_layer_package(FilterWorker(), source, p, display, '/input/eclipse.tif', out)
            manifest = json.loads((out / 'recipe.json').read_text())
            base = tifffile.imread(out / next(r['file'] for r in manifest['layers'] if r['filter']=='base'))
            result = base[..., 0].astype(float) / 65535
            self.assertEqual(base.dtype, np.uint16)
            np.testing.assert_array_equal(base[..., 0], to_u16(ael_tone_map(source,np.isfinite(source),manifest['display'])))
            for r in manifest['layers']:
                if r['filter'] in ('base','linear_reference'):continue
                layer = tifffile.imread(out / r['file'])
                self.assertEqual(layer.shape, (64, 80, 4))
                self.assertEqual(layer.dtype, np.uint16)
                self.assertEqual(layer[32, 40, 3], 0)
                with tifffile.TiffFile(out / r['file']) as tif:
                    self.assertEqual(int(tif.pages[0].extrasamples[0]), 2)
                result = overlay(result, layer[..., 0] / 65535., layer[..., 3] / 65535., r['opacity_255'] / 255.)
            saved = tifffile.imread(out / manifest['combined'])
            np.testing.assert_array_equal(saved[..., 0], to_u16(result.astype(np.float32)))
            np.testing.assert_array_equal(tifffile.imread(out / 'SOURCE_float32.tif'), source)
            self.assertFalse(manifest['parameters'].get('pre_stretch_enabled', False))
            with self.assertRaises(FileExistsError):
                export_layer_package(FilterWorker(), source, p, display, 'eclipse.tif', out)

    def test_zero_gain_layer_is_hidden_and_failed_branch_leaves_no_package(self):
        p = dict(sx=4., sy=4., sr=1., mgn_enabled=True, mgn_str=0,mgn_gam=32)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'layers'
            export_layer_package(FilterWorker(), np.ones((8, 8)), p, {}, 'flat.tif', out)
            manifest = json.loads((out / 'recipe.json').read_text())
            self.assertFalse(next(r for r in manifest['layers'] if r['filter']=='mgn')['visible'])
            worker = Mock()
            worker.run_mgn_native.side_effect = RuntimeError('filter failed')
            with self.assertRaises(RuntimeError):
                export_layer_package(worker, np.ones((8, 8)), dict(p, mgn_str=10, mgn_gam=32), {},
                                     'flat.tif', Path(tmp) / 'bad')
            self.assertEqual(sorted(x.name for x in Path(tmp).iterdir()), ['layers'])

    def test_achf_background_is_not_exported_as_false_detail(self):
        source = np.arange(64, dtype=np.float32).reshape(8, 8)
        worker = Mock()
        worker.run_achf.side_effect = lambda a, *args, **kwargs: .1 * a
        params = dict(sx=4., sy=4., sr=1., achf_enabled=True, achf_str=20,
                      achf_kernel=10, achf_boost=10, achf_background=10)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'layers'
            export_layer_package(worker, source, params, {}, 'test.tif', output)
            manifest = json.loads((output / 'recipe.json').read_text())
            layer = tifffile.imread(output / next(r['file'] for r in manifest['layers'] if r['filter']=='achf'))
            np.testing.assert_array_equal(layer[..., 0], 32768)
            self.assertTrue(next(r['normalization'] for r in manifest['layers'] if r['filter']=='achf')['constant'])
