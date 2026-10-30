#!/usr/bin/env python3
"""Automation helpers for the Photoshop AEL workflow.

MIT License
Copyright (c) 2026 Pere Guerra Serra

Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

The AEL package remains unchanged. This module measures metadata and registration,
writes declared recipes, and exports filter layers for Photoshop/PixelMath.
"""
from __future__ import annotations

import argparse
import calendar
import json
import math
import os
from pathlib import Path
import re
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


def capture_time(text) -> tuple[float | None, float]:
    """Seconds on the camera's clock when a frame was taken, and how finely that time is known (EXIF or FITS)."""
    match = re.match(r"(\d{4})[:-](\d\d)[:-](\d\d)[ T](\d\d):(\d\d):(\d\d)(\.\d+)?", str(text or "").strip())
    if not match:
        return None, 1.0
    seconds = calendar.timegm(tuple(int(v) for v in match.groups()[:6]) + (0, 0, 0))
    fraction = match.group(7)
    return seconds + (float(fraction) if fraction else 0.0), 0.01 if fraction else 1.0


def metadata(path: Path) -> dict:
    if path.suffix.lower() in (".fits", ".fit", ".fts"):
        # Astronomical cameras write exposure and gain in the FITS header, not in EXIF.
        from astropy.io import fits
        header = fits.getheader(path)
        exposure = next((header[k] for k in ("EXPTIME", "EXPOSURE") if k in header), None)
        if exposure is None:
            raise ValueError(f"Missing EXPTIME/EXPOSURE in the FITS header: {path}")
        gain = next((header[k] for k in ("ISOSPEED", "ISO", "GAIN") if k in header), 0)
        time_s, resolution = capture_time(header.get("DATE-OBS"))
        return {"exposure_s": number(exposure), "iso": number(gain),
                "make": str(header.get("INSTRUME", "")), "model": str(header.get("TELESCOP", "")),
                "time_s": time_s, "time_resolution_s": resolution}
    run = subprocess.run([exiftool_path(), "-json", "-ExposureTime", "-ISO", "-Make", "-Model", "-DateTimeOriginal",
                          "-SubSecDateTimeOriginal", str(path)], text=True, capture_output=True, timeout=30, check=False)
    if run.returncode != 0:
        raise RuntimeError(f"ExifTool failed for {path}: {run.stderr.strip()}")
    values = json.loads(run.stdout)[0]
    if "ExposureTime" not in values or "ISO" not in values:
        raise ValueError(f"Missing exposure or ISO metadata: {path}")
    time_s, resolution = capture_time(values.get("SubSecDateTimeOriginal") or values.get("DateTimeOriginal"))
    return {"exposure_s": number(values["ExposureTime"]), "iso": number(values["ISO"]),
            "make": values.get("Make", ""), "model": values.get("Model", ""),
            "time_s": time_s, "time_resolution_s": resolution}


RAW_EXTENSIONS = {".cr2", ".cr3", ".nef", ".arw", ".dng", ".raf", ".orf", ".rw2"}


def raw_levels(path: Path) -> dict:
    """Black, white and linear ceiling of a RAW frame.

    Black is measured on the sensor's covered border (the raw samples outside the visible area) when it has one: LibRaw
    declares [0, 32, 96, 64] for a Canon EOS R6 Mark III whose covered border reads 512 (507-518), and the declared value
    is used only without a border (a Sony declares 512, which its border confirms). White is the level LibRaw declares
    (where the sensor clips). The sensor stops being linear before it clips (about 85 % of the range on the R6 Mark
    III), so only 85 % of the range from black to white counts as linear.
    """
    import rawpy
    with rawpy.imread(str(path)) as raw:
        declared = [float(v) for v in raw.black_level_per_channel]
        white = float(raw.white_level)
        full = raw.raw_image
        sizes = raw.sizes
        covered = np.ones(full.shape, bool)
        covered[sizes.top_margin:sizes.top_margin + sizes.height, sizes.left_margin:sizes.left_margin + sizes.width] = False
        border = full[covered]
    if border.size >= 10000:
        black = float(np.median(border))
        source = (f"black {black:g} measured on the covered border of the sensor ({border.size} samples; LibRaw declares "
                  f"{declared}); white {white:g} as LibRaw declares it; linear up to 85 % of the range")
    else:
        black = float(np.median(declared))
        source = f"black {black:g} and white {white:g} as LibRaw declares them (no covered border); linear up to 85 % of the range"
    return {"black": black, "white": white, "linearity_fraction": 0.85, "black_declared": declared, "source": source}


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
        return {"black": 0.0, "white": white, "linearity_fraction": 0.95,
                "source": f"black 0 (calibrated frame); saturation at {white:g}, where {count} samples of one channel "
                          "share the highest value"}
    return {"black": 0.0, "white": 2.0 * highest, "linearity_fraction": 0.95,
            "source": "black 0 (calibrated frame); no saturation plateau, so nothing is marked as saturated"}


