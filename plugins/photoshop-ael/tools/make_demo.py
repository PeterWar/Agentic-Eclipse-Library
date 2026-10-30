#!/usr/bin/env python3
"""Synthetic demonstration files for the four operations of the Photoshop bridge.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

Everything here is synthetic (ael.synthetic): no real eclipse frame is used or imitated. The Moon is 6 %
larger than the Sun and moves across it between the three master frames, as in a real totality.

    python make_demo.py --out demo
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
from ael.synthetic import SyntheticScene, render_scene

SHAPE = (720, 960)
SUN = np.array([480.0, 360.0])
SUN_R = 60.0
MOON_R = 1.06 * SUN_R
COLOUR = (1.03, 1.0, 0.96)


def rgb(mono: np.ndarray) -> np.ndarray:
    return np.stack([mono * k for k in COLOUR], axis=-1).astype(np.float32)


def geometry(moon_xy, note: str) -> EclipseGeometry:
    return EclipseGeometry(shape=SHAPE, sun_xy=tuple(SUN), sun_radius_px=SUN_R, moon_xy=tuple(moon_xy),
                           moon_radius_px=MOON_R, north_deg=17, arcsec_per_px=8, note=note)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--exiftool", default=shutil.which("exiftool") or "/opt/homebrew/bin/exiftool")
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise SystemExit(f"{out} exists: choose a new folder")
    scene = SyntheticScene(sun_radius_px=SUN_R, seed=73, n_rays=220, psf_sigma_px=1.0, moon_radius_px=MOON_R)

    one = out / "1_structure_polar"
    one.mkdir(parents=True)
    # Scaled to 0-1 so that Photoshop's 32-bit view shows the inner corona instead of a white frame.
    linear = scene.radiance(SHAPE, tuple(SUN), tuple(SUN))
    linear = linear / float(linear.max())
    tifffile.imwrite(one / "corona_linear.tif", rgb(linear), photometric="rgb", metadata=None,
                     description="Synthetic linear corona (ael.synthetic), float32 RGB, scaled to 0-1")
    level = float(np.percentile(linear[linear > 0], 99.5))
    display = np.arcsinh(20 * np.clip(linear, 0, None) / level) / np.arcsinh(20)
    tifffile.imwrite(one / "corona_display.tif", rgb(np.clip(display, 0, 1)), photometric="rgb", metadata=None,
                     description="Synthetic corona, asinh display range 0-1, float32 RGB")
    geometry(SUN, "Synthetic demonstration: structure and polar").to_json(one / "geometry.json")

    three = out / "3_master"
    three.mkdir()
    direction = np.array([np.cos(np.radians(24)), np.sin(np.radians(24))])
    drift = [np.zeros(2), np.array([2.0, -1.5]), np.array([-2.5, 2.0])]
    lunar = [-2.0 * direction, np.zeros(2), 2.0 * direction]
    exposures = [0.01, 0.02, 0.04]
    for index, (shift, moon, exposure) in enumerate(zip(drift, lunar, exposures)):
        counts, _ = render_scene(scene, SHAPE, tuple(SUN + shift), tuple(SUN + shift + moon), 0.0, exposure,
                                 full_well=15000.0, seed=200 + index)
        path = three / f"frame_{index + 1}.tif"
        tifffile.imwrite(path, rgb(counts), photometric="rgb", metadata=None,
                         description="Synthetic calibrated frame (ael.synthetic): counts above black")
        subprocess.run([args.exiftool, "-q", "-overwrite_original", f"-ExposureTime={exposure}", "-ISO=100",
                        "-Make=Synthetic", "-Model=AEL demonstration camera", str(path)], check=True)
    (three / "camera.json").write_text(json.dumps({"black": 0, "white": 15000, "linearity_fraction": 0.95,
                                                   "train": "synthetic demonstration"}, indent=1), encoding="utf-8")
    geometry(SUN + lunar[0], "Synthetic demonstration: reference frame of the master").to_json(three / "geometry.json")

    # A linear master for the filters operation: the same frames stacked by the bridge's own workflow.
    two = out / "2_filters" / "linear_master"
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
    from ael_workflow import run_master
    with tempfile.TemporaryDirectory(prefix="ael-demo-") as temporary:
        stacked = Path(temporary) / "master"
        run_master({"frames": [str(three / f"frame_{i}.tif") for i in (1, 2, 3)], "reference": 0,
                    "camera": json.loads((three / "camera.json").read_text()),
                    "geometry": str(three / "geometry.json"), "out": str(stacked), "run_filters": False})
        two.mkdir(parents=True)
        for name in ("linear.npy", "geometry.json", "valid.npy", "coverage.npy", "alpha.npy"):
            shutil.copy2(stacked / "master" / name, two / name)
    print(json.dumps({"out": str(out), "files": sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file())},
                     indent=1))


if __name__ == "__main__":
    main()
