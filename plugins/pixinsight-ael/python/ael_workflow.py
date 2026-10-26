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

import ael
from ael import calibrate, develop, io, photoshop, stack
from ael.filterbank import DEFAULTS, NAMES
from ael.geometry import EclipseGeometry, fit_limb

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
    run = subprocess.run([exiftool_path(), "-json", "-ExposureTime", "-ISO", "-Make", "-Model", str(path)],
                         text=True, capture_output=True, timeout=30, check=False)
    if run.returncode != 0:
        raise RuntimeError(f"ExifTool failed for {path}: {run.stderr.strip()}")
    values = json.loads(run.stdout)[0]
    if "ExposureTime" not in values or "ISO" not in values:
        raise ValueError(f"Missing exposure or ISO metadata: {path}")
    return {"exposure_s": number(values["ExposureTime"]), "iso": number(values["ISO"]),
            "make": values.get("Make", ""), "model": values.get("Model", "")}


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
    layer = f"AEL_L_{name}"
    alpha = f"AEL_A_{name}"
    weight = f"{alpha}*{opacity:.10g}"
    if mode == "normal":
        expression = "$T*(1-w)+L*w"
    elif mode == "multiply":
        expression = "$T*(1-w)+$T*L*w"
    elif mode == "overlay":
        expression = "$T*(1-w)+iif($T<=0.5,2*$T*L,1-2*(1-$T)*(1-L))*w"
    else:
        raise ValueError(f"Unsupported PixelMath blend mode: {mode}")
    return {"filter": name, "layer_view": layer, "alpha_view": alpha,
            "symbols": f"w={weight},L={layer}", "expression": expression,
            "mode": mode, "opacity": opacity}