def listed(value) -> list[Path]:
    """One file or several, as a configuration names them."""
    if not value:
        return []
    values = [value] if isinstance(value, (str, Path)) else list(value)
    return [Path(item).expanduser().resolve() for item in values if str(item).strip()]


def same_exposure(a: float, b: float) -> bool:
    return abs(a - b) <= 1e-3 * max(a, b)


def exposure_text(seconds: float) -> str:
    return f"1/{1 / seconds:.0f} s" if seconds < 0.5 else f"{seconds:g} s"


def recorded_metadata(path: Path) -> dict | None:
    """Exposure, ISO and camera of a calibration file, or None when it records none (a master made elsewhere)."""
    if path.suffix.lower() == ".npy":
        return None
    try:
        return metadata(path)
    except (ValueError, KeyError, OSError):
        return None


def calibration_plan(paths: list[Path], kinds: list[str], meta: list[dict], dark_value, flat_value) -> dict:
    """Which master dark and which master flat calibrate each frame, checked before anything is computed.

    Darks: one file is a master dark (a single dark frame is a master of one); several are combined into one master
    dark for each exposure, because a dark holds the dark current of its own exposure and ISO. Each frame takes the
    master of its own exposure, and a frame whose exposure has no dark stops the run. A master dark whose file records
    no exposure is taken only when all the frames have one exposure. Flats: one file is a master flat (or a single flat
    frame); several are combined into one master flat for every frame.
    """
    darks, flats = listed(dark_value), listed(flat_value)
    for path in darks + flats:
        if not path.is_file():
            raise FileNotFoundError(f"Calibration file not found: {path}")
    raw_frames = kinds[0] == "raw"
    for label, files in (("dark", darks), ("flat", flats)):
        raw = [path.suffix.lower() in RAW_EXTENSIONS for path in files]
        if any(raw) and not raw_frames:
            raise ValueError(f"The frames are TIFF or FITS files and a {label} is a RAW file; give the {label}s converted "
                             "as the frames were, or as one master.")
        if any(raw) and not all(raw):
            raise ValueError(f"Give the {label}s either as RAW files or as one master, not both.")
    cameras = {(item["make"], item["model"]) for item in meta}
    plan = {"darks": [], "frame_dark": [None] * len(paths), "flat": None}
    if darks:
        recorded = [recorded_metadata(path) for path in darks]
        unknown = [path.name for path, item in zip(darks, recorded) if item is None]
        if unknown and len(darks) > 1:
            raise ValueError("These darks record no exposure, so AEL cannot tell which frames each one calibrates: "
                             f"{', '.join(unknown)}. Give the dark frames as the camera wrote them, or one master dark.")
        if unknown:
            exposures = sorted({item["exposure_s"] for item in meta})
            if len(exposures) > 1:
                raise ValueError(f"{darks[0].name} records no exposure, and the frames have {len(exposures)} exposures "
                                 f"({', '.join(exposure_text(e) for e in exposures)}); a master dark holds the dark "
                                 "current of one exposure. Give the dark frames as the camera wrote them (AEL makes "
                                 "a master dark for each exposure), or leave the darks empty.")
            plan["darks"] = [{"exposure_s": None, "iso": None, "files": [str(darks[0])],
                              "note": "master dark given; its file records no exposure, so it was not checked "
                                      "against the frames"}]
            plan["frame_dark"] = [0] * len(paths)
        else:
            for path, item in zip(darks, recorded):
                if (item["make"], item["model"]) not in cameras:
                    raise ValueError(f"The dark {path.name} was taken with {item['make']} {item['model']}, not with "
                                     "the camera of the frames.")
                if item["iso"] != meta[0]["iso"]:
                    raise ValueError(f"The dark {path.name} is at ISO {item['iso']:g} and the frames at ISO "
                                     f"{meta[0]['iso']:g}; a dark must have the ISO of the frames.")
                group = next((g for g in plan["darks"] if same_exposure(g["exposure_s"], item["exposure_s"])), None)
                if group is None:
                    group = {"exposure_s": item["exposure_s"], "iso": item["iso"], "files": []}
                    plan["darks"].append(group)
                group["files"].append(str(path))
            missing = []
            for index, (path, item) in enumerate(zip(paths, meta)):
                match = next((i for i, g in enumerate(plan["darks"]) if same_exposure(g["exposure_s"], item["exposure_s"])),
                             None)
                if match is None:
                    missing.append(f"{path.name} ({exposure_text(item['exposure_s'])})")
                plan["frame_dark"][index] = match
            if missing:
                raise ValueError(f"No dark has the exposure of {'; '.join(missing)}. The darks have "
                                 f"{', '.join(exposure_text(g['exposure_s']) for g in plan['darks'])}. A dark holds the "
                                 "dark current of its own exposure: add darks with every exposure of the frames, or "
                                 "leave the darks empty.")
    if flats:
        for path in flats:
            item = recorded_metadata(path)
            if item and (item["make"], item["model"]) not in cameras:
                raise ValueError(f"The flat {path.name} was taken with {item['make']} {item['model']}, not with the "
                                 "camera of the frames.")
        plan["flat"] = {"files": [str(path) for path in flats],
                        "kind": "raw" if flats[0].suffix.lower() in RAW_EXTENSIONS else "data"}
    return plan


