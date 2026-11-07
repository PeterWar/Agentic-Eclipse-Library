"""Build the Claude plugin folder from the published Codex plugin, without touching it.

plugins/codex-ael/ is the host-neutral bundle (AEL runtime, seven short skills, docs, examples,
launcher) maintained by tools/build_codex_plugin_20261016.py. Claude's plugin directory accepts
programs only from Verified organizations; from anyone else it takes Markdown, text, JSON, YAML and
images, nothing that starts with #! and no package-manager configuration. So plugins/claude-ael/
carries no code: the skills, docs, examples and images of the Codex bundle, without `runtime/` and
`scripts/`, with the few sentences that point at the bundled launcher rewritten, and its own
`docs/USAGE.md`, which installs the engine from the GitHub release wheel pinned by its SHA-256.

    python tools/build_claude_plugin.py                 # rebuild plugins/claude-ael/
    python tools/build_claude_plugin.py --check         # exit 1 if it is out of step with codex-ael
    python tools/build_claude_plugin.py --policy DIR    # list the files of DIR the directory refuses
"""
import filecmp
import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "plugins" / "codex-ael"
DEST = REPO / "plugins" / "claude-ael"
SHARED = ["LICENSE", "docs", "examples", "skills", "assets/synthetic-workflow.png"]
SKIP = {".DS_Store", "__pycache__"}
EXCLUDE = {Path("skills/eclipse-astrophotography/agents/openai.yaml")}  # Codex interface metadata

VERSION = "1.4.2"
WHEEL = f"agentic_eclipse_library-{VERSION}-py3-none-any.whl"
WHEEL_URL = f"https://github.com/PeterWar/Agentic-Eclipse-Library/releases/download/v{VERSION}/{WHEEL}"
WHEEL_SHA256 = "a86e0e75c01a8bbc59173c03d82afbeda68bbab0a73de326c4a3ca7223007e25"
RELEASE_URL = f"https://github.com/PeterWar/Agentic-Eclipse-Library/releases/tag/v{VERSION}"

MANIFEST = {
    "name": "agentic-eclipse-library",
    "version": VERSION,
    "description": ("Process total solar eclipse photos locally: calibrated HDR stacking, corona filter layers, "
                    "layered Photoshop files, polar views, motion analysis and coronagraph comparisons, with "
                    f"measured inputs and explicit validation limits. Uses the AEL {VERSION} Python engine, "
                    "installed with your approval from the project's GitHub release."),
    "author": {"name": "Pere Guerra Serra", "url": "https://github.com/PeterWar"},
    "homepage": "https://github.com/PeterWar/Agentic-Eclipse-Library",
    "repository": "https://github.com/PeterWar/Agentic-Eclipse-Library",
    "license": "MIT",
    "keywords": ["solar-eclipse", "astrophotography", "astronomy", "solar-corona", "hdr", "raw",
                 "image-processing", "photoshop", "photometry", "coronagraph", "polar", "scientific-imaging"],
}

# Sentences of the shared files that point at the bundled launcher, and how many times each appears.
# A change in the Codex text makes the build stop here instead of copying a stale sentence.
_SETUP = "Resolve this plugin's root from this skill file and use its bundled launcher."
_SETUP_NEW = (f"This plugin holds instructions only: run the AEL {VERSION} engine installed and checked as that "
              "guide describes.")
