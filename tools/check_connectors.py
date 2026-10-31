"""Check that the PixInsight and Photoshop connectors stay in step, without running either program.

plugins/pixinsight-ael/ and plugins/photoshop-ael/ are self-contained, so each carries its own copy of the
shared parts. This script fails when those copies drift apart:

- python/ael_auto.py, the RAW-to-layered-image engine, is the same file in both: the same photos give the same
  linear master and the same filter layers in either program;
- python/ael_workflow.py, tools/make_demo.py and tools/build_package.py are the same file once the program
  names are set aside (and, for the builder, its list of files), so both packages carry the same demonstration;
- both dialogs ask for the same three things, the totality RAW photos, the optional darks and the optional flats, and offer
  the same output folder line ("Output folder" with "Browse…");
- both offer the same advanced settings, with the same list of AEL's filters (names, layer names, blend modes, default
  opacities and the words that say what each shows), and the same invitation to the whole library with its GitHub
  address;
- both show the same licence line, and on its tip the disclaimer of the LICENSE file, which is the same in both;
- both probes refuse an AEL older than the same version: each probe runs against stand-in `ael` packages that
  carry only a version (1.3.3 and an unreadable one) and must refuse both, and the floor they print must match;
- neither connector names a private interpreter or a home folder.

    python tools/check_connectors.py        # exit 1 and list the differences if they drift
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI, PS = REPO / "plugins/pixinsight-ael", REPO / "plugins/photoshop-ael"
INPUTS = ("Totality RAW photos", "Darks (optional)", "Flats (optional)")
OUTPUT = ("Output folder", "Browse…")
MORE = ("Advanced settings…", "AEL defaults", "All 16", "GitHub", "https://github.com/PeterWar/Agentic-Eclipse-Library",
        "For more faithful results and more filters, try the whole library with an AI agent:",
        "For more faithful results and more filters, try the whole Agentic Eclipse Library with an AI agent:")
LICENCE_LINE = "MIT License · Copyright © 2026 Pere Guerra Serra · Provided “as is”, without warranty of any kind."
# where each connector keeps its dialog and its list of filters
WORDS = {"PixInsight": (PI / "AELBridgeDialog.jsh", PI / "AELWorkflowCore.jsh"),
         "Photoshop": (PS / "AELPhotoshopDialog.jsx", PS / "AELPhotoshopCore.jsx")}
PRIVATE = re.compile(r"/Users/|eines-ia|\.venvs/[A-Za-z0-9_-]+/bin")


def neutral(text: str) -> str:
    """The program names and plugin folders replaced by one placeholder."""
    for name in ("PixInsight", "Photoshop", "pixinsight-ael", "photoshop-ael"):
        text = text.replace(name, "<PROGRAM>")
    return text


def without_file_list(text: str) -> str:
    return re.sub(r"FILES = \[.*?\]\n", "FILES = [...]\n", text, flags=re.S)


def literal_text(path: Path) -> str:
    """The string literals of a script joined, without markup and with \\u and \\" escapes read: what the dialog shows."""
    source = path.read_text(encoding="utf-8")
    pieces = re.findall(r'"((?:[^"\\]|\\.)*)"', source)
    text = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), "".join(pieces)).replace('\\"', '"')
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", text))


def disclaimer(path: Path) -> str:
    """The disclaimer of a LICENSE file, on one line."""
    text = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
    return text[text.index("THE SOFTWARE IS PROVIDED"):].strip()


