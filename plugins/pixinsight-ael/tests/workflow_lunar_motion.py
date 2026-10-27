#!/usr/bin/env python3
"""Registration must follow the Sun when the Moon moves across it.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

During totality the Moon moves relative to the Sun (28.5 px in 105 s on a 2026 train).
The corona is fixed on the Sun, so the stack must be registered on the Sun; each frame
keeps its own measured Moon only for its mask. Three synthetic frames share a telescope
drift; the Moon moves another 1.6 and 3.2 px (0.07 lunar radii, about one totality) and
always covers the Sun. Truth for reference_to_input is the drift.
A control run with a still Moon must pass too, so a failure points at the lunar motion.
A third run adds photon and read noise and an exposure ladder that saturates the inner
corona of the longer frames (full well 15000 counts). A control with another corona and
the Moon in the same place (the limb matches, the corona does not) must be rejected.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
import tifffile

from ael.geometry import EclipseGeometry
from ael.synthetic import SyntheticScene, render_scene

SHAPE = (480, 600)
SUN = np.array([300.0, 240.0])
MOON = SUN + [-1.5, -0.5]
MOON_RADIUS = 44.0  # 1.10 R: the Moon covers the Sun in every frame, as in totality
DRIFT = [np.array([0.0, 0.0]), np.array([2.0, -1.5]), np.array([-2.5, 2.0])]
EXPOSURES = [0.01, 0.02, 0.04]
LADDER = [0.05, 0.2, 0.8]
FULL_WELL = 15000.0


def run_case(root: Path, lunar: list[np.ndarray], args, *, noisy: bool = False) -> dict:
    root.mkdir()
    geometry = EclipseGeometry(shape=SHAPE, sun_xy=tuple(SUN), sun_radius_px=40, moon_xy=tuple(MOON),
                               moon_radius_px=MOON_RADIUS, north_deg=17, arcsec_per_px=8, note="Lunar motion test")
    scene = SyntheticScene(sun_radius_px=40, moon_radius_px=MOON_RADIUS, seed=73, n_rays=160, psf_sigma_px=0.9)
    frames = []
    for index, (drift, moon, exposure) in enumerate(zip(DRIFT, lunar, LADDER if noisy else EXPOSURES)):
        path = root / f"frame_{index}.tif"
        if noisy:
            planes = [render_scene(scene, SHAPE, tuple(SUN + drift), tuple(MOON + drift + moon), 0.0,
                                   exposure * gain, full_well=FULL_WELL, seed=10 * index + channel)[0]
                      for channel, gain in enumerate((1.03, 1.0, 0.96))]
            tifffile.imwrite(path, np.stack(planes, axis=-1).astype(np.float32), photometric="rgb")
        else:
            image = scene.radiance(SHAPE, tuple(SUN + drift), tuple(MOON + drift + moon)).astype(np.float32) / 10
            tifffile.imwrite(path, np.stack([image * 1.03, image, image * 0.96], axis=-1) * exposure,
                             photometric="rgb")
        subprocess.run([args.exiftool, "-overwrite_original", f"-ExposureTime={exposure}", "-ISO=100",
                        "-Make=Synthetic", "-Model=LunarMotion", str(path)], capture_output=True, check=True)
        frames.append(str(path))
    config = {"frames": frames, "reference": 0, "geometry": json.loads(geometry.to_json()),
              "camera": {"black": 0, "white": FULL_WELL if noisy else 1e6, "linearity_fraction": 0.95,
                         "train": "synthetic"},
              "out": str(root / "output"), "run_filters": False}
    (root / "config.json").write_text(json.dumps(config), encoding="utf-8")
    helper = args.repo / "plugins/pixinsight-ael/python/ael_workflow.py"
    env = dict(os.environ, PYTHONPATH=f"{args.repo}:{helper.parent}", PYTHONDONTWRITEBYTECODE="1")
    completed = subprocess.run([args.python, str(helper), "master", str(root / "config.json")],
                               text=True, capture_output=True, env=env, timeout=900, check=False)
    result = json.loads(completed.stdout[completed.stdout.find("{"):completed.stdout.rfind("}") + 1])
    case = {"lunar_motion_px": [m.tolist() for m in lunar], "noisy": noisy, "workflow_ok": result.get("ok"),
            "message": result.get("message")}
    if result.get("ok"):
        recipe = json.loads((root / "output/stack_recipe.json").read_text())
        measured = [np.asarray(frame["reference_to_input"])[:, 2] for frame in recipe["frames"]]
        case["sun_error_px"] = [float(np.linalg.norm(t - d)) for t, d in zip(measured, DRIFT)]
        case["measured_lunar_shift_px"] = [r.get("lunar_shift_px") for r in result["registrations"]]
        # Diagnostic, not gated: how well each frame's own Moon was measured.
        case["moon_error_px"] = [float(np.linalg.norm(np.asarray(f["moon_xy"]) - (MOON + d + m)))
                                 for f, d, m in zip(recipe["frames"], DRIFT, lunar)]
        case["correlations"] = [r.get("correlation") for r in result["registrations"]]
        case["passed"] = max(case["sun_error_px"]) < 0.1
    else:
        case["passed"] = False
    return case


def unrelated_corona_rejected(args) -> dict:
    sys.path.insert(0, str(args.repo / "plugins/pixinsight-ael/python"))
    from ael_workflow import measure_moon, register_frame
    geometry = EclipseGeometry(shape=SHAPE, sun_xy=tuple(SUN), sun_radius_px=40, moon_xy=tuple(MOON),
                               moon_radius_px=MOON_RADIUS, north_deg=17)
    first = SyntheticScene(sun_radius_px=40, moon_radius_px=MOON_RADIUS, seed=73, n_rays=160)
    other = SyntheticScene(sun_radius_px=40, moon_radius_px=MOON_RADIUS, seed=99, n_rays=160,
                           streamers=((90.0, 20.0, 2.0), (200.0, 25.0, 1.5)))
    a = first.radiance(SHAPE, tuple(SUN), tuple(MOON))
    b = other.radiance(SHAPE, tuple(SUN), tuple(MOON))
    moon = measure_moon(a, geometry.moon_xy, MOON_RADIUS)
    try:
        register_frame((a, a > 0), (b, b > 0), geometry, moon, margin_px=6.0)
    except RuntimeError as exc:
        return {"rejected": True, "message": str(exc)}
    return {"rejected": False}


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
        moving = [np.zeros(2), np.array([1.5, 0.5]), np.array([3.0, 1.0])]
        report["moving_moon"] = run_case(Path(temporary) / "moving", moving, args)
        report["moving_moon_noisy"] = run_case(Path(temporary) / "noisy", moving, args, noisy=True)
    report["unrelated_corona"] = unrelated_corona_rejected(args)
    report["ok"] = (all(report[key]["passed"] for key in ("still_moon", "moving_moon", "moving_moon_noisy"))
                    and report["unrelated_corona"]["rejected"])
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "LUNAR_MOTION.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