EDITS = {
    "skills/eclipse-first-steps/SKILL.md": [
        (_SETUP, _SETUP_NEW, 1),
        ("Check Python dependencies with `scripts/run_ael.py --check`, then run `selftest`.",
         "Check the installed AEL version and its Python dependencies as the guide describes, then run `selftest`.", 1),
    ],
    "skills/eclipse-calibration-stacking/SKILL.md": [
        (_SETUP, _SETUP_NEW, 1),
        ("Run `stack --config RECIPE --out NEW_DIR` through the launcher.",
         "Run `stack --config RECIPE --out NEW_DIR` with the installed engine (`PYTHON -m ael`), into a new directory.", 1),
    ],
    "skills/corona-filter-layers/SKILL.md": [
        (_SETUP, _SETUP_NEW, 1),
        ("Run `filters --config RECIPE --out NEW_DIR` through the launcher.",
         "Run `filters --config RECIPE --out NEW_DIR` with the installed engine (`PYTHON -m ael`), into a new directory.", 1),
    ],
    "skills/eclipse-artefact-diagnosis/SKILL.md": [(_SETUP, _SETUP_NEW, 1)],
    "skills/coronagraph-comparison/SKILL.md": [(_SETUP, _SETUP_NEW, 1)],
    "skills/corona-views-motion/SKILL.md": [
        (_SETUP, _SETUP_NEW, 1),
        ("and the corresponding maintained source under `runtime/ael/` for API parameters.",
         "and the docstrings of the installed `ael` package for API parameters.", 1),
        ("For structure, use the plugin launcher `structure --input ARRAY --valid MASK --geometry GEOMETRY --out NEW_DIR`. "
         "It preserves the full canvas and defaults to mono.",
         "For structure, use [the full-canvas call of the setup guide](../../docs/USAGE.md#structure-display-on-the-full-canvas): "
         "it keeps the whole canvas and writes mono by default. The plain `PYTHON -m ael structure` command crops to "
         "3.2 solar radii and, from RGB data, adds two colour styles; do not use it for this plugin's work.", 1),
    ],
    "skills/eclipse-astrophotography/SKILL.md": [
        ("use that package's bundled launcher instead of assuming the shell working directory or another installed AEL.",
         "use the engine version that guide pins and checks instead of assuming the shell working directory or "
         "another installed AEL.", 1),
        ("Offering to prepare a local draft of a useful lesson, as AEL's AGENTS.md asks, is still welcome;",
         "Offering to prepare a local draft of a useful lesson for the AEL project is still welcome;", 1),
        ("In the Codex plugin or the Claude plugin folder (`plugins/claude-ael`) use `eclipse-calibration-stacking`, "
         "`corona-filter-layers` or `eclipse-artefact-diagnosis`; in this repository, and in the Claude Code plugin "
         "installed from its marketplace, the corresponding skills are `apilatge-imatges-eclipsi`, "
         "`postprocessat-corona` and `corregeix-artefactes`. Read their actual local entrypoints when present.",
         "In this plugin, use `eclipse-calibration-stacking`, `corona-filter-layers` or `eclipse-artefact-diagnosis`.", 1),
        ("Use AEL 1.3.3 as the reference for this skill; record the actual source version and environment",
         f"This skill was written against AEL 1.3.3; run the version that [the setup guide](../../docs/USAGE.md) "
         f"pins ({VERSION}) and record the actual source version and environment", 1),
        ("(`eclipse-artefact-diagnosis` in the plugin, `corregeix-artefactes` in a source checkout)",
         "(`eclipse-artefact-diagnosis`)", 1),
    ],
    "docs/coronagraph-method.md": [
        ("its docstrings in `runtime/ael/coronagraph.py`", "its docstrings in the installed package (`ael/coronagraph.py`)", 1),
    ],
}