def _visible_raw(path: Path) -> np.ndarray:
    import rawpy
    with rawpy.imread(str(path)) as raw:
        return raw.raw_image_visible.copy()


MEDIAN_UP_TO = 25


def _combine(files: list[Path], load) -> tuple[np.ndarray, str]:
    """One master from calibration files: the file itself, the per-pixel median of up to 25 files, or, from more, the
    mean without the values beyond 3 standard deviations, in two passes that read one file at a time (a long series of
    darks does not fit in memory)."""
    if len(files) == 1:
        return np.asarray(load(files[0]), np.float32), "the file itself"
    if len(files) <= MEDIAN_UP_TO:
        arrays = [load(path) for path in files]
        out = np.empty(np.shape(arrays[0]), np.float32)
        for start in range(0, out.shape[0], 256):
            out[start:start + 256] = np.median(np.stack([a[start:start + 256] for a in arrays]), axis=0)
        return out, f"per-pixel median of {len(files)} files"
    total = squares = None
    for path in files:
        array = np.asarray(load(path), np.float64)
        total = array.copy() if total is None else total + array
        squares = array * array if squares is None else squares + array * array
    mean = total / len(files)
    spread = 3 * np.maximum(np.sqrt(np.maximum(squares / len(files) - mean ** 2, 0)), 1e-6)
    del total, squares
    kept_sum, kept = np.zeros_like(mean), np.zeros(mean.shape, np.uint32)
    for path in files:
        array = np.asarray(load(path), np.float64)
        keep = np.abs(array - mean) <= spread
        kept_sum += np.where(keep, array, 0)
        kept += keep
    return (kept_sum / np.maximum(kept, 1)).astype(np.float32), \
        f"per-pixel mean of {len(files)} files without the values beyond 3 standard deviations (two passes)"


