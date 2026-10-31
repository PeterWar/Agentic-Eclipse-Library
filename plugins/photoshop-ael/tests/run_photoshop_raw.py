#!/usr/bin/env python3
"""Photoshop test of the RAW workflow, run the way a person runs it.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

The connector's entry script and dialog run inside Photoshop with five substitutions only: the dialog windows, the
file chooser, the folder chooser, opening a web page and alert() are test doubles. The window double presses the
dialog's own buttons in order ("Browse…", every "Choose…", "Advanced settings…", "GitHub", then "Make the image"); in
the advanced settings it presses "AEL defaults", ticks the extra filters given here (by default the NRGF log at 0 %,
which must arrive as a hidden layer) and presses "OK". The file chooser double returns the RAW files, then the darks,
then the flats, given here; the folder chooser double returns this test's results folder; the web page double keeps
the address; alert() keeps the messages. Every button, tick box and field of both windows must say what it does when
the pointer rests on it. The progress palette, the Python run in the background, opening the PSB and Photoshop's own
reading of its layers are the real ones; the palette's log must say that AEL is still working during a long step.
Only documents this test opened are closed. The connector's folder must come out byte for byte unchanged.

The output folder the dialog keeps in Photoshop's custom options is set aside before the run, so the dialog starts as
it does the first time (at Downloads), and put back afterwards. Nothing is written to Downloads.

    python run_photoshop_raw.py --plugin photoshop-ael --raw raws.txt [--darks darks.txt] [--flats flats.txt]
        [--extra-filter "01 NRGF log=0"] --output report/
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

SWAPS = (("new Window(", "new AEL_TEST_WINDOW(", 2), ("File.openDialog(", "AEL_TEST_OPEN_DIALOG(", 1),
         ("output.folder.selectDlg(", "AEL_TEST_SELECT_FOLDER(output.folder, ", 1), ("alert(", "AEL_TEST_ALERT(", 3))
GITHUB = "https://github.com/PeterWar/Agentic-Eclipse-Library"
DOUBLES = r"""
var AEL_TEST_MESSAGES = [], AEL_TEST_CHOICE = 0, AEL_TEST_SHOWN = [], AEL_TEST_STARTS = [], AEL_TEST_URLS = [];
var AEL_TEST_PRESSED = [], AEL_TEST_ADVANCED_PRESSED = [], AEL_TEST_CHOICE_LINE = [], AEL_TEST_NO_TIP = [];
function AEL_TEST_ALERT(message) { AEL_TEST_MESSAGES.push(String(message)); }
function AEL_TEST_SELECT_FOLDER(start, prompt) {
    AEL_TEST_STARTS.push(start.fsName);
    return new Folder(AEL_TEST_PICKED);
}
function AEL_TEST_OPEN_DIALOG(prompt, filter, multiple) {
    var list = AEL_TEST_CHOICES[AEL_TEST_CHOICE++] || [], files = [];
    for (var i = 0; i < list.length; i++) files.push(new File(list[i]));
    return files.length ? files : null;
}
// Every element belongs to its window (win.all, in the order the dialog adds them), so that a window opened from
// another keeps its own.
function AEL_TEST_ELEMENT(kind, text, root) {
    this.kind = kind; this.text = text || ""; this.root = root || this;
    this.preferredSize = {width: 0, height: 0};
    this.graphics = {PenType: {SOLID_COLOR: 0}, newPen: function () { return {}; }};
    if (!root) this.all = [];
}
AEL_TEST_ELEMENT.prototype.add = function (kind, bounds, text, properties) {
    var element = new AEL_TEST_ELEMENT(kind, text, this.root);
    element.properties = properties;
    this.root.all.push(element);
    return element;
};
function AEL_TEST_WINDOW(kind, title) { AEL_TEST_ELEMENT.call(this, kind, title); this.code = null; }
AEL_TEST_WINDOW.prototype = new AEL_TEST_ELEMENT("window", "");
AEL_TEST_WINDOW.prototype.close = function (code) { this.code = code; };
AEL_TEST_WINDOW.prototype.show = function () {
    return this.text === "Advanced settings" ? AEL_TEST_ADVANCED(this) : AEL_TEST_MAIN(this);
};
// a button, tick box or field that does not say what it does
function AEL_TEST_TIPS(win) {
    for (var i = 0; i < win.all.length; i++) {
        var e = win.all[i];
        if ((e.kind === "button" || e.kind === "checkbox" || e.kind === "edittext") && !e.helpTip) {
            AEL_TEST_NO_TIP.push(win.text + ": " + e.kind + " " + e.text);
        }
    }
}
function AEL_TEST_PRESS(win, label) {
    for (var i = 0; i < win.all.length; i++) {
        if (win.all[i].kind === "button" && win.all[i].text === label) { win.all[i].onClick(); return; }
    }
    throw new Error("No button " + label + " in " + win.text);
}
function AEL_TEST_MAIN(win) {
    var i, e, pressed = [];
    // the output folder the dialog shows (the text after its button), before and after "Browse…"
    for (i = 0; i < win.all.length; i++) {
        e = win.all[i];
        if (e.kind === "button" && e.text === "Browse…") {
            AEL_TEST_SHOWN.push(win.all[i + 1].text);
            e.onClick(); pressed.push("browse");
            AEL_TEST_SHOWN.push(win.all[i + 1].text);
        }
    }
    for (i = 0; i < win.all.length; i++) {
        e = win.all[i];
        if (e.kind === "button" && e.text === "Choose…") { e.onClick(); pressed.push("choose"); }
    }
    // the filter line (the text before its button), before and after the advanced settings; then the GitHub button
    for (i = 0; i < win.all.length; i++) {
        e = win.all[i];
        if (e.kind === "button" && e.text === "Advanced settings…") {
            AEL_TEST_CHOICE_LINE.push(win.all[i - 1].text);
            e.onClick(); pressed.push("advanced");
            AEL_TEST_CHOICE_LINE.push(win.all[i - 1].text);
        }
        if (e.kind === "button" && e.text === "GitHub") { e.onClick(); pressed.push("github"); }
    }
    AEL_TEST_TIPS(win);
    for (i = 0; i < win.all.length; i++) {
        e = win.all[i];
        if (e.kind === "button" && e.text === "Make the image") { e.onClick(); pressed.push("make"); break; }
    }
    AEL_TEST_PRESSED = pressed;
    return win.code;
}
function AEL_TEST_ADVANCED(win) {
    var i, k, e, label;
    AEL_TEST_PRESS(win, "AEL defaults"); AEL_TEST_ADVANCED_PRESSED.push("defaults");
    for (label in AEL_TEST_EXTRA) {
        for (i = 0; i < win.all.length; i++) {
            e = win.all[i];
            if (e.kind !== "checkbox" || e.text !== label) continue;
            e.value = true;
            for (k = i + 1; k < win.all.length; k++) {
                if (win.all[k].kind === "edittext") { win.all[k].text = AEL_TEST_EXTRA[label]; break; }
            }
            AEL_TEST_ADVANCED_PRESSED.push("tick " + label);
        }
    }
    AEL_TEST_TIPS(win);
    AEL_TEST_PRESS(win, "OK"); AEL_TEST_ADVANCED_PRESSED.push("ok");
    return win.code;
}
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
    parser.add_argument("--darks", type=Path, help="text file, one dark RAW path per line")
    parser.add_argument("--flats", type=Path, help="text file, one flat RAW path per line")
    parser.add_argument("--extra-filter", action="append", default=None, metavar="LABEL=PERCENT",
                        help='a filter to tick in the advanced settings, as it is listed there (default "01 NRGF log=0")')
    parser.add_argument("--output", type=Path, required=True, help="new folder for this test's report")
    parser.add_argument("--timeout", type=int, default=7200)
    args = parser.parse_args()
    plugin = args.plugin.resolve()
    output = args.output.resolve()
    if output.exists():
        raise SystemExit(f"{output} exists: choose a new folder")
    output.mkdir(parents=True)
    raws = [line.strip() for line in args.raw.read_text(encoding="utf-8").splitlines() if line.strip()]
    listed = lambda path: ([line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
                           if path else [])
    darks, flats = listed(args.darks), listed(args.flats)
    extra = dict(item.rsplit("=", 1) for item in (args.extra_filter or ["01 NRGF log=0"]))
    before = digest(plugin)

    entry = (plugin / "AELPhotoshop.jsx").read_text(encoding="utf-8")
    entry = "\n".join(line for line in entry.splitlines() if not line.startswith("#"))
    entry = swapped(entry, (("alert(", "AEL_TEST_ALERT(", 2),))
    dialog = swapped((plugin / "AELPhotoshopDialog.jsx").read_text(encoding="utf-8"), SWAPS)
    core = plugin / "AELPhotoshopCore.jsx"
    choices = json.dumps([raws, darks, flats], ensure_ascii=False)
    picked = output / "results"
    picked.mkdir()
    code = f"""
var AEL_TEST_REPORT = (function () {{
    var before = {{}}, i;
    for (i = 0; i < app.documents.length; i++) before[String(app.documents[i].id)] = true;
    var AEL_TEST_CHOICES = {choices};
    var AEL_TEST_PICKED = {json.dumps(str(picked))};
    var AEL_TEST_EXTRA = {json.dumps(extra, ensure_ascii=False)};
    {DOUBLES}
    $.evalFile(new File({json.dumps(str(core))}));
    // "GitHub" would open the browser: the address is kept instead.
    AELPhotoshop.openUrl = function (url) {{ AEL_TEST_URLS.push(url); }};
    // The output folder the dialog keeps: set aside, so the dialog starts as the first time, and put back afterwards.
    var kept = AELPhotoshop.savedOutput(), remembered = null, restored = null;
    try {{ app.eraseCustomOptions(AELPhotoshop.outputKey); }} catch (none) {{}}
    var started = new Date().getTime();
    try {{
        {dialog}
        {entry}
    }} finally {{
        remembered = AELPhotoshop.savedOutput();
        if (kept) AELPhotoshop.saveOutput(kept);
        else {{ try {{ app.eraseCustomOptions(AELPhotoshop.outputKey); }} catch (none2) {{}} }}
        restored = AELPhotoshop.savedOutput();
    }}
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
        seconds: (new Date().getTime() - started) / 1000, documents_left: app.documents.length,
        output_shown: AEL_TEST_SHOWN, folder_chooser_started_at: AEL_TEST_STARTS, output_kept_before: kept,
        output_remembered: remembered, output_kept_after: restored, advanced_pressed: AEL_TEST_ADVANCED_PRESSED,
        filter_line: AEL_TEST_CHOICE_LINE, urls: AEL_TEST_URLS, without_tip: AEL_TEST_NO_TIP,
        progress_log: AELPhotoshop.progressLog || []}});
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
        match = re.search(r"saved, with the linear master and a receipt, in:\n([^\n]+)", messages[-1])
        folder = Path(match.group(1).strip()) if match else None
    report["result_folder"] = str(folder) if folder else None
    remembered = report.get("output_remembered")
    gates = {"dialog_pressed_its_buttons": (report.get("pressed") == ["browse", "choose", "choose", "choose", "advanced",
                                                                      "github", "make"] and
                                            report.get("advanced_pressed") == ["defaults"] + [f"tick {label}" for label in
                                                                                              extra] + ["ok"]),
             "done_message": bool(messages) and messages[-1].startswith("Done:"),
             # what the PixInsight connector also does: a word for every control, the invitation and its GitHub
             # button, the filter line, and a progress that keeps talking during a long step
             "every_control_says_what_it_does": report.get("without_tip") == [],
             "github_button_opens_the_library": report.get("urls") == [GITHUB],
             "done_message_invites_to_the_library": bool(messages) and messages[-1].endswith(
                 "try the whole Agentic Eclipse Library with an AI agent: " + GITHUB),
             "progress_says_it_is_still_working": any(line.startswith("AEL: still working on Filters")
                                                      for line in report.get("progress_log", [])),
             "one_psb_opened": len(report.get("opened", [])) == 1,
             "plugin_unchanged": report["unchanged_plugin"],
             # nothing kept: the dialog shows Downloads; "Browse…" changes it; the run goes to a new dated folder in it
             "output_folder_starts_at_downloads": (report.get("output_shown", [])[:1] == ["~/Downloads"] and
                                                   report.get("folder_chooser_started_at") == [str(Path.home() / "Downloads")]),
             "results_in_a_new_folder_inside_the_chosen_one": bool(folder) and folder.parent == picked
                                                               and folder.name.startswith("AEL_"),
             "output_folder_remembered": bool(remembered) and Path(remembered).resolve() == picked,
             "kept_folder_put_back": report.get("output_kept_after") == report.get("output_kept_before")}
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
        # the advanced settings reach the PSB: AEL's three default layers, visible, then each extra filter, hidden when
        # its opacity is 0, under the names AEL gives them (two of one family become 01a, 01b); Photoshop reads them so;
        # the filter line said so before the run
        keys = dict((label, name) for name, label in re.findall(r'\{name: "(\w+)", label: "([^"]+)"', core.read_text(
            encoding="utf-8")))
        wanted = [("nrgf", True), ("wow_edge_aware", True), ("achf_iso_04", True)] + [
            (keys.get(label), int(percent) > 0) for label, percent in extra.items()]
        made = json.loads((folder / "details" / "filters_receipt.json").read_text(encoding="utf-8"))["parameters"]["layers"]
        read = [(layer["name"], layer["visible"]) for layer in opened[0].get("layers", [])[3:]]
        report["filter_layers"] = {"wanted": wanted, "made": [(e["name"], e["layer"], e["visible"]) for e in made],
                                   "read_in_photoshop": read}
        gates["advanced_settings_reach_the_psb"] = ([(e["name"], e["visible"]) for e in made] == wanted and
                                                    read == [(e["layer"], e["visible"]) for e in made])
        hidden = sum(1 for percent in extra.values() if int(percent) == 0)
        line = "Filter layers: NRGF 39\u00a0%, ACHF iso 1–16 px 8\u00a0%, WOW edge-aware 37\u00a0%"
        gates["filter_line_shows_the_choice"] = report.get("filter_line") == [
            line, line + (f", and {hidden} more, hidden" if hidden else "")]
    report["gates"] = gates
    report["ok"] = all(gates.values()) and len(gates) >= 17
    (output / "REPORT.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "gates": gates, "seconds": report["seconds"],
                      "messages": [m[:400] for m in messages], "summary": report.get("summary")},
                     indent=1, ensure_ascii=False))
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
