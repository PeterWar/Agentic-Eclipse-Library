import unittest
import numpy as np
from scipy.ndimage import gaussian_filter
from core.filters import mgn_normalize, FilterWorker, blend_filter_result


def reference_mgn(source, scales, k=.7, gamma=3.2, h=.7, weights=None, truncate=3):
    data=source.copy()
    data[data<=0]=1e-15
    data=data.astype(np.float32)
    image=np.zeros_like(data)
    conv=np.zeros_like(data)
    sd=np.zeros_like(data)
    for scale, weight in zip(scales, np.ones(len(scales)) if weights is None else weights):
        gaussian_filter(data,scale,truncate=truncate,mode='nearest',output=conv)
        conv=data-conv
        gaussian_filter(conv**2,scale,truncate=truncate,mode='nearest',output=sd)
        np.sqrt(sd,out=sd)
        sd=np.where(sd==0,1.,sd)
        conv/=sd
        conv*=k
        np.arctan(conv,out=conv)
        conv*=weight
        image+=conv
    image/=len(scales)
    global_image=data-data.min()
    if data.max()-data.min()!=0:
        global_image/=data.max()-data.min()
    global_image**=1/gamma
    global_image*=h
    image*=1-h
    image+=global_image
    return image


class MGNTests(unittest.TestCase):
    def test_official_operations(self):
        a=np.random.default_rng(5).normal(10,4,(43,37))
        a[0,0]=-5; a[1,1]=0
        for truncate in [1,2,3,6]:
            for weights in [None,(.5,1,1.3)]:
                scales=(1.25,2.5,5)
                actual=mgn_normalize(a,sigma=scales,weights=weights,truncate=truncate)
                expected=reference_mgn(a,scales,weights=weights,truncate=truncate)
                np.testing.assert_array_equal(actual,expected)

    def test_defaults_and_slider_units(self):
        a=np.random.default_rng(7).uniform(1,100,(32,32)).astype(np.float32)
        core=mgn_normalize(a)
        ref=reference_mgn(a,(1.25,2.5,5,10,20,40))
        np.testing.assert_array_equal(core,ref)
        np.testing.assert_array_equal(FilterWorker().run_mgn_native(a,100,32,70,70,3),blend_filter_result(a,core,100))

    def test_constant_and_input_preservation(self):
        a=np.full((15,15),7.,dtype=np.float32)
        np.testing.assert_array_equal(mgn_normalize(a),0)
        b=np.array([[-1.,0,2],[3,4,5],[6,7,8]])
        original=b.copy(); errors=np.geterr().copy()
        mgn_normalize(b)
        np.testing.assert_array_equal(b,original)
        self.assertEqual(np.geterr(),errors)

    def test_gamma_only_and_bypass(self):
        a=np.arange(1,26,dtype=np.float32).reshape(5,5)
        np.testing.assert_allclose(mgn_normalize(a,h=1),((a-1)/24)**(1/3.2),rtol=1e-6)
        np.testing.assert_array_equal(FilterWorker().run_mgn_native(a,0,32,70,70,3),a)


if __name__=='__main__':
    unittest.main()
