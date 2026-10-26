"""Fast RGB preview shares native calibration and leaves numerical filtering alone."""
from gui_wait import wait_for_gui, close_window

import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import unittest
from unittest.mock import patch
import numpy as np
from PySide6.QtWidgets import QApplication
from core.colour import neutralize_tse, set_luminosity
from core.image_data import resize_observed
from core.layer_engine import colour_display
from core.layer_export import to_u16
from core.presentation import normalized_base, composition_settings
from gui.app import EclipseProcessorApp


class FastColourPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        w=self.window=EclipseProcessorApp();w.auto_calculate=False
        w.btn_psb_preview.setChecked(False)
        w.request_processing_signal.disconnect()
        t=np.linspace(.01,.8,160*192,dtype=np.float32).reshape(160,192)
        self.rgb=t[...,None]*np.array([.7,1.,.4],np.float32)
        self.rgb[20:22,30:32]=np.nan
        w.full_source_rgb=self.rgb
        w.full_raw_image=(self.rgb @ np.array([.299,.587,.114])).astype(np.float32)
        w.raw_image=resize_observed(w.full_raw_image,(96,80))
        w.preview_image=w.raw_image;w.processed_image=w.raw_image.copy()
        w.txt_x.setText('96');w.txt_y.setText('80');w.txt_r.setText('20')
        w.chk_calibrate_colour.setChecked(False);wait_for_gui(w)
        w.on_input_state_changed()
        w.recalculation_timer.stop();w.presentation_timer.stop()

    def tearDown(self):close_window(self.window)

    def test_fast_calibrated_colour_is_visible_and_uses_native_gains(self):
        w=self.window
        original=self.rgb.copy()
        with patch.object(w,'dispatch_pipeline_request_if_auto') as dispatch,patch('gui.app.neutralize_tse',wraps=neutralize_tse) as calibration:
            w.chk_calibrate_colour.setChecked(True);wait_for_gui(w)
            self.assertEqual(calibration.call_count,1)
            self.assertIs(calibration.call_args.args[0],self.rgb)
            dispatch.assert_not_called()
        self.assertFalse(w.chk_verify_preview.isChecked())
        self.assertEqual(w.last_preview_presentation.shape,(80,96,3))
        native,_=neutralize_tse(self.rgb)
        reduced=np.stack([resize_observed(native[...,c],(96,80)) for c in range(3)],axis=-1)
        display=w.collect_display_parameters()
        base=to_u16(normalized_base(w.raw_image,composition_settings(display))).astype(float)/65535
        expected=set_luminosity(colour_display(reduced,w.raw_image,composition_settings(display)),base)
        from core.presentation_edges import finish_presentation
        from core.layer_engine import engine_for
        expected=finish_presentation(expected,engine_for(w.filter_worker).edge_alpha(w.raw_image,w.collect_filter_parameters(w.raw_image.shape)))
        np.testing.assert_allclose(w.last_preview_presentation,expected,atol=1e-7,rtol=0)
        np.testing.assert_array_equal(self.rgb,original)

    def test_display_edits_reuse_calibration_and_reduced_rgb_and_toggle_is_reversible(self):
        w=self.window
        with patch('gui.app.neutralize_tse',wraps=neutralize_tse) as calibration:
            w.chk_calibrate_colour.setChecked(True);wait_for_gui(w)
            calibrated=w.last_preview_presentation.copy()
            cached=w._preview_colour_cache[2]
            w.render_matrix_to_screen();wait_for_gui(w)
            self.assertIs(w._preview_colour_cache[2],cached)
            self.assertEqual(calibration.call_count,1)
            w.sl_psb_exposure.setValue(100);w.render_matrix_to_screen();wait_for_gui(w)
            self.assertIs(w._preview_colour_cache[2],cached)
            self.assertEqual(calibration.call_count,1)
            w.sl_psb_exposure.setValue(0)
            w.chk_calibrate_colour.setChecked(False);wait_for_gui(w)
            uncalibrated=w.last_preview_presentation.copy()
            self.assertGreater(np.max(abs(calibrated-uncalibrated)),.01)
            self.assertEqual(calibration.call_count,1)
            w.chk_calibrate_colour.setChecked(True);wait_for_gui(w)
            np.testing.assert_array_equal(w.last_preview_presentation,calibrated)
            self.assertEqual(calibration.call_count,2)
            w.show_original_mode=True;w.render_matrix_to_screen();wait_for_gui(w)
            self.assertEqual(calibration.call_count,2)
            self.assertEqual(w.last_preview_presentation.shape,(80,96,3))

    def test_original_view_respects_calibration_in_fit_and_native_zoom(self):
        from core.result_cache import parameter_signature
        w=self.window;source_before=self.rgb.copy()
        for native in (False,True):
            with self.subTest(native=native):
                w.chk_calibrate_colour.setChecked(False);wait_for_gui(w)
                if native:
                    p=w.collect_filter_parameters(w.full_raw_image.shape)
                    w._full_cache=(w.full_raw_image,parameter_signature(p),w.full_raw_image.copy(),w._preview_revision)
                    w.set_preview_zoom(1);wait_for_gui(w)
                w.btn_compare.setChecked(True);w.toggle_compare_mode(True);wait_for_gui(w)
                uncalibrated=w.last_preview_presentation.copy()
                raw_native=w.image_label._native_pixels.copy() if native else None
                with patch('gui.app.neutralize_tse',wraps=neutralize_tse) as calibration:
                    w.chk_calibrate_colour.setChecked(True);wait_for_gui(w)
                    calibrated=w.last_preview_presentation.copy()
                    self.assertTrue(w.show_original_mode)
                    self.assertGreater(np.max(np.abs(calibrated-uncalibrated)),.01)
                    self.assertEqual(calibration.call_count,1)
                    if native:
                        self.assertFalse(np.array_equal(w.image_label._native_pixels,raw_native))
                    # With no active detail filters, both comparison states share the same colour.
                    w.btn_compare.setChecked(False);w.toggle_compare_mode(False);wait_for_gui(w)
                    np.testing.assert_array_equal(w.last_preview_presentation,calibrated)
                    w.btn_compare.setChecked(True);w.toggle_compare_mode(True);wait_for_gui(w)
                    self.assertEqual(calibration.call_count,1)
                    w.chk_calibrate_colour.setChecked(False);wait_for_gui(w)
                    np.testing.assert_array_equal(w.last_preview_presentation,uncalibrated)
                    if native:
                        np.testing.assert_array_equal(w.image_label._native_pixels,raw_native)
                raw,_,report=w._colour_cache
                np.testing.assert_array_equal(raw,self.rgb)
                self.assertEqual(report['method'],'none')
        np.testing.assert_array_equal(self.rgb,source_before)

    def test_invalid_balance_falls_back_to_source_rgb_in_fast_preview(self):
        w=self.window
        w.full_source_rgb=np.ones((160,192,3),np.float32)
        w.source_rgb_white=None
        w.chk_calibrate_colour.setChecked(True);wait_for_gui(w)
        self.assertFalse(w.chk_calibrate_colour.isChecked())
        self.assertIn('neutralization disabled',w.status_label.text())
        self.assertEqual(w.last_preview_presentation.shape,(80,96,3))
        self.assertTrue(np.isfinite(w.last_preview_presentation).all())

    def test_psb_color_correction_does_not_change_fast_preview(self):
        w=self.window;w.render_matrix_to_screen();wait_for_gui(w);before=w.last_preview_presentation.copy()
        w.chk_color_correction.setChecked(True);w.render_matrix_to_screen();wait_for_gui(w)
        np.testing.assert_array_equal(w.last_preview_presentation,before)
