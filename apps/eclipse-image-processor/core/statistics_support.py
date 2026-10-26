"""Statistical support is separate from observed-data validity and output alpha."""
import numpy as np


def statistics_support(image, parameters, valid=None):
    a = np.asarray(image)
    observed = np.isfinite(a) if valid is None else np.asarray(valid, dtype=bool) & np.isfinite(a)
    support = observed.copy()
    p = parameters
    if p.get('statistics_exclude_lunar', False) or p.get('statistics_exclude_bright', False):
        y, x = np.ogrid[:a.shape[0], :a.shape[1]]
        r = np.hypot(x-p['sx'], y-p['sy'])
        if p.get('statistics_exclude_lunar', False):
            support &= r > p['sr']+p.get('statistics_guard_px', 0.)
        if p.get('statistics_exclude_bright', False):
            percentile = p.get('statistics_bright_percentile', 99.5)
            if not 90 <= percentile <= 100:
                raise ValueError('Bright-limb percentile must lie in [90, 100]')
            annulus = observed & (r > p['sr']) & (r < p.get('statistics_limb_outer', 1.5)*p['sr'])
            if annulus.any():
                limit = np.percentile(a[annulus], percentile)
                support &= ~(annulus & (a > limit))
    if not support.any():
        raise ValueError('Statistics exclusions leave no observed support; reduce radius or guard')
    return support


class StatisticsWorker:
    """Exclude samples from statistics and retain each stage's input there."""
    def __init__(self, worker, support):
        from .masked_filters import MaskedWorker
        self.worker = MaskedWorker(worker, support)
        self.support = support

    def __getattr__(self, name):
        method = getattr(self.worker, name)
        def run(image, *args, **kwargs):
            transport = np.where(self.support, image, 0)
            result = method(transport, *args, **kwargs)
            return np.where(self.support, result, image).astype(np.float32)
        return run


def radial_confidence(image, radii, bin_px, valid, threshold):
    """Approximate contrast/noise blend weight; never modifies the ranking core."""
    from scipy.ndimage import gaussian_filter1d
    a = np.asarray(image, dtype=float)
    observed = np.isfinite(a) if valid is None else np.asarray(valid, bool) & np.isfinite(a)
    pairs = observed[:, 1:] & observed[:, :-1]
    diff = np.diff(a, axis=1)[pairs]
    noise = 1.4826*np.median(np.abs(diff-np.median(diff)))/np.sqrt(2) if diff.size else 0.
    if noise == 0:
        return observed.astype(float)
    bins = (radii/bin_px).astype(int)
    counts = np.bincount(bins[observed])
    means = np.bincount(bins[observed], weights=a[observed])/np.maximum(counts, 1)
    variance = np.bincount(bins[observed], weights=(a[observed]-means[bins[observed]])**2)/np.maximum(counts, 1)
    weight = np.clip(np.sqrt(np.maximum(variance-noise**2, 0))/(threshold*noise), 0, 1)
    support = gaussian_filter1d((counts > 0).astype(float), 2.)
    weight = np.divide(gaussian_filter1d(weight*(counts > 0), 2.), support, out=np.zeros_like(weight), where=support > 0)
    return np.where(observed, weight[np.minimum(bins, len(weight)-1)], 0)
