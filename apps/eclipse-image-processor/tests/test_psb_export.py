"""Exact PSB16 package roundtrip, native-compatible block order and atomic failure."""
import json
from pathlib import Path
import tempfile
from threading import Event
import unittest
from unittest.mock import patch

import numpy as np
from psd_tools import PSDImage
from psd_tools.constants import Resource,Tag
import tifffile

from core.cancellation import cancellation_scope,ProcessingCancelled
from core.psb_export import export_psb_package,verify_psb_package
from scripts.research.probe_psb_writer import independent_read


class PSBExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.package = self.root/'layers'
        self.package.mkdir()
        self.shape = (9,13)
        y,x = np.indices(self.shape)
        self.rgb = np.stack([1000+x+20*y,10001+3*x+40*y,30000+5*x+3*y],axis=-1).astype(np.uint16)
        self.alpha = np.full(self.shape,65535,np.uint16)
        self.alpha[2:4,3:6] = 0
        self.alpha[4:6,3:6] = 32768
        rows=[]
        for i,mode in enumerate(('Normal','Overlay','Color','Linear Light','Normal')):
            name=f'{i} · Sol — 精度'
            file=f'layer_{i}.tif'
            tifffile.imwrite(self.package/file,np.dstack([self.rgb+i,self.alpha]),
                             photometric='rgb',extrasamples=['unassalpha'])
            rows.append(dict(file=file,name=name,mode=mode,opacity_255=255-21*i,visible=i!=4))
        tifffile.imwrite(self.package/'combined.tif',np.dstack([self.rgb,self.alpha]),
                         photometric='rgb',extrasamples=['unassalpha'])
        self.recipe=dict(shape=list(self.shape),layers=rows,combined='combined.tif')
        self._save_recipe()

    def tearDown(self):
        self.tmp.cleanup()

    def _save_recipe(self):
        (self.package/'recipe.json').write_text(json.dumps(self.recipe))

    def test_exact_channels_and_metadata_with_independent_reader(self):
        destination=self.root/'test.psb'
        report=export_psb_package(self.package,destination)
        self.assertTrue(report['exact_composite'])
        self.assertFalse(report['merged_transparency'])
        self.assertTrue(report['black_background'])
        data=independent_read(destination)
        for i,record in enumerate(data['records'][1:]):
            np.testing.assert_array_equal(record['rgb16'],self.rgb+i)
            np.testing.assert_array_equal(record['alpha16'],self.alpha)
            self.assertEqual(record['name'],self.recipe['layers'][i]['name'])
        np.testing.assert_array_equal(data['records'][0]['rgb16'],np.zeros_like(self.rgb))
        np.testing.assert_array_equal(data['records'][0]['alpha16'],np.full(self.shape,65535,np.uint16))
        expected=np.rint(self.rgb.astype(float)*self.alpha[...,None]/65535).astype(np.uint16)
        np.testing.assert_array_equal(data['merged'],expected)
        doc=PSDImage.open(destination)
        keys=list(doc._record.layer_and_mask_information.tagged_blocks)
        self.assertNotIn(Tag.SAVING_MERGED_TRANSPARENCY16,keys)
        self.assertEqual(doc._record._get_layer_info().layer_count,6)
        self.assertIn(Resource.XMP_METADATA,doc._record.image_resources)
        self.assertEqual(doc._record.header.channels,3)

    def test_rejects_hidden_black_background(self):
        destination=self.root/'test.psb'
        export_psb_package(self.package,destination)
        doc=PSDImage.open(destination)
        doc[0].visible=False
        with destination.open('wb') as stream:
            doc._record.write(stream)
        with self.assertRaisesRegex(ValueError,'background metadata'):
            verify_psb_package(destination,self.package)

    def test_opaque_composite_and_sequential_output_integration(self):
        tifffile.imwrite(self.package/'combined.tif',self.rgb,photometric='rgb')
        destination=self.root/'opaque.psb'
        report=export_psb_package(self.package,destination)
        self.assertFalse(report['merged_transparency'])
        self.assertEqual(PSDImage.open(destination)._record.header.channels,3)
        # Explicit PSB request still produces the regular final TIFF/JPEG separately.
        from core.export import export_images
        source=np.linspace(1,9,9*13).reshape(self.shape).astype(np.float32)
        with patch('core.export.export_layer_package',return_value=self.package):
            export_images(source,{},dict(mode='asinh',strength=10),str(self.root/'final.v1.tif'),
                          'source.fits',export_layers=True,layers_format='psb',processed=source)
        self.assertTrue((self.root/'final.v1.tif').exists())
        self.assertTrue((self.root/'final.v1_preview.jpg').exists())
        self.assertTrue((self.root/'final.v1_PS_layers.psb').exists())
        self.assertFalse((self.root/'final.v1_PS_layers').exists())

    def test_atomic_failure_and_no_overwrite(self):
        destination=self.root/'test.psb'
        with patch('core.psb_export.verify_psb_package',side_effect=ValueError('bad PSB')):
            with self.assertRaises(ValueError):export_psb_package(self.package,destination)
        self.assertFalse(destination.exists())
        self.assertFalse(list(self.root.glob('.*.psb.tmp')))
        destination.write_bytes(b'preserve existing work')
        with self.assertRaises(FileExistsError):export_psb_package(self.package,destination)
        self.assertEqual(destination.read_bytes(),b'preserve existing work')

    def test_rejects_changed_pixels_and_unsafe_or_invalid_inputs(self):
        destination=self.root/'test.psb'
        export_psb_package(self.package,destination)
        tifffile.imwrite(self.package/'layer_0.tif',np.dstack([self.rgb+1,self.alpha]),
                         photometric='rgb',extrasamples=['unassalpha'])
        with self.assertRaisesRegex(ValueError,'pixel mismatch'):
            verify_psb_package(destination,self.package)
        self.recipe['layers'][0]['file']='../outside.tif'
        self._save_recipe()
        with self.assertRaises(ValueError):export_psb_package(self.package,self.root/'bad.psb')
        self.assertFalse((self.root/'bad.psb').exists())

    def test_cancelled_export_never_publishes_a_file(self):
        event=Event()
        with self.assertRaises(ProcessingCancelled):
            with cancellation_scope(event):
                event.set()
                export_psb_package(self.package,self.root/'cancelled.psb')
        self.assertFalse((self.root/'cancelled.psb').exists())
