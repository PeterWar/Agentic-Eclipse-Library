"""Visual controls must never alter numerical TIFF or editable PSB presentation."""
import json
from pathlib import Path
import tempfile
import unittest
import cv2
import numpy as np
import tifffile
from core.export import export_images
from core.filters import FilterWorker
from core.layer_package import export_layered_package
from core.layer_engine import engine_for
from core.layer_export import to_u16
from core.presentation import psb_presentation_settings


class ExportDisplaySeparationTests(unittest.TestCase):
    def setUp(self):
        self.source=np.linspace(0,1000,48*64,dtype=np.float32).reshape(48,64)
        self.source[0,0]=np.nan
        self.params=dict(layered_model=True)
        self.displays=[dict(mode='asinh',strength=0.,normalization_range=[0.,1000.]),
                       dict(mode='log',strength=30.,normalization_range=[0.,1000.])]

    def test_retired_visual_keys_do_not_affect_tiff_or_jpeg_including_cached_composition(self):
        worker=FilterWorker()
        composition=engine_for(worker).render(worker,self.source,self.params,self.displays[0])
        with tempfile.TemporaryDirectory() as tmp:
            tiffs=[];jpegs=[]
            for i,display in enumerate(self.displays):
                target=Path(tmp)/f'out{i}.tif'
                export_images(self.source,self.params,display,str(target),'input.tif',
                              processed=composition if i else None)
                tiffs.append(tifffile.imread(target))
                jpegs.append(cv2.imread(str(target.with_name(f'out{i}_preview.jpg')),0))
                metadata=json.loads(tifffile.TiffFile(target).pages[0].description)
                self.assertFalse(metadata['visual_stretch_applied'])
            np.testing.assert_array_equal(tiffs[0],tiffs[1])
            from core.presentation_edges import finish_presentation
            expected=finish_presentation(composition,engine_for(worker).edge_alpha(self.source,self.params))
            np.testing.assert_array_equal(tiffs[0],to_u16(expected))
            np.testing.assert_array_equal(jpegs[0],jpegs[1])
            self.assertEqual(tiffs[0][0,0],0)

    def test_package_base_and_hidden_reference_are_independent_of_gui(self):
        rgb=self.source[...,None]*np.array([.7,1.,1.2])
        with tempfile.TemporaryDirectory() as tmp:
            recipes=[];bases=[]
            for i,display in enumerate(self.displays):
                root=export_layered_package(FilterWorker(),self.source,self.params,display,
                                           'input.tif',Path(tmp)/str(i),rgb=rgb)
                recipe=json.loads((root/'recipe.json').read_text());recipes.append(recipe)
                reference=next(row for row in recipe['layers'] if row['filter']=='linear_reference')
                self.assertFalse(reference['visible'])
                scale=reference['reference_scale']
                actual=tifffile.imread(root/reference['file'])
                np.testing.assert_array_equal(actual[...,:3],to_u16(np.nan_to_num(rgb/scale,nan=0.)))
                self.assertEqual(actual[0,0,3],0)
                base=next(row for row in recipe['layers'] if row['filter']=='base')
                bases.append(tifffile.imread(root/base['file']))
            np.testing.assert_array_equal(bases[0],bases[1])
            self.assertEqual(recipes[0]['display'],recipes[1]['display'])
            self.assertEqual(recipes[0]['display']['mode'],'ael_presentation')

    def test_rgb_calibration_and_active_filter_export_ignore_all_visual_curves(self):
        params=dict(self.params,sx=32,sy=24,sr=2,mgn_enabled=True,mgn_str=100,mgn_gam=320,
                    mgn_opacity=20,mgn_sigmas=(1.,2.),mgn_weights=(1.,1.))
        rgb=self.source[...,None]*np.array([.6,1.,.8])
        worker=FilterWorker()
        composition=engine_for(worker).render(worker,self.source,params,self.displays[0])
        with tempfile.TemporaryDirectory() as tmp:
            outputs=[]
            for i,display in enumerate([*self.displays,dict(mode='ghs',strength=2.)]):
                target=Path(tmp)/f'rgb{i}.tif'
                export_images(self.source,params,display,str(target),'input.tif',
                              source_rgb=rgb,calibrate_colour=True,white=2000.,
                              processed=composition,layer_cache=engine_for(worker))
                outputs.append(tifffile.imread(target))
            for actual in outputs[1:]:
                np.testing.assert_array_equal(actual,outputs[0])
            self.assertEqual(outputs[0].shape,(*self.source.shape,3))

    def test_psb_reference_scale_excludes_explicitly_masked_outliers(self):
        source=self.source.copy();source[0,1]=1.e9
        valid=np.isfinite(source);valid[0,1]=False
        self.assertAlmostEqual(psb_presentation_settings(source,valid)['scale'],
                               np.percentile(source[valid & (source > 0)],99.5))
        with tempfile.TemporaryDirectory() as tmp:
            root=export_layered_package(FilterWorker(),source,dict(self.params,valid_mask=valid),
                                       self.displays[1],'input.tif',Path(tmp)/'layers')
            recipe=json.loads((root/'recipe.json').read_text())
            reference=next(row for row in recipe['layers'] if row['filter']=='linear_reference')
            self.assertAlmostEqual(reference['reference_scale'],1000./.98)
            self.assertTrue((tifffile.imread(root/reference['file'])[0,1]==0).all())
