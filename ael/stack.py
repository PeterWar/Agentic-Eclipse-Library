"""Linear CFA/RGB stacking with explicit, frozen calibration and registration.

All affine matrices map reference pixel centres to input pixel centres. CFA samples
are interpolated once, directly onto the union canvas. No demosaicing, auto crop,
cloud fitting, registration guess or saturation reconstruction is hidden here.
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from . import calibrate, io
from .filters import normalized_gaussian
from .geometry import EclipseGeometry


def smoothstep(x, lo, hi):
    if not hi > lo:
        raise ValueError("smoothstep requires hi > lo")
    q = np.clip((x - lo) / (hi - lo), 0, 1)
    return q * q * (3 - 2 * q)


def full_resolution_affine(matrix):
    """Half-resolution superpixel registration -> full-resolution pixel centres.

    A half-resolution sample is centred at (2*x + .5, 2*y + .5).
    Apply the returned matrix directly to (x,y); never subtract .5 again.
    """
    m = affine(matrix).copy()
    m[:, 2] = 2 * m[:, 2] + .5 - m[:, :2] @ np.array([.5, .5])
    return m


def affine(value):
    m = np.asarray(value, np.float64)
    if m.shape != (2, 3) or not np.isfinite(m).all() or abs(np.linalg.det(m[:, :2])) < 1e-8:
        raise ValueError("reference_to_input must be a finite, invertible 2x3 affine")
    return m


def union_canvas(shapes, matrices):
    """Full union of sensor footprints, with no extra half-pixel in the mapping."""
    points = []
    for (h, w), matrix in zip(shapes, matrices):
        m = affine(matrix)
        corners = np.array([[-.5, -.5], [w-.5, -.5], [-.5, h-.5], [w-.5, h-.5]])
        points.append((corners - m[:, 2]) @ np.linalg.inv(m[:, :2]).T)
    p = np.concatenate(points)
    origin = np.floor(p.min(axis=0) + .5).astype(int)
    end = np.ceil(p.max(axis=0) + .5).astype(int)
    return (int(end[1]-origin[1]), int(end[0]-origin[0])), tuple(map(int, origin))


def hot_pixel_mask(planes, *, threshold=6.0, persistence=.8, read_noise_dn=3.0,
                   gain_e_per_dn=1.0):
    """Persistent signed outliers, normalised by LOCAL shot/read/texture noise.

    Input: same CFA plane in >=3 dithered exposures. Never use on a stationary
    scene: unresolved stars would be indistinguishable from fixed sensor defects.
    Pixels are rejected, not replaced. NaN/saturated samples do not vote.
    """
    if len(planes) < 3 or threshold <= 0 or not .5 < persistence <= 1:
        raise ValueError("hot pixels require >=3 frames, threshold >0 and persistence in (.5,1]")
    if not np.isfinite([read_noise_dn, gain_e_per_dn]).all() or read_noise_dn < 0 or gain_e_per_dn <= 0:
        raise ValueError('read_noise_dn >=0 and gain_e_per_dn >0 required')
    pos = np.zeros(planes[0].shape, np.uint16)
    neg = np.zeros_like(pos); count = np.zeros_like(pos)
    for p in planes:
        p = np.asarray(p, np.float32)
        ok = np.isfinite(p)
        a = np.where(ok, p, 0)
        med = cv2.medianBlur(a, 3)
        residual = a - med
        local = 1.4826 * cv2.medianBlur(np.abs(residual), 5)
        sigma = np.maximum(local, np.sqrt(np.maximum(med, 0) / gain_e_per_dn + read_noise_dn**2))
        good = ok & (cv2.boxFilter(ok.astype(np.float32), -1, (5, 5),
                                 borderType=cv2.BORDER_CONSTANT) > .999)
        z = residual / np.maximum(sigma, 1e-6)
        pos += good & (z > threshold); neg += good & (z < -threshold); count += good
    return (count >= 3) & (np.maximum(pos, neg) >= persistence * count)


def _path(base, value):
    p = Path(value).expanduser()
    return p if p.is_absolute() else base / p


def _field(value, base, shape, name, *, positive=False):
    a = io.load_array(_path(base, value)) if isinstance(value, str) else np.asarray(value, np.float32)
    try:
        a = np.broadcast_to(a, shape)
    except ValueError as e:
        raise ValueError(f"{name}: expected scalar or native input shape {shape}") from e
    if not np.isfinite(a).all() or (positive and (a <= 0).any()):
        raise ValueError(f"{name} must be finite" + (" and positive" if positive else ""))
    return a


def _read(frame, base):
    p = _path(base, frame['path'])
    kind = frame.get('kind', 'raw')
    if kind == 'raw':
        raw = calibrate.read_raw(p, full=False)
        return raw['bayer'].astype(np.float32), raw['pattern']
    a = np.asarray(io.load_array(p), np.float32)
    if kind == 'bayer':
        pat = np.asarray(frame['pattern'])
        if a.ndim != 2 or pat.shape != (2, 2) or sorted(pat.ravel()) != ['B', 'G', 'G', 'R']:
            raise ValueError("bayer input needs a 2D mosaic and an RGB Bayer pattern")
        return a, pat
    if kind == 'rgb' and a.ndim == 3 and a.shape[-1] == 3:
        return a, None
    raise ValueError("kind must be raw, bayer, or rgb (linear sensor DN, HxWx3)")


def _prepare(frame, base):
    raw, pat = _read(frame, base)
    shape = raw.shape
    black = _field(frame['black'], base, shape, 'black')
    white = _field(frame['white'], base, shape, 'white')
    if np.any(white <= black):
        raise ValueError('white must exceed black')
    dark = _field(frame.get('dark', frame['black']), base, shape, 'dark')
    flat = _field(frame.get('flat', 1), base, shape, 'flat', positive=True)
    transmission = _field(frame.get('transmission', 1), base, shape, 'transmission', positive=True)
    background = _field(frame.get('background', 0), base, shape, 'background')
    exposure = float(frame['exposure_s'])
    scale = float(frame.get('flux_scale', 1))
    if not np.isfinite(exposure * scale) or exposure <= 0 or scale <= 0:
        raise ValueError('exposure_s and flux_scale must be finite and positive')
    # Background is a native DN/s field after dark/flat; transmission is dimensionless.
    value = ((raw - dark) / flat / exposure - background) / (scale * transmission)
    frac = float(frame.get('linearity_fraction', .95))
    if not 0 < frac <= 1:
        raise ValueError('linearity_fraction must be in (0,1]')
    ratio = (raw - black) / (frac * (white - black))
    return value.astype(np.float32), ratio.astype(np.float32), pat


def _remap(a, x, y):
    return cv2.remap(np.ascontiguousarray(a, np.float32), x, y, cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def resample_frame(value, ratio, pattern, x, y, *, hot=None, taper_start=.8):
    """One interpolation of observed CFA planes (or RGB), one taper for ALL colours.

    Geometric support is independent of the saturation taper. Saturation and hot
    pixels are excluded before interpolation; the taper never enters its numerator.
    """
    if pattern is None:
        planes = [(k, value[..., k], ratio[..., k], 0, 0, 1) for k in range(3)]
    else:
        planes = [('RGB'.index(pattern[oy, ox]), value[oy::2, ox::2], ratio[oy::2, ox::2], ox, oy, 2)
                  for oy in range(2) for ox in range(2)]
    nums = [np.zeros_like(x) for _ in range(3)]
    dens = [np.zeros_like(x) for _ in range(3)]
    counts = [0, 0, 0]
    maximum = np.zeros_like(x)
    geometric = np.ones_like(x)
    for i, (c, a, r, ox, oy, step) in enumerate(planes):
        xx = ((x-ox)/step).astype(np.float32); yy = ((y-oy)/step).astype(np.float32)
        finite = np.isfinite(a) & np.isfinite(r)
        good = finite & (r < 1)
        if hot is not None:
            good &= ~hot[i]
        nums[c] += _remap(np.where(good, a, 0), xx, yy)
        den = _remap(good, xx, yy)
        dens[c] += den; counts[c] += 1
        footprint = _remap(np.ones_like(a), xx, yy)
        geometric = np.minimum(geometric, footprint)
        ratio_good = finite if hot is None else finite & ~hot[i]
        ratio_support = _remap(ratio_good, xx, yy)
        rr = _remap(np.where(ratio_good, np.maximum(r, 0), 0), xx, yy) / np.maximum(ratio_support, 1e-12)
        maximum = np.maximum(maximum, rr)
    support = np.minimum.reduce([d/n for d, n in zip(dens, counts)])
    result = np.stack([n/np.maximum(d, 1e-12) for n, d in zip(nums, dens)], axis=-1)
    taper = 1 - smoothstep(maximum, taper_start, 1)
    return result, support, geometric, taper


def stack_from_config(config_path, out_dir, *, progress=print):
    """Run a frozen stack recipe. Relative paths resolve against the JSON file.

    Single optical train/ISO only. Mixed optics must be distortion-corrected
    before input; no free affine can replace a calibrated distortion model.
    """
    config_path = Path(config_path).resolve(); base = config_path.parent
    cfg = json.loads(config_path.read_text())
    def keys(obj, allowed, label):
        unknown = set(obj) - set(allowed.split())
        if unknown: raise ValueError(f'unknown {label} keys: {sorted(unknown)}')
    keys(cfg, 'frames geometry stack note', 'recipe')
    frames = cfg['frames']
    if not frames:
        raise ValueError('frames cannot be empty')
    if len({str(f.get('train', 'one')) for f in frames}) > 1 or len({f['iso'] for f in frames}) > 1:
        raise ValueError('stack one optical train and one ISO at a time')
    matrices = [affine(f['reference_to_input']) for f in frames]
    geo = EclipseGeometry.from_json(cfg['geometry'])
    if not np.isfinite(geo.sun_radius_px) or geo.sun_radius_px <= 0 or not np.isfinite(geo.sun_xy).all():
        raise ValueError('solar geometry must be finite with a positive radius')
    settings = cfg.get('stack', {})
    keys(settings, 'taper_start band_sigma_px clouds hot_pixels moon_guard_px limb_fade_px gain_e_per_dn read_noise_dn', 'stack')
    for f in frames:
        keys(f, 'path kind pattern iso train exposure_s black white dark flat transmission background flux_scale '
             'linearity_fraction reference_to_input moon_xy moon_radius_px cirrus_fraction note', 'frame')
    taper_start = float(settings.get('taper_start', .8))
    if not 0 < taper_start < 1:
        raise ValueError('taper_start must be in (0,1)')
    band_sigma = float(settings.get('band_sigma_px', 0))
    if not np.isfinite(band_sigma) or band_sigma < 0:
        raise ValueError('band_sigma_px must be finite and >=0')
    gain = float(settings.get('gain_e_per_dn', 1))
    noise = float(settings.get('read_noise_dn', 3))
    guard = float(settings.get('moon_guard_px', 2))
    fade = float(settings.get('limb_fade_px', 4))
    if not np.isfinite([gain, noise, guard, fade]).all() or gain <= 0 or min(noise, guard) < 0 or fade <= 0:
        raise ValueError('finite gain >0, read noise >=0, moon guard >=0 and limb fade >0 required')
    if settings.get('clouds', False):
        if band_sigma <= 0 or any(not isinstance(f.get('transmission'), str) or
                                  'background' not in f or 'cirrus_fraction' not in f for f in frames):
            raise ValueError('clouds require two bands and frozen spatial transmission/background/cirrus per frame')
    hp = settings.get('hot_pixels', {})
    keys(hp, 'enabled dithered threshold persistence read_noise_dn gain_e_per_dn', 'hot_pixels')
    if hp.get('enabled') and not hp.get('dithered'):
        raise ValueError('hot-pixel inference requires an explicitly confirmed dithered sequence')
    # Validate all inputs before creating any output. Stream them again for stacking.
    shapes, patterns = [], []
    for f in frames:
        v, r, pat = _prepare(f, base)
        if v.shape[:2] != tuple(geo.shape) and f is frames[0]:
            raise ValueError('geometry.shape must describe the first/reference input')
        if 'moon_xy' not in f or not np.isfinite(float(f['moon_radius_px'])) or float(f['moon_radius_px']) <= 0:
            raise ValueError('each frame needs its native moon_xy and moon_radius_px')
        if not np.isfinite(f['moon_xy']).all() or len(f['moon_xy']) != 2:
            raise ValueError('moon_xy must contain two finite coordinates')
        cirrus = float(f.get('cirrus_fraction', 0))
        if not np.isfinite(cirrus) or cirrus < 0:
            raise ValueError('cirrus_fraction must be finite and nonnegative')
        shapes.append(v.shape[:2]); patterns.append(None if pat is None else pat.tolist())
    del v, r
    if any(p != patterns[0] for p in patterns):
        raise ValueError('CFA patterns must agree within a train')
    shape, origin = union_canvas(shapes, matrices)
    outgeo = geo.shifted(-origin[0], -origin[1], shape)
    hot = None
    if hp.get('enabled'):
        if len(set(shapes)) != 1:
            raise ValueError('hot-pixel inference requires equal native input shapes')
        # One plane at a time bounds memory. Sensor DN, not exposure-normalised.
        hot = []
        nplanes = 3 if patterns[0] is None else 4
        for k in range(nplanes):
            samples = []
            for f in frames:
                raw, pat = _read(f, base)
                black = _field(f['black'], base, raw.shape, 'black')
                white = _field(f['white'], base, raw.shape, 'white')
                a = raw-black
                a[raw >= black + float(f.get('linearity_fraction', .95))*(white-black)] = np.nan
                p = a[..., k] if pat is None else a[k//2::2, k%2::2]
                samples.append(p.copy())
            hot.append(hot_pixel_mask(samples, threshold=float(hp.get('threshold', 6)),
                                      persistence=float(hp.get('persistence', .8)),
                                      read_noise_dn=float(hp.get('read_noise_dn', 3)),
                                      gain_e_per_dn=float(hp.get('gain_e_per_dn', 1))))
            del samples, raw, a
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=False)
    h, w = shape
    # Float64 accumulators avoid order-dependent loss in HDR exposure ladders.
    numerator = np.zeros((h,w,3), np.float64); denominator = np.zeros((h,w), np.float64)
    coarse_num = np.zeros_like(numerator) if band_sigma else None
    coarse_den = np.zeros_like(denominator) if band_sigma else None
    support_sum = np.zeros((h,w), np.float32); footprint_sum = np.zeros_like(support_sum)
    distance = np.full((h,w), -np.inf, np.float32)
    y, x = np.mgrid[:h,:w].astype(np.float32)
    x += origin[0]; y += origin[1]
    frame_reports = []
    for index, (f, matrix) in enumerate(zip(frames, matrices)):
        progress(f"stack {index+1}/{len(frames)}: {Path(f['path']).name}")
        value, ratio, pat = _prepare(f, base)
        xx = (matrix[0,0]*x+matrix[0,1]*y+matrix[0,2]).astype(np.float32)
        yy = (matrix[1,0]*x+matrix[1,1]*y+matrix[1,2]).astype(np.float32)
        rgb, support, footprint, taper = resample_frame(value, ratio, pat, xx, yy, hot=hot,
                                                       taper_start=taper_start)
        d = np.hypot(xx-f['moon_xy'][0], yy-f['moon_xy'][1])-float(f['moon_radius_px'])
        support = np.where(d > guard, support, 0)
        distance = np.maximum(distance, np.where(footprint >= .5, d, -np.inf))
        # The support threshold NEVER contains the limb ramp or exposure taper.
        support_sum += np.where(support >= .5, support, 0)
        footprint_sum += footprint
        ramp = smoothstep(d, guard, guard+fade)
        wt = np.where(support >= .5, support*taper*ramp, 0).astype(np.float32)
        fine_weight = wt * float(f['exposure_s'])
        if band_sigma:
            good = (support >= .5) & (taper > 0)
            low = np.stack([normalized_gaussian(rgb[...,c], good, band_sigma, min_support=.01)
                            for c in range(3)], axis=-1)
            good &= np.isfinite(low).all(axis=-1)
            fine_weight = np.where(good, fine_weight, 0)
            low = np.nan_to_num(low)
            cirrus = float(f.get('cirrus_fraction', 0))
            lum = np.maximum((rgb[...,0]+2*rgb[...,1]+rgb[...,2])/4, 1e-6)
            eff = float(f['exposure_s'])*float(f.get('flux_scale',1))
            variance = (lum/(gain*eff)+(noise/eff)**2)/(4*np.pi*band_sigma**2)+(cirrus*lum)**2
            cw = np.where(good, wt/np.maximum(variance,1e-12), 0)
            coarse_num += cw[...,None]*low; coarse_den += cw
            rgb = rgb-low
        numerator += fine_weight[...,None]*rgb
        denominator += fine_weight
        frame_reports.append(dict(observed_pixels=int((support>=.5).sum()),
                                  weighted_pixels=int((fine_weight>0).sum())))
    valid = (support_sum >= .5) & (denominator > 0)
    result = numerator/np.maximum(denominator[...,None],1e-30)
    if band_sigma:
        valid &= coarse_den > 0
        result += coarse_num/np.maximum(coarse_den[...,None],1e-30)
    result[~valid] = np.nan
    result = result.astype(np.float32)
    alpha = np.where(valid, smoothstep(distance, guard, guard+fade), 0).astype(np.float32)
    files = {}
    for name, a in [('linear', result), ('valid', valid), ('support', support_sum),
                    ('coverage', footprint_sum), ('weight', denominator.astype(np.float32)), ('alpha', alpha)]:
        p = out/f'{name}.npy'; np.save(p,a); files[name] = p
    files['tiff'] = io.save_tiff(out/'linear.tif', result, description='Linear sensor RGB in DN/s; invalid pixels NaN')
    outgeo.to_json(out/'geometry.json'); files['geometry'] = out/'geometry.json'
    inputs = {'config':config_path}
    for n,f in enumerate(frames):
        inputs[f'frame_{n}'] = _path(base,f['path'])
        for key in ('black','white','dark','flat','transmission','background'):
            if isinstance(f.get(key),str): inputs[f'{key}_{n}'] = _path(base,f[key])
    colour = np.nanmedian(result[valid],axis=0) if valid.any() else np.zeros(3)
    gates = {'observed_support': bool(valid.any()), 'nothing_outside_data': bool(np.isnan(result[~valid]).all())}
    receipt = io.write_receipt(out/'receipt.json', product='linear stack', inputs=inputs, outputs=files,
        parameters=dict(recipe=cfg, origin_reference_xy=origin, frames=frame_reports,
                        hot_pixels_per_plane=[] if hot is None else [int(a.sum()) for a in hot],
                        median_rgb_dn_per_s=colour.tolist(), colour_region='all valid pixels, unbalanced sensor RGB'),
        gates=gates, notes='One train/ISO. Frozen registration and calibrations. No automatic cloud fitting. '
        'Coverage is geometric, support excludes saturation. No saturated-pixel reconstruction. '
        'No absolute photometry, uncertainty budget or scientific validation implied.')
    if not valid.any():
        raise ValueError(f'no observed output pixels; diagnostics retained at {receipt}')
    return dict(files={k:str(v) for k,v in files.items()},receipt=str(receipt),shape=shape)
