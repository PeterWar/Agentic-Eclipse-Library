#!/usr/bin/env python3
"""Drive both dialogs inside PixInsight, as a person would, and check what they leave behind.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

validate.py renders the dialogs and calls the Core functions directly; nothing there presses «Run». This test
builds each dialog in a new PixInsight instance (-n --automation-mode, never an existing one), fills its fields,
presses its Run button and checks the result. The data are the synthetic files of demo/ (made by tools/make_demo.py
when no folder is given), the same files a person opens:

* bridge dialog: the active image is taken, the geometry file is only typed (the Run handler must load it), the
  Python field stays empty (detection) and the AEL folder keeps its starting value; `structure` on the linear
  corona and `polar` on the display one open their windows and write their receipts, and the pixels equal those of
  `python -m ael` from the terminal;
* workflow dialog, «Filter layers from linear.npy»: with «all 16 filters» ticked it makes 16 layers and, unticked,
  only AEL's own default layers (read from ael.filterbank, not written here); the PixelMath composite is built and
  matches AEL's display.tif within the final rounding (one 16-bit step gate); the layers equal those of
  `python -m ael filters` on the recipe the dialog wrote;
* workflow dialog, «Linear master + all filter layers» (experimental): three frames, the master equals the one
  the helper makes from the terminal;
* a message box never appears on the way (a box would wait for a click that does not come in automation).

To test a built package instead of the checkout: --plugin PACKAGE/pixinsight-ael --ael-root PACKAGE/pixinsight-ael/runtime
--demo PACKAGE/../demo --expect-root PACKAGE/pixinsight-ael/runtime, with PYTHONPATH set to that runtime.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import traceback

import numpy as np
import tifffile

from ael.filterbank import DEFAULTS, NAMES


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_sha256(folder: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        digest.update(path.relative_to(folder).as_posix().encode())
        digest.update(sha256(path).encode())
    return digest.hexdigest()


def pixels(path: Path) -> np.ndarray:
    if Path(path).suffix.lower() == ".png":
        from PIL import Image
        return np.asarray(Image.open(path))
    return tifffile.imread(path)


PJSR = r'''
#engine v8
#include "%(core)s"
#include "%(dialog)s"
#include "%(wcore)s"
#include "%(wdialog)s"
var CFG = JSON.parse( File.readTextFile( %(config)s ) );
var REPORT = { ok: false, messages: [], steps: {} };
function save() { File.writeTextFile( CFG.report, JSON.stringify( REPORT, null, 1 ) ); }
// A message box waits for a click that never comes in automation, and it would stop the whole run. Replacing the
// prototype does not work (execute is a property of each instance), so the class itself is replaced by one that
// records the text and returns: the dialogs call `new MessageBox(...).execute()` by its global name.
MessageBox = function( text, caption, icon, button1, button2, button3 )
{
   this.text = text;
   this.caption = caption;
   this.execute = function() { REPORT.messages.push( String( text ) ); save(); return StdButton.Ok; };
};
function ids()
{
   let list = [];
   let windows = ImageWindow.windows;
   for ( let i = 0; i < windows.length; ++i )
      list.push( windows[i].mainView.id );
   return list;
}
function fresh( before )
{
   return ids().filter( function( id ) { return before.indexOf( id ) < 0; } );
}
function closeFresh( before )
{
   let windows = ImageWindow.windows;
   for ( let i = windows.length - 1; i >= 0; --i )
      if ( before.indexOf( windows[i].mainView.id ) < 0 )
         windows[i].forceClose();
}
function openActive( path, id )
{
   let window = ImageWindow.open( path, id )[0];
   window.show();
   window.bringToFront();
   return window;
}
function count( list, prefix )
{
   return list.filter( function( id ) { return id.indexOf( prefix ) == 0; } ).length;
}
try
{
   // ---- bridge dialog: structure on the linear corona, polar on the display one
   let linear = openActive( CFG.structureImage, "corona_linear" );
   let start = ids();                       // after opening the image, so that closeFresh() leaves it open
   let bridge = new AELBridgeDialog;
   REPORT.steps.bridge_target = bridge.targetView ? bridge.targetView.id : null;
   REPORT.steps.bridge_root = bridge.aelRootEdit.text;
   bridge.outputEdit.text = CFG.bridgeOut;
   bridge.pythonEdit.text = "";
   bridge.geometryFileEdit.text = CFG.structureGeometry;
   bridge.modeList.currentItem = 0;
   bridge.runButton.onClick();
   REPORT.steps.structure_windows = fresh( start );
   closeFresh( start );
   linear.forceClose();
   let display = openActive( CFG.polarImage, "corona_display" );
   start = ids();
   let polarDialog = new AELBridgeDialog;
   REPORT.steps.polar_target = polarDialog.targetView ? polarDialog.targetView.id : null;
   polarDialog.outputEdit.text = CFG.bridgeOut;
   polarDialog.pythonEdit.text = "";
   polarDialog.geometryFileEdit.text = CFG.structureGeometry;
   polarDialog.rmaxEdit.text = "4.0";
   polarDialog.modeList.currentItem = 1;
   polarDialog.runButton.onClick();
   REPORT.steps.polar_windows = fresh( start );
   closeFresh( start );
   display.forceClose();
   REPORT.steps.bridge_python_saved = Settings.read( AEL_BRIDGE_SETTINGS_KEY + "pythonPath", DataType.UTF8String );
   save();

   // ---- workflow dialog: filter layers from an existing linear stack, then a linear master (experimental)
   function workflowRound( key, setup )
   {
      let before = ids();
      let workflow = new AELWorkflowDialog;
      workflow.pythonEdit.text = "";
      workflow.compositeCheck.checked = true;
      REPORT.steps[key + "_root"] = workflow.aelRootEdit.text;
      setup( workflow );
      workflow.runButton.onClick();
      let opened = fresh( before );
      REPORT.steps[key] = { windows: opened, layers: count( opened, "AEL_L_" ), alphas: count( opened, "AEL_A_" ),
                            composite: opened.filter( function( id ) { return id.indexOf( "AEL_COMPOSITE" ) == 0; } ) };
      let compositeId = REPORT.steps[key].composite[0];
      if ( compositeId )
         aelBridgeExportFloat32( View.viewById( compositeId ), CFG.out[key] + "/composite_from_pixinsight.tif" );
      closeFresh( before );
      save();
   }
   workflowRound( "filters_defaults", function( d )
   {
      d.modeList.currentItem = 1; d.frames = [ CFG.linearStack ]; d.updateFiles();
      d.outputEdit.text = CFG.out.filters_defaults; d.allFiltersCheck.checked = false;
   } );
   workflowRound( "filters_all", function( d )
   {
      d.modeList.currentItem = 1; d.frames = [ CFG.linearStack ]; d.updateFiles();
      d.outputEdit.text = CFG.out.filters_all; d.allFiltersCheck.checked = true;
   } );
   workflowRound( "master", function( d )
   {
      d.modeList.currentItem = 0; d.frames = CFG.masterFrames; d.updateFiles();
      d.geometryEdit.text = CFG.masterGeometry; d.cameraEdit.text = CFG.masterCamera;
      d.outputEdit.text = CFG.out.master; d.allFiltersCheck.checked = false;
   } );
   REPORT.ok = true;
}
catch ( error )
{
   REPORT.error = String( error );
   Console.criticalln( "AEL dialog flow: " + error );
}
save();
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, help="checkout: plugin and AEL are taken from it")
    parser.add_argument("--plugin", type=Path, help="folder with AELBridge.js (default: REPO/plugins/pixinsight-ael)")
    parser.add_argument("--ael-root", type=Path, help="folder that holds ael/ (default: REPO)")
    parser.add_argument("--demo", type=Path, help="folder of the synthetic files (default: made by tools/make_demo.py)")
    parser.add_argument("--expect-root", type=Path, help="the AEL folder the dialogs must start with")
    parser.add_argument("--python", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pixinsight", type=Path,
                        default=Path("/Applications/PixInsight/PixInsight.app/Contents/MacOS/PixInsight"))
    parser.add_argument("--keep", type=Path, help="work here and keep every file (default: a temporary folder)")
    args = parser.parse_args()
    plugin = args.plugin or (args.repo / "plugins/pixinsight-ael")
    ael_root = args.ael_root or args.repo
    expect_root = args.expect_root or (None if args.plugin else args.repo)
    report = {"ok": False, "synthetic": True, "plugin": str(plugin), "ael_root": str(ael_root), "gates": {}, "steps": {}}
    context = tempfile.TemporaryDirectory(prefix="ael-dialogs-") if args.keep is None else None
    base = Path(context.name) if context else args.keep
    base.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=str(ael_root), PYTHONDONTWRITEBYTECODE="1")
    try:
        root = base / "prova diàlegs àè"
        root.mkdir()
        before_tree = tree_sha256(plugin)
        if args.demo:
            demo = args.demo
        else:
            demo = root / "demo"
            subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / "tools/make_demo.py"), "--out", str(demo)],
                           check=True, env=env, capture_output=True, text=True)
        report["demo"] = str(demo)
        structure_dir, filters_dir, master_dir = demo / "1_structure_polar", demo / "2_filters/linear_master", demo / "3_master"
        out = {key: str(root / key) for key in ("filters_defaults", "filters_all", "master")}
        config = {"structureImage": str(structure_dir / "corona_linear.tif"), "polarImage": str(structure_dir / "corona_display.tif"),
                  "structureGeometry": str(structure_dir / "geometry.json"), "bridgeOut": str(root / "bridge out"),
                  "linearStack": str(filters_dir / "linear.npy"), "masterFrames": [str(master_dir / f"frame_{i}.tif") for i in (1, 2, 3)],
                  "masterGeometry": str(master_dir / "geometry.json"), "masterCamera": str(master_dir / "camera.json"),
                  "out": out, "report": str(root / "pjsr_report.json")}
        config_path = root / "dialog_config.json"
        config_path.write_text(json.dumps(config, indent=1), encoding="utf-8")
        script = root / "dialog_flow.js"
        script.write_text(PJSR % {"core": plugin / "AELBridgeCore.jsh", "dialog": plugin / "AELBridgeDialog.jsh",
                                  "wcore": plugin / "AELWorkflowCore.jsh", "wdialog": plugin / "AELWorkflowDialog.jsh",
                                  "config": json.dumps(str(config_path))}, encoding="utf-8")

        # the terminal runs that the dialogs must equal
        direct = {}
        for mode, source in (("structure", config["structureImage"]), ("polar", config["polarImage"])):
            target = root / f"direct_{mode}"
            command = [args.python, "-m", "ael", mode, "--input", source, "--geometry", config["structureGeometry"],
                       "--out", str(target)] + (["--name", "structure"] if mode == "structure" else ["--rmax", "4.0"])
            direct[mode] = json.loads(subprocess.run(command, text=True, capture_output=True, env=env, timeout=600,
                                                     check=True).stdout)
            direct[mode]["input_sha256"] = sha256(Path(source))
        report["inputs"] = {Path(p).name: sha256(Path(p)) for p in
                            (config["structureImage"], config["polarImage"], config["structureGeometry"], config["linearStack"])}

        # PixInsight: a new instance, without AEL_PYTHON so that the interpreter is detected; its own process group,
        # so that if it stops on something unforeseen only the instance started here is stopped
        pi_env = {key: value for key, value in os.environ.items() if key != "AEL_PYTHON"}
        command = [str(args.pixinsight), "-n", "--automation-mode", f"-r={script}", "--force-exit"]
        process = subprocess.Popen(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=pi_env,
                                   start_new_session=True)
        try:
            output, _ = process.communicate(timeout=600)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            output, _ = process.communicate()
            output += "\nSTOPPED: the instance did not finish in 600 s"
        (root / "pixinsight.log").write_text(output, encoding="utf-8")
        pjsr_path = root / "pjsr_report.json"
        if not pjsr_path.is_file():
            raise RuntimeError("PixInsight did not write its report")
        pjsr = json.loads(pjsr_path.read_text())
        report["pjsr"] = pjsr
        if not pjsr.get("ok"):
            raise RuntimeError("the dialog flow failed in PixInsight: " + str(pjsr.get("error")))
        steps = pjsr["steps"]

        gates = {"no_message_box": pjsr["messages"] == [],
                 "bridge_takes_the_active_image": steps["bridge_target"] == "corona_linear" and steps["polar_target"] == "corona_display",
                 "structure_opens_windows": len(steps["structure_windows"]) > 0,
                 "polar_opens_windows": len(steps["polar_windows"]) > 0,
                 "python_saved_after_detection": bool(steps["bridge_python_saved"]) and Path(steps["bridge_python_saved"]).is_file()}
        if expect_root is not None:
            gates["bridge_starts_with_the_expected_AEL_folder"] = steps["bridge_root"] == str(expect_root)
            for key in ("filters_defaults_root", "filters_all_root", "master_root"):
                gates[f"{key}_is_the_expected_AEL_folder"] = steps[key] == str(expect_root)

        # the bridge dialog's output equals python -m ael
        bridge_runs = sorted((root / "bridge out").glob("*"))
        gates["bridge_two_output_folders"] = len(bridge_runs) == 2
        report["steps"]["bridge_outputs"] = {}
        for folder in bridge_runs:
            mode = "structure" if "structure" in folder.name else "polar"
            receipt = json.loads((folder / "AEL_BRIDGE_RECEIPT.json").read_text())
            compared = {}
            for key, direct_file in direct[mode]["files"].items():
                if Path(direct_file).suffix.lower() not in (".tif", ".png"):
                    continue
                other = Path(receipt["files"][key])
                a, b = pixels(Path(direct_file)), pixels(other)
                compared[key] = {"equal": bool(np.array_equal(a, b)), "sha256_terminal": sha256(Path(direct_file)),
                                 "sha256_dialog": sha256(other), "shape": list(a.shape)}
            report["steps"]["bridge_outputs"][mode] = {"folder": str(folder), "files": compared,
                                                      "input_sha256": direct[mode]["input_sha256"],
                                                      "ael_version": receipt["runtime"]["ael_version"],
                                                      "python": receipt["runtime"]["python"]}
            gates[f"dialog_{mode}_pixels_equal_terminal"] = bool(compared) and all(v["equal"] for v in compared.values())

        # the workflow dialog: defaults and all
        expected_layers = {"filters_defaults": len(DEFAULTS), "filters_all": len(NAMES)}
        for key in ("filters_defaults", "filters_all"):
            info = steps[key]
            folder = next(Path(out[key]).glob("ael_filters_*"))
            recipe = json.loads((folder / "filters_recipe.json").read_text())
            pixelmath = json.loads((folder / "pixelmath.json").read_text())
            tiffs = sorted((folder / "tiff").glob("*_layer.tif"))
            gates[f"{key}_layers"] = info["layers"] == expected_layers[key] == len(tiffs)
            gates[f"{key}_alphas"] = info["alphas"] == expected_layers[key]
            gates[f"{key}_one_composite"] = len(info["composite"]) == 1
            if key == "filters_defaults":
                gates["filters_defaults_are_AEL_defaults"] = sorted(p.name.replace("_layer.tif", "") for p in tiffs) == sorted(DEFAULTS)
            composite = tifffile.imread(Path(out[key]) / "composite_from_pixinsight.tif")
            reference = tifffile.imread(folder / "ael/display.tif").astype(np.float32) / 65535.0
            difference = float(np.max(np.abs(composite - reference)))
            gates[f"{key}_composite_within_a_step"] = difference <= 1 / 65535
            terminal = root / f"terminal_{key}"
            run = subprocess.run([args.python, "-m", "ael", "filters", "--config", str(folder / "filters_recipe.json"),
                                  "--out", str(terminal)], text=True, capture_output=True, env=env, timeout=900, check=False)
            names = list(NAMES if key == "filters_all" else DEFAULTS)
            identical = {}
            if run.returncode == 0:
                for name in names:
                    for kind in ("layer", "alpha"):
                        a = np.load(terminal / f"{name}_{kind}.npy")
                        b = np.load(folder / "ael" / f"{name}_{kind}.npy")
                        identical[f"{name}_{kind}"] = {"equal": bool(np.array_equal(a, b, equal_nan=True)),
                                                       "sha256_terminal": sha256(terminal / f"{name}_{kind}.npy"),
                                                       "sha256_dialog": sha256(folder / "ael" / f"{name}_{kind}.npy")}
            gates[f"{key}_layers_equal_terminal"] = (run.returncode == 0 and len(identical) == 2 * len(names)
                                                    and all(v["equal"] for v in identical.values()))
            report["steps"][key] = {"folder": str(folder), "composite_max_difference_steps": difference * 65535,
                                    "operations": [o["filter"] for o in pixelmath["operations"]],
                                    "recipe_filters": recipe["filters"], "terminal_rc": run.returncode,
                                    "terminal_stderr": run.stderr[-400:], "input_sha256": sha256(Path(config["linearStack"])),
                                    "layers": identical}

        # the linear master (experimental): equal to the helper run from the terminal with the same configuration
        master_folder = next(Path(out["master"]).glob("ael_master_*"))
        master = steps["master"]
        helper = plugin / "python/ael_workflow.py"
        terminal_master = root / "terminal_master"
        terminal_config = {"frames": config["masterFrames"], "reference": 0, "camera": config["masterCamera"],
                           "geometry": config["masterGeometry"], "out": str(terminal_master), "run_filters": True,
                           "filter_options": {"filters": "defaults"}}
        (root / "terminal_master_config.json").write_text(json.dumps(terminal_config), encoding="utf-8")
        run = subprocess.run([args.python, str(helper), "master", str(root / "terminal_master_config.json")], text=True,
                             capture_output=True, env=env, timeout=900, check=False)
        a = np.load(terminal_master / "master/linear.npy") if run.returncode == 0 else None
        b = np.load(master_folder / "master/linear.npy")
        gates["master_made"] = (master_folder / "master/linear.npy").is_file() and master["layers"] == len(DEFAULTS)
        gates["master_equals_terminal"] = a is not None and bool(np.array_equal(a, b, equal_nan=True))
        stack_recipe = json.loads((master_folder / "stack_recipe.json").read_text())
        report["steps"]["master"] = {"folder": str(master_folder), "terminal_rc": run.returncode,
                                     "terminal_stderr": run.stderr[-400:], "windows": master["windows"],
                                     "linear_sha256_dialog": sha256(master_folder / "master/linear.npy"),
                                     "linear_sha256_terminal": sha256(terminal_master / "master/linear.npy") if a is not None else None,
                                     "reference_to_input": [f["reference_to_input"] for f in stack_recipe["frames"]],
                                     "frame_sha256": {Path(p).name: sha256(Path(p)) for p in config["masterFrames"]}}
        gates["package_unchanged_by_the_run"] = tree_sha256(plugin) == before_tree
        report["gates"] = gates
        report["ok"] = all(gates.values())
    except Exception as exc:
        report["ok"] = False
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
    finally:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "DIALOG_FLOW.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
        log = base / "prova diàlegs àè/pixinsight.log"
        if log.is_file():
            (args.output / "dialog_flow_pixinsight.log").write_text(log.read_text(), encoding="utf-8")
        if context:
            context.cleanup()
    print(json.dumps({"ok": report["ok"], "output": str(args.output), "failed": [k for k, v in report.get("gates", {}).items() if not v],
                      "error": report.get("error")}))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
