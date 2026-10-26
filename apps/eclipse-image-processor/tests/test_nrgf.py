"""AEL NRGF nulls, observed support, independent composition and persisted UI."""
from gui_wait import close_window

import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import tifffile
from PySide6.QtWidgets import QApplication
from core.filters import FilterWorker
from core.nrgf import nrgf_normalize, nrgf_layer
from core.layer_engine import LayerEngine, requests
from core.pipeline import apply_filter, execute_pipeline, prepare_parameters
from core.export import export_images
from gui.app import EclipseProcessorApp
from gui.project_settings import capture_settings, restore_settings


def corona():
    y, x = np.indices((80, 96), dtype=float)
    r = np.hypot(x-47.3, y-39.7)
    theta = np.arctan2(y-39.7, x-47.3)
    return (100/(1+r/8)**3*(1+.15*np.cos(5*theta))+.002*np.random.default_rng(64).normal(size=r.shape)).astype(np.float32)


class NRGFTests(unittest.TestCase):
    def setUp(self):
        self.image=corona()
        self.p=dict(sx=47.3,sy=39.7,sr=8.,nrgf_enabled=True,nrgf_str=100,
                    nrgf_opacity=39,nrgf_bin_px=2.,nrgf_min_count=12)

    def test_matches_bundled_ael_133_oracles(self):
        y,x=np.indices(self.image.shape,dtype=float)
        valid=np.hypot(x-47.3,y-39.7)>8
        valid[10:30,35:45]=False
        # Frozen outputs from AEL 1.3.3 radial.continuous_nrgf, bin_px=2, min_count=12.
        with np.load(Path(__file__).parent/'fixtures/ael_nrgf.npz') as oracle:
            for key,a,kw in (('robust',self.image,{}),('signed_mean',self.image-.2,dict(robust=False)),
                             ('smooth',self.image,dict(smooth_bins=2.))):
                with self.subTest(variant=key):
                    np.testing.assert_allclose(nrgf_normalize(a,47.3,39.7,8.,valid,**kw),
                                               oracle[key],rtol=1e-6,atol=1e-6,equal_nan=True)

    def test_constant_radial_and_sparse_inputs_are_undefined(self):
        y,x=np.indices(self.image.shape,dtype=float)
        r=np.hypot(x-47.3,y-39.7)
        for a,kw in ((np.ones_like(r),{}), ((100/(1+r/8)**3).astype(np.float32),{}),
                     (self.image,dict(min_count=100000))):
            with self.subTest(parameters=kw,constant=np.ptp(a)==0):
                q=nrgf_normalize(a,47.3,39.7,8.,**kw)
                self.assertFalse(np.isfinite(q).any())
        layer=LayerEngine().layer(FilterWorker(),np.ones_like(self.image),self.p,'nrgf')
        self.assertFalse(layer['alpha'].any())
        np.testing.assert_array_equal(layer['image'],65535)

    def test_angular_signal_signed_radiance_and_intensity_units(self):
        q=nrgf_normalize(self.image,47.3,39.7,8.)
        self.assertGreater(np.isfinite(q).mean(),.85)
        scaled=nrgf_normalize(self.image*65535,47.3,39.7,8.)
        np.testing.assert_allclose(q,scaled,rtol=3e-4,atol=3e-4,equal_nan=True)
        signed=nrgf_normalize(self.image-.2,47.3,39.7,8.)
        self.assertTrue(np.isfinite(signed[self.image<.2]).any())
        self.assertGreater(np.nanstd(q),.1)

    def test_masked_nonfinite_and_statistics_exclusions_do_not_leak(self):
        valid=np.ones_like(self.image,bool);valid[10:30,35:45]=False
        a=self.image.copy();a[~valid]=np.nan;a[0,0]=np.inf
        q=nrgf_normalize(a,47.3,39.7,8.,valid)
        b=a.copy();b[~valid]=1e15
        np.testing.assert_array_equal(q,nrgf_normalize(b,47.3,39.7,8.,valid))
        self.assertFalse(np.isfinite(q[~valid]).any())
        self.assertFalse(np.isfinite(q[0,0]))
        support=valid.copy();support[45:60,60:70]=False
        p=dict(self.p,valid_mask=valid,statistics_mask=support)
        a=self.image.copy();a[~valid]=np.nan
        first=apply_filter(FilterWorker(),a,p,verbose=False)
        b=a.copy();b[valid & ~support]=1e15
        second=apply_filter(FilterWorker(),b,p,verbose=False)
        np.testing.assert_array_equal(first[support],second[support])
        np.testing.assert_array_equal(second[valid & ~support],b[valid & ~support])
        self.assertTrue(np.isnan(second[~valid]).all())

    def test_invalid_parameters_and_strength_zero(self):
        for kw in (dict(bin_px=0),dict(bin_px=np.nan),dict(min_count=1),dict(min_count=2.5),
                   dict(smooth_bins=-1),dict(valid=np.ones((2,2),bool))):
            with self.subTest(parameters=kw),self.assertRaises(ValueError):
                nrgf_normalize(self.image,47.3,39.7,8.,**kw)
        worker=FilterWorker()
        with patch('core.nrgf.nrgf_layer',side_effect=AssertionError('Bypass calculated')):
            np.testing.assert_array_equal(worker.run_nrgf_native(self.image,0,47.3,39.7,8.),self.image)
        with self.assertRaises(ValueError):
            worker.run_nrgf_native(self.image,101,47.3,39.7,8.)

    def test_cancellation_inside_annular_measurement_does_not_cache_partial_layer(self):
        from core.cancellation import ProcessingCancelled
        engine=LayerEngine()
        with patch('core.nrgf.check_cancelled',side_effect=[None,None,ProcessingCancelled()]):
            with self.assertRaises(ProcessingCancelled):
                engine.layer(FilterWorker(),self.image,self.p,'nrgf')
        self.assertIsNone(engine.layer(FilterWorker(),self.image,self.p,'nrgf',calculate=False))

    def test_cached_multiply_layer_and_independent_fnrgf_order(self):
        engine=LayerEngine();worker=FilterWorker()
        p=dict(self.p,layered_model=True)
        with patch('core.nrgf.nrgf_layer',wraps=nrgf_layer) as calculation:
            first=engine.render(worker,self.image,p,{})
            altered=engine.render(worker,self.image,dict(p,nrgf_opacity=80),{})
            engine.render(worker,self.image,dict(p,nrgf_enabled=False),{})
            engine.render(worker,self.image,p,{})
            self.assertEqual(calculation.call_count,1)
            self.assertGreater(np.max(abs(first-altered)),.001)
            layer=engine.layer(worker,self.image,p,'nrgf')
            self.assertEqual(layer['mode'],'Multiply')
            encoded,_=nrgf_layer(self.image,p)
            good=np.isfinite(encoded)
            np.testing.assert_allclose(layer['image'][good],encoded[good].astype(float)*65535,rtol=0,atol=1)
        p.update(fnrgf_enabled=True,fnrgf_str=20,fnrgf_ord=3,fnrgf_seg=16,fnrgf_cut=0,
                 fnrgf_rad=10,fnrgf_rmax=60,fnrgf_nbins=20,fnrgf_mode='continuous')
        self.assertEqual([r[0] for r in requests(p)],['nrgf','fnrgf'])
        np.testing.assert_array_equal(engine.layer(worker,self.image,p,'nrgf')['image'],layer['image'])
        self.assertTrue(np.isfinite(engine.render(worker,self.image,p,{})).all())

    def test_native_width_scaling_and_tiff_jpeg_package_parity(self):
        prepared=prepare_parameters(self.p,(160,192),(80,96),(80,96))
        self.assertEqual(prepared['nrgf_bin_px'],2.)
        self.assertEqual(prepared['nrgf_scale'],.5)
        p=dict(self.p,layered_model=True,valid_mask=np.isfinite(self.image))
        worker=FilterWorker()
        expected=execute_pipeline(worker,self.image,p)
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'nrgf.tif'
            export_images(self.image,p,{},str(output),'source.fits',layer_cache=worker.layer_engine,export_layers=True)
            result=tifffile.imread(output)
            self.assertEqual(result.dtype,np.uint16)
            self.assertEqual(result.shape,self.image.shape)
            np.testing.assert_array_equal(result,np.rint(np.clip(expected,0,1)*65535).astype(np.uint16))
            import cv2
            self.assertEqual(cv2.imread(str(Path(tmp)/'nrgf_preview.jpg'),0).shape,self.image.shape)
            package=Path(tmp)/'nrgf_PS_layers'
            recipe=json.loads((package/'recipe.json').read_text())
            self.assertEqual([r['filter'] for r in recipe['layers']],['linear_reference','base','nrgf'])
            self.assertEqual(recipe['layers'][2]['mode'],'Multiply')
            self.assertEqual(tifffile.imread(package/recipe['layers'][2]['file']).dtype,np.uint16)

    def test_layer_package_uses_the_declared_multiply_equation(self):
        from core.layer_export import export_layer_package, to_u16
        from core.presentation import normalized_base
        p=dict(self.p,nrgf_str=100,nrgf_opacity=39)
        with tempfile.TemporaryDirectory() as tmp:
            package=export_layer_package(FilterWorker(),self.image,p,{},'input.tif',Path(tmp)/'layers')
            recipe=json.loads((package/'recipe.json').read_text())
            row=next(row for row in recipe['layers'] if row['filter']=='nrgf')
            layer=tifffile.imread(package/row['file'])
            base=tifffile.imread(package/next(row['file'] for row in recipe['layers'] if row['filter']=='base'))[...,0].astype(float)/65535
            weight=layer[...,3].astype(float)/65535*(round(.39*255)/255)
            expected=to_u16((base*(1+(layer[...,0].astype(float)/65535-1)*weight)).astype(np.float32))
            np.testing.assert_array_equal(tifffile.imread(package/recipe['combined'])[...,0],expected)


class NRGFGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_order_controls_and_partial_filter_settings_round_trip(self):
        w=EclipseProcessorApp();w.auto_calculate=False
        try:
            w.full_raw_image=w.raw_image=w.preview_image=corona()
            w.txt_x.setText('47');w.txt_y.setText('40');w.txt_r.setText('8')
            layout=w.sec_nrgf.parentWidget().layout()
            self.assertLess(layout.indexOf(w.sec_nrgf),layout.indexOf(w.sec_fnrgf))
            self.assertFalse(w.sec_nrgf.is_filter_active())
            self.assertEqual(w.sl_nrgf_opacity.value(),40)
            self.assertFalse(hasattr(w,'sl_nrgf_str'))
            self.assertEqual(w.sec_nrgf.content_layout.indexOf(w.sl_nrgf_opacity.parameter_row),0)
            old=capture_settings(w)
            old['sections'].pop('sec_nrgf')
            old['controls']={k:v for k,v in old['controls'].items() if '_nrgf_' not in k}
            w.sec_nrgf.chk_active.setChecked(True)
            w.sec_fnrgf.chk_active.setChecked(True)
            w.sl_nrgf_opacity.setValue(61);w.sl_nrgf_bin_px.setValue(35)
            saved=capture_settings(w)
            restore_settings(w,saved)
            self.assertEqual(capture_settings(w),saved)
            p=w.collect_filter_parameters(w.raw_image.shape)
            self.assertTrue(p['nrgf_enabled'] and p['fnrgf_enabled'])
            self.assertEqual(p['nrgf_bin_px'],3.5)
            restore_settings(w,old)
            self.assertFalse(w.sec_nrgf.is_filter_active())
            self.assertEqual(w.sl_nrgf_opacity.value(),40)
            self.assertEqual(w.sl_nrgf_bin_px.value(),20)
            self.assertTrue(w.sl_nrgf_min_count.parameter_row.isHidden())
            w.chk_advanced.setChecked(True)
            self.assertFalse(w.sl_nrgf_min_count.parameter_row.isHidden())
        finally:close_window(w)
