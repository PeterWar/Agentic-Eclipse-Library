#!/usr/bin/env python3
"""Synthetic end-to-end test for the automated AEL PixInsight workflow.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback

import cv2
import numpy as np
import tifffile

from ael.geometry import EclipseGeometry
from ael.synthetic import SyntheticScene
from ael import io
from ael_workflow import measure_moon, register_frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    helper = args.repo / "plugins/pixinsight-ael/python/ael_workflow.py"
    report = {"ok": False, "synthetic": True}
    with tempfile.TemporaryDirectory(prefix="ael-workflow-") as temporary:
        root = Path(temporary) / "flux automàtic àè"
        root.mkdir()
        shape = (320, 400)
        geometry = EclipseGeometry(shape=shape, sun_xy=(198, 158), sun_radius_px=20,
                                   moon_xy=(198, 158), moon_radius_px=20.6,
                                   north_deg=17, arcsec_per_px=8, note="Synthetic workflow")
        scene = SyntheticScene(sun_radius_px=20, seed=73, n_rays=120, psf_sigma_px=0.8)
        base = scene.radiance(shape, geometry.sun_xy, geometry.moon_xy).astype(np.float32) / 10
        base = np.stack([base * 1.03, base, base * 0.96], axis=-1).astype(np.float32)
        matrices = [np.array([[1, 0, 0], [0, 1, 0]], np.float32),
                    np.array([[1, 0, 2.0], [0, 1, -1.5]], np.float32),
                    np.array([[1, 0, -2.5], [0, 1, 2.0]], np.float32)]
        exposures = [0.01, 0.02, 0.04]
        frames = []
        for index, (matrix, exposure) in enumerate(zip(matrices, exposures)):
            moving = cv2.warpAffine(base, matrix, (shape[1], shape[0]), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                                    borderMode=cv2.BORDER_CONSTANT, borderValue=0).astype(np.float32)
            path = root / f"frame_{index}.tif"
            tifffile.imwrite(path, moving * exposure, photometric="rgb")
            run = subprocess.run(["/opt/homebrew/bin/exiftool", "-overwrite_original", f"-ExposureTime={exposure}",
                                  "-ISO=100", "-Make=Synthetic", "-Model=WorkflowCamera", str(path)],
                                 text=True, capture_output=True, check=True)
            frames.append(path)
        out = root / "output"
        config = {"frames": [str(path) for path in frames], "reference": 0,
                  "camera": {"black": 0, "white": 1000000, "linearity_fraction": 0.95,
                             "train": "synthetic"},
                  "geometry": json.loads(geometry.to_json()), "out": str(out), "run_filters": True,
                  "filter_options": {"filters": "all"}}
        config_path = root / "config.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")
        env = dict(os.environ, PYTHONPATH=str(args.repo) + ":" + str(helper.parent), PYTHONDONTWRITEBYTECODE="1")
        command = [args.python, str(helper), "master", str(config_path)]
        completed = subprocess.run(command, text=True, capture_output=True, env=env, timeout=900, check=False)
        report["command"] = command
        report["stdout"] = completed.stdout
        report["stderr"] = completed.stderr
        result = {"ok": False}
        try:
            result = json.loads(completed.stdout[completed.stdout.find("{"):completed.stdout.rfind("}") + 1])
            if not result.get("ok"):
                raise RuntimeError(result.get("message"))
            report["result"] = result
            linear = io.load_array(out / "master/linear.npy")
            valid = np.load(out / "master/valid.npy")
            difference = np.abs(linear - base)
            finite = valid & np.isfinite(difference).all(axis=-1)
            relative = difference / np.maximum(np.abs(base), 1.0)
            report["master"] = {"valid_pixels": int(valid.sum()),
                "median_abs_difference": float(np.median(difference[finite])),
                "median_relative_difference": float(np.median(relative[finite])),
                "p99_abs_difference": float(np.percentile(difference[finite], 99)),
                "max_abs_difference": float(difference[finite].max())}
            measured_frames = json.loads((out / "stack_recipe.json").read_text())["frames"]
            truth_ref_input = [np.linalg.inv(np.vstack([matrix, [0, 0, 1]]))[:2] for matrix in matrices]
            report["translation_errors_px"] = [float(np.linalg.norm(np.asarray(frame["reference_to_input"])[:, 2] - truth[:, 2]))
                                               for frame, truth in zip(measured_frames, truth_ref_input)]
            tiffs = list((out / "filters/tiff").glob("*_layer.tif"))
            alphas = list((out / "filters/tiff").glob("*_alpha.tif"))
            pixelmath = json.loads((out / "filters/pixelmath.json").read_text())
            report["filters"] = {"layer_tiffs": len(tiffs), "alpha_tiffs": len(alphas),
                                 "pixelmath_operations": len(pixelmath["operations"]),
                                 "all_16": len(tiffs) == 16 and len(alphas) == 16}
            report["registration_correlations"] = [item["correlation"] for item in result["registrations"]]

            result_path = root / "pjsr_result.json"
            result_path.write_text(json.dumps(result), encoding="utf-8")
            composite_path = root / "composite.tif"
            pjsr_report_path = root / "pjsr_report.json"
            core = args.repo / "plugins/pixinsight-ael/AELWorkflowCore.jsh"
            script = root / "pixelmath_validation.js"
            script.write_text(
                "/* MIT License — synthetic validation */\n#engine v8\n"
                f"#include {json.dumps(str(core))}\n"
                f"var RESULT = JSON.parse(File.readTextFile({json.dumps(str(result_path))}));\n"
                "var REPORT = {ok:false};\n"
                "try {\n"
                "  aelWorkflowOpenImages(RESULT);\n"
                "  aelWorkflowBuildComposite(RESULT);\n"
                f"  aelBridgeExportFloat32(RESULT.composite,{json.dumps(str(composite_path))});\n"
                "  REPORT.ok=true; REPORT.windows=RESULT.windows.length;\n"
                "  for(let i=0;i<RESULT.windows.length;++i) RESULT.windows[i].forceClose();\n"
                "} catch(error) { REPORT.error=String(error); }\n"
                f"File.writeTextFile({json.dumps(str(pjsr_report_path))},JSON.stringify(REPORT));\n", encoding="utf-8")
            pi = Path("/Applications/PixInsight/PixInsight.app/Contents/MacOS/PixInsight")
            command = [str(pi), "-n", "--automation-mode", f"-r={script}", "--force-exit"]
            completed_pi = subprocess.run(command, text=True, capture_output=True, timeout=300, check=False)
            report["pixinsight_log"] = completed_pi.stdout + completed_pi.stderr
            pjsr = json.loads(pjsr_report_path.read_text()) if pjsr_report_path.exists() else {"ok": False}
            report["pixelmath_pjsr"] = pjsr
            composite = tifffile.imread(composite_path) if composite_path.exists() else None
            expected = tifffile.imread(out / "filters/ael/display.tif").astype(np.float32) / 65535.0
            start = tifffile.imread(out / "filters/tiff/display.tif").astype(np.float32) / 65535.0
            # The composite must be built from the display base. If the start already equals
            # AEL's composite, a PixelMath that does nothing would pass the comparison.
            report["pixelmath_start_vs_expected_max"] = float(np.max(np.abs(start - expected)))
            report["pixelmath_start_differs"] = report["pixelmath_start_vs_expected_max"] > 1e-3
            report["pixelmath_max_abs_difference"] = (float(np.max(np.abs(composite - expected)))
                                                       if composite is not None else None)
            report["pixelmath_equal"] = bool(pjsr.get("ok") and report["pixelmath_start_differs"]
                                             and report["pixelmath_max_abs_difference"] <= 1 / 65535)
            rng = np.random.default_rng(4)
            noise = rng.random(base.shape, dtype=np.float32)
            try:
                lum_base = (base[..., 0] + 2 * base[..., 1] + base[..., 2]) / 4
                lum_noise = (noise[..., 0] + 2 * noise[..., 1] + noise[..., 2]) / 4
                reference_moon = measure_moon(lum_base, geometry.moon_xy, geometry.moon_radius_px)
                register_frame((lum_base, lum_base > 0), (lum_noise, lum_noise > 0), geometry, reference_moon,
                               margin_px=6.0)
                report["negative_registration"] = False
            except Exception:
                report["negative_registration"] = True
            report["filters_ok"] = (len(tiffs) == 16 and len(alphas) == 16
                                    and len(pixelmath["operations"]) == 3 and report["pixelmath_equal"])
            report["master_ok"] = (report["negative_registration"]
                                   and report["master"]["median_relative_difference"] < 0.001
                                   and max(report["translation_errors_px"]) < 0.1
                                   and min(report["registration_correlations"]) > 0.25)
            report["ok"] = report["filters_ok"] and report["master_ok"]
        except Exception as exc:
            report["error"] = f"{type(exc).__name__}: {exc}"
            report["traceback"] = traceback.format_exc()
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "WORKFLOW_VALIDATION.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
        if result.get("ok") and (out / "filters/PIXELMATH.md").exists():
            (args.output / "PIXELMATH.md").write_text((out / "filters/PIXELMATH.md").read_text(), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "output": str(args.output)}))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
