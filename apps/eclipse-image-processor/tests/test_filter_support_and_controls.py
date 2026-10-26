"""Statistical exclusions, native preview/export consistency and UI parameter contracts."""
from gui_wait import wait_for_gui, close_window

import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import cv2
import numpy as np
import tifffile
from PySide6.QtWidgets import QApplication
from core.filters import FilterWorker
from core.pipeline import apply_filter, execute_pipeline, prepare_parameters
from core.presentation import composition_settings
from core.colour import set_luminosity
from core.statistics_support import statistics_support
from core.layer_export import export_layer_package
from core.result_cache import parameter_signature
from gui.app import EclipseProcessorApp
from gui.filter_controls import CONTROLS


class StatisticalSupportTests(unittest.TestCase):
    def test_mask_is_not_missing_data_and_excluded_samples_do_not_change_neighbors(self):
        a=np.random.default_rng(8).uniform(1,20,(64,80)).astype(np.float32)
        valid=np.ones_like(a,bool);valid[:2]=False
        support=valid.copy();support[25:40,30:50]=False
        p=dict(sx=40,sy=32,sr=8,valid_mask=valid,statistics_mask=support,
               mgn_enabled=True,mgn_str=50,mgn_gam=32,
               wow_enabled=True,wow_str=30,wow_scales=3,
               tangential_enabled=True,tangential_str=40)
        original=a.copy()
        for family in ('mgn','wow','tangential'):
            selected=dict(p,**{name+'_enabled':name == family for name in ('mgn','wow','tangential')})
            first=apply_filter(FilterWorker(),a,selected)
            altered=a.copy();altered[valid & ~support]=1e20
            second=apply_filter(FilterWorker(),altered,selected)
            np.testing.assert_array_equal(first[support],second[support])
            np.testing.assert_array_equal(second[valid & ~support],altered[valid & ~support])
            np.testing.assert_array_equal(np.isfinite(second),valid)
        np.testing.assert_array_equal(a,original)

    def test_bright_limb_mask_uses_only_observed_annular_samples(self):
        y,x=np.indices((81,81));r=np.hypot(x-40,y-40);a=np.ones((81,81));a[40,51]=100
        p=dict(sx=40,sy=40,sr=10,statistics_exclude_lunar=True,statistics_exclude_bright=True,
               statistics_bright_percentile=99.5,statistics_limb_outer=1.5)
        support=statistics_support(a,p)
        self.assertFalse(support[40,40]);self.assertFalse(support[40,51])
        self.assertTrue(support[40,60]);self.assertTrue(support[0,0])

    def test_tangential_layer_support_and_numeric_source_are_separate(self):
        a=np.random.default_rng(3).uniform(1,10,(64,80)).astype(np.float32)
        p=dict(sx=40,sy=32,sr=8,statistics_exclude_lunar=True,
               tangential_enabled=True,tangential_str=30,tangential_inner=1.2,tangential_outer=3)
        with tempfile.TemporaryDirectory() as tmp:
            out=export_layer_package(FilterWorker(),a,p,{},'input.tif',Path(tmp)/'layers')
            recipe=json.loads((out/'recipe.json').read_text())
            self.assertEqual([r['filter'] for r in recipe['layers']],['linear_reference','base','tangential'])
            self.assertNotIn('statistics_mask',recipe['parameters'])
            support=tifffile.imread(out/'STATISTICS_SUPPORT.tif')
            self.assertEqual(support[32,40],0)
            np.testing.assert_array_equal(tifffile.imread(out/'SOURCE_float32.tif'),a)
            layer=tifffile.imread(out/recipe['layers'][2]['file'])
            self.assertEqual(layer[32,40,3],0)
            self.assertEqual(layer[32,66,3],0)
            base=tifffile.imread(out/recipe['layers'][1]['file'])
            self.assertEqual(base.shape,(64,80,4))  # valid Moon remains an observed base

    def test_noise_confidence_reduces_noise_only_rank_contribution(self):
        a=np.random.default_rng(90).normal(10,1,(96,96)).astype(np.float32); w=FilterWorker()
        plain=w.run_rhef_native(a,100,10,35,48,48,10)
        gated=w.run_rhef_native(a,100,10,35,48,48,10,noise_confidence=5)
        self.assertLess(np.mean((gated-a)**2),.2*np.mean((plain-a)**2))


class ControlAndVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.window=EclipseProcessorApp();self.window.auto_calculate=False
        self.window.btn_psb_preview.setChecked(False)
        self.window.request_processing_signal.disconnect()
        a=np.random.default_rng(71).uniform(2,20,(80,96)).astype(np.float32)
        w=self.window;w.full_raw_image=a;w.raw_image=a.copy();w.preview_image=w.raw_image;w.processed_image=a.copy()
        w.txt_x.setText('48');w.txt_y.setText('40');w.txt_r.setText('8');w.update_wow_controls()
    def tearDown(self):close_window(self.window)

    def test_every_new_slider_endpoint_maps_to_finite_recipe_and_filter_output(self):
        w=self.window
        for family,specs in CONTROLS.items():
            for attr,key,title,lo,hi,default,divisor,help_text in specs:
                slider=getattr(w,'sl_'+attr)
                for endpoint in (slider.minimum(),slider.maximum()):
                    with self.subTest(parameter=key,endpoint=endpoint):
                        slider.setValue(endpoint)
                        p=w.collect_filter_parameters(w.raw_image.shape)
                        p[family+'_enabled']=True
                        p[family+'_str']=50
                        out=execute_pipeline(FilterWorker(),w.raw_image,p)
                        self.assertTrue(np.isfinite(out).all())
                        self.assertEqual(out.shape,w.raw_image.shape)
                slider.setValue(default)
        self.assertFalse(hasattr(w,'sec_usm'))

    def test_dynamic_constraints_and_no_silent_inactive_values(self):
        w=self.window
        w.combo_wow_bilateral.setCurrentIndex(1)
        w.sl_fnrgf_seg.setValue(9);w.sl_fnrgf_ord.setValue(20)
        self.assertEqual(w.sl_fnrgf_seg.value(),9)
        self.assertGreaterEqual(2**w.sl_fnrgf_seg.minimum(),2*w.sl_fnrgf_ord.value()+1)
        w.chk_tangential_outer.setChecked(True);w.sl_tangential_inner.setValue(30)
        self.assertGreater(w.sl_tangential_outer.minimum(),w.sl_tangential_inner.value())
        w.sl_wow_scales.setValue(2)
        self.assertEqual([s.isEnabled() for s in w.sl_wow_denoise],[True,True]+[False]*8)
        self.assertEqual(len(w.collect_filter_parameters(w.raw_image.shape)['wow_denoise']),2)
        w.chk_rhef_symmetric.setChecked(False);w.sl_rhef_upsilon_high.setValue(150)
        self.assertEqual(w.collect_filter_parameters(w.raw_image.shape)['rhef_upsilon_high'],150)

    def test_each_mgn_scale_and_native_wow_threshold_is_wired(self):
        w=self.window
        w.combo_wow_bilateral.setCurrentIndex(1)
        for collection, key, divisor in ((w.sl_mgn_sigmas, 'mgn_sigmas', 100), (w.sl_mgn_weights, 'mgn_weights', 100)):
            for index, slider in enumerate(collection):
                original=slider.value()
                for endpoint in (slider.minimum(), slider.maximum()):
                    slider.setValue(endpoint)
                    p=w.collect_filter_parameters(w.raw_image.shape)
                    self.assertEqual(p[key][index], endpoint/divisor)
                    p.update(mgn_enabled=True, mgn_str=50)
                    self.assertTrue(np.isfinite(execute_pipeline(FilterWorker(),w.raw_image,p)).all())
                slider.setValue(original)
        w.sl_wow_scales.setValue(0)
        count=w.sl_wow_scales.maximum()
        for index, slider in enumerate(w.sl_wow_denoise[:count]):
            slider.setValue(15+index)
        p=w.collect_filter_parameters(w.raw_image.shape)
        self.assertEqual(p['wow_denoise'],[(15+i)/10 for i in range(count)])
        for bilateral in (None, .1, 5.):
            p.update(wow_enabled=True, wow_str=50, wow_bilateral=bilateral)
            self.assertTrue(np.isfinite(execute_pipeline(FilterWorker(),w.raw_image,p)).all())

    def test_composite_signature_includes_masks_but_excludes_visual_curve(self):
        w=self.window;p=w.collect_filter_parameters(w.raw_image.shape)
        first=parameter_signature(p)
        w.sl_psb_exposure.setValue(100)
        self.assertEqual(first,parameter_signature(w.collect_filter_parameters(w.raw_image.shape)))
        altered=dict(p);altered['valid_mask']=p['valid_mask'].copy();altered['valid_mask'][0,0]=False
        self.assertNotEqual(first,parameter_signature(altered))

    def test_native_wavelet_band_controls_are_not_shifted_on_export(self):
        p=dict(sx=100,sy=100,sr=20,wow_native_scales=True,wow_scales=4,wow_denoise=[1,2,3,4])
        full=prepare_parameters(p,(400,600),(200,300),(400,600))
        reduced=prepare_parameters(p,(400,600),(200,300),(200,300))
        self.assertEqual(full['wow_scales'],4);self.assertEqual(full['wow_denoise'],[1,2,3,4])
        self.assertEqual(reduced['wow_scales'],3);self.assertEqual(reduced['wow_denoise'],[2,3,4])

    def test_verification_preview_reuses_native_result_for_actual_rgb_export(self):
        w=self.window
        w.chk_verify_preview.setChecked(True)
        full=w.full_raw_image;w.full_source_rgb=np.stack([full*.9,full,full*1.2],axis=-1)
        w.raw_image=cv2.resize(full,(48,40),interpolation=cv2.INTER_AREA);w.preview_image=w.raw_image;w.processed_image=w.raw_image.copy()
        w.sec_tangential.chk_active.setChecked(True);w.sl_tangential_opacity.setValue(40)
        requests=[];w.request_processing_signal.connect(lambda a,p:requests.append((a,p)))
        w.dispatch_pipeline_request();a,p=requests[0]
        self.assertIs(a,w.full_raw_image)
        result=execute_pipeline(w.filter_worker,a,p);w.on_processing_finished(result);wait_for_gui(w)
        expected=result
        from core.layer_engine import colour_display
        expected=set_luminosity(colour_display(w.full_source_rgb,full,composition_settings(w.collect_display_parameters())),expected)
        reduced=cv2.resize(expected,(48,40),interpolation=cv2.INTER_AREA)
        np.testing.assert_allclose(w.last_preview_presentation,reduced,atol=1e-7)
        w.chk_export_layers.setChecked(False)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'actual.tif'
            with patch('gui.app.QFileDialog.getSaveFileName',return_value=(str(path),'')),patch('core.pipeline.apply_filter',side_effect=AssertionError('native cache was not reused')):
                w.export_image_action()
                self.assertTrue(w._export_thread.wait(30000))
                self.app.processEvents()
            np.testing.assert_array_equal(tifffile.imread(path),np.rint(np.clip(expected,0,1)*65535).astype(np.uint16))
            self.assertEqual(cv2.imread(str(path.with_name('actual_preview.jpg'))).shape,(*full.shape,3))
        # Numeric settings invalidate this cache, whereas display controls do not.
        signature=parameter_signature(w.collect_filter_parameters(full.shape))
        w.sl_tangential_gain.setValue(20)
        self.assertNotEqual(signature,parameter_signature(w.collect_filter_parameters(full.shape)))

    def test_obsolete_full_result_never_becomes_verification_cache(self):
        w=self.window;w.dispatch_pipeline_request();w.txt_x.setText('30')
        w.on_processing_finished(np.zeros(w.full_raw_image.shape,np.float32))
        self.assertIsNone(w._full_cache)

    def test_failed_colour_neutralization_is_reported_and_disabled_in_verification(self):
        w=self.window;full=w.full_raw_image
        w.chk_verify_preview.setChecked(True)
        w.chk_calibrate_colour.setChecked(False)
        w.full_source_rgb=np.repeat(full[...,None],3,axis=-1)
        w._full_cache=(full,parameter_signature(w.collect_filter_parameters(full.shape)),full.copy(),w._preview_revision)
        w.combo_input_state.setCurrentIndex(1)
        w.chk_calibrate_colour.setChecked(True);wait_for_gui(w)
        self.assertFalse(w.chk_calibrate_colour.isChecked())
        self.assertIn('neutralization disabled',w.status_label.text())
        self.assertTrue(np.isfinite(w.last_preview_presentation).all())

    def test_achf_background_one_and_zero_gain_are_exact_identity(self):
        w=self.window;w.sl_achf_background.setValue(100);w.sl_achf_boost.setValue(0)
        w.combo_achf_variant.setCurrentIndex(0)
        p=w.collect_filter_parameters(w.raw_image.shape);p['achf_enabled']=True;p.pop('layered_model',None)
        np.testing.assert_array_equal(apply_filter(FilterWorker(),w.raw_image,p),w.raw_image)

    def test_presentation_keyboard_changes_render_without_reprocessing(self):
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest
        w=self.window;full=w.full_raw_image
        w._full_cache=(full,parameter_signature(w.collect_filter_parameters(full.shape)),full.copy(),w._preview_revision)
        requests=[];w.request_processing_signal.connect(lambda a,p:requests.append(p))
        w.render_matrix_to_screen();wait_for_gui(w);before=w.last_preview_presentation.copy()
        signature=parameter_signature(w.collect_filter_parameters(full.shape))
        w.btn_psb_preview.setChecked(True);wait_for_gui(w)
        w.render_matrix_to_screen();wait_for_gui(w);before=w.last_preview_presentation.copy()
        QTest.keyClick(w.sl_psb_exposure,Qt.Key.Key_Right)
        QTest.qWait(150);wait_for_gui(w)
        self.assertFalse(np.array_equal(before,w.last_preview_presentation))
        self.assertEqual(signature,parameter_signature(w.collect_filter_parameters(full.shape)))
        self.assertEqual(requests,[])
