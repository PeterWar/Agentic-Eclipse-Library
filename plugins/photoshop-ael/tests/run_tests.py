#!/usr/bin/env python3
"""Synthetic validation for the Adobe Photoshop AEL bridge.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import traceback

import cv2
import numpy as np
import tifffile

from ael.geometry import EclipseGeometry
from ael.synthetic import SyntheticScene


def detect_python() -> str:
    candidates = [os.environ.get("AEL_PYTHON"), sys.executable,
                  str(Path.home() / ".venvs/eines-ia-py312/bin/python"),
                  "/opt/homebrew/bin/python3.12", "/opt/homebrew/bin/python3"]
    for candidate in candidates:
        if not candidate:
            continue
        run = subprocess.run([candidate, "-c", "import sys, ael; assert sys.version_info >= (3, 10)"],
                             capture_output=True, check=False)
        if run.returncode == 0:
            return candidate
    raise RuntimeError("Select a Python 3.10+ with AEL using --python or AEL_PYTHON")


def photoshop_running() -> bool:
    return subprocess.run(["pgrep", "-f", "Adobe Photoshop 2026.app/Contents/MacOS"],
                          capture_output=True, check=False).returncode == 0


def do_javascript(code: str, timeout: int = 1800) -> subprocess.CompletedProcess:
    script = ('tell application id "com.adobe.Photoshop"\n'
              f'with timeout of {timeout} seconds\n'
              f'do javascript {json.dumps(code, ensure_ascii=False)}\n'
              'end timeout\nend tell')
    return subprocess.run(["osascript", "-e", script], text=True, capture_output=True,
                          timeout=timeout + 30, check=False)


def direct(repo: Path, python: str, operation: str, source: Path, geometry: Path,
           parent: Path, rmax: float = 4.0) -> dict:
    root = parent / f"direct_{operation}"
    root.mkdir()
    cfg = {"operation": operation, "input": str(source), "geometry": str(geometry),
           "out": str(root / operation), "run_root": str(root), "rmax": rmax,
           "source": {"width": 400, "height": 320, "channels": 3}}
    config, result = root / "config.json", root / "result.json"
    config.write_text(json.dumps(cfg), encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=str(repo), PYTHONDONTWRITEBYTECODE="1")
    run = subprocess.run([python, str(repo / "plugins/photoshop-ael/python/ael_photoshop.py"),
                          str(config), str(result)], text=True, capture_output=True, env=env,
                         timeout=900, check=False)
    if run.returncode or not result.exists():
        raise RuntimeError(f"Direct {operation} failed: {run.stdout}\n{run.stderr}")
    answer = json.loads(result.read_text())
    if not answer.get("ok"):
        raise RuntimeError(answer.get("message"))
    return answer


def compare_products(direct_result: dict, bridge_root: Path, operation: str) -> dict:
    comparisons = {}
    for image in direct_result["images"]:
        expected = tifffile.imread(image["path"]) if image["path"].endswith(".tif") else None
        produced_path = bridge_root / operation / Path(image["path"]).name
        if expected is None:
            import imageio.v3 as iio
            expected = iio.imread(image["path"])
            produced = iio.imread(produced_path)
        else:
            produced = tifffile.imread(produced_path)
        difference = float(np.max(np.abs(expected.astype(np.float64) - produced.astype(np.float64))))
        comparisons[Path(image["path"]).name] = {"max_abs_difference": difference,
                                                 "same_shape": expected.shape == produced.shape}
    return comparisons


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--python")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--skip-photoshop", action="store_true")
    args = parser.parse_args()
    # Photoshop resolves relative paths from its own working directory, not from this shell.
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    repo = args.repo.resolve()
    python = args.python or detect_python()
    helper = repo / "plugins/photoshop-ael/python/ael_photoshop.py"
    core = repo / "plugins/photoshop-ael/AELPhotoshopCore.jsx"
    report = {"ok": False, "synthetic": True, "python": python, "repo": str(repo),
              "photoshop_tested": not args.skip_photoshop}
    was_running = photoshop_running()
    report["photoshop_was_running"] = was_running
    try:
        with tempfile.TemporaryDirectory(prefix="ael-photoshop-") as temporary:
            root = Path(temporary) / "prova pont àè"
            root.mkdir()
            shape = (320, 400)
            geometry = EclipseGeometry(shape=shape, sun_xy=(198, 158), sun_radius_px=20,
                                       moon_xy=(198, 158), moon_radius_px=20.6,
                                       north_deg=17, arcsec_per_px=8, note="Synthetic Photoshop validation")
            geometry_path = root / "geometry.json"
            geometry.to_json(geometry_path)
            scene = SyntheticScene(sun_radius_px=20, seed=73, n_rays=120, psf_sigma_px=0.8)
            base = scene.radiance(shape, geometry.sun_xy, geometry.moon_xy).astype(np.float32) / 10
            base = np.stack([base * 1.03, base, base * 0.96], axis=-1).astype(np.float32)
            source = root / "source.tif"
            tifffile.imwrite(source, base, photometric="rgb")
            direct_structure = direct(repo, python, "structure", source, geometry_path, root)
            direct_polar = direct(repo, python, "polar", source, geometry_path, root)
            report["direct"] = {"structure": direct_structure["out"], "polar": direct_polar["out"]}

            matrices = [np.array([[1, 0, 0], [0, 1, 0]], np.float32),
                        np.array([[1, 0, 2.0], [0, 1, -1.5]], np.float32),
                        np.array([[1, 0, -2.5], [0, 1, 2.0]], np.float32)]
            exposures = [0.01, 0.02, 0.04]
            exiftool = shutil.which("exiftool") or "/opt/homebrew/bin/exiftool"
            frames = []
            for index, (matrix, exposure) in enumerate(zip(matrices, exposures)):
                moving = cv2.warpAffine(base, matrix, (shape[1], shape[0]),
                                        flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                                        borderMode=cv2.BORDER_CONSTANT, borderValue=0).astype(np.float32)
                path = root / f"frame_{index}.tif"
                tifffile.imwrite(path, moving * exposure, photometric="rgb")
                subprocess.run([exiftool, "-overwrite_original", f"-ExposureTime={exposure}",
                                "-ISO=100", "-Make=Synthetic", "-Model=WorkflowCamera", str(path)],
                               text=True, capture_output=True, check=True)
                frames.append(path)
            camera = root / "camera.json"
            camera.write_text(json.dumps({"black": 0, "white": 1000000,
                                          "linearity_fraction": 0.95, "train": "synthetic"}), encoding="utf-8")

            if not args.skip_photoshop:
                jsx_report = args.output / "JSX_PROGRESS.json"
                after_structure = root / "after_structure.tif"
                after_polar = root / "after_polar.tif"
                after_untagged = root / "after_untagged.tif"
                jsx = f'''#include {json.dumps(str(core))}
var REPORT = {{ok:false}};
var OWNED = {{}};
function remember(id) {{ OWNED[String(id)] = true; }}
function rememberResults(result) {{
    for (var i=0; i<result.opened_documents.length; i++) remember(result.opened_documents[i].id);
}}
function closeOwned() {{
    for (var i=app.documents.length-1; i>=0; i--) {{
        var doc=app.documents[i];
        if (OWNED[String(doc.id)]) doc.close(SaveOptions.DONOTSAVECHANGES);
    }}
    OWNED={{}};
}}
function imageOperation(operation, afterPath) {{
    REPORT.stage=operation+'_open'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    var oldDialogs=app.displayDialogs; app.displayDialogs=DialogModes.NO;
    var source;
    try {{ source=app.open(new File({json.dumps(str(source))})); }}
    finally {{ app.displayDialogs=oldDialogs; }}
    remember(source.id);
    REPORT.stage=operation+'_run'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    var saved=source.saved;
    var result=AELPhotoshop.run({{operation:operation,outputParent:{json.dumps(str(root))},
        geometry:{json.dumps(str(geometry_path))},python:{json.dumps(python)},aelFolder:{json.dumps(str(repo))},
        rmax:4.0}});
    rememberResults(result);
    AELPhotoshop.exportDocument(source,new File(afterPath));
    var answer={{run_root:result.run_root,opened:result.opened_documents.length,
        receipt:result.bridge_receipt,source_saved_before:saved,source_saved_after:source.saved}};
    closeOwned();
    return answer;
}}
function newOwned(name, fill, bits) {{
    var oldUnits=app.preferences.rulerUnits; app.preferences.rulerUnits=Units.PIXELS;
    try {{ var d=app.documents.add(400,320,72,name,NewDocumentMode.RGB,fill,1,bits); remember(d.id); return d; }}
    finally {{ app.preferences.rulerUnits=oldUnits; }}
}}
function runFolders() {{
    var names=[], files=new Folder({json.dumps(str(root))}).getFiles("AEL_*");
    for (var i=0; i<files.length; i++) if (files[i] instanceof Folder) names.push(files[i].name);
    return names;
}}
function transparentRefusal() {{
    var d=newOwned('AEL test transparent',DocumentFill.TRANSPARENT,BitsPerChannelType.THIRTYTWO);
    d.selection.select([[100,80],[300,80],[300,240],[100,240]]);
    var c=new SolidColor(); c.rgb.red=128; c.rgb.green=128; c.rgb.blue=128;
    d.selection.fill(c); d.selection.deselect();
    var before=runFolders(), answer={{refused:false}}, seen={{}};
    try {{
        var result=AELPhotoshop.run({{operation:'structure',outputParent:{json.dumps(str(root))},
            geometry:{json.dumps(str(geometry_path))},python:{json.dumps(python)},aelFolder:{json.dumps(str(repo))}}});
        rememberResults(result); answer.opened=result.opened_documents.length;
    }} catch(e) {{ answer.refused=true; answer.error=String(e.message); }}
    for (var i=0; i<before.length; i++) seen[before[i]]=true;
    var after=runFolders(); answer.new_run_folders=[];
    for (var j=0; j<after.length; j++) if (!seen[after[j]]) answer.new_run_folders.push(after[j]);
    closeOwned();
    return answer;
}}
function untaggedExport() {{
    var d=newOwned('AEL test untagged',DocumentFill.WHITE,BitsPerChannelType.SIXTEEN);
    d.colorProfileType=ColorProfile.NONE;
    var answer={{}};
    try {{
        var info=AELPhotoshop.exportDocument(d,new File({json.dumps(str(after_untagged))}));
        answer.ok=true; answer.color_profile=info.color_profile; answer.color_profile_type=info.color_profile_type;
    }} catch(e) {{ answer.ok=false; answer.error=String(e.message); }}
    closeOwned();
    return answer;
}}
try {{
    REPORT.stage='bad_path'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    try {{ AELPhotoshop.probe('/path/that/does/not/exist',{json.dumps(str(repo))}); }}
    catch(e) {{ REPORT.bad_path_error=String(e.message); }}
    REPORT.stage='read_json'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    var hostile=new File({json.dumps(str(root / "not_json_result.json"))});
    hostile.encoding='UTF8'; hostile.open('w');
    hostile.write('(function(){{ REPORT.json_code_ran=true; return {{ok:true}}; }})()'); hostile.close();
    try {{ AELPhotoshop.readJSON(hostile); REPORT.json_refused=false; }} catch(e) {{ REPORT.json_refused=true; }}
    REPORT.stage='structure'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    REPORT.structure=imageOperation('structure',{json.dumps(str(after_structure))});
    REPORT.stage='polar'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    REPORT.polar=imageOperation('polar',{json.dumps(str(after_polar))});
    REPORT.stage='master'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    var master=AELPhotoshop.run({{operation:'master',outputParent:{json.dumps(str(root))},
        geometry:{json.dumps(str(geometry_path))},camera:{json.dumps(str(camera))},
        frames:{json.dumps([str(p) for p in frames])},python:{json.dumps(python)},
        aelFolder:{json.dumps(str(repo))},run_filters:true,filter_options:{{filters:'all'}}}});
    rememberResults(master);
    REPORT.master={{run_root:master.run_root,opened:master.opened_documents.length,
        registrations:master.registrations,linear:master.images[0].path,receipt:master.bridge_receipt}};
    closeOwned();
    REPORT.stage='filters'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    var filters=AELPhotoshop.run({{operation:'filters',outputParent:{json.dumps(str(root))},
        input:REPORT.master.linear,python:{json.dumps(python)},aelFolder:{json.dumps(str(repo))},filters:'all'}});
    rememberResults(filters);
    REPORT.filters={{run_root:filters.run_root,opened:filters.opened_documents.length,
        images:filters.images.length,receipt:filters.bridge_receipt}};
    closeOwned();
    REPORT.stage='transparent'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    REPORT.transparent=transparentRefusal();
    REPORT.stage='untagged'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    REPORT.untagged=untaggedExport();
    REPORT.stage='done'; REPORT.ok=true;
}} catch(e) {{ REPORT.error=String(e.message); REPORT.stack=String(e.stack); }}
finally {{ closeOwned(); AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT); }}
'PHOTOSHOP_AEL_TEST_DONE';'''
                completed = do_javascript(jsx, timeout=240)
                report["photoshop_command"] = "osascript: tell com.adobe.Photoshop to do javascript <generated synthetic test>"
                report["photoshop_stdout"] = completed.stdout
                report["photoshop_stderr"] = completed.stderr
                if completed.returncode or not jsx_report.exists():
                    raise RuntimeError(f"Photoshop test failed: {completed.stdout}\n{completed.stderr}")
                jsx_result = json.loads(jsx_report.read_text())
                report["jsx"] = jsx_result
                if not jsx_result.get("ok"):
                    raise RuntimeError(jsx_result.get("error"))

                report["structure_products"] = compare_products(direct_structure,
                    Path(jsx_result["structure"]["run_root"]), "structure")
                report["polar_products"] = compare_products(direct_polar,
                    Path(jsx_result["polar"]["run_root"]), "polar")
                report["source_roundtrip"] = {}
                for name, after in (("structure", after_structure), ("polar", after_polar)):
                    restored = tifffile.imread(after)
                    difference = float(np.max(np.abs(restored - base)))
                    negative = float(np.max(np.abs(np.flipud(restored) - base)))
                    report["source_roundtrip"][name] = {"shape": list(restored.shape),
                        "dtype": str(restored.dtype), "max_abs_difference": difference,
                        "negative_orientation_difference": negative}
                report["source_saved_unchanged"] = all(
                    jsx_result[name]["source_saved_before"] == jsx_result[name]["source_saved_after"]
                    for name in ("structure", "polar"))

                master_out = Path(jsx_result["master"]["run_root"]) / "master"
                linear = np.load(master_out / "master/linear.npy")
                valid = np.load(master_out / "master/valid.npy")
                difference = np.abs(linear - base)
                finite = valid & np.isfinite(difference).all(axis=-1)
                relative = difference / np.maximum(np.abs(base), 1.0)
                measured_frames = json.loads((master_out / "stack_recipe.json").read_text())["frames"]
                truth = [np.linalg.inv(np.vstack([matrix, [0, 0, 1]]))[:2] for matrix in matrices]
                report["translation_errors_px"] = [float(np.linalg.norm(
                    np.asarray(frame["reference_to_input"])[:, 2] - expected[:, 2]))
                    for frame, expected in zip(measured_frames, truth)]
                report["master"] = {"median_relative_difference": float(np.median(relative[finite])),
                    "median_abs_difference": float(np.median(difference[finite])),
                    "p99_abs_difference": float(np.percentile(difference[finite], 99))}
                filters_out = Path(jsx_result["filters"]["run_root"]) / "filters"
                report["filter_counts"] = {"layers": len(list((filters_out / "tiff").glob("*_layer.tif"))),
                    "alphas": len(list((filters_out / "tiff").glob("*_alpha.tif")))}
                transparent = jsx_result["transparent"]
                transparent["ael_outputs"] = [name for name in transparent["new_run_folders"]
                                              if (root / name / "structure").exists()]
                report["transparent"] = transparent
                report["untagged"] = dict(jsx_result["untagged"], exported=after_untagged.exists())

            report["gates"] = {
                "direct_structure": bool(direct_structure.get("ok")),
                "direct_polar": bool(direct_polar.get("ok"))}
            if not args.skip_photoshop:
                report["gates"].update({
                    "bad_path_clear": "bad_path" in report["jsx"].get("bad_path_error", ""),
                    "non_json_not_evaluated": bool(report["jsx"].get("json_refused")) and
                                              not report["jsx"].get("json_code_ran"),
                    # bool(...) first: all() of an empty product list would pass silently.
                    "structure_matches_direct": bool(report["structure_products"]) and all(
                        x["same_shape"] and x["max_abs_difference"] == 0
                        for x in report["structure_products"].values()),
                    "polar_matches_direct": bool(report["polar_products"]) and all(
                        x["same_shape"] and x["max_abs_difference"] == 0
                        for x in report["polar_products"].values()),
                    "transparent_refused": report["transparent"]["refused"] and
                                           "transparent" in report["transparent"].get("error", "") and
                                           len(report["transparent"]["new_run_folders"]) == 1 and
                                           not report["transparent"]["ael_outputs"],
                    "untagged_exported": bool(report["untagged"].get("ok")) and report["untagged"]["exported"],
                    "source_exact": all(x["max_abs_difference"] == 0 and x["negative_orientation_difference"] > 0
                                        for x in report["source_roundtrip"].values()),
                    "source_saved_unchanged": report["source_saved_unchanged"],
                    "master_translation": max(report["translation_errors_px"]) < 0.1,
                    "master_pixels": report["master"]["median_relative_difference"] < 0.001,
                    "sixteen_filters": report["filter_counts"] == {"layers": 16, "alphas": 16},
                    "results_opened": report["jsx"]["structure"]["opened"] == 3 and
                                      report["jsx"]["polar"]["opened"] == 8 and
                                      report["jsx"]["master"]["opened"] == 34 and
                                      report["jsx"]["filters"]["opened"] == 33})
            report["ok"] = all(report["gates"].values())
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
    finally:
        if not was_running and not args.skip_photoshop:
            quit_run = subprocess.run(["osascript", "-e",
                'tell application id "com.adobe.Photoshop" to quit'],
                text=True, capture_output=True, check=False)
            report["photoshop_quit_by_test"] = quit_run.returncode == 0
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "VALIDATION.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "output": str(args.output), "gates": report.get("gates")}, ensure_ascii=False))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
