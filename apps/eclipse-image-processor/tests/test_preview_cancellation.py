"""Cancellation during real worker execution, quiet-period scheduling and isolation."""
from gui_wait import close_window

import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from threading import Event, Thread
import unittest
from unittest.mock import patch
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication
from core.cancellation import check_cancelled
from core.filters import FilterWorker
from core.pipeline import apply_filter, execute_pipeline
from gui.app import EclipseProcessorApp


class CancellationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_cancels_inside_mgn_before_remaining_scales(self):
        import core.filters as filters
        worker = FilterWorker()
        image = np.random.default_rng(90).uniform(1, 9, (64, 64)).astype(np.float32)
        params = dict(sx=32,sy=32,sr=8,mgn_enabled=True,mgn_str=30,mgn_gam=32)
        entered, release = Event(), Event()
        outcomes = []
        worker.cancelled.connect(lambda: outcomes.append('cancelled'), Qt.ConnectionType.DirectConnection)
        worker.finished.connect(lambda _: outcomes.append('finished'), Qt.ConnectionType.DirectConnection)
        worker.failed.connect(lambda e: outcomes.append(e), Qt.ConnectionType.DirectConnection)
        original = filters.gaussian_filter
        def blocking_gaussian(*args, **kwargs):
            entered.set()
            if not release.wait(3):
                raise AssertionError('Test did not release first convolution')
            return original(*args, **kwargs)
        with patch('core.filters.gaussian_filter', side_effect=blocking_gaussian) as gaussian:
            thread = Thread(target=worker.process_pipeline, args=(image, params))
            thread.start()
            try:
                self.assertTrue(entered.wait(3))
                worker.cancel()
            finally:
                release.set()
                thread.join(3)
            self.assertFalse(thread.is_alive())
            self.assertEqual(outcomes, ['cancelled'])
            self.assertLess(gaussian.call_count, 12)  # six full scales would need 12
        # Cancellation is scoped to preview work, not synchronous exports.
        np.testing.assert_array_equal(apply_filter(worker, image, {}), image)
        worker.prepare_job()
        worker.process_pipeline(image, {})
        self.assertEqual(outcomes, ['cancelled', 'finished'])

    def test_compatible_fnrgf_helper_threads_share_the_job_cancellation(self):
        import core.filters as filters
        from core.cancellation import cancellation_check
        worker = FilterWorker()
        entered, release = Event(), Event()
        outcomes = []
        worker.cancelled.connect(lambda: outcomes.append('cancelled'), Qt.ConnectionType.DirectConnection)
        worker.failed.connect(lambda e: outcomes.append(e), Qt.ConnectionType.DirectConnection)
        image = np.random.default_rng(5).uniform(1, 10, (48, 48))
        yy, xx = np.indices(image.shape)
        radius, angle = np.hypot(xx-24, yy-24), np.arctan2(yy-24, xx-24)
        def capture_check():
            captured = cancellation_check()
            def probe():
                entered.set()
                if not release.wait(3):
                    raise AssertionError('Helper-thread checkpoint was not released')
                captured()
            return probe
        def run(*_):
            return filters.fnrgf_normalize(image, radius, angle, np.arange(0, 41, 4),
                                            order=2, segments=8)
        with patch('core.filters.cancellation_check', side_effect=capture_check), \
             patch.object(worker, '_process_pipeline', side_effect=run):
            thread = Thread(target=worker.process_pipeline, args=(image, {}))
            thread.start()
            try:
                self.assertTrue(entered.wait(3))
                worker.cancel()
            finally:
                release.set(); thread.join(3)
            self.assertFalse(thread.is_alive())
        self.assertEqual(outcomes, ['cancelled'])

    def test_cancel_before_execution_and_at_completion_emit_one_terminal_signal(self):
        for at_completion in (False, True):
            worker = FilterWorker(); image = np.ones((12, 12), np.float32)
            cancelled, finished, failed = QSignalSpy(worker.cancelled), QSignalSpy(worker.finished), QSignalSpy(worker.failed)
            def complete(*_):
                worker.cancel()
                return image
            if not at_completion:
                worker.cancel()
            with patch.object(worker, '_process_pipeline', side_effect=complete) as pipeline:
                worker.process_pipeline(image, {})
                self.assertEqual(pipeline.call_count, int(at_completion))
            self.assertEqual((cancelled.count(), finished.count(), failed.count()), (1, 0, 0))
            check_cancelled()  # scoped token was reset even on an exception

    def test_cancelled_gui_job_is_replaced_once_after_last_slider_pause(self):
        w = EclipseProcessorApp()
        w.auto_calculate = False
        a = np.random.default_rng(16).uniform(1, 10, (80, 96)).astype(np.float32)
        w.full_raw_image = a; w.raw_image = a.copy(); w.preview_image = w.raw_image
        w.processed_image = a.copy()
        w.txt_x.setText('48'); w.txt_y.setText('40'); w.txt_r.setText('8')
        w.chk_statistics_lunar.setChecked(False)
        w.sec_mgn.chk_active.setChecked(True)
        entered = Event(); calls = []
        original = FilterWorker.run_mgn_native
        def interruptible_stage(worker, *args, **kwargs):
            calls.append(args[1])
            if len(calls) == 1:
                entered.set()
                if not worker._cancel_event.wait(3):
                    raise AssertionError('Slider did not cancel the running job')
                check_cancelled()
            return original(worker, *args, **kwargs)
        cancelled, finished = QSignalSpy(w.filter_worker.cancelled), QSignalSpy(w.filter_worker.finished)
        try:
            with patch.object(FilterWorker, 'run_mgn_native', interruptible_stage):
                w.auto_calculate = True
                w.dispatch_pipeline_request()
                self.assertTrue(entered.wait(3))
                w.sl_mgn_k.setValue(23)
                QTest.qWait(200)
                self.assertFalse(w.is_processing)
                self.assertEqual(cancelled.count(), 1)
                np.testing.assert_array_equal(w.processed_image, a)
                w.sl_mgn_k.setValue(27)
                QTest.qWait(400)
                self.assertEqual(len(calls), 1)
                # Pump Qt while releasing the GIL for the Python worker.
                import time
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline and (finished.count() < 1 or w.is_processing):
                    self.app.processEvents()
                    time.sleep(.01)
                self.assertEqual(calls, [100, 100])
                self.assertEqual(finished.count(), 1)
                self.assertFalse(w.is_processing)
                self.assertFalse(w.recalculation_timer.isActive())
            expected = execute_pipeline(FilterWorker(), a, w.collect_filter_parameters(a.shape))
            np.testing.assert_array_equal(w.processed_image, expected)
        finally:
            close_window(w)
