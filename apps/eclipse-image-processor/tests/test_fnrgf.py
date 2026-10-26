import unittest
import numpy as np
from core.filters import fnrgf_normalize, FilterWorker


class FNRGFTests(unittest.TestCase):
    def test_width_floor_bounds_high_order_amplification_in_input_units(self):
        n = 64
        phi = (np.arange(n) + .5) * 2 * np.pi / n
        widths = np.random.default_rng(7).lognormal(-2, 2, n)
        image = np.stack([100 - widths, 100 + widths])
        angles = np.broadcast_to(phi, image.shape)
        radii = np.full(image.shape, 1.5)
        for order in (20, 21, 22):
            kwargs = dict(order=order, segments=n, width_floor_fraction=.05)
            out = fnrgf_normalize(image, radii, angles, [1, 2], **kwargs)
            self.assertTrue(np.isfinite(out).all())
            # Fourier mean is constant here: attenuation[1] = 1 - 1/order.
            numerator = image - 100 * (1 - 1 / order)
            bound = np.abs(numerator) / (.05 * np.median(widths))
            self.assertTrue(np.all(np.abs(out) <= bound + 1e-8))
            scaled = fnrgf_normalize(image * 65535, radii, angles, [1, 2], **kwargs)
            np.testing.assert_allclose(scaled, out, rtol=1e-9, atol=1e-8)

    def test_direct_reference_and_angular_width(self):
        # One complete annulus, with controlled mean and width in each sector.
        n, order = 16, 3
        phi = (np.arange(n)+.5)*2*np.pi/n
        mean = 10+2*np.cos(phi)
        width = 2+.8*np.sin(phi)
        image = np.stack([mean-width, mean+width])
        angles = np.broadcast_to(phi, image.shape)
        radii = np.full(image.shape, 1.5)
        attenuation = np.linspace(1, 0, order+1)
        profiles = []
        for values in (mean, width):
            profile = np.full(n, values.mean()*attenuation[1])
            for k in range(1, order+1):
                ak = 2/n*np.sum(values*np.cos(k*phi))*attenuation[k]
                bk = 2/n*np.sum(values*np.sin(k*phi))*attenuation[k]
                profile += ak*np.cos(k*phi)+bk*np.sin(k*phi)
            profiles.append(profile)
        expected = (image-profiles[0])/profiles[1]
        actual = fnrgf_normalize(image, radii, angles, [1,2], order=order, segments=n)
        np.testing.assert_allclose(actual, expected, atol=1e-12)
        self.assertGreater(np.ptp(profiles[1]), .5)

    def test_cutoff_all_coefficients(self):
        a = np.arange(32).reshape(2,16)
        theta = np.broadcast_to((np.arange(16)+.5)*2*np.pi/16, a.shape)
        out = fnrgf_normalize(a, np.full(a.shape,1.5), theta, [1,2], order=3, segments=16, cutoff=4)
        np.testing.assert_allclose(out, a)

    def test_domain_and_local_limb_protection(self):
        yy,xx = np.indices((101,101))
        r = np.hypot(xx-50,yy-50)/20
        a = (100+xx+yy*.3).astype(np.float32)
        worker = FilterWorker()
        args = (a,100,3,16,0,10,20,4,50,50,20)
        out = worker.run_fnrgf_native(*args)
        masked = worker.run_fnrgf_native(*args,apply_mask=100)
        outside = (r <= 1) | (r >= 2)
        np.testing.assert_array_equal(out[outside],a[outside])
        np.testing.assert_array_equal(masked[r>=1.05],out[r>=1.05])
        self.assertTrue(np.isfinite(out).all())

    def test_core_fill_and_invalid_sampling(self):
        a=np.ones((3,3))
        out=fnrgf_normalize(a,a,np.zeros_like(a),[1,2],order=1,segments=4)
        self.assertTrue(np.isnan(out).all())
        with self.assertRaises(ValueError):
            fnrgf_normalize(a,a,a,[1,2],order=3,segments=4)


if __name__ == '__main__':
    unittest.main()
