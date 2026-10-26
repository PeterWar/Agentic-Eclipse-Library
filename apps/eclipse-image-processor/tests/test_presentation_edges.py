"""Black export storage and non-destructive observed-side lunar antialiasing."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import tifffile
from psd_tools import PSDImage
from core.presentation_edges import black_edge_alpha, finish_presentation
from core.image_data import zero_missing
from core.layer_export import export_layer_package,to_u16
from core.layer_engine import LayerEngine
from core.filters import FilterWorker
from core.export import export_images


class PresentationEdgeTests(unittest.TestCase):
    def setUp(self):
        self.shape=(80,96);y,x=np.indices(self.shape)
        self.r=np.hypot(x-48.3,y-40.7)
        self.valid=self.r>17.2
        self.source=np.where(self.valid,1+self.r/100,np.nan).astype(np.float32)
        self.params=dict(sx=48.3,sy=40.7,sr=17.2,valid_mask=self.valid,layered_model=True)

    def test_soft_band_keeps_missing_black_far_corona_exact_and_source_untouched(self):
        before=self.source.copy()
        alpha=black_edge_alpha(self.source)
        result=finish_presentation(np.ones(self.shape),alpha)
        self.assertTrue(np.all(result[~self.valid]==0))
        self.assertTrue(np.all(result[self.r>21]==1))
        self.assertTrue(((result>0)&(result<1)).any())
        self.assertGreater(result[self.valid].min(),0)
        self.assertLess(result[self.valid].min(),.2)
        self.assertTrue(np.all((result>=0)&(result<=1)))
        np.testing.assert_array_equal(self.source,before)
        self.assertFalse(alpha.flags.writeable)
        self.assertIsNone(black_edge_alpha(np.ones(self.shape)))

    def test_observed_black_lunar_disk_is_softened_but_other_observed_zeros_are_not(self):
        finite=np.nan_to_num(self.source);finite[0,0]=0
        alpha=black_edge_alpha(finite,geometry=self.params)
        np.testing.assert_array_equal(alpha,black_edge_alpha(self.source))
        self.assertEqual(alpha[0,0],0)
        self.assertTrue(np.isfinite(finite).all())
        mixed=finite.copy();mixed[self.r<15]=np.nan
        np.testing.assert_array_equal(black_edge_alpha(mixed,geometry=self.params),alpha)

    def test_cache_avoids_recomputing_distance_on_opacity_and_display_changes(self):
        engine=LayerEngine()
        with patch('core.presentation_edges.black_edge_alpha',wraps=black_edge_alpha) as distance:
            first=engine.edge_alpha(self.source,self.params)
            self.assertIs(engine.edge_alpha(self.source,dict(self.params,mgn_opacity=90)),first)
            self.assertEqual(distance.call_count,1)
            engine.edge_alpha(self.source,dict(self.params,nrgf_scale=.5))
            self.assertEqual(distance.call_count,2)
        with self.assertRaises(ValueError):black_edge_alpha(self.source,scale=0)
        with self.assertRaises(ValueError):black_edge_alpha(self.source,valid=np.ones((2,2),bool))

    def test_nonfinite_export_samples_are_explicit_zero_without_warnings_or_mutation(self):
        values=np.array([np.nan,np.inf,-np.inf,-2.,.5,1.])
        with np.errstate(invalid='raise',over='raise'):
            np.testing.assert_array_equal(zero_missing(values),[0,0,0,-2,.5,1])
            np.testing.assert_array_equal(to_u16(values),[0,0,0,0,32768,65535])
        self.assertTrue(np.isnan(values[0]))
        self.assertTrue(np.isinf(values[1:3]).all())

    def test_layer_package_psb_and_final_tiff_share_the_soft_edge(self):
        worker=FilterWorker()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);package=root/'layers'
            export_layer_package(worker,self.source,self.params,{},'source.fits',package)
            recipe=json.loads((package/'recipe.json').read_text())
            self.assertEqual(recipe['layers'][-1]['filter'],'edge_antialias')
            edge=tifffile.imread(package/recipe['layers'][-1]['file'])
            np.testing.assert_array_equal(edge[...,3],worker.layer_engine.edge_alpha(self.source,self.params))
            np.testing.assert_array_equal(tifffile.imread(package/'SOURCE_float32.tif'),np.nan_to_num(self.source))
            np.testing.assert_array_equal(tifffile.imread(package/'VALID.tif')>0,self.valid)
            expected=tifffile.imread(package/recipe['combined'])
            self.assertTrue(np.all(expected[~self.valid]==0))
            out=root/'final.tif'
            export_images(self.source,self.params,{},str(out),'source.fits',export_layers=True,
                          layers_format='psb',layer_cache=worker.layer_engine,export_linear=True,input_state='linear')
            final=tifffile.imread(out)
            self.assertEqual(final.shape,self.shape)
            neutral=worker.layer_engine.render(worker,self.source,self.params,{})
            np.testing.assert_array_equal(final,to_u16(finish_presentation(neutral,worker.layer_engine.edge_alpha(self.source,self.params))))
            doc=PSDImage.open(root/'final_PS_layers.psb')
            self.assertEqual(doc[-1].name,'Edge Antialias')
            for plane in doc._record.image_data.get_data(doc._record.header):
                np.testing.assert_array_equal(np.frombuffer(plane,dtype='>u2').reshape(self.shape),expected[...,0])
            for path in (root/'final_sources').glob('*.tif'):
                self.assertTrue(np.isfinite(tifffile.imread(path)).all())
            self.assertTrue(np.isnan(self.source[~self.valid]).all())

    def test_sequential_final_tiff_is_opaque_zero_not_nan_or_transparency(self):
        p=dict(self.params,layered_model=False)
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'final.tif'
            export_images(self.source,p,{},str(out),'source.fits')
            final=tifffile.imread(out)
            self.assertEqual(final.shape,self.shape)
            self.assertTrue(np.all(final[~self.valid]==0))
            self.assertTrue(np.isfinite(final).all())
