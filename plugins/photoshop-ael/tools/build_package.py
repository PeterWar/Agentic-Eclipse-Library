#!/usr/bin/env python3
"""Build a self-contained folder of the Photoshop bridge: scripts, Python runner, the AEL engine of this
checkout under runtime/ael, and the synthetic demonstration files.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

    python plugins/photoshop-ael/tools/build_package.py --out /path/to/new/folder
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

PLUGIN = Path(__file__).resolve().parents[1]
REPO = PLUGIN.parents[1]
FILES = ["AELPhotoshop.jsx", "AELPhotoshopCore.jsx", "AELPhotoshopDialog.jsx", "README.md", "LICENSE",
         "python/ael_photoshop.py", "python/ael_workflow.py"]
SKIP = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--no-demo", action="store_true")
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise SystemExit(f"{out} exists: choose a new folder")
    target = out / "photoshop-ael"
    for name in FILES:
        (target / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PLUGIN / name, target / name)
    shutil.copytree(REPO / "ael", target / "runtime" / "ael", ignore=SKIP)
    shutil.copy2(REPO / "LICENSE", target / "runtime" / "LICENSE")
    sys.path.insert(0, str(REPO))
    import ael

    def git(*words: str) -> str:
        return subprocess.run(["git", "-C", str(REPO), *words], capture_output=True, text=True,
                              check=False).stdout.strip()

    commit = git("rev-parse", "--short", "HEAD")
    (target / "runtime" / "VERSION.json").write_text(json.dumps({"ael_version": ael.__version__,
        "source_commit": commit, "ael_last_commit": git("log", "-1", "--format=%h", "--", "ael"),
        "uncommitted_changes": bool(git("status", "--porcelain", "--", "ael", "plugins/photoshop-ael")),
        "source": "Agentic Eclipse Library, ael/ and plugins/photoshop-ael/ of this checkout"}, indent=1),
        encoding="utf-8")
    if not args.no_demo:
        subprocess.run([sys.executable, str(PLUGIN / "tools" / "make_demo.py"), "--out", str(out / "demo")],
                       check=True, env={**__import__("os").environ, "PYTHONPATH": str(REPO),
                                        "PYTHONDONTWRITEBYTECODE": "1"})
    print(json.dumps({"out": str(out), "ael_version": ael.__version__, "source_commit": commit}))


if __name__ == "__main__":
    main()
