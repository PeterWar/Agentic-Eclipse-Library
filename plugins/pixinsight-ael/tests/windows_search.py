#!/usr/bin/env python3
"""The search for a Python on Windows, checked in PixInsight on any system.

The connector's own search on Windows (aelBridgeWindowsPythons in AELBridgeCore.jsh) depends only on the folders it
is given, so it is run here on a made-up Windows disk: the folders where the installers, conda, the virtual
environments, the py launcher and the Microsoft Store put a Python. The stand-in for py.exe is a small script that
answers as the launcher does (one Python by default, another for ``-3``) and one stand-in for python.exe starts the
Python running this test, so the launcher is really asked and the probe really runs through a file named python.exe,
with the environment the connector hands to a Python on Windows.

Then the whole search runs as it does on Windows, in a copy of the connector with two changes, the ones the system
itself makes there (aelBridgeOnWindows() answers yes, and the lines kept for macOS are left out), started with the environment of that made-up computer (USERPROFILE, LOCALAPPDATA,
PATH with ";", AEL_PYTHON written with "\" and quotes): the Python is found, and on an empty computer the message
says what to do on Windows.

It does not replace a run on Windows: what Windows itself does (its file system, its environment, how it starts a
process) is not exercised here.

    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python plugins/pixinsight-ael/tests/windows_search.py \
        [--pixinsight /path/to/PixInsight] [--plugin PACKAGE/pixinsight-ael --root PACKAGE/pixinsight-ael/runtime] \
        [--output FOLDER]

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

CREDIT = ("Processed with Agentic Eclipse Library by Pere Guerra — "
          "https://github.com/PeterWar/Agentic-Eclipse-Library")

BODY = r'''
var REPORT = {};
try
{
   let disk = CFG.disk;
   function back( path ) { return path.split( "/" ).join( "\\" ); }   // no /\//: PixInsight reads "//" as a comment
   let home = disk + "/Home/u", local = home + "/AppData/Local";
   // as Windows gives them: with "\", a folder of PATH ending in "\", one between quotes, an empty one, one that is not there
   let places = { home: home, local: local, programs: [ disk + "/Program Files", disk + "/Program Files (x86)" ],
                  data: disk + "/ProgramData", system: disk + "/Windows", drive: disk,
                  path: [ back( disk + "/tools" ) + "\\", back( local + "/Microsoft/WindowsApps" ), "",
                          "\"" + back( disk + "/Program Files/Python312" ) + "\"", back( disk + "/missing" ),
                          back( disk + "/TOOLS" ) ] };
   REPORT.found = aelBridgeWindowsPythons( places );
   REPORT.launcher = aelBridgeLauncherPythons( disk + "/Windows/py.exe" );
   REPORT.listed = aelBridgeLauncherListed( " -V:3.13 *        C:\\Home\\u\\AppData\\Local\\Programs\\Python\\Python313\\python.exe\r\n"
                                            + " -V:3.12          D:\\My Tools\\Python\\python.exe\r\n"
                                            + " -V:3.12          D:\\My Tools\\Python\\python.exe\r\n"
                                            + "No path on this line\n" );
   REPORT.empty = aelBridgeWindowsPythons( { home: disk + "/nobody", local: disk + "/nobody/AppData/Local", programs: [],
                                             data: disk + "/none", system: disk + "/none", drive: disk + "/none",
                                             path: [] } );
   REPORT.onWindows = aelBridgeOnWindows();
   REPORT.paths = aelBridgeResultPaths( { a: "C:\\x\\y z.tif", b: [ "\\\\server\\share\\f.tif", "keep \\ this" ], n: 3,
                                          c: { d: "D:\\e", e: "C:/already/right", f: null } } );
   REPORT.slashes = aelBridgeSlashes( "C:\\a\\b/c" );
   REPORT.environment = aelBridgeWindowsEnvironment();
   REPORT.adviceNothing = aelBridgeWindowsAdvice( [] );
   REPORT.adviceTried = aelBridgeWindowsAdvice( [ "C:/p/python.exe: Cannot import ael: No module named 'numpy'" ] );
   // the probe through a file named python.exe, as the connector runs it, and with what it hands to a Python on Windows
   let named = disk + "/tools/python.exe";
   let probe = aelBridgeProbe( named, CFG.root );
   REPORT.probe = { ok: probe.ok, python: probe.python, message: probe.message || "", ael_version: probe.ael_version || "" };
   let environment = [ "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=" + CFG.root ].concat( aelBridgeWindowsEnvironment() );
   let run = aelBridgeRun( named, [ AEL_BRIDGE_CHECK_SCRIPT, "probe" ], CFG.root, environment, 20000 );
   REPORT.probeWindowsEnvironment = { ok: run.ok, answer: run.ok ? aelBridgeParseJson( run.stdout, "probe" ) : null,
                                      stderr: run.stderr };
   run = aelBridgeRun( named, [ "-c", "import sys, os; print(sys.flags.utf8_mode, sys.stdout.encoding, "
                                       + "os.environ.get('PYTHONDONTWRITEBYTECODE'))" ], CFG.root, environment, 20000 );
   REPORT.utf8 = run.stdout.trim();
   // a Python that is not there, and a folder: refused before anything is started
   REPORT.missing = aelBridgeProbe( disk + "/missing/python.exe", CFG.root ).message;
   // the whole search of this system is the one it was: something is found without anything chosen
   Settings.remove( AEL_BRIDGE_SETTINGS_KEY + "pythonPath" );
   let detected = aelBridgeCandidates( "", CFG.root );
   REPORT.here = { python: detected.python, ael_version: detected.ael_version };
   REPORT.ok = true;
}
catch ( error )
{
   REPORT.ok = false;
   REPORT.error = String( error );
}
File.writeTextFile( CFG.report, JSON.stringify( REPORT, null, 1 ) );
'''


FORCED_BODY = r'''
var REPORT = {};
try
{
   REPORT.onWindows = aelBridgeOnWindows();
   Settings.remove( AEL_BRIDGE_SETTINGS_KEY + "pythonPath" );
   try
   {
      let detected = aelBridgeCandidates( "", CFG.root );
      REPORT.detected = { python: detected.python, ael_version: detected.ael_version, tried_before: detected.diagnostics };
   }
   catch ( error )
   {
      REPORT.refused = String( error.message || error );
   }
   REPORT.launcher_calls_before_detection = File.exists( CFG.calls ) ? File.readLines( CFG.calls ).length : 0;
   REPORT.places = aelBridgeWindowsPlaces();
   REPORT.found = aelBridgeWindowsPythons( REPORT.places );
   REPORT.environment = aelBridgeEnvironment( CFG.root );
   Settings.remove( AEL_BRIDGE_SETTINGS_KEY + "pythonPath" );
   REPORT.ok = true;
}
catch ( error )
{
   REPORT.ok = false;
   REPORT.error = String( error );
}
File.writeTextFile( CFG.report, JSON.stringify( REPORT, null, 1 ) );
'''

SWITCH = """   let windows = false;
#ifeq __PI_PLATFORM__ MSWINDOWS
   windows = true;
