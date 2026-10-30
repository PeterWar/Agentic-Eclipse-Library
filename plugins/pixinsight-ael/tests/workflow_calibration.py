#!/usr/bin/env python3
"""Darks and flats of the linear master: several files make the masters, one file is the master.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

Three synthetic frames of one totality (ael.synthetic) at 0.01, 0.02 and 0.04 s are written as a sensor records them:
the corona times a flat field (vignetting and a dust shadow) plus a dark signal that grows with the exposure and has hot
pixels. There are three noisy darks for each exposure and three flats at different levels with a dead pixel. The
workflow must

* make one master dark for each exposure, the per-pixel median of its files, and give each frame the master of its
  own exposure;
* make the master flat (each plane normalised on the central annulus, then the per-pixel median), with no value at
  the dead pixel;
* stack what AEL stacks from the frames calibrated here by hand with those masters, with the same registration (this
  checks the calibration, not the registration), to float rounding; the same frames without calibration differ, so
  the comparison can fail;
* refuse, before writing anything: a frame whose exposure has no dark, a dark at another ISO, one master dark that
  records no exposure for frames of several exposures, a RAW dark for TIFF frames, and a flat of another camera;
* take one master dark that records no exposure when the frames have one exposure.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import numpy as np
import tifffile

from ael.geometry import EclipseGeometry
from ael.stack import stack_from_config
from ael.synthetic import SyntheticScene, render_scene
from ael_workflow import calibration_plan, metadata, run_master

SHAPE = (360, 480)
SUN = np.array([240.0, 180.0])
SUN_R = 40.0
MOON_R = 1.06 * SUN_R
EXPOSURES = [0.01, 0.02, 0.04]
DRIFT = [np.zeros(2), np.array([2.0, -1.5]), np.array([-2.5, 2.0])]
LUNAR = [np.zeros(2), np.array([0.8, 0.3]), np.array([1.6, 0.6])]
COLOUR = (1.03, 1.0, 0.96)
DEAD = (100, 150)


def tag(exiftool: str, path: Path, exposure: float, iso: int = 100, model: str = "Calibration") -> None:
    subprocess.run([exiftool, "-q", "-overwrite_original", f"-ExposureTime={exposure}", f"-ISO={iso}",
                    "-Make=Synthetic", f"-Model={model}", str(path)], check=True, capture_output=True)


def flat_field() -> np.ndarray:
    yy, xx = np.mgrid[0:SHAPE[0], 0:SHAPE[1]].astype(np.float32)
    r = np.hypot(xx - SHAPE[1] / 2, yy - SHAPE[0] / 2) / np.hypot(*SHAPE)
    dust = 1 - 0.15 * np.exp(-((xx - 330) ** 2 + (yy - 90) ** 2) / (2 * 9.0 ** 2))
    base = (1 - 0.5 * r ** 2) * dust
    return np.stack([base * k for k in (1.0, 0.98, 1.02)], axis=-1).astype(np.float32)


def dark_signal(exposure: float) -> np.ndarray:
    rng = np.random.default_rng(5)
    hot = np.zeros(SHAPE, np.float32)
    hot[rng.integers(0, SHAPE[0], 40), rng.integers(0, SHAPE[1], 40)] = 400.0
    plane = 5.0 + 300.0 * exposure + hot * exposure / 0.04
    return np.repeat(plane[..., None], 3, axis=-1).astype(np.float32)


def write(path: Path, array: np.ndarray) -> Path:
    tifffile.imwrite(path, np.asarray(array, np.float32), photometric="rgb")
    return path


def make_inputs(root: Path, exiftool: str) -> dict:
    scene = SyntheticScene(sun_radius_px=SUN_R, seed=73, n_rays=220, psf_sigma_px=1.0, moon_radius_px=MOON_R)
    flat = flat_field()
    frames, clean = [], []
    for index, (drift, moon, exposure) in enumerate(zip(DRIFT, LUNAR, EXPOSURES)):
        counts, _ = render_scene(scene, SHAPE, tuple(SUN + drift), tuple(SUN + drift + moon), 0.0, exposure,
                                 full_well=1e9, seed=200 + index)
        rgb = np.stack([counts * k for k in COLOUR], axis=-1).astype(np.float32)
        clean.append(rgb)
        path = write(root / f"frame_{index + 1}.tif", rgb * flat + dark_signal(exposure))
        tag(exiftool, path, exposure)
        frames.append(path)
    rng = np.random.default_rng(11)
    darks = {}
    for exposure in EXPOSURES:
        darks[exposure] = []
        for k in range(3):
            path = write(root / f"dark_{exposure:g}_{k + 1}.tif",
                         dark_signal(exposure) + rng.normal(0, 1.0, SHAPE + (3,)).astype(np.float32))
            tag(exiftool, path, exposure)
            darks[exposure].append(path)
    flats = []
    for k, level in enumerate((5000.0, 6000.0, 7000.0)):
        values = flat * level * (1 + rng.normal(0, 0.002, SHAPE + (3,))).astype(np.float32)
        values[DEAD] = 0.0                                   # a dead pixel: it sees no light in any flat
        path = write(root / f"flat_{k + 1}.tif", values)
        tag(exiftool, path, 0.01)
        flats.append(path)
    return {"frames": frames, "darks": darks, "flats": flats, "flat_truth": flat, "clean": clean}


def config(root: Path, inputs: dict, out: str, **extra) -> dict:
    geometry = EclipseGeometry(shape=SHAPE, sun_xy=tuple(SUN), sun_radius_px=SUN_R, moon_xy=tuple(SUN),
                               moon_radius_px=MOON_R, north_deg=0, arcsec_per_px=8, note="Calibration test")
    cfg = {"frames": [str(p) for p in inputs["frames"]], "reference": 0, "geometry": json.loads(geometry.to_json()),
           "camera": {"black": 0, "white": 1e6, "linearity_fraction": 0.95, "train": "synthetic"},
           "out": str(root / out), "run_filters": False}
    cfg.update(extra)
    return cfg


def normalised(array: np.ndarray) -> np.ndarray:
    h, w = array.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot(xx - (w - 1) / 2, yy - (h - 1) / 2) / min(h, w)
    ring = (rr >= 0.05) & (rr <= 0.18)
    return np.stack([array[..., c] / np.nanmedian(array[..., c][ring]) for c in range(3)], axis=-1)


def refused(cfg: dict) -> str:
    try:
        run_master(cfg)
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
    return "accepted"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exiftool", default=shutil.which("exiftool") or "/opt/homebrew/bin/exiftool")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {"synthetic": True, "gates": {}}
    gates = report["gates"]
    with tempfile.TemporaryDirectory(prefix="ael-calibration-") as temporary:
        root = Path(temporary) / "calibratge àè"
        root.mkdir()
        inputs = make_inputs(root, args.exiftool)
        all_darks = [str(p) for e in EXPOSURES for p in inputs["darks"][e]]
        cfg = config(root, inputs, "calibrated", dark=all_darks, flat=[str(p) for p in inputs["flats"]])
        result = run_master(cfg)
        out = Path(result["out"])
        receipt = json.loads((out / "AEL_WORKFLOW_RECEIPT.json").read_text())
        calibration = receipt["calibration"]
        folder = Path(calibration["folder"])
        recipe = json.loads((out / "stack_recipe.json").read_text())

        # one master dark per exposure, the median of its files, and each frame takes the one of its exposure
        masters = {}
        for group in calibration["darks"]:
            expected = np.median(np.stack([tifffile.imread(p) for p in group["files"]]), axis=0)
            master = folder / group["master"]
            masters[group["exposure_s"]] = (str(master), float(np.max(np.abs(np.load(master) - expected))))
        gates["one_master_dark_per_exposure"] = sorted(masters) == EXPOSURES and all(
            len(g["files"]) == 3 for g in calibration["darks"])
        gates["master_dark_is_the_median_of_its_files"] = max(v[1] for v in masters.values()) <= 1e-4
        gates["each_frame_takes_the_dark_of_its_exposure"] = [f["dark"] for f in recipe["frames"]] == [
            masters[e][0] for e in EXPOSURES]
        # the master flat: normalised planes, their median, no value at the dead pixel
        flat = np.load(folder / calibration["flat"]["master"])
        expected = np.median(np.stack([normalised(tifffile.imread(p)) for p in inputs["flats"]]), axis=0)
        expected[DEAD] = np.nan
        known = np.isfinite(expected)
        gates["master_flat_is_the_median_of_normalised_flats"] = (
            bool(np.array_equal(np.isfinite(flat), known)) and float(np.max(np.abs(flat[known] - expected[known]))) <= 1e-5)
        gates["dead_pixel_has_no_flat_value"] = bool(np.isnan(flat[DEAD]).all()) and \
            calibration["flat"]["samples_without_value"] == 3
        gates["every_frame_takes_the_master_flat"] = all(f["flat"] == str(folder / calibration["flat"]["master"]) for f in recipe["frames"])

        # the same registration, frames calibrated here by hand: AEL must stack the same master
        by_hand = json.loads(json.dumps(recipe))
        plain = json.loads(json.dumps(recipe))
        for index, (frame, path) in enumerate(zip(recipe["frames"], inputs["frames"])):
            light = tifffile.imread(path).astype(np.float32)
            calibrated = (light - np.load(frame["dark"])) / flat
            np.save(root / f"by_hand_{index}.npy", calibrated.astype(np.float32))
            for copy, source in ((by_hand, root / f"by_hand_{index}.npy"), (plain, path)):
                entry = copy["frames"][index]
                entry["path"] = str(source)
                entry.pop("dark", None)
                entry.pop("flat", None)
        for name, copy in (("by_hand", by_hand), ("plain", plain)):
            (root / f"{name}.json").write_text(json.dumps(copy), encoding="utf-8")
            stack_from_config(root / f"{name}.json", root / f"{name}_stack", progress=lambda *_: None)
        master = np.load(out / "master/linear.npy")
        hand = np.load(root / "by_hand_stack/linear.npy")
        plain_master = np.load(root / "plain_stack/linear.npy")
        both = np.isfinite(master) & np.isfinite(hand)
        scale = float(np.nanmedian(np.abs(hand)))
        difference = float(np.max(np.abs(master[both] - hand[both]))) / scale
        gates["master_equals_hand_calibration"] = (bool(np.array_equal(np.isfinite(master), np.isfinite(hand)))
                                                   and difference <= 1e-5)
        common = np.isfinite(plain_master) & np.isfinite(hand)
        control = float(np.max(np.abs(plain_master[common] - hand[common]))) / scale
        gates["control_without_calibration_differs"] = control > 0.05
        report["master"] = {"relative_max_difference_to_hand": difference, "control_relative_difference": control,
                            "flat_samples_without_value": calibration["flat"]["samples_without_value"]}

        # refusals, before anything is written
        darks_two = [str(p) for e in EXPOSURES[:2] for p in inputs["darks"][e]]
        other_iso = root / "dark_iso200.tif"
        shutil.copy2(inputs["darks"][0.04][0], other_iso)
        tag(args.exiftool, other_iso, 0.04, iso=200)
        np.save(root / "master_dark.npy", np.median(np.stack([tifffile.imread(p) for p in inputs["darks"][0.02]]), axis=0))
        (root / "dark.cr2").write_bytes(b"")
        other_camera = root / "flat_other_camera.tif"
        shutil.copy2(inputs["flats"][0], other_camera)
        tag(args.exiftool, other_camera, 0.01, model="Another camera")
        cases = {"missing_exposure": (dict(dark=darks_two), "No dark has the exposure of frame_3.tif (1/25 s)"),
                 "other_iso": (dict(dark=darks_two + [str(other_iso)]), "ISO 200"),
                 "master_without_exposure": (dict(dark=str(root / "master_dark.npy")), "records no exposure"),
                 "raw_dark_for_tiff_frames": (dict(dark=[str(root / "dark.cr2")]), "a dark is a RAW file"),
                 "flat_of_another_camera": (dict(flat=[str(other_camera)]), "not with the camera of the frames")}
        report["refusals"] = {}
        for name, (extra, expected_text) in cases.items():
            message = refused(config(root, inputs, f"refused_{name}", **extra))
            report["refusals"][name] = message
            gates[f"refuses_{name}"] = expected_text in message and not (root / f"refused_{name}").exists()

        # one master dark that records no exposure, for frames of one exposure: taken, and the receipt says so
        one = [inputs["frames"][1]]
        plan = calibration_plan([Path(p) for p in one], ["rgb"], [metadata(Path(p)) for p in one],
                                str(root / "master_dark.npy"), None)
        gates["master_dark_without_exposure_taken_for_one_exposure"] = (
            plan["frame_dark"] == [0] and "not checked" in plan["darks"][0]["note"])
    report["ok"] = all(gates.values())
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "CALIBRATION.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "failed": [k for k, v in gates.items() if not v], "master": report["master"]}))
    if not report["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