def run_filters(cfg: dict) -> dict:
    input_path = Path(cfg["input"]).expanduser().resolve()
    out = Path(cfg["out"]).expanduser().resolve()
    if out.exists():
        raise FileExistsError(f"Output directory already exists: {out}")
    out.mkdir(parents=True)
    geometry = Path(cfg.get("geometry") or sibling(input_path, "geometry.json") or "").resolve()
    if not geometry.is_file():
        raise FileNotFoundError("geometry.json is required beside linear.npy or explicitly in the configuration")
    valid = Path(cfg["valid"]).resolve() if cfg.get("valid") else sibling(input_path, "valid.npy")
    coverage = Path(cfg["coverage"]).resolve() if cfg.get("coverage") else sibling(input_path, "coverage.npy")
    alpha = Path(cfg["alpha"]).resolve() if cfg.get("alpha") else sibling(input_path, "alpha.npy")
    minimum = float(cfg.get("min_coverage", 0.5))
    display = dict(cfg.get("display") or {})
    measured_scale = automatic_scale(input_path, geometry, valid, coverage, minimum) if "scale" not in display else None
    if measured_scale is not None:
        display["scale"] = measured_scale
    display.setdefault("asinh", 20)
    display.setdefault("highlight_ceiling", 0.9)
    recipe = {"input": str(input_path), "geometry": str(geometry),
              "min_coverage": minimum, "filters": cfg.get("filters", "all"),
              "visible": cfg.get("visible", list(DEFAULTS)),
              "opacities": cfg.get("opacities", {}), "display": display,
              "photoshop": False, "note": "PixInsight workflow; portable AEL filters, not historical layer replay"}
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

    tiff_dir = out / "tiff"
    tiff_dir.mkdir()
    images = [{"name": "display", "kind": "display", "path": str(tiff_dir / "display.tif"),
               "view": "AEL_DISPLAY"}]
    shutil.copy2(result["files"]["display"], tiff_dir / "display.tif")
    selected = recipe["filters"] if recipe["filters"] != "all" else list(NAMES)
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
        "source_view": "AEL_DISPLAY", "operations": operations}, indent=1), encoding="utf-8")
    instructions = ["# PixelMath replay", "", "Open the TIFF images, duplicate `AEL_DISPLAY` as `AEL_COMPOSITE`,",
                    "and execute these single expressions in order with the listed symbols.", ""]
    for index, operation in enumerate(operations, 1):
        instructions += [f"## {index}. {operation['filter']} — {operation['mode']}, opacity {operation['opacity']:g}",
                         f"Symbols: `{operation['symbols']}`", "", f"```text\n{operation['expression']}\n```", ""]
    (out / "PIXELMATH.md").write_text("\n".join(instructions), encoding="utf-8")
    receipt = {"product": "PixInsight AEL filter layers", "runtime": runtime(),
               "input": str(input_path), "recipe": str(recipe_path), "ael_receipt": str(ael_receipt_path),
               "display_scale_measured": measured_scale, "images": images, "pixelmath": operations,
               "gates": ael_receipt["gates"], "credit": CREDIT}
    receipt_path = out / "AEL_WORKFLOW_RECEIPT.json"
    receipt_path.write_text(json.dumps(receipt, indent=1, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "operation": "filters", "out": str(out), "images": images,
            "pixelmath": operations, "receipt": str(receipt_path), "gates": ael_receipt["gates"]}


def proxy(path: Path, kind: str, black: float):
    if kind == "raw":
        raw = calibrate.read_raw(path, full=False)
        rgb = calibrate.superpixel_rgb(raw["bayer"].astype(np.float32) - black, raw["pattern"])
        return rgb, raw["bayer"].shape, raw["pattern"]
    array = io.load_array(path).astype(np.float32)
    if array.ndim != 3 or array.shape[-1] != 3:
        raise ValueError(f"Linear RGB input must be HxWx3: {path}")
    h, w = (array.shape[0] // 2) * 2, (array.shape[1] // 2) * 2
    reduced = array[:h, :w].reshape(h // 2, 2, w // 2, 2, 3).mean(axis=(1, 3))
    return reduced, array.shape[:2], None


def full_luminance(path: Path, kind: str, black: float) -> np.ndarray:
    if kind == "raw":
        raw = calibrate.read_raw(path, full=False)
        green, _ = calibrate.green_plane(raw["bayer"].astype(np.float32) - black, raw["pattern"])
        return green
    array = io.load_array(path).astype(np.float32)
    if array.ndim != 3 or array.shape[-1] != 3:
        raise ValueError(f"Linear RGB input must be HxWx3: {path}")
    return (array[..., 0] + 2 * array[..., 1] + array[..., 2]) / 4


def radial_residual(rgb: np.ndarray, geometry: EclipseGeometry) -> tuple[np.ndarray, np.ndarray]:
    lum = rgb if rgb.ndim == 2 else (rgb[..., 0] + 2 * rgb[..., 1] + rgb[..., 2]) / 4
    valid = np.isfinite(lum) & (lum > 0)
    if geometry.moon_xy is not None:
        valid &= ~geometry.moon_mask(3)
    r = geometry.rsun_map()
    valid &= (r > 0.95) & (r < 6)
    log = np.where(valid, np.log(np.where(valid, lum, 1)), np.nan)
    radial = np.rint(r).astype(np.int16)
    profile = np.zeros_like(log, dtype=np.float64)
    for radius in np.unique(radial[valid]):
        mask = valid & (radial == radius)
        profile[mask] = np.median(log[mask])
    residual = np.where(valid, log - profile, 0).astype(np.float32)
    lo, hi = np.percentile(residual[valid], [2, 98]) if valid.any() else (0, 1)
    scaled = np.clip((residual - lo) / max(float(hi - lo), 1e-6), 0, 1).astype(np.float32)
    return scaled, valid


def register(reference: np.ndarray, moving: np.ndarray, geometry: EclipseGeometry, *,
             initial=None, half_resolution=True, allow_rotation=False) -> dict:
    ref, ref_valid = radial_residual(reference, geometry)
    mov, mov_valid = radial_residual(moving, geometry)
    if not ref_valid.any() or not mov_valid.any():
        raise ValueError("No valid corona pixels for registration")
    warp = np.eye(2, 3, dtype=np.float32) if initial is None else np.asarray(initial, np.float32).copy()
    sift_inliers = 0
    feature_warp = None
    if initial is None:
        sift = cv2.SIFT_create(nfeatures=1500, contrastThreshold=0.01)
        ref_u8 = np.round(ref * 255).astype(np.uint8)
        mov_u8 = np.round(mov * 255).astype(np.uint8)
        kp1, d1 = sift.detectAndCompute(ref_u8, ref_valid.astype(np.uint8))
        kp2, d2 = sift.detectAndCompute(mov_u8, mov_valid.astype(np.uint8))
        if d1 is not None and d2 is not None and len(kp1) >= 4 and len(kp2) >= 4:
            pairs = cv2.BFMatcher().knnMatch(d1, d2, k=2)
            good = [a for a, b in pairs if a.distance < 0.75 * b.distance]
            if len(good) >= 6:
                p1 = np.float32([kp1[m.queryIdx].pt for m in good])
                p2 = np.float32([kp2[m.trainIdx].pt for m in good])
                estimate, inliers = cv2.estimateAffinePartial2D(p1, p2, method=cv2.RANSAC,
                    ransacReprojThreshold=1.0, maxIters=5000, confidence=0.999)
                if estimate is not None and inliers is not None:
                    sift_inliers = int(inliers.sum())
                    if sift_inliers >= 6:
                        feature_warp = estimate.astype(np.float32)
                        warp = feature_warp.copy()
    iterations = 500 if initial is None else 120
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, iterations, 1e-8)
    motion = cv2.MOTION_AFFINE if allow_rotation else cv2.MOTION_TRANSLATION
    selected = "ecc"
    cc = None
    if not allow_rotation and feature_warp is not None:
        warp = feature_warp.copy()
        selected = "sift_translation"
    else:
        cc, warp = cv2.findTransformECC(ref, mov, warp, motion, criteria, None, 5)
    if not np.isfinite(warp).all() or (cc is not None and not math.isfinite(float(cc))):
        raise RuntimeError("Registration did not converge")
    if not allow_rotation:
        warp[:, :2] = np.eye(2, dtype=np.float32)
    warp = np.asarray(warp, dtype=np.float64)
    if allow_rotation:
        # The affine is only an estimator. Keep its translation but project the linear
        # part to the nearest rotation: no scale or shear is allowed into the stack.
        u, _, vt = np.linalg.svd(warp[:, :2].astype(np.float64))
        warp[:, :2] = u @ vt
        if np.linalg.det(warp[:, :2]) < 0:
            u[:, -1] *= -1
            warp[:, :2] = u @ vt
    # findTransformECC uses the same reference->input convention as AEL when
    # WARP_INVERSE_MAP aligns the moving image to the reference.
    full = stack.full_resolution_affine(warp) if half_resolution else warp
    singular = np.linalg.svd(full[:, :2], compute_uv=False)
    if singular[0] / singular[1] > 1.02 or not 0.5 < abs(np.linalg.det(full[:, :2])) < 2:
        raise RuntimeError(f"Registration is not sufficiently similar to a rigid/similarity transform: {full.tolist()}")
    aligned = cv2.warpAffine(mov, warp, (ref.shape[1], ref.shape[0]),
                             flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_CONSTANT)
    mask = ref_valid & mov_valid & np.isfinite(aligned)
    if mask.sum() < 100:
        raise RuntimeError("Insufficient overlap after registration")
    correlation = float(np.corrcoef(ref[mask], aligned[mask])[0, 1])
    if not math.isfinite(correlation) or correlation < 0.25:
        raise RuntimeError(f"Registration rejected: correlation {correlation:.4f} < 0.25")
    return {"estimator_matrix": warp.tolist(), "reference_to_input": full.tolist(), "selected": selected,
            "resolution": "half" if half_resolution else "full", "sift_inliers": sift_inliers,
            "rotation_allowed": allow_rotation,
            "ecc": None if cc is None else float(cc), "correlation": correlation, "overlap_pixels": int(mask.sum())}


def run_master(cfg: dict) -> dict:
    paths = [Path(value).expanduser().resolve() for value in cfg["frames"]]
    if not paths:
        raise ValueError("No input frames")
    profile = cfg["camera"]
    if isinstance(profile, (str, Path)):
        profile = json.loads(Path(profile).expanduser().read_text())
    black, white = float(profile["black"]), float(profile["white"])
    fraction = float(profile.get("linearity_fraction", 0.95))
    if not white > black or not 0 < fraction <= 1:
        raise ValueError("Invalid camera black/white/linearity profile")
    reference_index = int(cfg.get("reference", 0))
    if reference_index < 0 or reference_index >= len(paths):
        raise ValueError("Invalid reference index")
    geometry = EclipseGeometry.from_json(cfg["geometry"])
    raw_extensions = {".cr2", ".cr3", ".nef", ".arw", ".dng", ".raf", ".orf", ".rw2"}
    kinds = ["raw" if path.suffix.lower() in raw_extensions else "rgb" for path in paths]
    meta = [metadata(path) for path in paths]
    if len({item["iso"] for item in meta}) != 1:
        raise ValueError("Stack one ISO at a time")
    if len({(item["make"], item["model"]) for item in meta}) != 1:
        raise ValueError("Stack one camera/optical train at a time")
    proxies = [proxy(path, kind, black) for path, kind in zip(paths, kinds)]
    shapes = [tuple(item[1]) for item in proxies]
    if shapes[reference_index] != tuple(geometry.shape):
        raise ValueError("Reference geometry shape does not match the reference frame")
    patterns = [None if item[2] is None else np.asarray(item[2]).tolist() for item in proxies]
    if any(pattern != patterns[0] for pattern in patterns):
        raise ValueError("CFA patterns must agree")

    registrations = []
    matrices = []
    moon_geometries = []
    reference_proxy = proxies[reference_index][0]
    half_geometry = geometry.scaled(0.5)
    luminances = [full_luminance(path, kind, black) for path, kind in zip(paths, kinds)]
    reference_fit = fit_limb(luminances[reference_index], geometry.moon_xy, geometry.moon_radius_px,
                             n_rays=720, search_frac=0.08, smooth_px=1.1, n_iter=4)
    ref_residual, ref_valid = radial_residual(reference_proxy, half_geometry)
    for index, item in enumerate(proxies):
        if index == reference_index:
            matrix = np.eye(2, 3, dtype=np.float64)
            registration = {"ecc": 1.0, "correlation": 1.0, "identity": True,
                            "moon_fit": {key: reference_fit[key] for key in ("xy", "r", "rms", "n_used", "n_rays")},
                            "selected": "reference_limb"}
        else:
            coarse = register(reference_proxy, item[0], half_geometry, allow_rotation=True)
            approximate = coarse["reference_to_input"] @ np.array([geometry.moon_xy[0], geometry.moon_xy[1], 1.0])
            measured = fit_limb(luminances[index], approximate[:2], geometry.moon_radius_px,
                                n_rays=720, search_frac=0.08, smooth_px=1.1, n_iter=4)
            linear = np.asarray(coarse["reference_to_input"], dtype=np.float64)[:, :2] if cfg.get("allow_rotation", False) else np.eye(2)
            translation = np.asarray(measured["xy"]) - linear @ np.asarray(reference_fit["xy"])
            matrix = np.hstack([linear, translation[:, None]])
            half = matrix.copy()
            half[:, 2] = (matrix[:, 2] - 0.5 + matrix[:, :2] @ np.array([0.5, 0.5])) / 2
            moving_residual, moving_valid = radial_residual(item[0], half_geometry)
            aligned = cv2.warpAffine(moving_residual, half, (ref_residual.shape[1], ref_residual.shape[0]),
                                     flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                                     borderMode=cv2.BORDER_CONSTANT)
            mask = ref_valid & moving_valid & np.isfinite(aligned)
            correlation = float(np.corrcoef(ref_residual[mask], aligned[mask])[0, 1]) if mask.sum() >= 100 else -1
            if not math.isfinite(correlation) or correlation < 0.25:
                raise RuntimeError(f"Limb registration rejected by coronal correlation: {correlation:.4f}")
            registration = dict(coarse)
            registration.update({"selected": "limb_rigid" if cfg.get("allow_rotation", False) else "limb_translation",
                "reference_to_input": matrix.tolist(),
                "moon_fit": {key: measured[key] for key in ("xy", "r", "rms", "n_used", "n_rays")},
                "correlation": correlation, "coarse_ecc": coarse["ecc"]})
        registrations.append(registration)
        matrices.append(matrix)
        moon_geometries.append(registration["moon_fit"])
    frames = []
    for index, (path, kind, info, matrix, moon_fit) in enumerate(zip(paths, kinds, meta, matrices, moon_geometries)):
        frame = {"path": str(path), "kind": kind, "iso": info["iso"], "exposure_s": info["exposure_s"],
                 "black": black, "white": white, "linearity_fraction": fraction,
                 "reference_to_input": matrix.tolist(), "moon_xy": list(moon_fit["xy"]),
                 "moon_radius_px": moon_fit["r"], "train": profile.get("train", "one")}
        for key in ("dark", "flat"):
            if cfg.get(key):
                frame[key] = str(Path(cfg[key]).expanduser().resolve())
        frames.append(frame)
    recipe = {"geometry": cfg["geometry"] if isinstance(cfg["geometry"], dict) else json.loads(Path(cfg["geometry"]).read_text()),
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
        filter_cfg.update({"input": result["files"]["linear"], "geometry": result["files"]["geometry"],
                           "valid": result["files"]["valid"], "coverage": result["files"]["coverage"],
                           "alpha": result["files"]["alpha"], "out": str(out / "filters")})
        filter_result = run_filters(filter_cfg)
        images += filter_result["images"]
    receipt = {"product": "PixInsight AEL linear master workflow", "runtime": runtime(),
               "recipe": str(recipe_path), "ael_receipt": result["receipt"], "metadata": meta,
               "registrations": registrations, "images": images,
               "filters_receipt": filter_result["receipt"] if filter_result else None,
               "gates": ael_receipt["gates"], "credit": CREDIT}
    receipt_path = out / "AEL_WORKFLOW_RECEIPT.json"
    receipt_path.write_text(json.dumps(receipt, indent=1, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "operation": "master", "out": str(out), "images": images,
            "pixelmath": filter_result["pixelmath"] if filter_result else [],
            "receipt": str(receipt_path), "gates": ael_receipt["gates"],
            "registrations": registrations}


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
