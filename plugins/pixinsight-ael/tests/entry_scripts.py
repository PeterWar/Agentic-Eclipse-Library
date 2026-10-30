#!/usr/bin/env python3
"""Start each menu script from its own entry file, as PixInsight does, and check that its dialog appears.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

dialog_flow.py includes the dialog files itself; nothing there runs AELBridge.js or AELWorkflow.js, the two files that
Script > Utilities starts. Here each entry file runs unchanged in a new PixInsight instance (-n --automation-mode, never
an existing one): it includes its own files, builds its dialog and calls execute(), which waits for a click. The native
Dialog class is replaced, before the entry file is read, by a subclass that records every dialog built; a timer that
fires inside the dialog's own event loop checks its title, that it is visible, its Run button, its fields and the AEL
folder it starts with, and closes it with Cancel. A message box never appears (it would wait for a click that does not
come). The control: the same check on a copy of the plugin whose bridge entry has lost the include of its dialog must
fail, so that a broken entry file cannot pass.

To test a built package: --plugin PACKAGE/pixinsight-ael --expect-root PACKAGE/pixinsight-ael/runtime.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile

ENTRIES = {
    "bridge": {"file": "AELBridge.js", "title": "Agentic Eclipse Library", "run": "Run AEL",
               "controls": ["imageList", "modeList", "outputEdit", "rmaxEdit"]},
    "workflow": {"file": "AELWorkflow.js", "title": "AEL Linear Master and Filter Layers", "run": "Run workflow",
                 "controls": ["modeList", "outputEdit", "allFiltersCheck", "darkEdit", "flatEdit"]},
}
# What a person who does not know the technology should not have to fill in (Pere, 30-10): none of these fields exists.
TECHNICAL = ["pythonEdit", "aelRootEdit", "geometryFileEdit", "geometryEdits", "validMaskEdit", "geometryEdit",
             "cameraEdit", "compositeCheck", "noteEdit", "mirroredCheck"]

PJSR = r'''
#engine v8
var CFG = JSON.parse( File.readTextFile( %(config)s ) );
var REPORT = { finished: false, built: 0, messages: [], dialogs: [] };
function save() { File.writeTextFile( CFG.report, JSON.stringify( REPORT, null, 1 ) ); }
// A message box waits for a click that never comes in automation; the entry files call `new MessageBox(...)` by name.
MessageBox = function( text, caption )
{
   this.execute = function() { REPORT.messages.push( String( text ) ); save(); return StdButton.Ok; };
};
// Each dialog class of the plugin extends the global Dialog when its file is read, so it is replaced first.
var BUILT = [];
var NativeDialog = Dialog;
Dialog = class extends NativeDialog
{
   constructor() { super(); BUILT.push( this ); }
};
var checked = false;
var timer = new Timer;
timer.interval = 0.25;
timer.periodic = true;
timer.onTimeout = function()
{
   if ( checked || BUILT.length == 0 )
      return;
   checked = true;
   timer.stop();
   let dialog = BUILT[0];
   let info = { title: dialog.windowTitle, visible: dialog.visible, controls: {}, operations: [] };
   try
   {
      info.runText = dialog.runButton ? dialog.runButton.text : null;
      info.runEnabled = dialog.runButton ? dialog.runButton.enabled : null;
      for ( let i = 0; i < CFG.controls.length; ++i )
         info.controls[CFG.controls[i]] = dialog[CFG.controls[i]] !== undefined && dialog[CFG.controls[i]] !== null;
      info.technical = [];
      for ( let i = 0; i < CFG.technical.length; ++i )
         if ( dialog[CFG.technical[i]] !== undefined )
            info.technical.push( CFG.technical[i] );
      info.aelRoot = dialog.aelRoot !== undefined ? dialog.aelRoot : null;
      info.python = dialog.pythonPath !== undefined ? dialog.pythonPath : null;
      if ( dialog.modeList )
         for ( let i = 0; i < dialog.modeList.numberOfItems; ++i )
            info.operations.push( dialog.modeList.itemText( i ) );
   }
   catch ( error )
   {
      info.error = String( error );
   }
   REPORT.dialogs.push( info );
   save();
   dialog.cancel();
};
timer.start();
#include "%(entry)s"
timer.stop();
REPORT.built = BUILT.length;
REPORT.finished = true;
save();
'''


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


def run_entry(name: str, plugin: Path, work: Path, pixinsight: Path, timeout: float) -> dict:
    """Run one entry file in its own new PixInsight instance and return what the harness recorded."""
    spec = ENTRIES[name]
    work.mkdir(parents=True, exist_ok=True)
    report_path = work / "pjsr_report.json"
    config = {"report": str(report_path), "controls": spec["controls"], "technical": TECHNICAL}
    (work / "entry_config.json").write_text(json.dumps(config, indent=1), encoding="utf-8")
    script = work / f"entry_{name}.js"
    script.write_text(PJSR % {"config": json.dumps(str(work / "entry_config.json")), "entry": plugin / spec["file"]},
                      encoding="utf-8")
    # no AEL_PYTHON, as in dialog_flow.py; its own process group, so that a stop reaches only this instance
    env = {key: value for key, value in os.environ.items() if key != "AEL_PYTHON"}
    process = subprocess.Popen([str(pixinsight), "-n", "--automation-mode", f"-r={script}", "--force-exit"], text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, start_new_session=True)
    stopped = False
    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        stopped = True
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        output, _ = process.communicate()
        output += f"\nSTOPPED: the instance did not finish in {timeout:.0f} s"
    (work / "pixinsight.log").write_text(output, encoding="utf-8")
    recorded = json.loads(report_path.read_text()) if report_path.is_file() else {"finished": False, "dialogs": [],
                                                                                   "messages": ["no report written"]}
    recorded["stopped_by_timeout"] = stopped
    return recorded


def judge(name: str, recorded: dict, expect_root: Path | None) -> dict[str, bool]:
    spec = ENTRIES[name]
    dialogs = recorded.get("dialogs", [])
    first = dialogs[0] if dialogs else {}
    gates = {
        f"{name}_dialog_shown": bool(dialogs) and first.get("title") == spec["title"] and first.get("visible") is True,
        f"{name}_run_button": first.get("runText") == spec["run"] and first.get("runEnabled") is True,
        f"{name}_fields": bool(first) and all(first.get("controls", {}).get(key) for key in spec["controls"]),
        f"{name}_no_technical_fields": bool(first) and first.get("technical") == [],
        f"{name}_closed_and_finished": recorded.get("finished") is True and not recorded.get("stopped_by_timeout"),
        f"{name}_no_message_box": recorded.get("messages") == [],
    }
    if expect_root is not None:
        gates[f"{name}_starts_with_the_expected_AEL_folder"] = first.get("aelRoot") == str(expect_root)
    return gates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, help="checkout: the plugin is REPO/plugins/pixinsight-ael")
    parser.add_argument("--plugin", type=Path, help="folder with AELBridge.js (default: REPO/plugins/pixinsight-ael)")
    parser.add_argument("--expect-root", type=Path, help="the AEL folder the dialogs must start with")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pixinsight", type=Path,
                        default=Path("/Applications/PixInsight/PixInsight.app/Contents/MacOS/PixInsight"))
    parser.add_argument("--timeout", type=float, default=120.0, help="seconds an instance may take (default 120)")
    args = parser.parse_args()
    if args.plugin is None and args.repo is None:
        parser.error("give --repo or --plugin")
    plugin = args.plugin or (args.repo / "plugins/pixinsight-ael")
    expect_root = args.expect_root or (None if args.plugin else args.repo)
    args.output.mkdir(parents=True, exist_ok=True)
    report = {"ok": False, "synthetic": True, "plugin": str(plugin), "gates": {}, "entries": {}}
    with tempfile.TemporaryDirectory(prefix="ael-entries-") as temporary:
        base = Path(temporary) / "prova entrades àè"
        before = tree_sha256(plugin)
        for name in ENTRIES:
            recorded = run_entry(name, plugin, base / name, args.pixinsight, args.timeout)
            report["entries"][name] = recorded
            report["gates"].update(judge(name, recorded, expect_root))
            shutil.copy2(base / name / "pixinsight.log", args.output / f"entry_{name}.log")
        report["gates"]["plugin_unchanged_by_the_runs"] = tree_sha256(plugin) == before

        # control: a bridge entry that has lost the include of its dialog must not pass the same judgement
        broken = base / "plugin_trencat"
        shutil.copytree(plugin, broken)
        entry = broken / ENTRIES["bridge"]["file"]
        text = entry.read_text(encoding="utf-8")
        line = '#include "AELBridgeDialog.jsh"\n'
        if line not in text:
            raise SystemExit("the control cannot be built: the include of the bridge dialog is not in " + str(entry))
        entry.write_text(text.replace(line, ""), encoding="utf-8")
        recorded = run_entry("bridge", broken, base / "control", args.pixinsight, args.timeout)
        report["entries"]["control_broken_bridge"] = recorded
        verdict = judge("bridge", recorded, expect_root)
        report["control_broken_bridge_gates"] = verdict
        report["gates"]["control_broken_entry_is_detected"] = not verdict["bridge_dialog_shown"] and not verdict["bridge_no_message_box"]
    report["ok"] = all(report["gates"].values())
    (args.output / "ENTRY_SCRIPTS.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "output": str(args.output),
                      "failed": [key for key, value in report["gates"].items() if not value]}))
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
