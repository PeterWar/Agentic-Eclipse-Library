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
    """Value at each node of a parabola fitted to its neighbours with Gaussian weights (σ in nodes).

    Equally spaced nodes. The window is symmetric about the node, so near the ends it narrows (the end node itself is
    returned as it is): a window cut on one side would bias the value by the profile's third derivative. Constants,
    straight lines, parabolas and cubics come back unchanged."""
    y = np.asarray(y, np.float64); n = len(y)
    if n < 2 or not sigma > 0:
        return y.copy()
    K = max(1, int(np.ceil(3*sigma))); out = np.empty(n)
    for i in range(n):
        k = min(K, i, n-1-i)
        if k == 0:
            out[i] = y[i]; continue
        lo, hi = i-k, i+k+1
        t = (np.arange(lo, hi)-i).astype(np.float64); w = np.sqrt(np.exp(-.5*(t/sigma)**2))
        out[i] = np.linalg.lstsq(np.vander(t, 3, increasing=True)*w[:, None], y[lo:hi]*w, rcond=None)[0][0]
    return out


def _local_curvature(y, sigma):
    """Second derivative (per node squared) at each node, from the same weighted local parabola as
    `_local_quadratic` (σ at least one node); zero where fewer than three nodes are in the window."""
    y = np.asarray(y, np.float64); n = len(y); out = np.zeros(n)
    s = max(float(sigma), 1.); K = max(1, int(np.ceil(3*s)))
    for i in range(n):
        lo, hi = max(0, i-K), min(n, i+K+1)
        if hi-lo < 3:
            continue
        t = (np.arange(lo, hi)-i).astype(np.float64); w = np.sqrt(np.exp(-.5*(t/s)**2))
        out[i] = 2*np.linalg.lstsq(np.vander(t, 3, increasing=True)*w[:, None], y[lo:hi]*w, rcond=None)[0][2]
    return out


def _annulus_slope(rr, z, robust):
    """Local slope dI/dr of one annulus: least squares, or (robust) the medians of its inner and outer halves."""
    if robust:
        cut = np.median(rr); inner = rr <= cut; outer = ~inner
        if inner.any() and outer.any():
            dr = float(np.median(rr[outer])-np.median(rr[inner]))
            if dr > 0:
                return float(np.median(z[outer])-np.median(z[inner]))/dr
        return 0.
    dr = rr-rr.mean(); den = float(np.dot(dr, dr))
    return float(np.dot(dr, z-z.mean()))/den if den > 0 else 0.


