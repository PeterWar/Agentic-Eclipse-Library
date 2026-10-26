"""AEL oracle, positive observed support, pipeline scaling and exported layer pixels."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import tifffile

from core.ael_achf import ael_achf_layer, apply_ael_achf
from core.filters import FilterWorker
from core.pipeline import apply_filter, prepare_parameters
from core.layer_export import export_layer_package, to_u16


class AELACHFTests(unittest.TestCase):
    def setUp(self):
        with np.load(Path(__file__).parent/'fixtures/ael_achf_iso04.npz') as f:
            self.image = f['image']
            self.valid = f['valid']
            self.expected = f['expected']
            self.cx, self.cy, self.radius = f['geometry']

    def test_matches_installed_ael_133_oracle(self):
        before = self.image.copy()
        actual, info = ael_achf_layer(self.image, self.cx, self.cy, self.radius, self.valid)
        np.testing.assert_allclose(actual, self.expected, atol=1e-7, equal_nan=True)
        np.testing.assert_array_equal(self.image, before)
        self.assertEqual(info['native_sigmas'], [1,2,4,8,16])
        self.assertEqual(info['native_outer_sigma'], 1.5)

    def test_three_variants_match_upstream_oracles_and_accept_custom_parameters(self):
        with np.load(Path(__file__).parent/'fixtures/ael_achf_variants.npz') as oracles:
            for variant in ('ael_iso_01','ael_iso_04','ael_angular_4'):
                layer, _ = ael_achf_layer(self.image,self.cx,self.cy,self.radius,
                                         self.valid,variant=variant)
                np.testing.assert_allclose(layer,oracles[variant],atol=1e-7,equal_nan=True)
                custom = dict(outer_sigma=0)
                if variant == 'ael_angular_4':
                    custom['angular_sigma'] = 2.
                else:
                    custom['sigmas'] = [3.,6.,12.,24.,48.]
                changed, _ = ael_achf_layer(self.image,self.cx,self.cy,self.radius,
                    self.valid,variant=variant,parameters=custom)
                use = np.isfinite(layer) & np.isfinite(changed)
                self.assertGreater(np.max(abs(layer[use]-changed[use])),.01)

    def test_disabled_family_omits_achf_even_with_inclusion_flags(self):
        from core.ael_achf import AEL_PRESETS
        p=dict(sx=self.cx,sy=self.cy,sr=self.radius,valid_mask=self.valid,achf_enabled=False,
               achf_variants={key:dict(value,enabled=True,strength=100) for key,value in AEL_PRESETS.items()})
        with tempfile.TemporaryDirectory() as tmp:
            destination=Path(tmp)/'layers'
            export_layer_package(FilterWorker(),self.image,p,{},'synthetic.fits',destination)
            recipe=json.loads((destination/'recipe.json').read_text())
            self.assertFalse(any(row['filter']=='achf' for row in recipe['layers']))

    def test_export_three_independent_variants_including_hidden_zero_strength(self):
        from core.ael_achf import AEL_PRESETS
        p = dict(sx=self.cx,sy=self.cy,sr=self.radius,valid_mask=self.valid,
                 statistics_exclude_lunar=True,
                 achf_kernel=10,achf_boost=20,
                 achf_variant='ael_iso_04',achf_enabled=True,achf_str=77,
                 achf_variants={key:dict(value,enabled=True,strength=100) for key,value in AEL_PRESETS.items()})
        p['achf_variants']['ael_iso_01']['strength'] = 0
        p['achf_variants']['ael_iso_04']['opacity'] = 23
        p['achf_variants']['ael_angular_4']['angular_sigma'] = 2.
        p['achf_variants']['adaptive']=dict(enabled=False)
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)/'layers'
            export_layer_package(FilterWorker(),self.image,p,{},'synthetic.fits',destination)
            recipe = json.loads((destination/'recipe.json').read_text())
            layers = [r for r in recipe['layers'] if r.get('filter')=='achf']
            self.assertEqual(len(layers),3)
            self.assertEqual({r['variant'] for r in layers},set(AEL_PRESETS))
            self.assertEqual(len({r['file'] for r in layers}),3)
            for record in layers:
                variant = record['variant']
                expected, _ = ael_achf_layer(self.image,self.cx,self.cy,self.radius,
                    self.valid,variant=variant,parameters=p['achf_variants'][variant])
                use = np.isfinite(expected)
                rgba = tifffile.imread(destination/record['file'])
                np.testing.assert_array_equal(rgba[...,0][use],to_u16(np.where(use,.5+(expected-.5)*p['achf_variants'][variant]['strength']/100,.5))[use])
                self.assertTrue((rgba[...,3][~use]==0).all())
                if variant=='ael_iso_01':
                    self.assertEqual(record['opacity_255'],0)
                    self.assertFalse(record['visible'])
                elif variant=='ael_iso_04':
                    self.assertEqual(record['opacity_255'],round(.23*255))

    def test_ignored_pixels_cannot_change_observed_detail(self):
        poisoned = self.image.copy()
        poisoned[~self.valid] = 1e20
        layer, _ = ael_achf_layer(poisoned, self.cx, self.cy, self.radius, self.valid)
        np.testing.assert_allclose(layer, self.expected, atol=1e-7, equal_nan=True)
        poisoned[30, 30] = -1
        poisoned[31, 30] = 0
        result = apply_ael_achf(poisoned, 10, self.cx, self.cy, self.radius, self.valid)
        np.testing.assert_array_equal(result[~self.valid], poisoned[~self.valid])
        self.assertEqual(result[30,30], -1)
        self.assertEqual(result[31,30], 0)
        np.testing.assert_array_equal(apply_ael_achf(poisoned, 0, 0, 0, 0), poisoned)

    def test_overlay_formula_and_pipeline_mask(self):
        p = dict(sx=self.cx, sy=self.cy, sr=self.radius, achf_variant='ael_iso_04',
                 achf_enabled=True, achf_str=10, valid_mask=self.valid,
                 statistics_exclude_lunar=True)
        actual = apply_filter(FilterWorker(), self.image, p)
        low, high = np.nanmin(self.image), np.nanmax(self.image)
        base = (self.image-low)/(high-low)
        full = np.where(base <= .5, 2*base*self.expected,
                        1-2*(1-base)*(1-self.expected))
        expected = self.image + .1*(full-base)*(high-low)
        np.testing.assert_allclose(actual, expected, atol=2e-6, equal_nan=True)
        scaled = prepare_parameters(p, self.image.shape, self.image.shape,
                                    (self.image.shape[0]*2,self.image.shape[1]*2))
        self.assertEqual(scaled['achf_ael_scale'], 2.)
        self.assertEqual(scaled['achf_variant'], 'ael_iso_04')

    def test_export_preserves_ael_encoding_without_second_normalization(self):
        p = dict(sx=self.cx, sy=self.cy, sr=self.radius, achf_variant='ael_iso_04',
                 achf_enabled=True, achf_str=100, valid_mask=self.valid,
                 statistics_exclude_lunar=True,
                 achf_variants={'adaptive':dict(enabled=False),'ael_iso_04':dict(enabled=True,opacity=10,strength=100)})
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp)/'layers'
            export_layer_package(FilterWorker(), self.image, p, {}, 'synthetic.fits', destination)
            recipe = json.loads((destination/'recipe.json').read_text())
            record = next(r for r in recipe['layers'] if r.get('filter') == 'achf')
            rgba = tifffile.imread(destination/record['file'])
            self.assertEqual(record['mode'], 'Overlay')
            self.assertEqual(record['normalization']['variant'], 'ael_iso_04')
            np.testing.assert_array_equal(rgba[...,0][self.valid], to_u16(np.where(self.valid, self.expected, .5))[self.valid])
            self.assertTrue((rgba[...,3][~self.valid] == 0).all())

    def test_layer_export_option_leaves_main_pixels_unchanged(self):
        from unittest.mock import patch
        from core.export import export_images
        source = np.nan_to_num(self.image,nan=1.)
        p = dict(sx=self.cx,sy=self.cy,sr=self.radius)
        with tempfile.TemporaryDirectory() as tmp, patch('core.export.export_layer_package') as package:
            package.return_value = Path(tmp)/'layers'
            first = str(Path(tmp)/'single.tif')
            export_images(source,p,{},first,'synthetic.fits',processed=source,export_layers=False)
            package.assert_not_called()
            multiple = dict(p)
            second = str(Path(tmp)/'multiple.tif')
            export_images(source,multiple,{},second,'synthetic.fits',processed=source,export_layers=True)
            package.assert_called_once()
            np.testing.assert_array_equal(tifffile.imread(first),tifffile.imread(second))

    def test_invalid_geometry_sparse_support_and_constant(self):
        for radius, scale in ((0,1),(20,0),(np.nan,1)):
            with self.assertRaises(ValueError):
                ael_achf_layer(self.image,self.cx,self.cy,radius,scale=scale)
        with self.assertRaises(ValueError):
            ael_achf_layer(self.image,self.cx,self.cy,20,valid=np.ones((2,2),bool))
        with self.assertRaises(ValueError):
            ael_achf_layer(np.ones((3,3)),1,1,1)
        for variant, settings in (
                ('ael_iso_01',dict(sigmas=[1,2])),
                ('ael_iso_04',dict(outer_sigma=-1)),
                ('ael_angular_4',dict(angular_sigma=0))):
            with self.assertRaises(ValueError):
                ael_achf_layer(self.image,self.cx,self.cy,20,variant=variant,parameters=settings)
        a = np.ones((128,160),np.float32)
        np.testing.assert_array_equal(apply_ael_achf(a,100,self.cx,self.cy,20),a)
