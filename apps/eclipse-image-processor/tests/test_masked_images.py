"""Missing eclipse samples stay missing through loading, filters and export."""
from gui_wait import wait_for_gui, close_window

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import tifffile

from core.filters import FilterWorker
from core.image_data import observed_image, resize_observed
from core.layer_export import export_layer_package
from core.masked_filters import MaskedWorker
from core.pipeline import apply_filter
from core.presentation import normalized_base
from gui.app import EclipseProcessorApp


def parameters(valid):
    return dict(valid_mask=valid, sx=40., sy=32., sr=8.,
                pre_stretch_enabled=True, pre_stretch_mode='log', pre_stretch_val=1,
                noise_gate_enabled=True, noise_gate_str=10, noise_gate_thr=10,
                bilateral_enabled=True, bilateral_str=10, bilateral_d=10, bilateral_sc=30, bilateral_ss=50,
                fnrgf_enabled=True, fnrgf_str=20, fnrgf_ord=3, fnrgf_seg=16, fnrgf_cut=0,
                fnrgf_rad=10, fnrgf_rmax=61, fnrgf_nbins=15,
                mgn_enabled=True, mgn_str=10, mgn_gam=32,
                rhef_enabled=True, rhef_str=10, rhef_rad=10, rhef_upsilon=35, rhef_mode='continuous',
                wow_enabled=True, wow_str=10, wow_scales=3, wow_denoise=[1, 2, 3], wow_bilateral=1,
                tangential_enabled=True, tangential_str=10, tangential_arc=10, tangential_gain=2,
                achf_enabled=True, achf_str=10, achf_kernel=10, achf_boost=20)


