#!/usr/bin/env python3
"""Automation helpers for the PixInsight AEL workflow.

MIT License
Copyright (c) 2026 Pere Guerra Serra

Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

The AEL package remains unchanged. This module measures metadata and registration,
writes declared recipes, and exports filter layers for PixInsight/PixelMath.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

import cv2
import numpy as np
import tifffile

import ael
from ael import calibrate, develop, io, photoshop, stack
from ael.filterbank import ALIASES, DEFAULTS, NAMES
from ael.filters import normalized_gaussian
from ael.geometry import EclipseGeometry, fit_limb, measure_geometry

CREDIT = ael.CREDIT


def emit(**payload) -> None:
    print(json.dumps(payload, ensure_ascii=False, default=str))


def runtime() -> dict:
    return {"python": sys.executable, "python_version": list(sys.version_info[:3]),
            "ael_version": ael.__version__, "ael_file": ael.__file__}


def exiftool_path() -> str:
    for candidate in (shutil.which("exiftool"), "/opt/homebrew/bin/exiftool", "/usr/local/bin/exiftool"):
        if candidate and Path(candidate).is_file():
            return candidate
    raise RuntimeError("ExifTool is required to read exposure and ISO metadata. Install it or provide metadata explicitly.")


def number(value) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if "/" in text:
        a, b = text.split("/", 1)
        return float(a) / float(b)
    return float(text.split()[0])


def metadata(path: Path) -> dict:
    if path.suffix.lower() in (".fits", ".fit", ".fts"):
        # Astronomical cameras write exposure and gain in the FITS header, not in EXIF.
        from astropy.io import fits
        header = fits.getheader(path)
        exposure = next((header[k] for k in ("EXPTIME", "EXPOSURE") if k in header), None)
        if exposure is None:
            raise ValueError(f"Missing EXPTIME/EXPOSURE in the FITS header: {path}")
        gain = next((header[k] for k in ("ISOSPEED", "ISO", "GAIN") if k in header), 0)
        return {"exposure_s": number(exposure), "iso": number(gain),
                "make": str(header.get("INSTRUME", "")), "model": str(header.get("TELESCOP", ""))}
    run = subprocess.run([exiftool_path(), "-json", "-ExposureTime", "-ISO", "-Make", "-Model", str(path)],
                         text=True, capture_output=True, timeout=30, check=False)
    if run.returncode != 0:
        raise RuntimeError(f"ExifTool failed for {path}: {run.stderr.strip()}")
    values = json.loads(run.stdout)[0]
    if "ExposureTime" not in values or "ISO" not in values:
        raise ValueError(f"Missing exposure or ISO metadata: {path}")
    return {"exposure_s": number(values["ExposureTime"]), "iso": number(values["ISO"]),
            "make": values.get("Make", ""), "model": values.get("Model", "")}


RAW_EXTENSIONS = {".cr2", ".cr3", ".nef", ".arw", ".dng", ".raf", ".orf", ".rw2"}


def raw_levels(path: Path) -> dict:
    """Black and white levels as the RAW file declares them (LibRaw, through rawpy)."""
    import rawpy
    with rawpy.imread(str(path)) as raw:
        black = [float(v) for v in raw.black_level_per_channel]
        white = float(raw.white_level)
    return {"black": float(np.median(black)), "white": white, "black_per_channel": black,
            "source": "the RAW file's own black and white levels"}


def data_levels(path: Path) -> dict:
    """Black and saturation of a calibrated linear frame (TIFF, FITS, NPY), measured on its data.

    Black is 0: the frame is taken as calibrated. A channel is saturated where its highest value is a plateau that
    many samples share; the lowest such plateau is the white level. Without a plateau nothing is marked saturated.
    """
    array = np.asarray(io.load_array(path))
    if array.ndim == 3 and array.shape[-1] == 4:
        array = array[..., :3]
    channels = [array] if array.ndim == 2 else [array[..., c] for c in range(array.shape[-1])]
    plateaus = []
    for channel in channels:
        finite = channel[np.isfinite(channel)] if channel.dtype.kind == "f" else channel.ravel()
        if finite.size == 0:
            raise ValueError(f"No finite samples in {path}")
        top = finite.max()
        count = int(np.count_nonzero(finite == top))
        if count >= max(25, 1e-6 * finite.size):
            plateaus.append((float(top), count))
    highest = float(max(np.nanmax(c) if c.dtype.kind == "f" else c.max() for c in channels))
    if not highest > 0:
        raise ValueError(f"The frame has no positive samples: {path}")
    if plateaus:
        white, count = min(plateaus)
        return {"black": 0.0, "white": white,
                "source": f"black 0 (calibrated frame); saturation at {white:g}, where {count} samples of one channel "
                          "share the highest value"}
    return {"black": 0.0, "white": 2.0 * highest,
            "source": "black 0 (calibrated frame); no saturation plateau, so nothing is marked as saturated"}


def sibling(input_path: Path, name: str) -> Path | None:
    candidate = input_path.parent / name
    return candidate if candidate.is_file() else None


def automatic_scale(input_path: Path, geometry_path: Path, valid_path: Path | None,
                    coverage_path: Path | None, min_coverage: float) -> float:
    rgb = io.load_array(input_path).astype(np.float32)
    if rgb.ndim == 2:
        rgb = np.repeat(rgb[..., None], 3, axis=-1)
    valid = np.isfinite(rgb).all(axis=-1)
    if valid_path:
        valid &= io.load_array(valid_path).astype(bool)
    if coverage_path:
        valid &= io.load_array(coverage_path) >= min_coverage
    geo = EclipseGeometry.from_json(geometry_path)
    valid &= ~geo.moon_mask(2) if geo.moon_xy is not None else valid
    r = geo.rsun_map()
    ring = valid & (r >= 1.1) & (r <= 2.0)
    if not ring.any():
        ring = valid & (r > 1.0)
    if not ring.any():
        raise ValueError("No observed corona pixels available to measure display scale")
    lum = (rgb[..., 0] + 2 * rgb[..., 1] + rgb[..., 2]) / 4
    positive = ring & (lum > 0)
    if not positive.any():
        raise ValueError("No positive corona pixels available to measure display scale")
    scale = float(np.median(lum[positive]))
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("Measured display scale is not positive")
    return scale


def pixelmath_expression(name: str, mode: str, opacity: float) -> dict:
    # PixelMath symbols take constants only: "L=<view id>" makes executeOn fail and leave
    # the target untouched. View identifiers therefore go straight into the expression.
    # AEL and Photoshop store opacity in 8 bits, so the effective weight is round(255*o)/255.
    layer = f"AEL_L_{name}"
    alpha = f"AEL_A_{name}"
    effective = round(opacity * 255) / 255
    weight = f"({alpha}*{effective:.10g})"
    if mode == "normal":
        expression = f"$T*(1-{weight})+{layer}*{weight}"
    elif mode == "multiply":
        expression = f"$T*(1-{weight})+$T*{layer}*{weight}"
    elif mode == "overlay":
        expression = f"$T*(1-{weight})+iif($T<=0.5,2*$T*{layer},1-2*(1-$T)*(1-{layer}))*{weight}"
    else:
        raise ValueError(f"Unsupported PixelMath blend mode: {mode}")
    return {"filter": name, "layer_view": layer, "alpha_view": alpha,
            "symbols": "", "expression": expression,
            "mode": mode, "opacity": opacity, "effective_opacity": effective}


def run_filters(cfg: dict) -> dict:
    input_path = Path(cfg["input"]).expanduser().resolve()
    out = Path(cfg["out"]).expanduser().resolve()
    if out.exists():
        raise FileExistsError(f"Output directory already exists: {out}")
    out.mkdir(parents=True)
    valid = Path(cfg["valid"]).resolve() if cfg.get("valid") else sibling(input_path, "valid.npy")
    source = np.asarray(io.load_array(input_path))
    if source.ndim == 3 and source.shape[-1] == 4:
        # An alpha channel marks the observed pixels: AEL takes the colour and that mask.
        alpha_valid = source[..., 3] > 0
        if valid:
            alpha_valid &= np.asarray(io.load_array(valid)).astype(bool)
        np.save(out / "input_rgb.npy", np.ascontiguousarray(source[..., :3], np.float32))
        np.save(out / "valid_from_alpha.npy", alpha_valid)
        input_path, valid = out / "input_rgb.npy", out / "valid_from_alpha.npy"
    given = cfg.get("geometry")
    beside = sibling(Path(cfg["input"]).expanduser().resolve(), "geometry.json")
    geometry_report = None
    if given and given != "auto":
        geometry = Path(given).expanduser().resolve()
        if not geometry.is_file():
            raise FileNotFoundError(f"Geometry file not found: {geometry}")
    elif beside and given != "auto":
        geometry = beside
    else:
        # No geometry: AEL measures it on the image (the lunar disc, or the region without data around it).
        mask = np.asarray(io.load_array(valid)).astype(bool) if valid else None
        measured, geometry_report = measure_geometry(source, mask)
        geometry = out / "geometry_measured.json"
        measured.to_json(geometry)
    del source
    coverage = Path(cfg["coverage"]).resolve() if cfg.get("coverage") else sibling(input_path, "coverage.npy")
    alpha = Path(cfg["alpha"]).resolve() if cfg.get("alpha") else sibling(input_path, "alpha.npy")
    minimum = float(cfg.get("min_coverage", 0.5))
    display = dict(cfg.get("display") or {})
    measured_scale = automatic_scale(input_path, geometry, valid, coverage, minimum) if "scale" not in display else None
    if measured_scale is not None:
        display["scale"] = measured_scale
    display.setdefault("asinh", 20)
    display.setdefault("highlight_ceiling", 0.9)
    # "all" (the default), "defaults" (AEL's own default layers, read from ael.filterbank) or a list of names; the
    # names AEL still accepts for renamed filters (ael.filterbank.ALIASES) are turned into the current ones.
    requested = cfg.get("filters", "all")
    if requested == "defaults":
        requested = list(DEFAULTS)
    elif isinstance(requested, list):
        requested = [ALIASES.get(name, name) for name in requested]
    recipe = {"input": str(input_path), "geometry": str(geometry),
              "min_coverage": minimum, "filters": requested,
              "visible": cfg.get("visible", list(DEFAULTS)),
              "opacities": cfg.get("opacities", {}), "display": display,
              "photoshop": bool(cfg.get("photoshop_layers", False)),
              "note": "PixInsight workflow; portable AEL filters, not historical layer replay"}
    for key, value in (("valid", valid), ("coverage", coverage), ("alpha", alpha)):
        if value:
            recipe[key] = str(value)
    if cfg.get("white_balance") is not None:
        recipe["white_balance"] = cfg["white_balance"]
    if cfg.get("camera_to_linear_rgb") is not None:
        recipe["camera_to_linear_rgb"] = cfg["camera_to_linear_rgb"]
    recipe_path = out / "filters_recipe.json"
    recipe_path.write_text(json.dumps(recipe, indent=1, ensure_ascii=False), encoding="utf-8")
    product = out / "ael"
    result = develop.filters_from_config(recipe_path, product)
    ael_receipt_path = Path(result["receipt"])
    ael_receipt = json.loads(ael_receipt_path.read_text())
    if not all(ael_receipt["gates"].get(key) for key in ("nothing_outside_data", "positive_display_base_not_clipped")):
        raise RuntimeError(f"AEL filter gate failed: {ael_receipt['gates']}")
    selected = recipe["filters"] if recipe["filters"] != "all" else list(NAMES)

    # AEL's display.tif is the finished composite, filters included. PixelMath must start from the display
    # base alone, and from exactly what AEL starts from. AEL composites in floating point from the 16-bit layer
    # images and the 16-bit alpha (develop.py, add()) and rounds once, at the very end. Starting PixelMath from a
    # base composite already rounded to 16 bits would round twice and could drift by one 16-bit step (half a step
    # at the start, half at the end). AEL therefore renders the base once more without its alpha file: the alpha
    # is then the 0/1 valid mask, so its display.tif is the 16-bit base layer itself. The start is then formed
    # in float32 as AEL forms it, base/65535 * alpha/65535 over black, and written as a 32-bit TIFF.
    base_recipe = {key: value for key, value in recipe.items() if key != "alpha"}
    base_recipe.update(filters=selected[:1], visible=[], opacities={}, photoshop=False,
                       note="Display base layer only (alpha = valid mask): no visible filter layer")
    base_recipe_path = out / "display_base_recipe.json"
    base_recipe_path.write_text(json.dumps(base_recipe, indent=1, ensure_ascii=False), encoding="utf-8")
    base_result = develop.filters_from_config(base_recipe_path, out / "ael_display_base")

    tiff_dir = out / "tiff"
    tiff_dir.mkdir()
    images = [{"name": "display", "kind": "display", "path": str(tiff_dir / "display.tif"),
               "view": "AEL_DISPLAY"}]
    base_u16 = tifffile.imread(base_result["files"]["display"])
    if base_u16.dtype != np.uint16 or base_u16.ndim != 3 or base_u16.shape[-1] != 3:
        raise RuntimeError(f"AEL display base is not a 16-bit RGB image: {base_u16.dtype} {base_u16.shape}")
    start = base_u16.astype(np.float32) / 65535           # develop.add(): x = u.astype(np.float32) / 65535
    if alpha:
        # outside the valid domain the base is 0, so the alpha there cannot change the product
        weight = photoshop.to_u16(np.asarray(io.load_array(alpha))).astype(np.float32)[..., None] / 65535
        weight = weight * (round(1 * 255) / 255)           # opacity 1, stored in 8 bits as AEL does
        start = np.zeros_like(start) * (1 - weight) + start * weight
    io.save_tiff(tiff_dir / "display.tif", start.astype(np.float32),
                 description="AEL display base over black with its alpha, float32, the start of AEL's own composite")
    layer_receipt = {entry["name"]: entry for entry in ael_receipt["parameters"]["layers"]}
    operations = []
    for name in selected:
        info = layer_receipt[name]
        for kind in ("layer", "alpha"):
            source = Path(result["files"][f"{name}_{kind}"])
            array = np.load(source)
            target = tiff_dir / f"{name}_{kind}.tif"
            io.save_tiff(target, photoshop.to_u16(array),
                         description=f"AEL {name} {kind}; 16-bit display domain; NPY is authoritative")
            images.append({"name": name, "kind": kind, "path": str(target),
                           "view": f"AEL_{'L' if kind == 'layer' else 'A'}_{name}"})
        if info["visible"]:
            operations.append(pixelmath_expression(name, info["mode"], float(info["opacity"])))
    (out / "pixelmath.json").write_text(json.dumps({"target_view": "AEL_COMPOSITE",
        "source_view": "AEL_DISPLAY", "reference_composite": result["files"]["display"],
        "operations": operations}, indent=1), encoding="utf-8")
    instructions = ["# PixelMath replay", "",
                    "Open the TIFF images. `AEL_DISPLAY` is the display base over black with its alpha, as a",
                    "32-bit float image: exactly where AEL starts its own composite, before any filter.",
                    "Duplicate it as `AEL_COMPOSITE`, make sure the duplicate is 32-bit float (a 16-bit target",
                    "rounds after every step), and execute these single expressions on it,",
                    "in order, with no symbols. If a view was renamed on opening, change its identifier",
                    "in the expression. The result matches AEL's composite `ael/display.tif` to its final",
                    "rounding to 16 bits (half a step), which is the only rounding AEL applies.", ""]
    for index, operation in enumerate(operations, 1):
        instructions += [f"## {index}. {operation['filter']} — {operation['mode']}, opacity {operation['opacity']:g}"
                         f" (8-bit effective {operation['effective_opacity']:.6g})",
                         "", f"```text\n{operation['expression']}\n```", ""]
    (out / "PIXELMATH.md").write_text("\n".join(instructions), encoding="utf-8")
    receipt = {"product": "PixInsight AEL filter layers", "runtime": runtime(),
               "input": str(input_path), "recipe": str(recipe_path), "ael_receipt": str(ael_receipt_path),
               "geometry": str(geometry),
               "geometry_source": "measured on the image" if geometry_report else "given",
               "geometry_measurement": geometry_report,
               "display_base_recipe": str(base_recipe_path), "display_base_receipt": base_result["receipt"],
               "display_start": "float32, base/65535 * alpha/65535 over black, formed as AEL starts its composite",
               "reference_composite": result["files"]["display"],
               "display_scale_measured": measured_scale, "images": images, "pixelmath": operations,
               "gates": ael_receipt["gates"], "credit": CREDIT}
    receipt_path = out / "AEL_WORKFLOW_RECEIPT.json"
    receipt_path.write_text(json.dumps(receipt, indent=1, ensure_ascii=False), encoding="utf-8")
    answer = {"ok": True, "operation": "filters", "out": str(out), "images": images,
              "geometry": json.loads(Path(geometry).read_text(encoding="utf-8")),
              "geometry_source": "measured on the image" if geometry_report else "given",
              "pixelmath": operations, "receipt": str(receipt_path), "gates": ael_receipt["gates"]}
    if recipe["photoshop"]:
        # AEL wrote one layered 16-bit PSB and verified it by reading it back. These are its layers from the
        # bottom up, as develop.filters_from_config adds them, for the check inside Photoshop itself.
        answer["psb"] = result["files"]["psb"]
        answer["psb_layers"] = [{"name": "Background", "mode": "normal", "opacity": 1.0, "visible": True},
                                {"name": "Linear reference / receipt scale", "mode": "normal", "opacity": 1.0,
                                 "visible": False},
                                {"name": "00 Display base", "mode": "normal", "opacity": 1.0, "visible": True}]
        answer["psb_layers"] += [{"name": entry["layer"], "mode": entry["mode"], "opacity": float(entry["opacity"]),
                                  "visible": bool(entry["visible"])} for entry in ael_receipt["parameters"]["layers"]]
    return answer


MOON_KEYS = ("xy", "r", "rms", "n_used", "n_rays")


def frame_luminance(path: Path, kind: str, black: float, white: float, fraction: float):
    """Full-resolution luminance above black, its usable pixels, native shape and CFA pattern.

    The luminance keeps saturated samples (clipped) for the limb fit; the usable mask drops
    them, together with non-positive samples, for the solar registration.
    """
    ceiling = fraction * (white - black)
    if kind == "raw":
        raw = calibrate.read_raw(path, full=False)
        bayer = raw["bayer"].astype(np.float32) - black
        green, _ = calibrate.green_plane(bayer, raw["pattern"])
        _, bad = calibrate.green_plane(bayer, raw["pattern"], bayer >= ceiling)
        return green, ~bad & (green > 0), bayer.shape, np.asarray(raw["pattern"]).tolist()
    array = io.load_array(path).astype(np.float32) - black
    if array.ndim != 3 or array.shape[-1] != 3:
        raise ValueError(f"Linear RGB input must be HxWx3: {path}")
    lum = (array[..., 0] + 2 * array[..., 1] + array[..., 2]) / 4
    usable = np.isfinite(lum) & (lum > 0) & ~(array >= ceiling).any(axis=-1)
    return lum, usable, array.shape[:2], None


def measure_moon(lum: np.ndarray, approx_xy, radius: float) -> dict:
    """Lunar limb of one frame: a wide search (±30 % of the radius), then a narrow one."""
    wide = fit_limb(lum, approx_xy, radius, n_rays=720, search_frac=0.3, smooth_px=1.1, n_iter=4)
    return fit_limb(lum, wide["xy"], wide["r"], n_rays=720, search_frac=0.08, smooth_px=1.1, n_iter=4)


def _shrink(value: np.ndarray, usable: np.ndarray, factor: int):
    """Means of complete blocks; block pixel i is centred at factor*i + (factor-1)/2."""
    if factor == 1:
        return value, usable
    h, w = (value.shape[0] // factor) * factor, (value.shape[1] // factor) * factor
    blocks = (h // factor, factor, w // factor, factor)
    count = usable[:h, :w].reshape(blocks).sum(axis=(1, 3))
    total = np.where(usable, value, 0)[:h, :w].reshape(blocks).sum(axis=(1, 3))
    full = count == factor * factor
    return np.where(full, total / np.maximum(count, 1), 0).astype(np.float32), full


def _sampler(shape, t):
    yy, xx = np.mgrid[:shape[0], :shape[1]].astype(np.float32)
    mx, my = (xx + t[0]).astype(np.float32), (yy + t[1]).astype(np.float32)
    return lambda a: cv2.remap(np.ascontiguousarray(a, np.float32), mx, my, cv2.INTER_LINEAR,
                               borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def _solve_translation(ref, ref_use, weight, mov, mov_use, t, *, iterations=100):
    """Weighted Gauss-Newton for mov(x + t) = a*ref(x) + b over pixels usable in both frames."""
    gy, gx = np.gradient(mov)
    # A gradient counts only where its whole 3x3 neighbourhood is usable.
    grad_use = cv2.erode(mov_use.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(np.float32)
    t = np.asarray(t, np.float64).copy()
    for _ in range(iterations):
        sample = _sampler(ref.shape, t)
        m = ref_use & (sample(grad_use) > 0.999)
        n = int(m.sum())
        if n < 100:
            raise RuntimeError("Insufficient overlap for solar registration")
        root = np.sqrt(weight[m]).astype(np.float64)
        a = np.column_stack([sample(gx)[m], sample(gy)[m], -ref[m], -np.ones(n)]) * root[:, None]
        step = np.linalg.lstsq(a, -sample(mov)[m] * root, rcond=None)[0][:2]
        step *= min(1.0, 1.0 / max(float(np.hypot(*step)), 1e-12))  # at most one pixel per iteration
        t += step
        if np.hypot(*step) < 1e-4:
            return t
    raise RuntimeError("Solar registration did not converge")


def _log_positive(value: np.ndarray) -> np.ndarray:
    return np.where(value > 0, np.log(np.where(value > 0, value, 1.0)), np.nan).astype(np.float32)


def _inside(mask: np.ndarray, distance: float) -> np.ndarray:
    """Pixels farther than ``distance`` from any pixel without data."""
    padded = np.pad(mask.astype(np.uint8), 1)
    return cv2.distanceTransform(padded, cv2.DIST_L2, 5)[1:-1, 1:-1] > distance


def _pearson(a: np.ndarray, b: np.ndarray, mask: np.ndarray) -> float:
    x, y = a[mask].astype(np.float64), b[mask].astype(np.float64)
    x, y = x - x.mean(), y - y.mean()
    return float((x * y).sum() / np.sqrt((x * x).sum() * (y * y).sum()))


def structure_check(reference, moving, ref_valid, mov_valid, geometry: EclipseGeometry, t, *,
                    rmax_rsun: float, small_px: float = 1.5) -> dict:
    """Check a registration on coronal structure, against the frame turned about the Sun.

    The corona is band-passed (linear smoothing, then logarithm, so noisy short exposures keep
    their structure) and compared only where both filters saw data over their whole support.
    A frame turned by 90° or 270° about the Sun keeps the radial statistics and loses the
    structure; the score is the share of what the turn leaves unexplained that the structure
    matches. 180° is left out: equatorial streamers can be symmetric.
    """
    large = max(3 * small_px, 0.1 * geometry.sun_radius_px)
    # Only the corona within rmax_rsun is compared: work on that box (plus the filter's reach and
    # the shift), in the same pixels of both frames.
    sun = np.asarray(geometry.sun_xy, np.float64)
    reach = rmax_rsun * geometry.sun_radius_px + 4 * large + float(np.hypot(*t)) + 2
    height, width = ref_valid.shape
    x0, x1 = max(0, int(sun[0] - reach)), min(width, int(np.ceil(sun[0] + reach)) + 1)
    y0, y1 = max(0, int(sun[1] - reach)), min(height, int(np.ceil(sun[1] + reach)) + 1)
    sun = sun - [x0, y0]
    maps, cores = [], []
    for (lum, _), valid in ((reference, ref_valid), (moving, mov_valid)):
        lum, valid = lum[y0:y1, x0:x1], valid[y0:y1, x0:x1]
        band = (_log_positive(normalized_gaussian(lum, valid, small_px, 0.5)) -
                _log_positive(normalized_gaussian(lum, valid, large, 0.5)))
        maps.append(band)
        cores.append(_inside(valid, 2 * large) & np.isfinite(band))
    h, w = maps[0].shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    seen = (np.hypot(xx - sun[0], yy - sun[1]) <= rmax_rsun * geometry.sun_radius_px) & cores[0]
    filled = np.where(np.isfinite(maps[1]), maps[1], 0).astype(np.float32)
    values = {}
    for angle in (0, 90, 180, 270):
        c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        linear = np.array([[c, -s], [s, c]])
        warp = np.hstack([linear, (sun + np.asarray(t) - linear @ sun)[:, None]]).astype(np.float32)
        turned = cv2.warpAffine(filled, warp, (w, h), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
        covered = cv2.warpAffine(cores[1].astype(np.uint8), warp, (w, h),
                                 flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP).astype(bool)
        mask = seen & covered
        values[str(angle)] = _pearson(maps[0], turned, mask) if mask.sum() >= 100 else float("nan")
    null = max(values["90"], values["270"])
    score = (values["0"] - null) / (1.0 - null) if null < 1 else float("nan")
    return {"correlation": values["0"], "turned_correlation": {k: values[k] for k in ("90", "180", "270")},
            "structure_score": score, "band_px": [small_px, large]}


def register_on_sun(reference, moving, geometry: EclipseGeometry, reference_moon: dict, moving_moon: dict, *,
                    margin_px: float, rmax_rsun: float = 3.0, initial=(0.0, 0.0),
                    min_structure: float = 0.25) -> dict:
    """Translation reference->input measured on the corona, which is fixed on the Sun.

    Each frame leaves out its own Moon, measured on its own limb, plus ``margin_px`` for the
    blurred lunar edge; the Moon moves relative to the Sun during totality. Only unsaturated
    pixels within ``rmax_rsun`` of the reference Sun count. Log intensity turns exposure into
    an offset; weights follow the reference signal (Poisson). Coarse-to-fine block means.
    """
    def logged(lum, usable, moon):
        yy, xx = np.mgrid[:lum.shape[0], :lum.shape[1]]
        free = np.hypot(xx - moon["xy"][0], yy - moon["xy"][1]) > moon["r"] + margin_px
        use = usable & free
        # The structure check smooths linearly, so it keeps the noise below zero.
        linear = (usable | (np.isfinite(lum) & (lum <= 0))) & free
        return np.where(use, np.log(np.where(use, lum, 1)), 0).astype(np.float32), use, linear
    ref, ref_use, ref_linear = logged(*reference, reference_moon)
    mov, mov_use, mov_linear = logged(*moving, moving_moon)
    ref_use &= geometry.rsun_map() <= rmax_rsun
    weight = np.where(ref_use, reference[0], 0).astype(np.float32)
    weight /= max(float(weight.max()), 1e-30)
    factors = [f for f in (16, 8, 4, 2) if geometry.sun_radius_px / f >= 8] + [1]
    t = np.asarray(initial, np.float64)
    for factor in factors:
        r, ru = _shrink(ref, ref_use, factor)
        w, _ = _shrink(weight, ref_use, factor)
        m, mu = _shrink(mov, mov_use, factor)
        t = _solve_translation(r, ru, w, m, mu, t / factor) * factor
    # Independent check on coronal structure: an unrelated image or a false optimum fails here.
    check = structure_check(reference, moving, ref_linear, mov_linear, geometry, t, rmax_rsun=rmax_rsun)
    score = check["structure_score"]
    if not math.isfinite(score) or score < min_structure:
        raise RuntimeError(f"Solar registration rejected: coronal structure correlates {check['correlation']:.3f}, "
                           f"the frame turned about the Sun up to "
                           f"{max(check['turned_correlation']['90'], check['turned_correlation']['270']):.3f}; "
                           f"structure score {score:.3f} < {min_structure}")
    return dict(check, translation=t.tolist(), levels=factors, margin_px=margin_px, rmax_rsun=rmax_rsun)


def register_frame(reference, moving, geometry: EclipseGeometry, reference_moon: dict, *, margin_px: float,
                   rmax_rsun: float = 3.0, max_lunar_px: float | None = None) -> dict:
    """Moon of the moving frame from its own limb; registration on the Sun from the corona."""
    moon = measure_moon(moving[0], reference_moon["xy"], reference_moon["r"])
    moon_shift = np.asarray(moon["xy"]) - np.asarray(reference_moon["xy"])
    solar = register_on_sun(reference, moving, geometry, reference_moon, moon, margin_px=margin_px,
                            rmax_rsun=rmax_rsun, initial=moon_shift)
    lunar = moon_shift - np.asarray(solar["translation"])
    if max_lunar_px is not None and np.hypot(*lunar) > max_lunar_px:
        raise RuntimeError(f"Moon moved {np.hypot(*lunar):.2f} px relative to the Sun, above the "
                           f"{max_lunar_px:.2f} px allowed; check the frames or the registration")
    return dict(solar, selected="sun_translation", moon_fit={key: moon[key] for key in MOON_KEYS},
                lunar_shift_px=lunar.tolist())


def run_master(cfg: dict) -> dict:
    paths = [Path(value).expanduser().resolve() for value in cfg["frames"]]
    if not paths:
        raise ValueError("No input frames")
    reference_index = int(cfg.get("reference", 0))
    if reference_index < 0 or reference_index >= len(paths):
        raise ValueError("Invalid reference index")
    kinds = ["raw" if path.suffix.lower() in RAW_EXTENSIONS else "rgb" for path in paths]
    profile = cfg.get("camera")
    if isinstance(profile, (str, Path)) and str(profile).strip() and str(profile) != "auto":
        profile = json.loads(Path(profile).expanduser().read_text())
    if isinstance(profile, dict):
        # A camera profile given by the user holds for every frame.
        levels = [{"black": float(profile["black"]), "white": float(profile["white"]),
                   "source": "camera profile given"} for _ in paths]
        fraction = float(profile.get("linearity_fraction", 0.95))
    else:
        # Not given: each RAW file declares its own black and white levels; a calibrated TIFF/FITS frame is measured.
        profile = {}
        levels = [raw_levels(path) if kind == "raw" else data_levels(path) for path, kind in zip(paths, kinds)]
        fraction = 0.95
    for path, level in zip(paths, levels):
        if not level["white"] > level["black"]:
            raise ValueError(f"Invalid black/white levels for {path}: {level}")
    if not 0 < fraction <= 1:
        raise ValueError("Invalid linearity fraction")
    meta = [metadata(path) for path in paths]
    if len({item["iso"] for item in meta}) != 1:
        raise ValueError("Stack one ISO at a time")
    if len({(item["make"], item["model"]) for item in meta}) != 1:
        raise ValueError("Stack one camera/optical train at a time")
    exposures = sorted({item["exposure_s"] for item in meta})
    if cfg.get("dark") and len(exposures) > 1:
        # AEL subtracts the dark as recorded, before dividing by each frame's exposure.
        # One master dark can match one exposure only.
        raise ValueError(f"One master dark cannot calibrate frames with different exposures {exposures}. "
                         "Stack each exposure with its own matching dark, or leave the dark empty.")
    if cfg.get("allow_rotation"):
        raise ValueError("Rotation is not supported: registration is a translation measured on the Sun")
    data = [frame_luminance(path, kind, level["black"], level["white"], fraction)
            for path, kind, level in zip(paths, kinds, levels)]
    shapes = [tuple(item[2]) for item in data]
    given = cfg.get("geometry")
    geometry_report = None
    if given and given != "auto":
        geometry = EclipseGeometry.from_json(given if isinstance(given, dict) else Path(given).expanduser())
    else:
        # Not given: measured on the reference frame (the lunar limb, or the region without data around it). On a long
        # exposure the lunar disc itself can be saturated, with no limb to measure: then the first frame whose limb
        # holds becomes the reference, and the receipt says so.
        failures = {}
        for index in [reference_index] + [i for i in range(len(paths)) if i != reference_index]:
            try:
                geometry, geometry_report = measure_geometry(data[index][0])
            except RuntimeError as exc:
                failures[str(paths[index].name)] = str(exc)
                continue
            if index != reference_index:
                geometry_report["reference_changed"] = {"from": paths[reference_index].name, "to": paths[index].name,
                                                        "reason": failures[paths[reference_index].name]}
                reference_index = index
            break
        else:
            raise RuntimeError("The Moon could not be measured on any frame; give the reference geometry. " +
                               "; ".join(f"{name}: {message}" for name, message in failures.items()))
    if shapes[reference_index] != tuple(geometry.shape):
        raise ValueError("Reference geometry shape does not match the reference frame")
    patterns = [item[3] for item in data]
    if any(pattern != patterns[0] for pattern in patterns):
        raise ValueError("CFA patterns must agree")

    # The corona is fixed on the Sun and the Moon moves across it during totality, so frames
    # are registered on the Sun; each frame keeps its own measured Moon for its mask.
    margin = float(cfg.get("registration_margin_px", max(6.0, 0.015 * geometry.moon_radius_px)))
    rmax = float(cfg.get("registration_rmax_rsun", 3.0))
    # During totality the Moon crosses at most twice the difference of the radii, and the Moon never looks more than
    # about 8 % larger than the Sun: 0.16 lunar radii holds for every total eclipse, short or long.
    max_lunar = float(cfg.get("max_lunar_shift_px", 0.16 * geometry.moon_radius_px + 2))
    reference = data[reference_index][:2]
    reference_fit = measure_moon(reference[0], geometry.moon_xy, geometry.moon_radius_px)
    registrations = []
    matrices = []
    moon_geometries = []
    for index, item in enumerate(data):
        if index == reference_index:
            matrix = np.eye(2, 3, dtype=np.float64)
            registration = {"selected": "reference", "translation": [0.0, 0.0], "correlation": 1.0,
                            "moon_fit": {key: reference_fit[key] for key in MOON_KEYS},
                            "lunar_shift_px": [0.0, 0.0]}
        else:
            registration = register_frame(reference, item[:2], geometry, reference_fit, margin_px=margin,
                                          rmax_rsun=rmax, max_lunar_px=max_lunar)
            matrix = np.hstack([np.eye(2), np.asarray(registration["translation"])[:, None]])
        registration["reference_to_input"] = matrix.tolist()
        registrations.append(registration)
        matrices.append(matrix)
        moon_geometries.append(registration["moon_fit"])
    frames = []
    for index, (path, kind, info, matrix, moon_fit, level) in enumerate(
            zip(paths, kinds, meta, matrices, moon_geometries, levels)):
        frame = {"path": str(path), "kind": kind, "iso": info["iso"], "exposure_s": info["exposure_s"],
                 "black": level["black"], "white": level["white"], "linearity_fraction": fraction,
                 "reference_to_input": matrix.tolist(), "moon_xy": list(moon_fit["xy"]),
                 "moon_radius_px": moon_fit["r"], "train": profile.get("train", "one")}
        for key in ("dark", "flat"):
            if cfg.get(key):
                frame[key] = str(Path(cfg[key]).expanduser().resolve())
        frames.append(frame)
    recipe = {"geometry": json.loads(geometry.to_json()),
              "frames": frames, "stack": {"canvas": "reference", "taper_start": 0.8,
              "moon_guard_px": 2, "limb_fade_px": 4, "band_sigma_px": 0,
              "hot_pixels": {"enabled": False}}, "note": "PixInsight automated metadata and measured registration"}
    out = Path(cfg["out"]).expanduser().resolve()
    if out.exists():
        raise FileExistsError(f"Output directory already exists: {out}")
    out.mkdir(parents=True)
    recipe_path = out / "stack_recipe.json"
    recipe_path.write_text(json.dumps(recipe, indent=1, ensure_ascii=False), encoding="utf-8")
    master_dir = out / "master"
    result = stack.stack_from_config(recipe_path, master_dir)
    ael_receipt = json.loads(Path(result["receipt"]).read_text())
    if not all(ael_receipt["gates"].get(key) for key in ("observed_support", "nothing_outside_data")):
        raise RuntimeError(f"AEL stack gate failed: {ael_receipt['gates']}")
    images = [{"name": "linear", "kind": "linear", "path": result["files"]["tiff"], "view": "AEL_LINEAR_MASTER"}]
    filter_result = None
    if cfg.get("run_filters", True):
        filter_cfg = dict(cfg.get("filter_options") or {})
        filter_cfg.setdefault("photoshop_layers", cfg.get("photoshop_layers", False))
        filter_cfg.update({"input": result["files"]["linear"], "geometry": result["files"]["geometry"],
                           "valid": result["files"]["valid"], "coverage": result["files"]["coverage"],
                           "alpha": result["files"]["alpha"], "out": str(out / "filters")})
        filter_result = run_filters(filter_cfg)
        images += filter_result["images"]
    receipt = {"product": "PixInsight AEL linear master workflow", "runtime": runtime(),
               "recipe": str(recipe_path), "ael_receipt": result["receipt"], "metadata": meta,
               "camera_levels": [dict(level, path=str(path)) for path, level in zip(paths, levels)],
               "geometry_source": "measured on the reference frame" if geometry_report else "given",
               "geometry_measurement": geometry_report,
               "registrations": registrations, "images": images,
               "filters_receipt": filter_result["receipt"] if filter_result else None,
               "gates": ael_receipt["gates"], "credit": CREDIT}
    receipt_path = out / "AEL_WORKFLOW_RECEIPT.json"
    receipt_path.write_text(json.dumps(receipt, indent=1, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "operation": "master", "out": str(out), "images": images,
            "geometry": json.loads(Path(result["files"]["geometry"]).read_text(encoding="utf-8")),
            "geometry_source": "measured on the reference frame" if geometry_report else "given",
            "pixelmath": filter_result["pixelmath"] if filter_result else [],
            "receipt": str(receipt_path), "gates": ael_receipt["gates"],
            "registrations": registrations,
            "psb": filter_result.get("psb") if filter_result else None,
            "psb_layers": filter_result.get("psb_layers") if filter_result else None}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("master", "filters"))
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    try:
        cfg = json.loads(args.config.read_text(encoding="utf-8"))
        result = run_master(cfg) if args.operation == "master" else run_filters(cfg)
        emit(**result)
    except Exception as exc:
        emit(ok=False, kind=type(exc).__name__, message=str(exc), runtime=runtime())


if __name__ == "__main__":
    main()
