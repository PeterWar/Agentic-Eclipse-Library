"""Observed-support angular Gaussian detail, with an untouched Cartesian base.

Independent implementation of angular unsharp masking. A bounded radial tile
keeps memory independent of the size of the complete polar canvas. Only detail
is resampled; missing or off-frame samples carry zero statistical weight.
"""
from .cancellation import check_cancelled
import numpy as np
from scipy.ndimage import map_coordinates, gaussian_filter1d
from scipy.fft import rfft, irfft
import os


FFT_MIN_RADIUS = 32

def tangential_detail(image, cx, cy, radius, arc_sigma_deg=3., gain=1.,
                      denoise=0., inner_radius=1., outer_radius=0., fade_px=8., valid=None):
    a = np.asarray(image, dtype=float)
    if a.ndim != 2 or not a.size:
        raise ValueError('Tangential detail needs a nonempty 2D image')
    values = [cx, cy, radius, arc_sigma_deg, gain, denoise, inner_radius, outer_radius, fade_px]
    if not np.isfinite(values).all() or radius <= 0 or not .1 <= arc_sigma_deg <= 30 or gain < 0 or denoise < 0 or inner_radius < 0 or outer_radius < 0 or fade_px < 0:
        raise ValueError('Invalid tangential geometry or parameters')
    if outer_radius and outer_radius <= inner_radius:
        raise ValueError('Tangential outer radius must exceed inner radius')
    mask = np.isfinite(a)
    if valid is not None:
        if np.shape(valid) != a.shape:
            raise ValueError('Tangential validity must match image')
        mask &= valid
    if not mask.any():
        raise ValueError('Tangential detail needs observed samples')
    yy, xx = np.indices(a.shape, dtype=float)
    r = np.hypot(xx-cx, yy-cy)
    angle = np.arctan2(yy-cy, xx-cx) % (2*np.pi)
    domain = mask & (r >= inner_radius*radius)
    if outer_radius:
        domain &= r < outer_radius*radius
    detail = np.zeros(a.shape, dtype=float)
    maximum = float(r.max())
    na = max(128, 4*int(np.ceil(2*np.pi*maximum/4)))
    # Avoid silently capping angular resolution and aliasing large images.
    if na > 131072:
        raise ValueError('Tangential angular grid too large; reduce image dimensions')
    phi = np.arange(na, dtype=float)*(2*np.pi/na)
    sine, cosine = np.sin(phi)[:, None], np.cos(phi)[:, None]
    signal = np.where(mask, a, 0)
    support = mask.astype(float)
    sigma = arc_sigma_deg/360*na
    # Preserve the finite truncate=3 kernel, rather than an ideal spectral Gaussian.
    kernel_radius = int(3*sigma+.5)
    spectrum = None
    if kernel_radius >= FFT_MIN_RADIUS:
        offsets = np.arange(-kernel_radius, kernel_radius+1)
        weights = np.exp(-.5*(offsets/sigma)**2)
        weights /= weights.sum()
        kernel = np.zeros(na)
        np.add.at(kernel, offsets % na, weights)
        spectrum = rfft(kernel)[:, None]
    def angular_blur(values):
        check_cancelled()
        if spectrum is None:
            return gaussian_filter1d(values, sigma, axis=0, mode='wrap', truncate=3.)
        workers = min(4, os.cpu_count() or 1)
        return irfft(rfft(values, axis=0, workers=workers)*spectrum,
                     n=na, axis=0, workers=workers)
    active_rows = np.flatnonzero(domain)
    # Partition Cartesian targets once, avoiding a full-canvas scan per tile.
    tiles = (r.ravel()[active_rows]//128).astype(int)
    order = np.argsort(tiles, kind='stable')
    active_rows, tiles = active_rows[order], tiles[order]
    cuts = np.r_[0, np.flatnonzero(np.diff(tiles))+1, len(tiles)]
    for start, stop in zip(cuts[:-1], cuts[1:]):
        check_cancelled()
        if stop == start:
            continue
        tile = tiles[start]
        first = max(0, tile*128-1)
        radii = np.arange(first, (tile+1)*128+2, dtype=float)[None, :]
        Y, X = cy+radii*sine, cx+radii*cosine
        inside = (Y >= -1e-7) & (Y <= a.shape[0]-1+1e-7) & (X >= -1e-7) & (X <= a.shape[1]-1+1e-7)
        coordinates = [np.clip(Y, 0, a.shape[0]-1), np.clip(X, 0, a.shape[1]-1)]
        w = map_coordinates(support, coordinates, order=1, mode='nearest', prefilter=False)*inside
        v = map_coordinates(signal, coordinates, order=1, mode='nearest', prefilter=False)*inside
        sw = angular_blur(w)
        sv = angular_blur(v)
        mean = np.divide(sv, sw, out=np.zeros_like(v), where=sw > .05)
        original = np.divide(v, w, out=np.zeros_like(v), where=w > 0)
        d = np.where((w >= 1-1e-6) & (sw > .05), original-mean, 0)
        target = active_rows[start:stop]
        coords = [angle.ravel()[target]*na/(2*np.pi), r.ravel()[target]-first]
        periodic = np.concatenate([d, d[:1]], axis=0)
        detail.ravel()[target] = map_coordinates(periodic, coords, order=1, mode='nearest', prefilter=False)
    if denoise:
        # Robust high-pass estimate on observed adjacent pairs; not detector SNR.
        differences = np.diff(signal, axis=1)
        pairs = mask[:, 1:] & mask[:, :-1]
        samples = differences[pairs]
        noise = (1.4826*np.median(np.abs(samples-np.median(samples)))/np.sqrt(2)) if samples.size else 0.
        detail = np.sign(detail)*np.maximum(np.abs(detail)-denoise*noise, 0)
    ramp = np.ones_like(a)
    if fade_px:
        ramp = np.clip((r-inner_radius*radius)/fade_px, 0, 1)
        if outer_radius:
            ramp *= np.clip((outer_radius*radius-r)/fade_px, 0, 1)
        ramp = ramp*ramp*(3-2*ramp)
    result = a.copy()
    result[domain] += gain*detail[domain]*ramp[domain]
    return result.astype(np.float32)
