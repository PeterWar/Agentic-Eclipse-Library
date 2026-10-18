# Setup and operation

Resolve the plugin root from this file's parent directory, or from the selected skill at `skills/NAME/SKILL.md`
(two parents up). Never assume the shell's current directory is the plugin directory. Resolve user input and
output paths against the user's workspace, not the plugin's read-only installation/cache directory.

## Choose and check Python

Use the user's existing Python environment and project conventions. Find a Python 3.10+ interpreter with
the needed packages; do not embed a machine-specific interpreter path in a saved script. In the examples,
`PYTHON` means that chosen executable and `PLUGIN` means the resolved plugin directory, not literal commands.

```
PYTHON PLUGIN/scripts/run_ael.py --check
```

The check reports available modules without installing anything. If dependencies are missing, explain the
required installation and use the user's normal Python setup. The bundled source is installable with pip:

```
PYTHON -m pip install "PLUGIN/runtime"
PYTHON -m pip install "PLUGIN/runtime[raw,photoshop]"
```

Choose only the extras needed. `raw` adds rawpy and Astropy; `photoshop` adds psd-tools. Do not silently upgrade
unrelated environments, use system-wide elevated installation, or create a new environment against the
user's project conventions. The launcher always imports the bundled AEL, so an older system installation
cannot silently replace it. Python dependencies remain required. For direct Python API work, add
`PLUGIN/runtime` to the script's import path explicitly, or use the installed, version-checked package.

Run `PYTHON PLUGIN/scripts/run_ael.py selftest` before first processing. Report passed, failed and skipped
tests separately. These known-truth tests exercise the program; they do not certify real astronomical data.

## Commands

Use `PYTHON PLUGIN/scripts/run_ael.py COMMAND --help` for exact arguments. The launcher refuses an existing
output path for every writing command. It never installs packages or downloads observations itself.

| Task | Command | Read first |
| --- | --- | --- |
| Declared linear stacking | `stack --config RECIPE --out NEW_DIR` | `DEVELOP.md`, `examples/stack_config_template.json` |
| Differential extinction | `extinction --config RECIPE --out NEW_DIR` | `DEVELOP.md`, `examples/extinction_config_template.json` |
| Filter layers and optional PSB | `filters --config RECIPE --out NEW_DIR` | `DEVELOP.md`, `examples/filters_config_template.json` |
| Structure display | `structure --input ARRAY --geometry GEOMETRY --valid MASK --out NEW_DIR` | `README_AEL.md` |
| Polar view | `polar --input IMAGE --geometry GEOMETRY --out NEW_DIR` | `README_AEL.md` |
| Motion analysis | `motion --config RECIPE --out NEW_DIR` | `README_AEL.md`, `examples/motion_config_template.json` |
| Coronal structure comparison | `coronagraph --config RECIPE --out NEW_DIR` | `README_AEL.md`, `examples/coronagraph_config_template.json` |
| Synthetic demonstration | `demo-motion --out NEW_DIR` | This creates synthetic test data, not an observed eclipse |

Recipe paths resolve relative to the recipe file. Templates require measured values and real file paths;
they are not ready-to-run observations. Copy them into the user's workspace before editing.

The plugin's `structure` command uses the full canvas (`crop_height_rsun=None`) and mono by default.
Choose `--style measured` only for colour data with a justified colour interpretation. `--style cool` is an
explicit display choice, not measured colour. It also accepts `--sky-r-min-rsun` for a justified sky region;
never fit a sky inside the corona just to make an image run. The underlying AEL 1.3.3 CLI has different
display/crop defaults; use this launcher for plugin work.

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
