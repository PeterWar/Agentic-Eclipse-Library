"""Experimental local continuous background estimators, not a production filter.

Native Cartesian samples; compact C2 Wendland weights. No annulus bins,
pixel inpainting, radial output subtraction, or fitted external reference.
"""
from functools import lru_cache
import numpy as np
from scipy.signal import fftconvolve


@lru_cache(maxsize=12)
def kernel(radius):
    h = int(radius)
    y, x = np.mgrid[-h:h+1, -h:h+1].astype(float) / h
    d = np.hypot(x, y)
    w = np.maximum(1-d, 0)**4 * (1+4*d)
    w /= w.sum()
    return w, x, y


def conv(a, k):
    # Correlation convention: sample at query + offset; zero weight outside data.
    return fftconvolve(np.asarray(a, float), k[::-1, ::-1], mode='same')


def smooth(a, mask, radius):
    return weighted_smooth(a,np.asarray(mask,float),radius)


def weighted_smooth(a, weight, radius):
    k, _, _ = kernel(radius)
    den = conv(weight, k)
    return np.divide(conv(np.where(weight>0, a, 0.)*weight, k), den,
                     out=np.zeros_like(a, dtype=float), where=den > 1e-12)


class LocalModel:
    def __init__(self, mask, radius, kind='quadratic', log_radius=None, certainty=None):
        self.mask = np.asarray(mask, bool)
        self.radius = int(radius)
        self.kind = kind
        self.weight = self.mask.astype(float)
        if certainty is not None:
            certainty=np.asarray(certainty,float)
            assert np.isfinite(certainty[self.mask]).all() and np.all(certainty[self.mask]>0) and np.all(certainty[self.mask]<=1)
            self.weight*=np.where(self.mask,certainty,0.)
        k, x, y = kernel(radius)
        self.k = k
        self.mass = conv(self.weight, k)
        self.valid = self.mask & (self.mass > 1e-8)
        if kind == 'mean':
            return
        if kind == 'lograd':
            assert log_radius is not None
            self.q = np.asarray(log_radius, float)
            self.qbar = weighted_smooth(self.q, self.weight, radius)
            self.vq = weighted_smooth(self.q**2, self.weight, radius) - self.qbar**2
            self.valid &= self.vq > 1e-12
            return
        assert kind == 'quadratic'
        self.basis = [np.ones_like(x), x, y, x*x, x*y, y*y]
        # Complete interior has a single exact polynomial equivalent kernel.
        mr2 = np.sum(k*(x*x+y*y))
        mr4 = np.sum(k*(x*x+y*y)**2)
        self.equivalent = k*(mr4-mr2*(x*x+y*y))/(mr4-mr2**2)
        self.partial = self.valid & (self.mass < 1-1e-10)
        ids = np.flatnonzero(self.partial)
        self.partial_ids = ids
        self.coeff = None
        if len(ids):
            mat = np.empty((len(ids), 6, 6), float)
            for i in range(6):
                for j in range(i+1):
                    v = conv(self.weight, k*self.basis[i]*self.basis[j]).ravel()[ids]
                    mat[:, i, j] = v
                    mat[:, j, i] = v
            coeff = np.zeros((len(ids), 6), float)
            for start in range(0, len(ids), 32768):
                stop = min(start+32768, len(ids))
                block = mat[start:stop]
                eig = np.linalg.eigvalsh(block)
                good = eig[:, 0] > eig[:, -1]*1e-10
                self.valid.ravel()[ids[start:stop][~good]] = False
                rhs = np.zeros((good.sum(), 6, 1)); rhs[:, 0] = 1
                coeff[start:stop][good] = np.linalg.solve(block[good], rhs)[..., 0]
            self.coeff = coeff

    def background(self, log_image):
        a = np.asarray(log_image, float)
        if self.kind == 'mean':
            mu = weighted_smooth(a, self.weight, self.radius)
        elif self.kind == 'lograd':
            abar = weighted_smooth(a, self.weight, self.radius)
            cov = weighted_smooth(a*self.q, self.weight, self.radius)-abar*self.qbar
            slope = np.divide(cov, self.vq, out=np.zeros_like(cov), where=self.vq > 1e-12)
            mu = abar+slope*(self.q-self.qbar)
        else:
            clean = np.where(self.mask, a, 0.)*self.weight
            mu = conv(clean, self.equivalent)
            if len(self.partial_ids):
                fit = np.zeros(len(self.partial_ids), float)
                for i in range(6):
                    b = conv(clean, self.k*self.basis[i]).ravel()[self.partial_ids]
                    fit += self.coeff[:, i]*b
                mu.ravel()[self.partial_ids] = fit
        mu[~self.valid] = np.nan
        return mu

    def apply(self, log_image, adaptive=False, floor=.002):
        mu = self.background(log_image)
        d = np.asarray(log_image)-mu
        if adaptive:
            # Explicit experimental regularizer, not a measured camera-noise model.
            variance = smooth(d*d, self.valid, self.radius)
            scale = np.sqrt(np.maximum(variance, 0.)+floor**2)
            return d/scale, mu, scale
        return d, mu, np.ones_like(d)


def robust_refit(log_image, initial_model, threshold=.002):
    """One smooth certainty refit, not per-query IRLS nor output denoising.

    Certainty is pseudo-Huber weight of the pilot residual. Raw observed
    samples remain in D. The dependency radius is twice the initial radius.
    All weights are strictly positive; the data footprint stays unchanged.
    """
    first=initial_model.apply(log_image)[0]
    certainty=1/np.sqrt(1+(np.nan_to_num(first)/threshold)**2)
    q=getattr(initial_model,'q',None)
    model=LocalModel(initial_model.mask,initial_model.radius,initial_model.kind,q,certainty)
    result=model.apply(log_image)[0]
    return result,model,certainty


def nrgf(image, mask, radius, interpolate=True, phase=0.):
    ri = np.floor(radius-phase).astype(int)
    shift = min(int(ri.min()), 0); ri -= shift
    ids = ri[mask]; n = int(ri.max())+1
    count = np.bincount(ids, minlength=n)
    a = image[mask]
    mu = np.divide(np.bincount(ids, weights=a, minlength=n), count,
                   out=np.zeros(n), where=count > 0)
    var = np.divide(np.bincount(ids, weights=a*a, minlength=n), count,
                   out=np.zeros(n), where=count > 0)-mu*mu
    sd = np.sqrt(np.maximum(var, 0.))
    if interpolate:
        nodes = np.arange(n)+phase+shift+.5; good = count > 0
        m = np.interp(radius, nodes[good], mu[good])
        s = np.interp(radius, nodes[good], sd[good])
    else:
        m = mu[ri]; s = sd[ri]
    out = np.divide(image-m, s, out=np.zeros_like(image), where=s > 1e-15)
    out[~mask] = np.nan
    return out
