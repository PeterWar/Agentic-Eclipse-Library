"""Build the Claude plugin folder from the published Codex plugin, without touching it.

plugins/codex-ael/ is the host-neutral bundle (AEL runtime, seven short skills, docs, examples,
launcher) maintained by tools/build_codex_plugin_20261016.py. The Claude plugin directory needs
a `.claude-plugin/plugin.json`, an icon and a README written for Claude, and validates one small
folder; the whole repository is too large for it. This script copies the shared files into
plugins/claude-ael/ and writes the Claude-specific ones.

    python tools/build_claude_plugin.py          # rebuild plugins/claude-ael/
    python tools/build_claude_plugin.py --check  # exit 1 if it is out of step with codex-ael
"""
import filecmp
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "plugins" / "codex-ael"
DEST = REPO / "plugins" / "claude-ael"
SHARED = ["LICENSE", "docs", "examples", "runtime", "scripts", "skills", "assets/synthetic-workflow.png"]
SKIP = {".DS_Store", "__pycache__"}

MANIFEST = {
    "name": "agentic-eclipse-library",
    "version": "1.3.6",
    "description": ("Process total solar eclipse photos locally: calibrated HDR stacking, corona filter layers, "
                    "layered Photoshop files, polar views, motion analysis and coronagraph comparisons, with "
                    "measured inputs and explicit validation limits. Bundles the AEL 1.3.6 Python engine."),
    "author": {"name": "Pere Guerra Serra", "url": "https://github.com/PeterWar"},
    "homepage": "https://github.com/PeterWar/Agentic-Eclipse-Library",
    "repository": "https://github.com/PeterWar/Agentic-Eclipse-Library",
    "license": "MIT",
    "keywords": ["solar-eclipse", "astrophotography", "astronomy", "solar-corona", "hdr", "raw",
                 "image-processing", "photoshop", "photometry", "coronagraph", "polar", "scientific-imaging"],
}

README = """# Agentic Eclipse Library for Claude

Process total solar eclipse photographs with seven guided workflows: get started, calibrate and stack,
create corona filter layers, investigate artefacts, make polar views and motion analyses, compare
observations with coronagraphs, and take a whole case to an editable master the photographer accepts
(contributed by Raúl Hussein). Created by Pere Guerra Serra. MIT licensed.

This plugin bundles the AEL 1.3.6 Python processing engine, its known-truth tests, recipe templates and
practical documentation. It runs on your computer with Python 3.10 or later. Claude plans the work and
explains the results; AEL performs the numerical processing.

![A labelled synthetic demonstration of the workflow](assets/synthetic-workflow.png)

## Start

Install this plugin from Claude's plugin directory. (The repository's own marketplace installs the full
research edition instead: the same engine plus the original project's longer skills, mostly in Catalan.)
Then ask, in your language:

- Help me process my total solar eclipse photos while preserving the original files.
- Inspect the rings in my corona image and find which processing stage caused them.
- Show me a clearly labelled synthetic demonstration before I use my own photos.

Follow [setup and operating instructions](docs/USAGE.md). Installing the plugin does not install Python
or Python dependencies. The setup checks what is available before proposing a change.

## Outputs and limits

AEL can write linear stacks, validity and coverage maps, filter layers, 16-bit layered Photoshop files,
polar views, motion check sheets and animations. A photograph is not an absolute brightness measurement.
Calibration, registration, geometry and any spatial cloud correction require measured inputs; AEL does
not infer all of these from a folder of RAWs. Photoshop itself is optional.

Known limitations in 1.3.6 include bands near data boundaries in ACHF/WOW, some fine-detail sign inversion
in the worst sectors of the default edge-aware WOW, and rings of the plain WOW next to a lunar limb that the data reach. See [field lessons](docs/FIELD_LESSONS.md). Passing the bundled tests does
not validate a new astronomical observation. Missing data stays missing. Synthetic examples are labelled
and must never be used as pixels in an observed image.

## What this plugin runs, fetches and sends

- **Runs locally.** The skills run the bundled Python source through `scripts/run_ael.py`. It reads the
  files selected for the task and writes new output folders; it refuses to write into an existing one.
- **Fetches, only when needed.** Installing the Python dependencies uses pip, which normally downloads
  them from PyPI: NumPy, SciPy, OpenCV, Pillow, tifffile and imageio, plus rawpy and Astropy for RAW and
  FITS, and psd-tools for Photoshop files. The launcher itself never installs packages. Public coronagraph
  data (K-Cor from the Mauna Loa Solar Observatory, SOHO/LASCO from the Naval Research Laboratory, SDO/AIA
  from Stanford's JSOC) is downloaded only after you approve it, with its source, purpose and size stated
  first. Astropy may fetch Earth-orientation tables when network access is enabled.
- **Sends nothing.** No MCP server, no hooks, no telemetry, no paid model calls, no credential reader and
  no uploader. Claude's own data policy applies to what enters the conversation: filenames, prompts,
  previews and tool outputs. Publishing photographs, uploading data or contacting anyone requires your
  authorisation for that action.

The original project's research archive stays in the
[source repository](https://github.com/PeterWar/Agentic-Eclipse-Library); this plugin does not install it.

Support: [GitHub Issues](https://github.com/PeterWar/Agentic-Eclipse-Library/issues).
[Privacy policy](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/main/docs/CODEX_PLUGIN_PRIVACY.md)
(it covers this plugin too) and
[licence and terms](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/main/docs/CODEX_PLUGIN_TERMS.md).
Optional credit: Processed with Agentic Eclipse Library by Pere Guerra.
"""