def _flat_planes(array: np.ndarray, pattern) -> np.ndarray:
    """Colour planes of a flat: the CFA planes of a mosaic, or the channels of an RGB image."""
    if array.ndim == 2:
        return calibrate.split_cfa(array, np.asarray(pattern))[0]
    return np.moveaxis(array, -1, 0)


def _normalise_planes(planes: np.ndarray) -> np.ndarray:
    """Each plane divided by its median in the central annulus, as ael.calibrate.master_flat does."""
    _, h, w = planes.shape
    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot(xx - (w - 1) / 2, yy - (h - 1) / 2) / min(h, w)
    ring = (rr >= 0.05) & (rr <= 0.18)
    out = []
    for plane in planes.astype(np.float32):
        level = float(np.nanmedian(plane[ring]))
        if not level > 0:
            raise ValueError("A flat has no positive signal in its centre")
        out.append(plane / level)
    return np.stack(out)


FLAT_NO_VALUE_BELOW = 0.1


def native_layout(path: Path, kind: str) -> tuple[tuple, list | None]:
    """Shape of a frame as AEL stacks it (the visible sensor area of a RAW file) and its CFA pattern (None for RGB)."""
    if kind == "raw":
        raw = calibrate.read_raw(path, full=False)
        return tuple(raw["bayer"].shape), np.asarray(raw["pattern"]).tolist()
    return tuple(np.shape(io.load_array(path))), None


