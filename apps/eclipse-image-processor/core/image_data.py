"""Observed-data masks, separate from numerical/display storage."""
import cv2
import numpy as np


def observed_image(image, valid=None):
    a = np.asarray(image, dtype=np.float64)
    if a.ndim != 2 or not a.size:
        raise ValueError('Image must be a nonempty 2D array')
    mask = np.isfinite(a) if valid is None else np.asarray(valid, dtype=bool)
    if mask.shape != a.shape or not mask.any() or not np.isfinite(a[mask]).all():
        raise ValueError('Image needs finite observed pixels and a matching validity mask')
    return np.where(mask, a, np.nan), mask


def observed_bounds(image):
    """Finite native extrema; no full-size floating copy or extracted sample array."""
    a=np.asarray(image)
    valid=np.isfinite(a)
    if a.ndim!=2 or not valid.any():
        raise ValueError('Display reference needs finite observed pixels in a 2D image')
    low_initial=np.iinfo(a.dtype).max if np.issubdtype(a.dtype,np.integer) else np.inf
    high_initial=np.iinfo(a.dtype).min if np.issubdtype(a.dtype,np.integer) else -np.inf
    return (float(np.min(a,where=valid,initial=low_initial)),
            float(np.max(a,where=valid,initial=high_initial)))


def normalize_observed(image, bounds=None):
    a, valid = observed_image(image)
    if bounds is None:
        values=a[valid]
        low,high=float(values.min()),float(values.max())
    else:
        if len(bounds)!=2 or not np.isfinite(bounds).all() or bounds[1]<bounds[0]:
            raise ValueError('Display reference must contain finite ordered black/white levels')
        low,high=bounds
    out = np.zeros(a.shape, dtype=np.float64)
    if high>low:
        out[valid] = np.clip((a[valid]-low)/(high-low),0,1)
    return out


def resize_observed(image, size):
    """Area-average observed samples only; conservatively keep full support.

    Partially missing preview pixels remain missing rather than mixing the lunar
    boundary with a zero fill. No reconstructed pixels are added to the source.
    """
    a, valid = observed_image(image)
    weights = cv2.resize(valid.astype(np.float32), size, interpolation=cv2.INTER_AREA)
    values = cv2.resize(np.where(valid, a, 0).astype(np.float32), size, interpolation=cv2.INTER_AREA)
    mask = weights >= 1 - 1e-6
    result = np.full(weights.shape, np.nan, dtype=np.float32)
    np.divide(values, weights, out=result, where=mask)
    return result


def recipe_parameters(params):
    """Masks are image data, stored separately, never embedded in JSON metadata."""
    return {k: v for k, v in params.items() if k not in ('valid_mask', 'statistics_mask')}


def zero_missing(image, valid=None):
    """Finite export copy; VALID, not the stored zero, identifies missing samples."""
    result=np.nan_to_num(image,nan=0.,posinf=0.,neginf=0.)
    if valid is not None:
        mask=np.asarray(valid,bool)
        if result.shape[:2]!=mask.shape:
            raise ValueError('Export validity must match image')
        result=np.where(mask[...,None] if result.ndim==3 else mask,result,0)
    return result
