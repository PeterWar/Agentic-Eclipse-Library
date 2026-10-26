"""Known-slope recovery, preservation of coronal structure, missing data and sample controls."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from copy import deepcopy
import unittest
from unittest.mock import patch
import numpy as np
from PySide6.QtWidgets import QApplication
from core.background import equalize_background,sample_grid
from core.image_data import resize_observed
from gui.app import EclipseProcessorApp
from gui.project_settings import capture_settings,restore_settings
from gui_wait import wait_for_gui,close_window


def scene(rgb=False):
    h,w=240,320;y,x=np.indices((h,w))
    u=(x+.5)/w*2-1;v=(y+.5)/h*2-1
    corona=np.maximum(1-np.hypot(x-160,y-120)/60,0)**2*.5
    if rgb:
        slopes=np.array([[.03,.05,-.01],[-.02,.01,.04]])
        image=.3+u[...,None]*slopes[0]+v[...,None]*slopes[1]+corona[...,None]
    else:
        slopes=np.array([[.03],[-.02]])
        image=.3+.03*u-.02*v+corona
    image=image.astype(np.float32)
    mono=image.mean(axis=-1) if rgb else image
    return dict(full=mono,rgb=image if rgb else None,preview=resize_observed(mono,(80,60))),slopes,corona


class BackgroundTests(unittest.TestCase):
    def test_known_rgb_and_mono_slopes_recovered_and_corona_preserved(self):
        for rgb in (False,True):
            base,slopes,corona=scene(rgb)
            original=(base['rgb'] if rgb else base['full']).copy()
            result=equalize_background(base,(160,120,15),5,16)
            coefficients=np.asarray(result['report']['coefficients'])
            np.testing.assert_allclose(coefficients[1:],slopes,atol=2e-6)
            corrected=result['rgb'] if rgb else result['full']
            if rgb:
                from core.linear_export import split_source_channels
                np.testing.assert_array_equal(result['full'],split_source_channels(corrected)[0])
            sky_level=.3+np.asarray(result['report']['reference'])@slopes
            expected=sky_level+corona[...,None] if rgb else sky_level[0]+corona
            np.testing.assert_allclose(corrected,expected,atol=2e-6)
            np.testing.assert_array_equal(base['rgb'] if rgb else base['full'],original)

    def test_zero_and_missing_pixels_preserved_and_bright_patches_rejected(self):
        base,slopes,_=scene(True)
        base['rgb'][100:140,140:180]=0
        base['rgb'][:8,:8]=np.nan
        base['rgb'][20,300]=-1
        points=sample_grid(base['full'].shape,(160,120,15),5,16)
        for x,y in points[:5]:base['rgb'][y-2:y+3,x-2:x+3]+=2
        result=equalize_background(base,(160,120,15),5,16)
        np.testing.assert_array_equal(result['rgb'][100:140,140:180],0)
        self.assertTrue(np.isnan(result['rgb'][:8,:8]).all())
        self.assertTrue((result['rgb'][20,300]<0).all())
        np.testing.assert_allclose(np.asarray(result['report']['coefficients'])[1:],slopes,atol=1e-4)
        self.assertLess(result['report']['inliers'],result['report']['samples'])

    def test_sampling_excludes_whole_patches_and_rejects_insufficient_coverage(self):
        base,_,_=scene()
        points=sample_grid(base['full'].shape,(160,120,15),5,16)
        self.assertTrue(all(np.hypot(x-160,y-120)-np.sqrt(2)*2>=75 for x,y in points))
        for samples in ([],[(x,10) for x in range(10,300,20)]):
            with self.assertRaises(ValueError):equalize_background(base,(160,120,15),5,16,samples)
        with self.assertRaises(ValueError):equalize_background(base,(160,120,15),100,16)
        result=equalize_background(base,(160,120,15),5,16,enabled=False)
        self.assertIs(result['full'],base['full'])
        self.assertIsNone(result['report'])


class BackgroundGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.w=EclipseProcessorApp();w=self.w;w.auto_calculate=False
        w.request_processing_signal.disconnect();self.requests=[]
        w.request_processing_signal.connect(lambda a,p:self.requests.append((a,p)))
        self.base,_,_=scene(True)
        w.full_raw_image=self.base['full'];w.full_source_rgb=self.base['rgb']
        w.raw_image=w.preview_image=self.base['preview'];w.processed_image=w.raw_image
        w.txt_x.setText('160');w.txt_y.setText('120');w.txt_r.setText('15')
        w.chk_calibrate_colour.setChecked(False);wait_for_gui(w)
        w.background.reset_source(self.base,None)
        w.recalculation_timer.stop();w.presentation_timer.stop()

    def tearDown(self):close_window(self.w)

    def test_enable_disable_prepares_all_layers_and_keeps_original(self):
        w=self.w
        w.chk_background.setChecked(True);w.sl_background_radius.setValue(50)
        w.dispatch_pipeline_request();wait_for_gui(w)
        self.assertIsNot(w.full_raw_image,self.base['full'])
        self.assertTrue(w.background.report['preserve_sky_level'])
        self.assertIs(w._display_reference_source,w.full_raw_image)
        self.assertEqual(w.collect_display_parameters()['normalization_range'],[float(np.nanmin(w.full_raw_image)),float(np.nanmax(w.full_raw_image))])
        self.assertEqual(len(self.requests),1)
        self.assertEqual(self.requests[0][1]['background_extraction'],w.background.report)
        w.on_processing_finished(w.raw_image.copy());wait_for_gui(w)
        w.chk_background.setChecked(False);w.dispatch_pipeline_request();wait_for_gui(w)
        self.assertIs(w.full_raw_image,self.base['full'])
        self.assertIs(w.full_source_rgb,self.base['rgb'])
        self.assertIsNone(w.background.report)
        self.assertEqual(w.collect_display_parameters()['normalization_range'],[float(np.nanmin(self.base['full'])),float(np.nanmax(self.base['full']))])

    def test_manual_samples_round_trip_and_missing_current_controls_are_rejected(self):
        w=self.w;w.background.generate()
        self.assertTrue(w.btn_background_samples.isChecked())
        initial=len(w.background.points)
        w.background.add_point(160,120)
        self.assertEqual(len(w.background.points),initial)
        w.background.add_point(15,15)
        self.assertEqual(len(w.background.points),initial+1)
        settings=capture_settings(w)
        w.background.points=None;restore_settings(w,settings)
        self.assertEqual(capture_settings(w),settings)
        bad=deepcopy(settings);bad['background_samples']=[[float('nan'),1]]
        with self.assertRaises(ValueError):restore_settings(w,bad)
        old=deepcopy(settings);old.pop('background_samples');old['sections'].pop('sec_background')
        for key in ('chk_background','sl_background_radius','sl_background_grid'):old['controls'].pop(key)
        with self.assertRaises(ValueError):restore_settings(w,old)
        self.assertEqual(capture_settings(w),settings)

    def test_actual_psb_tiff_sources_and_json_reload_apply_correction_once(self):
        import json,tempfile,time
        from pathlib import Path
        import tifffile
        from PySide6.QtTest import QTest
        w=self.w
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source.tif';out=root/'equalized.tif'
            tifffile.imwrite(source,self.base['rgb'],photometric='rgb')
            w.source_path=str(source)
            w.chk_background.setChecked(True);w.sl_background_radius.setValue(50)
            with patch('gui.app.QFileDialog.getSaveFileName',return_value=(str(out),'')):
                w.export_image_action()
                deadline=time.monotonic()+30
                while w.background.thread is not None and time.monotonic()<deadline:
                    self.app.processEvents();time.sleep(.01)
                self.assertIsNone(w.background.thread)
                if w._export_thread is not None:
                    self.assertTrue(w._export_thread.wait(90000))
                    self.app.processEvents()
                wait_for_gui(w)
            self.assertTrue(out.is_file(),w.status_label.text())
            self.assertEqual(tifffile.imread(out).dtype,np.uint16)
            self.assertTrue((root/'equalized_PS_layers.psb').is_file())
            document=json.loads((root/'equalized.json').read_text())
            self.assertTrue(document['parameters']['background_extraction']['preserve_sky_level'])
            from core.linear_export import export_linear_sources
            export_linear_sources(w.full_raw_image,w.full_source_rgb,source,root/'equalized_sources','linear',preprocessing=w.background.report)
            linear=json.loads((root/'equalized_sources/sources.json').read_text())
            self.assertEqual(linear['preprocessing'],w.background.report)
            expected=w.full_raw_image.copy()
            reloaded=EclipseProcessorApp()
            try:
                with patch('gui.app.QFileDialog.getOpenFileName',return_value=(str(root/'equalized.json'),'')):
                    reloaded.load_image_action();wait_for_gui(reloaded)
                reloaded.dispatch_pipeline_request();wait_for_gui(reloaded)
                deadline=time.monotonic()+10
                while reloaded.is_processing and time.monotonic()<deadline:QTest.qWait(10)
                wait_for_gui(reloaded)
                np.testing.assert_allclose(reloaded.full_raw_image,expected,atol=1e-6)
                np.testing.assert_array_equal(tifffile.imread(source),self.base['rgb'])
            finally:close_window(reloaded)

    def test_export_applies_pending_background_before_building_export_request(self):
        w=self.w;w.chk_background.setChecked(True);w.sl_background_radius.setValue(50)
        original_action=w.export_image_action
        with patch.object(w,'export_image_action') as after_fit:
            original_action();wait_for_gui(w)
            after_fit.assert_called_once()
        self.assertIsNotNone(w.background.report)
        self.assertFalse(w.background.dirty)
