"""Native PSB correction layers, masks, colour profile and export-only settings."""
from gui_wait import close_window

import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import tifffile
from PIL import ImageCms
from psd_tools import PSDImage
from psd_tools.constants import Resource,ChannelID,BlendMode
from PySide6.QtWidgets import QApplication
from core.color_correction import correction_masks,verify_color_correction
from core.psb_export import export_psb_package,verify_psb_package
from core.export import export_images
from gui.app import EclipseProcessorApp
from gui.project_settings import capture_settings,restore_settings


class ColorCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.package=self.root/'layers';self.package.mkdir()
        self.shape=(48,64);y,x=np.indices(self.shape)
        self.rgb=np.stack([x*900,y*1200,(x+y)*450],axis=-1).astype(np.uint16)
        self.valid=np.ones(self.shape,bool);self.valid[:3,:5]=False
        self.geometry=dict(sx=32.,sy=24.,sr=7.)
        tifffile.imwrite(self.package/'base.tif',np.dstack([self.rgb,self.valid.astype(np.uint16)*65535]),
                         photometric='rgb',extrasamples=['unassalpha'])
        tifffile.imwrite(self.package/'merged.tif',self.rgb,photometric='rgb')
        tifffile.imwrite(self.package/'VALID.tif',self.valid.astype(np.uint8)*255)
        recipe=dict(shape=list(self.shape),parameters=self.geometry,combined='merged.tif',
                    layers=[dict(file='base.tif',name='BASE',mode='Normal',opacity_255=255,visible=True)])
        (self.package/'recipe.json').write_text(json.dumps(recipe))

    def tearDown(self):self.tmp.cleanup()

    def test_psb_group_native_adjustments_masks_and_srgb_are_verified(self):
        out=self.root/'correction.psb'
        report=export_psb_package(self.package,out,color_correction=True)
        self.assertFalse(report['exact_composite'])
        self.assertTrue(report['exact_base_reference'])
        self.assertTrue(report['color_correction']['native_adjustments'])
        doc=PSDImage.open(out)
        self.assertEqual(len(doc),3)
        self.assertEqual((doc.depth,doc._record.header.version),(16,2))
        group=doc[-1]
        self.assertEqual(group.name,'Color Correction')
        self.assertEqual((group.blend_mode,group.opacity),(BlendMode.NORMAL,128))
        self.assertEqual([l.kind for l in group],['pixel','gradientmap','colorbalance','huesaturation'])
        profile=doc._record.image_resources.get_data(Resource.ICC_PROFILE)
        self.assertIn('sRGB',ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(profile))))
        self.assertFalse(doc.has_preview())
        verify_color_correction(doc,self.rgb,self.valid,self.geometry)
        for layer in list(group)[1:]:
            self.assertIn(ChannelID.USER_LAYER_MASK,[ci.id for ci in layer._record.channel_info])
        # A correct round trip must also fail when the requested native settings are corrupted.
        group[2]._data.midtones=(0,0,0)
        with out.open('wb') as stream:doc._record.write(stream)
        with self.assertRaisesRegex(ValueError,'balance mismatch'):
            verify_psb_package(out,self.package,color_correction=True)

    def test_masks_exclude_missing_and_disk_and_remain_soft(self):
        y,x=np.indices(self.shape);radius=np.hypot(x-32,y-24);disk=radius<=7
        field=np.clip(500+60000*np.exp(-(radius-7)/7),0,65535).astype(np.uint16)
        rgb=np.repeat(field[...,None],3,axis=-1)
        (corona,sky),info=correction_masks(rgb,self.valid,self.geometry)
        for mask in (corona,sky):
            self.assertEqual(mask.dtype,np.uint16)
            self.assertFalse(mask[disk | ~self.valid].any())
            self.assertTrue(((mask>0)&(mask<65535)).any())
        self.assertTrue(info['review_required'])
        self.assertFalse(np.array_equal(sky,65535-corona))
        with self.assertRaises(ValueError):correction_masks(self.rgb,self.valid,dict(sx=0,sy=0,sr=0))

    def test_disabled_option_keeps_original_psb_and_atomic_failure(self):
        plain=self.root/'plain.psb';export_psb_package(self.package,plain)
        doc=PSDImage.open(plain)
        self.assertEqual(len(doc),2)
        self.assertNotIn(Resource.ICC_PROFILE,doc._record.image_resources)
        out=self.root/'bad.psb'
        with patch('core.color_correction.verify_color_correction',side_effect=ValueError('invalid correction')):
            with self.assertRaisesRegex(ValueError,'invalid correction'):
                export_psb_package(self.package,out,color_correction=True)
        self.assertFalse(out.exists())
        self.assertFalse(list(self.root.glob('*.psb.tmp')))

    def test_final_tiff_jpeg_are_identical_with_correction_on_and_off(self):
        source=np.linspace(1,10,np.prod(self.shape),dtype=np.float32).reshape(self.shape)
        with patch('core.export.export_layer_package',return_value=self.package):
            for name,enabled in (('plain',False),('corrected',True)):
                export_images(source,self.geometry,{},str(self.root/(name+'.tif')),'source.fits',
                              export_layers=True,layers_format='psb',color_correction=enabled)
        np.testing.assert_array_equal(tifffile.imread(self.root/'plain.tif'),tifffile.imread(self.root/'corrected.tif'))
        self.assertEqual((self.root/'plain_preview.jpg').read_bytes(),(self.root/'corrected_preview.jpg').read_bytes())
        self.assertEqual(PSDImage.open(self.root/'corrected_PS_layers.psb')[-1].name,'Color Correction')
        with self.assertRaisesRegex(ValueError,'requires Photoshop PSB'):
            export_images(source,self.geometry,{},str(self.root/'unsupported.tif'),'source.fits',
                          export_layers=True,layers_format='tiff',color_correction=True)
        self.assertFalse((self.root/'unsupported.tif').exists())


class ColorCorrectionGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_checkbox_is_psb_only_and_current_json_requires_its_state(self):
        w=EclipseProcessorApp();w.auto_calculate=False
        w.full_raw_image=w.raw_image=w.preview_image=np.ones((64,80),np.float32)
        w.txt_x.setText('40');w.txt_y.setText('32');w.txt_r.setText('8')
        try:
            before=w.collect_filter_parameters(w.raw_image.shape)
            self.assertFalse(w.chk_color_correction.isChecked())
            self.assertTrue(w.chk_color_correction.isEnabled())
            with patch.object(w,'dispatch_pipeline_request_if_auto') as pipeline,patch.object(w,'render_matrix_to_screen') as preview:
                w.chk_color_correction.setChecked(True)
                pipeline.assert_not_called();preview.assert_not_called()
            from core.result_cache import parameter_signature
            self.assertEqual(parameter_signature(before),parameter_signature(w.collect_filter_parameters(w.raw_image.shape)))
            w.combo_layers_format.setCurrentIndex(1)
            self.assertFalse(w.chk_color_correction.isEnabled())
            w.combo_layers_format.setCurrentIndex(0)
            self.assertTrue(w.chk_color_correction.isEnabled())
            w.chk_export_layers.setChecked(False)
            self.assertFalse(w.chk_color_correction.isEnabled())
            w.chk_export_layers.setChecked(True)
            settings=capture_settings(w)
            restore_settings(w,settings)
            self.assertEqual(capture_settings(w),settings)
            old=deepcopy(settings);old['controls'].pop('chk_color_correction')
            with self.assertRaises(ValueError):restore_settings(w,old)
            self.assertEqual(capture_settings(w),settings)
        finally:close_window(w)
