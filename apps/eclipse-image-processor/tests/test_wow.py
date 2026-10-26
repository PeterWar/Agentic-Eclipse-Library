import unittest
import numpy as np
from watroo import utils
from core.filters import FilterWorker, blend_filter_result


class WOWTests(unittest.TestCase):
    def setUp(self):
        self.a=np.random.default_rng(3).uniform(1,20,(64,64))
        self.worker=FilterWorker()

    def test_matches_backend(self):
        for bilateral in (None,1):
            for levels in ([],[3,2,1]):
                expected,_=utils.wow(self.a.copy(),n_scales=3,denoise_coefficients=levels,bilateral=bilateral)
                actual=self.worker.run_wow_native(self.a,100,3,denoise_coefficients=levels,bilateral=bilateral)
                np.testing.assert_array_equal(actual,blend_filter_result(self.a,expected,100))

    def test_bypass_constant_and_scale_cap(self):
        np.testing.assert_array_equal(self.worker.run_wow_native(self.a,0),self.a)
        np.testing.assert_array_equal(self.worker.run_wow_native(np.ones((64,64)),100),1)
        np.testing.assert_array_equal(self.worker.run_wow_native(self.a,100,99),self.worker.run_wow_native(self.a,100,0))

    def test_noise_map_and_no_mutation(self):
        original=self.a.copy(); noise=np.full(self.a.shape,.3)
        expected,_=utils.wow(self.a.copy(),n_scales=3,noise=noise,denoise_coefficients=[3,2,1])
        actual=self.worker.run_wow_native(self.a,100,3,noise=noise,denoise_coefficients=[3,2,1])
        np.testing.assert_array_equal(actual,blend_filter_result(self.a,expected,100))
        np.testing.assert_array_equal(self.a,original)

    def test_pipeline_reports_error_then_recovers(self):
        failed=[]; finished=[]
        self.worker.failed.connect(failed.append); self.worker.finished.connect(finished.append)
        self.worker.process_pipeline(self.a,dict(sx=32,sy=32,sr=8,wow_enabled=True,wow_str=100,wow_scales=-1))
        self.assertEqual(len(failed),1)
        self.worker.process_pipeline(self.a,dict(sx=32,sy=32,sr=8,wow_enabled=True,wow_str=100,wow_scales=3))
        self.assertEqual(len(finished),1)


if __name__=='__main__': unittest.main()
