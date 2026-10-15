"""Continuous measured radial statistics; never a replacement for missing radiance."""
from __future__ import annotations

import numpy as np
from scipy.interpolate import CubicSpline, PchipInterpolator
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


def _local_quadratic(y, sigma, x=None):
    """Value at each node of a parabola fitted to its neighbours with Gaussian weights (σ in nodes).

    x: node positions in units of the node spacing (default 0, 1, 2…). The window holds the same number of nodes on
    each side, so near the ends it narrows (the end node itself is returned as it is): a window cut on one side would
    bias the value by the profile's third derivative. Constants, straight lines and parabolas come back unchanged;
    with equally spaced nodes, cubics too."""
    y = np.asarray(y, np.float64); n = len(y)
    if n < 2 or not sigma > 0:
        return y.copy()
    x = np.arange(n, dtype=np.float64) if x is None else np.asarray(x, np.float64)
    K = max(1, int(np.ceil(3*sigma))); out = np.empty(n)
    for i in range(n):
        k = min(K, i, n-1-i)
        if k == 0:
            out[i] = y[i]; continue
        lo, hi = i-k, i+k+1
        t = x[lo:hi]-x[i]; w = np.sqrt(np.exp(-.5*(t/sigma)**2))
        out[i] = np.linalg.lstsq(np.vander(t, 3, increasing=True)*w[:, None], y[lo:hi]*w, rcond=None)[0][0]
    return out


def _node_derivatives(y, x):
    """First and second derivative at each node: from the parabola through it and its two neighbours, and at the
    two end nodes from the cubic through the four nearest nodes (a parabola there, cut on one side, would err by the
    third derivative). x are the node positions; at least three nodes."""
    y = np.asarray(y, np.float64); x = np.asarray(x, np.float64); n = len(y)
    j = np.clip(np.arange(n)-1, 0, n-3)
    x1, x2, x3, y1, y2, y3 = x[j], x[j+1], x[j+2], y[j], y[j+1], y[j+2]
    a12, a23 = (y2-y1)/(x2-x1), (y3-y2)/(x3-x2)
    d2 = 2*(a23-a12)/(x3-x1)
    d1 = a12+.5*d2*(2*x-x1-x2)
    if n >= 4:
        for i, sl in ((0, slice(0, 4)), (n-1, slice(n-4, n))):
            t = x[sl]-x[i]; c = np.linalg.solve(np.vander(t, 4, increasing=True), y[sl])
            d1[i], d2[i] = c[1], 2*c[2]
    return d1, d2


