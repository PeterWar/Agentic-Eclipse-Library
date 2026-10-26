"""Independent inputs, Photoshop blends, cache invalidation and export parity."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy as np
import tifffile
from psd_tools import PSDImage

from core.layer_engine import LayerEngine, blend
from core.layer_export import export_layer_package, neutral_layer, to_u16, overlay
from core.filters import FilterWorker
from core.pipeline import execute_pipeline
from core.presentation import normalized_base, composition_settings
from core.export import export_images


class IndependentLayerTests(unittest.TestCase):
    def setUp(self):
        self.source=np.linspace(1,10,192,dtype=np.float32).reshape(12,16)
        self.p=dict(layered_model=True,sx=8.,sy=6.,sr=2.,
                    mgn_enabled=True,mgn_str=100,mgn_gam=32,mgn_opacity=20,
                    wow_enabled=True,wow_str=100,wow_scales=1,wow_opacity=30,
                    statistics_exclude_lunar=False,statistics_exclude_bright=False)
        self.display=dict(mode='asinh',strength=5,blend=1.)
        self.worker=Mock()
        self.worker.run_mgn_native.side_effect=lambda a,*args,**kw:a**2
        self.worker.run_wow_native.side_effect=lambda a,*args,**kw:np.sqrt(a)
        self.engine=LayerEngine()
        self.quiet=redirect_stdout(io.StringIO());self.quiet.__enter__()

    def tearDown(self):
        self.quiet.__exit__(None,None,None)

    def test_each_filter_receives_original_and_blends_once_above_linear_base(self):
        before=self.source.copy()
        actual=self.engine.render(self.worker,self.source,self.p,self.display)
        for method in (self.worker.run_mgn_native,self.worker.run_wow_native):
            np.testing.assert_array_equal(method.call_args.args[0],self.source)
        expected=to_u16(normalized_base(self.source,composition_settings(self.display))).astype(float)/65535
        yy,xx=np.indices(self.source.shape)
        domain=(xx-8)**2+(yy-6)**2 > 4
        for image,amount in ((self.source**2,51/255),(np.sqrt(self.source),76/255)):
            encoded,_=neutral_layer(image,domain)
            expected=overlay(expected,to_u16(encoded)/65535.,domain.astype(float),amount)
        np.testing.assert_array_equal(actual,expected.astype(np.float32))
        np.testing.assert_array_equal(self.source,before)

    def test_opacity_toggle_display_and_unrelated_parameter_edits_reuse_filters(self):
        first=self.engine.render(self.worker,self.source,self.p,self.display)
        self.p['mgn_opacity']=70
        changed=self.engine.render(self.worker,self.source,self.p,self.display)
        self.assertGreater(np.max(abs(first-changed)),.001)
        self.p['mgn_enabled']=False
        self.engine.render(self.worker,self.source,self.p,self.display)
        self.p['mgn_enabled']=True
        self.engine.render(self.worker,self.source,self.p,dict(self.display,strength=15))
        self.p['fnrgf_ord']=23  # an inactive/unrelated filter's control
        self.engine.render(self.worker,self.source,self.p,self.display)
        self.assertEqual(self.worker.run_mgn_native.call_count,1)
        self.assertEqual(self.worker.run_wow_native.call_count,1)
        self.p['mgn_gam']=45
        self.engine.render(self.worker,self.source,self.p,self.display)
        self.assertEqual(self.worker.run_mgn_native.call_count,2)
        self.assertEqual(self.worker.run_wow_native.call_count,1)
        self.p['mgn_str']=50
        self.engine.render(self.worker,self.source,self.p,self.display)
        self.assertEqual(self.worker.run_mgn_native.call_count,3)
        self.assertEqual(self.worker.run_wow_native.call_count,1)

    def test_log_distinguishes_calculation_from_cached_fusion_without_duplicate_lines(self):
        first=io.StringIO()
        with redirect_stdout(first):
            self.engine.render(self.worker,self.source,self.p,self.display)
        text=first.getvalue()
        self.assertEqual(text.count('[FILTER: MGN] Calculated'),1)
        self.assertEqual(text.count('[FILTER: WOW] Calculated'),1)
        self.assertNotIn('Execution start',text)
        self.assertNotIn('CACHE',text)
        cached=io.StringIO()
        with redirect_stdout(cached):
            self.engine.render(self.worker,self.source,self.p,self.display)
        self.assertEqual(cached.getvalue().strip(),
                         '[FUSION] Reusing calculated layers; no filters recalculated')

    def test_geometry_masks_new_source_and_resolution_invalidate(self):
        self.engine.render(self.worker,self.source,self.p,self.display)
        self.p['sx']=9.
        self.engine.render(self.worker,self.source,self.p,self.display)
        self.assertEqual(self.worker.run_mgn_native.call_count,2)
        self.engine.render(self.worker,self.source.copy(),self.p,self.display)
        self.assertEqual(self.worker.run_mgn_native.call_count,3)
        self.engine.render(self.worker,self.source[::2,::2].copy(),self.p,self.display)
        self.assertEqual(len(self.engine.sources),2)
        self.assertEqual(self.worker.run_mgn_native.call_count,4)

    def test_validity_mask_change_invalidates_cached_result(self):
        with patch.object(self.engine,'_calculate',wraps=self.engine._calculate) as calculation:
            self.engine.render(self.worker,self.source,self.p,self.display)
            self.p['valid_mask']=np.ones(self.source.shape,bool)
            self.engine.render(self.worker,self.source,self.p,self.display)
            before=calculation.call_count
            self.p['valid_mask'][0,0]=False
            self.engine.layer(self.worker,self.source,self.p,'mgn')
            self.assertEqual(calculation.call_count,before+1)

    def test_zero_opacity_is_base_and_cached_only_never_computes(self):
        self.assertIsNone(self.engine.render(self.worker,self.source,self.p,self.display,calculate=False))
        self.worker.run_mgn_native.assert_not_called()
        p=dict(self.p,mgn_opacity=0,wow_opacity=0)
        actual=self.engine.render(self.worker,self.source,p,self.display)
        np.testing.assert_array_equal(actual,(to_u16(normalized_base(self.source,composition_settings(self.display)))/65535.).astype(np.float32))
        self.assertEqual(self.worker.run_mgn_native.call_count,1)
        self.engine.render(self.worker,self.source,dict(p,mgn_opacity=60),self.display)
        self.assertEqual(self.worker.run_mgn_native.call_count,1)
        with self.assertRaises(ValueError):
            self.engine.render(self.worker,self.source,dict(self.p,mgn_opacity=101),self.display)

    def test_multiply_and_linear_light_match_scalar_equations(self):
        base=np.array([[.2,.8]])
        layer=np.array([[.9,.1]])
        alpha=np.array([[1.,.5]])
        amount=.3
        np.testing.assert_allclose(blend(base,layer,alpha,'Multiply',amount),
                                  base*(1-alpha*amount)+base*layer*alpha*amount)
        np.testing.assert_allclose(blend(base,layer,alpha,'Linear Light',amount),
            base*(1-alpha*amount)+np.clip(base+2*layer-1,0,1)*alpha*amount)

    def test_multiple_achf_variants_are_independent_and_keep_their_caches(self):
        p=dict(layered_model=True,sx=8,sy=6,sr=2,achf_enabled=True,
               achf_variants={v:dict(enabled=True,opacity=20,strength=80)
                              for v in ('ael_iso_01','ael_iso_04','ael_angular_4')})
        p['achf_variants']['adaptive']=dict(enabled=False)
        def ael(a,*args,**kwargs):
            variant=args[5]
            return np.full(a.shape,{'ael_iso_01':.7,'ael_iso_04':.6,'ael_angular_4':.4}[variant]),{}
        with patch('core.ael_achf.ael_achf_layer',side_effect=ael) as operator:
            self.engine.render(self.worker,self.source,p,self.display)
            self.assertEqual(operator.call_count,3)
            p['achf_variants']['ael_iso_01']['enabled']=False
            self.engine.render(self.worker,self.source,p,self.display)
            p['achf_variants']['ael_iso_01'].update(enabled=True,opacity=60)
            p['achf_variant']='ael_angular_4'  # selected editing panel only
            self.engine.render(self.worker,self.source,p,self.display)
            self.assertEqual(operator.call_count,3)
            p['achf_variants']['ael_iso_04']['outer_sigma']=2
            self.engine.render(self.worker,self.source,p,self.display)
            self.assertEqual(operator.call_count,4)

    def test_tiff_uses_neutral_composition_psb_uses_its_presentation_and_cached_layers(self):
        source=self.source.copy();source[0,:3]=np.nan
        p=dict(self.p,wow_enabled=False)
        worker=FilterWorker()
        worker.layer_engine=LayerEngine()
        # Use the real MGN and masked-support path.
        display=dict(self.display,blend=.7)
        actual=execute_pipeline(worker,source,dict(p,layer_display=display))
        from core.presentation_edges import finish_presentation
        actual=finish_presentation(actual,worker.layer_engine.edge_alpha(source,p))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);package=root/'layers'
            export_layer_package(worker,source,p,display,'source.fits',package)
            recipe=json.loads((package/'recipe.json').read_text())
            combined=tifffile.imread(package/recipe['combined'])
            presentation=worker.layer_engine.render(worker,source,p,recipe['display'])
            presentation=finish_presentation(presentation,worker.layer_engine.edge_alpha(source,p))
            np.testing.assert_array_equal(combined[...,0],to_u16(presentation))
            copied=source.copy()
            snapshot=worker.layer_engine.snapshot(source,copied)
            with patch.object(LayerEngine,'_calculate',side_effect=AssertionError('cache missed')):
                export_images(copied,p,display,str(root/'final.tif'),'source.fits',
                              export_layers=True,layers_format='psb',layer_cache=snapshot)
            np.testing.assert_array_equal(tifffile.imread(root/'final.tif'),to_u16(actual))
            doc=PSDImage.open(root/'final_PS_layers.psb')
            self.assertEqual(doc[1].name,'Linear reference / receipt scale')
            self.assertFalse(doc[1].visible)
            self.assertEqual(doc[2].name,'Display base')
            planes=doc._record.image_data.get_data(doc._record.header)
            np.testing.assert_array_equal(np.frombuffer(planes[0],dtype='>u2').reshape(source.shape),to_u16(presentation))
            np.testing.assert_array_equal(source,np.where(np.isfinite(source),self.source,np.nan))

    def test_fnrgf_uses_multiply_and_reveal_zero_preserves_base(self):
        p=dict(sx=8,sy=6,sr=2,fnrgf_enabled=True,fnrgf_str=100,fnrgf_opacity=35,
               fnrgf_ord=2,fnrgf_seg=8,fnrgf_cut=0,fnrgf_rad=10)
        self.worker.run_fnrgf_native.side_effect=lambda a,*args,**kw:a*a
        output=self.engine.render(self.worker,self.source,p,self.display)
        layer=self.engine.layer(self.worker,self.source,p,'fnrgf')
        self.assertEqual(layer['mode'],'Multiply')
        base=to_u16(normalized_base(self.source,composition_settings(self.display)))/65535.
        self.assertTrue((output<=base+1e-7).all())
        zero=self.engine.render(self.worker,self.source,p,dict(self.display,blend=0))
        np.testing.assert_array_equal(zero,base.astype(np.float32))


if __name__=='__main__':
    unittest.main()