class MaskedImageTests(unittest.TestCase):
    def setUp(self):
        yy, xx = np.mgrid[:64, :80]
        self.valid = (xx-40)**2 + (yy-32)**2 > 8**2
        self.image = np.random.default_rng(48).uniform(.1, 1, (64, 80)).astype(np.float32)
        self.image[~self.valid] = np.nan

    def test_explicit_mask_excludes_values_and_preserves_missing_through_every_stage(self):
        for family in ('mgn','wow','tangential','achf','fnrgf','rhef'):
            p=parameters(self.valid)
            for name in ('mgn','wow','tangential','achf','fnrgf','rhef'):
                p[name+'_enabled']=name == family
            for bilateral in (None,1):
                for mode in ('legacy','continuous'):
                    p.update(wow_bilateral=bilateral,rhef_mode=mode)
                    expected=apply_filter(FilterWorker(),self.image,p)
                    contaminated=np.where(self.valid,self.image,1e20)
                    actual=apply_filter(FilterWorker(),contaminated,p)
                    np.testing.assert_array_equal(actual,expected)
                    np.testing.assert_array_equal(np.isfinite(actual),self.valid)
        self.assertTrue(np.isnan(self.image[~self.valid]).all())
        with self.assertRaises(ValueError):
            apply_filter(FilterWorker(), self.image, {})

    def test_constant_has_no_missing_boundary_contrast(self):
        worker = MaskedWorker(FilterWorker(), self.valid)
        image = np.where(self.valid, 7., 0)
        for bilateral in (None, 1):
            smooth = worker.starlet_blur(image, 4, bilateral)
            np.testing.assert_allclose(smooth[self.valid], 7., atol=1e-12)
        for name in ('mgn', 'wow', 'tangential', 'achf', 'fnrgf', 'rhef'):
            p = parameters(self.valid)
            for other in ('pre_stretch', 'noise_gate', 'bilateral', 'mgn', 'wow', 'tangential', 'achf', 'fnrgf', 'rhef'):
                p[other+'_enabled'] = other == name
            result = apply_filter(FilterWorker(), np.where(self.valid, 7., np.nan), p)
            self.assertTrue(np.isfinite(result[self.valid]).all())
            self.assertLess(float(np.ptp(result[self.valid])), 1e-5, name)

    def test_area_preview_ignores_missing_and_retains_holes(self):
        image = np.ones((8, 8), np.float32)*5
        image[:3, :3] = np.nan
        resized = resize_observed(image, (4, 4))
        self.assertTrue(np.isnan(resized[:2, :2]).all())
        np.testing.assert_array_equal(resized[np.isfinite(resized)], 5)
        with self.assertRaises(ValueError):
            observed_image(np.full((4, 4), np.nan))

    def test_constant_bilateral_starlet_excludes_missing_buffers_without_overflow(self):
        worker = MaskedWorker(FilterWorker(), self.valid)
        for value in (0., 7., -3., 1e-20):
            for missing in (0., 1e20, -1e20, np.nan):
                image = np.where(self.valid, value, missing)
                with self.subTest(value=value, missing=missing), np.errstate(over='raise', invalid='raise', divide='raise'):
                    smooth = worker.starlet_blur(image, 4, 1)
                    np.testing.assert_allclose(smooth[self.valid], value, rtol=1e-12, atol=1e-30)

    def test_bilateral_starlet_matches_observed_only_scalar_taps(self):
        image = np.random.default_rng(17).normal(size=(9, 11))
        valid = np.ones(image.shape, dtype=bool)
        valid[2:6, 4:7] = False
        image[~valid] = np.nan
        worker = MaskedWorker(FilterWorker(), valid)
        coefficients = np.array([1, 4, 6, 4, 1])/16
        for step in (1, 2, 4):
            for bilateral in (.2, 1., 3.):
                sigma = np.std(image[valid])*bilateral
                expected = np.zeros_like(image)
                for y, x in zip(*np.nonzero(valid)):
                    total, mass = 0., 0.
                    for j, cy in enumerate(coefficients):
                        for i, cx in enumerate(coefficients):
                            yy, xx = y+(j-2)*step, x+(i-2)*step
                            if 0 <= yy < image.shape[0] and 0 <= xx < image.shape[1] and valid[yy, xx]:
                                weight = cy*cx*np.exp(-.5*((image[yy, xx]-image[y, x])/sigma)**2)
                                total += weight*image[yy, xx]
                                mass += weight
                    expected[y, x] = total/mass
                with np.errstate(over='raise', invalid='raise', divide='raise'):
                    actual = worker.starlet_blur(image, step, bilateral)
                np.testing.assert_allclose(actual[valid], expected[valid], atol=1e-14, rtol=1e-13)
        with self.assertRaises(ValueError):
            observed_image(image, np.ones((4, 4), bool))

    def test_layer_package_stores_zero_source_validity_and_opaque_antialiased_combined(self):
        p = parameters(self.valid)
        display = dict(mode='asinh', strength=10, blend=.8)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'layers'
            export_layer_package(FilterWorker(), self.image, p, display, 'masked.tif', output)
            manifest = json.loads((output/'recipe.json').read_text())
            self.assertNotIn('valid_mask', manifest['parameters'])
            self.assertEqual(int((tifffile.imread(output/'VALID.tif')==0).sum()),int((~self.valid).sum()))
            source = tifffile.imread(output/'SOURCE_float32.tif')
            np.testing.assert_array_equal(source, np.nan_to_num(self.image))
            for record in manifest['layers']:
                layer=tifffile.imread(output/record['file'])
                self.assertEqual(layer.shape,(64,80,4))
                if record['filter']=='edge_antialias':
                    self.assertTrue(np.all(layer[~self.valid,3]==65535))
                else:
                    self.assertTrue(np.all(layer[~self.valid,3]==0))
                self.assertTrue(np.isfinite(layer).all())
            combined=tifffile.imread(output/manifest['combined'])
            self.assertEqual(combined.shape,(64,80,3))
            self.assertTrue(np.all(combined[~self.valid]==0))
            presentation = normalized_base(self.image, display)
            self.assertTrue(np.isfinite(presentation).all())
            self.assertTrue(np.all(presentation[~self.valid] == 0))

    def test_load_float_rgb_with_missing_moon_and_export_actual_gui_action(self):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        window = EclipseProcessorApp()
        window.auto_calculate = False
        yy, xx = np.mgrid[:160, :240]
        radius = np.hypot(xx-140, yy-90)
        image = np.where(radius > 23, 1+np.exp(-radius/40), np.nan).astype(np.float32)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)/'realistic.tif'
                tifffile.imwrite(path, np.repeat(image[..., None], 3, axis=2), photometric='rgb')
                with patch('gui.app.QFileDialog.getOpenFileName', return_value=(str(path), '')):
                    window.load_image_action();wait_for_gui(window)
                self.assertEqual(window.source_path, str(path), window.status_label.text())
                np.testing.assert_allclose(window.full_raw_image, image, rtol=2e-7, equal_nan=True)
                np.testing.assert_array_equal(np.isfinite(window.full_raw_image), np.isfinite(image))
                np.testing.assert_allclose([int(window.txt_x.text()), int(window.txt_y.text()), int(window.txt_r.text())], (140,90,23), atol=1)
                self.assertFalse(window.combo_input_state.isHidden())  # All sources need transfer-state control.
                window.combo_input_state.setCurrentIndex(1)
                # This normalized-float fixture is deliberately above white=1;
                # this test checks missing-data export without neutralization.
                window.chk_calibrate_colour.setChecked(False)
                window.chk_export_layers.setChecked(True)
                result = Path(tmp)/'final.tif'
                with patch('gui.app.QFileDialog.getSaveFileName', return_value=(str(result), '')):
                    window.export_image_action()
                    self.assertTrue(window._export_thread.wait(30000))
                    app.processEvents()
                self.assertTrue(result.is_file(), window.status_label.text())
                final = tifffile.imread(result)
                self.assertEqual(final.dtype, np.uint16)
                self.assertEqual(final.shape, (160, 240, 3))
                self.assertTrue((final[~np.isfinite(image)] == 0).all())
                self.assertTrue((Path(tmp)/'final_PS_layers.psb').is_file())
                from psd_tools import PSDImage
                psb = PSDImage.open(Path(tmp)/'final_PS_layers.psb')
                self.assertEqual(psb.depth,16)
                self.assertEqual(psb._record.header.channels,3)
                self.assertFalse((Path(tmp)/'final_sources').exists())
        finally:
            close_window(window)
