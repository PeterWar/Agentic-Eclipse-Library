#!/usr/bin/env python3
"""Registration must follow the Sun when the Moon moves across it.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

During totality the Moon moves relative to the Sun (28.5 px in 105 s on a 2026 train).
The corona is fixed on the Sun, so the stack must be registered on the Sun; each frame
keeps its own measured Moon only for its mask. Three synthetic frames share a telescope
drift; the Moon moves another 1.6 and 3.2 px. Truth for reference_to_input is the drift.
A control run with a still Moon must pass too, so a failure points at the lunar motion.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

import numpy as np
import tifffile

from ael.geometry import EclipseGeometry
from ael.synthetic import SyntheticScene

SHAPE = (480, 600)
SUN = np.array([300.0, 240.0])
MOON = SUN + [1.0, -0.5]
DRIFT = [np.array([0.0, 0.0]), np.array([2.0, -1.5]), np.array([-2.5, 2.0])]
EXPOSURES = [0.01, 0.02, 0.04]


def run_case(root: Path, lunar: list[np.ndarray], args) -> dict:
    root.mkdir()
    geometry = EclipseGeometry(shape=SHAPE, sun_xy=tuple(SUN), sun_radius_px=40, moon_xy=tuple(MOON),
                               moon_radius_px=41.2, north_deg=17, arcsec_per_px=8, note="Lunar motion test")
    scene = SyntheticScene(sun_radius_px=40, seed=73, n_rays=160, psf_sigma_px=0.9)
    frames = []
    for index, (drift, moon, exposure) in enumerate(zip(DRIFT, lunar, EXPOSURES)):
        image = scene.radiance(SHAPE, tuple(SUN + drift), tuple(MOON + drift + moon)).astype(np.float32) / 10
        path = root / f"frame_{index}.tif"
        tifffile.imwrite(path, np.stack([image * 1.03, image, image * 0.96], axis=-1) * exposure, photometric="rgb")
        subprocess.run([args.exiftool, "-overwrite_original", f"-ExposureTime={exposure}", "-ISO=100",
                        "-Make=Synthetic", "-Model=LunarMotion", str(path)], capture_output=True, check=True)
        frames.append(str(path))
    config = {"frames": frames, "reference": 0, "geometry": json.loads(geometry.to_json()),
              "camera": {"black": 0, "white": 1e6, "linearity_fraction": 0.95, "train": "synthetic"},
              "out": str(root / "output"), "run_filters": False}
    (root / "config.json").write_text(json.dumps(config), encoding="utf-8")
    helper = args.repo / "plugins/pixinsight-ael/python/ael_workflow.py"
    env = dict(os.environ, PYTHONPATH=f"{args.repo}:{helper.parent}", PYTHONDONTWRITEBYTECODE="1")
    completed = subprocess.run([args.python, str(helper), "master", str(root / "config.json")],
                               text=True, capture_output=True, env=env, timeout=900, check=False)
    result = json.loads(completed.stdout[completed.stdout.find("{"):completed.stdout.rfind("}") + 1])
    case = {"lunar_motion_px": [m.tolist() for m in lunar], "workflow_ok": result.get("ok"),
            "message": result.get("message")}
    if result.get("ok"):
        recipe = json.loads((root / "output/stack_recipe.json").read_text())
        measured = [np.asarray(frame["reference_to_input"])[:, 2] for frame in recipe["frames"]]
        case["sun_error_px"] = [float(np.linalg.norm(t - d)) for t, d in zip(measured, DRIFT)]
        case["passed"] = max(case["sun_error_px"]) < 0.1
    else:
        case["passed"] = False
    return case


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--exiftool", default="exiftool")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {"gate": "max translation error against the Sun < 0.1 px"}
    with tempfile.TemporaryDirectory(prefix="ael-lunar-") as temporary:
        report["still_moon"] = run_case(Path(temporary) / "still", [np.zeros(2)] * 3, args)
        report["moving_moon"] = run_case(Path(temporary) / "moving",
                                         [np.zeros(2), np.array([1.5, 0.5]), np.array([3.0, 1.0])], args)
    report["ok"] = report["still_moon"]["passed"] and report["moving_moon"]["passed"]
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "LUNAR_MOTION.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