def build_calibration(plan: dict, level: dict, native: tuple, pattern, raw_frames: bool, folder: Path) -> dict:
    """Make in folder the master darks that the frames use and the master flat; what was done to make them, and each
    frame's files (names inside folder)."""
    folder.mkdir(parents=True, exist_ok=True)
    report = {"darks": [], "flat": None, "frames": [{"dark": None, "flat": None} for _ in plan["frame_dark"]]}
    for index, group in enumerate(plan["darks"]):
        files = [Path(p) for p in group["files"]]
        if index not in plan["frame_dark"]:
            report["darks"].append(dict(group, master=None, note="not used: no frame has this exposure"))
            continue

        def load(path: Path) -> np.ndarray:
            array = _visible_raw(path) if path.suffix.lower() in RAW_EXTENSIONS else calibrate.load_calibration_frame(path)
            if array.shape != native:
                raise ValueError(f"The dark {path.name} measures {array.shape} and the frames {native}: a dark must "
                                 "come from the camera of the frames, at full size.")
            return array
        master, method = _combine(files, load)
        scaled = None
        if raw_frames:
            # A dark reads the black level plus a little dark current. A master saved in 0-1 (astronomy programs keep
            # raw values divided by 65535) is brought back to the raw levels, and the same check then confirms it.
            what =f"darks of {exposure_text(group['exposure_s'])}" if group["exposure_s"] else f"master dark {files[0].name}"
            if not any(p.suffix.lower() in RAW_EXTENSIONS for p in files) and float(np.nanmax(master)) <= 1.0:
                master, scaled = master * 65535.0, "values in 0-1 multiplied by 65535 (raw levels kept as 0-1)"
            offset = float(np.median(master)) - level["black"]
            if abs(offset) > 0.05 * (level["white"] - level["black"]):
                raise ValueError(f"The {what} read{'s' if not group['exposure_s'] else ''} {offset:+.0f} levels from "
                                 f"the black level of the frames ({level['black']:g}): "
                                 + ("they do not look like darks (taken with the lens covered)." if offset > 0 else
                                    "it is not in the raw levels of the frames. Give the dark frames as the camera "
                                    "wrote them."))
        name = f"master_dark_{index + 1}.npy"
        np.save(folder / name, master)
        report["darks"].append(dict(group, master=name, n_files=len(files), method=method, scaled=scaled,
                                    median_level=float(np.median(master))))
        for frame, used in zip(report["frames"], plan["frame_dark"]):
            if used == index:
                frame["dark"] = name
    if plan["flat"]:
        files = [Path(p) for p in plan["flat"]["files"]]
        if plan["flat"]["kind"] == "raw":
            flat_level = raw_levels(files[0])
            ceiling = flat_level["black"] + flat_level["linearity_fraction"] * (flat_level["white"] - flat_level["black"])
            planes, info = calibrate.master_flat(files, black=flat_level["black"], saturation=ceiling, visible=True)
            method = dict(info, method="ael.calibrate.master_flat: each plane normalised on the central annulus, "
                                       "weighted mean with rejection", black_source=flat_level["source"])
            method.pop("pattern", None)
        else:
            def load(path: Path) -> np.ndarray:
                array = np.asarray(calibrate.load_calibration_frame(path), np.float32)
                if array.shape != native:
                    raise ValueError(f"The flat {path.name} measures {array.shape} and the frames {native}: a flat "
                                     "must come from the camera of the frames, at full size.")
                return _normalise_planes(_flat_planes(array, pattern))
            planes, combined = _combine(files, load)
            method = {"n_frames": len(files), "method": f"each plane normalised on the central annulus; {combined}"}
        master = calibrate.merge_cfa(planes) if raw_frames else np.moveaxis(planes, 0, -1)
        if raw_frames and master.shape != native and all(0 <= n - m <= 1 for n, m in zip(native, master.shape)):
            # A sensor with an odd side (4639 x 6959 on a Canon EOS R6 Mark III): its last row or column makes no 2x2
            # cell, so the flat has no value there.
            master = np.pad(master, [(0, n - m) for n, m in zip(native, master.shape)], constant_values=np.nan)
        if master.shape != native:
            raise ValueError(f"The flats give a master of {master.shape} and the frames measure {native}: a flat must "
                             "come from the camera of the frames, at full size.")
        # Where the flats saw no light (saturated or rejected in every flat, a dead pixel) the flat has no value, and
        # the frames are left without data there.
        no_value = ~np.isfinite(master) | (master < FLAT_NO_VALUE_BELOW)
        master = np.where(no_value, np.nan, master).astype(np.float32)
        np.save(folder / "master_flat.npy", master)
        report["flat"] = dict(method, files=[str(p) for p in files], master="master_flat.npy",
                              samples_without_value=int(no_value.sum()), no_value_below=FLAT_NO_VALUE_BELOW,
                              median_per_plane=[float(np.nanmedian(p)) for p in _flat_planes(master, pattern)])
        for frame in report["frames"]:
            frame["flat"] = "master_flat.npy"
    return report


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
              "note": "Photoshop workflow; portable AEL filters, not historical layer replay"}
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
    receipt = {"product": "Photoshop AEL filter layers", "runtime": runtime(),
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


def frame_luminance(path: Path, kind: str, black: float, white: float, fraction: float,
                    dark: np.ndarray | None = None, flat: np.ndarray | None = None):
    """Full-resolution luminance above black (or above the master dark, divided by the master flat), its usable pixels,
    native shape and CFA pattern.

    The luminance keeps saturated samples (clipped) for the limb fit; the usable mask drops
    them, together with non-positive samples and pixels without a flat value, for the solar
    registration. Saturation is decided on the raw value, before any subtraction.
    """
    ceiling = fraction * (white - black)
    if kind == "raw":
        raw = calibrate.read_raw(path, full=False)
        bayer = raw["bayer"].astype(np.float32)
        value = calibrate.calibrate(bayer, black if dark is None else dark, flat)
        green, _ = calibrate.green_plane(value, raw["pattern"])
        _, bad = calibrate.green_plane(value, raw["pattern"], bayer - black >= ceiling)
        return green, ~bad & (green > 0), bayer.shape, np.asarray(raw["pattern"]).tolist()
    array = io.load_array(path).astype(np.float32)
    if array.ndim != 3 or array.shape[-1] != 3:
        raise ValueError(f"Linear RGB input must be HxWx3: {path}")
    value = calibrate.calibrate(array, black if dark is None else dark, flat)
    lum = (value[..., 0] + 2 * value[..., 1] + value[..., 2]) / 4
    usable = np.isfinite(lum) & (lum > 0) & ~(array - black >= ceiling).any(axis=-1)
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
                   rmax_rsun: float = 3.0, max_lunar_px: float | None = None,
                   lunar_basis: str = "during a totality") -> dict:
    """Moon of the moving frame from its own limb; registration on the Sun from the corona."""
    moon = measure_moon(moving[0], reference_moon["xy"], reference_moon["r"])
    moon_shift = np.asarray(moon["xy"]) - np.asarray(reference_moon["xy"])
    solar = register_on_sun(reference, moving, geometry, reference_moon, moon, margin_px=margin_px,
                            rmax_rsun=rmax_rsun, initial=moon_shift)
    lunar = moon_shift - np.asarray(solar["translation"])
    if max_lunar_px is not None and np.hypot(*lunar) > max_lunar_px:
        raise RuntimeError(f"aligned on the Sun, the Moon would have moved {np.hypot(*lunar):.1f} px across it, and "
                           f"it can move at most {max_lunar_px:.1f} px {lunar_basis}: the alignment on the Sun is "
                           "wrong, or the frames are not of one totality")
    return dict(solar, selected="sun_translation", moon_fit={key: moon[key] for key in MOON_KEYS},
                lunar_shift_px=lunar.tolist(), lunar_bound_px=max_lunar_px, lunar_bound_basis=lunar_basis)


