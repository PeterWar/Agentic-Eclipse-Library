#!/usr/bin/env python3
"""Build a self-contained folder of the Photoshop connector: scripts, Python helpers, the AEL engine of this
checkout under runtime/ael, and the synthetic demonstration files. Then a deterministic ZIP of the whole folder.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library

    python plugins/photoshop-ael/tools/build_package.py --out /path/to/new/folder [--zip /path/to/folder.zip]
    python plugins/photoshop-ael/tools/build_package.py --pack /path/to/folder --zip /path/to/folder.zip

The folder has the same form as the one of the PixInsight connector: photoshop-ael/ (scripts, python/, runtime/ael and
runtime/VERSION.json) and demo/. Everything under runtime/ael is checked byte by byte against the checkout. A guide
(LLEGEIX-ME.md) is added to the folder by hand once the tests are done; --pack then makes the ZIP of the finished
folder, with the folder as its root: sorted names, fixed times and modes, no build date inside.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

PLUGIN = Path(__file__).resolve().parents[1]
REPO = PLUGIN.parents[1]
FILES = ["AELPhotoshop.jsx", "AELPhotoshopCore.jsx", "AELPhotoshopDialog.jsx", "README.md", "LICENSE",
         "python/ael_photoshop.py", "python/ael_workflow.py", "python/ael_auto.py"]
SKIP = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")


def git(*arguments: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *arguments], capture_output=True, text=True, check=False).stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def provenance() -> dict:
    """Where the package comes from, with the same keys in the PixInsight and Photoshop connectors: the last commit
    that changed ael/ or LICENSE, the commit of the checkout, and whether either part had uncommitted changes."""
    dirty = bool(git("status", "--porcelain", "--", "ael", "LICENSE", f"plugins/{PLUGIN.name}"))
    head = git("rev-parse", "--short", "HEAD") or "unknown"
    return {"ael_commit": git("log", "-1", "--format=%h", "--", "ael", "LICENSE") or "unknown",
            "connector_commit": head + ("+modified" if dirty else ""), "uncommitted_changes": dirty}


def write_zip(folder: Path, target: Path) -> str:
    """Deterministic: sorted names, fixed times and modes, no build date inside; the folder is the root of the ZIP."""
    if folder in target.resolve().parents:
        raise SystemExit("the ZIP cannot go inside the folder it packs")
    files = sorted(p for p in folder.rglob("*") if p.is_file() and p.name != ".DS_Store")
    with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            info = zipfile.ZipInfo(f"{folder.name}/{path.relative_to(folder).as_posix()}", (2026, 10, 30, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    return sha256(target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, help="build a new folder here")
    parser.add_argument("--pack", type=Path, help="make the ZIP of a folder that is already built (needs --zip)")
    parser.add_argument("--zip", type=Path, help="write a deterministic ZIP of the whole folder here")
    parser.add_argument("--no-demo", action="store_true")
    args = parser.parse_args()
    if args.zip and args.zip.exists():
        raise SystemExit(f"{args.zip} exists: choose a new file")
    if args.pack:
        if not args.zip:
            raise SystemExit("--pack needs --zip")
        print(json.dumps({"packed": str(args.pack.resolve()), "zip": str(args.zip),
                          "zip_sha256": write_zip(args.pack.resolve(), args.zip.resolve())}))
        return
    if not args.out:
        raise SystemExit("give --out (build) or --pack (make the ZIP of a built folder)")
    out = args.out.resolve()
    if out.exists():
        raise SystemExit(f"{out} exists: choose a new folder")
    sys.path.insert(0, str(REPO))
    import ael

    target = out / "photoshop-ael"
    for name in FILES:
        (target / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PLUGIN / name, target / name)
    shutil.copytree(REPO / "ael", target / "runtime" / "ael", ignore=SKIP)
    shutil.copy2(REPO / "LICENSE", target / "runtime" / "LICENSE")
    origin = provenance()
    (target / "runtime" / "VERSION.json").write_text(json.dumps({"ael_version": ael.__version__, **origin,
        "source": f"Agentic Eclipse Library, ael/ and plugins/{PLUGIN.name}/ of this checkout"}, indent=1),
        encoding="utf-8")

    # the copy must be the checkout's, byte by byte, and nothing else
    expected = {p.relative_to(REPO / "ael") for p in (REPO / "ael").rglob("*") if p.is_file()
                and "__pycache__" not in p.parts and p.suffix != ".pyc" and p.name != ".DS_Store"}
    found = {p.relative_to(target / "runtime" / "ael") for p in (target / "runtime" / "ael").rglob("*") if p.is_file()}
    if expected != found or any(sha256(REPO / "ael" / r) != sha256(target / "runtime" / "ael" / r) for r in expected):
        raise SystemExit("the runtime copy differs from the checkout's ael/: nothing was packaged")

    if not args.no_demo:
        subprocess.run([sys.executable, str(PLUGIN / "tools" / "make_demo.py"), "--out", str(out / "demo")], check=True,
                       env={**os.environ, "PYTHONPATH": str(REPO), "PYTHONDONTWRITEBYTECODE": "1"})
    zip_sha = write_zip(out, args.zip.resolve()) if args.zip else None
    print(json.dumps({"out": str(out), "ael_version": ael.__version__, **origin,
                      "runtime_files": len(expected), "zip": str(args.zip) if args.zip else None, "zip_sha256": zip_sha}))


if __name__ == "__main__":
    main()