#endif
"""


def forced_copy(plugin: Path, target: Path) -> Path:
    """The connector as PixInsight reads it on Windows: aelBridgeOnWindows() answers yes and the lines between
    ``#ifeq __PI_PLATFORM__ MACOSX`` and ``#endif`` are left out. Everything else is the file as it is."""
    shutil.copytree(plugin, target, ignore=shutil.ignore_patterns("tests", "runtime", "__pycache__", "demo", ".DS_Store"))
    core = target / "AELBridgeCore.jsh"
    text = core.read_text(encoding="utf-8")
    if text.count(SWITCH) != 1:
        raise SystemExit("aelBridgeOnWindows() is not written as this test expects")
    text = text.replace(SWITCH, "   let windows = true;\n")
    if "#ifeq __PI_PLATFORM__ MACOSX" not in text:
        raise SystemExit("the lines for macOS are not written as this test expects")
    core.write_text(text.replace("#ifeq __PI_PLATFORM__ MACOSX", "#ifeq __PI_PLATFORM__ NOT_THIS_SYSTEM"),
                    encoding="utf-8")
    return core


def as_windows(pixinsight: Path, core: Path, work: Path, name: str, root: Path, variables: dict) -> dict:
    # the made-up disk is beside the work folder's scripts: its launcher notes its calls in disk/launcher_calls.txt
    """One PixInsight instance that takes itself for Windows, with the environment of the made-up computer."""
    config, script, report = work / f"{name}.json", work / f"{name}.js", work / f"{name}_report.json"
    config.write_text(json.dumps({"root": str(root), "report": str(report),
                                  "calls": str(work / "disk/launcher_calls.txt")}), encoding="utf-8")
    script.write_text("#engine v8\n" f"#include {json.dumps(str(core))}\n"
                      f"var CFG = JSON.parse(File.readTextFile({json.dumps(str(config))}));\n" + FORCED_BODY,
                      encoding="utf-8")
    windows_only = ("AEL_PYTHON", "USERPROFILE", "LOCALAPPDATA", "ProgramFiles", "ProgramFiles(x86)", "ProgramW6432",
                    "ProgramData", "SystemRoot", "SystemDrive", "APPDATA", "TEMP")
    environment = {key: value for key, value in os.environ.items() if key not in windows_only}
    environment.update(variables)
    completed = subprocess.run([str(pixinsight), "-n", "--automation-mode", f"-r={script}", "--force-exit"],
                               text=True, capture_output=True, timeout=600, check=False, env=environment)
    (work / f"{name}_log.txt").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    if not report.is_file():
        raise SystemExit(f"PixInsight wrote no report for {name} (exit {completed.returncode})")
    got = json.loads(report.read_text(encoding="utf-8"))
    if not got.get("ok"):
        raise SystemExit(f"The script {name} failed in PixInsight: " + str(got.get("error")))
    return got


