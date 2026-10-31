#!/usr/bin/env python3
"""Drive the dialog inside PixInsight, as a person would, and check what it leaves behind.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

validate.py renders the dialog and calls the Core functions directly; nothing there presses «Run». This test builds
the dialog in a new PixInsight instance (-n --automation-mode, never an existing one), chooses each operation, fills
its few fields, presses Run and checks the result. The stacked image is made from real RAW photos of a totality, given
here (--raw), with their darks and flats if there are any (--calibration); the other operations use the synthetic
files of demo/ (made by tools/make_demo.py when no folder is given), the same files a person opens. The file and folder
choosers are replaced by stand-ins that record how they were asked (several files at once, which file types) and
answer with the files a person would pick.

* Stacked image from RAW photos (the first operation, chosen when the dialog opens): the photos are added twice and a
  TIFF with them, the darks and flats mixed in the second list; the photos are listed once, the TIFF is not added. The
  linear master and the filter layers equal those of the same engine run from the terminal with the same files
  (ael_bridge_check.py raw: the engine the Photoshop connector shares), the PixelMath composite matches AEL's own
  composite (its preview) within one 8-bit step, a master dark is made for each exposure and a master flat, the
  geometry is measured and shown, and the engine's steps reach the Console. Without photos, Run says what is missing;
  stopped from the Console, the run ends with a message and leaves no folder behind.
* Structure on the open linear corona and unrolled view on the open display one: the dialog has no Python, AEL folder
  or geometry fields, so the Python is detected, AEL is the connector's own, and AEL measures the geometry on each
  image and opens a check window; the pixels equal those of `python -m ael ... --geometry auto` from the terminal, and
  the Moon of the demonstration image is found within 1 px (on the display-stretched image the measured limb lies
  about 1.5 px inside the true one: the centre is gated, the radius reported).
* Filter layers from an open image: once from the linear corona (AEL is handed the image) with AEL's default layers,
  and once from a master frame whose values PixInsight rescaled to 0-1 on opening (AEL reads the file) with all 16;
  the layers equal those of the helper run from the terminal on the same file, the PixelMath composite matches
  AEL's display.tif within one 16-bit step, and the geometry is measured and shown.
* Each operation shows only what it needs; the output folder starts at Downloads (the setting the dialog keeps is
  restored afterwards) and «Browse…» sets it; no message box appears where none is due (a box would wait for a click
  that does not come in automation: the stand-in records it instead).

To test a built package instead of the checkout: --plugin PACKAGE/pixinsight-ael --ael-root PACKAGE/pixinsight-ael/runtime
--demo PACKAGE/../demo --expect-root PACKAGE/pixinsight-ael/runtime, with PYTHONPATH set to that runtime.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
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


def listed(path: Path | None) -> list[str]:
    """One file per line; empty lines and lines starting with # are skipped."""
    if path is None:
        return []
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return [line for line in lines if line and not line.startswith("#")]


