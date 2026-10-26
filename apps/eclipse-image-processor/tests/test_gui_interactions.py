from gui_wait import wait_for_gui, close_window
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest, QSignalSpy
from PySide6.QtWidgets import QApplication

from gui.app import EclipseProcessorApp


class GuiInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = EclipseProcessorApp()
        self.window.request_processing_signal.disconnect()
        self.requests = []
        self.window.request_processing_signal.connect(lambda a, p: self.requests.append(p))
        image = np.ones((64, 64), dtype=np.float32)
        self.window.raw_image = image
        self.window.preview_image = image
        self.window.full_raw_image = image
        self.window.processed_image = image
        self.window.txt_x.setText("32")
        self.window.txt_y.setText("32")
        self.window.txt_r.setText("8")
        self.window.recalculation_timer.stop()

    def tearDown(self):
        close_window(self.window)

    def test_pipeline_completion_log_distinguishes_idle_pending_and_running(self):
        w=self.window
        w.recalculation_timer.stop();w.presentation_timer.stop()
        w.has_pending_request=False;w.is_processing=False
        with patch('builtins.print') as output:
            w._log_processing_end('PIPELINE','Complete')
            self.assertIn('Idle — no processing running or queued',output.call_args.args[0])
            w.recalculation_timer.start(1000)
            w._log_processing_end('PIPELINE','Complete')
            self.assertIn('Waiting for pending update',output.call_args.args[0])
            w.is_processing=True
            w._log_processing_end('PIPELINE','Complete')
            self.assertIn('Another process is running',output.call_args.args[0])
        w.is_processing=False;w.recalculation_timer.stop()


    def test_disk_overlay_button_is_adjacent_and_does_not_reprocess(self):
        from core.result_cache import parameter_signature
        w=self.window
        row=next(w.sec_geo.content_layout.itemAt(i).layout() for i in range(w.sec_geo.content_layout.count())
                 if w.sec_geo.content_layout.itemAt(i).layout() is not None
                 and w.sec_geo.content_layout.itemAt(i).layout().indexOf(w.btn_auto_moon)>=0)
        self.assertEqual(row.indexOf(w.btn_disk_overlay),row.indexOf(w.btn_auto_moon)+1)
        self.assertTrue(w.btn_disk_overlay.isChecked())
        before=parameter_signature(w.collect_filter_parameters(w.raw_image.shape))
        revision=w._preview_revision
        with patch.object(w,'render_matrix_to_screen',side_effect=AssertionError('Recomposed pixels')):
            w.btn_disk_overlay.click()
            self.assertFalse(w.image_label.disk_overlay_visible)
            w.btn_disk_overlay.click()
            self.assertTrue(w.image_label.disk_overlay_visible)
        self.assertEqual(w._preview_revision,revision)
        self.assertEqual(parameter_signature(w.collect_filter_parameters(w.raw_image.shape)),before)
        self.assertEqual(self.requests,[])

    def test_larson_sekanina_controls_are_available_and_collected(self):
        w = self.window
        self.assertEqual(w.sl_larson_sekanina_str.maximum(),200)
        self.assertEqual(w.sl_larson_sekanina_angular.value(),30)
        self.assertEqual(w.sl_larson_sekanina_angular.property('reset_value'),30)
        w.auto_calculate = False
        w.chk_advanced.setChecked(False)
        w.sec_larson_sekanina.chk_active.setChecked(True)
        w.sl_larson_sekanina_str.setValue(200)
        w.sl_larson_sekanina_angular.setValue(23)
        params = w.collect_filter_parameters((64, 64))
        self.assertTrue(params['larson_sekanina_enabled'])
        self.assertEqual(params['larson_sekanina_str'], 200)
        self.assertEqual(params['larson_sekanina_radial'], 0.)
        self.assertEqual(params['larson_sekanina_angular'], 2.3)
        self.assertFalse(hasattr(w,'sl_larson_sekanina_radial'))
        self.assertFalse(w.sl_larson_sekanina_angular.isHidden())
        from gui.project_settings import capture_settings,restore_settings
        saved=capture_settings(w)
        w.sl_larson_sekanina_str.setValue(25)
        restore_settings(w,saved)
        self.assertEqual(w.sl_larson_sekanina_str.value(),200)

    def test_linear_colour_and_verification_defaults_reset_on_loading(self):
        from pathlib import Path
        import tempfile
        from unittest.mock import patch
        import tifffile
        w = self.window
        self.assertEqual(w.combo_input_state.currentData(), "linear")
        self.assertTrue(w.chk_calibrate_colour.isChecked())
        self.assertFalse(w.chk_verify_preview.isChecked())
        w.auto_calculate = False
        yy, xx = np.mgrid[:80, :100]
        mono = (100 + 20000*np.exp(-np.hypot(xx-50, yy-40)/12)).astype(np.uint16)
        rgb = np.stack([mono, mono//2, mono//3], axis=-1)
        with tempfile.TemporaryDirectory() as tmp:
            for name, image in (("rgb", rgb), ("mono", mono), ("rgb_again", rgb), ("rgb_hdr",rgb.astype(np.float32)*10)):
                path = Path(tmp)/f"{name}.tif"
                tifffile.imwrite(path, image, photometric="rgb" if image.ndim == 3 else "minisblack")
                w.combo_input_state.setCurrentIndex(2)
                w.chk_verify_preview.setChecked(True)
                with patch("gui.app.QFileDialog.getOpenFileName", return_value=(str(path), "")):
                    w.load_image_action();wait_for_gui(w)
                self.assertEqual(w.source_path, str(path), w.status_label.text())
                self.assertEqual(w.combo_input_state.currentData(), "linear")
                self.assertFalse(w.lbl_input_linearity.isHidden())
                self.assertEqual(w.lbl_input_linearity.text(), "Assumed linear; not confirmed.")
                self.assertFalse(w.lbl_input_linearity.wordWrap())
                header=w.combo_input_state.parentWidget().layout()
                self.assertEqual(header.indexOf(w.lbl_input_linearity), header.indexOf(w.combo_input_state)+1)
                self.assertFalse(w.combo_input_state.isHidden())
                self.assertFalse(w.chk_verify_preview.isChecked())
                self.assertEqual(w.chk_calibrate_colour.isChecked(), image.ndim == 3)
                self.assertEqual(w.chk_calibrate_colour.isEnabled(), image.ndim == 3)
                np.testing.assert_array_equal(w.full_source_rgb, image if image.ndim == 3 else None)
                if name == 'rgb_hdr':
                    self.assertIsNone(w.source_rgb_white)
                    balanced, _, report = w._colour_cache
                    self.assertTrue(np.isfinite(balanced).all())
                    self.assertIn('shared observed maximum',report['white_source'])
                    self.assertTrue(w.chk_calibrate_colour.isChecked())

    def test_colour_calibration_requires_declared_linear_rgb_and_is_reversible(self):
        self.assertFalse(self.window.chk_calibrate_colour.isEnabled())
        t = np.linspace(.01, .9, 64*64).reshape(64, 64)
        rgb = np.stack([.1+.6*t, .05+.3*t, .025+.15*t], axis=-1).astype(np.float32)
        self.window.full_source_rgb = rgb
        self.window.combo_input_state.setCurrentIndex(0)
        self.window.on_input_state_changed()
        self.assertFalse(self.window.chk_calibrate_colour.isEnabled())
        self.window.combo_input_state.setCurrentIndex(1)
        self.assertTrue(self.window.chk_calibrate_colour.isEnabled())
        from core.colour import neutralize_tse, set_luminosity
        with patch("gui.app.neutralize_tse", wraps=neutralize_tse) as calibrate, patch("gui.app.set_luminosity", wraps=set_luminosity) as colorize:
            self.window.chk_calibrate_colour.setChecked(True)
            self.window.render_matrix_to_screen();wait_for_gui(self.window)
            self.assertEqual(calibrate.call_count,1)
            self.assertEqual(self.window.last_preview_presentation.ndim,3)
            self.window.show_original_mode = True
            self.window.render_matrix_to_screen();wait_for_gui(self.window)
            self.window.show_original_mode = False
            self.assertEqual(calibrate.call_count,1)
            self.assertGreaterEqual(colorize.call_count,2)
            self.assertEqual(self.window.last_preview_presentation.shape,(64,64,3))
        calibrated, _, report = self.window._colour_cache
        self.assertIn("gain-only", report["method"])
        np.testing.assert_allclose(calibrated[..., 0], calibrated[..., 1], atol=1e-6)
        original, _, original_report = self.window._colour_cache
        np.testing.assert_array_equal(original, calibrated)
        self.assertIn("gain-only", original_report["method"])
        self.window.combo_input_state.setCurrentIndex(2)
        self.assertFalse(self.window.chk_calibrate_colour.isChecked())
        wait_for_gui(self.window)
        restored, _, report = self.window._colour_cache
        np.testing.assert_array_equal(restored, rgb)
        self.assertEqual(report["method"], "none")

    def test_calibration_row_whitespace_toggles_once_per_click(self):
        self.window.full_source_rgb = np.repeat(np.linspace(.01,.9,64*64,dtype=np.float32).reshape(64,64,1),3,axis=-1)
        self.window.combo_input_state.setCurrentIndex(1)
        self.window.on_input_state_changed()
        checkbox = self.window.chk_calibrate_colour
        checkbox.setChecked(False)
        checkbox.resize(350, 30)
        self.assertTrue(checkbox.isEnabled())
        point = QPoint(checkbox.width()-3, checkbox.height()//2)
        for expected in (True, False, True):
            QTest.mouseClick(checkbox, Qt.MouseButton.LeftButton, pos=point)
            self.assertEqual(checkbox.isChecked(), expected)

    def test_invalid_recipe_does_not_leave_pipeline_busy(self):
        from unittest.mock import patch
        with patch.object(self.window, "collect_filter_parameters", side_effect=ValueError("invalid control")):
            self.window.dispatch_pipeline_request()
        self.assertFalse(self.window.is_processing)
        self.assertEqual(self.requests, [])
        self.window.dispatch_pipeline_request()
        self.assertEqual(len(self.requests), 1)

    def test_edits_during_worker_run_publish_only_the_latest_recipe(self):
        original = self.window.processed_image.copy()
        self.window.dispatch_pipeline_request()
        self.window.txt_x.setText("25")
        # Debounce expires while worker is still running: queue exactly one run.
        self.window.recalculation_timer.stop()
        self.window.dispatch_pipeline_request()
        self.window.txt_y.setText("26")
        self.window.on_processing_finished(np.zeros_like(original))
        np.testing.assert_array_equal(self.window.processed_image, original)
        self.assertEqual(len(self.requests), 1)
        QTest.qWait(800)
        self.assertEqual(len(self.requests), 2)
        self.assertEqual((self.requests[-1]["sx"], self.requests[-1]["sy"]), (25, 26))
        result = np.full_like(original, 3)
        self.window.on_processing_finished(result)
        np.testing.assert_array_equal(self.window.processed_image, result)
        self.assertFalse(self.window.is_processing)

    def test_manual_recalculate_during_worker_run_is_not_lost(self):
        self.window.toggle_auto_calc_mode(False)
        self.window.dispatch_pipeline_request()
        self.window.txt_x.setText("24")
        self.window.dispatch_pipeline_request()
        self.window.on_processing_finished(np.zeros_like(self.window.raw_image))
        self.assertEqual(len(self.requests), 2)
        self.assertEqual(self.requests[-1]["sx"], 24)

    def test_old_image_result_is_ignored_after_loading_another_image(self):
        self.window.dispatch_pipeline_request()
        replacement = self.window.raw_image.copy()*7
        self.window.raw_image = replacement
        self.window.preview_image = replacement
        self.window.processed_image = replacement
        self.window.dispatch_pipeline_request_if_auto()
        self.window.on_processing_finished(np.zeros_like(replacement))
        np.testing.assert_array_equal(self.window.processed_image, replacement)
        QTest.qWait(800)
        self.assertEqual(len(self.requests), 2)

    def test_real_worker_finishes_with_latest_slider_values(self):
        from core.filters import FilterWorker
        from core.pipeline import execute_pipeline
        image = np.random.default_rng(51).uniform(.1, 1, (128, 160)).astype(np.float32)
        self.window.raw_image = image
        self.window.preview_image = image
        self.window.full_raw_image = image
        self.window.processed_image = image.copy()
        self.window.request_processing_signal.connect(self.window.filter_worker.process_pipeline)
        self.window.sec_mgn.chk_active.setChecked(True)
        self.window.dispatch_pipeline_request()
        self.window.sl_mgn_gam.setValue(45)
        self.window.sl_mgn_k.setValue(27)
        # Let queued Qt completion and debounce events run, with a bounded wait.
        import time
        for _ in range(300):
            self.application.processEvents()
            time.sleep(.01)  # Release the GIL so the Python Qt worker can progress.
            if len(self.requests) >= 2 and not self.window.is_processing and not self.window.recalculation_timer.isActive():
                break
        self.assertGreaterEqual(len(self.requests), 2)
        self.assertFalse(self.window.is_processing)
        self.assertFalse(self.window.recalculation_timer.isActive())
        expected = execute_pipeline(FilterWorker(), image, self.window.collect_filter_parameters(image.shape))
        np.testing.assert_array_equal(self.window.processed_image, expected)

    def test_version_and_layer_model_tooltips_match_current_behavior(self):
        from config import APP_VERSION
        w=self.window
        self.assertEqual(APP_VERSION,'0.6.0')
        self.assertIn('v'+APP_VERSION,w.windowTitle())
        self.assertFalse(hasattr(w,'combo_stretch_mode'))
        self.assertTrue(w.btn_psb_preview.isChecked())
        self.assertFalse(hasattr(w,'btn_pick_sp'))
        self.assertFalse(hasattr(w,'sl_blend'))
        self.assertEqual(w.collect_display_parameters()['blend'],1.)
        self.assertIn('original-image pixels',w.sl_mgn_sigmas[0].toolTip())

    def test_all_user_controls_have_english_tooltips(self):
        import re
        from PySide6.QtWidgets import QWidget, QSlider, QComboBox, QPushButton, QLineEdit, QCheckBox, QLabel, QProgressBar
        controls = [widget for widget in self.window.findChildren(QWidget)
                    if isinstance(widget, (QSlider, QComboBox, QPushButton, QLineEdit, QCheckBox, QProgressBar))
                    or (isinstance(widget,QLabel) and widget.text().strip())]
        self.assertGreater(len(controls), 80)
        for control in controls:
            with self.subTest(control=control.objectName() or type(control).__name__, text=getattr(control, "text", lambda: "")()):
                help_text = control.toolTip().strip()
                self.assertTrue(help_text, "User control has no tooltip")
                self.assertIsNone(re.search(r"[áéíóúñ¿¡]|\b(entrada|imagen|calibrar|exportar|guardar|filtro|seleccionar)\b", help_text, re.I))
                self.assertNotIn("tse-tools", help_text)

    def test_tooltip_is_opaque_wrapped_and_contained_in_main_window(self):
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QHelpEvent
        self.window.show()
        self.application.processEvents()
        button = self.window.btn_export
        point = QPoint(button.width()-2, button.height()-2)
        help_event = QHelpEvent(QEvent.Type.ToolTip, point, button.mapToGlobal(point))
        self.application.sendEvent(button, help_event)
        panel = self.window.in_window_tooltips.panel
        self.assertFalse(panel.isVisible())
        QTest.qWait(self.window.in_window_tooltips.hover_delay_ms + 100)
        self.assertTrue(panel.isVisible())
        self.assertFalse(panel.isWindow())
        self.assertTrue(self.window.rect().contains(panel.geometry()))
        self.assertTrue(self.window.in_window_tooltips.label.wordWrap())
        self.assertEqual(panel.grab().toImage().pixelColor(3, 3).name(), "#151a21")
        self.application.sendEvent(button, QEvent(QEvent.Type.Leave))
        self.assertFalse(panel.isVisible())

    def test_tooltip_hover_is_cancelled_and_restarted_for_another_control(self):
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QHelpEvent
        self.window.show()
        self.application.processEvents()
        tips = self.window.in_window_tooltips
        tips.hover_delay_ms = 100
        def hover(widget):
            point = QPoint(2, 2)
            self.application.sendEvent(widget, QHelpEvent(QEvent.Type.ToolTip, point, widget.mapToGlobal(point)))
        hover(self.window.btn_load)
        QTest.qWait(40)
        self.application.sendEvent(self.window.btn_load, QEvent(QEvent.Type.Leave))
        QTest.qWait(120)
        self.assertFalse(tips.panel.isVisible())
        hover(self.window.btn_load)
        QTest.qWait(60)
        hover(self.window.btn_compare)
        QTest.qWait(60)
        self.assertFalse(tips.panel.isVisible())
        QTest.qWait(70)
        self.assertTrue(tips.panel.isVisible())
        self.assertEqual(tips.label.text(), self.window.btn_compare.toolTip())




    def test_rhef_mode_is_part_of_preview_and_export_recipe(self):
        self.assertEqual(self.window.combo_rhef_mode.currentData(), "continuous")
        for index, expected in ((1, "continuous"), (0, "legacy")):
            self.window.combo_rhef_mode.setCurrentIndex(index)
            for shape in (self.window.raw_image.shape, self.window.full_raw_image.shape):
                params = self.window.collect_filter_parameters(shape)
                self.assertEqual(params["rhef_mode"], expected)

    def test_opacity_only_controls_recompose_cached_filters(self):
        from core.layer_engine import engine_for
        from unittest.mock import patch
        w=self.window
        w.chk_statistics_lunar.setChecked(False)
        w.sec_mgn.chk_active.setChecked(True)
        p=w.collect_filter_parameters(w.raw_image.shape)
        engine=engine_for(w.filter_worker)
        with patch.object(w.filter_worker,'run_mgn_native', wraps=w.filter_worker.run_mgn_native) as operator:
            engine.render(w.filter_worker,w.raw_image,p,w.collect_display_parameters())
            self.assertEqual(operator.call_count,1)
            w.sl_mgn_opacity.setValue(25)
            w.render_matrix_to_screen();wait_for_gui(w)
            w.sl_mgn_opacity.setValue(70)
            w.render_matrix_to_screen();wait_for_gui(w)
            self.assertEqual(operator.call_count,1)
        for name in ('nrgf','fnrgf','rhef','mgn','wow','tangential','achf'):
            self.assertFalse(hasattr(w,'sl_'+name+'_str'))
            opacity=getattr(w,'sl_'+name+'_opacity')
            self.assertEqual(opacity.parameter_row.parentWidget().layout().indexOf(opacity.parameter_row),1 if name == 'achf' else 0)
        self.assertEqual(w.sl_larson_sekanina_str.title_label.text(),'Gain (%)')
        for controls in w.achf_ael_controls.values():
            self.assertNotIn('strength',controls)

    def test_all_opacity_edits_debounce_without_immediate_render(self):
        w=self.window
        w.recalculation_timer.stop();w.presentation_timer.stop()
        updates=QSignalSpy(w.presentation_timer.timeout)
        w.sl_mgn_opacity.setValue(43)
        QTest.qWait(80)
        w.achf_ael_controls['ael_angular_4']['opacity'].setValue(44)
        QTest.qWait(80)
        w.achf_ael_controls['ael_iso_04']['opacity'].setValue(45)
        self.assertEqual(w.presentation_timer.interval(),250)
        QTest.qWait(180)
        self.assertEqual(updates.count(),0)
        QTest.qWait(120)
        self.assertEqual(updates.count(),1)
        self.assertEqual(self.requests,[])
        # A later stretch edit retains its own shorter presentation delay.
        w.sl_mgn_opacity.setValue(46)
        w.sl_psb_exposure.setValue(100)
        self.assertEqual(w.presentation_timer.interval(),100)
        w.presentation_timer.stop()

    def test_ael_achf_selection_reaches_preview_and_export(self):
        w = self.window
        self.assertEqual(w.combo_achf_variant.currentData(), 'ael_iso_04')
        w.combo_achf_variant.setCurrentIndex(w.combo_achf_variant.findData('ael_iso_04'))
        for shape in (w.raw_image.shape, w.full_raw_image.shape):
            self.assertEqual(w.collect_filter_parameters(shape)['achf_variant'], 'ael_iso_04')
        self.assertFalse(w.sl_achf_kernel.isEnabled())
        self.assertTrue(w.achf_ael_controls['ael_iso_04']['opacity'].isEnabled())
        w.combo_achf_variant.setCurrentIndex(0)
        self.assertTrue(w.sl_achf_kernel.isEnabled())

    def test_ael_variants_keep_independent_settings_and_export_snapshot(self):
        w = self.window
        variants = ('ael_iso_01','ael_iso_04','ael_angular_4')
        self.assertEqual(w.combo_achf_variant.count(), 4)
        for i, variant in enumerate(variants):
            w.combo_achf_variant.setCurrentIndex(w.combo_achf_variant.findData(variant))
            controls = w.achf_ael_controls[variant]
            controls['opacity'].setValue(11+i)
            controls['outer_sigma'].setValue(21+i)
            if 'sigmas' in controls:
                controls['sigmas'][0].setValue(30+i)
            else:
                controls['angular_sigma'].setValue(15)
        for i, variant in enumerate(variants):
            w.combo_achf_variant.setCurrentIndex(w.combo_achf_variant.findData(variant))
            params = w.collect_filter_parameters(w.raw_image.shape)
            self.assertEqual(params['achf_str'],100)
            self.assertEqual(params['achf_ael_parameters']['opacity'],11+i)
            self.assertEqual(params['achf_ael_parameters']['outer_sigma'],(21+i)/10)
            self.assertEqual(set(params['achf_variants']),set(variants)|{'adaptive'})
            self.assertEqual(params['achf_adaptive_strength'],100)
        w.combo_achf_variant.setCurrentIndex(0)
        self.assertEqual(w.sl_achf_opacity.value(),19)

    def test_achf_starts_with_full_background_retention(self):
        w = self.window
        self.assertEqual(w.sl_achf_background.value(), 100)
        self.assertFalse(w.sec_achf.is_filter_active())
        self.assertEqual(w.sl_achf_opacity.value(),19)
        for shape in (w.raw_image.shape, w.full_raw_image.shape):
            self.assertEqual(w.collect_filter_parameters(shape)['achf_background'], 100)

    def test_adaptive_defaults_reset_to_loaded_values_and_log_actual_settings(self):
        from contextlib import redirect_stdout
        from io import StringIO
        w = self.window
        w.auto_calculate = False
        w.combo_achf_variant.setCurrentIndex(0)
        # A large radius exercises clamping of the automatically chosen support.
        w.full_raw_image = np.ones((1800, 2400), dtype=np.float32)
        w.preview_image = np.ones((900, 1200), dtype=np.float32)
        w.txt_x.setText('1200')
        w.txt_y.setText('900')
        output = StringIO()
        with redirect_stdout(output):
            w.apply_recommended_parameters_to_gui(2000, 2400, 1800)
        for slider in (w.sl_fnrgf_ord, w.sl_fnrgf_seg,
                       w.sl_fnrgf_bin_px, w.sl_fnrgf_rmax, w.sl_wow_scales,
                       w.sl_achf_kernel):
            expected = slider.value()
            slider.setValue(slider.minimum() if expected != slider.minimum() else slider.maximum())
            QTest.mouseDClick(slider, Qt.MouseButton.LeftButton)
            self.assertEqual(slider.value(), expected)
        self.assertEqual(w.sl_achf_kernel.value(), w.sl_achf_kernel.maximum())
        self.assertIn('WOW: 6 native scales', output.getvalue())
        self.assertIn('support radius = 20.0 preview px', output.getvalue())
        self.assertNotIn('arcsec/pixel', output.getvalue())

    def test_geometry_edits_restart_one_debounce_timer(self):
        self.window.txt_x.setText("20")
        QTest.qWait(350)
        self.window.txt_y.setText("25")
        QTest.qWait(350)
        self.assertEqual(self.requests, [])
        QTest.qWait(350)
        self.assertEqual(len(self.requests), 1)
        self.assertEqual(self.requests[0]["sx"], 20)
        self.assertEqual(self.requests[0]["sy"], 25)

    def test_active_slider_change_is_delayed_and_coalesced(self):
        # Enable without a recomputation; the worker is disconnected in setUp.
        from unittest.mock import patch
        with patch.object(self.window.sec_fnrgf, "is_filter_active", return_value=True):
            self.window.sl_fnrgf_cut.setValue(1)
            QTest.qWait(350)
            self.window.sl_fnrgf_cut.setValue(2)
            self.window.sl_fnrgf_cut.sliderReleased.emit()
            QTest.qWait(350)
            self.assertEqual(self.requests, [])
            QTest.qWait(350)
            self.assertEqual(len(self.requests), 1)
            self.assertEqual(self.requests[0]["fnrgf_cut"], 2)

    def test_edit_during_processing_waits_for_pause(self):
        self.window.is_processing = True
        self.window.has_pending_request = True
        self.window.txt_x.setText("21")
        self.window.on_processing_finished(self.window.raw_image.copy())
        self.assertEqual(self.requests, [])
        QTest.qWait(800)
        self.assertEqual(len(self.requests), 1)

    def test_manual_mode_does_not_schedule_and_explicit_calculate_cancels_timer(self):
        self.window.txt_x.setText("21")
        self.window.toggle_auto_calc_mode(False)
        QTest.qWait(800)
        self.assertEqual(self.requests, [])
        self.window.txt_y.setText("22")
        self.assertFalse(self.window.recalculation_timer.isActive())
        self.window.auto_calculate = True
        self.window.dispatch_pipeline_request_if_auto()
        self.window.dispatch_pipeline_request()
        self.assertEqual(len(self.requests), 1)
        self.assertFalse(self.window.recalculation_timer.isActive())

    def test_basic_mode_visibility_and_advanced_round_trip(self):
        from core.result_cache import parameter_signature
        w = self.window
        self.assertFalse(w.chk_advanced.isChecked())
        for slider in (*w.sl_mgn_sigmas, *w.sl_mgn_weights, w.sl_fnrgf_smooth,
                       w.sl_rhef_upsilon_high, w.sl_wow_scales):
            self.assertTrue(slider.isHidden())
            self.assertTrue(slider.title_label.isHidden())
            self.assertTrue(slider.value_label.isHidden())
        for slider in (w.sl_fnrgf_mask, w.sl_fnrgf_ord, w.sl_mgn_k, w.sl_mgn_h,
                       w.sl_tangential_denoise, w.sl_achf_threshold, w.sl_wow_noise):
            self.assertFalse(slider.isHidden())
        before = parameter_signature(w.collect_filter_parameters((64, 64)))
        w.chk_advanced.setChecked(True)
        self.assertFalse(w.sl_mgn_sigmas[0].isHidden())
        self.assertTrue(w.sl_wow_noise.isHidden())
        w.chk_advanced.setChecked(False)
        self.assertEqual(before, parameter_signature(w.collect_filter_parameters((64, 64))))
        self.assertIs(w.chk_advanced.parentWidget(), w.chk_calibrate_colour.parentWidget())

    def test_basic_wow_noise_updates_every_scale_and_advanced_values_survive(self):
        w = self.window
        w.combo_wow_bilateral.setCurrentIndex(1)
        self.assertEqual(w.sl_wow_noise.value(), 0)
        w.sl_wow_noise.setValue(23)
        self.assertTrue(all(s.value() == 23 for s in w.sl_wow_denoise))
        self.assertTrue(all(s.value_label.text() == '2.3' for s in w.sl_wow_denoise))
        self.assertTrue(all(x == 2.3 for x in w.collect_filter_parameters((64, 64))['wow_denoise']))
        w.chk_advanced.setChecked(True)
        w.sl_wow_denoise[0].setValue(41)
        w.chk_advanced.setChecked(False)
        self.assertEqual(w.sl_wow_denoise[0].value(), 41)
        self.assertFalse(w.lbl_advanced_values.isHidden())
        w.sl_wow_noise.setValue(24)
        self.assertTrue(all(s.value() == 24 for s in w.sl_wow_denoise))
        self.assertTrue(w.lbl_advanced_values.isHidden())

    def test_basic_rhef_edit_links_tails_without_resetting_on_mode_switch(self):
        w = self.window
        w.chk_advanced.setChecked(True)
        w.chk_rhef_symmetric.setChecked(False)
        w.sl_rhef_upsilon_high.setValue(77)
        w.chk_advanced.setChecked(False)
        self.assertEqual(w.sl_rhef_upsilon_high.value(), 77)
        self.assertFalse(w.lbl_advanced_values.isHidden())
        w.sl_rhef_upsilon.setValue(42)
        params = w.collect_filter_parameters((64, 64))
        self.assertEqual(params['rhef_upsilon_high'], params['rhef_upsilon'])
        self.assertTrue(w.chk_rhef_symmetric.isChecked())
        self.assertEqual(w.sl_rhef_upsilon_high.value(), 42)
