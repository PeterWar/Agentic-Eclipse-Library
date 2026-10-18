"""Refresh the documented runtime snapshot, verify it, and create a deterministic plugin ZIP."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile

REPO = Path(__file__).resolve().parents[1]
PLUGIN = REPO / "plugins" / "codex-ael"
DOCS = ("DEVELOP.md", "FIELD_LESSONS.md", "PAPER_AND_LIBRARY.md", "EXISTING_EDIT_CASE_STUDY.md",
        "VALIDATION_1.3.2.md")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():
    pairs = [(p, PLUGIN / "runtime" / p.relative_to(REPO)) for p in sorted((REPO / "ael").rglob("*.py"))]
    pairs += [(REPO / n, PLUGIN / "runtime" / n) for n in ("pyproject.toml", "README_AEL.md", "LICENSE")]
    pairs += [(REPO / "docs" / n, PLUGIN / "docs" / n) for n in DOCS]
    pairs += [(p, PLUGIN / "examples" / p.name) for p in sorted((REPO / "examples").glob("*.json"))]
    pairs += [(REPO / "README_AEL.md", PLUGIN / "docs" / "README_AEL.md"),
              (REPO / "LICENSE", PLUGIN / "LICENSE"),
              (REPO / ".claude-plugin" / "icon.png", PLUGIN / "assets" / "icon.png")]
    # Keep the case-workflow skill canonical at the source root and mirror it for Codex.
    astro = Path("skills") / "eclipse-astrophotography"
    pairs += [(REPO / astro / n, PLUGIN / astro / n) for n in (
        "SKILL.md", "agents/openai.yaml", "references/acquisition-and-authority.md",
        "references/examples-and-receipts.md")]
    return pairs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sync", action="store_true", help="copy current canonical runtime and reference files")
    p.add_argument("--out", type=Path, required=True, help="new ZIP path; never overwritten")
    args = p.parse_args()
    if args.out.exists():
        p.error("ZIP already exists; choose a new name")
    pairs = sources()
    for src, dst in pairs:
        if args.sync:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        if not dst.is_file() or digest(src) != digest(dst):
            raise SystemExit(f"Bundled snapshot differs from maintained source: {dst.relative_to(REPO)}")
    expected = {dst for src, dst in pairs if dst.is_relative_to(PLUGIN / "runtime")}
    found = {x for x in (PLUGIN / "runtime").rglob("*") if x.is_file() and "__pycache__" not in x.parts}
    if expected != found:
        raise SystemExit("Unexpected/missing runtime files; inspect the runtime snapshot before packaging")
    files = sorted(x for x in PLUGIN.rglob("*") if x.is_file() and "__pycache__" not in x.parts
                   and x.name != "BUNDLE_CONTENTS.json" and x.suffix != ".pyc")
    for f in files:
        if f.is_symlink() or ".git" in f.parts or f.name == ".DS_Store":
            raise SystemExit(f"Unsupported package entry: {f.relative_to(PLUGIN)}")
    manifest = json.loads((PLUGIN / "plugin.json").read_text())
    ui = manifest["extensions"]["com.openai"]["interface"]
    for field, limit in (("displayName", 30), ("shortDescription", 30), ("longDescription", 4000)):
        if not ui[field] or len(ui[field]) > limit:
            raise SystemExit(f"Listing field exceeds its limit: {field}")
    for field in ("composerIcon", "logo"):
        if not (PLUGIN / ui[field]).is_file():
            raise SystemExit(f"Missing icon: {field}")
    for skill in (PLUGIN / "skills").iterdir():
        if not (skill / "SKILL.md").is_file():
            raise SystemExit(f"Missing skill entrypoint: {skill.name}")
    receipt = {"plugin_version": manifest["version"],
               "runtime_source_commit": subprocess.check_output(["git", "log", "-1", "--format=%H", "--", "ael", "pyproject.toml"], cwd=REPO, text=True).strip(),
               "runtime_snapshot_matches_source": True,
               "files": {f.relative_to(PLUGIN).as_posix(): digest(f) for f in files}}
    index = PLUGIN / "BUNDLE_CONTENTS.json"
    index.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.out, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in sorted(files + [index]):
            info = zipfile.ZipInfo("agentic-eclipse-library/" + str(f.relative_to(PLUGIN)), (2026, 10, 16, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, f.read_bytes())
    print(json.dumps({"zip": str(args.out), "sha256": digest(args.out), "files": len(files) + 1,
                      "bytes": args.out.stat().st_size, "runtime_snapshot_matches_source": True}, indent=2))


if __name__ == "__main__":
    main()
