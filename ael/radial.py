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


def _local_quadratic(y, sigma):
    """Value at each node of a quadratic fitted to its neighbours with Gaussian weights (σ in nodes).

    Equally spaced nodes; near the ends the window is truncated and the fit uses the nodes that exist."""
    y = np.asarray(y, np.float64); n = len(y)
    if n < 4:
        return y.copy()
    K = int(np.ceil(3*sigma)); out = np.empty(n)
    for i in range(n):
        lo, hi = max(0, i-K), min(n, i+K+1)
        t = np.arange(lo, hi)-i; w = np.exp(-.5*(t/sigma)**2)
        A = np.stack([np.ones_like(t, float), t, t*t], 1) if hi-lo >= 5 else np.stack([np.ones_like(t, float), t], 1)
        coef = np.linalg.lstsq(A*np.sqrt(w)[:, None], y[lo:hi]*np.sqrt(w), rcond=None)[0]
        out[i] = coef[0]
    return out


def continuous_nrgf(img, valid, geometry, *, center='sun', bin_px=1., robust=True,
                    min_count=50, smooth_bins=0., spread_about='profile'):
    """Evaluate annular mean/spread at the actual radius, without image smoothing.

    PCHIP interpolates measured statistical nodes, separately across each contiguous
    run of populated annuli. Sparse annuli stay undefined; endpoint statistics are
    held only inside their own observed end annulus. A zero spread is undefined.

    ``spread_about='profile'`` (default since 1.3.2) measures the spread of each annulus
    about the continuous mean profile evaluated at every pixel's own radius, so the
    fall of brightness *inside* an annulus no longer inflates the spread nor prints
    ripples locked to the annuli where the profile is steep. ``'bin'`` reproduces 1.3.1
    (spread about the annulus' own centre value).
    """
    if spread_about not in ('profile', 'bin'):
        raise ValueError("spread_about must be 'profile' or 'bin'")
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
        if spread_about == 'bin':                              # 1.3.1: node at the annulus' median (or mean) radius
            mu[k] = np.median(z) if robust else np.mean(z)
            sd[k] = 1.4826*np.median(np.abs(z-mu[k])) if robust else np.std(z)
            anchors[k] = np.median(radii[seg]) if robust else np.mean(radii[seg])
        else:                                                   # 1.3.2: node at the annulus' exact centre, local slope removed
            rr = radii[seg].astype(np.float64); rc = (k+.5)*bin_px
            dr = rr-rr.mean(); den = float(np.dot(dr, dr))
            slope = float(np.dot(dr, z-z.mean()))/den if den > 0 else 0.
            zc = z-slope*(rr-rc)                                # each value moved to the centre radius along the local slope
            mu[k] = np.median(zc) if robust else np.mean(zc)
            sd[k] = 1.4826*np.median(np.abs(zc-mu[k])) if robust else np.std(zc)
            anchors[k] = rc

    def runs_of(ok):
        populated = np.flatnonzero(ok)
        return [run for run in np.split(populated, np.flatnonzero(np.diff(populated) != 1)+1) if len(run)]

    def evaluate(nodes, run, use):
        vals = nodes[run]
        if smooth_bins > 0:
            if spread_about != 'bin':
                # 1.3.2: a local quadratic fit with Gaussian weights instead of a plain Gaussian blur. Blurring a
                # steep, curved profile biases it (by ~σ²·I''/2: about 1 % of the brightness, one ring sigma,
                # 0.2 R☉ above the limb of a 120-pixel Sun with σ = 6 px), which leaves a broad false ring; a
                # local quadratic keeps the curvature, and on the logarithm of a positive profile the residual
                # bias is of fourth order.
                pos = bool(np.all(vals > 0))
                vals = _local_quadratic(np.log(vals) if pos else vals, smooth_bins)
                vals = np.exp(vals) if pos else vals
            else:
                vals = gaussian_filter1d(vals, smooth_bins, mode='nearest')
        if len(run) == 1:
            return np.full(int(use.sum()), vals[0])
        at = np.clip(r[use], anchors[run[0]], anchors[run[-1]])
        return PchipInterpolator(anchors[run], vals)(at)

    if spread_about == 'bin':
        for run in runs_of(np.isfinite(mu) & (sd > 0)):
            use = m & (bins >= run[0]) & (bins <= run[-1])
            out[use] = (a[use]-evaluate(mu, run, use))/np.maximum(evaluate(sd, run, use), 1e-12)
        return out
    # 1st pass: the continuous mean profile at every pixel's radius
    resid = np.full(a.shape, np.nan, np.float64)
    for run in runs_of(np.isfinite(mu)):
        use = m & (bins >= run[0]) & (bins <= run[-1])
        resid[use] = a[use]-evaluate(mu, run, use)
    # 2nd pass: the spread of each annulus about that profile
    ok = m & np.isfinite(resid)
    d = resid[ok]; bd = bins[ok]
    o2 = np.argsort(bd, kind='stable'); c2 = np.bincount(bd, minlength=len(count)); k2 = np.r_[0, np.cumsum(c2)]
    ds = d[o2]
    sd2 = np.full(len(count), np.nan)
    for k in np.flatnonzero(c2 >= min_count):
        z = ds[k2[k]:k2[k+1]]
        sd2[k] = 1.4826*np.median(np.abs(z-np.median(z))) if robust else np.std(z)
    for run in runs_of(np.isfinite(mu) & np.isfinite(sd2) & (sd2 > 0)):
        use = ok & (bins >= run[0]) & (bins <= run[-1])
        out[use] = resid[use]/np.maximum(evaluate(sd2, run, use), 1e-12)
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
