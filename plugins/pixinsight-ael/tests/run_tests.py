#!/usr/bin/env python3
"""Detect a suitable Python and run the PixInsight bridge validation.

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

CREDIT = ("Processed with Agentic Eclipse Library by Pere Guerra — "
          "https://github.com/PeterWar/Agentic-Eclipse-Library")


def candidates() -> list[str]:
    values = [os.environ.get("AEL_PYTHON", ""), sys.executable,
              "/opt/homebrew/bin/python3", "/usr/local/bin/python3",
              str(Path.home() / ".pyenv/shims/python"),
              str(Path.home() / ".venvs/eines-ia-py312/bin/python"),
              str(Path.home() / "miniconda3/bin/python"),
              str(Path.home() / "miniforge3/bin/python")]
    return list(dict.fromkeys(value for value in values if value and Path(value).is_file()))


def detect(repo: Path) -> tuple[str, dict]:
    helper = repo / "plugins/pixinsight-ael/python/ael_bridge_check.py"
    errors = []
    for python in candidates():
        env = dict(os.environ, PYTHONPATH=str(repo), PYTHONDONTWRITEBYTECODE="1")
        try:
            run = subprocess.run([python, str(helper), "probe"], text=True, capture_output=True,
                                 env=env, timeout=20, check=False)
            info = json.loads(run.stdout[run.stdout.find("{"):run.stdout.rfind("}") + 1])
        except Exception as exc:
            errors.append(f"{python}: {exc}")
            continue
        if info.get("ok"):
            info["detection_errors"] = errors
            return python, info
        errors.append(f"{python}: {info.get('message')}")
    raise SystemExit("No Python 3.10+ with AEL and its dependencies found. "
                     "Set AEL_PYTHON or install AEL. " + " | ".join(errors))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, help="copy the JSON receipt, logs and screenshots here")
    parser.add_argument("--pixinsight", type=Path,
                        default=Path("/Applications/PixInsight/PixInsight.app/Contents/MacOS/PixInsight"))
    parser.add_argument("--skip-pixinsight", action="store_true", help="run only direct AEL checks (not a full validation)")
    parser.add_argument("--skip-captures", action="store_true")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[3]
    python, runtime = detect(repo)
    command = [python, str(Path(__file__).with_name("validate.py")), "--repo", str(repo),
               "--python", python, "--pixinsight", str(args.pixinsight)]
    if args.skip_pixinsight:
        command.append("--skip-pixinsight")
    if args.skip_captures:
        command.append("--skip-captures")
    env = dict(os.environ, PYTHONPATH=str(repo), PYTHONDONTWRITEBYTECODE="1")
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        env["AEL_VALIDATION_OUTPUT"] = str(args.output.resolve())
    env["AEL_VALIDATION_RUNTIME"] = json.dumps(runtime)
    completed = subprocess.run(command, env=env, check=False)
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