USAGE = f"""# Setup and operation

This plugin holds instructions, recipe templates and documentation only. The numerical work is done by the
AEL {VERSION} Python package, installed in the user's Python environment from the project's GitHub release.
Resolve user input and output paths against the user's workspace, not the plugin's installation directory.

## Choose Python and check what is installed

Use the user's existing Python environment and project conventions. Find a Python 3.10+ interpreter; do not
embed a machine-specific interpreter path in a saved script. In the examples, `PYTHON` means that chosen
executable, not a literal command. If there is no Python 3.10+, or pip refuses to install into the chosen one
because the operating system or Homebrew manages it, propose a virtual environment (`PYTHON -m venv DIR`), say
where, and wait for approval. Never use `sudo` or `--break-system-packages`.

Check what is there without installing anything. The first line lists the modules found; the second prints the
installed AEL version, or fails if AEL is not installed:

```
PYTHON -c "import importlib.util as u, sys; print(sys.version.split()[0], {{m: u.find_spec(m) is not None for m in ('ael', 'numpy', 'scipy', 'cv2', 'PIL', 'tifffile', 'imageio', 'rawpy', 'astropy', 'psd_tools')}})"
PYTHON -c "import importlib.metadata as md; print(md.version('agentic-eclipse-library'))"
```

These instructions were checked against AEL {VERSION}. If another version is installed, tell the user which one
and ask before replacing it; do not mix these instructions with another version's defaults.

## Install the engine, only with the user's approval

Before installing, tell the user what will be downloaded and from where, and wait for their approval:

- the AEL {VERSION} wheel (about 250 KB) from the project's GitHub release, which pip checks against the SHA-256
  fingerprint written below;
- its dependencies, normally from PyPI: numpy ≥ 1.24, scipy ≥ 1.10, opencv-python-headless ≥ 4.8, pillow ≥ 9,
  tifffile ≥ 2023.1 and imageio ≥ 2.30; the `raw` extra adds rawpy ≥ 0.19 and astropy ≥ 5 for RAW and FITS
  frames, and `photoshop` adds psd-tools ≥ 1.18 for layered Photoshop files.

```
PYTHON -m pip install "agentic-eclipse-library[raw,photoshop] @ {WHEEL_URL}#sha256={WHEEL_SHA256}"
```

Choose only the extras needed; with none, the requirement starts `agentic-eclipse-library @`. Run the command
first with `--dry-run` added: if pip would upgrade or replace a package already in the environment, or if
`opencv-python` is installed (two copies of `cv2` conflict), tell the user and ask before going on. pip refuses
the file if its fingerprint differs: report that and stop, never remove or edit the `#sha256=` part to get past
it. The release page lists the same fingerprint in `SHA256SUMS`: {RELEASE_URL}. Do not upgrade unrelated
packages silently.

After installing, check from the user's workspace that the installed package is the one imported. Its path must
lie inside the environment's `site-packages`: an `ael` folder in the current directory would be imported first.

```
PYTHON -c "import ael; print(ael.__version__, ael.__file__)"
```

Run `PYTHON -m ael selftest` before first processing. Report passed, failed and skipped tests separately. These
known-truth tests exercise the program; they do not certify real astronomical data.

The examples in `README_AEL.md` and `DEVELOP.md` assume a copy of the source repository: their `pip install .`
lines are for that copy, not for this plugin, and some of them write two commands into the same `out/` folder.
Here, install only as above, and give every run its own new folder.

## Commands

Use `PYTHON -m ael COMMAND --help` for exact arguments. Every writing command needs a new output path: before
each run, check that it does not exist, and choose another if it does. Do not rely on AEL to refuse one: some
commands and every Python call write into an existing folder.

AEL has no network code: it never installs packages or downloads observations. Astropy, when `extinction`
computes the Sun's position from a site and a time, may download Earth-orientation tables if network access is
available; say so before such a run. To write MP4 animations, AEL runs ffmpeg if it is already installed. Other
tools a task may need, such as sunpy to read some LASCO files, are not part of AEL: ask before installing them.

| Task | Command | Read first |
| --- | --- | --- |
| Declared linear stacking | `PYTHON -m ael stack --config RECIPE --out NEW_DIR` | `DEVELOP.md`, `examples/stack_config_template.json` |
| Differential extinction | `PYTHON -m ael extinction --config RECIPE --out NEW_DIR` | `DEVELOP.md`, `examples/extinction_config_template.json` |
| Filter layers and optional PSB | `PYTHON -m ael filters --config RECIPE --out NEW_DIR` | `DEVELOP.md`, `examples/filters_config_template.json` |
| Structure display | the full-canvas call below | `README_AEL.md` |
| Polar view | `PYTHON -m ael polar --input IMAGE --geometry GEOMETRY --out NEW_DIR` | `README_AEL.md` |
| Motion analysis | `PYTHON -m ael motion --config RECIPE --out NEW_DIR` | `README_AEL.md`, `examples/motion_config_template.json` |
| Coronal structure comparison | `PYTHON -m ael coronagraph --config RECIPE --out NEW_DIR` | `README_AEL.md`, `examples/coronagraph_config_template.json` |
| Synthetic demonstration | `PYTHON -m ael demo-motion --out NEW_DIR` | This creates synthetic test data, not an observed eclipse |

Recipe paths resolve relative to the recipe file. Templates require measured values and real file paths;
they are not ready-to-run observations. Copy them into the user's workspace before editing.

## Structure display on the full canvas

The `PYTHON -m ael structure` command keeps the package defaults: a crop to 3.2 solar radii and, from RGB data,
two colour styles besides mono.
For this plugin's work, call the package so that it keeps the full canvas and writes mono unless the user chose
otherwise. Save this in the user's workspace with the real paths, check that `NEW_DIR` does not exist, and run it
with `PYTHON`:

```python
import json
import numpy as np
from ael import io, pipelines
from ael.geometry import EclipseGeometry

data = io.load_array("ARRAY")                    # linear composite, (H, W) or (H, W, 3)
valid = np.load("MASK").astype(bool)             # mask of observed pixels; valid = None without one
result = pipelines.structure_from_linear(
    data, EclipseGeometry.from_json("GEOMETRY"), "NEW_DIR",
    valid=valid, name="structure", styles=("mono",),
    crop_height_rsun=None, sky_r_min_rsun=7.0)
print(json.dumps({{k: result[k] for k in ("files", "receipt", "gate")}}, indent=2))
```

Choose `styles=("measured",)` only for colour data with a justified colour interpretation. `("cool",)` is an
explicit display choice, not measured colour. Both colour styles need RGB input. Change `sky_r_min_rsun` only
for a sky region the field supports; never fit a sky inside the corona just to make an image run.

## Preserve evidence

Keep input RAWs, manual edits, masks, alignment and colour profiles intact. Use new output directories and
record input hashes, geometry, calibration, recipe and environment. Show full canvases; inspect the limb,
coverage boundaries and corners. A diagnostic crop is not a replacement deliverable.

Never fill missing or saturated areas with invented pixels. Never insert pixels from external reference
images. Correct an artefact where it originates and rebuild dependent products. Keep failed controls and
unchanged thresholds. Geometry, colour and the existing look belong to the user: show proposed changes before
adopting them. Do not apply the 2026 camera constants, limb or colour settings to a new dataset.

Distinguish file integrity, visual checks and scientific validation. `linear.npy`/float TIFF and validity
maps carry the linear result; a display TIFF or a Photoshop composite is a presentation product. For a
Photoshop check, use a uniquely named copy and never close a document opened by the user.

Before publication, read `FIELD_LESSONS.md` for unresolved cases and `PAPER_AND_LIBRARY.md` for differences
between the runnable package and historical image layers. Do not claim an exact replay of the author's
finished image or an artefact-free result.
"""