# The Moon crosses the Sun at most about 0.6"/s (its own motion at perigee less the Sun's; the Earth's rotation only
# slows it for an observer), and in a total eclipse it looks at least as large as the Sun, at least 944" in radius. A
# Moon of R px therefore crosses at most 0.65 * R / 944 px in a second.
LUNAR_RATE_ARCSEC_PER_S = 0.65
MOON_RADIUS_MIN_ARCSEC = 944.0


def lunar_bound(geometry: EclipseGeometry, reference: dict, frame: dict) -> tuple[float, str]:
    """How far the Moon can move across the Sun between the reference frame and another one, and why."""
    # During totality the Moon crosses at most twice the difference of the radii, and the Moon never looks more than
    # about 8 % larger than the Sun: 0.16 lunar radii holds for every total eclipse, short or long.
    totality = 0.16 * geometry.moon_radius_px + 2
    if reference.get("time_s") is None or frame.get("time_s") is None:
        return totality, "during a totality"
    # the time between the starts of the two exposures, plus both exposures and how finely the times are known
    seconds = (abs(frame["time_s"] - reference["time_s"]) + frame["exposure_s"] + reference["exposure_s"]
               + max(frame["time_resolution_s"], reference["time_resolution_s"]))
    bound = LUNAR_RATE_ARCSEC_PER_S * geometry.moon_radius_px / MOON_RADIUS_MIN_ARCSEC * seconds + 2
    if bound >= totality:
        return totality, "during a totality"
    return bound, f"in the {seconds:.1f} s between the two frames"


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
        fraction = float(profile.get("linearity_fraction", 0.95))
        levels = [{"black": float(profile["black"]), "white": float(profile["white"]), "linearity_fraction": fraction,
                   "source": "camera profile given"} for _ in paths]
    else:
        # Not given: each RAW file declares its own black and white levels; a calibrated TIFF/FITS frame is measured.
        profile = {}
        levels = [raw_levels(path) if kind == "raw" else data_levels(path) for path, kind in zip(paths, kinds)]
    for path, level in zip(paths, levels):
        if not level["white"] > level["black"]:
            raise ValueError(f"Invalid black/white levels for {path}: {level}")
        if not 0 < level["linearity_fraction"] <= 1:
            raise ValueError(f"Invalid linearity fraction for {path}: {level}")
    meta = [metadata(path) for path in paths]
    if len({item["iso"] for item in meta}) != 1:
        raise ValueError("Stack one ISO at a time")
    if len({(item["make"], item["model"]) for item in meta}) != 1:
        raise ValueError("Stack one camera/optical train at a time")
    if len(set(kinds)) > 1:
        raise ValueError("Give the frames either all as RAW files or all as TIFF or FITS files")
    # Darks and flats are checked before anything is read or written.
    plan = calibration_plan(paths, kinds, meta, cfg.get("dark"), cfg.get("flat"))
    if cfg.get("allow_rotation"):
        raise ValueError("Rotation is not supported: registration is a translation measured on the Sun")
    out = Path(cfg["out"]).expanduser().resolve()
    if out.exists():
        raise FileExistsError(f"Output directory already exists: {out}")
    calibration = {"darks": [], "flat": None, "frames": [{"dark": None, "flat": None} for _ in paths]}
    if plan["darks"] or plan["flat"]:
        # The masters are made first, into the output: the frames are registered calibrated, as they are stacked
        # (a dark signal that does not grow with the exposure would bias a registration on the logarithm).
        native, pattern = native_layout(paths[0], kinds[0])
        calibration = build_calibration(plan, levels[0], native if kinds[0] == "raw" else native[:2] + (3,), pattern,
                                        kinds[0] == "raw", out / "calibration")
        calibration["folder"] = str(out / "calibration")
    master_flat = (np.load(out / "calibration" / calibration["frames"][0]["flat"])
                   if calibration["frames"][0]["flat"] else None)
    data = [frame_luminance(path, kind, level["black"], level["white"], level["linearity_fraction"],
                            dark=np.load(out / "calibration" / files["dark"]) if files["dark"] else None,
                            flat=master_flat)
            for path, kind, level, files in zip(paths, kinds, levels, calibration["frames"])]
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
            # How far the Moon can cross the Sun: since the reference frame when both record when they were taken,
            # otherwise in a whole totality (or as the configuration gives it).
            if cfg.get("max_lunar_shift_px") is not None:
                bound, basis = float(cfg["max_lunar_shift_px"]), "as the configuration allows"
            else:
                bound, basis = lunar_bound(geometry, meta[reference_index], meta[index])
            try:
                registration = register_frame(reference, item[:2], geometry, reference_fit, margin_px=margin,
                                              rmax_rsun=rmax, max_lunar_px=bound, lunar_basis=basis)
            except RuntimeError as exc:
                raise RuntimeError(f"{paths[index].name} could not be aligned with {paths[reference_index].name}, so "
                                   f"no master was made: {exc}") from exc
            matrix = np.hstack([np.eye(2), np.asarray(registration["translation"])[:, None]])
        registration["reference_to_input"] = matrix.tolist()
        registrations.append(registration)
        matrices.append(matrix)
        moon_geometries.append(registration["moon_fit"])
    out.mkdir(parents=True, exist_ok=True)
    frames = []
    for index, (path, kind, info, matrix, moon_fit, level) in enumerate(
            zip(paths, kinds, meta, matrices, moon_geometries, levels)):
        frame = {"path": str(path), "kind": kind, "iso": info["iso"], "exposure_s": info["exposure_s"],
                 "black": level["black"], "white": level["white"], "linearity_fraction": level["linearity_fraction"],
                 "reference_to_input": matrix.tolist(), "moon_xy": list(moon_fit["xy"]),
                 "moon_radius_px": moon_fit["r"], "train": profile.get("train", "one")}
        for key in ("dark", "flat"):
            if calibration["frames"][index][key]:
                frame[key] = str(out / "calibration" / calibration["frames"][index][key])
        frames.append(frame)
    recipe = {"geometry": json.loads(geometry.to_json()),
              "frames": frames, "stack": {"canvas": "reference", "taper_start": 0.8,
              "moon_guard_px": 2, "limb_fade_px": 4, "band_sigma_px": 0,
              "hot_pixels": {"enabled": False}}, "note": "Photoshop automated metadata and measured registration"}
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
    receipt = {"product": "Photoshop AEL linear master workflow", "runtime": runtime(),
               "recipe": str(recipe_path), "ael_receipt": result["receipt"], "metadata": meta,
               "camera_levels": [dict(level, path=str(path)) for path, level in zip(paths, levels)],
               "calibration": calibration,
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
