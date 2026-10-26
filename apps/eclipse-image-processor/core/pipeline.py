"""Independent layer composition and a numerical dispatcher limited to one filter."""
import time
from .cancellation import check_cancelled
from copy import deepcopy
import numpy as np


def prepare_parameters(parameters, full_shape, preview_shape, target_shape):
    """Geometry and MGN sigmas use full-res pixels; other spatial controls use preview pixels.

    Scale X/Y independently using OpenCV's pixel-centre convention. Circular
    radii and kernels use the geometric mean scale for rounded aspect ratios.
    FNRGF ring widths are target-image pixels, independent of preview resizing.
    """
    shapes = (full_shape, preview_shape, target_shape)
    if any(len(shape) != 2 or not np.isfinite(shape).all() or min(shape) <= 0 for shape in shapes):
        raise ValueError("Resolution shapes must contain two positive finite dimensions")
    p = deepcopy({key: value for key, value in parameters.items()
                  if not key.startswith(("pre_stretch", "noise_gate", "bilateral"))})
    sy, sx = target_shape[0] / full_shape[0], target_shape[1] / full_shape[1]
    p["sx"] = (p["sx"] + .5) * sx - .5
    p["sy"] = (p["sy"] + .5) * sy - .5
    p["sr"] *= float(np.sqrt(sx * sy))
    scale = float(np.sqrt(target_shape[0] / preview_shape[0] * target_shape[1] / preview_shape[1]))
    p["spatial_scale"] = scale
    p["achf_ael_scale"] = float(np.sqrt(sx * sy))
    p["nrgf_scale"] = float(np.sqrt(sx * sy))
    for key in ("achf_kernel", "rhef_bin_px",
                "fnrgf_smooth", "fnrgf_fade", "tangential_fade", "larson_sekanina_radial", "statistics_guard_px"):
        if key in p:
            p[key] *= scale
    if "fnrgf_bin_px" in p:
        from utils.helpers import recommended_radial_bins
        p["fnrgf_nbins"] = recommended_radial_bins(
            p.get("fnrgf_rad", 10) / 10.0 * p["sr"],
            p.get("fnrgf_rmax", 30) / 10.0 * p["sr"],
            logarithmic=p.get("fnrgf_radial_binning", "linear") == "log",
            width_px=p["fnrgf_bin_px"],
        )
    elif "fnrgf_nbins" in p:
        # Compatibility with callers supplying the former preview-count control.
        p["fnrgf_nbins"] = max(1, int(round(p["fnrgf_nbins"] * scale)))
    if "wow_scales" in p or p.get("wow_enabled", False):
        # Starlet supports are dyadic: choose the nearest available footprint.
        reference_shape = full_shape if p.get('wow_native_scales', False) else preview_shape
        preview_max = max(1, int(np.round(np.log2(min(reference_shape) / 5.0))))
        target_max = max(1, int(np.round(np.log2(min(target_shape) / 5.0))))
        requested = p.get("wow_scales")
        count = preview_max if requested in (None, 0) else min(int(requested), preview_max)
        wavelet_scale = float(np.sqrt(target_shape[0]/reference_shape[0]*target_shape[1]/reference_shape[1]))
        offset = int(np.floor(np.log2(wavelet_scale) + 0.5))
        p["wow_scales"] = int(np.clip(count + offset, 1, target_max))
        if p.get('wow_mode') == 'ael_bilateral':
            p['wow_scales'] = int(np.clip(int(requested or 6) + offset, 1, 10))
        levels = list(p.get("wow_denoise", []))
        if levels:
            # Keep thresholds attached to the same physical bands. Newly added
            # fine bands inherit the finest threshold instead of disabling noise control.
            levels = [levels[0]] * offset + levels if offset >= 0 else levels[-offset:]
            p["wow_denoise"] = levels[:p["wow_scales"]]
    p["mgn_sigmas"] = tuple(s * p["achf_ael_scale"] for s in p.get("mgn_sigmas", (1.25, 2.5, 5, 10, 20, 40)))
    return p


def execute_pipeline(worker, raw_image, params):
    """Compose independent layers; every layer reads the original source."""
    from .layer_engine import engine_for
    return engine_for(worker).render(worker,raw_image,params,params.get('layer_display',{}))


