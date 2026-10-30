#!/usr/bin/env python3
"""Photoshop test of a folder written by tools/build_package.py, run the way a person runs it.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

The entry script and the dialog are the package's own, evaluated with three substitutions only: the
ScriptUI window, the file and folder choosers, and alert() are replaced by test doubles that fill in the
dialog and keep the messages, so that no modal window can appear. Python and AEL are left empty in the
dialog: the package must find a Python and use its bundled runtime/ael. The four operations run on the
package's demonstration files, plus a master without frames that must be refused. Only documents opened
by this test are closed, and the package must come out byte for byte unchanged.

    python run_package_tests.py --package /path/to/package --output /path/to/new/folder
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

DIALOG_SWAPS = (("new Window(", "new AEL_TEST_WINDOW(", 1), ("File.openDialog(", "AEL_TEST_OPEN_DIALOG(", 2),
                ("Folder.selectDialog(", "AEL_TEST_SELECT_FOLDER(", 1))
# The synthetic drift of demo frames 2 and 3 (tools/make_demo.py), measured on the Sun by the master.
DEMO_DRIFT = [[0.0, 0.0], [2.0, -1.5], [-2.5, 2.0]]


def do_javascript(code: str, timeout: int) -> subprocess.CompletedProcess:
    script = ('tell application id "com.adobe.Photoshop"\n'
              f'with timeout of {timeout} seconds\n'
              f'do javascript {json.dumps(code, ensure_ascii=False)}\n'
              'end timeout\nend tell')
    return subprocess.run(["osascript", "-e", script], text=True, capture_output=True,
                          timeout=timeout + 30, check=False)


def digest(folder: Path) -> dict:
    answer = {}
    for path in sorted(p for p in folder.rglob("*") if p.is_file() or p.is_symlink()):
        answer[str(path.relative_to(folder))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return answer


def swapped(text: str, swaps) -> str:
    for old, new, count in swaps:
        if text.count(old) != count:
            raise RuntimeError(f"Expected {count} × {old!r} in the package script, found {text.count(old)}")
        text = text.replace(old, new)
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    package = args.package.resolve()
    plugin = package / "photoshop-ael"
    demo = package / "demo"
    output = args.output.resolve()
    if output == package or package in output.parents:
        raise SystemExit("The output folder must be outside the package")
    if output.exists():
        raise SystemExit(f"{output} exists: choose a new folder")
    output.mkdir(parents=True)
    runs = output / "runs àè"
    runs.mkdir()
    before = digest(package)

    entry = (plugin / "AELPhotoshop.jsx").read_text(encoding="utf-8")
    entry = "\n".join(line for line in entry.splitlines() if not line.startswith("#"))
    entry = swapped(entry, (("alert(", "AEL_TEST_ALERT(", 2), ("AELPhotoshopDialog()", "AELPhotoshopDialog()", 1)))
    dialog = swapped((plugin / "AELPhotoshopDialog.jsx").read_text(encoding="utf-8"), DIALOG_SWAPS)

    s, m, f = demo / "1_structure_polar", demo / "3_master", demo / "2_filters" / "linear_master"
    frames = [str(m / f"frame_{i}.tif") for i in (1, 2, 3)]
    # Fields for other operations are filled in on purpose: the dialog must leave them out.
    plans = [
        {"name": "structure", "index": 0, "open": str(s / "corona_linear.tif"), "geometry": str(s / "geometry.json"),
         "linear": str(f / "linear.npy"), "camera": str(m / "camera.json"), "rmax": "3,5", "frames": []},
        {"name": "polar", "index": 1, "open": str(s / "corona_display.tif"), "geometry": str(s / "geometry.json"),
         "linear": str(f / "linear.npy"), "camera": str(m / "camera.json"), "rmax": "3,5", "frames": []},
        {"name": "master", "index": 2, "geometry": str(m / "geometry.json"), "linear": str(f / "linear.npy"),
         "camera": str(m / "camera.json"), "rmax": "3,5", "frames": frames},
        {"name": "filters", "index": 3, "geometry": "", "linear": str(f / "linear.npy"),
         "camera": str(m / "camera.json"), "rmax": "3,5", "frames": []},
        {"name": "master_without_frames", "index": 2, "geometry": str(m / "geometry.json"), "linear": "",
         "camera": str(m / "camera.json"), "rmax": "4.0", "frames": []},
    ]
    progress = output / "JSX_PROGRESS.json"
    jsx = f'''#include {json.dumps(str(plugin / "AELPhotoshopCore.jsx"))}
var AEL_TEST = {{plan: null, closed: null, alerts: [], answer: null, result: null}};
var REPORT = {{ok: false, runs: [], documents_before: app.documents.length}};
function AEL_TEST_CONTROL(type, text, items) {{
    this.type = type; this.text = text === undefined ? "" : text; this.items = items || null;
    this.preferredSize = {{}}; this.children = []; this.value = false;
    AEL_TEST.controls.push(this);
}}
AEL_TEST_CONTROL.prototype.add = function (type, bounds, text, properties) {{
    var items = type === "dropdownlist" ? text : null;
    var control = new AEL_TEST_CONTROL(type, items ? "" : text, items);
    if (items) control.watch("selection", function (name, old, value) {{
        return typeof value === "number" ? {{index: value, text: items[value]}} : value; }});
    this.children.push(control);
    return control;
}};
function AEL_TEST_WINDOW(type, title) {{
    AEL_TEST.controls = []; this.type = type; this.title = title; this.children = []; this.preferredSize = {{}};
}}
AEL_TEST_WINDOW.prototype.add = AEL_TEST_CONTROL.prototype.add;
AEL_TEST_WINDOW.prototype.close = function (code) {{ AEL_TEST.closed = code; }};
AEL_TEST_WINDOW.prototype.show = function () {{
    var plan = AEL_TEST.plan, fields = [], i, c, dropdown, checkbox, choose, run;
    for (i = 0; i < AEL_TEST.controls.length; i++) {{
        c = AEL_TEST.controls[i];
        if (c.type === "edittext") fields.push(c);
        if (c.type === "dropdownlist") dropdown = c;
        if (c.type === "checkbox") checkbox = c;
        if (c.type === "button" && c.text === "Choose master frames…") choose = c;
        if (c.type === "button" && c.text === "Run AEL") run = c;
    }}
    if (fields.length !== 8 || !dropdown || !checkbox || !choose || !run)
        throw new Error("Unexpected dialog layout: " + fields.length + " fields");
    AEL_TEST.default_output = fields[0].text;
    dropdown.selection = plan.index;
    var values = [{json.dumps(str(runs))}, plan.geometry, "", "", plan.linear, plan.camera, "", plan.rmax];
    for (i = 0; i < 8; i++) fields[i].text = values[i];
    checkbox.value = false;
    if (plan.frames.length) {{ AEL_TEST.files = plan.frames; choose.onClick(); }}
    run.onClick();
    return AEL_TEST.closed;
}};
function AEL_TEST_OPEN_DIALOG(prompt, filter, multiple) {{
    var files = [];
    for (var i = 0; i < (AEL_TEST.files || []).length; i++) files.push(new File(AEL_TEST.files[i]));
    AEL_TEST.files = null;
    return multiple ? files : (files[0] || null);
}}
function AEL_TEST_SELECT_FOLDER() {{ return null; }}
function AEL_TEST_ALERT(message) {{ AEL_TEST.alerts.push(String(message)); }}
{dialog}
var AEL_TEST_REAL_DIALOG = AELPhotoshopDialog;
AELPhotoshopDialog = function () {{
    // A copy: AELPhotoshop.run completes the same object (Python found, run folder, exported input).
    var answer = AEL_TEST_REAL_DIALOG(), copy = {{}};
    for (var key in answer) if (answer.hasOwnProperty(key))
        copy[key] = answer[key] instanceof Array ? answer[key].slice(0) : answer[key];
    AEL_TEST.answer = copy;
    return answer;
}};
function AEL_TEST_ENTRY() {{
{entry}
}}
var AEL_TEST_REAL_RUN = AELPhotoshop.run;
var PLANS = {json.dumps(plans, ensure_ascii=False)};
try {{
    AELPhotoshop.run = function (options) {{ AEL_TEST.result = AEL_TEST_REAL_RUN(options); return AEL_TEST.result; }};
    for (var p = 0; p < PLANS.length; p++) {{
        var plan = PLANS[p], owned = {{}}, record = {{name: plan.name}};
        AEL_TEST.plan = plan; AEL_TEST.alerts = []; AEL_TEST.answer = null; AEL_TEST.result = null;
        REPORT.stage = plan.name; AELPhotoshop.writeJSON(new File({json.dumps(str(progress))}), REPORT);
        var source = null;
        if (plan.open) {{
            // Opening a file that is already open would return that document, unsaved changes included.
            if (AELPhotoshop.isOpen(plan.open)) throw new Error("Already open in Photoshop, not touched: " + plan.open);
            var oldDialogs = app.displayDialogs; app.displayDialogs = DialogModes.NO;
            try {{ source = app.open(new File(plan.open)); }} finally {{ app.displayDialogs = oldDialogs; }}
            owned[String(source.id)] = true;
            record.source_saved_before = source.saved;
        }}
        try {{ AEL_TEST_ENTRY(); }}
        finally {{
            if (AEL_TEST.result && AEL_TEST.result.opened_documents)
                for (var d = 0; d < AEL_TEST.result.opened_documents.length; d++)
                    owned[String(AEL_TEST.result.opened_documents[d].id)] = true;
            if (source) record.source_saved_after = source.saved;
            record.answer = AEL_TEST.answer; record.alerts = AEL_TEST.alerts;
            record.default_output = AEL_TEST.default_output;
            if (AEL_TEST.result) record.result = {{run_root: AEL_TEST.result.run_root,
                opened: AEL_TEST.result.opened_documents.length, native_check: AEL_TEST.result.native_check || null,
                ael_version: AEL_TEST.result.ael_version, receipt: AEL_TEST.result.bridge_receipt,
                registrations: AEL_TEST.result.registrations || null}};
            record.documents_open_before_closing = app.documents.length;
            for (var k = app.documents.length - 1; k >= 0; k--) {{
                var doc = app.documents[k], path = "";
                try {{ path = doc.fullName.fsName; }} catch (unsaved) {{}}
                // A run that failed after opening some results returns no list: its files are in the runs folder.
                if (owned[String(doc.id)] || path.indexOf({json.dumps(str(runs) + "/")}) === 0)
                    doc.close(SaveOptions.DONOTSAVECHANGES);
            }}
            REPORT.runs.push(record);
        }}
    }}
    REPORT.ok = true;
}} catch (e) {{ REPORT.error = String(e.message); REPORT.line = e.line; }}
finally {{
    AELPhotoshop.run = AEL_TEST_REAL_RUN;
    REPORT.documents_after = app.documents.length;
    AELPhotoshop.writeJSON(new File({json.dumps(str(progress))}), REPORT);
    AEL_TEST = null;
}}
'AEL_PACKAGE_TEST_DONE';'''
    (output / "package_test.jsx").write_text(jsx, encoding="utf-8")
    completed = do_javascript(jsx, timeout=1500)
    report = {"package": str(package), "output": str(output), "photoshop_stdout": completed.stdout.strip(),
              "photoshop_stderr": completed.stderr.strip()}
    jsx_report = json.loads(progress.read_text(encoding="utf-8")) if progress.exists() else {}
    report["jsx"] = jsx_report
    runs_by_name = {run["name"]: run for run in jsx_report.get("runs", [])}
    runtime = os.path.realpath(plugin / "runtime" / "ael")
    gates = {"photoshop_ran": completed.returncode == 0 and jsx_report.get("ok") is True}
    expected = {"structure": (3, None, {"geometry"}), "polar": (8, None, {"geometry", "rmax"}),
                "master": (2, 19, {"geometry", "camera"}), "filters": (1, 19, {"input"})}
    common = {"operation", "outputParent", "python", "aelFolder", "open_mode", "frames"}
    for name, (opened, layers, keys) in expected.items():
        run = runs_by_name.get(name, {})
        answer, result = run.get("answer") or {}, run.get("result") or {}
        alert = (run.get("alerts") or [""])[0]
        receipt = json.loads(Path(result["receipt"]).read_text(encoding="utf-8")) if result.get("receipt") else {}
        ael_file = (receipt.get("runtime") or {}).get("ael_file") or ""
        checks = {
            "dialog_fields": set(answer) == common | keys and answer.get("operation") == name and
                answer.get("python") == "" and answer.get("aelFolder") == "" and answer.get("open_mode") == "layered",
            "opened": result.get("opened") == opened,
            "alert": alert.startswith(f"AEL 1.3.6 completed. {opened} result document(s) opened."),
            "bundled_ael": receipt.get("runtime", {}).get("ael_version") == "1.3.6" and
                os.path.realpath(ael_file).startswith(runtime + os.sep),
        }
        if layers:
            native = result.get("native_check") or {}
            checks["psb_native"] = native.get("ok") is True and native.get("layers") == layers and \
                f"Layered PSB checked in Photoshop: OK, {layers} layers." in alert
        if name == "polar":
            checks["rmax_comma"] = answer.get("rmax") == 3.5
        if name == "master":
            checks["frames"] = answer.get("frames") == frames
            measured = [r.get("translation") for r in result.get("registrations") or []]
            checks["registration_0.1px"] = len(measured) == 3 and all(
                abs(a - b) <= 0.1 for row, truth in zip(measured, DEMO_DRIFT) for a, b in zip(row, truth))
            report["master_translation"] = measured
        if name in ("structure", "polar"):
            checks["source_unchanged"] = run.get("source_saved_before") == run.get("source_saved_after")
        report[name] = {"checks": checks, "alert": alert, "ael_file": ael_file, "python": receipt.get("runtime", {}).get("python")}
        gates.update({f"{name}_{key}": value for key, value in checks.items()})
    refused = runs_by_name.get("master_without_frames", {})
    gates["master_without_frames_refused"] = (refused.get("alerts") or [""])[0].startswith(
        "AEL could not complete:\nSelect the master frames") and not refused.get("result")
    gates["default_output_documents"] = all(run.get("default_output") for run in runs_by_name.values())
    gates["photoshop_documents_restored"] = jsx_report.get("documents_after") == jsx_report.get("documents_before")
    gates["package_unchanged"] = digest(package) == before
    report["gates"] = gates
    report["ok"] = all(gates.values())
    (output / "PACKAGE_TEST.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "gates": gates}, indent=1, ensure_ascii=False))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