PJSR = r'''
#engine v8
#include "%(core)s"
#include "%(wcore)s"
#include "%(dialog)s"
var CFG = JSON.parse( File.readTextFile( %(config)s ) );
var REPORT = { ok: false, messages: [], choosers: [], steps: {} };
function save() { File.writeTextFile( CFG.report, JSON.stringify( REPORT, null, 1 ) ); }
// A message box waits for a click that never comes in automation, and it would stop the whole run. Replacing the
// prototype does not work (execute is a property of each instance), so the class itself is replaced by one that
// records the text and returns: the dialog calls `new MessageBox(...).execute()` by its global name.
MessageBox = function( text, caption, icon, button1, button2, button3 )
{
   this.text = text;
   this.caption = caption;
   this.execute = function() { REPORT.messages.push( String( text ) ); save(); return StdButton.Ok; };
};
// The file and folder choosers: they record how the dialog asked and answer with what a person would pick.
var PICKS = [];
OpenFileDialog = function()
{
   this.caption = ""; this.multipleSelections = false; this.filters = []; this.fileNames = []; this.fileName = "";
   this.execute = function()
   {
      let picked = PICKS.shift() || [];
      REPORT.choosers.push( { caption: this.caption, multiple: this.multipleSelections, filters: this.filters,
                              picked: picked.length } );
      this.fileNames = picked;
      this.fileName = picked.length ? picked[0] : "";
      return picked.length > 0;
   };
};
GetDirectoryDialog = function()
{
   this.caption = ""; this.initialPath = ""; this.directory = "";
   this.execute = function()
   {
      REPORT.choosers.push( { caption: this.caption, folder: true, initialPath: this.initialPath } );
      this.directory = CFG.pickedFolder;
      return true;
   };
};
// What the RAW run answers, which the dialog does not keep: recorded on the way out.
var realRaw = aelWorkflowRaw;
aelWorkflowRaw = function()
{
   let result = realRaw.apply( this, arguments );
   REPORT.steps.raw_result = { out: result.out, receipt: result.receipt, summary: result.summary,
                               left_out: result.left_out, geometry_source: result.geometry_source,
                               preview: result.preview, linear_master: result.linear_master };
   return result;
};
// Aborting from the Console makes the progress watcher leave the cancel file; here it is left at once.
var realProgress = aelWorkflowProgress;
function cancelAtOnce( progressPath, cancelPath )
{
   File.writeTextFile( cancelPath, "stop" );
   return realProgress( progressPath, cancelPath );
}
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
// what each operation shows, once the dialog is on screen (a control of a dialog that is not shown is never visible)
function shown( d )
{
   return { raw: d.rawText.visible, calibration: d.calibrationText.visible, radius: d.rmaxEdit.visible,
            image: d.imageList.visible, filters: d.allFiltersCheck.visible };
}
var OUTPUT_KEY = AEL_BRIDGE_SETTINGS_KEY + "outputDirectory";
var savedOutput = Settings.read( OUTPUT_KEY, DataType.UTF8String );
try
{
   // the first time (no folder kept), the output folder is Downloads; «Browse…» sets another one
   Settings.remove( OUTPUT_KEY );
   let first = new AELBridgeDialog;
   REPORT.steps.output_default = first.outputEdit.text;
   REPORT.steps.operation_default = { index: first.modeList.currentItem,
                                      text: first.modeList.itemText( first.modeList.currentItem ) };
   first.outputButton.onClick();
   REPORT.steps.output_browsed = first.outputEdit.text;
   first.cancel();

   function round( key, imagePath, imageId, mode, setup )
   {
      let window = imagePath ? openActive( imagePath, imageId ) : null;
      let before = ids();                       // after opening the image, so that closeFresh() leaves it open
      let messages = REPORT.messages.length;
      let d = new AELBridgeDialog;
      d.pythonPath = "";
      REPORT.steps[key + "_root"] = d.aelRoot;
      REPORT.steps[key + "_target"] = d.targetView ? d.targetView.id : null;
      d.modeList.currentItem = mode;
      d.updateOperation();
      d.show();
      REPORT.steps[key + "_shown"] = shown( d );
      d.outputEdit.text = CFG.out[key];
      setup( d );
      d.runButton.onClick();
      let opened = fresh( before );
      REPORT.steps[key] = { windows: opened, layers: count( opened, "AEL_L_" ), alphas: count( opened, "AEL_A_" ),
                            composite: opened.filter( function( id ) { return id.indexOf( "AEL_COMPOSITE" ) == 0; } ),
                            messages: REPORT.messages.slice( messages ) };
      let compositeId = REPORT.steps[key].composite[0];
      if ( compositeId )
         aelBridgeExportFloat32( View.viewById( compositeId ), CFG.out[key] + "/composite_from_pixinsight.tif" );
      closeFresh( before );
      if ( d.visible )
         d.cancel();
      if ( window )
         window.forceClose();
      save();
   }
   // RAW photos: none chosen; stopped from the Console; and the whole run, with darks and flats
   round( "raw_empty", null, null, 0, function( d ) {} );
   round( "raw_cancel", null, null, 0, function( d )
   {
      PICKS.push( CFG.raw );
      d.addRawButton.onClick();
      aelWorkflowProgress = cancelAtOnce;
   } );
   aelWorkflowProgress = realProgress;
   round( "raw", null, null, 0, function( d )
   {
      // the photos are added twice, as a person might, the second time with a TIFF among them
      PICKS.push( CFG.raw, CFG.raw.concat( [ CFG.notRaw ] ), CFG.calibration );
      d.addRawButton.onClick();
      d.addRawButton.onClick();
      d.addCalibrationButton.onClick();
      REPORT.steps.raw_lists = { raw: d.raw.slice(), calibration: d.calibration.slice(), raw_text: d.rawText.text };
      console.beginLog();                       // what the Console shows during the run
   } );
   REPORT.steps.raw_console = console.endLog().utf8ToString();
   round( "structure", CFG.structureImage, "corona_linear", 1, function( d ) {} );
   round( "polar", CFG.polarImage, "corona_display", 2, function( d ) { d.rmaxEdit.text = "4.0"; } );
   REPORT.steps.python_saved = Settings.read( AEL_BRIDGE_SETTINGS_KEY + "pythonPath", DataType.UTF8String );
   round( "filters_defaults", CFG.structureImage, "corona_linear", 3,
          function( d ) { d.allFiltersCheck.checked = false; } );
   round( "filters_all", CFG.rescaledImage, "frame_rescaled", 3, function( d ) { d.allFiltersCheck.checked = true; } );
   REPORT.ok = true;
}
catch ( error )
{
   REPORT.error = String( error );
   Console.criticalln( "AEL dialog flow: " + error );
}
finally
{
   aelWorkflowProgress = realProgress;
   // the folder the dialog keeps is the user's: put it back as it was
   if ( savedOutput )
      Settings.write( OUTPUT_KEY, DataType.UTF8String, savedOutput );
   else
      Settings.remove( OUTPUT_KEY );
}
save();
'''


