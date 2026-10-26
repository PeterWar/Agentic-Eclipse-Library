"""Round-trip actual GUI controls through exported JSON and original source loading."""
from gui_wait import wait_for_gui, close_window

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import tifffile
from PySide6.QtWidgets import QApplication

from core.project_settings import VERSION, read_settings,write_settings
from gui.app import EclipseProcessorApp
from gui.project_settings import capture_settings,restore_settings


class ProjectSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_save_settings_only_writes_reloadable_json_without_processing(self):
        w=EclipseProcessorApp()
        try:
            w.auto_calculate=False
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);source=root/'source.tif';destination=root/'adjustments.json'
                tifffile.imwrite(source,np.ones((32,48),np.float32))
                w.source_path=str(source)
                w.full_raw_image=np.ones((32,48),np.float32)
                w.raw_image=w.preview_image=w.full_raw_image
                w.txt_x.setText('24');w.txt_y.setText('16');w.txt_r.setText('5')
                w.sl_mgn_opacity.setValue(73)
                with patch('gui.app.QFileDialog.getSaveFileName',return_value=(str(destination),'')), \
                     patch.object(w,'export_image_action',side_effect=AssertionError('Image export called')), \
                     patch.object(w.filter_worker,'_process_pipeline',side_effect=AssertionError('Filter calculated')):
                    w.btn_save_settings.click()
                self.assertTrue(destination.is_file(),w.status_label.text())
                loaded_source,settings=read_settings(destination)
                self.assertEqual(loaded_source,source.resolve())
                self.assertEqual(settings,capture_settings(w))
                self.assertEqual({p.name for p in root.iterdir()},{'source.tif','adjustments.json'})
                with patch('gui.app.QFileDialog.getSaveFileName',return_value=('','')):
                    w.save_settings_action()
                self.assertEqual({p.name for p in root.iterdir()},{'source.tif','adjustments.json'})
        finally:
            close_window(w)

    def test_only_current_file_version_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source.tif';source.touch()
            path=write_settings(root/'output.tif',source,{}, {}, {})
            data=json.loads(path.read_text())
            self.assertEqual(data['version'],VERSION)
            self.assertEqual(VERSION,4)
            for version in (1,2,3,VERSION+1,None,True,'4',4.0):
                data['version']=version;path.write_text(json.dumps(data))
                with self.subTest(version=version),self.assertRaisesRegex(ValueError,'version'):
                    read_settings(path)

    def test_retired_controls_are_rejected_without_changing_current_settings(self):
        from copy import deepcopy
        w=EclipseProcessorApp()
        try:
            w.txt_x.setText('20');w.txt_y.setText('20');w.txt_r.setText('10')
            saved=capture_settings(w)
            for name in ('chk_export_achf_ael','sl_blend','sl_mgn_str','combo_stretch_mode'):
                settings=deepcopy(saved)
                settings['controls'][name]=dict(kind='check',value=True)
                with self.subTest(control=name),self.assertRaises(ValueError):restore_settings(w,settings)
                self.assertEqual(capture_settings(w),saved)
        finally:close_window(w)

    def test_actual_export_then_open_json_restores_all_settings(self):
        windows=[]
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);source=root/'original.tif';output=root/'processed.session.tif'
                with np.load(Path(__file__).parent/'fixtures/ael_achf_iso04.npz') as f:
                    image=f['image']
                tifffile.imwrite(source,image)
                w=EclipseProcessorApp();windows.append(w);w.auto_calculate=False
                with patch('gui.app.QFileDialog.getOpenFileName',return_value=(str(source),'')):
                    w.load_image_action();wait_for_gui(w)
                self.assertEqual(w.source_path,str(source),w.status_label.text())
                for name in ('fnrgf','rhef','mgn','wow','tangential','larson_sekanina','achf'):
                    self.assertEqual(getattr(w,'sl_'+name+'_opacity').value(),10 if name=='wow' else 75 if name=='larson_sekanina' else 19 if name=='achf' else 20)
                for variant,controls in w.achf_ael_controls.items():
                    self.assertEqual(controls['opacity'].value(),10)
                w.chk_advanced.setChecked(True)
                w.combo_input_state.setCurrentIndex(0)
                w.chk_verify_preview.setChecked(True)
                w.sl_psb_exposure.setValue(125)
                w.sec_mgn.chk_active.setChecked(True)
                w.sec_mgn.toggle_expanded()
                w.sl_mgn_opacity.setValue(62)
                w.sl_mgn_sigmas[0].setValue(175)
                w.sl_wow_denoise[0].setValue(13)
                w.sl_wow_denoise[1].setValue(27)
                for index,controls in enumerate(w.achf_ael_controls.values()):
                    controls['opacity'].setValue(41+index)
                    controls['outer_sigma'].setValue(21+index)
                    controls['enabled'].setChecked(index!=1)
                w.combo_achf_variant.setCurrentIndex(3)
                w.chk_export_layers.setChecked(False)
                expected=capture_settings(w)
                with patch('gui.app.QFileDialog.getSaveFileName',return_value=(str(output),'')):
                    w.export_image_action()
                    thread=w._export_thread
                    self.assertIsNotNone(thread)
                    self.assertTrue(thread.wait(30000))
                    self.assertIsNone(thread.error,thread.error)
                    self.app.processEvents()
                settings_file=root/'processed.session.json'
                self.assertTrue(settings_file.is_file())
                document=json.loads(settings_file.read_text())
                self.assertEqual(document['settings'],expected)
                self.assertNotIn('valid_mask',document['parameters'])
                self.assertNotIn('statistics_mask',document['parameters'])
                restored=EclipseProcessorApp();windows.append(restored)
                with patch('gui.app.QFileDialog.getOpenFileName',return_value=(str(settings_file),'')), \
                     patch.object(restored,'detect_lunar_limb',side_effect=AssertionError('Saved geometry was recalculated')):
                    restored.load_image_action();wait_for_gui(restored)
                self.assertEqual(Path(restored.source_path).resolve(),source.resolve(),restored.status_label.text())
                self.assertEqual(capture_settings(restored),expected,restored.status_label.text())
                np.testing.assert_array_equal(restored.full_raw_image,w.full_raw_image)
                from core.result_cache import parameter_signature
                self.assertEqual(parameter_signature(restored.collect_filter_parameters(restored.full_raw_image.shape)),
                                 parameter_signature(w.collect_filter_parameters(w.full_raw_image.shape)))
        finally:
            for window in windows:close_window(window)

    def test_relative_source_survives_moving_project_and_missing_source_is_clear(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);old=root/'old';old.mkdir()
            source=old/'input.tif';source.write_bytes(b'fixture')
            path=write_settings(old/'output.tif',source,dict(controls={}),{}, {})
            moved=root/'moved';shutil.copytree(old,moved)
            resolved,_=read_settings(moved/path.name)
            self.assertEqual(resolved,(moved/'input.tif').resolve())
            source.unlink();(moved/'input.tif').unlink()
            with self.assertRaisesRegex(FileNotFoundError,'Original image not found'):
                read_settings(moved/path.name)

    def test_invalid_json_is_not_treated_as_an_image_and_failed_write_preserves_settings(self):
        w=EclipseProcessorApp();w.auto_calculate=False
        try:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);path=root/'bad.json';path.write_text('{}')
                with patch('gui.app.QFileDialog.getOpenFileName',return_value=(str(path),'')):
                    w.load_image_action();wait_for_gui(w)
                self.assertIsNone(w.full_raw_image)
                self.assertIn('supported',w.status_label.text())
                source=root/'source.tif';source.write_bytes(b'fixture')
                path=write_settings(root/'out.tif',source,{}, {}, {})
                before=path.read_bytes()
                with self.assertRaises(ValueError):
                    write_settings(root/'out.tif',source,dict(bad=float('nan')),{}, {})
                self.assertEqual(path.read_bytes(),before)
                self.assertFalse(list(root.glob('*.tmp')))
        finally:close_window(w)
