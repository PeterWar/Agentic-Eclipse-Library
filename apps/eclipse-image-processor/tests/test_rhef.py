import unittest
import numpy as np
from core.filters import rhef_normalize, FilterWorker


class RHEFTests(unittest.TestCase):
    def test_corona_changes_without_changing_lunar_disk(self):
        y, x = np.indices((128, 128))
        r = np.hypot(x - 64, y - 64)
        angle = np.arctan2(y - 64, x - 64)
        corona = 10000 * np.exp(-r / 30) * (1 + .2 * np.cos(4 * angle))
        image = np.where(r < 20, 100., corona).astype(np.float32)
        actual = FilterWorker().run_rhef_native(image, 50, 10, 35, 64, 64, 20)
        np.testing.assert_array_equal(actual[r < 20], image[r < 20])
        outer = r > 40
        self.assertGreater(np.mean(np.abs(actual[outer] - image[outer])), 100)

    def test_average_ties(self):
        a=np.array([[1,1,3,4.]])
        out=rhef_normalize(a,np.ones_like(a),[0,2],upsilon=None)
        np.testing.assert_allclose(out,[[.375,.375,.75,1]])

    def test_constant_ring_remains_constant(self):
        a=np.full((5,5),7.)
        out=rhef_normalize(a,np.ones_like(a),[0,2])
        self.assertEqual(np.unique(out).size,1)

    def test_upsilon_uses_ring_mean(self):
        a=np.arange(1,6,dtype=float)[None,:]
        out=rhef_normalize(a,np.ones_like(a),[0,2],upsilon=(.35,.6))
        ranks=np.arange(1,6)/5
        expected=np.where(ranks<ranks.mean(),.5*(2*ranks)**.35,1-.5*(2-2*ranks)**.6)
        np.testing.assert_allclose(out[0],expected)

    def test_application_radius_before_ranking(self):
        a=np.array([[1.,2.,3.,4.]])
        radii=np.array([[.8,1.,1.1,1.2]])
        out=rhef_normalize(a,radii,[0,2],application_radius=1,upsilon=None)
        self.assertTrue(np.isnan(out[0,0]))
        np.testing.assert_allclose(out[0,1:],[1/3,2/3,1])

    def test_vignette_after_ranking(self):
        a=np.array([[1.,2.,3.]])
        out=rhef_normalize(a,np.array([[1.,1.2,1.4]]),[0,2],upsilon=None,vignette=1.3)
        np.testing.assert_allclose(out[0,:2],[1/3,2/3])
        self.assertTrue(np.isnan(out[0,2]))

    def test_mask_nan_and_ring_independence(self):
        a=np.array([[1.,np.nan,3.,10.,20.]])
        r=np.array([[1.,1.,1.,2.,2.]])
        out=rhef_normalize(a,r,[0,1.5,3],upsilon=None)
        np.testing.assert_allclose(out,[[.5,np.nan,1,.5,1]],equal_nan=True)

    def test_small_upsilon_not_clamped(self):
        a=np.arange(25,dtype=np.float32).reshape(5,5)
        worker=FilterWorker()
        low=worker.run_rhef_native(a,100,0,1,2,2,1)
        high=worker.run_rhef_native(a,100,0,5,2,2,1)
        self.assertGreater(np.max(np.abs(low-high)),.001)
        with self.assertRaises(ValueError):
            worker.run_rhef_native(a,100,0,35,2,2,1,bin_px=0)


if __name__=='__main__':
    unittest.main()
