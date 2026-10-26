"""Fresh-image AEL defaults, partial settings and the exact AEL WOW operator."""
from gui_wait import wait_for_gui, close_window

import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import tifffile
from PySide6.QtWidgets import QApplication
from core.ael_wow import ael_wow_layer
from core.filters import FilterWorker
from core.layer_engine import LayerEngine, requests
from core.pipeline import apply_filter, execute_pipeline, prepare_parameters
from core.project_settings import write_settings
from gui.app import EclipseProcessorApp
from gui.project_settings import capture_settings, restore_settings, validate_settings


class AELWOWTests(unittest.TestCase):
    def setUp(self):
        with np.load(Path(__file__).parent/'fixtures/ael_achf_iso04.npz') as f:
            self.image=f['image'];self.valid=f['valid'];cx,cy,r=f['geometry']
        self.p=dict(sx=cx,sy=cy,sr=r,wow_mode='ael_bilateral',wow_scales=6,
                    wow_str=100,wow_opacity=37,wow_enabled=True,wow_noise_floor=3.)

    def test_frozen_upstream_ael_oracle_and_excluded_data(self):
        before=self.image.copy()
        actual,info=ael_wow_layer(self.image,self.p,self.valid)
        with np.load(Path(__file__).parent/'fixtures/ael_wow_bilateral.npz') as f:
            np.testing.assert_allclose(actual,f['expected'],atol=1e-7,equal_nan=True)
        altered=self.image.copy();altered[~self.valid]=1e20
        np.testing.assert_array_equal(ael_wow_layer(altered,self.p,self.valid)[0],actual)
        np.testing.assert_array_equal(self.image,before)
        self.assertEqual(info['noise_floor'],3.)
        self.assertFalse(np.isfinite(actual[~self.valid]).any())

    def test_own_noise_floor_changes_output_and_invalid_parameters_fail(self):
        plain,_=ael_wow_layer(self.image,self.p,self.valid)
        changed,_=ael_wow_layer(self.image,dict(self.p,wow_noise_floor=0),self.valid)
        self.assertGreater(np.nanmax(abs(plain-changed)),.001)
        for kw in (dict(wow_noise_floor=np.nan),dict(wow_scales=0.5),dict(wow_scales=11)):
            with self.subTest(parameters=kw),self.assertRaises(ValueError):
                ael_wow_layer(self.image,dict(self.p,**kw),self.valid)

    def test_layer_cache_masks_zero_strength_and_native_scales(self):
        p=dict(self.p,valid_mask=self.valid,statistics_mask=self.valid,layered_model=True)
        engine=LayerEngine();worker=FilterWorker()
        with patch('core.ael_wow.ael_wow_layer',wraps=ael_wow_layer) as operator:
            first=engine.render(worker,self.image,p,{})
            other=engine.render(worker,self.image,dict(p,wow_opacity=80),{})
            self.assertEqual(operator.call_count,1)
            self.assertGreater(np.max(abs(first-other)),.001)
        self.assertFalse(engine.layer(worker,self.image,p,'wow')['alpha'][~self.valid].any())
        self.assertEqual(prepare_parameters(self.p,self.image.shape,self.image.shape,self.image.shape)['wow_scales'],6)
        p=dict(self.p,wow_str=0,valid_mask=self.valid)
        with patch('core.ael_wow.ael_wow_layer',side_effect=AssertionError('Bypass calculated')):
            out=apply_filter(worker,self.image,p,verbose=False)
        np.testing.assert_array_equal(out[self.valid],self.image[self.valid])

    def test_cancellation_and_compatibility_export(self):
        from core.cancellation import ProcessingCancelled
        from core.layer_export import export_layer_package
        import json
        with patch('core.ael_wow.check_cancelled',side_effect=ProcessingCancelled):
            with self.assertRaises(ProcessingCancelled):
                ael_wow_layer(self.image,self.p,self.valid)
        with tempfile.TemporaryDirectory() as tmp:
            package=export_layer_package(FilterWorker(),self.image,dict(self.p,valid_mask=self.valid,wow_str=100,wow_opacity=37),
                                         {},'input.tif',Path(tmp)/'layers')
            recipe=json.loads((package/'recipe.json').read_text())
            self.assertEqual(next(r for r in recipe['layers'] if r['filter']=='wow')['mode'],'Overlay')
            self.assertEqual(next(r for r in recipe['layers'] if r['filter']=='wow')['opacity_255'],round(.37*255))
            layer=tifffile.imread(package/next(r for r in recipe['layers'] if r['filter']=='wow')['file'])
            encoded,_=ael_wow_layer(self.image,self.p,self.valid)
            use=layer[...,3]>0
            np.testing.assert_allclose(layer[...,0][use],encoded[use]*65535,rtol=0,atol=1)


class LoadingDefaultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        with np.load(Path(__file__).parent/'fixtures/ael_achf_iso04.npz') as f:
            self.image=f['image']
        self.source=self.root/'source.tif';tifffile.imwrite(self.source,self.image)
        self.window=EclipseProcessorApp();self.window.auto_calculate=False
        self.window.request_processing_signal.disconnect()

    def tearDown(self):
        close_window(self.window);self.tmp.cleanup()

    def load(self,path):
        with patch('gui.app.QFileDialog.getOpenFileName',return_value=(str(path),'')), \
                patch.object(self.window,'detect_lunar_limb',return_value=(80,63,20)):
            self.window.load_image_action();wait_for_gui(self.window)
        self.assertNotIn('Error loading',self.window.status_label.text())

    def test_first_image_applies_initial_filters_and_psb_preview(self):
        w=self.window
        w.sec_mgn.chk_active.setChecked(True)
        w.sl_mgn_opacity.setValue(10)
        w.sl_nrgf_bin_px.setValue(70)
        w.combo_wow_bilateral.setCurrentIndex(0)
        w.sl_wow_scales.setValue(1)
        w.achf_ael_controls['ael_iso_04']['sigmas'][0].setValue(80)
        w.achf_ael_controls['ael_iso_01']['enabled'].setChecked(True)
        w.chk_achf_adaptive.setChecked(True)
        self.load(self.source)
        p=w.collect_filter_parameters(w.full_raw_image.shape)
        self.assertEqual([(n,v) for n,v,_,_ in requests(p)],
                         [('fnrgf',None),('mgn',None),('wow',None),('achf','ael_iso_04'),('achf','ael_angular_4')])
        self.assertFalse(p['nrgf_enabled'])
        display=w.collect_display_parameters()
        self.assertTrue(w.btn_psb_preview.isChecked())
        self.assertNotIn('mode',display)
        self.assertNotIn('strength',display)
        for name in ('fnrgf','rhef','mgn','tangential','larson_sekanina','achf'):
            self.assertEqual(p[name+'_str'],25 if name == 'larson_sekanina' else 100)
            self.assertEqual(getattr(w,'sl_'+name+'_opacity').value(),75 if name == 'larson_sekanina' else 19 if name == 'achf' else 20)
        self.assertEqual((p['nrgf_str'],p['nrgf_opacity'],p['nrgf_bin_px']),(100,40,2.))
        self.assertEqual((p['wow_mode'],p['wow_scales'],p['wow_noise_floor'],p['wow_str'],p['wow_opacity']),
                         ('ael_bilateral',6,3.,100,10))
        self.assertEqual(p['achf_ael_parameters']['sigmas'],[1.,2.,4.,8.,16.])
        self.assertEqual((p['achf_str'],p['achf_variants']['ael_iso_04']['opacity']),(100,10))
        self.assertFalse(w.chk_achf_adaptive.isChecked())
        angular=p['achf_variants']['ael_angular_4']
        self.assertTrue(angular['enabled'])
        self.assertEqual((angular['strength'],angular['opacity']),(100,10))
        for variant in ('ael_iso_01',):
            c=w.achf_ael_controls[variant]
            self.assertFalse(c['enabled'].isChecked())
            self.assertNotIn('strength',c)
            self.assertEqual(c['opacity'].value(),10)
        self.assertTrue(np.isfinite(execute_pipeline(FilterWorker(),w.full_raw_image,p)).all())

    def test_next_image_preserves_every_filter_control_and_activation(self):
        from core.layer_engine import ORDER
        from gui.project_settings import filter_widgets
        self.load(self.source);w=self.window
        for index,name in enumerate(ORDER+('achf',)):
            getattr(w,'sec_'+name).chk_active.setChecked(index%2==0)
            if name == 'larson_sekanina':w.sl_larson_sekanina_str.setValue(11+index)
            getattr(w,'sl_'+name+'_opacity').setValue(81-index)
        w.sl_fnrgf_ord.setValue(11)
        w.sl_fnrgf_bin_px.setValue(9)
        w.sl_fnrgf_rmax.setValue(41)
        w.sl_achf_kernel.setValue(77)
        w.sl_nrgf_bin_px.setValue(35)
        w.combo_wow_bilateral.setCurrentIndex(1)
        w.sl_wow_scales.setValue(w.sl_wow_scales.maximum())
        w.sl_wow_denoise[0].setValue(23)
        w.sl_wow_noise_floor.setValue(42)
        w.chk_achf_adaptive.setChecked(True)
        for index,controls in enumerate(w.achf_ael_controls.values()):
            controls['enabled'].setChecked(index!=1)
            controls['opacity'].setValue(61+index)
            controls['outer_sigma'].setValue(20+index)
        w.combo_achf_variant.setCurrentIndex(3)
        expected=capture_settings(w)
        names=set(filter_widgets(w))
        second=self.root/'second.tif'
        tifffile.imwrite(second,self.image[:64,:80])
        self.load(second)
        actual=capture_settings(w)
        self.assertEqual({key:value for key,value in actual['controls'].items() if key in names},
                         {key:value for key,value in expected['controls'].items() if key in names})
        self.assertEqual(actual['sections'],expected['sections'])
        self.assertEqual(w.full_raw_image.shape,(64,80))

    def test_json_takes_priority_and_omitted_filters_and_variants_stay_off(self):
        self.load(self.source);w=self.window
        settings=capture_settings(w)
        settings['controls']['sl_mgn_opacity']['value']=62
        settings['sections']['sec_mgn']['active']=True
        settings['sections']['sec_fnrgf']['active']=False
        for name in ('nrgf','wow'):
            settings['sections'].pop('sec_'+name)
            settings['controls']={key:record for key,record in settings['controls'].items() if '_'+name+'_' not in key}
        settings['controls'].pop('achf_ael_controls.ael_iso_04.enabled')
        settings['controls'].pop('achf_ael_controls.ael_angular_4.enabled')
        project=write_settings(self.root/'project.tif',self.source,settings,{}, {})
        # Start from an active recipe, then load a partial JSON through the actual action.
        self.load(project)
        p=w.collect_filter_parameters(w.full_raw_image.shape)
        self.assertEqual([(n,v) for n,v,_,_ in requests(p)],[('mgn',None)])
        self.assertEqual((p['mgn_str'],p['mgn_opacity']),(100,62))
        self.assertFalse(w.achf_ael_controls['ael_iso_04']['enabled'].isChecked())
        self.load(self.source)
        self.assertEqual([(n,v) for n,v,_,_ in requests(w.collect_filter_parameters(w.full_raw_image.shape))],
                         [('mgn',None)])

    def test_full_json_preserves_explicit_values_and_unknown_controls_are_rejected(self):
        self.load(self.source);w=self.window
        settings=capture_settings(w)
        settings['controls']['sl_wow_opacity']['value']=91
        settings['controls']['combo_wow_bilateral']=dict(kind='combo',value=1,text=w.combo_wow_bilateral.itemText(1))
        settings['controls']['sl_wow_scales']['value']=3
        restore_settings(w,settings)
        self.assertEqual(capture_settings(w),settings)
        bad=deepcopy(settings);bad['controls']['unknown_filter']=dict(kind='slider',value=1)
        with self.assertRaises(ValueError):validate_settings(w,bad)
        bad=deepcopy(settings);bad['controls']['sl_mgn_str']=dict(kind='slider',value='25')
        with self.assertRaises(ValueError):validate_settings(w,bad)

    def test_json_without_any_filter_does_not_fall_back_to_ael(self):
        from gui.project_settings import filter_widgets
        self.load(self.source);w=self.window
        settings=capture_settings(w)
        filter_names=set(filter_widgets(w))
        settings['controls']={key:record for key,record in settings['controls'].items() if key not in filter_names}
        settings['sections']={key:record for key,record in settings['sections'].items() if key in ('sec_geo',)}
        project=write_settings(self.root/'empty_filters.tif',self.source,settings,{}, {})
        self.load(project)
        self.assertEqual(requests(w.collect_filter_parameters(w.full_raw_image.shape)),[])
        self.assertFalse(w.chk_achf_adaptive.isChecked())
        self.assertTrue(all(not c['enabled'].isChecked() for c in w.achf_ael_controls.values()))
