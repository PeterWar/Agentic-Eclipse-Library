"""Continuous measured radial statistics; never a replacement for missing radiance."""
from __future__ import annotations

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d


def _observed(img, valid, geometry, bin_px, min_count, center='sun'):
    if not np.isfinite(bin_px) or bin_px <= 0:
        raise ValueError('bin_px must be finite and positive')
    if not isinstance(min_count, (int, np.integer)) or min_count < 2:
        raise ValueError('min_count must be an integer >= 2')
    a = np.asarray(img, np.float32)
    if a.ndim != 2 or a.shape != tuple(geometry.shape):
        raise ValueError('image must match the two-dimensional geometry')
    m = np.isfinite(a)
    if valid is not None:
        if np.shape(valid) != a.shape:
            raise ValueError('valid must match image')
        m &= np.asarray(valid, bool)
    r = geometry.radius_map(center, np.float32)
    return a, m, r


def continuous_nrgf(img, valid, geometry, *, center='sun', bin_px=1., robust=True,
                    min_count=50, smooth_bins=0.):
    """Evaluate annular mean/spread at the actual radius, without image smoothing.

    PCHIP interpolates measured statistical nodes, separately across each contiguous
    run of populated annuli. Sparse annuli stay undefined; endpoint statistics are
    held only inside their own observed end annulus. A zero spread is undefined.
    """
    a, m, r = _observed(img, valid, geometry, bin_px, min_count, center)
    if not np.isfinite(smooth_bins) or smooth_bins < 0:
        raise ValueError('smooth_bins must be finite and nonnegative')
    out = np.full(a.shape, np.nan, np.float32)
    if not m.any():
        return out
    bins = np.floor(r / bin_px).astype(np.int64)
    b, v = bins[m], a[m]
    count = np.bincount(b)
    order = np.argsort(b, kind='stable')
    cuts = np.r_[0, np.cumsum(count)]
    values, radii = v[order], r[m][order]
    mu = np.full(len(count), np.nan)
    sd, anchors = mu.copy(), mu.copy()
    for k in np.flatnonzero(count >= min_count):
        seg = slice(cuts[k], cuts[k+1])
        z = values[seg].astype(np.float64)
        mu[k] = np.median(z) if robust else np.mean(z)
        sd[k] = 1.4826*np.median(np.abs(z-mu[k])) if robust else np.std(z)
        anchors[k] = np.median(radii[seg]) if robust else np.mean(radii[seg])
    populated = np.flatnonzero(np.isfinite(mu) & (sd > 0))
    runs = np.split(populated, np.flatnonzero(np.diff(populated) != 1)+1)
    for run in runs:
        if not len(run):
            continue
        means, spreads = mu[run], sd[run]
        if smooth_bins > 0:
            means = gaussian_filter1d(means, smooth_bins, mode='nearest')
            spreads = gaussian_filter1d(spreads, smooth_bins, mode='nearest')
        use = m & (bins >= run[0]) & (bins <= run[-1])
        if len(run) == 1:
            mean, spread = means[0], spreads[0]
        else:
            at = np.clip(r[use], anchors[run[0]], anchors[run[-1]])
            mean = PchipInterpolator(anchors[run], means)(at)
            spread = PchipInterpolator(anchors[run], spreads)(at)
        out[use] = (a[use]-mean)/np.maximum(spread, 1e-12)
    return out


def radial_quantile_rank(img, valid, geometry, sector_deg=None, bin_px=2., *, min_count=12):
    """Interpolate measured log-intensity quantiles in radius/angle, then invert.

    257 quantiles per observed cell; local angular nodes every quarter-sector.
    Only immediate populated neighbours contribute. No image blur, extrapolated
    radiance or output outside valid positive samples. Constant distributions rank
    at one half; ties use the midpoint of the coincident quantile interval.
    """
    a, m, radius = _observed(img, valid, geometry, bin_px, min_count)
    m &= a > 0
    if sector_deg is not None:
        if not np.isfinite(sector_deg) or not 0 < sector_deg <= 360:
            raise ValueError('sector_deg must be in (0,360]')
        if not np.isclose(1440/sector_deg, round(1440/sector_deg)):
            raise ValueError('quarter-sector nodes must divide 360 degrees exactly')
    result = np.full(a.shape, np.nan, np.float32)
    ids = np.flatnonzero(m)
    if not len(ids):
        return result
    r = radius.ravel()[ids]
    v = np.log(a.ravel()[ids])
    theta = geometry.pa_map().ravel()[ids] % 360
    bins = np.floor(r/bin_px).astype(np.int64)
    first = bins.min()
    bins -= first
    nb = int(bins.max())+1
    step = 360 if sector_deg is None else sector_deg/4
    na = int(round(360/step))
    nq = 257
    probabilities = np.linspace(0, 1, nq)
    table = np.full((nb, na, nq), np.nan, np.float32)
    count = np.bincount(bins, minlength=nb)
    order = np.argsort(bins, kind='stable')
    cuts = np.r_[0, np.cumsum(count)]
    for k in np.flatnonzero(count >= min_count):
        ix = order[cuts[k]:cuts[k+1]]
        values, angles = v[ix], theta[ix]
        if sector_deg is None:
            table[k, 0] = np.quantile(values, probabilities)
            continue
        j0 = np.floor(angles/step).astype(int)
        for j in np.unique(np.r_[j0, j0+1] % na):
            sample = values[np.abs((angles-j*step+180) % 360-180) <= sector_deg/2]
            if len(sample) >= min_count:
                table[k, j] = np.quantile(sample, probabilities)
    u = np.clip(r/bin_px-.5-first, 0, nb-1)
    k0 = np.floor(u).astype(int)
    k1 = np.minimum(k0+1, nb-1)
    wr = u-k0
    j0 = np.floor(theta/step).astype(int) % na
    j1 = (j0+1) % na
    wa = theta/step-np.floor(theta/step)
    nodes = ((k0,j0,(1-wr)*(1-wa)), (k0,j1,(1-wr)*wa),
             (k1,j0,wr*(1-wa)), (k1,j1,wr*wa))
    den = np.zeros(len(ids), np.float32)
    terms = []
    for k,j,w in nodes:
        ww = w*np.isfinite(table[k,j,0])
        terms.append((k,j,ww))
        den += ww
    # A neighbouring cell cannot make an underpopulated annulus valid.
    good = (den > 1e-8) & (count[bins] >= min_count)

    def threshold(qi):
        value = np.zeros(len(ids), np.float32)
        for k,j,w in terms:
            value += np.nan_to_num(table[k,j,qi])*w
        return value/np.maximum(den, 1e-12)

    def inverse(right):
        low = np.zeros(len(ids), np.int16)
        high = np.full(len(ids), nq-1, np.int16)
        for _ in range(8):
            mid = (low+high)//2
            z = threshold(mid)
            above = v >= z if right else v > z
            low = np.where(above, mid, low)
            high = np.where(above, high, mid)
        vl, vh = threshold(low), threshold(high)
        fraction = np.clip((v-vl)/np.maximum(vh-vl, 1e-12), 0, 1)
        rank = (low+fraction*(high-low))/(nq-1)
        return np.where(vh == vl, (high if right else low)/(nq-1), rank)

    cdf = (inverse(False)+inverse(True))/2
    flat = threshold(np.full(len(ids), nq-1, np.int16))-threshold(np.zeros(len(ids), np.int16))
    cdf = np.where(flat == 0, .5, cdf)
    result.ravel()[ids[good]] = cdf[good]
    return result
