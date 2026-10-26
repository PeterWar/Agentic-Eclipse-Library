"""Physical slider labels and wheel routing through the real sidebar widgets."""
from gui_wait import close_window

import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication, QComboBox, QScrollArea, QSlider
from gui.app import EclipseProcessorApp
from gui.components import ScrollSafeComboBox, ScrollSafeSlider


class SliderInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = EclipseProcessorApp()
        self.window.auto_calculate = False
        self.window.request_processing_signal.disconnect()

    def tearDown(self):
        self.window.presentation_timer.stop()
        close_window(self.window)
        self.window.deleteLater()
        self.app.processEvents()

    def test_removed_preparation_controls_are_absent(self):
        for name in ("sec_pre_stretch", "sec_noise_gate", "sec_bilateral"):
            self.assertFalse(hasattr(self.window, name))
        import numpy as np
        self.window.full_raw_image=np.ones((64,64),np.float32)
        self.window.preview_image=self.window.full_raw_image.copy()
        params=self.window.collect_filter_parameters((64, 64))
        self.assertFalse(any(key.startswith(("pre_stretch", "noise_gate", "bilateral")) for key in params))


    def test_all_controls_use_wheel_safe_widgets_and_unencoded_labels(self):
        sliders = self.window.findChildren(QSlider)
        self.assertGreater(len(sliders), 70)
        for slider in sliders:
            self.assertIsInstance(slider, ScrollSafeSlider)
            if hasattr(slider, 'title_label'):
                self.assertNotIn('×10', slider.title_label.text())
                self.assertNotIn('/10', slider.toolTip())
                self.assertNotIn('value /', slider.toolTip())
                for tick in (slider.minimum(), slider.maximum()):
                    slider.setValue(tick)
                    if tick == 0 and slider.property("zero_label"):
                        self.assertEqual(slider.value_label.text(), slider.property("zero_label"))
                        continue
                    self.assertEqual(float(slider.value_label.text()),
                                     float(slider.display_formatter(tick)) if slider.display_formatter
                                     else tick / slider.display_divisor)
        for combo in self.window.findChildren(QComboBox):
            self.assertIsInstance(combo, ScrollSafeComboBox)

    def test_fnrgf_compact_editing_reset_and_advanced_visibility(self):
        w = self.window
        slider = w.sl_fnrgf_rad
        slider.value_label.setText('1.7')
        slider.value_label.editingFinished.emit()
        self.assertEqual(slider.value(), 17)
        for invalid in ('nan', 'invalid', '999'):
            slider.value_label.setText(invalid)
            slider.value_label.editingFinished.emit()
            self.assertEqual(slider.value(), 17)
            self.assertEqual(slider.value_label.text(), '1.7')
        segments = w.sl_fnrgf_seg
        segments.value_label.setText('64')
        segments.value_label.editingFinished.emit()
        self.assertEqual(segments.value(), 6)
        segments.value_label.setText('63')
        segments.value_label.editingFinished.emit()
        self.assertEqual(segments.value_label.text(), '64')
        QTest.mouseDClick(slider, Qt.MouseButton.LeftButton)
        self.assertEqual(slider.value(), 10)
        self.assertTrue(w.sl_fnrgf_smooth.parameter_row.isHidden())
        w.chk_advanced.setChecked(True)
        self.assertFalse(w.sl_fnrgf_smooth.parameter_row.isHidden())
        w.combo_fnrgf_mode.setCurrentIndex(1)
        self.assertFalse(w.sl_fnrgf_smooth.value_label.isEnabled())
        w.combo_fnrgf_mode.setCurrentIndex(0)
        self.assertTrue(w.sl_fnrgf_smooth.value_label.isEnabled())

    def test_all_parameters_have_editable_rows_and_mode_aware_values(self):
        from PySide6.QtWidgets import QLineEdit
        w = self.window
        for slider in w.findChildren(QSlider):
            self.assertIsInstance(slider.value_label, QLineEdit)
            self.assertIsNotNone(slider.parameter_row)
        w.sl_psb_exposure.value_label.setText('1.25')
        w.sl_psb_exposure.value_label.editingFinished.emit()
        self.assertEqual(w.sl_psb_exposure.value(),125)
        QTest.mouseDClick(w.sl_psb_exposure,Qt.MouseButton.LeftButton)
        self.assertEqual(w.sl_psb_exposure.value(),0)
        for slider in (w.sl_statistics_percentile, w.sl_tangential_outer):
            self.assertFalse(slider.value_label.isEnabled())
            previous = slider.value()
            slider.value_label.setText('1')
            slider.value_label.editingFinished.emit()
            self.assertEqual(slider.value(), previous)
        w.chk_advanced.setChecked(True)
        self.assertFalse(w.sl_wow_denoise[0].parameter_row.isHidden())
        w.chk_advanced.setChecked(False)
        self.assertTrue(w.sl_wow_denoise[0].parameter_row.isHidden())

    def test_long_parameter_labels_put_parenthetical_units_on_second_line(self):
        w = self.window
        self.assertEqual(w.sl_mgn_sigmas[0].title_label.text(), 'Scale 1 sigma\n(native px)')
        self.assertEqual(w.sl_mgn_trunc.title_label.text(), 'Kernel Truncation\n(Sigmas)')
        self.assertEqual(w.sl_larson_sekanina_str.title_label.text(), 'Gain (%)')
        from gui.factories import update_slider_display
        update_slider_display(w.sl_mgn_trunc, title='Long parameter name (preview px)')
        self.assertEqual(w.sl_mgn_trunc.title_label.text(), 'Long parameter name\n(preview px)')

    def test_quantile_counts_remain_integers_and_wow_auto_tracks_the_panel_limit(self):
        import numpy as np
        from gui.filter_controls import collect_controls
        w = self.window
        w.combo_rhef_mode.setCurrentIndex(1)
        w.combo_wow_bilateral.setCurrentIndex(1)
        w.sl_wow_scales.setValue(0)
        for count in (17, 32, 33, 257, 1025):
            w.sl_rhef_quantiles.value_label.setText(str(count))
            w.sl_rhef_quantiles.value_label.editingFinished.emit()
            self.assertEqual(collect_controls(w)['rhef_quantiles'], count)
        w.full_raw_image = np.zeros((80, 96), np.float32)
        w.raw_image = w.full_raw_image
        w.preview_image = w.full_raw_image
        w.update_wow_controls()
        self.assertEqual(w.sl_wow_scales.value_label.text(), 'Auto')
        self.assertEqual(w.collect_filter_parameters(w.raw_image.shape)['wow_scales'], 4)
        for count in (1, 3, 4):
            w.sl_wow_scales.value_label.setText(str(count))
            w.sl_wow_scales.value_label.editingFinished.emit()
            self.assertEqual(w.sl_wow_scales.value(), count)
        w.sl_wow_scales.value_label.setText('auto')
        w.sl_wow_scales.value_label.editingFinished.emit()
        self.assertEqual(w.sl_wow_scales.value(), 0)
        self.assertEqual(w.sl_wow_scales.value_label.text(), 'Auto')
        w.sl_wow_scales.setValue(4)
        w.full_raw_image = np.zeros((20, 24), np.float32)
        w.update_wow_controls()
        self.assertEqual(w.sl_wow_scales.maximum(), 2)
        self.assertEqual(w.sl_wow_scales.value_label.text(), '2')
        self.assertEqual(sum(s.isEnabled() for s in w.sl_wow_denoise), 2)

    def test_known_physical_values_and_finest_symmetry_step(self):
        w = self.window
        for name, expected in {
            'fnrgf_rad': '1', 'mgn_gam': '3.2', 'mgn_k': '0.7', 'mgn_h': '0.7',
            'rhef_upsilon': '0.35', 'rhef_bin': '1', 'achf_kernel': '2',
            'achf_boost': '2',
        }.items():
            self.assertEqual(getattr(w, 'sl_' + name).value_label.text(), expected, name)
        w.sl_fnrgf_seg.setValue(5)
        self.assertEqual(w.sl_fnrgf_seg.value_label.text(), '32')



    def wheel(self, widget, angle=QPoint(0, -120), pixels=QPoint()):
        event = QWheelEvent(QPointF(widget.rect().center()),
                            QPointF(widget.mapToGlobal(widget.rect().center())),
                            pixels, angle, Qt.MouseButton.NoButton,
                            Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False)
        QApplication.sendEvent(widget, event)
        self.app.processEvents()

    def test_wheel_scrolls_sidebar_without_parameter_changes_and_keyboard_still_works(self):
        w = self.window
        w.sec_mgn.toggle_expanded()
        w.sec_mgn.chk_active.setChecked(True)
        w.show()
        self.app.processEvents()
        scroll = w.findChild(QScrollArea)
        bar = scroll.verticalScrollBar()
        self.assertGreater(bar.maximum(), 0)
        slider = w.sl_mgn_gam
        for focused in (False, True):
            slider.setFocus() if focused else slider.clearFocus()
            bar.setValue(bar.maximum() // 2)
            previous = bar.value()
            value = slider.value()
            spy = QSignalSpy(slider.valueChanged)
            self.wheel(slider)
            self.assertGreater(bar.value(), previous)
            self.assertEqual(slider.value(), value)
            self.assertEqual(spy.count(), 0)
            self.wheel(slider, QPoint(0, 120))
            self.assertEqual(bar.value(), previous)
        # Pixel deltas from touchpads are forwarded as well.
        bar.setValue(bar.maximum() // 2)
        previous = bar.value()
        self.wheel(slider, QPoint(0, -120), QPoint(0, -24))
        self.assertGreater(bar.value(), previous)
        combo = w.combo_layers_format
        combo.setFocus()
        index = combo.currentIndex()
        bar.setValue(bar.maximum() // 2)
        previous = bar.value()
        self.wheel(combo)
        self.assertEqual(combo.currentIndex(), index)
        self.assertGreater(bar.value(), previous)
        slider.setFocus()
        before = slider.value()
        QTest.keyClick(slider, Qt.Key.Key_Right)
        self.assertEqual(slider.value(), before + 1)
        self.assertEqual(slider.value_label.text(), '3.3')
