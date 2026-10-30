#!/usr/bin/env python3
"""Minimal JSX/runtime probe; writes a marker before and after Python starts."""
import argparse
import json
from pathlib import Path
import subprocess

from run_tests import do_javascript, photoshop_running


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--python", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    report_path = args.output / "JSX_PROBE.json"
    core = args.repo / "plugins/photoshop-ael/AELPhotoshopCore.jsx"
    dialog = args.repo / "plugins/photoshop-ael/AELPhotoshopDialog.jsx"
    report = {"photoshop_was_running": photoshop_running()}
    code = f'''#include {json.dumps(str(core))}
#include {json.dumps(str(dialog))}
var R={{stage:"include_ok",dialog_type:typeof AELPhotoshopDialog}};
AELPhotoshop.writeJSON(new File({json.dumps(str(report_path))}),R);
try {{
  var P=AELPhotoshop.probe({json.dumps(args.python)},{json.dumps(str(args.repo))});
  R.stage="probe_ok"; R.runtime=P.runtime;
}} catch(e) {{ R.stage="probe_error"; R.error=String(e.message); }}
AELPhotoshop.writeJSON(new File({json.dumps(str(report_path))}),R);
R.stage;'''
    completed = do_javascript(code, timeout=60)
    report.update(returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)
    if report_path.exists():
        report["jsx"] = json.loads(report_path.read_text())
    if not report["photoshop_was_running"]:
        subprocess.run(["osascript", "-e", 'tell application id "com.adobe.Photoshop" to quit'],
                       capture_output=True, timeout=20, check=False)
    (args.output / "JSX_PROBE_PROCESS.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    if completed.returncode or report.get("jsx", {}).get("stage") != "probe_ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
