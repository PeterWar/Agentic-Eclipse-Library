import unittest
import numpy as np
from core.tangential import tangential_detail
from core.filters import FilterWorker


class TangentialTests(unittest.TestCase):
    def test_constant_and_angular_harmonic_transfer(self):
        y,x=np.indices((101,101)); r=np.hypot(x-50,y-50); theta=np.arctan2(y-50,x-50)
        a=100+5*np.cos(12*theta)
        out=tangential_detail(a,50,50,10,arc_sigma_deg=5,fade_px=0)
        expected=a+5*(1-np.exp(-.5*(12*np.deg2rad(5))**2))*np.cos(12*theta)
        use=(r>25)&(r<40)
        np.testing.assert_allclose(out[use],expected[use],atol=.12)
        np.testing.assert_allclose(tangential_detail(np.full(a.shape,7.),50,50,10),7,atol=1e-6)

    def test_rotation_periodicity_missing_support_and_input_preservation(self):
        rng=np.random.default_rng(9); a=rng.uniform(5,10,(81,81)); original=a.copy()
        valid=np.ones_like(a,bool);valid[:15,:20]=False
        first=tangential_detail(a,40,40,10,valid=valid)
        altered=a.copy();altered[~valid]=1e30
        second=tangential_detail(altered,40,40,10,valid=valid)
        np.testing.assert_array_equal(first[valid],second[valid])
        np.testing.assert_array_equal(second[~valid],altered.astype(np.float32)[~valid])
        rot=tangential_detail(np.rot90(a),40,40,10,valid=np.rot90(valid))
        np.testing.assert_allclose(rot,np.rot90(first),rtol=1e-6,atol=1e-6)
        np.testing.assert_array_equal(a,original)

    def test_strength_gain_zero_and_domains(self):
        a=np.random.default_rng(2).uniform(1,10,(64,80)).astype(np.float32); w=FilterWorker()
        full=w.run_tangential(a,100,40,32,8,outer_radius=3,fade_px=2)
        mix=w.run_tangential(a,37,40,32,8,outer_radius=3,fade_px=2)
        np.testing.assert_allclose(mix,.63*a+.37*full,atol=1e-6)
        np.testing.assert_array_equal(w.run_tangential(a,0,40,32,8),a)
        np.testing.assert_array_equal(w.run_tangential(a,100,40,32,8,gain=0),a)
        y,x=np.indices(a.shape);r=np.hypot(x-40,y-32)
        np.testing.assert_array_equal(full[(r<=8)|(r>=24)],a[(r<=8)|(r>=24)])

    def test_radial_null_and_tile_boundary(self):
        y,x=np.indices((301,301));r=np.hypot(x-150,y-150);a=10+.01*r
        out=tangential_detail(a,150,150,10,arc_sigma_deg=5,fade_px=0)
        use=(r>20)&(r<145)
        self.assertLess(np.max(np.abs((out-a)[use])),.0002)

    def test_invalid_parameters(self):
        invalid=np.ones((16,16));invalid[0,0]=np.nan
        with self.assertRaises(ValueError): FilterWorker().run_tangential(invalid,100,8,8,2)
        for extra in (dict(arc_sigma_deg=0),dict(gain=-1),dict(outer_radius=.5),dict(valid=np.ones((2,2)))):
            with self.assertRaises(ValueError): tangential_detail(np.ones((16,16)),8,8,2,**extra)
