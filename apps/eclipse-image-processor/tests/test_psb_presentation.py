"""AEL tone mapping, automatic exposure, preview parity and export isolation."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import tifffile
from psd_tools import PSDImage
from core.presentation import ael_tone_map, psb_presentation_settings
from core.layer_engine import engine_for
from core.layer_package import export_layered_package
from core.export import export_images
from core.filters import FilterWorker
from core.result_cache import parameter_signature


class PSBPresentationTests(unittest.TestCase):
    def test_ael_curve_has_shared_rgb_shoulder_and_preserves_highlight_order(self):
        rgb=np.array([[[0.,0.,0.],[1.,2.,4.],[2.,4.,8.],[np.nan]*3]])
        valid=np.array([[True,True,True,False]])
        settings=dict(scale=1.,strength=10.,highlight_ceiling=.9)
        actual=ael_tone_map(rgb,valid,settings)
        u=np.arcsinh(rgb[0,1:3]*10)/np.arcsinh(10.)
        peak=u.max(axis=-1)
        expected=u*(.9*(-np.expm1(-peak/.9))/peak)[:,None]
        np.testing.assert_allclose(actual[0,1:3],expected,rtol=1e-7)
        self.assertTrue((actual[0,2]>actual[0,1]).all())
        self.assertTrue((actual < .9).all())
        np.testing.assert_array_equal(actual[0,[0,3]],0)
        np.testing.assert_allclose(actual[0,1,:]/actual[0,1,0],u[0]/u[0,0],rtol=1e-7)
        self.assertTrue(np.isnan(rgb[0,3]).all())
        for scale in (0.,np.inf,-1.):
            with self.assertRaises(ValueError):ael_tone_map(rgb,valid,dict(settings,scale=scale))
        with self.assertRaises(ValueError):ael_tone_map(rgb,np.ones_like(valid),settings)

    def test_automatic_scale_rejects_lunar_pixels_outliers_and_missing_samples(self):
        y,x=np.indices((128,160));r=np.hypot(x-80,y-64)
        source=np.full(r.shape,100.,np.float32)
        source[r<20]=1.e8;source[0,0]=1.e8;source[1,1]=np.nan
        params=dict(sx=80,sy=64,sr=20)
        baseline=psb_presentation_settings(source,params=params)
        brighter=psb_presentation_settings(source,params=params,exposure_ev=1.)
        self.assertEqual(baseline['scale'],100.)
        self.assertEqual(brighter['scale'],50.)
        mask=np.isfinite(source)
        self.assertGreater(ael_tone_map(source,mask,brighter)[0,1],ael_tone_map(source,mask,baseline)[0,1])
        for bad in (np.nan,np.inf,-7,7):
            with self.assertRaises(ValueError):psb_presentation_settings(source,exposure_ev=bad)
        self.assertEqual(psb_presentation_settings(np.zeros((4,4)))['scale'],1.)
        np.testing.assert_array_equal(ael_tone_map(np.zeros((4,4)),np.ones((4,4),bool),baseline),0)

    def test_exposure_changes_psb_and_preview_jpeg_but_never_tiff_or_hidden_reference(self):
        source=np.linspace(1,1000,32*48,dtype=np.float32).reshape(32,48)
        rgb=source[...,None]*np.array([.5,1.,.8])
        params=dict(layered_model=True,sx=24,sy=16,sr=4,mgn_enabled=True,
                    mgn_str=100,mgn_gam=320,mgn_opacity=20,mgn_sigmas=(1.,2.))
        display=dict(mode='log',strength=30)
        worker=FilterWorker();engine=engine_for(worker);engine.prepare(worker,source,params)
        with tempfile.TemporaryDirectory() as tmp:
            outputs=[];previews=[];bases=[];references=[]
            for i,ev in enumerate((0.,1.)):
                target=Path(tmp)/f'image{i}.tif'
                export_images(source,params,display,str(target),'source.tif',source_rgb=rgb,
                              export_layers=True,layers_format='psb',psb_exposure_ev=ev,psb_preview_jpeg=True,layer_cache=engine)
                outputs.append(tifffile.imread(target))
                previews.append(target.with_name(f'image{i}_preview.jpg').read_bytes())
                doc=PSDImage.open(target.with_name(f'image{i}_PS_layers.psb'))
                import cv2
                jpeg=cv2.cvtColor(cv2.imread(str(target.with_name(f'image{i}_preview.jpg'))),cv2.COLOR_BGR2RGB)
                planes=doc._record.image_data.get_data(doc._record.header)
                composite=np.stack([np.frombuffer(plane,dtype='>u2').reshape(source.shape) for plane in planes],axis=-1)
                self.assertLess(float(np.mean(abs(jpeg.astype(float)-composite/65535.*255))),3.)
                self.assertFalse(doc[1].visible)
                references.append(doc[1]._channels[1].get_data(48,32,16,2))
                bases.append(np.frombuffer(doc[2]._channels[1].get_data(48,32,16,2),dtype='>u2'))
            np.testing.assert_array_equal(outputs[0],outputs[1])
            self.assertNotEqual(previews[0],previews[1])
            self.assertEqual(references[0],references[1])
            self.assertGreater(float(bases[1].mean()),float(bases[0].mean()))


from PySide6.QtWidgets import QApplication
from gui.app import EclipseProcessorApp
from gui.project_settings import capture_settings, restore_settings
from gui_wait import wait_for_gui, close_window


class PSBPresentationGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_preview_is_default_above_exports_and_current_controls_round_trip(self):
        from copy import deepcopy
        w=EclipseProcessorApp();w.auto_calculate=False
        try:
            self.assertTrue(w.btn_psb_preview.isChecked())
            for name in ('combo_stretch_mode','sl_stretch','sl_ghs_sp'):
                self.assertFalse(hasattr(w,name))
            group=w.sl_psb_exposure.parameter_row.parentWidget().parentWidget()
            layout=group.parentWidget().layout()
            self.assertLess(layout.indexOf(group),layout.indexOf(w.chk_export_layers))
            w.chk_export_layers.setChecked(False)
            self.assertTrue(w.btn_psb_preview.isChecked())
            self.assertTrue(w.sl_psb_exposure.isEnabled())
            w.txt_x.setText('32');w.txt_y.setText('32');w.txt_r.setText('5')
            w.sl_psb_exposure.setValue(200)
            saved=capture_settings(w)
            restore_settings(w,saved)
            self.assertTrue(w.btn_psb_preview.isChecked())
            self.assertEqual(w.sl_psb_exposure.value(),200)
            self.assertNotIn('sec_stretch',saved['sections'])
            invalid=deepcopy(saved);invalid['controls']['unknown_control']=dict(kind='slider',value=1)
            with self.assertRaises(ValueError):restore_settings(w,invalid)
        finally:close_window(w)

    def test_native_preview_matches_layer_package_and_ev_reuses_filter_cache(self):
        w=EclipseProcessorApp();w.auto_calculate=False;w.request_processing_signal.disconnect()
        try:
            source=np.linspace(1,1000,40*48,dtype=np.float32).reshape(40,48)
            w.full_raw_image=w.raw_image=w.preview_image=source
            w.full_source_rgb=source[...,None]*np.array([.6,1.,.9])
            w.chk_calibrate_colour.setChecked(False)
            w.txt_x.setText('24');w.txt_y.setText('20');w.txt_r.setText('4')
            w.sec_mgn.chk_active.setChecked(True)
            params=w.collect_filter_parameters(source.shape)
            engine=engine_for(w.filter_worker)
            composition=engine.render(w.filter_worker,source,params,w.collect_display_parameters())
            w.processed_image=composition
            w._full_cache=(source,parameter_signature(params),composition,w._preview_revision)
            w.set_preview_zoom(1.);wait_for_gui(w)
            display=w.collect_display_parameters()
            signature=parameter_signature(params)
            with patch.object(engine,'_calculate',side_effect=AssertionError('Recalculated a filter')):
                w.btn_psb_preview.setChecked(True);wait_for_gui(w)
                self.assertFalse(hasattr(w,'sec_stretch'))
                before=w.image_label._native_pixels.copy()
                w.sl_psb_exposure.setValue(100);w.render_matrix_to_screen();wait_for_gui(w)
                self.assertFalse(np.array_equal(before,w.image_label._native_pixels))
            self.assertEqual(parameter_signature(w.collect_filter_parameters(source.shape)),signature)
            self.assertEqual(w.collect_display_parameters(),display)
            settings=psb_presentation_settings(source,rgb=w.full_source_rgb,params=params,exposure_ev=1.)
            with tempfile.TemporaryDirectory() as tmp:
                root=export_layered_package(w.filter_worker,source,params,settings,'source.tif',Path(tmp)/'layers',rgb=w.full_source_rgb)
                recipe=json.loads((root/'recipe.json').read_text())
                expected=tifffile.imread(root/recipe['combined']).astype(float)/65535.
                np.testing.assert_allclose(w.image_label._native_pixels,np.clip(expected*255,0,255).astype(np.uint8),atol=1)
            self.assertIn('PSB preview',w.lbl_view_state.text())
            saved=capture_settings(w)
            w.btn_psb_preview.setChecked(False);wait_for_gui(w)
            self.assertFalse(hasattr(w,'sl_stretch'))
            normal=w.last_preview_presentation.copy()
            w.sl_psb_exposure.setValue(-100);w.render_matrix_to_screen();wait_for_gui(w)
            np.testing.assert_array_equal(w.last_preview_presentation,normal)
            restore_settings(w,saved)
            self.assertEqual(w.sl_psb_exposure.value(),100)
            self.assertTrue(w.btn_psb_preview.isChecked())
            old=capture_settings(w);old['controls'].pop('sl_psb_exposure')
            with self.assertRaises(ValueError):restore_settings(w,old)
            self.assertEqual(w.sl_psb_exposure.value(),100)
        finally:close_window(w)
