"""Exercise the real export action without a visible Qt window or file dialog."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
import tifffile

from core.filters import FilterWorker
from core.pipeline import prepare_parameters
from core.export import export_images


class FilterExportTests(unittest.TestCase):
    def test_cached_composition_must_match_source_canvas(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination=Path(tmp)/'final.tif'
            with self.assertRaisesRegex(ValueError,'source canvas'):
                export_images(np.ones((8,10)),{},{},str(destination),'source.tif',processed=np.ones((4,5)))
            self.assertEqual(list(Path(tmp).iterdir()),[])

    def test_final_images_are_written_only_after_layers_succeed(self):
        image=np.ones((8,10),np.float32)
        with tempfile.TemporaryDirectory() as tmp:
            destination=Path(tmp)/'final.tif'
            jpeg=Path(tmp)/'final_preview.jpg'
            def layers(*args, **kwargs):
                self.assertFalse(destination.exists())
                self.assertFalse(jpeg.exists())
                return Path(tmp)/'layers'
            updates=[]
            with patch('core.export.export_layer_package',side_effect=layers) as package:
                export_images(image,{}, {},str(destination),'source.fits',
                              export_layers=True,processed=image,progress=lambda value,label:updates.append((value,label)))
            self.assertEqual([label for _,label in updates],[
                'Preparing export','Calculating filters','Writing layer package',
                'Composing final image','Writing TIFF','Writing JPEG','Export complete'])
            self.assertEqual(updates[0][0],0)
            self.assertEqual(updates[-1][0],100)
            self.assertEqual([value for value,_ in updates],sorted(value for value,_ in updates))
            package.assert_called_once()
            self.assertTrue(destination.exists())
            self.assertTrue(jpeg.exists())
            failed=Path(tmp)/'failed.tif'
            with patch('core.export.export_layer_package',side_effect=ValueError('layer failure')):
                with self.assertRaisesRegex(ValueError,'layer failure'):
                    export_images(image,{}, {},str(failed),'source.fits',
                                  export_layers=True,processed=image)
            self.assertFalse(failed.exists())
            self.assertFalse((Path(tmp)/'failed_preview.jpg').exists())

    def test_scaled_kernels_bins_and_real_16bit_tiff_and_jpeg(self):
        from core.layer_engine import engine_for
        from core.layer_export import to_u16
        import json
        image=np.random.default_rng(81).uniform(100,5000,(128,160)).astype(np.float32)
        original=image.copy()
        recipe=dict(layered_model=True,sx=80.,sy=64.,sr=16.,
                    fnrgf_enabled=True,fnrgf_str=100,fnrgf_opacity=20,fnrgf_ord=6,fnrgf_seg=16,
                    fnrgf_cut=0,fnrgf_rad=10,fnrgf_rmax=61,fnrgf_nbins=20,
                    mgn_enabled=True,mgn_str=100,mgn_opacity=20,mgn_gam=32,mgn_k=70,mgn_h=70,mgn_trunc=3,
                    rhef_enabled=True,rhef_str=100,rhef_opacity=20,rhef_rad=10,rhef_upsilon=35,
                    rhef_mode='continuous',rhef_bin_px=1.)
        parameters=prepare_parameters(recipe,image.shape,(64,80),image.shape)
        display={}
        methods={name:getattr(FilterWorker,name) for name in ('run_mgn_native','run_fnrgf_native')}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'export.tiff'
            with patch.object(FilterWorker,'run_mgn_native',autospec=True,side_effect=methods['run_mgn_native']) as mgn, \
                 patch.object(FilterWorker,'run_fnrgf_native',autospec=True,side_effect=methods['run_fnrgf_native']) as fnrgf:
                export_images(image,parameters,display,str(path),'original.tif',scale_factor=2.,export_layers=True)
            self.assertEqual(mgn.call_args.kwargs['sigmas'],(1.25,2.5,5,10,20,40))
            self.assertEqual(fnrgf.call_args.args[8],40)
            exported=tifffile.imread(path)
            self.assertEqual(exported.dtype,np.uint16)
            self.assertEqual(exported.shape,image.shape)
            self.assertEqual(cv2.imread(str(path.with_name('export_preview.jpg')),0).shape,image.shape)
            worker=FilterWorker()
            expected=engine_for(worker).render(worker,image,parameters,display)
            np.testing.assert_array_equal(exported,to_u16(expected))
            package=path.with_name('export_PS_layers')
            manifest=json.loads((package/'recipe.json').read_text())
            self.assertEqual([r['filter'] for r in manifest['layers']],['linear_reference','base','fnrgf','rhef','mgn'])
            self.assertTrue((package/'Load_layers_Photoshop.jsx').is_file())
            np.testing.assert_array_equal(image,original)
