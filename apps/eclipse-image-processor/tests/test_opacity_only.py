"""Current opacity controls and saved settings; no migration from old formats."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
import tifffile
from PySide6.QtWidgets import QApplication
from core.layer_engine import ORDER
from core.project_settings import VERSION, read_settings, write_settings
from gui.app import EclipseProcessorApp
from gui.project_settings import capture_settings, restore_settings
from gui_wait import close_window


class OpacityOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.w=EclipseProcessorApp();self.w.auto_calculate=False
        self.w.full_raw_image=self.w.raw_image=self.w.preview_image=np.ones((40,40),np.float32)
        self.w.txt_x.setText('20');self.w.txt_y.setText('20');self.w.txt_r.setText('5')
        self.w.recalculation_timer.stop();self.w.presentation_timer.stop()

    def tearDown(self):close_window(self.w)

    def test_only_larson_sekanina_exposes_gain_and_current_settings_round_trip(self):
        w=self.w
        for name in (*ORDER,'achf'):
            self.assertEqual(hasattr(w,'sl_'+name+'_str'),name == 'larson_sekanina')
        for controls in w.achf_ael_controls.values():self.assertNotIn('strength',controls)
        w.sl_wow_opacity.setValue(13);w.sl_mgn_opacity.setValue(24)
        w.sl_larson_sekanina_str.setValue(175)
        expected=capture_settings(w)
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'source.tif';tifffile.imwrite(source,w.full_raw_image)
            path=write_settings(Path(tmp)/'current.tif',source,expected,{}, {})
            document=json.loads(path.read_text())
            self.assertEqual(document['version'],VERSION)
            self.assertNotIn('layer_controls',document['settings'])
            _,settings=read_settings(path);restore_settings(w,settings)
            self.assertEqual(capture_settings(w),expected)

    def test_export_controls_are_adjacent_and_reveal_is_absent(self):
        w=self.w
        self.assertFalse(hasattr(w,'sl_blend'))
        self.assertNotIn('sl_blend',capture_settings(w)['controls'])
        layout=w.chk_export_layers.parentWidget().layout()
        self.assertEqual(layout.indexOf(w.chk_color_correction),layout.indexOf(w.chk_export_layers)+1)
        self.assertEqual(layout.indexOf(w.combo_layers_format),layout.indexOf(w.chk_color_correction)+1)
