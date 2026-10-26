"""Global continuous radial ranks, using measured positive samples only.

Quantile distributions are interpolated, not image pixels. Inspired by AEL's
continuous radial statistics (Pere Guerra Serra, MIT); implemented independently
for the global case. Output units are ranks [0, 1]; undefined pixels are NaN.
"""
from .cancellation import check_cancelled
import numpy as np


def rhef_continuous_normalize(image, radii, bin_px=2., application_radius=0.,
                              valid=None, min_count=12, quantile_count=257):
    a = np.asarray(image, dtype=np.float64)
    r = np.asarray(radii, dtype=np.float64)
    if a.ndim != 2 or a.shape != r.shape or not a.size:
        raise ValueError("Image and radii must be matching nonempty 2D arrays")
    if not np.isfinite([bin_px, application_radius]).all() or bin_px <= 0 or application_radius < 0:
        raise ValueError("Invalid radial bounds")
    if not isinstance(min_count, (int, np.integer)) or min_count < 2:
        raise ValueError("Minimum population must be an integer >= 2")
    if not isinstance(quantile_count, (int, np.integer)) or quantile_count < 3:
        raise ValueError("At least three quantiles are required")
    mask = np.isfinite(a) & (a > 0) & np.isfinite(r) & (r >= application_radius)
    if valid is not None:
        if np.shape(valid) != a.shape:
            raise ValueError("Valid mask must match image")
        mask &= np.asarray(valid, dtype=bool)
    out = np.full(a.shape, np.nan)
    ids = np.flatnonzero(mask)
    if not ids.size:
        return out
    rr = r.ravel()[ids]
    first = int(np.floor(rr.min() / bin_px))
    bins = np.floor(rr / bin_px).astype(np.int64) - first
    counts = np.bincount(bins)
    table = np.full((len(counts), quantile_count), np.nan)
    order = np.argsort(bins, kind="stable")
    cuts = np.r_[0, np.cumsum(counts)]
    values = np.log(a.ravel()[ids])
    probabilities = np.linspace(0, 1, quantile_count)
    for k in np.flatnonzero(counts >= min_count):
        check_cancelled()
        table[k] = np.quantile(values[order[cuts[k]:cuts[k + 1]]], probabilities)
    # Interpolate immediate neighbours only. An empty/sparse ring stays undefined;
    # a neighbour never validates it and no interpolation bridges a gap.
    eligible = counts[bins] >= min_count
    for start in range(0, ids.size, 16384):
        check_cancelled()
        use = np.arange(start, min(start + 16384, ids.size))
        use = use[eligible[use]]
        if not use.size:
            continue
        position = np.clip(rr[use] / bin_px - .5 - first, 0, len(counts) - 1)
        left = np.floor(position).astype(int)
        right = np.minimum(left + 1, len(counts) - 1)
        weight = position - left
        wl = (1 - weight) * np.isfinite(table[left, 0])
        wr = weight * np.isfinite(table[right, 0])
        mass = wl + wr
        # At exact node positions the current cell is always populated.
        good = mass > 0
        use, left, right, wl, wr, mass = (v[good] for v in (use, left, right, wl, wr, mass))
        def threshold(index):
            return (np.nan_to_num(table[left, index]) * wl +
                    np.nan_to_num(table[right, index]) * wr) / mass

        def insertion(side):
            lo = np.zeros(len(use), dtype=int)
            hi = np.full(len(use), quantile_count, dtype=int)
            for _ in range(int(quantile_count).bit_length()):
                check_cancelled()
                mid = (lo + hi) // 2
                value = threshold(np.minimum(mid, quantile_count - 1))
                active = lo < hi
                advance = value <= values[use] if side == "right" else value < values[use]
                lo = np.where(active & advance, mid + 1, lo)
                hi = np.where(active & ~advance, mid, hi)
            return lo

        lower, upper = insertion("left"), insertion("right")
        k = np.clip(lower - 1, 0, quantile_count - 2)
        lo, hi = threshold(k), threshold(k + 1)
        fraction = np.divide(values[use] - lo, hi - lo,
                             out=np.zeros(len(use)), where=hi > lo)
        ranks = (k + np.clip(fraction, 0, 1)) / (quantile_count - 1)
        # Exact ties take the midpoint of their quantile interval. In particular
        # a constant distribution maps to .5, independently of its population.
        ties = upper > lower
        ranks[ties] = (lower[ties] + upper[ties] - 1) / (2 * (quantile_count - 1))
        out.ravel()[ids[use]] = ranks
    return out
