"""Count real filter calculations across native GUI verification and saving."""
from gui_wait import close_window

from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PySide6.QtWidgets import QApplication

from core.image_data import resize_observed
from core.layer_engine import LayerEngine
from core.result_cache import parameter_signature
from gui.app import EclipseProcessorApp


class NativeExportCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.window=EclipseProcessorApp()
        w=self.window;w.auto_calculate=False
        with np.load(Path(__file__).parent/'fixtures/ael_achf_iso04.npz') as fixture:
            w.full_raw_image=fixture['image'].astype(np.float32)
        w.raw_image=resize_observed(w.full_raw_image,(80,64))
        w.preview_image=w.raw_image
        w.txt_x.setText('80');w.txt_y.setText('63');w.txt_r.setText('20')
        w.chk_verify_preview.setChecked(True)
        for name in ('fnrgf','rhef','mgn','wow','tangential','larson_sekanina','achf'):
            getattr(w,'sec_'+name).chk_active.setChecked(True)
        w.chk_achf_adaptive.setChecked(True)
        self.calls=[]
        original=LayerEngine._calculate
        def calculate(engine,worker,source,params,name,variant):
            self.calls.append((name,variant))
            return original(engine,worker,source,params,name,variant)
        self.capture=patch.object(LayerEngine,'_calculate',autospec=True,side_effect=calculate)
        self.capture.start()
        self.output=redirect_stdout(io.StringIO());self.output.__enter__()

    def tearDown(self):
        close_window(self.window)
        self.capture.stop()
        self.output.__exit__(None,None,None)

    def verify_native(self):
        w=self.window
        p=w.collect_filter_parameters(w.full_raw_image.shape)
        w._running_signature=parameter_signature(p)
        w._running_full_job=True
        result=w.filter_worker._process_pipeline(w.full_raw_image,p)
        w.on_processing_finished(result)
        self.assertIsNotNone(w._full_cache)

    def save(self,path):
        w=self.window
        with patch('gui.app.QFileDialog.getSaveFileName',return_value=(str(path),'')):
            w.export_image_action()
            self.assertIsNotNone(w._export_thread)
            thread=w._export_thread
            self.assertTrue(thread.wait(30000))
            self.assertIsNone(thread.error,thread.error)
            self.app.processEvents()
        self.assertIsNone(w._export_thread)
        self.assertTrue(path.is_file())

    def test_native_all_filters_then_psb_and_tiff_save_have_zero_recalculations(self):
        w=self.window
        for controls in w.achf_ael_controls.values():controls['enabled'].setChecked(True)
        self.verify_native()
        self.assertEqual(len(self.calls),10)
        self.calls.clear()
        with tempfile.TemporaryDirectory() as tmp:
            self.save(Path(tmp)/'native_psb.tif')
            self.assertEqual(self.calls,[])
            # These invalidate the rendered composite, not its numerical layers.
            w.sl_mgn_opacity.setValue(47)
            w.sl_psb_exposure.setValue(125)
            w.chk_verify_preview.setChecked(False)
            w.filter_worker._process_pipeline(w.raw_image,w.collect_filter_parameters(w.raw_image.shape))
            self.assertEqual(len(self.calls),10)  # first calculation at the smaller preview scale
            self.calls.clear()
            w.combo_layers_format.setCurrentIndex(w.combo_layers_format.findData('tiff'))
            self.save(Path(tmp)/'native_tiff.tif')
            self.assertEqual(self.calls,[])

    def test_export_cache_is_not_merged_into_a_replaced_source(self):
        from types import SimpleNamespace
        w=self.window
        original=w.full_raw_image
        copied=original.copy()
        snapshot=LayerEngine()
        thread=SimpleNamespace(source_identity=original,
            request=dict(source=copied,layer_cache=snapshot),error=None,message='Exported',
            deleteLater=lambda:None)
        w._export_thread=thread
        w.full_raw_image=original.copy()  # same shape, different observation identity
        with patch.object(LayerEngine,'absorb') as absorb:
            w._on_export_finished()
            absorb.assert_not_called()

    def test_export_only_active_achf_and_reuses_newly_enabled_variants(self):
        w=self.window
        self.verify_native()
        self.assertEqual(len(self.calls),7)
        self.calls.clear()
        with tempfile.TemporaryDirectory() as tmp:
            self.save(Path(tmp)/'first.tif')
            self.assertEqual(self.calls,[])
            w.achf_ael_controls['ael_iso_04']['enabled'].setChecked(True)
            self.save(Path(tmp)/'enabled.tif')
            self.assertEqual(self.calls,[('achf','ael_iso_04')])
            self.calls.clear()
            self.save(Path(tmp)/'second.tif')
            self.assertEqual(self.calls,[])