EXPECTED_SHOWN = {  # RAW photos, darks and flats, radius, image, filters
    "raw": dict(raw=True, calibration=True, radius=False, image=False, filters=False),
    "structure": dict(raw=False, calibration=False, radius=False, image=True, filters=False),
    "polar": dict(raw=False, calibration=False, radius=True, image=True, filters=False),
    "filters_defaults": dict(raw=False, calibration=False, radius=False, image=True, filters=True),
    "filters_all": dict(raw=False, calibration=False, radius=False, image=True, filters=True),
}
ROUNDS = ["raw_empty", "raw_cancel"] + list(EXPECTED_SHOWN)
RAW_TYPES = ["*.cr2", "*.cr3", "*.nef", "*.arw", "*.dng", "*.raf", "*.orf", "*.rw2"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, help="checkout: plugin and AEL are taken from it")
    parser.add_argument("--plugin", type=Path, help="folder with AELBridge.js (default: REPO/plugins/pixinsight-ael)")
    parser.add_argument("--ael-root", type=Path, help="folder that holds ael/ (default: REPO)")
    parser.add_argument("--demo", type=Path, help="folder of the synthetic files (default: made by tools/make_demo.py)")
    parser.add_argument("--expect-root", type=Path, help="the AEL folder the dialog must start with")
    parser.add_argument("--raw", type=Path, required=True,
                        help="text file with the RAW photos of one totality, one path per line")
    parser.add_argument("--calibration", type=Path, help="text file with their darks and flats, one path per line")
    parser.add_argument("--python", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pixinsight", type=Path,
                        default=Path("/Applications/PixInsight/PixInsight.app/Contents/MacOS/PixInsight"))
    parser.add_argument("--timeout", type=int, default=3600, help="seconds the PixInsight instance may take")
    parser.add_argument("--keep", type=Path, help="work here and keep every file (default: a temporary folder)")
    args = parser.parse_args()
    plugin = args.plugin or (args.repo / "plugins/pixinsight-ael")
    ael_root = args.ael_root or args.repo
    expect_root = args.expect_root or (None if args.plugin else args.repo)
    raw, calibration = listed(args.raw), listed(args.calibration)
    report = {"ok": False, "plugin": str(plugin), "ael_root": str(ael_root), "raw": raw, "calibration": calibration,
              "gates": {}, "steps": {}}
    context = tempfile.TemporaryDirectory(prefix="ael-dialogs-") if args.keep is None else None
    base = Path(context.name) if context else args.keep
    base.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=str(ael_root), PYTHONDONTWRITEBYTECODE="1")
    try:
        if not raw or not all(Path(p).is_file() for p in raw + calibration):
            raise FileNotFoundError("the RAW photos (and darks and flats) given must exist")
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
        structure_dir, master_dir = demo / "1_structure_polar", demo / "3_master"
        out = {key: str(root / "out" / key) for key in ROUNDS}
        config = {"structureImage": str(structure_dir / "corona_linear.tif"),
                  "polarImage": str(structure_dir / "corona_display.tif"),
                  # values far above 1: PixInsight rescales the view to 0-1, so AEL must read the file itself
                  "rescaledImage": str(master_dir / "frame_1.tif"),
                  "raw": raw, "calibration": calibration, "notRaw": str(structure_dir / "corona_linear.tif"),
                  "pickedFolder": str(root / "picked folder"), "out": out, "report": str(root / "pjsr_report.json")}
        config_path = root / "dialog_config.json"
        config_path.write_text(json.dumps(config, indent=1), encoding="utf-8")
        script = root / "dialog_flow.js"
        script.write_text(PJSR % {"core": plugin / "AELBridgeCore.jsh", "wcore": plugin / "AELWorkflowCore.jsh",
                                  "dialog": plugin / "AELBridgeDialog.jsh", "config": json.dumps(str(config_path))},
                          encoding="utf-8")

        # the terminal runs the dialog must equal
        truth = json.loads((structure_dir / "geometry.json").read_text())
        direct = {}
        for mode, source in (("structure", config["structureImage"]), ("polar", config["polarImage"])):
            target = root / f"direct_{mode}"
            command = [args.python, "-m", "ael", mode, "--input", source, "--geometry", "auto",
                       "--out", str(target)] + (["--name", "structure"] if mode == "structure" else ["--rmax", "4.0"])
            direct[mode] = json.loads(subprocess.run(command, text=True, capture_output=True, env=env, timeout=600,
                                                     check=True).stdout)
        report["inputs"] = {Path(p).name: sha256(Path(p)) for p in
                            [config["structureImage"], config["polarImage"], config["rescaledImage"]] + raw}

        # PixInsight: a new instance, without AEL_PYTHON so that the interpreter is detected; its own process group,
        # so that if it stops on something unforeseen only the instance started here is stopped
        pi_env = {key: value for key, value in os.environ.items() if key != "AEL_PYTHON"}
        command = [str(args.pixinsight), "-n", "--automation-mode", f"-r={script}", "--force-exit"]
        process = subprocess.Popen(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=pi_env,
                                   start_new_session=True)
        try:
            output, _ = process.communicate(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            output, _ = process.communicate()
            output += f"\nSTOPPED: the instance did not finish in {args.timeout} s"
        (root / "pixinsight.log").write_text(output, encoding="utf-8")
        pjsr_path = root / "pjsr_report.json"
        if not pjsr_path.is_file():
            raise RuntimeError("PixInsight did not write its report")
        pjsr = json.loads(pjsr_path.read_text())
        report["pjsr"] = pjsr
        if not pjsr.get("ok"):
            raise RuntimeError("the dialog flow failed in PixInsight: " + str(pjsr.get("error")))
        steps = pjsr["steps"]

        choosers = pjsr["choosers"]
        lists = [c for c in choosers if not c.get("folder")]
        raw_lists = [c for c in lists if c["caption"] in ("RAW photos of the totality (select them all)",
                                                          "Dark and flat frames of the same camera")]
        expected_messages = {"raw_empty": 1, "raw_cancel": 1}
        gates = {"no_other_message_box": all(len(steps[key]["messages"]) == expected_messages.get(key, 0) for key in ROUNDS)
                                         and len(pjsr["messages"]) == sum(expected_messages.values()),
                 "output_folder_starts_at_downloads": steps["output_default"] == str(Path.home() / "Downloads"),
                 "browse_sets_the_output_folder": steps["output_browsed"] == config["pickedFolder"],
                 "raw_photos_is_the_first_operation": steps["operation_default"] == {
                     "index": 0, "text": "Stacked image from RAW photos"},
                 "each_operation_shows_only_what_it_needs": all(steps[f"{key}_shown"] == expected
                                                                for key, expected in EXPECTED_SHOWN.items()),
                 "file_lists_take_several_files": len(raw_lists) == len(lists) == 4 and all(c["multiple"] is True for c in lists),
                 # in both cases: cameras write upper-case names (_MG_9502.CR2)
                 "file_lists_take_raw_photos_only": len(lists) == 4 and all(
                     all(t in c["filters"][0] and t.upper() in c["filters"][0] for t in RAW_TYPES)
                     and not any(".tif" in t.lower() for t in c["filters"][0]) and len(c["filters"]) == 1 for c in lists),
                 "a_photo_added_twice_is_listed_once": steps["raw_lists"]["raw"] == raw,
                 "a_file_that_is_not_raw_is_not_added": config["notRaw"] not in steps["raw_lists"]["raw"],
                 "darks_and_flats_listed": steps["raw_lists"]["calibration"] == calibration,
                 "without_photos_it_says_so": len(steps["raw_empty"]["messages"]) == 1
                                              and "Choose the RAW photos of the totality first." in steps["raw_empty"]["messages"][0]
                                              and steps["raw_empty"]["windows"] == [],
                 "stopped_it_says_so_and_leaves_nothing": len(steps["raw_cancel"]["messages"]) == 1
                                                          and "Stopped from PixInsight" in steps["raw_cancel"]["messages"][0]
                                                          and steps["raw_cancel"]["windows"] == []
                                                          and not any(Path(out["raw_cancel"]).glob("AEL_*")),
                 "takes_the_active_image": steps["structure_target"] == "corona_linear"
                                           and steps["polar_target"] == "corona_display"
                                           and steps["filters_all_target"] == "frame_rescaled",
                 "structure_opens_windows": len(steps["structure"]["windows"]) > 0,
                 "polar_opens_windows": len(steps["polar"]["windows"]) > 0,
                 "python_saved_after_detection": bool(steps["python_saved"]) and Path(steps["python_saved"]).is_file()}
        report["steps"]["shown"] = {key: steps[f"{key}_shown"] for key in EXPECTED_SHOWN}
        report["steps"]["messages"] = {key: steps[key]["messages"] for key in ROUNDS}
        if expect_root is not None:
            for key in EXPECTED_SHOWN:
                gates[f"{key}_starts_with_the_expected_AEL_folder"] = steps[f"{key}_root"] == str(expect_root)

        # the stacked image from RAW photos: equal to the same engine run from the terminal with the same files
        folders = sorted(Path(out["raw"]).glob("AEL_*"))
        gates["raw_one_output_folder"] = len(folders) == 1
        folder = folders[0]
        # named as the Photoshop connector names its runs: AEL_, the local date and time, the milliseconds (a name in
        # universal time would be an hour or more away from the folder's local time, here in Central Europe)
        named = re.fullmatch(r"AEL_(\d{8})_(\d{6})_\d{1,3}", folder.name)
        made = datetime.fromtimestamp(folder.stat().st_mtime)
        gates["raw_folder_named_as_in_photoshop"] = bool(named) and abs(
            (datetime.strptime("".join(named.groups()), "%Y%m%d%H%M%S") - made).total_seconds()) < 1800
        result = steps.get("raw_result") or {}
        terminal = root / "terminal_raw"
        terminal_config = root / "terminal_raw.json"
        terminal_config.write_text(json.dumps({"raw": raw, "calibration": calibration, "out": str(terminal)}),
                                   encoding="utf-8")
        run = subprocess.run([args.python, str(plugin / "python/ael_bridge_check.py"), "raw", str(terminal_config)],
                             text=True, capture_output=True, env=env, timeout=args.timeout, check=False)
        answer = json.loads(run.stdout[run.stdout.find("{"):run.stdout.rfind("}") + 1]) if "{" in run.stdout else {}
        dialog_master, terminal_master = list(folder.glob("* linear master.tif")), list(terminal.glob("* linear master.tif"))
        identical = {}
        if answer.get("ok") and len(dialog_master) == len(terminal_master) == 1:
            pairs = [(dialog_master[0], terminal_master[0])] + [(p, terminal / "layers" / p.name)
                                                                for p in sorted((folder / "layers").glob("*.tif"))]
            for a_path, b_path in pairs:
                same = b_path.is_file() and bool(np.array_equal(pixels(a_path), pixels(b_path), equal_nan=True))
                identical[a_path.name] = {"equal": same, "sha256_dialog": sha256(a_path),
                                          "sha256_terminal": sha256(b_path) if b_path.is_file() else None}
        receipt = json.loads((folder / "AEL receipt.json").read_text()) if (folder / "AEL receipt.json").is_file() else {}
        summary = receipt.get("summary", {})
        windows = steps["raw"]["windows"]
        composite = tifffile.imread(Path(out["raw"]) / "composite_from_pixinsight.tif") if steps["raw"]["composite"] else None
        preview = pixels(Path(result["preview"])).astype(np.float32) / 255.0 if result.get("preview") else None
        difference = (float(np.max(np.abs(composite[..., :3] - preview[..., :3])))
                      if composite is not None and preview is not None and composite.shape[:2] == preview.shape[:2] else None)
        # the Console of the run, without its time stamps
        log = [line.split("] ", 1)[-1] for line in steps.get("raw_console", "").splitlines()]
        gates.update({
            "raw_master_and_layers_equal_terminal": len(identical) == 2 + 2 * len(DEFAULTS) and all(
                v["equal"] for v in identical.values()),
            "raw_opens_master_base_layers_and_composite": "AEL_LINEAR_MASTER" in windows and "AEL_DISPLAY" in windows
                                                           and steps["raw"]["layers"] == len(DEFAULTS)
                                                           and steps["raw"]["alphas"] == len(DEFAULTS)
                                                           and len(steps["raw"]["composite"]) == 1,
            "raw_composite_matches_AEL_composite_within_an_8_bit_step": difference is not None and difference <= 1 / 255,
            "raw_measures_the_geometry": result.get("geometry_source") == "measured on the RAW files",
            "raw_opens_a_geometry_check": any(i.startswith("AEL_geometry_check") for i in windows),
            "raw_stacks_every_photo": summary.get("frames_stacked") == summary.get("frames_chosen") == len(raw),
            "raw_master_dark_for_each_exposure": summary.get("darks") == len(summary.get("exposures") or [None]) > 0
                                                 if calibration else True,
            "raw_master_flat_made": summary.get("flat") is True if calibration else True,
            "raw_steps_reach_the_console": all(any(line.startswith(f"AEL: {stage}") for line in log) for stage in
                                               ("Reading the files", "Finding the Moon", "Registering on the Sun",
                                                "Stacking", "Filters")),
            "raw_console_says_what_was_stacked": any(f"AEL: {len(raw)} of {len(raw)} photos stacked into one image" in line
                                                     for line in log),
        })
        report["steps"]["raw"] = {"folder": str(folder), "terminal_rc": run.returncode, "terminal_ok": answer.get("ok"),
                                  "terminal_message": answer.get("message"), "terminal_stderr": run.stderr[-600:],
                                  "windows": windows, "files": identical, "summary": summary,
                                  "left_out": receipt.get("left_out"), "calibration": receipt.get("calibration"),
                                  "registration_method": (receipt.get("registration") or {}).get("method"),
                                  "composite_max_difference_8bit_steps": None if difference is None else difference * 255,
                                  "timings_s": receipt.get("timings_s"),
                                  "console_lines": [line for line in log if line.startswith(("AEL: ", "Left out: "))][:120]}

        # structure and unrolled view: equal to python -m ael, geometry measured and shown
        for mode in ("structure", "polar"):
            folders = sorted(Path(out[mode]).glob("*"))
            gates[f"{mode}_one_output_folder"] = len(folders) == 1
            folder = folders[0]
            receipt = json.loads((folder / "AEL_BRIDGE_RECEIPT.json").read_text())
            compared = {}
            for key, direct_file in direct[mode]["files"].items():
                if Path(direct_file).suffix.lower() not in (".tif", ".png"):
                    continue
                other = Path(receipt["files"][key])
                a, b = pixels(Path(direct_file)), pixels(other)
                compared[key] = {"equal": bool(np.array_equal(a, b)), "sha256_terminal": sha256(Path(direct_file)),
                                 "sha256_dialog": sha256(other), "shape": list(a.shape)}
            gates[f"{mode}_pixels_equal_terminal"] = bool(compared) and all(v["equal"] for v in compared.values())
            gates[f"{mode}_measures_the_geometry"] = str(receipt.get("geometry_source", "")).startswith("measured")
            gates[f"{mode}_opens_a_geometry_check"] = any(i.startswith("AEL_geometry_check") for i in steps[mode]["windows"])
            circle = (receipt.get("geometry_measurement") or {}).get("disc") or {}
            xy, r = circle.get("xy") or [float("nan")] * 2, circle.get("r", float("nan"))
            gates[f"{mode}_finds_the_moon_centre"] = (abs(xy[0] - truth["moon_xy"][0]) <= 1.0
                                                      and abs(xy[1] - truth["moon_xy"][1]) <= 1.0)
            if mode == "structure":
                gates["structure_finds_the_moon_radius"] = abs(r - truth["moon_radius_px"]) <= 1.0
            report["steps"][mode] = {"folder": str(folder), "files": compared, "measured_circle": {
                "xy": xy, "r": r, "r_minus_truth_px": r - truth["moon_radius_px"]},
                "ael_version": receipt["runtime"]["ael_version"], "python": receipt["runtime"]["python"]}

        # filter layers from an open image: equal to the helper from the terminal on the same file
        helper = plugin / "python/ael_workflow.py"
        sources = {"filters_defaults": (config["structureImage"], "defaults", len(DEFAULTS)),
                   "filters_all": (config["rescaledImage"], "all", len(NAMES))}
        for key, (source, which, expected) in sources.items():
            info = steps[key]
            folders = sorted(Path(out[key]).glob("ael_filters_*"))
            gates[f"{key}_one_output_folder"] = len(folders) == 1
            folder = folders[0]
            workflow_receipt = json.loads((folder / "AEL_WORKFLOW_RECEIPT.json").read_text())
            tiffs = sorted((folder / "tiff").glob("*_layer.tif"))
            gates[f"{key}_layers"] = info["layers"] == expected == len(tiffs)
            gates[f"{key}_alphas"] = info["alphas"] == expected
            gates[f"{key}_one_composite"] = len(info["composite"]) == 1
            if which == "defaults":
                gates["filters_defaults_are_AEL_defaults"] = sorted(p.name.replace("_layer.tif", "") for p in tiffs) == sorted(DEFAULTS)
            gates[f"{key}_measures_the_geometry"] = workflow_receipt.get("geometry_source") == "measured on the image"
            gates[f"{key}_opens_a_geometry_check"] = any(i.startswith("AEL_geometry_check") for i in info["windows"])
            composite = tifffile.imread(Path(out[key]) / "composite_from_pixinsight.tif")
            reference = tifffile.imread(folder / "ael/display.tif").astype(np.float32) / 65535.0
            difference = float(np.max(np.abs(composite - reference)))
            gates[f"{key}_composite_within_a_step"] = difference <= 1 / 65535
            terminal = root / f"terminal_{key}"
            terminal_config = root / f"terminal_{key}.json"
            terminal_config.write_text(json.dumps({"input": source, "geometry": "auto", "filters": which,
                                                   "out": str(terminal)}), encoding="utf-8")
            run = subprocess.run([args.python, str(helper), "filters", str(terminal_config)], text=True,
                                 capture_output=True, env=env, timeout=900, check=False)
            names = list(NAMES if which == "all" else DEFAULTS)
            identical = {}
            if run.returncode == 0:
                for name in names:
                    for kind in ("layer", "alpha"):
                        a = np.load(terminal / "ael" / f"{name}_{kind}.npy")
                        b = np.load(folder / "ael" / f"{name}_{kind}.npy")
                        identical[f"{name}_{kind}"] = {"equal": bool(np.array_equal(a, b, equal_nan=True)),
                                                       "sha256_terminal": sha256(terminal / "ael" / f"{name}_{kind}.npy"),
                                                       "sha256_dialog": sha256(folder / "ael" / f"{name}_{kind}.npy")}
            gates[f"{key}_layers_equal_terminal"] = (run.returncode == 0 and len(identical) == 2 * len(names)
                                                     and all(v["equal"] for v in identical.values()))
            report["steps"][key] = {"folder": str(folder), "source": source, "input_given_to_ael": workflow_receipt["input"],
                                    "composite_max_difference_steps": difference * 65535,
                                    "terminal_rc": run.returncode, "terminal_stderr": run.stderr[-400:],
                                    "geometry_measurement": workflow_receipt.get("geometry_measurement"),
                                    "layers": identical}
        # the rescaled frame is read from its file, the linear corona from the image handed over
        gates["filters_all_reads_the_rescaled_file"] = (Path(report["steps"]["filters_all"]["input_given_to_ael"]).resolve()
                                                        == Path(config["rescaledImage"]).resolve())
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