def icon_bytes():
    """The Codex icon, 768 px, stored uncompressed (about 1.7 MB, under the 2 MB limit).

    The directory scans an icon's bytes for text. Compressed PNG data holds thousands of short
    printable runs by chance, and one of them was read as a download-and-run command; stored
    uncompressed, the same pixels leave no printable run longer than six characters.
    """
    import io
    from PIL import Image
    im = Image.open(SRC / "assets" / "icon.png").convert("RGB").resize((768, 768), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG", compress_level=0)
    return buf.getvalue()


def files(base):
    return sorted(p.relative_to(base) for p in base.rglob("*") if p.is_file() and not SKIP & set(p.parts))


def expected():
    """Every file of the Claude folder, mapped to its source path or to generated text."""
    out = {}
    for item in SHARED:
        s = SRC / item
        if s.is_file():
            out[Path(item)] = s
        else:
            for f in files(s):
                out[Path(item) / f] = s / f
    out[Path(".claude-plugin/icon.png")] = icon_bytes()
    out[Path(".claude-plugin/plugin.json")] = json.dumps(MANIFEST, indent=2, ensure_ascii=False) + "\n"
    out[Path("README.md")] = README
    return out


def differences():
    want = expected()
    have = set(files(DEST)) if DEST.is_dir() else set()
    diffs = [f"extra: {f}" for f in sorted(have - set(want))]
    for rel, src in want.items():
        dst = DEST / rel
        if not dst.is_file():
            diffs.append(f"missing: {rel}")
        elif isinstance(src, str):
            if dst.read_text(encoding="utf-8") != src:
                diffs.append(f"changed: {rel}")
        elif isinstance(src, bytes):
            if dst.read_bytes() != src:
                diffs.append(f"changed: {rel}")
        elif not filecmp.cmp(src, dst, shallow=False):
            diffs.append(f"changed: {rel}")
    return diffs


def build():
    if DEST.exists():
        shutil.rmtree(DEST)
    for rel, src in expected().items():
        dst = DEST / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(src, str):
            dst.write_text(src, encoding="utf-8")
        elif isinstance(src, bytes):
            dst.write_bytes(src)
        else:
            shutil.copy2(src, dst)


if __name__ == "__main__":
    if not (SRC / "plugin.json").is_file():
        sys.exit(f"Codex plugin not found at {SRC}")
    if "--check" not in sys.argv:
        build()
    d = differences()
    for line in d:
        print(line)
    print("claude-ael in step with codex-ael" if not d else f"{len(d)} differences")
    sys.exit(1 if d else 0)
