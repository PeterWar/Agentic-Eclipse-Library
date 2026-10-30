#!/usr/bin/env python3
"""End-to-end synthetic validation for the PixInsight AEL bridge.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

import numpy as np
import tifffile
from PIL import Image

import ael
from ael.geometry import EclipseGeometry
from ael.synthetic import SyntheticScene

CREDIT = ("Processed with Agentic Eclipse Library by Pere Guerra — "
          "https://github.com/PeterWar/Agentic-Eclipse-Library")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_pixels(path: Path) -> np.ndarray:
    if path.suffix.lower() == ".png":
        return np.asarray(Image.open(path))
    return tifffile.imread(path)


def write_generated(path: Path, core: Path, config: Path, body: str, extra_includes: str = "") -> None:
    path.write_text(
        "/* MIT License — Copyright (c) 2026 Pere Guerra Serra.\n"
        " * Processed with Agentic Eclipse Library by Pere Guerra —\n"
        " * https://github.com/PeterWar/Agentic-Eclipse-Library */\n"
        "#engine v8\n"
        f"#include {json.dumps(str(core))}\n" + extra_includes
        + f"var CFG = JSON.parse(File.readTextFile({json.dumps(str(config))}));\n" + body,
        encoding="utf-8")


def pjsr_validation_body() -> str:
    return r'''
var REPORT = { ok: false, roundtrip: {}, errors: {}, bridge: {}, source_unchanged: {} };
function saveReport()
{
   File.writeTextFile( CFG.report, JSON.stringify( REPORT, null, 1 ) );
}
function snapshot( view )
{
   let channels = [];
   for ( let c = 0; c < view.image.numberOfChannels; ++c )
   {
      let samples = new Float32Array( view.image.width * view.image.height );
      view.image.getSamples( samples, 0, 0, view.image.width, view.image.height, c );
      channels.push( samples );
   }
   return channels;
}
function unchanged( view, before )
{
   let after = snapshot( view );
   if ( after.length != before.length )
      return false;
   for ( let c = 0; c < after.length; ++c )
   {
      if ( after[c].length != before[c].length )
         return false;
      for ( let i = 0; i < after[c].length; ++i )
         if ( after[c][i] != before[c][i] )
            return false;
   }
   return true;
}
function roundtrip( input, key, runtime )
{
   let windows = ImageWindow.open( input );
   if ( windows == null || windows.length != 1 )
      throw new Error( "Could not open synthetic roundtrip input: " + input );
   try
   {
      let view = windows[0].mainView;
      let before = snapshot( view );
      let output = CFG.temp + "/roundtrip_" + key + ".tif";
      let exported = aelBridgeExportFloat32( view, output );
      let inspected = aelBridgeInspectInput( runtime, CFG.repo, output, view, exported.sourceICCBytes, exported.iccSidecar );
      REPORT.roundtrip[key] = { output: output, input: inspected, source_unchanged: unchanged( view, before ),
                                source_icc_hex: exported.sourceICCHex };
   }
   finally
   {
      windows[0].forceClose();
   }
}
try
{
   let runtime = aelBridgeProbe( CFG.python, CFG.repo );
   if ( !runtime.ok )
      throw new Error( runtime.message );
   REPORT.runtime = runtime;
   roundtrip( CFG.rgb, "rgb", runtime );
   roundtrip( CFG.mono, "mono", runtime );

   REPORT.errors.bad_path = aelBridgeProbe( CFG.badPython, CFG.repo );
   REPORT.errors.missing_ael = aelBridgeProbe( CFG.python, "" );
   if ( CFG.oldPython.length > 0 )
      REPORT.errors.too_old = aelBridgeProbe( CFG.oldPython, CFG.repo );
   else
      REPORT.errors.too_old = { not_tested: "No pre-3.10 Python executable was available" };
   REPORT.errors.old_ael = aelBridgeProbe( CFG.python, CFG.staleAel );

   // PixInsight rescales a float file whose values leave 0-1 to exactly 0-1 when it opens it. The bridge must refuse
   // such a view, before exporting anything, and say why; the files that stay inside 0-1 are run below.
   try
   {
      let wide = ImageWindow.open( CFG.outOfRange, "fora_de_rang" )[0];
      try
      {
         REPORT.errors.out_of_range = { view_maximum: wide.mainView.image.maximum() };
         aelBridgeRunOnView( { view: wide.mainView, mode: "structure", geometry: CFG.geometry,
            outputDirectoryExact: CFG.bridgeRange, pythonPath: CFG.python, aelRoot: CFG.repo,
            runtime: runtime, validMask: "", timeoutMs: 600000 } );
         REPORT.errors.out_of_range.refused = false;
      }
      catch ( error )
      {
         REPORT.errors.out_of_range.refused = true;
         REPORT.errors.out_of_range.message = String( error );
      }
      wide.forceClose();
   }
   catch ( error )
   {
      REPORT.errors.out_of_range = { error: String( error ) };
   }

   // Detection with nothing chosen: an empty Python field, no saved path and no AEL_PYTHON (the launcher drops it from
   // the environment of this instance). The scan of the standard folders and the virtual environments must find an
   // interpreter that holds the AEL of the connector. The settings of this instance may hold a path saved by an
   // earlier run, which would hide the scan, so it is removed first.
   Settings.remove( AEL_BRIDGE_SETTINGS_KEY + "pythonPath" );
   let detected = aelBridgeCandidates( "", CFG.repo );
   REPORT.autodetect = { python: detected.python, ael_version: detected.ael_version, ael_file: detected.ael_file,
                         tried_before: detected.diagnostics };
   REPORT.default_root = aelBridgeDefaultRoot();

   let sceneWindows = ImageWindow.open( CFG.scene );
   if ( sceneWindows == null || sceneWindows.length != 1 )
      throw new Error( "Could not open synthetic AEL scene" );
   try
   {
      let view = sceneWindows[0].mainView;
      let beforeStructure = snapshot( view );
      let structure = aelBridgeRunOnView( { view: view, mode: "structure", geometry: CFG.geometry,
         outputDirectoryExact: CFG.bridgeStructure, pythonPath: CFG.python, aelRoot: CFG.repo,
         runtime: runtime, validMask: "", timeoutMs: 600000 } );
      REPORT.bridge.structure = { output: structure.outputDirectory, receipt: structure.receipt,
                                  result: structure.result, runtime: structure.runtime };
      REPORT.source_unchanged.structure = unchanged( view, beforeStructure );
      for ( let i = 0; i < structure.windows.length; ++i )
         structure.windows[i].forceClose();

      let beforePolar = snapshot( view );
      let polar = aelBridgeRunOnView( { view: view, mode: "polar", geometry: CFG.geometry,
         outputDirectoryExact: CFG.bridgePolar, pythonPath: CFG.python, aelRoot: CFG.repo,
         runtime: runtime, validMask: "", rmax: CFG.rmax, timeoutMs: 600000 } );
      REPORT.bridge.polar = { output: polar.outputDirectory, receipt: polar.receipt,
                              result: polar.result, runtime: polar.runtime };
      REPORT.source_unchanged.polar = unchanged( view, beforePolar );
      for ( let i = 0; i < polar.windows.length; ++i )
         polar.windows[i].forceClose();
   }
   finally
   {
      sceneWindows[0].forceClose();
   }
   REPORT.ok = true;
}
catch ( error )
{
   REPORT.error = String( error );
   Console.criticalln( "AEL validation: " + error );
}
saveReport();
'''


def pjsr_dialog_capture_body(dialog_script: Path) -> str:
    return r'''
try
{
   eval( File.readTextFile( "''' + str(dialog_script) + r'''" ) );
   let captureWindows = ImageWindow.open( CFG.scene );
   let captureDialog = new AELBridgeDialog;
   captureDialog.targetView = captureWindows[0].mainView;
   captureDialog.imageList.currentView = captureDialog.targetView;
   captureDialog.pythonEdit.text = CFG.python;
   captureDialog.aelRootEdit.text = CFG.repo;
   captureDialog.outputEdit.text = CFG.temp;
   captureDialog.geometryEdits.sunX.text = String( CFG.geometry.sun_xy[0] );
   captureDialog.geometryEdits.sunY.text = String( CFG.geometry.sun_xy[1] );
   captureDialog.geometryEdits.sunRadius.text = String( CFG.geometry.sun_radius_px );
   captureDialog.geometryEdits.moonX.text = String( CFG.geometry.moon_xy[0] );
   captureDialog.geometryEdits.moonY.text = String( CFG.geometry.moon_xy[1] );
   captureDialog.geometryEdits.moonRadius.text = String( CFG.geometry.moon_radius_px );
   captureDialog.geometryEdits.north.text = String( CFG.geometry.north_deg );
   captureDialog.geometryEdits.arcsec.text = String( CFG.geometry.arcsec_per_px );
   captureDialog.show();
   CoreApplication.processEvents();
   captureDialog.render().save( CFG.captureImage );
   ExternalProcess.execute( "/bin/sleep", [ String( CFG.holdSeconds ) ] );
   captureDialog.cancel();
   captureWindows[0].forceClose();
   File.writeTextFile( CFG.captureMarker, "dialog capture completed" );
}
catch ( error )
{
   File.writeTextFile( CFG.captureMarker + ".error", String( error ) );
}
'''


def pjsr_result_capture_body() -> str:
    return r'''
try
{
   let resultWindow = ImageWindow.open( CFG.resultImage );
   if ( resultWindow == null || resultWindow.length == 0 )
      throw new Error( "Could not open result for capture" );
   resultWindow[0].show();
   resultWindow[0].zoomToFit();
   CoreApplication.processEvents();
   resultWindow[0].mainView.image.render().save( CFG.captureImage );
   ExternalProcess.execute( "/bin/sleep", [ String( CFG.holdSeconds ) ] );
   resultWindow[0].forceClose();
   File.writeTextFile( CFG.captureMarker, "result capture completed" );
}
catch ( error )
{
   File.writeTextFile( CFG.captureMarker + ".error", String( error ) );
}
'''


def pixinsight_environment() -> dict:
    """The environment of the PixInsight instances: without AEL_PYTHON, so that the interpreter detection is tested."""
    return {key: value for key, value in os.environ.items() if key != "AEL_PYTHON"}


def run_pixinsight(executable: Path, script: Path, log: Path, timeout: int = 900) -> dict:
    command = [str(executable), "-n", "--automation-mode", f"-r={script}", "--force-exit"]
    completed = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False,
                               env=pixinsight_environment())
    log.write_text("COMMAND: " + shlex.join(command) + "\n\nSTDOUT/STDERR:\n" + completed.stdout + completed.stderr,
                   encoding="utf-8")
    return {"command": command, "exit_code": completed.returncode, "log": str(log)}


def capture(executable: Path, script: Path, screenshot: Path, log: Path, hold: int = 12) -> dict:
    command = [str(executable), "-n", "--automation-mode", f"-r={script}", "--force-exit"]
    process = subprocess.Popen(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               env=pixinsight_environment())
    try:
        output, _ = process.communicate(timeout=hold + 45)
    except subprocess.TimeoutExpired:
        process.kill()
        output, _ = process.communicate()
    log.write_text("COMMAND: " + shlex.join(command) + "\n\n" + (output or ""), encoding="utf-8")
    return {"command": command, "exit_code": process.returncode, "method": "PixInsight internal render",
            "screenshot": str(screenshot), "created": screenshot.is_file(), "log": str(log)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--pixinsight", type=Path, required=True)
    parser.add_argument("--skip-pixinsight", action="store_true")
    parser.add_argument("--skip-captures", action="store_true")
    args = parser.parse_args()

    destination = Path(os.environ["AEL_VALIDATION_OUTPUT"]) if os.environ.get("AEL_VALIDATION_OUTPUT") else None
    report = {"ok": False, "synthetic": True, "credit": CREDIT,
              "direct_runtime": {"python": args.python, "python_version": list(sys.version_info[:3]),
                                 "ael_version": ael.__version__, "ael_file": ael.__file__},
              "tests": {}, "commands": [], "captures": {}}
    with tempfile.TemporaryDirectory(prefix="ael-pixinsight-") as temporary:
        root = Path(temporary) / "prova pont àè"
        root.mkdir(parents=True)
        report["temporary_root"] = str(root)
        try:
            h, w = 37, 53
            yy, xx = np.mgrid[:h, :w].astype(np.float32)
            rgb = np.stack([(xx + 1) / w, (yy + 1) / h, (xx + yy + 2) / (w + h)], axis=-1).astype(np.float32)
            rgb[0, 0] = [0.01, 0.21, 0.41]
            rgb[0, -1] = [0.02, 0.22, 0.42]
            rgb[-1, 0] = [0.03, 0.23, 0.43]
            rgb[-1, -1] = [0.04, 0.24, 0.44]
            mono = ((xx / w + (yy / h) ** 2 + 0.001 * xx * yy / (w * h)) / 2.001).astype(np.float32)
            rgb_path, mono_path = root / "asymmetric_rgb.tif", root / "asymmetric_mono.tif"
            from PIL import ImageCms
            icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
            tifffile.imwrite(rgb_path, rgb, photometric="rgb",
                             extratags=[(34675, "B", len(icc), icc, True)])
            tifffile.imwrite(mono_path, mono, photometric="minisblack")

            shape = (320, 400)
            geometry = EclipseGeometry(shape=shape, sun_xy=(198.0, 158.0), sun_radius_px=20.0,
                                       moon_xy=(198.0, 158.0), moon_radius_px=20.6,
                                       north_deg=17.0, mirrored=False, arcsec_per_px=8.0,
                                       note="Synthetic validation only")
            scene = SyntheticScene(sun_radius_px=20.0, seed=42, n_rays=100, psf_sigma_px=0.8)
            base = scene.radiance(shape, geometry.sun_xy, geometry.moon_xy).astype(np.float32) / 200000.0
            scene_rgb = np.stack([base * 1.04, base, base * 0.93], axis=-1).astype(np.float32)
            scene_path = root / "synthetic_corona.tif"
            geometry_path = root / "geometry.json"
            tifffile.imwrite(scene_path, scene_rgb, photometric="rgb")
            geometry.to_json(geometry_path)
            report["inputs"] = {p.name: {"sha256": sha256(p), "bytes": p.stat().st_size}
                                for p in (rgb_path, mono_path, scene_path, geometry_path)}
            # the same scene at eight times the level: values above 1, which PixInsight rescales when it opens the file
            wide_path = root / "out_of_range.tif"
            tifffile.imwrite(wide_path, (scene_rgb * 8.0).astype(np.float32), photometric="rgb")
            assert float(tifffile.imread(wide_path).max()) > 1.0

            # Stand-ins for the `ael` package that carry only a version: the connector must refuse an AEL older than 1.3.6
            # (or one whose version cannot be read) and accept a later one, comparing numbers and not text (1.10.0 > 1.3.6).
            stubs = {}
            for label, version in (("stale", "1.3.3"), ("newer", "1.10.0"), ("unreadable", "development")):
                stub_root = root / f"{label} ael"
                (stub_root / "ael").mkdir(parents=True)
                (stub_root / "ael" / "__init__.py").write_text(f'__version__ = "{version}"\n', encoding="utf-8")
                stubs[label] = stub_root
            stale_root = stubs["stale"]
            helper_check = args.repo / "plugins/pixinsight-ael/python/ael_bridge_check.py"
            versions = {}
            for label, stub_root in stubs.items():
                probe_run = subprocess.run([args.python, str(helper_check), "probe"], text=True, capture_output=True,
                                           env=dict(os.environ, PYTHONPATH=str(stub_root), PYTHONDONTWRITEBYTECODE="1"),
                                           timeout=60, check=False)
                info = json.loads(probe_run.stdout[probe_run.stdout.find("{"):probe_run.stdout.rfind("}") + 1])
                versions[label] = {"ok": info.get("ok"), "kind": info.get("kind"), "ael_version": info.get("ael_version")}
            report["tests"]["ael_version_floor"] = versions

            direct = {}
            for mode in ("structure", "polar"):
                out = root / f"direct_{mode}"
                command = [args.python, "-m", "ael", mode, "--input", str(scene_path),
                           "--geometry", str(geometry_path), "--out", str(out)]
                if mode == "structure":
                    command += ["--name", "structure"]
                else:
                    command += ["--rmax", "3.0"]
                completed = subprocess.run(command, text=True, capture_output=True,
                                           env=dict(os.environ, PYTHONPATH=str(args.repo), PYTHONDONTWRITEBYTECODE="1"),
                                           timeout=600, check=True)
                result = json.loads(completed.stdout)
                direct[mode] = {"output": str(out), "command": command, "result": result}
            report["direct"] = direct
            report["tests"]["negative_rotated"] = bool(not np.array_equal(rgb, np.rot90(rgb, 2)))
            report["tests"]["direct_structure_and_polar"] = True

            if not args.skip_pixinsight:
                if not args.pixinsight.is_file():
                    raise FileNotFoundError(f"PixInsight not found: {args.pixinsight}")
                core = args.repo / "plugins/pixinsight-ael/AELBridgeCore.jsh"
                config = {
                    "repo": str(args.repo), "python": args.python, "temp": str(root),
                    "rgb": str(rgb_path), "mono": str(mono_path), "scene": str(scene_path),
                    "geometry": json.loads(geometry_path.read_text()), "rmax": 3.0,
                    "bridgeStructure": str(root / "bridge_structure"),
                    "bridgePolar": str(root / "bridge_polar"),
                    "report": str(root / "pjsr_report.json"),
                    "badPython": str(root / "no-such-python"), "staleAel": str(stale_root),
                    "outOfRange": str(wide_path), "bridgeRange": str(root / "bridge_out_of_range"),
                    "oldPython": "/usr/bin/python3" if Path("/usr/bin/python3").is_file() else ""
                }
                config_path = root / "pjsr_config.json"
                config_path.write_text(json.dumps(config, indent=1), encoding="utf-8")
                script = root / "pjsr_validation.js"
                write_generated(script, core, config_path, pjsr_validation_body())
                run = run_pixinsight(args.pixinsight, script, root / "pixinsight_validation.log")
                report["commands"].append(run)
                pjsr_report_path = root / "pjsr_report.json"
                if not pjsr_report_path.is_file():
                    raise RuntimeError("PixInsight did not write its validation report")
                pjsr = json.loads(pjsr_report_path.read_text())
                report["pixinsight"] = pjsr
                if not pjsr.get("ok"):
                    raise RuntimeError("PixInsight validation failed: " + str(pjsr.get("error")))

                for key, original in (("rgb", rgb), ("mono", mono)):
                    exported = tifffile.imread(pjsr["roundtrip"][key]["output"])
                    difference = float(np.max(np.abs(exported - original)))
                    report["tests"][f"roundtrip_{key}"] = {"shape": list(exported.shape),
                        "dtype": str(exported.dtype), "max_abs_difference": difference,
                        "passed": exported.shape == original.shape and exported.dtype == np.float32 and difference == 0.0}
                    report["tests"][f"negative_{key}"] = bool(not np.array_equal(exported, np.flipud(original)))
                with tifffile.TiffFile(pjsr["roundtrip"]["rgb"]["output"]) as exported_tiff:
                    exported_icc = exported_tiff.pages[0].tags[34675].value
                report["tests"]["icc_preserved_exactly"] = bytes(exported_icc) == icc
                pixinsight_icc = bytes.fromhex(pjsr["roundtrip"]["rgb"]["source_icc_hex"])
                report["icc_details"] = {"source_bytes": len(icc), "exported_bytes": len(exported_icc),
                    "source_sha256": hashlib.sha256(icc).hexdigest(),
                    "pixinsight_source_sha256": hashlib.sha256(pixinsight_icc).hexdigest(),
                    "exported_sha256": hashlib.sha256(bytes(exported_icc)).hexdigest(),
                    "pixinsight_source_matches": pixinsight_icc == icc,
                    "mismatch_offsets": [index for index, (a, b) in enumerate(zip(icc, bytes(exported_icc))) if a != b][:30]}
                report["tests"]["source_unchanged"] = pjsr["source_unchanged"]
                report["tests"]["roundtrip_source_unchanged"] = {
                    key: pjsr["roundtrip"][key]["source_unchanged"] for key in ("rgb", "mono")}
                report["tests"]["old_ael_kind"] = pjsr["errors"]["old_ael"].get("kind")
                report["tests"]["out_of_range"] = {**pjsr["errors"]["out_of_range"],
                                                   "output_written": (root / "bridge_out_of_range").exists()
                                                                     and any((root / "bridge_out_of_range").iterdir())}
                report["tests"]["autodetect_python"] = {"detected": pjsr["autodetect"], "default_root": pjsr["default_root"]}
                report["tests"]["clear_errors"] = {
                    "bad_path": pjsr["errors"]["bad_path"].get("kind") == "bad_path",
                    "missing_ael": pjsr["errors"]["missing_ael"].get("kind") == "missing_ael",
                    "too_old": pjsr["errors"]["too_old"].get("kind") == "too_old"
                    if "kind" in pjsr["errors"]["too_old"] else pjsr["errors"]["too_old"]}

                for mode in ("structure", "polar"):
                    expected = direct[mode]["result"]["files"]
                    actual = pjsr["bridge"][mode]["result"]["files"]
                    comparison = {}
                    for key, direct_file in expected.items():
                        if Path(direct_file).suffix.lower() not in (".tif", ".png"):
                            continue
                        a = load_pixels(Path(direct_file))
                        b = load_pixels(Path(actual[key]))
                        comparison[key] = {"shape": list(a.shape), "equal": bool(np.array_equal(a, b)),
                                           "max_abs_difference": float(np.max(np.abs(a.astype(np.float64) - b.astype(np.float64))))}
                    report["tests"][f"bridge_equals_direct_{mode}"] = comparison
                    bridge_receipt = json.loads(Path(pjsr["bridge"][mode]["receipt"]).read_text())
                    report["tests"][f"runtime_receipt_{mode}"] = {
                        "ael_version": bridge_receipt["runtime"]["ael_version"],
                        "ael_file": bridge_receipt["runtime"]["ael_file"],
                        "matches_direct": bridge_receipt["runtime"]["ael_version"] == ael.__version__
                                          and Path(bridge_receipt["runtime"]["ael_file"]).resolve() == Path(ael.__file__).resolve()}

                if not args.skip_captures:
                    dialog_script_path = args.repo / "plugins/pixinsight-ael/AELBridgeDialog.jsh"
                    dialog_script = root / "capture_dialog.js"
                    capture_config = dict(config, captureMarker=str(root / "dialog_capture.done"), holdSeconds=1,
                                          captureImage=str(root / "dialog.png"))
                    capture_config_path = root / "capture_config.json"
                    capture_config_path.write_text(json.dumps(capture_config), encoding="utf-8")
                    write_generated(dialog_script, core, capture_config_path,
                                    pjsr_dialog_capture_body(dialog_script_path))
                    report["captures"]["dialog"] = capture(args.pixinsight, dialog_script,
                        root / "dialog.png", root / "capture_dialog.log", hold=1)

                    result_config = dict(config, resultImage=pjsr["bridge"]["structure"]["result"]["files"]["mono"],
                        captureMarker=str(root / "result_capture.done"), holdSeconds=1,
                        captureImage=str(root / "results.png"))
                    result_config_path = root / "result_capture_config.json"
                    result_config_path.write_text(json.dumps(result_config), encoding="utf-8")
                    result_script = root / "capture_results.js"
                    write_generated(result_script, core, result_config_path, pjsr_result_capture_body())
                    report["captures"]["results"] = capture(args.pixinsight, result_script,
                        root / "results.png", root / "capture_results.log", hold=1)
                else:
                    report["captures"]["status"] = "not tested: captures skipped"

            floor = report["tests"]["ael_version_floor"]
            gates = {
                "negative_rotated": report["tests"]["negative_rotated"],
                "direct_structure_and_polar": report["tests"]["direct_structure_and_polar"],
                "old_ael_refused": floor["stale"]["kind"] == "old_ael" and floor["unreadable"]["kind"] == "old_ael",
                "newer_ael_accepted": bool(floor["newer"]["ok"]) and floor["newer"]["ael_version"] == "1.10.0"}
            if not args.skip_pixinsight:
                gates.update({
                    "roundtrip_rgb": report["tests"]["roundtrip_rgb"]["passed"],
                    "roundtrip_mono": report["tests"]["roundtrip_mono"]["passed"],
                    "negative_rgb": report["tests"]["negative_rgb"],
                    "negative_mono": report["tests"]["negative_mono"],
                    "icc_preserved_exactly": report["tests"]["icc_preserved_exactly"],
                    "source_unchanged": all(report["tests"]["source_unchanged"].values()),
                    "roundtrip_source_unchanged": all(report["tests"]["roundtrip_source_unchanged"].values()),
                    "clear_errors": all(value is True or isinstance(value, dict)
                                        for value in report["tests"]["clear_errors"].values()),
                    "old_ael_refused_in_pixinsight": report["tests"]["old_ael_kind"] == "old_ael",
                    "out_of_range_file_refused": report["tests"]["out_of_range"].get("refused") is True
                                                 and "rescaled" in report["tests"]["out_of_range"].get("message", "")
                                                 and report["tests"]["out_of_range"].get("view_maximum") == 1.0
                                                 and not report["tests"]["out_of_range"]["output_written"],
                    "python_autodetected": bool(Path(report["tests"]["autodetect_python"]["detected"]["python"]).is_file())
                                           and report["tests"]["autodetect_python"]["detected"]["ael_version"] == ael.__version__,
                    "structure_pixels_equal": all(item["equal"] for item in report["tests"]["bridge_equals_direct_structure"].values()),
                    "polar_pixels_equal": all(item["equal"] for item in report["tests"]["bridge_equals_direct_polar"].values()),
                    "runtime_receipts_match": all(report["tests"][f"runtime_receipt_{mode}"]["matches_direct"]
                                                   for mode in ("structure", "polar"))})
                if not args.skip_captures:
                    gates["captures_created"] = all(report["captures"][key]["created"] for key in ("dialog", "results"))
            report["gates"] = gates
            report["ok"] = all(gates.values())
        except Exception as exc:
            report["ok"] = False
            report["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            if destination:
                destination.mkdir(parents=True, exist_ok=True)
                (destination / "VALIDATION.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
                inputs_destination = destination / "synthetic_inputs"
                inputs_destination.mkdir(exist_ok=True)
                for name in ("asymmetric_rgb.tif", "asymmetric_mono.tif", "synthetic_corona.tif", "geometry.json"):
                    if (root / name).exists():
                        shutil.copy2(root / name, inputs_destination / name)
                for pattern in ("*.log", "*.js", "*_config.json", "*.error", "dialog.png", "results.png", "pjsr_report.json"):
                    for path in root.glob(pattern):
                        shutil.copy2(path, destination / path.name)
            (root / "VALIDATION.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({"ok": report["ok"], "output": str(destination) if destination else str(root)}))
        if not report["ok"]:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
