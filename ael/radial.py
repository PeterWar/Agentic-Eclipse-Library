"""Continuous measured radial statistics; never a replacement for missing radiance."""
from __future__ import annotations

import numpy as np
from scipy.interpolate import CubicHermiteSpline, CubicSpline, PchipInterpolator
from scipy.ndimage import gaussian_filter1d, median_filter


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
    """First and second derivative at each node: from the quartic through it and its two neighbours on each side,
    and at the two nodes next to each end of a run from the cubic through the four nearest (a quartic cut on one side
    extrapolates badly). x are the node positions; at least four nodes. Exact for cubics."""
    y = np.asarray(y, np.float64); x = np.asarray(x, np.float64); n = len(y)
    d1, d2 = np.empty(n), np.empty(n)
    for i in range(n):
        w = 5 if (2 <= i <= n-3 and n >= 5) else min(4, n)       # centred quartic inside, cubic near the ends
        lo = min(max(i-w//2, 0), n-w); t = x[lo:lo+w]-x[i]
        c = np.linalg.solve(np.vander(t, w, increasing=True), y[lo:lo+w])
        d1[i], d2[i] = c[1], 2*c[2]
    return d1, d2


def _radial_smooth(rr, z, step, least=24, distinct=4, slope=False):
    """A smooth function of radius through z (sorted radii rr): in radial bands `step` px wide (merged until each holds
    at least `least` samples at `distinct` different radii), the value at the band's centroid of a parabola fitted
    inside the band (a plain band mean would be off by z''·width²/24; with fewer than three radii the parabola is not
    determined), joined by a not-a-knot cubic spline. One pass over the data. With `slope`, also its derivative."""
    band = np.floor((rr-rr[0])/step).astype(np.int64)
    cnt = np.bincount(band)
    new = np.bincount(band, np.r_[True, np.diff(rr) > 1e-3*step], minlength=len(cnt))   # radii a band adds
    gid, acc, nd, g = np.empty(len(cnt), np.int64), 0, 0, 0
    for i, c in enumerate(cnt):                                  # merge sparse bands into the next
        gid[i] = g; acc += c; nd += new[i]
        if acc >= least and nd >= distinct:
            g += 1; acc = nd = 0
    if acc and g:                                                # a short last group joins the one before
        gid[gid == g] = g-1
    grp = gid[band]; n = int(grp.max())+1
    w = np.bincount(grp, minlength=n)
    centre = np.bincount(grp, rr, minlength=n)/w
    u = (rr-centre[grp])/step
    S = [np.bincount(grp, u**k, minlength=n) for k in range(5)]
    T = [np.bincount(grp, z*u**k, minlength=n) for k in range(3)]
    A = np.stack([np.stack([S[0], S[1], S[2]], -1), np.stack([S[1], S[2], S[3]], -1), np.stack([S[2], S[3], S[4]], -1)], -2)
    level = T[0]/w
    ok = np.abs(np.linalg.det(A)) > 1e-12*np.maximum(S[0], 1)**3
    if ok.any():
        level[ok] = np.linalg.solve(A[ok], np.stack([T[0], T[1], T[2]], -1)[ok][..., None])[..., 0, 0]
    if n < 4 or np.any(np.diff(centre) <= 0):
        s = median_filter(z, size=9, mode='nearest')
        return (s, np.zeros(len(z))) if slope else s
    f = CubicSpline(centre, level, bc_type='not-a-knot')
    return (f(rr), f(rr, 1)) if slope else f(rr)


def continuous_nrgf(img, valid, geometry, *, center='sun', bin_px=1., robust=True,
                    min_count=50, smooth_bins=0., spread_about='profile'):
    """Evaluate annular mean/spread at the actual radius, without image smoothing.

    Statistical nodes are measured annulus by annulus and interpolated separately across each contiguous run of
    populated annuli. Sparse annuli stay undefined. A zero spread (also one that is zero to rounding, as for a
    constant input) is undefined.

    ``spread_about='profile'`` (default since 1.3.2): each annulus gives a node at the mean radius of its pixels,
    with the profile's slope and curvature removed inside it (both from the neighbouring median nodes). A cubic
    Hermite curve through the nodes gives the mean at every pixel's radius, also inside the end annuli of a run; one
    node moves only the two intervals beside it. The spread,
    measured about it, is interpolated without overshoot and held at the end nodes. Each run is also modelled on its
    logarithm (or on asinh when the profile goes through zero) and keeps the model that fits its pixels better.
    Undefined: a run of fewer than four annuli; an annulus where half the pixels share one value (zeros,
    clipping, integers coarser than the noise); an annulus whose residuals vary with radius only (no angular spread
    above a float32 step of its own values). Nodes are smoothed only if ``smooth_bins`` > 0.
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

    order = np.argsort(r[m], kind='stable')                    # by radius (annuli stay contiguous)
    values, radii = v[order], r[m][order]
    pos = np.flatnonzero(m.ravel())[order]
    # 1.3.2. Each annulus gives a node at the mean radius of its own pixels (a node placed at the annulus' centre would
    # be extrapolated from its data where an edge cuts the annulus), with the profile's local slope and curvature
    # removed inside the annulus. Both come from the quartic through the five nearest nodes (the cubic through four
    # next to the ends of a run), refined up to four times. Without the curvature, the node keeps
    # ~I''·<Δr²>/2 (5·10⁻⁴ of the brightness just above the limb of a 60-pixel Sun on r⁻³), which a very clean stack
    # turns into a broad offset of several sigma; a slope measured from the two halves of the annulus itself is
    # thrown off by angular structure, because the halves see different angles. The slope and curvature always come
    # from median nodes, so that with the mean statistic one bright pixel moves only its own node. A run of fewer than
    # four annuli gives no output. A cubic Hermite curve through the nodes, with those slopes, gives the profile at
    # every pixel's radius and moves only the two intervals beside a node (a global spline carried one bright pixel's
    # node to five annuli away); the spread is interpolated without overshoot (PCHIP on its logarithm) and held at
    # the end nodes, so it never dips towards zero. The nodes are not smoothed by default: each averages hundreds of pixels, and a smoothing window bends a
    # profile whose power-law index changes (2.5 sigma on a Baumbach corona, 10 sigma on a 15-pixel Sun at 6 px).
    anchors = np.full(len(count), np.nan); mag = np.full(len(count), np.nan); usable = count >= min_count
    for k in np.flatnonzero(usable):
        seg = slice(cuts[k], cuts[k+1]); z = values[seg].astype(np.float64)
        anchors[k] = float(np.mean(radii[seg], dtype=np.float64))
        mag[k] = float(np.median(np.abs(z)))
        # Ties (zeros, clipping, integers coarser than the noise): with half the pixels on one value the robust
        # spread (MAD) is zero and the node is that value, not the corona.
        med = np.median(z)
        if max(np.mean(z == z.min()), np.mean(z == z.max()), np.mean(z == med)) >= .5:
            usable[k] = False

    def segment(k):
        seg = slice(cuts[k], cuts[k+1])
        return radii[seg].astype(np.float64)-anchors[k], values[seg].astype(np.float64)

    def fwd(tr, x):
        return x if tr[0] == 'lin' else np.log(x) if tr[0] == 'log' else np.arcsinh(x/tr[1])

    def inv(tr, y):
        return y if tr[0] == 'lin' else np.exp(y) if tr[0] == 'log' else tr[1]*np.sinh(y)

    def fit(run, tr):
        """Nodes of one run in the transform tr, their slopes and curvatures; None if a node has no logarithm."""
        n = len(run); s1, s2 = np.zeros(n), np.zeros(n)

        def nodes(stat):
            nd = np.empty(n)
            for i, k in enumerate(run):
                dr, z = segment(k); t = s1[i]*dr+.5*s2[i]*dr**2
                x = z-t if tr[0] == 'lin' else z*np.exp(-t) if tr[0] == 'log' else inv(tr, fwd(tr, z)-t)
                c = stat(x)
                if tr[0] == 'log' and not c > 0:
                    return None
                nd[i] = fwd(tr, c)
            return nd
        # The shape of the profile (slope and curvature) always comes from median nodes, so that with the mean
        # statistic one bright pixel moves only its own node and not the shape of its neighbours'.
        nd = nodes(np.median)
        for _ in range(4):                                      # slope and curvature from the neighbouring nodes
            if nd is None:
                return None
            s1, s2 = _node_derivatives(nd, anchors[run])
            prev, nd = nd, nodes(np.median)
            if nd is not None and np.max(np.abs(nd-prev)) <= 1e-9*np.max(np.abs(nd)):
                break
        if nd is not None and not robust:
            nd = nodes(np.mean)
        return None if nd is None else (nd, s1, s2)

    def smooth(y, run):
        # Only when asked (smooth_bins > 0). A local parabola instead of a plain Gaussian blur: blurring a steep,
        # curved profile biases it (by ~σ²·I''/2: about 1 % of the brightness, half a ring sigma with 2 % structure,
        # 0.2 R☉ above the limb of a 120-pixel Sun with σ = 6 px), which leaves a broad false ring.
        return _local_quadratic(y, smooth_bins, anchors[run]/bin_px) if smooth_bins > 0 else y

    def along(y, run, rr, tr, d1):
        """Profile at radii rr inside the run: a cubic Hermite curve through the nodes y (in the transform tr) with
        slopes d1, which follows the profile's curvature between nodes, continues it inside the end annuli, and lets a
        node move only the two intervals beside it."""
        return inv(tr, CubicHermiteSpline(anchors[run], y, d1)(rr))

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

    def angular_spread(res, run, au):
        """Per annulus: the spread left once a smooth function of radius is removed: what radius alone cannot explain.
        Two functions are tried and the smaller spread is kept: one through the residuals, in radial bands a tenth of a
        pixel wide, and one through the values (residual plus profile: no kinks where the profile's pieces meet), in
        bands half as wide. Each band holds at least 24 samples at four or more different radii, and gives the value at
        its centre of a parabola fitted inside it; a cubic spline joins them (residuals clipped at five spreads, annulus
        by annulus, when robust). Too coarse to follow angular structure even where pixels at one radius are mirror
        images of each other (a centre on the pixel grid); fine enough to follow, to rounding, the profile's own shape
        and a ripple, a step or a kink a few pixels wide (limits in docs/VALIDATION_1.3.2.md). Also returns, per annulus,
        the median slope of the function through the values: the radius map is float32, so its rounding times that
        local slope belongs to the floor (a profile's own slope can be far smaller than that of a radial ripple)."""
        lo = cuts[run[0]]; rr = radii[lo:lo+len(res)].astype(np.float64); z = res.copy()
        if robust:                                             # clipped annulus by annulus: their scales differ
            for k in run:
                sl = slice(cuts[k]-lo, cuts[k+1]-lo); c = np.median(z[sl]); w = 1.4826*np.median(np.abs(z[sl]-c))
                z[sl] = np.clip(z[sl], c-5*w, c+5*w)
        ang, steep = np.full(len(run), np.inf), np.zeros(len(run))
        for zz, step in ((z, .1), (z+(au-res), .05)):
            s, ds = _radial_smooth(rr, zz, step, slope=True); e = zz-s
            for i, k in enumerate(run):
                sl = slice(cuts[k]-lo, cuts[k+1]-lo); ez = e[sl]
                ang[i] = min(ang[i], 1.4826*np.median(np.abs(ez-np.median(ez))) if robust else np.std(ez))
                steep[i] = np.median(np.abs(ds[sl]))               # the last function: the one through the values
        return ang, steep

    # The profile at every pixel's radius and the spread of each annulus about it. Every run is modelled on its values
    # and on their logarithm (or, when a node is not positive, on asinh(I/s) with s the median size of the nodes:
    # logarithmic where the corona is bright, linear where a subtracted sky takes it through zero), and keeps the
    # model with the smaller mean square misfit, annulus by annulus. An annulus whose residuals, once any function of
    # radius is removed, spread less than one float32 step of its own operands (the median size of its values, and
    # its slope times the radius, whose map is float32; at least the smallest subnormal) has no angular signal, only
    # rounding or the profile's own shape: no output there.
    eps, tiny = np.finfo(np.float32).eps, float(np.finfo(np.float32).smallest_subnormal)
    resid = np.full(len(values), np.nan); sd2 = np.full(len(count), np.nan); floor = np.full(len(count), np.inf)
    angular = np.full(len(count), np.nan)
    for run in runs_of(usable):
        if len(run) < 4:                                        # the end nodes need four nodes: no output
            continue
        lo, hi = cuts[run[0]], cuts[run[-1]+1]
        au, ru = values[lo:hi].astype(np.float64), radii[lo:hi].astype(np.float64)
        best, cands = None, [('lin', None), ('log', None)]
        for tr in cands:
            f = fit(run, tr)
            if f is None:
                if tr[0] == 'log' and best is not None and np.median(np.abs(best[2])) > 0:
                    cands.append(('asinh', float(np.median(np.abs(best[2])))))   # best[2]: the linear nodes
                continue
            nd, s1, s2 = f
            y = smooth(nd, run)
            res = au-along(y, run, ru, tr, s1 if smooth_bins == 0 else _node_derivatives(y, anchors[run])[0])
            sp, mse = spread(res, run)
            score = float(np.nansum(np.log(mse+(eps*mag[run])**2+tiny**2)))
            if best is None or score < best[0]:
                best = (score, tr, nd, s1, res, sp)
        _, tr, nd, s1, res, sp = best
        resid[lo:hi] = res; sd2[run] = sp; angular[run], steep = angular_spread(res, run, au)
        dIdy = 1. if tr[0] == 'lin' else np.exp(nd) if tr[0] == 'log' else tr[1]*np.cosh(nd)
        floor[run] = eps*(mag[run]+np.maximum(np.abs(s1*dIdy), steep)*anchors[run])+4*tiny
    real = np.isfinite(sd2) & (sd2 > 0) & (angular > floor)
    flat = out.reshape(-1)
    for run in [run for run in runs_of(real) if len(run) >= 4]:
        lo, hi = cuts[run[0]], cuts[run[-1]+1]
        y = smooth(np.log(sd2[run]), run)                       # the spread: shape-preserving, held at the end nodes
        at = np.clip(radii[lo:hi].astype(np.float64), anchors[run[0]], anchors[run[-1]])
        qq = resid[lo:hi]/np.exp(PchipInterpolator(anchors[run], y)(at))
        flat[pos[lo:hi]] = np.where(np.isfinite(qq) & (np.abs(qq) < 1e30), qq, np.nan)   # never inf in float32
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