def continuous_nrgf(img, valid, geometry, *, center='sun', bin_px=1., robust=True,
                    min_count=50, smooth_bins=0., spread_about='profile'):
    """Evaluate annular mean/spread at the actual radius, without image smoothing.

    Statistical nodes are measured annulus by annulus and interpolated separately across each contiguous run of
    populated annuli. Sparse annuli stay undefined. A zero spread (also one that is zero to rounding, as for a
    constant input) is undefined.

    ``spread_about='profile'`` (default since 1.3.2): each annulus gives a node at the mean radius of its pixels,
    with its own slope (robust: from the medians of its inner and outer halves) and the local curvature removed. The
    nodes are smoothed by a local parabola and a cubic spline through them gives the mean at every pixel's radius;
    the spread is measured about that continuous mean. Inside the end annuli of a run the mean follows the spline's
    curvature instead of being held flat. Each run is also modelled on its logarithm and keeps the model that fits
    its pixels better. A run of fewer than three annuli, or a spread below a few float32 steps of the annulus' own
    values, is undefined.
    ``'bin'`` reproduces 1.3.1: nodes at the median (or mean) radius, spread about each annulus' own centre, PCHIP.
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
    pos = np.flatnonzero(m.ravel())[order]                     # image position of each sorted sample
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

    # 1.3.2. Each annulus gives a node at the mean radius of its own pixels (a node placed at the annulus' centre would
    # be extrapolated from its data where an edge cuts the annulus), with the profile's local slope and curvature
    # removed inside the annulus. Both come from the parabola through the node and its two neighbours (at the end
    # nodes, the cubic through the four nearest), refined up to four times. Without the curvature, the node keeps
    # ~I''·<Δr²>/2 (5·10⁻⁴ of the brightness just above the limb of a 60-pixel Sun on r⁻³), which a very clean stack
    # turns into a broad offset of several sigma; a slope measured from the two halves of the annulus itself is
    # thrown off by angular structure, because the halves see different angles.
    # A run of fewer than three annuli has no neighbours and no output. A not-a-knot cubic spline through the nodes
    # gives the profile at every pixel's radius, following its curvature between nodes and inside the end annuli.
    # The nodes are not smoothed by default: each averages hundreds of pixels, and a smoothing window bends a profile
    # whose power-law index changes (2.5 sigma on a Baumbach corona, 10 sigma on a 15-pixel Sun at 6 px).
    # Every run is also modelled on the logarithm (the nodes must be positive; single non-positive pixels are
    # allowed), where a power law or an exponential is nearly straight, and keeps the model with the smaller mean
    # square misfit, annulus by annulus (a profile with a dip towards zero is better modelled on the values).
    anchors = np.full(len(count), np.nan); mag = np.full(len(count), np.nan)
    for k in np.flatnonzero(count >= min_count):
        seg = slice(cuts[k], cuts[k+1])
        anchors[k] = float(np.mean(radii[seg], dtype=np.float64))
        mag[k] = float(np.median(np.abs(values[seg].astype(np.float64))))

    def segment(k):
        seg = slice(cuts[k], cuts[k+1])
        return radii[seg].astype(np.float64)-anchors[k], values[seg].astype(np.float64)

    def fit(run, lg):
        """Nodes of one run (on the logarithm if lg), their slopes and curvatures; None if a node is not positive."""
        n = len(run); s1, s2 = np.zeros(n), np.zeros(n)

        def nodes():
            nd = np.empty(n)
            for i, k in enumerate(run):
                dr, z = segment(k); t = s1[i]*dr+.5*s2[i]*dr**2
                x = z*np.exp(-t) if lg else z-t
                c = np.median(x) if robust else np.mean(x)
                if lg and not c > 0:
                    return None
                nd[i] = np.log(c) if lg else c
            return nd
        nd = nodes()
        for _ in range(4):                                      # slope and curvature from the neighbouring nodes
            if nd is None:
                return None
            s1, s2 = _node_derivatives(nd, anchors[run])
            prev, nd = nd, nodes()
            if nd is not None and np.max(np.abs(nd-prev)) <= 1e-9*np.max(np.abs(nd)):
                break
        return None if nd is None else (nd, s1, s2)

    def smooth(y, run):
        # Only when asked (smooth_bins > 0). A local parabola instead of a plain Gaussian blur: blurring a steep,
        # curved profile biases it (by ~σ²·I''/2: about 1 % of the brightness, half a ring sigma with 2 % structure,
        # 0.2 R☉ above the limb of a 120-pixel Sun with σ = 6 px), which leaves a broad false ring.
        return _local_quadratic(y, smooth_bins, anchors[run]/bin_px) if smooth_bins > 0 else y

    def along(y, run, rr, lg):
        """Profile at radii rr inside the run: a not-a-knot cubic spline through the nodes y (on the logarithm if lg),
        which follows the profile's curvature between nodes and continues it inside the end annuli."""
        base = CubicSpline(anchors[run], y, bc_type='not-a-knot')(rr)
        return np.exp(base) if lg else base

    def spread(res, run):
        """Per annulus: the spread of the residuals about their centre, and their mean square about the profile
        (clipped at five spreads from the centre), which grows with any misfit of the profile."""
        sp, mse = np.full(len(run), np.nan), np.full(len(run), np.nan)
        for i, k in enumerate(run):
            z = res[cuts[k]-cuts[run[0]]:cuts[k+1]-cuts[run[0]]]
            c = np.median(z) if robust else np.mean(z)
            sp[i] = 1.4826*np.median(np.abs(z-c)) if robust else np.std(z)
            mse[i] = np.mean(np.clip(z, c-5*sp[i], c+5*sp[i])**2)
        return sp, mse

    def angular_spread(res, run):
        """Per annulus: the spread left once a cubic in radius is removed inside it (what radius alone cannot explain).
        Robust: the cubic is fitted to the residuals clipped at five spreads, and the spread is 1.4826 MAD."""
        ang = np.full(len(run), np.nan)
        for i, k in enumerate(run):
            z = res[cuts[k]-cuts[run[0]]:cuts[k+1]-cuts[run[0]]]
            dr = radii[cuts[k]:cuts[k+1]].astype(np.float64)-anchors[k]
            A = np.vander(dr/max(float(np.ptp(dr)), 1e-12), 4, increasing=True)
            if robust:
                c = np.median(z); w = 1.4826*np.median(np.abs(z-c))
                z = np.clip(z, c-5*w, c+5*w)
            e = z-A@np.linalg.lstsq(A, z, rcond=None)[0]
            ang[i] = 1.4826*np.median(np.abs(e-np.median(e))) if robust else np.std(e)
        return ang

    # The profile at every pixel's radius and the spread of each annulus about it. An annulus whose residuals, once
    # a cubic in radius is removed inside it, spread less than one float32 step of its own operands (the median size
    # of its values, and its slope times the radius, whose map is float32; at least the smallest subnormal) has no
    # angular signal, only rounding or the profile's own shape: no output there.
    eps, tiny = np.finfo(np.float32).eps, float(np.finfo(np.float32).smallest_subnormal)
    resid = np.full(len(values), np.nan); sd2 = np.full(len(count), np.nan); floor = np.full(len(count), np.inf)
    angular = np.full(len(count), np.nan)
    for run in runs_of(count >= min_count):
        if len(run) < 3:                                        # no curvature from neighbours: no output
            continue
        lo, hi = cuts[run[0]], cuts[run[-1]+1]
        au, ru = values[lo:hi].astype(np.float64), radii[lo:hi].astype(np.float64)
        best = None
        for lg in (False, True):
            f = fit(run, lg)
            if f is None:
                continue
            nd, s1, s2 = f
            res = au-along(smooth(nd, run), run, ru, lg)
            sp, mse = spread(res, run)
            score = float(np.nansum(np.log(mse+(eps*mag[run])**2+tiny)))
            if best is None or score < best[0]:
                best = (score, lg, nd, s1, res, sp)
        _, lg, nd, s1, res, sp = best
        resid[lo:hi] = res; sd2[run] = sp; angular[run] = angular_spread(res, run)
        floor[run] = eps*(mag[run]+np.abs(s1*np.exp(nd) if lg else s1)*anchors[run])+4*tiny
    real = np.isfinite(sd2) & (sd2 > 0) & (angular > floor)
    flat = out.reshape(-1)
    for run in [run for run in runs_of(real) if len(run) >= 3]:
        lo, hi = cuts[run[0]], cuts[run[-1]+1]
        flat[pos[lo:hi]] = resid[lo:hi]/along(smooth(np.log(sd2[run]), run), run, radii[lo:hi].astype(np.float64), True)
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
