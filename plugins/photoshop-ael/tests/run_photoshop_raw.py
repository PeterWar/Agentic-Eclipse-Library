#!/usr/bin/env python3
"""Photoshop test of the RAW workflow, run the way a person runs it.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

The connector's entry script and dialog run inside Photoshop with three substitutions only: the dialog window, the
file chooser and alert() are test doubles. The window double presses the dialog's own buttons in order (every
"Choose…", then "Make the image"); the chooser double returns the RAW files, then the calibration files, given here;
alert() keeps the messages; and the results go to this test's folder instead of the user's Pictures. The progress
palette, the Python run in the background, opening the PSB and Photoshop's own reading of its layers are the real
ones. Only documents this test opened are closed. The connector's folder must come out byte for byte unchanged.

    python run_photoshop_raw.py --plugin photoshop-ael --raw raws.txt [--calibration calib.txt] --output report/
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

SWAPS = (("new Window(", "new AEL_TEST_WINDOW(", 1), ("File.openDialog(", "AEL_TEST_OPEN_DIALOG(", 1))
DOUBLES = r"""
var AEL_TEST_MESSAGES = [], AEL_TEST_ALL = [], AEL_TEST_CHOICE = 0;
function AEL_TEST_ALERT(message) { AEL_TEST_MESSAGES.push(String(message)); }
function AEL_TEST_OPEN_DIALOG(prompt, filter, multiple) {
    var list = AEL_TEST_CHOICES[AEL_TEST_CHOICE++] || [], files = [];
    for (var i = 0; i < list.length; i++) files.push(new File(list[i]));
    return files.length ? files : null;
}
function AEL_TEST_ELEMENT(kind, text) {
    this.kind = kind; this.text = text || ""; this.preferredSize = {width: 0, height: 0};
}
AEL_TEST_ELEMENT.prototype.add = function (kind, bounds, text, properties) {
    var element = new AEL_TEST_ELEMENT(kind, text);
    element.properties = properties;
    AEL_TEST_ALL.push(element);
    return element;
};
function AEL_TEST_WINDOW(kind, title) { AEL_TEST_ALL = []; this.kind = kind; this.text = title; this.code = null; }
AEL_TEST_WINDOW.prototype = new AEL_TEST_ELEMENT("window", "");
AEL_TEST_WINDOW.prototype.close = function (code) { this.code = code; };
AEL_TEST_WINDOW.prototype.show = function () {
    var i, pressed = [];
    for (i = 0; i < AEL_TEST_ALL.length; i++) {
        if (AEL_TEST_ALL[i].kind === "button" && AEL_TEST_ALL[i].text === "Choose…") {
            AEL_TEST_ALL[i].onClick(); pressed.push("choose");
        }
    }
    for (i = 0; i < AEL_TEST_ALL.length; i++) {
        if (AEL_TEST_ALL[i].kind === "button" && AEL_TEST_ALL[i].text === "Make the image") {
            AEL_TEST_ALL[i].onClick(); pressed.push("make"); break;
        }
    }
    AEL_TEST_PRESSED = pressed;
    return this.code;
};
var AEL_TEST_PRESSED = [];
"""


def do_javascript(code: str, timeout: int) -> subprocess.CompletedProcess:
    script = ('tell application id "com.adobe.Photoshop"\n'
              f'with timeout of {timeout} seconds\n'
              f'do javascript {json.dumps(code, ensure_ascii=False)}\n'
              'end timeout\nend tell')
    return subprocess.run(["osascript", "-e", script], text=True, capture_output=True,
                          timeout=timeout + 60, check=False)


def digest(folder: Path) -> dict:
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()}


def swapped(text: str, swaps) -> str:
    for old, new, count in swaps:
        if text.count(old) != count:
            raise RuntimeError(f"Expected {count} x {old!r} in the connector script, found {text.count(old)}")
        text = text.replace(old, new)
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin", type=Path, required=True, help="the photoshop-ael folder")
    parser.add_argument("--raw", type=Path, required=True, help="text file, one RAW path per line")
    parser.add_argument("--calibration", type=Path, help="text file, one calibration RAW path per line")
    parser.add_argument("--output", type=Path, required=True, help="new folder for this test's report")
    parser.add_argument("--timeout", type=int, default=7200)
    args = parser.parse_args()
    plugin = args.plugin.resolve()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"{output} exists: choose a new folder")
    output.mkdir(parents=True)
    raws = [line.strip() for line in args.raw.read_text(encoding="utf-8").splitlines() if line.strip()]
    calibration = ([line.strip() for line in args.calibration.read_text(encoding="utf-8").splitlines() if line.strip()]
                   if args.calibration else [])
    before = digest(plugin)

    entry = (plugin / "AELPhotoshop.jsx").read_text(encoding="utf-8")
    entry = "\n".join(line for line in entry.splitlines() if not line.startswith("#"))
    entry = swapped(entry, (("alert(", "AEL_TEST_ALERT(", 2),))
    dialog = swapped((plugin / "AELPhotoshopDialog.jsx").read_text(encoding="utf-8"), SWAPS)
    core = plugin / "AELPhotoshopCore.jsx"
    choices = json.dumps([raws, calibration], ensure_ascii=False)
    code = f"""
