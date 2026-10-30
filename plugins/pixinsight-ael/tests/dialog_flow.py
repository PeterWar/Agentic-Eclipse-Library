#!/usr/bin/env python3
"""Drive both dialogs inside PixInsight, as a person would, and check what they leave behind.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

validate.py renders the dialogs and calls the Core functions directly; nothing there presses «Run». This test
builds each dialog in a new PixInsight instance (-n --automation-mode, never an existing one), fills its fields,
presses its Run button and checks the result:

* bridge dialog: the active image is taken, the geometry file is only typed (the Run handler must load it), the
  Python field stays empty (detection), `structure` and `polar` open their windows and write their receipts, and the
  pixels equal those of `python -m ael` from the terminal on the same input;
* workflow dialog, «Filter layers from linear.npy»: with «all 16 filters» ticked it makes 16 layers and, unticked,
  only AEL's own default layers (read from ael.filterbank, not written here); the PixelMath composite is built and
  matches AEL's display.tif within the final rounding (half a 16-bit step, gate one step);
* a message box never appears on the way (a box would wait for a click that does not come in automation).
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

from ael import io
from ael.filterbank import DEFAULTS, NAMES
from ael.geometry import EclipseGeometry
from ael.synthetic import SyntheticScene


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
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
function save() { File.writeTextFile( CFG.report, JSON.stringify( REPORT, null, 1 ) ); }
try
{
   let scene = ImageWindow.open( CFG.scene, "synthetic_corona" )[0];
   scene.show();
   scene.bringToFront();
   let start = ids();

   // ---- bridge dialog
   let bridge = new AELBridgeDialog;
   REPORT.steps.bridge_target = bridge.targetView ? bridge.targetView.id : null;
   REPORT.steps.bridge_root = bridge.aelRootEdit.text;
   bridge.outputEdit.text = CFG.bridgeOut;
   bridge.pythonEdit.text = "";
   bridge.geometryFileEdit.text = CFG.geometry;
   bridge.rmaxEdit.text = "3.0";
   bridge.modeList.currentItem = 0;
   bridge.runButton.onClick();
   REPORT.steps.structure_windows = fresh( start );
   closeFresh( start );
   bridge.modeList.currentItem = 1;
   bridge.runButton.onClick();
   REPORT.steps.polar_windows = fresh( start );
   closeFresh( start );
   REPORT.steps.bridge_python_saved = Settings.read( AEL_BRIDGE_SETTINGS_KEY + "pythonPath", DataType.UTF8String );

   // ---- workflow dialog, filter layers from an existing linear stack
   for ( let round = 0; round < 2; ++round )
   {
      let before = ids();
      let workflow = new AELWorkflowDialog;
      workflow.modeList.currentItem = 1;
      workflow.frames = [ CFG.linear ];
      workflow.updateFiles();
      workflow.outputEdit.text = round == 0 ? CFG.workflowDefaults : CFG.workflowAll;
      workflow.pythonEdit.text = "";
      workflow.allFiltersCheck.checked = round == 1;
      workflow.compositeCheck.checked = true;
      REPORT.steps["workflow_root_" + round] = workflow.aelRootEdit.text;
      workflow.runButton.onClick();
      let opened = fresh( before );
      REPORT.steps["workflow_" + round] = { windows: opened,
         layers: opened.filter( function( id ) { return id.indexOf( "AEL_L_" ) == 0; } ).length,
         alphas: opened.filter( function( id ) { return id.indexOf( "AEL_A_" ) == 0; } ).length,
         composite: opened.filter( function( id ) { return id.indexOf( "AEL_COMPOSITE" ) == 0; } ) };
      // export the composite before closing, to compare it with AEL's display.tif
      let compositeId = REPORT.steps["workflow_" + round].composite[0];
      if ( compositeId )
         aelBridgeExportFloat32( View.viewById( compositeId ),
                                 (round == 0 ? CFG.workflowDefaults : CFG.workflowAll) + "/composite_from_pixinsight.tif" );
      closeFresh( before );
   }
   scene.forceClose();
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
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pixinsight", type=Path,
                        default=Path("/Applications/PixInsight/PixInsight.app/Contents/MacOS/PixInsight"))
    parser.add_argument("--keep", type=Path, help="work here and keep every file (default: a temporary folder)")
    args = parser.parse_args()
    plugin = args.repo / "plugins/pixinsight-ael"
    report = {"ok": False, "synthetic": True, "gates": {}, "steps": {}}
    context = tempfile.TemporaryDirectory(prefix="ael-dialogs-") if args.keep is None else None
    base = Path(context.name) if context else args.keep
    base.mkdir(parents=True, exist_ok=True)
    try:
        root = base / "prova diàlegs àè"
        root.mkdir()
        shape = (320, 400)
        geometry = EclipseGeometry(shape=shape, sun_xy=(198.0, 158.0), sun_radius_px=20.0, moon_xy=(198.0, 158.0),
                                   moon_radius_px=20.6, north_deg=17.0, mirrored=False, arcsec_per_px=8.0,
                                   note="Synthetic dialog test")
        scene = SyntheticScene(sun_radius_px=20.0, seed=42, n_rays=100, psf_sigma_px=0.8)
        radiance = scene.radiance(shape, geometry.sun_xy, geometry.moon_xy).astype(np.float32)
        display = radiance / 200000.0
        scene_rgb = np.stack([display * 1.04, display, display * 0.93], axis=-1).astype(np.float32)
        scene_path = root / "synthetic_corona.tif"
        geometry_path = root / "geometry.json"
        tifffile.imwrite(scene_path, scene_rgb, photometric="rgb")
        geometry.to_json(geometry_path)

        # A linear stack in the layout the workflow reads: linear.npy with geometry.json, valid.npy, coverage.npy and
        # alpha.npy beside it. The alpha ramps across the lunar limb, so that part of it is neither 0 nor 1.
        stack = root / "linear stack"
        stack.mkdir()
        linear = np.stack([radiance * 1.03, radiance, radiance * 0.96], axis=-1).astype(np.float32) / 10
        yy, xx = np.mgrid[:shape[0], :shape[1]].astype(np.float32)
        distance = np.hypot(xx - 198.0, yy - 158.0)
        np.save(stack / "linear.npy", linear)
        np.save(stack / "valid.npy", distance > 21.0)
        np.save(stack / "coverage.npy", np.ones(shape, np.float32))
        np.save(stack / "alpha.npy", np.clip((distance - 21.0) / 4.0, 0, 1).astype(np.float32))
        geometry.to_json(stack / "geometry.json")

        config = {"scene": str(scene_path), "geometry": str(geometry_path), "linear": str(stack / "linear.npy"),
                  "bridgeOut": str(root / "bridge out"), "workflowDefaults": str(root / "workflow defaults"),
                  "workflowAll": str(root / "workflow all"), "report": str(root / "pjsr_report.json")}
        config_path = root / "dialog_config.json"
        config_path.write_text(json.dumps(config, indent=1), encoding="utf-8")
        script = root / "dialog_flow.js"
        script.write_text(PJSR % {"core": plugin / "AELBridgeCore.jsh", "dialog": plugin / "AELBridgeDialog.jsh",
                                  "wcore": plugin / "AELWorkflowCore.jsh", "wdialog": plugin / "AELWorkflowDialog.jsh",
                                  "config": json.dumps(str(config_path))}, encoding="utf-8")

        # the terminal runs that the dialogs must equal
        env = dict(os.environ, PYTHONPATH=str(args.repo), PYTHONDONTWRITEBYTECODE="1")
        direct = {}
        for mode in ("structure", "polar"):
            out = root / f"direct_{mode}"
            command = [args.python, "-m", "ael", mode, "--input", str(scene_path), "--geometry", str(geometry_path),
                       "--out", str(out)] + (["--name", "structure"] if mode == "structure" else ["--rmax", "3.0"])
            direct[mode] = json.loads(subprocess.run(command, text=True, capture_output=True, env=env, timeout=600,
                                                     check=True).stdout)
        recipe_out = root / "direct_filters"
        # the same recipe the helper writes for the defaults run is read back from the dialog's own output below

        # PixInsight, a new instance, without AEL_PYTHON so that the interpreter is detected
        pi_env = {key: value for key, value in os.environ.items() if key != "AEL_PYTHON"}
        command = [str(args.pixinsight), "-n", "--automation-mode", f"-r={script}", "--force-exit"]
        # its own process group: if the instance stops on something unforeseen, the whole group is stopped, and
        # only the instance started here (never one that was already open)
        process = subprocess.Popen(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=pi_env,
                                   start_new_session=True)
        try:
            output, _ = process.communicate(timeout=420)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            output, _ = process.communicate()
            output += "\nSTOPPED: the instance did not finish in 420 s"
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
                 "bridge_takes_the_active_image": steps["bridge_target"] == "synthetic_corona",
                 "structure_opens_windows": len(steps["structure_windows"]) > 0,
                 "polar_opens_windows": len(steps["polar_windows"]) > 0,
                 "python_saved_after_detection": bool(steps["bridge_python_saved"])
                                                and Path(steps["bridge_python_saved"]).is_file()}

        # the dialogs' bridge output equals python -m ael
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
                                                      "ael_version": receipt["runtime"]["ael_version"]}
            gates[f"dialog_{mode}_pixels_equal_terminal"] = bool(compared) and all(v["equal"] for v in compared.values())

        # the workflow dialog: defaults and all
        expected_layers = {0: len(DEFAULTS), 1: len(NAMES)}
        for round, key in ((0, "workflowDefaults"), (1, "workflowAll")):
            info = steps[f"workflow_{round}"]
            folder = next(Path(config[key]).glob("ael_filters_*"))
            recipe = json.loads((folder / "filters_recipe.json").read_text())
            pixelmath = json.loads((folder / "pixelmath.json").read_text())
            tiffs = sorted((folder / "tiff").glob("*_layer.tif"))
            gates[f"workflow_{round}_layers"] = info["layers"] == expected_layers[round] == len(tiffs)
            gates[f"workflow_{round}_alphas"] = info["alphas"] == expected_layers[round]
            gates[f"workflow_{round}_one_composite"] = len(info["composite"]) == 1
            if round == 0:
                gates["workflow_defaults_are_AEL_defaults"] = (sorted(p.name.replace("_layer.tif", "") for p in tiffs)
                                                               == sorted(DEFAULTS))
            composite = tifffile.imread(Path(config[key]) / "composite_from_pixinsight.tif")
            reference = tifffile.imread(folder / "ael/display.tif").astype(np.float32) / 65535.0
            difference = float(np.max(np.abs(composite - reference)))
            gates[f"workflow_{round}_composite_within_a_step"] = difference <= 1 / 65535
            # identity with the terminal: AEL's own recipe command on the recipe the dialog wrote
            terminal = root / f"terminal_filters_{round}"
            run = subprocess.run([args.python, "-m", "ael", "filters", "--config", str(folder / "filters_recipe.json"),
                                  "--out", str(terminal)], text=True, capture_output=True, env=env, timeout=900,
                                 check=False)
            names = [n for n in (NAMES if round == 1 else DEFAULTS)]
            identical = {}
            if run.returncode == 0:
                for name in names:
                    for kind in ("layer", "alpha"):
                        a = np.load(terminal / f"{name}_{kind}.npy")
                        b = np.load(folder / "ael" / f"{name}_{kind}.npy")
                        identical[f"{name}_{kind}"] = {"equal": bool(np.array_equal(a, b, equal_nan=True)),
                                                       "sha256_terminal": sha256(terminal / f"{name}_{kind}.npy"),
                                                       "sha256_dialog": sha256(folder / "ael" / f"{name}_{kind}.npy")}
            gates[f"workflow_{round}_layers_equal_terminal"] = run.returncode == 0 and all(v["equal"] for v in identical.values()) and len(identical) == 2 * len(names)
            report["steps"][f"workflow_{round}"] = {"folder": str(folder), "composite_max_difference": difference,
                                                    "composite_max_difference_steps": difference * 65535,
                                                    "operations": [o["filter"] for o in pixelmath["operations"]],
                                                    "recipe_filters": recipe["filters"],
                                                    "terminal_rc": run.returncode, "terminal_stderr": run.stderr[-400:],
                                                    "layers": identical}
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
    print(json.dumps({"ok": report["ok"], "output": str(args.output), "failed": [k for k, v in report.get("gates", {}).items() if not v]}))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