def back(path) -> str:
    return str(path).replace("/", "\\")


def executable(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


def build_disk(disk: Path, python: str) -> None:
    """A made-up Windows disk. Empty files stand for the Pythons that are only listed; two scripts really run."""
    home, local = disk / "Home/u", disk / "Home/u/AppData/Local"
    for folder in (local / "Programs/Python/Python39", local / "Programs/Python/Python313",
                   local / "Programs/Python/Python310", local / "Python/pythoncore-3.14-64",
                   disk / "Program Files/Python312", disk / "Program Files (x86)/Python38-32",
                   disk / "Python311", disk / "Python27", home / "miniconda3", disk / "ProgramData/anaconda3",
                   home / ".venvs/b/Scripts", home / ".venvs/a/Scripts", home / ".venv/Scripts"):
        folder.mkdir(parents=True)
        (folder / "python.exe").write_bytes(b"")
    for name in ("python.exe", "python3.exe"):
        (local / "Microsoft/WindowsApps").mkdir(parents=True, exist_ok=True)
        (local / "Microsoft/WindowsApps" / name).write_bytes(b"")
    (local / "Programs/Python/Python313/not-python.txt").write_bytes(b"")
    # py.exe answers as the launcher does when it is asked which Python it starts: by default the one in tools (the
    # one that works), for -3 another one, and for its list (-0p) nothing this system could read. It notes each call.
    executable(disk / "Windows/py.exe",
               f'#!/bin/sh\necho "$1" >> "{disk}/launcher_calls.txt"\n'
               f'case "$1" in\n -3) echo "{disk}/Python311/python.exe";;\n -c) echo "{disk}/tools/python.exe";;\n'
               f' *) exit 2;;\nesac\n')
    # a python.exe in PATH that works
    executable(disk / "tools/python.exe", f'#!/bin/sh\nexec "{python}" "$@"\n')


def main() -> None:
    parser = argparse.ArgumentParser()
    repo = Path(__file__).resolve().parents[3]
    parser.add_argument("--pixinsight", type=Path,
                        default=Path("/Applications/PixInsight/PixInsight.app/Contents/MacOS/PixInsight"))
    parser.add_argument("--plugin", type=Path, default=Path(__file__).resolve().parents[1],
                        help="the connector's folder (a built package, or this checkout)")
    parser.add_argument("--root", type=Path, default=repo, help="the folder that holds the ael package")
    parser.add_argument("--output", type=Path, help="keep the report, the script and the log here")
    args = parser.parse_args()
    if os.name == "nt":
        raise SystemExit("This test stands in for Windows on another system. On Windows, run the connector itself.")

    work = Path(tempfile.mkdtemp(prefix="ael-windows-search-")).resolve()
    try:
        disk = work / "disk"
        build_disk(disk, sys.executable)
        config, script, report, log = work / "config.json", work / "windows_search.js", work / "report.json", work / "log.txt"
        config.write_text(json.dumps({"disk": str(disk), "root": str(args.root.resolve()), "report": str(report)}),
                          encoding="utf-8")
        script.write_text("#engine v8\n"
                          f"#include {json.dumps(str(args.plugin.resolve() / 'AELBridgeCore.jsh'))}\n"
                          f"var CFG = JSON.parse(File.readTextFile({json.dumps(str(config))}));\n" + BODY,
                          encoding="utf-8")
        environment = {key: value for key, value in os.environ.items() if key != "AEL_PYTHON"}
        command = [str(args.pixinsight), "-n", "--automation-mode", f"-r={script}", "--force-exit"]
        completed = subprocess.run(command, text=True, capture_output=True, timeout=600, check=False, env=environment)
        log.write_text(completed.stdout + completed.stderr, encoding="utf-8")
        if not report.is_file():
            raise SystemExit(f"PixInsight wrote no report (exit {completed.returncode}). Log:\n{log.read_text()[-3000:]}")
        got = json.loads(report.read_text(encoding="utf-8"))
        if not got.get("ok"):
            raise SystemExit("The script failed in PixInsight: " + str(got.get("error")))

        home, local = f"{disk}/Home/u", f"{disk}/Home/u/AppData/Local"
        works, other = f"{disk}/tools/python.exe", f"{disk}/Python311/python.exe"
        in_path = f"{disk}/Program Files/Python312/python.exe"
        installers = [f"{local}/Programs/Python/Python313/python.exe",            # newest first
                      f"{local}/Programs/Python/Python310/python.exe",
                      f"{local}/Programs/Python/Python39/python.exe",
                      f"{local}/Python/pythoncore-3.14-64/python.exe"]
        other_installers = [f"{disk}/Program Files (x86)/Python38-32/python.exe"]
        rest = [f"{home}/miniconda3/python.exe", f"{disk}/ProgramData/anaconda3/python.exe",                # conda
                f"{home}/.venvs/a/Scripts/python.exe", f"{home}/.venvs/b/Scripts/python.exe",                 # environments
                f"{home}/.venv/Scripts/python.exe"]
        aliases = [f"{local}/Microsoft/WindowsApps/python.exe", f"{local}/Microsoft/WindowsApps/python3.exe"]  # last
        # the launcher's default and its Python 3 first; tools is also in PATH (its "\" at the end removed) and comes
        # once; the folder of PATH between quotes next; then the installers, conda, the environments and the aliases
        expected = [works, other, in_path] + installers + other_installers + rest + aliases
        calls = disk / "launcher_calls.txt"
        # the whole search as on Windows: the computer above, then a computer without any Python
        core = forced_copy(args.plugin.resolve(), work / "forced")
        computer = {"USERPROFILE": back(disk / "Home/u"), "LOCALAPPDATA": back(local),
                    "ProgramFiles": back(disk / "Program Files"), "ProgramFiles(x86)": back(disk / "Program Files (x86)"),
                    "ProgramData": back(disk / "ProgramData"), "SystemRoot": back(disk / "Windows"),
                    "SystemDrive": back(disk), "APPDATA": back(disk / "Home/u/AppData/Roaming"),
                    "PATH": ";".join([back(disk / "tools") + "\\", back(Path(local) / "Microsoft/WindowsApps")])}
        launched = as_windows(args.pixinsight, core, work, "launcher", args.root.resolve(), computer)
        calls.unlink()
        named = as_windows(args.pixinsight, core, work, "named", args.root.resolve(), dict(computer, AEL_PYTHON=back(works)))
        chosen = as_windows(args.pixinsight, core, work, "chosen", args.root.resolve(),
                            dict(computer, AEL_PYTHON='"' + back(disk / "Program Files/Python312/python.exe") + '"',
                                 SystemRoot=back(disk / "none")))
        (disk / "bare").mkdir()
        bare = {name: back(disk / "bare") for name in ("USERPROFILE", "LOCALAPPDATA", "ProgramFiles", "ProgramData",
                                                         "SystemRoot", "SystemDrive")}
        nothing = as_windows(args.pixinsight, core, work, "nothing", args.root.resolve(), dict(bare, PATH=""))
        stubs = as_windows(args.pixinsight, core, work, "stubs", args.root.resolve(),
                           dict(bare, LOCALAPPDATA=back(local), PATH=""))
        handed = dict(item.split("=", 1) for item in launched["environment"])
        environment_given = dict(item.split("=", 1) for item in got["environment"])
        answer = (got["probeWindowsEnvironment"].get("answer") or {})
        checks = {
            "the search finds every Python of the made-up disk, in order, each once": got["found"] == expected,
            "Python 2 is not offered": not any("Python27" in path for path in got["found"]),
            "the launcher is asked: its default Python first, then its Python 3": got["launcher"] == [works, other],
            "the launcher's list of Pythons is read, each once, with /": got["listed"] == [
                "C:/Home/u/AppData/Local/Programs/Python/Python313/python.exe", "D:/My Tools/Python/python.exe"],
            "nothing is found where there is nothing, without an error": got["empty"] == [],
            "this system is not taken for Windows": got["onWindows"] is (os.name == "nt"),
            "the paths of Windows in an answer from Python get /": got["paths"] == {
                "a": "C:/x/y z.tif", "b": ["//server/share/f.tif", "keep \\ this"], "n": 3,
                "c": {"d": "D:/e", "e": "C:/already/right", "f": None}},
            "a path gets / between its folders": got["slashes"] == "C:/a/b/c",
            "a Python on Windows is told to use UTF-8": environment_given.get("PYTHONUTF8") == "1"
                                                        and environment_given.get("PYTHONIOENCODING") == "utf-8",
            "it is handed the variables that are set (PATH here), and no empty one":
                environment_given.get("PATH") == os.environ.get("PATH") and all(environment_given.values()),
            "the advice for Windows names py and the Command Prompt, not python3":
                "py -m pip install" in got["adviceNothing"] and "Command Prompt" in got["adviceNothing"]
                and "python3 -m pip" not in got["adviceNothing"] and "No python.exe was found" in got["adviceNothing"],
            "the advice lists what was tried": got["adviceTried"].rstrip().endswith("No module named 'numpy'")
                                               and "Tried:" in got["adviceTried"],
            "the probe runs through a file named python.exe": got["probe"]["ok"] is True
                                                              and got["probe"]["python"] == f"{disk}/tools/python.exe",
            "the probe passes with what is handed to a Python on Windows":
                got["probeWindowsEnvironment"]["ok"] is True and answer.get("ok") is True
                and answer.get("ael_version") == got["probe"]["ael_version"],
            "that Python reads and writes UTF-8": got["utf8"].split()[:2] == ["1", "utf-8"],
            "a Python that is not there is refused by name": got["missing"] == "Python executable not found: "
                                                             + f"{disk}/missing/python.exe",
            "the search of this system still finds a Python by itself": bool(got["here"]["python"])
                and Path(got["here"]["python"]).is_file() and got["here"]["ael_version"] == got["probe"]["ael_version"],
            "as Windows: the folders come from the environment, with /": launched["onWindows"] is True
                and launched["places"]["home"] == home and launched["places"]["local"] == local
                and launched["places"]["system"] == f"{disk}/Windows" and launched["places"]["drive"] == str(disk)
                and launched["places"]["programs"] == [f"{disk}/Program Files", f"{disk}/Program Files (x86)"],
            "as Windows: the same Pythons are found, in the same order": launched["found"] ==
                [works, other] + installers + [in_path] + other_installers + rest + aliases,
            "as Windows: with nothing chosen, the launcher's default Python is found and used":
                launched.get("detected", {}).get("python") == works
                and launched["detected"]["ael_version"] == got["probe"]["ael_version"]
                and launched["detected"]["tried_before"] == [] and launched["launcher_calls_before_detection"] > 0,
            "as Windows: the Python gets PYTHONPATH, UTF-8 and the user's folders":
                handed.get("PYTHONPATH") == str(args.root.resolve()) and handed.get("PYTHONUTF8") == "1"
                and handed.get("APPDATA") == computer["APPDATA"] and handed.get("USERPROFILE") == computer["USERPROFILE"]
                and handed.get("LOCALAPPDATA") == computer["LOCALAPPDATA"] and handed.get("PATH") == computer["PATH"],
            "as Windows: AEL_PYTHON written with \\ and quotes is the first one tried":
                (chosen.get("refused") or "").split("Tried:\n")[-1].startswith(f"{disk}/Program Files/Python312/python.exe: ")
                or (chosen.get("detected", {}).get("tried_before") or [""])[0].startswith(
                    f"{disk}/Program Files/Python312/python.exe: "),
            "as Windows: a Python that does not start is passed over and the next one is used":
                chosen.get("detected", {}).get("python") == works,
            "as Windows: a Python named in AEL_PYTHON that serves is used without asking the launcher first":
                named.get("detected", {}).get("python") == works and named["detected"]["tried_before"] == []
                and named["launcher_calls_before_detection"] == 0,
            "as Windows: without any Python, the message says what to do on Windows and that none was found":
                "py -m pip install" in nothing.get("refused", "") and "No python.exe was found" in nothing["refused"]
                and "python3 -m pip" not in nothing["refused"] and nothing["found"] == [],
            "as Windows: Pythons that do not start (the Store's aliases among them) are each named in the message":
                stubs["found"] == installers + aliases and "detected" not in stubs
                and all(path + ": " in stubs.get("refused", "") for path in stubs["found"])
                and "py -m pip install" in stubs.get("refused", ""),
        }
        result = {"credit": CREDIT, "pixinsight": str(args.pixinsight), "plugin": str(args.plugin.resolve()),
                  "ael_version": got["probe"]["ael_version"], "checks": checks, "passed": sum(checks.values()),
                  "total": len(checks), "ok": all(checks.values()), "report": got, "expected_order": expected,
                  "as_windows": {"launcher": launched, "named": named, "chosen": chosen, "nothing": nothing,
                                 "stubs": stubs},
                  "limit": "Run on a made-up Windows disk on another system: Windows itself is not exercised."}
        if args.output:
            args.output.mkdir(parents=True, exist_ok=True)
            (args.output / "windows_search.json").write_text(json.dumps(result, indent=1, ensure_ascii=False),
                                                             encoding="utf-8")
            shutil.copy2(script, args.output / script.name)
            shutil.copy2(log, args.output / "pixinsight_log.txt")
        for name, passed in checks.items():
            print(("PASS  " if passed else "FAIL  ") + name)
        print(f"{result['passed']}/{result['total']}")
        if not result["ok"]:
            print("The reports are in windows_search.json (--output FOLDER).")
            raise SystemExit(1)
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
