"""Pixel-accurate zoom/pan without native-size scaled pixmap allocation."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import unittest
from unittest.mock import patch
import numpy as np
from PySide6.QtCore import QPoint, QPointF, Qt, QEvent
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest, QSignalSpy
from PySide6.QtWidgets import QApplication
from gui.image_view import ImageView
from gui.app import EclipseProcessorApp
from gui_wait import close_window,wait_for_gui
from core.image_data import resize_observed


class ImageViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.view=ImageView();self.view.resize(162,122)
        self.native=np.indices((400,600)).sum(axis=0).astype(np.uint8)%2*255
        self.preview=np.full((40,60),127,np.uint8)
        self.view.set_images(self.preview,self.native,600,400)
        self.view.show();self.app.processEvents()

    def tearDown(self):self.view.close()

    def test_disk_overlay_hides_circle_and_cross_without_changing_pixels_or_geometry(self):
        v=self.view;v.set_circle_parameters(300,200,12);v.set_zoom(2)
        pixels=v._native_pixels
        with patch('gui.image_view.QPainter') as painter:
            v.grab()
            self.assertEqual(painter.return_value.drawEllipse.call_count,1)
            self.assertEqual(painter.return_value.drawLine.call_count,2)
        v.set_disk_overlay_visible(False)
        with patch('gui.image_view.QPainter') as painter:
            v.grab()
            painter.return_value.drawEllipse.assert_not_called()
            painter.return_value.drawLine.assert_not_called()
        self.assertIs(v._native_pixels,pixels)
        self.assertEqual((v.circle_x,v.circle_y,v.circle_r),(300,200,12))
        v.clear()
        self.assertTrue(v.disk_overlay_visible)

    def test_physical_zoom_and_visible_roi_at_each_device_scale(self):
        v=self.view
        for dpr in (1.,1.5,2.):
            with patch.object(v,'devicePixelRatioF',return_value=dpr):
                for zoom in (1,2):
                    v.set_zoom(zoom)
                    image,target,source=v.visible_image()
                    self.assertIs(image,v._native)
                    self.assertAlmostEqual(v.image_rect().width()*dpr/600,zoom)
                    self.assertLessEqual(source.width(),v.width()*dpr/zoom)
                    self.assertLessEqual(source.height(),v.height()*dpr/zoom)
                    self.assertLessEqual(target.width(),v.width())
                    self.assertIs(v._native_pixels,self.native)

    def test_200_percent_draws_pixel_blocks_without_smoothing(self):
        v=self.view;v.set_zoom(2)
        image=v.grab().toImage()
        rect=v.image_rect();dpr=v.devicePixelRatioF()
        for y in range(6,18):
            for x in range(6,28):
                sx=int(((x+.5)/dpr-rect.x())*600/rect.width())
                sy=int(((y+.5)/dpr-rect.y())*400/rect.height())
                self.assertEqual(image.pixelColor(x,y).red(),int(self.native[sy,sx]))

    def test_click_and_circle_use_native_coordinates_after_pan(self):
        v=self.view;v.set_zoom(2);v._pan(QPointF(-20,-10))
        rect=v.image_rect();pos=QPoint(50,40)
        expected=(int((pos.x()-rect.x())*600/rect.width()),int((pos.y()-rect.y())*400/rect.height()))
        center=QSignalSpy(v.circle_center_requested)
        QTest.mouseClick(v,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.ControlModifier,pos)
        self.assertEqual(list(center.at(0)),list(expected))
        v.set_circle_parameters(*expected,12)
        with patch('gui.image_view.QPainter') as painter:
            v.grab()
        point,rx,ry=painter.return_value.drawEllipse.call_args.args
        self.assertAlmostEqual(point.x(),rect.x()+(expected[0]+.5)*rect.width()/600)
        self.assertAlmostEqual(point.y(),rect.y()+(expected[1]+.5)*rect.height()/400)
        self.assertAlmostEqual(rx,12*rect.width()/600)

    def test_drag_pans_without_clicking_or_changing_the_source(self):
        v=self.view;v.set_zoom(1)
        center=QSignalSpy(v.circle_center_requested)
        before=v.image_rect()
        QTest.mousePress(v,Qt.MouseButton.LeftButton,pos=QPoint(70,60))
        event=QMouseEvent(QEvent.Type.MouseMove,QPointF(100,80),QPointF(v.mapToGlobal(QPoint(100,80))),
                          Qt.MouseButton.NoButton,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier)
        self.app.sendEvent(v,event)
        QTest.mouseRelease(v,Qt.MouseButton.LeftButton,pos=QPoint(100,80))
        self.assertGreater(v.image_rect().x(),before.x())
        self.assertEqual(center.count(),0)
        self.assertIs(v._native_pixels,self.native)

    def test_pan_clamps_edges_and_fit_preserves_center(self):
        v=self.view;v.set_zoom(1)
        v._pan(QPointF(1e6,1e6));rect=v.image_rect()
        self.assertAlmostEqual(rect.left(),1,delta=1/v.devicePixelRatioF())
        self.assertAlmostEqual(rect.top(),1,delta=1/v.devicePixelRatioF())
        center=QPointF(v._center)
        v.set_zoom(None);v.set_zoom(1)
        self.assertEqual(v._center,center)
        v._pan(QPointF(-1e6,-1e6));rect=v.image_rect()
        self.assertAlmostEqual(rect.right(),v.width()-1,delta=1/v.devicePixelRatioF())
        self.assertAlmostEqual(rect.bottom(),v.height()-1,delta=1/v.devicePixelRatioF())

    def test_background_editing_uses_native_coordinates(self):
        v=self.view;v.set_zoom(None)
        v.set_background_samples([(450,300)],120,True)
        rect=v.image_rect()
        pos=QPoint(round(rect.x()+450.5*rect.width()/600),round(rect.y()+300.5*rect.height()/400))
        added=QSignalSpy(v.background_point_added);removed=QSignalSpy(v.background_point_removed)
        QTest.mouseClick(v,Qt.MouseButton.LeftButton,pos=pos)
        QTest.mouseClick(v,Qt.MouseButton.RightButton,pos=pos)
        self.assertEqual(added.count(),1);self.assertEqual(removed.count(),1)
        self.assertLess(abs(added.at(0)[0]-450),4)

    def test_missing_native_data_shows_fit_until_ready(self):
        v=self.view;v.set_images(self.preview,None,600,400)
        fit=v.image_rect();v.set_zoom(2)
        self.assertEqual(v.image_rect(),fit)
        self.assertIs(v.visible_image()[0],v._preview)
        self.assertIsNone(v._native)

    def test_sample_editor_does_not_pan_and_letterbox_clicks_are_ignored(self):
        v=self.view;v.set_zoom(1);v.set_background_samples([],120,True)
        before=v.image_rect();clicks=QSignalSpy(v.background_point_added)
        QTest.mouseClick(v,Qt.MouseButton.LeftButton,pos=QPoint(60,40))
        self.assertEqual(clicks.count(),1);self.assertEqual(v.image_rect(),before)
        v.set_zoom(None);v.resize(162,300);self.app.processEvents()
        QTest.mouseClick(v,Qt.MouseButton.LeftButton,pos=QPoint(10,5))
        self.assertEqual(clicks.count(),1)


class DisplayPixelsTests(unittest.TestCase):
    def test_tiled_conversion_matches_existing_pixel_values_without_mutating_input(self):
        from gui.background_tasks import display_pixels
        for dtype in (np.float32,np.float64):
            for shape in ((270,120),(270,120,3)):
                image=np.random.default_rng(42).uniform(-.1,1.1,shape).astype(dtype)
                original=image.copy()
                np.testing.assert_array_equal(display_pixels(image),np.clip(image*255.,0,255).astype(np.uint8))
                np.testing.assert_array_equal(image,original)


class NativeZoomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        w=self.w=EclipseProcessorApp();w.auto_calculate=False
        w.btn_psb_preview.setChecked(False)
        w.request_processing_signal.disconnect()
        self.requests=[]
        w.request_processing_signal.connect(lambda image,p:self.requests.append((image,p)))
        y,x=np.indices((192,256))
        w.full_raw_image=(.1+x/300+y/400+.03*(x%2)).astype(np.float32)
        w.raw_image=w.preview_image=resize_observed(w.full_raw_image,(64,48))
        w.processed_image=w.raw_image
        w.txt_x.setText('128');w.txt_y.setText('96');w.txt_r.setText('20')
        w.recalculation_timer.stop();w.presentation_timer.stop()
        w.render_matrix_to_screen();wait_for_gui(w)

    def tearDown(self):close_window(self.w)

    def complete_native(self):
        w=self.w
        source,params=self.requests[-1]
        result=w.filter_worker._process_pipeline(source,params)
        w.on_processing_finished(result);wait_for_gui(w)

    def test_native_request_then_zoom_and_pan_reuse_the_rendered_bytes(self):
        w=self.w;original=w.full_raw_image.copy()
        w.set_preview_zoom(1)
        self.assertEqual(len(self.requests),1)
        self.assertIs(self.requests[-1][0],w.full_raw_image)
        self.assertFalse(w.chk_verify_preview.isChecked())
        w.set_preview_zoom(2)
        self.assertEqual(len(self.requests),1)
        self.assertFalse(w.filter_worker._cancel_event.is_set())
        self.complete_native()
        pixels=w.image_label._native_pixels
        self.assertEqual(pixels.shape,w.full_raw_image.shape)
        self.assertEqual(pixels.dtype,np.uint8)
        self.assertEqual(w.last_preview_presentation.shape,w.raw_image.shape)
        with patch('gui.app.render_snapshot',side_effect=AssertionError('Recomposed on zoom')):
            w.set_preview_zoom(1);w.set_preview_zoom(2);w.image_label._pan(QPointF(20,10))
            w.set_preview_zoom(None);w.set_preview_zoom(1)
        self.assertEqual(len(self.requests),1)
        self.assertIs(w.image_label._native_pixels,pixels)
        np.testing.assert_array_equal(w.full_raw_image,original)

    def test_fit_returns_to_fast_calculation_after_native_inspection(self):
        w=self.w;w.set_preview_zoom(1);self.complete_native()
        w.set_preview_zoom(None)
        w.txt_x.setText('127');w.dispatch_pipeline_request()
        self.assertIs(self.requests[-1][0],w.raw_image)
        self.assertFalse(w._running_full_job)

    def test_native_cache_without_pixels_recomposes_without_recalculating_filters(self):
        w=self.w
        params=w.collect_filter_parameters(w.full_raw_image.shape)
        from core.result_cache import parameter_signature
        w._full_cache=(w.full_raw_image,parameter_signature(params),w.full_raw_image.copy(),w._preview_revision)
        w.set_preview_zoom(1);wait_for_gui(w)
        self.assertEqual(self.requests,[])
        self.assertIsNotNone(w.image_label._native_pixels)

    def test_zoom_keeps_original_comparison_enabled(self):
        w=self.w
        w.btn_compare.setChecked(True);w.toggle_compare_mode(True);wait_for_gui(w)
        w.set_preview_zoom(1)
        self.assertTrue(w.btn_compare.isChecked());self.assertTrue(w.show_original_mode)
        self.complete_native()
        self.assertTrue(w.btn_compare.isChecked());self.assertTrue(w.show_original_mode)
        self.assertIsNotNone(w.image_label._native_pixels)

    def test_native_rgb_pixels_match_full_presentation_before_reduction(self):
        from core.layer_engine import colour_display,engine_for
        from core.layer_export import to_u16
        from core.presentation import normalized_base, composition_settings
        from core.colour import set_luminosity
        from core.presentation_edges import finish_presentation
        w=self.w;source=w.full_raw_image
        w.full_source_rgb=source[...,None]*np.array([.7,1.,.4],np.float32)
        w.chk_calibrate_colour.setChecked(False);w.on_input_state_changed();wait_for_gui(w)
        w.set_preview_zoom(1);self.complete_native()
        display=w.collect_display_parameters()
        base=(to_u16(normalized_base(source,composition_settings(display))).astype(float)/65535).astype(np.float32)
        expected=set_luminosity(colour_display(w.full_source_rgb,source,composition_settings(display)),base)
        expected=finish_presentation(expected,engine_for(w.filter_worker).edge_alpha(source,w.collect_filter_parameters(source.shape)))
        np.testing.assert_array_equal(w.image_label._native_pixels,np.clip(expected*255,0,255).astype(np.uint8))
        self.assertEqual(w.last_preview_presentation.shape,(*w.raw_image.shape,3))

    def test_native_presentation_is_queued_behind_an_obsolete_fast_render(self):
        from threading import Event
        import time
        from gui.background_tasks import render_snapshot
        w=self.w;entered,release=Event(),Event();jobs=[]
        def blocked(job):
            jobs.append(job['native'])
            if not job['native']:
                entered.set()
                if not release.wait(3):raise AssertionError('Renderer was not released')
            return render_snapshot(job)
        try:
            with patch('gui.app.render_snapshot',side_effect=blocked):
                w.render_matrix_to_screen()
                deadline=time.monotonic()+2
                while not entered.is_set() and time.monotonic()<deadline:QTest.qWait(10)
                self.assertTrue(entered.is_set())
                w.set_preview_zoom(1)
                source,params=self.requests[-1]
                result=w.filter_worker._process_pipeline(source,params)
                w.on_processing_finished(result)
                w.set_preview_zoom(2)
                release.set();wait_for_gui(w)
            self.assertEqual(jobs,[False,True])
            self.assertEqual(len(self.requests),1)
            self.assertIsNotNone(w.image_label._native_pixels)
        finally:
            release.set()

    def test_loaded_tiff_keeps_sky_brightness_between_fast_and_native(self):
        import tempfile
        from pathlib import Path
        import tifffile
        w=self.w
        image=np.full((1600,2000),100,np.float32)
        image[600:900,800:1100]=5000
        image[10,10]=0
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'sky.tif';tifffile.imwrite(path,image)
            with patch('gui.app.QFileDialog.getOpenFileName',return_value=(str(path),'')):
                w.load_image_action();wait_for_gui(w)
        w.render_matrix_to_screen();wait_for_gui(w)
        self.assertEqual(w.collect_display_parameters()['normalization_range'],[0.,5000.])
        before=w.last_preview_presentation[-100:,-100:].copy()
        self.assertGreater(np.nanmin(w.raw_image),0)
        w.chk_verify_preview.setChecked(True);w.dispatch_pipeline_request();self.complete_native()
        np.testing.assert_allclose(w.last_preview_presentation[-100:,-100:],before,atol=1e-6)
        w.chk_verify_preview.setChecked(False);w.dispatch_pipeline_request()
        source,params=self.requests[-1]
        w.on_processing_finished(w.filter_worker._process_pipeline(source,params));wait_for_gui(w)
        np.testing.assert_allclose(w.last_preview_presentation[-100:,-100:],before,atol=1e-6)


    def test_manual_recipe_change_cannot_publish_old_native_result(self):
        w=self.w;w.set_preview_zoom(1)
        w.txt_x.setText('126')
        w.on_processing_finished(np.ones_like(w.full_raw_image))
        wait_for_gui(w)
        self.assertIsNone(w._full_cache)
        self.assertIsNone(w.image_label._native_pixels)
