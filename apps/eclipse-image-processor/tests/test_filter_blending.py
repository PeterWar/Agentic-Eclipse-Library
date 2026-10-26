import unittest
import numpy as np
from core.filters import FilterWorker


class FilterBlendTests(unittest.TestCase):
    def test_strength_is_linear_and_independent_of_input_units(self):
        a=np.random.default_rng(13).uniform(1000,50000,(64,64)).astype(np.float32)
        worker=FilterWorker()
        for run in (lambda x,s:worker.run_mgn_native(x,s,32,70,70,3),
                    lambda x,s:worker.run_rhef_native(x,s,10,35,32,32,12),
                    lambda x,s:worker.run_wow_native(x,s,3)):
            full=run(a,100)
            for strength in (1,10,50,95,99):
                out=run(a,strength)
                np.testing.assert_allclose(out,a+(full-a)*strength/100,rtol=2e-6,atol=.01)
                self.assertGreater(np.max(np.abs(out-a)),.1)
            scaled=run(a/65535,10)*65535
            np.testing.assert_allclose(scaled,run(a,10),rtol=2e-5,atol=.05)
            np.testing.assert_array_equal(run(a,0),a)