def apply_filter(worker, raw_image, params, *, process_label='FILTER', verbose=True):
    """Run at most one numerical operator, retaining masks and source intensity units.

    This is called by LayerEngine when building a layer, never a chain of filters.
    Multiple enabled operators are rejected before touching the input or worker.
    """
    from .layer_engine import ORDER
    active = [name for name in (*ORDER, 'achf') if params.get(name + '_enabled', False)]
    if len(active) > 1:
        raise ValueError('Numerical dispatch accepts only one filter; use independent layer composition')
    name = active[0] if active else None
    from .filters import finite_image, CPU_CORES
    check_cancelled()
    if raw_image is None:
        raise ValueError("No image supplied")

    pipeline_start = time.time()
    if verbose:
        print(f"\n{'='*80}\n[{process_label}] Execution start (Native Engine; {CPU_CORES} CPUs available) - Shape: {raw_image.shape}\n{'='*80}")

    p = params
    valid = p.get("valid_mask")
    if valid is not None:
        from .image_data import observed_image
        observed, valid = observed_image(raw_image, valid)
        # Zero is only a finite transport buffer. MaskedWorker excludes these
        # positions from statistics/support; restore NaN before returning data.
        img = np.where(valid, observed, 0).astype(np.float32)
        if not valid.all():
            from .masked_filters import MaskedWorker
            worker = MaskedWorker(worker, valid)
    else:
        img = finite_image(raw_image).astype(np.float32)

    if p.get('statistics_exclude_lunar', False) or p.get('statistics_exclude_bright', False) or p.get('statistics_mask') is not None:
        from .statistics_support import statistics_support, StatisticsWorker
        support = statistics_support(raw_image, p, valid) if p.get('statistics_mask') is None else np.asarray(p['statistics_mask'], dtype=bool) & np.isfinite(raw_image) & (valid if valid is not None else True)
        if support.shape != raw_image.shape or not support.any():
            raise ValueError('Statistics mask must match image and contain observations')
        from .masked_filters import MaskedWorker
        base_worker = worker.worker if isinstance(worker, MaskedWorker) else worker
        worker = StatisticsWorker(base_worker, support)

    check_cancelled()
    if name == 'nrgf':
        img = worker.run_nrgf_native(
            img, p.get('nrgf_str', 100), p['sx'], p['sy'], p['sr'],
            **{key: value for key, value in p.items()
               if key.startswith('nrgf_') and key not in ('nrgf_enabled', 'nrgf_str', 'nrgf_opacity')})

    check_cancelled()
    # FNRGF: radial normalization
    if name == 'fnrgf':
        step_start = time.time()
        img = worker.run_fnrgf_native(
            img,
            p["fnrgf_str"],
            p["fnrgf_ord"],
            p["fnrgf_seg"],
            p["fnrgf_cut"],
            p["fnrgf_rad"],
            p.get("fnrgf_rmax", 30),
            p.get("fnrgf_nbins", 100),
            p["sx"],
            p["sy"],
            p["sr"],
            width_function=p.get("fnrgf_width_func", "std"),
            radial_binning=p.get("fnrgf_radial_binning", "linear"),
            apply_mask=p.get("fnrgf_apply_mask", 0),
            mode=p.get('fnrgf_mode', 'legacy'), radial_smooth=p.get('fnrgf_smooth', 8.), boundary_fade=p.get('fnrgf_fade', 0.),
            ridge=p.get('fnrgf_ridge', .01), width_floor=p.get('fnrgf_floor', .05),
            robust_iterations=p.get('fnrgf_robust', 2), min_pixels_per_sector=p.get('fnrgf_min_pixels', 1),
            mean_attenuation_range=(1., p.get('fnrgf_mean_tail', 0.)),
            std_attenuation_range=(1., p.get('fnrgf_width_tail', 0.)),
        )
        if verbose:
            print(f"[{process_label}: FNRGF NATIVE] Done in {time.time() - step_start:.3f}s")

    check_cancelled()
    # RHEF: radial histogram equalization
    if name == 'rhef':
        step_start = time.time()
        img = worker.run_rhef_native(
            img, p["rhef_str"], p["rhef_rad"], p["rhef_upsilon"], p["sx"], p["sy"], p["sr"],
            bin_px=p.get("rhef_bin_px", 1.0),
            mode=p.get("rhef_mode", "legacy"), upsilon_h_val=p.get('rhef_upsilon_high'),
            min_count=p.get('rhef_min_count', 12), quantile_count=p.get('rhef_quantiles', 257),
            noise_confidence=p.get('rhef_noise_confidence', 0.),
        )
        if verbose:
            print(f"[{process_label}: RHEF NATIVE] Done in {time.time() - step_start:.3f}s")

    check_cancelled()
    # MGN: multiscale Gaussian normalization
    if name == 'mgn':
        step_start = time.time()
        img = worker.run_mgn_native(
            img,
            p["mgn_str"],
            p["mgn_gam"],
            p.get("mgn_k", 70),
            p.get("mgn_h", 70),
            p.get("mgn_trunc", 3),
            sigmas=p.get("mgn_sigmas", (1.25, 2.5, 5, 10, 20, 40)),
            weights=p.get('mgn_weights'),
        )
        if verbose:
            print(f"[{process_label}: MGN NATIVE] Done in {time.time() - step_start:.3f}s")

    check_cancelled()
    # WOW: wavelet whitening
    if name == "wow" and not (p.get('wow_mode') == 'ael_bilateral' and p.get('wow_str') == 0):
        step_start = time.time()
        if p.get('wow_mode') == 'ael_bilateral':
            from .ael_wow import ael_wow_layer
            strength=float(p['wow_str'])
            if not np.isfinite(strength) or not 0 <= strength <= 100:
                raise ValueError('AEL WOW strength must be between 0 and 100')
            support=np.isfinite(raw_image) & (valid if valid is not None else True)
            if (p.get('statistics_exclude_lunar', False) or p.get('statistics_exclude_bright', False)
                    or p.get('statistics_mask') is not None):
                support &= worker.support
            layer,_=ael_wow_layer(img,p,support)
            from .layer_export import overlay
            observed=np.isfinite(layer)
            low,high=float(img[observed].min()),float(img[observed].max())
            if high > low:
                base=(img[observed]-low)/(high-low)
                img[observed]=low+(high-low)*overlay(base,layer[observed],1.,strength/100)
        else:
            img = worker.run_wow_native(
                img, p["wow_str"], p.get("wow_scales"),
                denoise_coefficients=p.get("wow_denoise", []),
                bilateral=p.get("wow_bilateral"),
            )
        if verbose:
            print(f"[{process_label}: WOW NATIVE] Done in {time.time() - step_start:.3f}s")

    check_cancelled()
    if name == 'tangential':
        step_start = time.time()
        img = worker.run_tangential(
            img, p['tangential_str'], p['sx'], p['sy'], p['sr'],
            arc_sigma=p.get('tangential_arc', 3.), gain=p.get('tangential_gain', 1.),
            denoise=p.get('tangential_denoise', 0.), inner_radius=p.get('tangential_inner', 1.),
            outer_radius=p.get('tangential_outer', 0.), fade_px=p.get('tangential_fade', 8.))
        if verbose:
            print(f"[{process_label}: TANGENTIAL DETAIL] Done in {time.time() - step_start:.3f}s")

    check_cancelled()
    if name == 'larson_sekanina':
        step_start = time.time()
        img = worker.run_larson_sekanina(
            img, p['larson_sekanina_str'], p['sx'], p['sy'], p['sr'],
            radial_increment=p.get('larson_sekanina_radial', 0.),
            angular_increment=p.get('larson_sekanina_angular', 3.))
        if verbose:
            print(f"[{process_label}: LARSON-SEKANINA] Done in {time.time() - step_start:.3f}s")

    check_cancelled()
    # ACHF: final enhancement stage
    if name == 'achf':
        step_start = time.time()
        if p.get('achf_variant', 'adaptive') in ('ael_iso_01','ael_iso_04','ael_angular_4'):
            from .ael_achf import apply_ael_achf
            support = np.isfinite(raw_image)
            if valid is not None:
                support &= valid
            if (p.get('statistics_exclude_lunar', False) or p.get('statistics_exclude_bright', False)
                    or p.get('statistics_mask') is not None):
                support &= worker.support
            img = apply_ael_achf(img, p['achf_str'], p['sx'], p['sy'], p['sr'],
                                 support, p.get('achf_ael_scale', 1.), p['achf_variant'],
                                 p.get('achf_ael_parameters'))
        elif p.get('achf_variant', 'adaptive') == 'adaptive':
            img = worker.run_achf(
                img, p["achf_str"], p["achf_kernel"], p["achf_boost"], p["sx"], p["sy"], p["sr"],
                intensity_threshold=p.get("achf_threshold", 10),
                background=p.get("achf_background", 10),
                spatial_scale=p.get("spatial_scale", 1.0),
            )
        else:
            raise ValueError('Unknown ACHF variant')
        if verbose:
            print(f"[{process_label}: ACHF {p.get('achf_variant', 'adaptive')}] Done in {time.time() - step_start:.3f}s")

    check_cancelled()
    finite_image(img)
    if verbose:
        print(f"[{process_label}] Complete. Total time: {time.time() - pipeline_start:.3f}s\n{'='*80}\n")
    if valid is not None and not valid.all():
        img = np.where(valid, img, np.nan).astype(np.float32)
    return img
