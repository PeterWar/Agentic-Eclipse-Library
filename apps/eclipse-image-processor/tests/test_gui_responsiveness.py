"""Regression cases from the GUI architecture review."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import copy
from pathlib import Path
import tempfile
from threading import Event
import time
import unittest
from unittest.mock import patch
import numpy as np
import tifffile
from PySide6.QtCore import QThread, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from gui.app import EclipseProcessorApp
from gui.background_tasks import TaskThread, render_snapshot
from gui.project_settings import capture_settings, restore_settings
from core.project_settings import write_settings
from gui_wait import wait_for_gui, close_window


class GuiResponsivenessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.w = EclipseProcessorApp()
        w = self.w
        w.auto_calculate = False
        w.full_raw_image = np.ones((100,100),np.float32)
        w.raw_image = w.preview_image = w.processed_image = w.full_raw_image
        w.txt_x.setText('50');w.txt_y.setText('50');w.txt_r.setText('10')
        w.recalculation_timer.stop();w.presentation_timer.stop()

    def tearDown(self):
        close_window(self.w)

    def test_incomplete_geometry_keeps_last_valid_display(self):
        w = self.w
        w.render_matrix_to_screen();wait_for_gui(w)
        previous = w.last_preview_presentation
        for name in ('x','y','r'):
            field = getattr(w,'txt_'+name)
            value = field.text()
            field.setText('')
            w.render_matrix_to_screen();wait_for_gui(w)
            self.assertIs(w.last_preview_presentation,previous)
            field.setText(value)

    def test_redraw_and_resize_preserve_filter_values_and_do_not_recompose(self):
        w = self.w
        w.sl_fnrgf_rmax.setMaximum(200);w.sl_fnrgf_rmax.setValue(150)
        w.render_matrix_to_screen();wait_for_gui(w)
        with patch('gui.app.render_snapshot',side_effect=AssertionError('Recomposed on resize')):
            w.trigger_circle_redraw()
            w.resize(1100,700);self.app.processEvents()
        self.assertEqual(w.sl_fnrgf_rmax.value(),150)

    def test_invalid_restore_rolls_back_controls_geometry_and_ranges(self):
        w = self.w
        previous = capture_settings(w)
        maximum = w.sl_fnrgf_rmax.maximum()
        bad = copy.deepcopy(previous)
        bad['controls']['sl_mgn_opacity']['value'] = 51
        bad['controls']['sl_fnrgf_rmax']['value'] = maximum+100
        bad['controls']['sl_mgn_k']['value'] = 999999
        bad['geometry']['x'] = '12'
        with self.assertRaisesRegex(ValueError,'sl_mgn_k'):
            restore_settings(w,bad)
        self.assertEqual(capture_settings(w),previous)
        self.assertEqual(w.sl_fnrgf_rmax.maximum(),maximum)

    def test_rejected_json_keeps_current_source_and_recipe(self):
        w = self.w
        old_source = w.full_raw_image
        previous = capture_settings(w)
        bad = copy.deepcopy(previous)
        bad['controls']['sl_mgn_k']['value'] = 999999
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)/'source.tif'
            tifffile.imwrite(source,np.full((80,80),2.,np.float32))
            recipe = write_settings(Path(tmp)/'recipe.tif',source,bad,{}, {})
            with patch('gui.app.QFileDialog.getOpenFileName',return_value=(str(recipe),'')):
                w.load_image_action();wait_for_gui(w)
        self.assertIs(w.full_raw_image,old_source)
        self.assertEqual(capture_settings(w),previous)
        self.assertIn('Error loading',w.status_label.text())

    def test_composition_keeps_event_loop_alive_and_rejects_obsolete_result(self):
        w = self.w
        entered, release = Event(), Event()
        gui_thread = QThread.currentThread()
        def blocked(job):
            self.assertIsNot(QThread.currentThread(),gui_thread)
            entered.set()
            if not release.wait(5):
                raise AssertionError('Test did not release renderer')
            return render_snapshot(job)
        heartbeats = []
        timer = QTimer();timer.setInterval(5);timer.timeout.connect(lambda:heartbeats.append(1));timer.start()
        try:
            with patch('gui.app.render_snapshot',side_effect=blocked):
                w.render_matrix_to_screen()
                deadline = time.monotonic()+2
                while not entered.is_set() and time.monotonic()<deadline:QTest.qWait(10)
                self.assertTrue(entered.is_set())
                w.sl_psb_exposure.setValue(100)
                w.render_matrix_to_screen()
                QTest.qWait(40)
                self.assertGreater(len(heartbeats),0)
                self.assertFalse(hasattr(w,'last_preview_presentation'))
                release.set();wait_for_gui(w)
            expected = w.last_preview_presentation.copy()
            w.render_matrix_to_screen();wait_for_gui(w)
            np.testing.assert_array_equal(w.last_preview_presentation,expected)
        finally:
            release.set();timer.stop()

    def test_loading_runs_decoder_and_detection_outside_gui_thread(self):
        w = self.w
        gui_thread = QThread.currentThread()
        entered, release = Event(), Event()
        def detect(image):
            self.assertIsNot(QThread.currentThread(),gui_thread)
            entered.set()
            if not release.wait(5):raise AssertionError('Test did not release loader')
            return 40,40,10
        try:
            with tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp)/'source.tif';tifffile.imwrite(source,np.ones((80,80),np.float32))
                with patch('gui.app.QFileDialog.getOpenFileName',return_value=(str(source),'')),patch.object(w,'detect_lunar_limb',side_effect=detect):
                    w.btn_disk_overlay.setChecked(False)
                    w.load_image_action()
                    deadline = time.monotonic()+2
                    while not entered.is_set() and time.monotonic()<deadline:QTest.qWait(10)
                    self.assertTrue(entered.is_set())
                    self.assertIsNotNone(w._load_thread)
                    self.assertFalse(w.control_sidebar.isEnabled())
                    release.set();wait_for_gui(w)
                self.assertEqual(w.full_raw_image.shape,(80,80))
                self.assertTrue(w.btn_disk_overlay.isChecked())
                self.assertTrue(w.image_label.disk_overlay_visible)
                self.assertEqual(w.last_preview_presentation.shape,(80,80))
                self.assertTrue(np.isfinite(w.last_preview_presentation).all())
        finally:
            release.set()

    def test_manual_lunar_detection_is_asynchronous(self):
        w = self.w
        gui_thread = QThread.currentThread()
        def detect(image):
            self.assertIsNot(QThread.currentThread(),gui_thread)
            return 45,48,12
        with patch.object(w,'detect_lunar_limb',side_effect=detect):
            w.auto_detect_moon_action()
            wait_for_gui(w)
        self.assertEqual((w.txt_x.text(),w.txt_y.text(),w.txt_r.text()),('45','48','12'))
        self.assertTrue(w.control_sidebar.isEnabled())

    def test_native_fallback_is_reduced_in_the_background_for_fast_view(self):
        w = self.w
        w.raw_image = w.preview_image = np.ones((50,50),np.float32)
        w.processed_image = np.full((100,100),.4,np.float32)
        w._has_layer_result = True
        w.sec_mgn.chk_active.setChecked(True)  # No cached layer: use last numerical result.
        w.render_matrix_to_screen();wait_for_gui(w)
        self.assertEqual(w.last_preview_presentation.shape,(50,50))
        self.assertTrue(np.isfinite(w.last_preview_presentation).all())

    def test_close_does_not_block_on_export(self):
        w = self.w
        release = Event()
        thread = TaskThread(lambda:release.wait(5),parent=w)
        w._export_thread = thread
        def finished():
            w._export_thread = None
            thread.deleteLater()
            w._finish_close()
        thread.finished.connect(finished)
        thread.start()
        try:
            start = time.monotonic()
            self.assertFalse(w.close())
            self.assertLess(time.monotonic()-start,.2)
            heartbeat = []
            QTimer.singleShot(0,lambda:heartbeat.append(True))
            QTest.qWait(20)
            self.assertTrue(heartbeat)
        finally:
            release.set()
            deadline = time.monotonic()+2
            while w._export_thread is not None and time.monotonic()<deadline:QTest.qWait(10)