def continuous_nrgf(img, valid, geometry, *, center='sun', bin_px=1., robust=True,
                    min_count=50, smooth_bins=0., spread_about='profile'):
    """Evaluate annular mean/spread at the actual radius, without image smoothing.

    PCHIP interpolates measured statistical nodes, separately across each contiguous
    run of populated annuli. Sparse annuli stay undefined. A zero spread (also one that
    is zero to rounding, as for a constant input) is undefined.

    ``spread_about='profile'`` (default since 1.3.2): each annulus gives a node at its exact centre, with its own
    local slope (robust: from the medians of its inner and outer halves) and the local curvature removed. The nodes
    are smoothed by a local parabola, the mean is evaluated at every pixel's radius, and the spread is measured
    about that continuous mean. Inside the end annuli of a run the mean follows that annulus' own slope and
    curvature instead of being held flat. A run of positive annuli is also modelled on its logarithm and keeps the
    model whose profile is less biased. A spread below a few float32 steps of the annulus' own values is undefined.
    ``'bin'`` reproduces 1.3.1.
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
    def runs_of(ok):
        populated = np.flatnonzero(ok)
        return [run for run in np.split(populated, np.flatnonzero(np.diff(populated) != 1)+1) if len(run)]

    if spread_about == 'bin':                                   # 1.3.1: node at the annulus' median (or mean) radius
        mu = np.full(len(count), np.nan); sd, anchors = mu.copy(), mu.copy()
        for k in np.flatnonzero(count >= min_count):
            seg = slice(cuts[k], cuts[k+1])
            z = values[seg].astype(np.float64)
            mu[k] = np.median(z) if robust else np.mean(z)
            sd[k] = 1.4826*np.median(np.abs(z-mu[k])) if robust else np.std(z)
            anchors[k] = np.median(radii[seg]) if robust else np.mean(radii[seg])

        def evaluate(nodes, run, use):
            vals = nodes[run]
            if smooth_bins > 0:
                vals = gaussian_filter1d(vals, smooth_bins, mode='nearest')
            if len(run) == 1:
                return np.full(int(use.sum()), vals[0])
            at = np.clip(r[use], anchors[run[0]], anchors[run[-1]])
            return PchipInterpolator(anchors[run], vals)(at)
        for run in runs_of(np.isfinite(mu) & (sd > 0)):
            use = m & (bins >= run[0]) & (bins <= run[-1])
            out[use] = (a[use]-evaluate(mu, run, use))/np.maximum(evaluate(sd, run, use), 1e-12)
        return out

    # 1.3.2. Each annulus gives a node at its exact centre. The node removes the annulus' own slope (robust: from the
    # medians of its inner and outer halves) and the local curvature, taken from a parabola through the neighbouring
    # nodes: removing only the slope leaves ~I''·<Δr²>/2 in the node (5·10⁻⁴ of the brightness just above the limb of
    # a 60-pixel Sun on r⁻³), which a very clean stack turns into a broad offset of several sigma; that offset, nearly
    # the same in neighbouring nodes, cancels in their curvature. The nodes are smoothed by a local parabola,
    # interpolated by PCHIP, and continued inside the end annuli of a run by that annulus' own slope and curvature.
    # A run whose pixels are all positive is also modelled on the logarithm, where a power law or an exponential is
    # nearly straight, and keeps the model whose profile is less biased (the residuals of each annulus centred
    # nearer zero, in units of their spread; a profile with a dip towards zero is better modelled on the values).
    anchors = (np.arange(len(count))+.5)*bin_px

    def node_of(k, lg, s1, s2):
        seg = slice(cuts[k], cuts[k+1])
        dr, z = radii[seg].astype(np.float64)-anchors[k], values[seg].astype(np.float64)
        if s1 is None:
            return dr, z
        t = s1*dr+.5*s2*dr**2
        x = z*np.exp(-t) if lg else z-t
        c = np.median(x) if robust else np.mean(x)
        return np.log(c) if lg else c

    def fit(run, lg):
        nd, s1, s2 = np.empty(len(run)), np.empty(len(run)), np.zeros(len(run))
        for i, k in enumerate(run):
            dr, z = node_of(k, lg, None, None)
            s1[i] = _annulus_slope(dr, np.log(z) if lg else z, robust)
            nd[i] = node_of(k, lg, s1[i], 0.)
        if len(run) >= 3:
            s2 = _local_curvature(nd, smooth_bins)/bin_px**2
            nd = np.array([node_of(k, lg, s1[i], s2[i]) for i, k in enumerate(run)])
        return nd, s1, s2

    def smooth(y):
        # A local parabola instead of a plain Gaussian blur: blurring a steep, curved profile biases it (by
        # ~σ²·I''/2: about 1 % of the brightness, one ring sigma, 0.2 R☉ above the limb of a 120-pixel Sun with
        # σ = 6 px), which leaves a broad false ring.
        return _local_quadratic(y, smooth_bins) if smooth_bins > 0 else y

    def along(y, run, rr, lg, ends=None):
        """Profile (from nodes y, on the logarithm if lg) at radii rr inside the run; ends = (slopes, curvatures)."""
        if len(run) == 1:
            base = np.full(len(rr), y[0])
        else:
            base = PchipInterpolator(anchors[run], y)(np.clip(rr, anchors[run[0]], anchors[run[-1]]))
        if ends is not None:
            for i, side in ((0, rr < anchors[run[0]]), (-1, rr > anchors[run[-1]])):
                dr = rr[side]-anchors[run[i]]
                base[side] = y[i]+ends[0][i]*dr+.5*ends[1][i]*dr**2
        return np.exp(base) if lg else base

    def spread(res, bu, run):
        """Per annulus: the spread of the residuals about their centre, and that centre (zero for an unbiased profile)."""
        o = np.argsort(bu, kind='stable'); rs = res[o]
        cnt = np.bincount(bu-run[0], minlength=len(run)); cut = np.r_[0, np.cumsum(cnt)]
        sp, centre = np.full(len(run), np.nan), np.full(len(run), np.nan)
        for i in np.flatnonzero(cnt >= min_count):
            z = rs[cut[i]:cut[i+1]]
            centre[i] = np.median(z) if robust else np.mean(z)
            sp[i] = 1.4826*np.median(np.abs(z-centre[i])) if robust else np.std(z)
        return sp, centre

    # The profile at every pixel's radius and the spread of each annulus about it. A spread below a few float32 steps
    # of the annulus' own operands (its pixel values, and its slope times the radius, whose map is float32) is
    # numerical: no output there.
    resid = np.full(a.shape, np.nan, np.float64); sd2 = np.full(len(count), np.nan); floor = np.full(len(count), np.inf)
    mag = np.bincount(b, np.abs(v).astype(np.float64), minlength=len(count))/np.maximum(count, 1)
    for run in runs_of(count >= min_count):
        use = m & (bins >= run[0]) & (bins <= run[-1])
        au, ru, bu = a[use].astype(np.float64), r[use].astype(np.float64), bins[use]
        best = None
        for lg in ((False, True) if np.all(au > 0) else (False,)):
            nd, s1, s2 = fit(run, lg)
            res = au-along(smooth(nd), run, ru, lg, (s1, s2))
            sp, centre = spread(res, bu, run)
            score = float(np.nansum((centre/np.maximum(sp, 4*np.finfo(np.float32).eps*mag[run]+1e-300))**2))
            if best is None or score < best[0]:
                best = (score, lg, nd, s1, res, sp)
        _, lg, nd, s1, res, sp = best
        resid[use] = res; sd2[run] = sp
        floor[run] = 4*np.finfo(np.float32).eps*(mag[run]+np.abs(s1*np.exp(nd) if lg else s1)*anchors[run])
    real = np.isfinite(sd2) & (sd2 > 0) & (sd2 > floor)
    for run in runs_of(real):
        use = m & (bins >= run[0]) & (bins <= run[-1])
        out[use] = resid[use]/along(smooth(np.log(sd2[run])), run, r[use].astype(np.float64), True)
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
