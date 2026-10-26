"""Export runs away from Qt's GUI thread and always restores its controls."""
from gui_wait import close_window

import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
from pathlib import Path
from threading import Event
import unittest
from unittest.mock import patch
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import QTimer
from gui.app import EclipseProcessorApp


class ExportWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_missing_attribute_reports_full_console_traceback(self):
        import io
        from contextlib import redirect_stderr
        from gui.export_worker import ExportThread
        thread=ExportThread({})
        output=io.StringIO()
        with patch('gui.export_worker.export_images',side_effect=AttributeError("'LayerEngine' object has no attribute 'prepare'")):
            with redirect_stderr(output):
                thread.run()
        self.assertIn("has no attribute 'prepare'",thread.error)
        self.assertIn('Traceback (most recent call last)',output.getvalue())
        self.assertIn("has no attribute 'prepare'",output.getvalue())

    def test_snapshot_worker_keeps_event_loop_running_and_handles_failure(self):
        for fail in (False, True):
            w = EclipseProcessorApp()
            w.auto_calculate = False
            a = np.ones((32, 40), np.float32)
            w.full_raw_image = a
            w.raw_image = a.copy()
            w.preview_image = a.copy()
            w.txt_x.setText('20'); w.txt_y.setText('16'); w.txt_r.setText('4')
            entered, release = Event(), Event()
            captured = []
            def export(**request):
                captured.append(request)
                request["progress"](35,"Calculating filters")
                entered.set()
                if not release.wait(3):
                    raise AssertionError('Test did not release export')
                if fail:
                    raise OSError('simulated write failure')
                return 'Status: Exported test.tiff + preview'
            try:
                with tempfile.TemporaryDirectory() as tmp, \
                     patch('gui.app.QFileDialog.getSaveFileName', return_value=(str(Path(tmp)/'test.tiff'), '')), \
                     patch('gui.export_worker.export_images', side_effect=export):
                    w.export_image_action()
                    self.assertTrue(entered.wait(3))
                    self.assertFalse(w.control_sidebar.isEnabled())
                    ticks = []
                    QTimer.singleShot(0, lambda: ticks.append('responsive'))
                    QTest.qWait(30)
                    self.assertEqual(ticks, ['responsive'])
                    self.assertEqual(w.export_progress.value(),35)
                    self.assertIn('Calculating filters',w.export_progress.format())
                    # Work owns a source copy and a captured recipe.
                    a[:] = 9
                    np.testing.assert_array_equal(captured[0]['source'], 1)
                    self.assertEqual(captured[0]['parameters']['sx'], 20)
                    self.assertFalse(captured[0].get('export_linear', False))
                    self.assertEqual(captured[0]['layers_format'],'psb')
                    self.assertFalse(hasattr(w, 'chk_export_linear'))
                    release.set()
                    self.assertTrue(w._export_thread.wait(3000))
                    self.app.processEvents()
                    self.assertIsNone(w._export_thread)
                    self.assertEqual(w.export_progress.format(),'Export failed' if fail else 'Export complete')
                    self.assertTrue(w.control_sidebar.isEnabled())
                    self.assertIn('simulated write failure' if fail else 'Exported test.tiff', w.status_label.text())
                    self.assertIn('simulated write failure' if fail else 'Exported test.tiff', w.status_label.toolTip())
            finally:
                release.set()
                close_window(w)
