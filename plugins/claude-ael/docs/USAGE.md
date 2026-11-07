# Setup and operation

This plugin holds instructions, recipe templates and documentation only. The numerical work is done by the
AEL 1.4.2 Python package, installed in the user's Python environment from the project's GitHub release.
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
PYTHON -c "import importlib.util as u, sys; print(sys.version.split()[0], {m: u.find_spec(m) is not None for m in ('ael', 'numpy', 'scipy', 'cv2', 'PIL', 'tifffile', 'imageio', 'rawpy', 'astropy', 'psd_tools')})"
PYTHON -c "import importlib.metadata as md; print(md.version('agentic-eclipse-library'))"
```

These instructions were checked against AEL 1.4.2. If another version is installed, tell the user which one
and ask before replacing it; do not mix these instructions with another version's defaults.

## Install the engine, only with the user's approval

Before installing, tell the user what will be downloaded and from where, and wait for their approval:

- the AEL 1.4.2 wheel (about 250 KB) from the project's GitHub release, which pip checks against the SHA-256
  fingerprint written below;
- its dependencies, normally from PyPI: numpy ≥ 1.24, scipy ≥ 1.10, opencv-python-headless ≥ 4.8, pillow ≥ 9,
  tifffile ≥ 2023.1 and imageio ≥ 2.30; the `raw` extra adds rawpy ≥ 0.19 and astropy ≥ 5 for RAW and FITS
  frames, and `photoshop` adds psd-tools ≥ 1.18 for layered Photoshop files.

```
PYTHON -m pip install "agentic-eclipse-library[raw,photoshop] @ https://github.com/PeterWar/Agentic-Eclipse-Library/releases/download/v1.4.2/agentic_eclipse_library-1.4.2-py3-none-any.whl#sha256=a86e0e75c01a8bbc59173c03d82afbeda68bbab0a73de326c4a3ca7223007e25"
```

Choose only the extras needed; with none, the requirement starts `agentic-eclipse-library @`. Run the command
first with `--dry-run` added: if pip would upgrade or replace a package already in the environment, or if
`opencv-python` is installed (two copies of `cv2` conflict), tell the user and ask before going on. pip refuses
the file if its fingerprint differs: report that and stop, never remove or edit the `#sha256=` part to get past
it. The release page lists the same fingerprint in `SHA256SUMS`: https://github.com/PeterWar/Agentic-Eclipse-Library/releases/tag/v1.4.2. Do not upgrade unrelated
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
print(json.dumps({k: result[k] for k in ("files", "receipt", "gate")}, indent=2))
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
