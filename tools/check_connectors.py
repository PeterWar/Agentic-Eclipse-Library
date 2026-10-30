"""Check that the PixInsight and Photoshop connectors stay in step, without running either program.

plugins/pixinsight-ael/ and plugins/photoshop-ael/ are self-contained, so each carries its own copy of the
shared parts. This script fails when those copies drift apart:

- python/ael_workflow.py and tools/build_package.py are the same file once the program names are set aside
  (and, for the builder, its list of files);
- both dialogs show the same experimental notice about the linear master;
- both probes refuse an AEL older than the same version;
- neither connector names a private interpreter or a home folder.

    python tools/check_connectors.py        # exit 1 and list the differences if they drift
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI, PS = REPO / "plugins/pixinsight-ael", REPO / "plugins/photoshop-ael"
NOTICE = ("The linear master registers every frame on the Sun, and on real eclipse frames that registration is not "
          "valid yet: it lands 0.07-2.2 px from the reference registration. Do not use it on real frames.")
PRIVATE = re.compile(r"/Users/|eines-ia|\.venvs/[A-Za-z0-9_-]+/bin")


def neutral(text: str) -> str:
    """The program names and plugin folders replaced by one placeholder."""
    for name in ("PixInsight", "Photoshop", "pixinsight-ael", "photoshop-ael"):
        text = text.replace(name, "<PROGRAM>")
    return text


def without_file_list(text: str) -> str:
    return re.sub(r"FILES = \[.*?\]\n", "FILES = [...]\n", text, flags=re.S)


def literal_text(path: Path) -> str:
    """The string literals of a script joined, without markup: what the dialog shows."""
    source = path.read_text(encoding="utf-8")
    pieces = re.findall(r'"((?:[^"\\]|\\.)*)"', source)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", "".join(pieces)))


def minimum(path: Path) -> str:
    found = re.search(r"^MINIMUM_AEL = (\(.*?\))", path.read_text(encoding="utf-8"), flags=re.M)
    return found.group(1) if found else "none"


def main() -> None:
    checks = {}
    for relative, normalise in (("python/ael_workflow.py", neutral),
                                ("tools/build_package.py", lambda t: without_file_list(neutral(t)))):
        a, b = (normalise((root / relative).read_text(encoding="utf-8")) for root in (PI, PS))
        checks[f"{relative} is the same in both"] = a == b
    checks["same experimental notice in both dialogs"] = all(
        NOTICE in literal_text(path) for path in (PI / "AELWorkflowDialog.jsh", PS / "AELPhotoshopDialog.jsx"))
    floors = (minimum(PI / "python/ael_bridge_check.py"), minimum(PS / "python/ael_photoshop.py"))
    checks[f"same AEL floor in both probes {floors}"] = floors[0] == floors[1] != "none"
    private = sorted(str(p.relative_to(REPO)) for root in (PI, PS) for p in root.rglob("*")
                     if p.is_file() and p.suffix in {".py", ".js", ".jsh", ".jsx", ".md", ".json"}
                     and PRIVATE.search(p.read_text(encoding="utf-8", errors="ignore")))
    checks["no private interpreter or home folder" + (f": {private}" if private else "")] = not private
    print(json.dumps(checks, indent=1, ensure_ascii=False))
    if not all(checks.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