README = f"""# Agentic Eclipse Library for Claude

Process total solar eclipse photographs with seven guided workflows: get started, calibrate and stack,
create corona filter layers, investigate artefacts, make polar views and motion analyses, compare
observations with coronagraphs, and take a whole case to an editable master the photographer accepts
(contributed by Raúl Hussein). Created by Pere Guerra Serra. MIT licensed.

This plugin holds the workflows, recipe templates and practical documentation; it contains no program files. The
numerical processing is done by the AEL {VERSION} Python package, which runs on your computer with Python 3.10
or later. Claude plans the work and explains the results; AEL performs the numerical processing.

![A labelled synthetic demonstration of the workflow](assets/synthetic-workflow.png)

## Start

Install this plugin from Claude's plugin directory. (The repository's own marketplace installs the full
research edition instead: the engine itself plus the original project's longer skills, mostly in Catalan.)
Then ask, in your language:

- Help me process my total solar eclipse photos while preserving the original files.
- Inspect the rings in my corona image and find which processing stage caused them.
- Show me a clearly labelled synthetic demonstration before I use my own photos.

Follow [setup and operating instructions](docs/USAGE.md). Installing the plugin installs no software. Claude
first checks what your Python environment already has; if AEL {VERSION} is missing, it asks before installing it.

## Outputs and limits

AEL can write linear stacks, validity and coverage maps, filter layers, 16-bit layered Photoshop files,
polar views, motion check sheets and animations. A photograph is not an absolute brightness measurement.
Calibration, registration, geometry and any spatial cloud correction require measured inputs; AEL does
not infer all of these from a folder of RAWs. Photoshop itself is optional.

Known limitations in {VERSION} include bands near data boundaries in ACHF/WOW, some fine-detail sign inversion
in the worst sectors of the default edge-aware WOW, and rings of the plain WOW next to a lunar limb that the data reach; of the
layers new in 1.4.2, a light ring of NAFE next to the lunar limb and the copies at ±Δθ of the Larson–Sekanina layers. See [field lessons](docs/FIELD_LESSONS.md). Passing the package's
known-truth tests does not validate a new astronomical observation. Missing data stays missing. Synthetic examples
are labelled and must never be used as pixels in an observed image.

## What this plugin runs, fetches and sends

- **No program files.** Markdown instructions, JSON recipe templates and images only. Claude may write short
  Python scripts in your workspace that call AEL, as the setup instructions show.
- **Runs locally.** The skills run the AEL {VERSION} package with `python -m ael` in the Python environment you
  choose. It reads the files selected for the task and writes new output folders; Claude checks that each output
  folder is new before a command writes to it. To write MP4 animations, AEL runs ffmpeg if it is already installed.
- **Fetches, only with your approval.** Installing AEL downloads its wheel (about 250 KB) from this project's
  GitHub release v{VERSION}; pip refuses it unless its SHA-256 fingerprint matches the one written in the setup
  instructions. pip normally downloads the dependencies from PyPI: NumPy, SciPy, OpenCV, Pillow, tifffile and
  imageio, plus rawpy and Astropy for RAW and FITS, and psd-tools for Photoshop files. AEL itself has no network
  code. Public coronagraph data (K-Cor from the Mauna Loa Solar Observatory, SOHO/LASCO from the Naval Research
  Laboratory, SDO/AIA from Stanford's JSOC) is downloaded only after you approve it, with its source, purpose and
  size stated first. Astropy may fetch Earth-orientation tables when network access is enabled. Any other
  package a task needs, such as sunpy for some LASCO files, is installed only with your approval.
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

# What the directory accepts from an organization that is not Verified (its refusal of 1.4.2, 07-11-2026):
# Markdown, text, JSON, YAML, PNG, JPEG, GIF, WebP or ICO; no file starting with #!; no package-manager
# configuration; text in UTF-8 without NUL bytes. A licence, a readme and .gitignore may stay as UTF-8 text.
TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".json", ".yaml", ".yml"}
TEXT_NAMES = {"LICENSE", "LICENCE", "README", ".gitignore"}
IMAGE_MAGIC = {".png": (b"\x89PNG\r\n\x1a\n",), ".jpg": (b"\xff\xd8\xff",), ".jpeg": (b"\xff\xd8\xff",),
               ".gif": (b"GIF87a", b"GIF89a"), ".webp": (b"RIFF",), ".ico": (b"\x00\x00\x01\x00",)}
PACKAGE_CONFIG = re.compile(r"^(package(-lock)?\.json|npm-shrinkwrap\.json|pnpm-(workspace|lock)\.yaml|yarn\.lock|"
                            r"\.npmrc|\.yarnrc(\.yml)?|bun\.lockb?|pyproject\.toml|setup\.(py|cfg)|"
                            r"requirements.*\.txt|constraints.*\.txt|Pipfile(\.lock)?|poetry\.lock|uv\.lock|"
                            r"environment\.ya?ml|conda\.ya?ml|Cargo\.(toml|lock)|go\.(mod|sum)|Gemfile(\.lock)?|"
                            r"composer\.(json|lock)|deno\.jsonc?)$", re.IGNORECASE)
# Words that would mean a sentence still points at the bundled engine. Validation records are left as released.
LEFTOVER = re.compile(r"run_ael|runtime/|launcher|PLUGIN/|[Bb]undles the AEL")


def policy_findings(base):
    """Every file under `base` that the directory refuses from an organization that is not Verified."""
    found = []
    for rel in files(base):
        p = base / rel
        data = p.read_bytes()
        suffix = p.suffix.lower()
        if PACKAGE_CONFIG.match(p.name):
            found.append(f"package-manager configuration: {rel}")
        elif suffix in IMAGE_MAGIC:
            if not data.startswith(IMAGE_MAGIC[suffix]):
                found.append(f"not a {suffix} image: {rel}")
            elif suffix == ".webp" and data[8:12] != b"WEBP":
                found.append(f"not a .webp image: {rel}")
        elif suffix in TEXT_SUFFIXES or p.name in TEXT_NAMES:
            if data.startswith(b"#!") or data.startswith(b"\xef\xbb\xbf#!"):
                found.append(f"starts with #!: {rel}")
            if b"\x00" in data:
                found.append(f"NUL byte: {rel}")
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                found.append(f"not UTF-8: {rel}")
                continue
            if suffix == ".json":
                try:
                    json.loads(text)
                except ValueError:
                    found.append(f"invalid JSON: {rel}")
        else:
            found.append(f"type not accepted: {rel}")
    return found


def leftovers(base):
    """Sentences of the built folder that still point at a bundled engine."""
    out = []
    for rel in files(base):
        if rel.suffix.lower() in TEXT_SUFFIXES and not rel.name.startswith("VALIDATION_"):
            for n, line in enumerate((base / rel).read_text(encoding="utf-8").splitlines(), 1):
                if LEFTOVER.search(line):
                    out.append(f"points at a bundled engine: {rel}:{n}")
    return out


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


def edited(rel, src):
    text = src.read_text(encoding="utf-8")
    for old, new, count in EDITS[rel]:
        if text.count(old) != count:
            raise SystemExit(f"{SRC.name}/{rel}: expected {count} of the sentence below, found {text.count(old)}; "
                             f"update EDITS in {Path(__file__).name}\n  {old}")
        text = text.replace(old, new)
    return text


def expected():
    """Every file of the Claude folder, mapped to its source path or to generated text."""
    out = {}
    for item in SHARED:
        s = SRC / item
        if s.is_file():
            out[Path(item)] = s
        else:
            for f in files(s):
                if Path(item) / f not in EXCLUDE:
                    out[Path(item) / f] = s / f
    missing = sorted(set(EDITS) - {str(k) for k in out})
    if missing:
        raise SystemExit(f"files to edit not found in {SRC.name}: {missing}")
    for rel in EDITS:
        out[Path(rel)] = edited(rel, out[Path(rel)])
    out[Path("docs/USAGE.md")] = USAGE
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
    if "--policy" in sys.argv:
        target = Path(sys.argv[sys.argv.index("--policy") + 1])
        found = policy_findings(target)
        for line in found:
            print(line)
        print(f"{len(found)} files the directory refuses" if found else "every file is of a type the directory accepts")
        sys.exit(1 if found else 0)
    if not (SRC / "plugin.json").is_file():
        sys.exit(f"Codex plugin not found at {SRC}")
    if "--check" not in sys.argv:
        build()
    d = differences() + policy_findings(DEST) + leftovers(DEST)
    for line in d:
        print(line)
    print("claude-ael in step with codex-ael, and every file of a type the directory accepts"
          if not d else f"{len(d)} problems")
    sys.exit(1 if d else 0)
