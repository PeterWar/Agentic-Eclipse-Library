#!/usr/bin/env python3
"""Registration on the Sun with short, noisy exposures and an unrelated corona.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

A second, independent judge beside workflow_lunar_motion.py, written separately. The scene has
a Sun of 40 px and a Moon 6% larger, which covers the Sun in every frame; the Moon moves 4 px
across the Sun between the first and the last of three frames that also share a telescope drift.
Exposures are short (0.01, 0.02 and 0.04 s): the outer corona of the reference is close to the
read noise and the inner corona of the longest frame saturates. Truth for reference_to_input is
the drift.

Cases: a still Moon (control), a moving Moon, the moving Moon with photon and read noise, and a
frame of an unrelated corona (other streamers and orientation), which must be refused. With
noise the gate is three times the noise floor, measured in the same run through the workflow,
from noisy frames with no drift and no lunar motion.
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
from ael.synthetic import SyntheticScene, render_scene

SHAPE = (480, 600)
SUN = np.array([300.0, 240.0])
SUN_R = 40.0
MOON_R = 1.06 * SUN_R
DRIFT = [np.array([0.0, 0.0]), np.array([2.0, -1.5]), np.array([-2.5, 2.0])]
EXPOSURES = [0.01, 0.02, 0.04]
DIRECTION = np.array([np.cos(np.radians(24)), np.sin(np.radians(24))])
MOVING = [-2.0 * DIRECTION, np.zeros(2), 2.0 * DIRECTION]
FULL_WELL = 15000.0
SCENE = dict(sun_radius_px=SUN_R, n_rays=160, psf_sigma_px=0.9, moon_radius_px=MOON_R)


def scene(unrelated: bool = False) -> SyntheticScene:
    if unrelated:
        return SyntheticScene(seed=11, north_deg=40, **SCENE,
                              streamers=((80.0, 20.0, 2.0), (200.0, 22.0, 2.4), (330.0, 16.0, 1.6)))
    return SyntheticScene(seed=73, **SCENE)


def image(sc: SyntheticScene, drift, lunar, exposure: float, noise_seed: int | None) -> np.ndarray:
    sun, moon = tuple(SUN + drift), tuple(SUN + drift + lunar)
    if noise_seed is None:
        return (sc.radiance(SHAPE, sun, moon) * exposure / 10).astype(np.float32)
    counts, _ = render_scene(sc, SHAPE, sun, moon, 0.0, exposure, full_well=FULL_WELL, seed=noise_seed)
    return counts.astype(np.float32)


def run_case(root: Path, lunar: list[np.ndarray], args, *, noisy: bool = False,
             unrelated_from: int | None = None, drift: list | None = None, seed0: int = 100) -> dict:
    drift = DRIFT if drift is None else drift
    root.mkdir()
    geometry = EclipseGeometry(shape=SHAPE, sun_xy=tuple(SUN), sun_radius_px=SUN_R, moon_xy=tuple(SUN + lunar[0]),
                               moon_radius_px=MOON_R, north_deg=17, arcsec_per_px=8, note="Lunar motion test")
    frames = []
    for index, (shift, moon, exposure) in enumerate(zip(drift, lunar, EXPOSURES)):
        sc = scene(unrelated_from is not None and index >= unrelated_from)
        mono = image(sc, shift, moon, exposure, seed0 + index if noisy else None)
        path = root / f"frame_{index}.tif"
        tifffile.imwrite(path, np.stack([mono * 1.03, mono, mono * 0.96], axis=-1), photometric="rgb")
        subprocess.run([args.exiftool, "-overwrite_original", f"-ExposureTime={exposure}", "-ISO=100",
                        "-Make=Synthetic", "-Model=LunarMotion", str(path)], capture_output=True, check=True)
        frames.append(str(path))
    white = FULL_WELL if noisy else 1e6
    config = {"frames": frames, "reference": 0, "geometry": json.loads(geometry.to_json()),
              "camera": {"black": 0, "white": white, "linearity_fraction": 0.95, "train": "synthetic"},
              "out": str(root / "output"), "run_filters": False}
    (root / "config.json").write_text(json.dumps(config), encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=f"{args.repo}:{args.helper.parent}", PYTHONDONTWRITEBYTECODE="1")
    completed = subprocess.run([args.python, str(args.helper), "master", str(root / "config.json")],
                               text=True, capture_output=True, env=env, timeout=900, check=False)
    text = completed.stdout
    result = json.loads(text[text.find("{"):text.rfind("}") + 1]) if "{" in text else {"message": completed.stderr}
    case = {"lunar_motion_px": [m.tolist() for m in lunar], "noisy": noisy,
            "workflow_ok": bool(result.get("ok")), "message": result.get("message")}
    if result.get("ok"):
        recipe = json.loads((root / "output/stack_recipe.json").read_text())
        measured = [np.asarray(frame["reference_to_input"])[:, 2] for frame in recipe["frames"]]
        moons = [np.asarray(frame["moon_xy"]) for frame in recipe["frames"]]
        case["sun_error_px"] = [float(np.linalg.norm(t - d)) for t, d in zip(measured, drift)]
        # What a registration on the measured lunar limb would have given, for comparison.
        case["limb_registration_error_px"] = [float(np.linalg.norm(m - moons[0] - d)) for m, d in zip(moons, drift)]
        case["registrations"] = result["registrations"][1:]
    return case


def noise_floor(root: Path, args) -> dict:
    """Error of noisy frames with no drift and no lunar motion, through the workflow itself."""
    errors = []
    for k in range(2):
        case = run_case(root / f"floor_{k}", [np.zeros(2)] * 3, args, noisy=True,
                        drift=[np.zeros(2)] * 3, seed0=500 + 10 * k)
        if not case["workflow_ok"]:
            raise RuntimeError(case["message"])
        errors += case["sun_error_px"][1:]
    return {"errors_px": errors, "rms_px": float(np.sqrt(np.mean(np.square(errors))))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--exiftool", default="exiftool")
    parser.add_argument("--helper", type=Path, default=Path(__file__).resolve().parents[1] / "python/ael_workflow.py")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.repo, args.helper = args.repo.resolve(), args.helper.resolve()
    report = {"helper": str(args.helper), "gate_clean_px": 0.1}
    with tempfile.TemporaryDirectory(prefix="ael-lunar-") as temporary:
        root = Path(temporary)
        report["still_moon"] = run_case(root / "still", [np.zeros(2)] * 3, args)
        report["moving_moon"] = run_case(root / "moving", MOVING, args)
        report["moving_moon_noisy"] = run_case(root / "noisy", MOVING, args, noisy=True)
        report["unrelated_frame"] = run_case(root / "unrelated", [np.zeros(2)] * 3, args, noisy=True, unrelated_from=1)
        try:
            report["noise_floor"] = noise_floor(root, args)
            report["gate_noisy_px"] = 3 * report["noise_floor"]["rms_px"]
        except Exception as exc:
            report["noise_floor"] = {"error": f"{type(exc).__name__}: {exc}"}
            report["gate_noisy_px"] = 0.0

    def within(case: dict, gate: float) -> bool:
        return case["workflow_ok"] and max(case["sun_error_px"]) < gate

    moving = report["moving_moon"]
    report["gates"] = {
        "still_moon": within(report["still_moon"], 0.1),
        "moving_moon": within(moving, 0.1),
        # The case must really exercise lunar motion: a limb registration would fail it.
        "moving_moon_defeats_limb": moving["workflow_ok"] and max(moving["limb_registration_error_px"]) > 1.0,
        "moving_moon_noisy": within(report["moving_moon_noisy"], report["gate_noisy_px"]),
        "unrelated_frame_refused": not report["unrelated_frame"]["workflow_ok"],
    }
    report["ok"] = all(report["gates"].values())
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "LUNAR_MOTION.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "gates": report["gates"]}))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
