#!/usr/bin/env python3
"""One master dark must not calibrate frames of different exposures.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

AEL subtracts the dark before dividing by each frame's exposure, so a dark matches one
exposure only. The workflow must refuse before writing anything. With equal exposures
the same dark must get past this check.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
import tifffile

from ael_workflow import run_master


def frames(root: Path, exposures: list[float]) -> list[str]:
    paths = []
    for index, exposure in enumerate(exposures):
        path = root / f"frame_{index}.tif"
        tifffile.imwrite(path, np.ones((16, 16, 3), np.float32), photometric="rgb")
        subprocess.run(["exiftool", "-overwrite_original", f"-ExposureTime={exposure}", "-ISO=100",
                        "-Make=Synthetic", "-Model=DarkGuard", str(path)], capture_output=True, check=True)
        paths.append(str(path))
    return paths


def attempt(root: Path, exposures: list[float]) -> str:
    root.mkdir()
    np.save(root / "dark.npy", np.zeros((16, 16, 3), np.float32))
    config = {"frames": frames(root, exposures), "dark": str(root / "dark.npy"), "out": str(root / "out"),
              "camera": {"black": 0, "white": 1e6}, "run_filters": False,
              "geometry": {"shape": [16, 16], "sun_xy": [8, 8], "sun_radius_px": 3,
                           "moon_xy": [8, 8], "moon_radius_px": 3.1}}
    try:
        run_master(config)
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
    return "accepted"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="ael-dark-") as temporary:
        mixed = attempt(Path(temporary) / "mixed", [0.01, 0.04])
        equal = attempt(Path(temporary) / "equal", [0.02, 0.02])
        nothing_written = not (Path(temporary) / "mixed/out").exists()
    report = {"mixed_exposures": mixed, "equal_exposures": equal, "nothing_written": nothing_written,
              "ok": "master dark" in mixed and "master dark" not in equal and nothing_written}
    print(json.dumps(report, indent=1))
    if not report["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