var AEL_TEST_REPORT = (function () {{
    var before = {{}}, i;
    for (i = 0; i < app.documents.length; i++) before[String(app.documents[i].id)] = true;
    var AEL_TEST_CHOICES = {choices};
    {DOUBLES}
    $.evalFile(new File({json.dumps(str(core))}));
    // The results go to this test's folder, not to the user's Pictures.
    AELPhotoshop.resultsParent = function () {{
        var folder = new Folder({json.dumps(str(output / "results"))});
        if (!folder.exists) folder.create();
        return folder;
    }};
    {dialog}
    var started = new Date().getTime();
    {entry}
    var opened = [], closed = [];
    for (i = app.documents.length - 1; i >= 0; i--) {{
        var doc = app.documents[i];
        if (!before[String(doc.id)]) {{
            var layers = [];
            for (var k = doc.layers.length - 1; k >= 0; k--) {{
                layers.push({{name: doc.layers[k].name, mode: String(doc.layers[k].blendMode),
                    opacity: doc.layers[k].opacity, visible: doc.layers[k].visible}});
            }}
            opened.push({{name: doc.name, path: doc.fullName.fsName, bits: String(doc.bitsPerChannel),
                width: doc.width.as("px"), height: doc.height.as("px"), layers: layers,
                profile: doc.colorProfileType === ColorProfile.NONE ? null : doc.colorProfileName}});
            doc.close(SaveOptions.DONOTSAVECHANGES);
            closed.push(true);
        }}
    }}
    return AELPhotoshop.jsonString({{messages: AEL_TEST_MESSAGES, pressed: AEL_TEST_PRESSED, opened: opened,
        seconds: (new Date().getTime() - started) / 1000, documents_left: app.documents.length}});
}}());
AEL_TEST_REPORT;
"""
    (output / "harness.jsx").write_text(code, encoding="utf-8")
    t0 = time.time()
    done = do_javascript(code, args.timeout)
    report = {"seconds": round(time.time() - t0, 1), "osascript_exit": done.returncode,
              "stderr": done.stderr.strip()[-2000:]}
    try:
        report.update(json.loads(done.stdout.strip()))
    except Exception:
        report["stdout"] = done.stdout.strip()[-4000:]
    messages = report.get("messages", [])
    report["unchanged_plugin"] = digest(plugin) == before
    folder = None
    if messages:
        match = re.search(r"saved, with the linear master and a receipt, in:\n(.+)$", messages[-1])
        folder = Path(match.group(1).strip()) if match else None
    report["result_folder"] = str(folder) if folder else None
    gates = {"dialog_pressed_its_buttons": report.get("pressed", [])[-1:] == ["make"],
             "done_message": bool(messages) and messages[-1].startswith("Done:"),
             "one_psb_opened": len(report.get("opened", [])) == 1,
             "plugin_unchanged": report["unchanged_plugin"]}
    if folder and (folder / "AEL receipt.json").is_file():
        receipt = json.loads((folder / "AEL receipt.json").read_text(encoding="utf-8"))
        report["summary"] = receipt["summary"]
        opened = report.get("opened") or [{}]
        expected = [layer["name"] for layer in receipt["layers"]]
        gates["layers_as_written"] = [layer["name"] for layer in opened[0].get("layers", [])] == expected
        gates["psb_is_16_bit"] = opened[0].get("bits") == "BitsPerChannelType.SIXTEEN"
        gates["psb_sha_matches_receipt"] = (Path(receipt["outputs"]["psb"]["path"]).is_file() and
                                            hashlib.sha256(Path(receipt["outputs"]["psb"]["path"]).read_bytes()).hexdigest()
                                            == receipt["outputs"]["psb"]["sha256"])
    report["gates"] = gates
    report["ok"] = all(gates.values()) and len(gates) >= 7
    (output / "REPORT.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "gates": gates, "seconds": report["seconds"],
                      "messages": [m[:400] for m in messages], "summary": report.get("summary")},
                     indent=1, ensure_ascii=False))
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
