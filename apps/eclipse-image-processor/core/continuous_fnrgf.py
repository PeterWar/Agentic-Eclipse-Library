"""Independent support-aware Fourier radial normalization.

Fits sector statistics in input units. Adjacent populated radial models are
smoothed/interpolated; absent sectors never become zero-valued observations.
This optional variant differs from the reference-compatible FNRGF core.
"""
from .cancellation import check_cancelled
import numpy as np
from scipy.ndimage import gaussian_filter1d


def continuous_fnrgf(image, radii, angles, edges, order=6, segments=64,
                     cutoff=0, width_function='std', valid=None, smooth_px=8.,
                     ridge=.01, width_floor=.05, robust_iterations=2,
                     min_pixels=1, mean_tail=0., width_tail=0.):
    a = np.asarray(image, dtype=float)
    r, theta, edges = np.asarray(radii), np.asarray(angles), np.asarray(edges)
    if a.ndim != 2 or r.shape != a.shape or theta.shape != a.shape:
        raise ValueError('FNRGF image and geometry must be matching 2D arrays')
    if edges.ndim != 1 or len(edges) < 2 or not np.isfinite(edges).all() or np.any(np.diff(edges) <= 0):
        raise ValueError('FNRGF radial edges must increase')
    if order < 1 or segments < 2*order+1 or not 0 <= cutoff <= order+1:
        raise ValueError('FNRGF needs segments >= 2*order+1 and a valid cutoff')
    if width_function not in ('std', 'mad') or min_pixels < 1:
        raise ValueError('Invalid FNRGF sector statistics')
    if not np.isfinite([smooth_px, ridge, width_floor, mean_tail, width_tail]).all() or smooth_px < 0 or ridge < 0 or not 0 <= width_floor <= 1:
        raise ValueError('Invalid FNRGF smoothing, regularization or width floor')
    if not 0 <= mean_tail <= 1 or not 0 <= width_tail <= 1 or not 0 <= robust_iterations <= 5:
        raise ValueError('Invalid FNRGF attenuation or iteration count')
    observed = np.isfinite(a) & np.isfinite(r) & np.isfinite(theta)
    if valid is not None:
        if np.shape(valid) != a.shape:
            raise ValueError('FNRGF statistics mask must match image')
        observed &= valid
    bins = np.searchsorted(edges, r, side='right')-1
    observed &= (bins >= 0) & (bins < len(edges)-1)
    ids = np.flatnonzero(observed)
    output = np.full(a.shape, np.nan)
    if not ids.size:
        return output
    if np.ptp(a.ravel()[ids]) == 0:
        output[observed] = 0.
        return output
    # Scale internally to avoid unit-dependent ridge and width safety floors.
    magnitude = float(np.max(np.abs(a.ravel()[ids])))
    unit = a / (magnitude if magnitude else 1.)
    sector = np.floor((theta.ravel()[ids] % (2*np.pi))*segments/(2*np.pi)).astype(int) % segments
    keys = bins.ravel()[ids]*segments+sector
    sorting = np.argsort(keys, kind='stable')
    ids = ids[sorting]
    counts = np.bincount(keys, minlength=(len(edges)-1)*segments)
    cuts = np.r_[0, np.cumsum(counts)]
    phi = (np.arange(segments)+.5)*2*np.pi/segments
    design = np.column_stack([np.ones(segments)] + [f(k*phi) for k in range(1, order+1) for f in (np.cos, np.sin)])
    penalty = np.r_[0., np.repeat(np.arange(1, order+1, dtype=float)**2, 2)]
    models = np.full((2, len(edges)-1, design.shape[1]), np.nan)
    floors = np.full(len(edges)-1, np.nan)
    centers = (edges[:-1]+edges[1:])/2

    def fit(values, populations):
        good = populations > 0
        X, y = design[good], values[good]
        base = populations[good]/populations[good].sum()
        weights = base.copy()
        coverage = good.mean()
        regularizer = np.diag(np.sqrt(ridge/max(coverage, 1/segments)**4*penalty))
        for iteration in range(int(robust_iterations)+1):
            check_cancelled()
            coef = np.linalg.lstsq(np.vstack([X*np.sqrt(weights[:, None]), regularizer]),
                                   np.r_[y*np.sqrt(weights), np.zeros(len(penalty))], rcond=None)[0]
            residual = y-X@coef
            scatter = 1.4826*np.median(np.abs(residual-np.median(residual)))
            if iteration == robust_iterations or scatter <= np.finfo(float).eps*max(1., np.max(np.abs(y))):
                break
            weights = base/np.maximum(np.abs(residual)/(2*scatter), 1.)
        return coef

    for b in range(len(edges)-1):
        check_cancelled()
        means, widths, population = np.zeros(segments), np.zeros(segments), np.zeros(segments)
        for j in range(segments):
            check_cancelled()
            key = b*segments+j
            values = unit.ravel()[ids[cuts[key]:cuts[key+1]]]
            if values.size < min_pixels:
                continue
            population[j] = values.size
            means[j] = values.mean()
            widths[j] = values.std() if width_function == 'std' else 1.4826*np.median(np.abs(values-np.median(values)))
        if np.count_nonzero(population) < 3:
            continue
        # A single sample constrains a mean, but not a measured spread. Never
        # turn its undefined width into an almost-zero log-width observation.
        width_population = np.where(population >= 2, population, 0)
        if np.count_nonzero(width_population) < 3:
            continue
        positive = widths[(width_population > 0) & (widths > 0)]
        typical = float(np.median(positive)) if positive.size else 0.
        floors[b] = max(width_floor*typical, np.finfo(float).eps)
        models[0, b] = fit(means, population)
        # Model log-width, guaranteeing a positive interpolated divisor.
        models[1, b] = fit(np.log(np.maximum(widths, floors[b])), width_population)
    present = np.flatnonzero(np.isfinite(floors))
    for run in np.split(present, np.flatnonzero(np.diff(present) > 1)+1):
        check_cancelled()
        if not run.size:
            continue
        local = models[:, run].copy()
        if smooth_px and len(run) > 1:
            # Log bins have variable spacing: smooth on a uniform physical grid.
            spacing = max(float(np.min(np.diff(centers[run]))), .25)
            grid = np.linspace(centers[run[0]], centers[run[-1]], max(2, int(np.ceil(np.ptp(centers[run])/spacing))+1))
            for family in (0, 1):
                check_cancelled()
                for k in range(local.shape[-1]):
                    check_cancelled()
                    profile = np.interp(grid, centers[run], local[family, :, k])
                    profile = gaussian_filter1d(profile, smooth_px/(grid[1]-grid[0]), mode='nearest')
                    local[family, :, k] = np.interp(centers[run], grid, profile)
        target = observed & (bins >= run[0]) & (bins <= run[-1])
        targets = np.flatnonzero(target)
        attenuation = np.array([np.linspace(1., mean_tail, order+1),
                                np.linspace(1., width_tail, order+1)])
        if cutoff:
            attenuation[:, -cutoff:] = 0
        for first in range(0, targets.size, 32768):
            check_cancelled()
            selected = targets[first:first+32768]
            rr, tt = r.ravel()[selected], theta.ravel()[selected]
            # Share radial interpolation and angular bases across both families.
            nodes = centers[run]
            if len(run) == 1:
                coefficients = np.broadcast_to(local[:, :1, :], (2, rr.size, local.shape[-1]))
            else:
                position = np.clip(rr, nodes[0], nodes[-1])
                left = np.clip(np.searchsorted(nodes, position, side='right')-1, 0, len(nodes)-2)
                slopes = (local[:, left+1, :]-local[:, left, :]) / (nodes[left+1]-nodes[left])[None, :, None]
                coefficients = local[:, left, :]+slopes*(position-nodes[left])[None, :, None]
            mean, log_width = np.zeros(rr.size), np.zeros(rr.size)
            for k in range(local.shape[-1]):
                check_cancelled()
                harmonic = (k+1)//2
                basis = 1. if k == 0 else (np.cos(harmonic*tt) if k % 2 else np.sin(harmonic*tt))
                mean += coefficients[0, :, k]*basis*attenuation[0, harmonic]
                # The log-width DC term sets units and is never attenuated.
                factor = 1. if k == 0 else attenuation[1, harmonic]
                log_width += coefficients[1, :, k]*basis*factor
            floor = np.interp(rr, nodes, floors[run])
            width = np.maximum(np.exp(np.clip(log_width, -700, 700)), floor)
            output.ravel()[selected] = (unit.ravel()[selected]-mean)/width
    return output