def filter_list(path: Path) -> list:
    """The connector's list of AEL's filters: name, layer name, blend mode, default opacity and what it shows."""
    found = re.findall(r'\{\s*name: "(\w+)", label: "([^"]+)", mode: "(\w+)", opacity: ([0-9.]+),\s*about: (.*?)\s*\}',
                       path.read_text(encoding="utf-8"), flags=re.S)
    return [(name, label, mode, float(opacity), "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', about)))
            for name, label, mode, opacity, about in found]


def minimum(path: Path) -> str:
    found = re.search(r"^MINIMUM_AEL = (\(.*?\))", path.read_text(encoding="utf-8"), flags=re.M)
    return found.group(1) if found else "none"


def probe(connector: str, stub: Path) -> dict:
    """The connector's own probe, run with a stand-in ael first on the path (and as the working folder)."""
    if connector == "pixinsight":
        command = [sys.executable, str(PI / "python/ael_bridge_check.py"), "probe"]
    else:
        command = [sys.executable, "-c", "import json, sys; sys.path.insert(0, sys.argv[1]); import ael_photoshop; "
                   "print(json.dumps(ael_photoshop.execute({'operation': 'probe'})))", str(PS / "python")]
    completed = subprocess.run(command, capture_output=True, text=True, cwd=stub, timeout=120,
                               env={"PYTHONPATH": str(stub), "PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"})
    try:
        return json.loads(completed.stdout.strip().splitlines()[-1])
    except Exception:
        return {"ok": None, "kind": "no answer", "message": completed.stderr[-300:]}


def refusals() -> dict:
    """What each probe answers for AEL 1.3.3 and for an AEL whose version cannot be read."""
    answers = {}
    with tempfile.TemporaryDirectory(prefix="ael-check-connectors-") as folder:
        for version in ("1.3.3", "dev"):
            stub = Path(folder) / version
            (stub / "ael").mkdir(parents=True)
            (stub / "ael" / "__init__.py").write_text(f"__version__ = {version!r}\n", encoding="utf-8")
            for connector in ("pixinsight", "photoshop"):
                answer = probe(connector, stub)
                answers[f"{connector} {version}"] = (answer.get("kind"), answer.get("message") or "")
    return answers


def main() -> None:
    checks = {}
    for relative, normalise in (("python/ael_workflow.py", neutral), ("tools/make_demo.py", neutral),
                                ("tools/build_package.py", lambda t: without_file_list(neutral(t)))):
        a, b = (normalise((root / relative).read_text(encoding="utf-8")) for root in (PI, PS))
        checks[f"{relative} is the same in both"] = a == b
    checks["python/ael_auto.py is identical in both"] = (
        (PI / "python/ael_auto.py").read_bytes() == (PS / "python/ael_auto.py").read_bytes())
    checks[f"both dialogs ask for {' and '.join(INPUTS)}"] = all(
        label in literal_text(path) for label in INPUTS for path in (PI / "AELBridgeDialog.jsh", PS / "AELPhotoshopDialog.jsx"))
    checks[f"both dialogs offer {' with '.join(OUTPUT)}"] = all(
        label in literal_text(path) for label in OUTPUT for path in (PI / "AELBridgeDialog.jsh", PS / "AELPhotoshopDialog.jsx"))
    texts = {program: " ".join(literal_text(path) for path in paths) for program, paths in WORDS.items()}
    checks["both offer the advanced settings and the invitation to the library with its GitHub address"] = all(
        words in text for words in MORE for text in texts.values())
    licences = [disclaimer(root / "LICENSE") for root in (PI, PS)]
    checks["both show the MIT licence line and the disclaimer of their LICENSE, the same in both"] = (
        licences[0] == licences[1] and all(LICENCE_LINE in text and licences[0] in text for text in texts.values()))
    lists = {program: filter_list(paths[1]) for program, paths in WORDS.items()}
    checks[f"both list the same {len(lists['PixInsight'])} filters with the same words"] = (
        lists["PixInsight"] == lists["Photoshop"] and len(lists["PixInsight"]) == 16)
    floors = (minimum(PI / "python/ael_bridge_check.py"), minimum(PS / "python/ael_photoshop.py"))
    checks[f"same AEL floor in both probes {floors}"] = floors[0] == floors[1] != "none"
    answers = refusals()
    refused = {case: kind for case, (kind, message) in answers.items()}
    floor = ".".join(re.findall(r"\d+", floors[0]))
    checks[f"both probes refuse AEL 1.3.3 and an unreadable version {refused}"] = all(
        kind == "old_ael" and f"needs AEL {floor} or later" in message for kind, message in answers.values())
    private = sorted(str(p.relative_to(REPO)) for root in (PI, PS) for p in root.rglob("*")
                     if p.is_file() and p.suffix in {".py", ".js", ".jsh", ".jsx", ".md", ".json"}
                     and PRIVATE.search(p.read_text(encoding="utf-8", errors="ignore")))
    checks["no private interpreter or home folder" + (f": {private}" if private else "")] = not private
    print(json.dumps(checks, indent=1, ensure_ascii=False))
    if not all(checks.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
