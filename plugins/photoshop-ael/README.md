# Adobe Photoshop bridge for Agentic Eclipse Library

This prototype runs Agentic Eclipse Library (AEL) operations from Adobe Photoshop through ExtendScript and a small Python runner. AEL remains the only implementation of the calculations, recipes and scientific gates. It was validated with AEL 1.3.6.

The source document is never edited, saved or closed. The bridge duplicates it temporarily to export a TIFF, closes only that duplicate, and opens every result as a new document. Each run uses a new output directory; previous results are not overwritten.

## Requirements

- macOS with Adobe Photoshop 2026. Version 27.11.0 was used for validation.
- Python 3.10 or later with AEL's dependencies (numpy, scipy, opencv-python-headless, pillow, tifffile, imageio) and psd-tools, which writes the layered PSB. rawpy is needed only for RAW frames.
- The AEL engine. With **AEL folder (optional)** empty, the bridge uses, in this order, the engine bundled beside the scripts in `runtime/ael`, the repository that contains `plugins/photoshop-ael`, and an AEL installed in the selected Python.
- ExifTool for the automatic linear-master workflow.

Install the dependencies, or AEL itself from a checkout, in the selected Python environment:

```bash
python -m pip install "/path/to/Agentic-Eclipse-Library[photoshop]"
```

A folder chosen as **AEL folder (optional)** must contain the `ael` package. The bridge passes it through `PYTHONPATH`; it does not install or modify AEL.

The scripts name no interpreter. With **Python (optional)** empty, the bridge looks, in this order, at the Python that worked last time (kept in Photoshop's custom options), `AEL_PYTHON`, `python3` and `python3.N` (newest first) in `/opt/homebrew/bin` and `/usr/local/bin`, virtual environments (`~/.venvs/*`, `~/.virtualenvs/*`, `~/venvs/*`, `~/venv`, `~/.venv`), pyenv, conda and `/usr/bin/python3`. It asks each existing one for Python 3.10+, AEL and the modules above, and uses the first that answers; when none does, the error lists every Python tried and why it failed. A Python chosen in the dialog is the only candidate.

## Local installation

Keep `AELPhotoshop.jsx`, `AELPhotoshopCore.jsx`, `AELPhotoshopDialog.jsx`, `python/` and, when present, `runtime/` together with their relative paths.

`tools/build_package.py --out NEW_FOLDER [--zip FILE]` writes such a folder: the scripts, the runner, the `ael` package of this checkout under `runtime/ael` (checked byte by byte), `runtime/VERSION.json` (AEL version, the last commit of `ael/`, the commit of the connector and whether either had uncommitted changes), and synthetic demonstration files for the four operations made by `tools/make_demo.py`. `--zip` adds a deterministic ZIP of the whole folder; `--pack FOLDER --zip FILE` makes it from a folder already built. The PixInsight connector's builder is the same program.

In Photoshop, choose **File > Scripts > Browse…** and select `AELPhotoshop.jsx`. You can also copy the complete folder into Photoshop's Scripts folder and restart Photoshop. This is a local prototype, not a signed UXP plugin or an auto-updating package.

## Operations

### Structure or polar from the active document

1. Open an RGB or grayscale document and make it active.
2. Choose `structure` or `polar`.
3. Select an `EclipseGeometry` JSON file and an output parent folder.
4. Optionally select Python and an AEL source checkout. If Python is explicit, an invalid path is an error; if it is empty, the bridge tries known Python locations.
5. For `structure`, an optional boolean `valid.npy` mask can be supplied. For `polar`, set the outer radius in solar radii.

The bridge exports the merged visible document through a temporary duplicate. It does not change layer visibility, flatten the source, crop it, convert its colour profile or save it. The temporary TIFF shape, channel layout, sample type, ICC byte count and SHA-256 are recorded and checked before AEL runs. If the visible composite has transparent pixels, the run stops: Photoshop has no data there and would otherwise fill them with white. AEL outputs are opened as new documents and written to disk with `AEL_PHOTOSHOP_RECEIPT.json`.

`polar` expects display-range data. `structure` expects a linear composite with valid geometry and enough outer field for its sky model. AEL's own crop and display recipes apply to these products.

### Filter layers from an existing linear master

Choose `filters` and select `linear.npy`. The helper finds `geometry.json`, `valid.npy`, `coverage.npy` and `alpha.npy` beside it, measures a display scale from observed corona pixels, and generates all sixteen portable AEL filters by default. A Python configuration may ask for `"filters": "defaults"`, AEL's own default layers read from `ael.filterbank` (NRGF, WOW edge-aware and isotropic ACHF 04), or for a list of names; a name AEL still accepts for a renamed filter, such as `wow_bilateral`, becomes the current one.

It writes the authoritative NPY products, sixteen 16-bit filter TIFFs, sixteen alpha TIFFs and a display TIFF. `display.tif` is the display base alone over black with its alpha, as a 32-bit float image: exactly where AEL starts its own composite, rendered with the same scale and no visible filter, so the filter layers can be stacked on it with the blend mode and opacity listed for each one; AEL's finished display, filters included, stays in `ael/display.tif`. `pixelmath.json` and `PIXELMATH.md` are the same recipe written for PixInsight's PixelMath.

By default AEL also writes `ael/corona.psb`, one layered 16-bit Photoshop file verified by AEL after writing it: a hidden linear reference layer, the display base and the sixteen filters, each with its family name, blend mode, opacity, visibility and alpha. The bridge opens that PSB (and, for `master`, the linear master TIFF) instead of thirty-three documents, then reads the layers back in Photoshop and compares them with what AEL wrote: names, blend modes, the opacity byte (AEL stores opacity in 8 bits) and visibility. The comparison opens with the closing message and is saved as `AEL_PHOTOSHOP_NATIVE_CHECK.json`. **Open every filter layer as a separate document** opens every TIFF instead; there the display base, which AEL hands to PixelMath as a 32-bit float start, opens as a copy rounded once to 16 bits, because Photoshop has no Overlay at 32 bits per channel. No existing PSB/PSD is altered.

### Automatic linear master and filters

Choose `master`, select the input frames, reference geometry, and a measured camera-profile JSON:

```json
{
  "black": 512,
  "white": 16000,
  "linearity_fraction": 0.95,
  "train": "camera and optics identifier"
}
```

The workflow reads exposure and ISO with ExifTool, rejects mixed cameras or ISO values, registers every frame on the Sun, runs the frozen AEL stack recipe, and continues into filter layers. The dialog marks it EXPERIMENTAL and shows the same notice as the PixInsight connector: see the limitations.

The corona is fixed on the Sun, and during totality the Moon moves across it (about 0.5″ per second). Registration therefore measures a translation on the corona: the logarithm of the unsaturated corona within 3 solar radii, weighted by its signal, fitted coarse to fine with a free exposure offset. Each frame leaves out its own Moon, fitted on its own limb, plus a margin for the blurred lunar edge (6 px or 1.5 % of the lunar radius); the limb gives only the starting point and each frame's lunar mask. Two gates follow. The coronal structure must match: a band-pass of the corona (linear smoothing first, so short noisy exposures keep their structure) is correlated where both frames have data over the filter's whole support, and compared with the same frame turned 90° and 270° about the Sun; the structure score `(c − c_turned) / (1 − c_turned)` must reach 0.25. And the Moon may not have moved more than 0.1 lunar radii + 2 px relative to the Sun. Rotation is refused. Mixed-optics distortion, cloud transmission, colour calibration and absolute photometry are not inferred. This registration is the same code as the PixInsight connector's.

Black, white and the linear ceiling must be measured calibration values. Optional dark/flat support in the Python configuration requires compatible calibration masters; the minimal dialog does not expose these options. AEL subtracts the dark before dividing by each frame's exposure, so one dark matches one exposure: the workflow refuses a dark when the frames have different exposures.

## Validation

Run the synthetic test launcher with a suitable interpreter (`AEL_PYTHON` can select one explicitly):

```bash
PYTHONDONTWRITEBYTECODE=1 python plugins/photoshop-ael/tests/run_tests.py \
  --output /path/to/validation-output
```

The test uses only synthetic data and paths containing spaces and accented characters. It covers:

- exact float32 RGB round trips and a negative orientation control;
- identical `structure` and `polar` pixels from direct AEL and Photoshop bridge executions;
- unchanged source pixels and saved state;
- NaN, as real AEL stacks carry outside their coverage, also at the first and the last sample: Photoshop opens them, holds them at 32 bits and exports them unchanged, and `structure` matches direct AEL;
- a refused run, before AEL, for a document with transparent pixels;
- export of a document without a colour profile;
- a result file that is not plain JSON is refused instead of evaluated;
- a clear error for an explicitly invalid Python path;
- the automatic Python search from scratch, which must find one by itself, and its error listing every Python tried when none answers;
- no interpreter named in the scripts or the tests;
- with the AEL folder empty, the engine found is the one of this checkout;
- synthetic master registration on the Sun and comparison with known truth;
- sixteen filter TIFFs and sixteen alpha TIFFs;
- the layered PSB opened natively for `master` and `filters`, with its nineteen layers matching what AEL wrote, and the layer check failing on a stand-in document with one opacity byte too many or too few, or another blend mode;
- each of the eighteen layers above the Background as Photoshop holds it (alone, normal mode, full opacity) against the layer AEL wrote, where AEL's alpha is opaque: at most one 16-bit step, the round trip through Photoshop's 15-bit grid, declared before the first run;
- Photoshop's own composite of the PSB (a merged copy of the visible layers) against AEL's composite `ael/display.tif`: at most 8 16-bit steps, because Photoshop holds 16-bit images as 15-bit and rounds at each of the four visible blends; and against a model of that arithmetic (15-bit layers and alphas, rounding after every blend), which it must follow to a mean of 0.2 steps with at most 0.5 % of pixels beyond 2. On the demonstration image Photoshop lands up to 5 steps from AEL (4 at the 99.9th percentile, mean 0.9) and matches the model exactly at 95.8 % of its pixels. A 99.9th-percentile bound of 3, declared before the first run, failed at 4.0 and was replaced by the model once it reproduced Photoshop;
- every separate document 16-bit;
- the expected number of newly opened result documents, for the layered PSB and for separate documents;
- cleanup of only documents created by the test.

`run_package_tests.py --package FOLDER --output NEW_FOLDER` tests a folder written by `tools/build_package.py` in Photoshop the way a person uses it: the package's own entry script and dialog, with only the ScriptUI window, the file choosers and `alert()` replaced by test doubles so that no modal window appears; Python and AEL folder left empty, so the package must find a Python and use its bundled engine; the four operations on the demonstration files, with fields of other operations filled in to check that the dialog leaves them out and a comma as decimal separator; a master without frames that must be refused; only the test's documents closed; and the package byte for byte unchanged.

After the Photoshop part, the same test makes every product again with `python -m ael` from a terminal (same Python, the package's AEL, the bridge's own command or recipe) and compares every file by SHA-256, receipts aside because they record their own paths and times: `structure` and `polar` on the TIFF that Photoshop exported, whose pixels must equal the demonstration file's; `stack` for the master; `filters` for the filter layers, the PSB and the display base of both operations; and the 16-bit TIFFs the bridge writes, which must equal AEL's arrays through `ael.photoshop.to_u16`. The report lists the SHA-256 of every input and output.

`--skip-photoshop` checks only the direct Python/AEL operations and is not a complete bridge validation. `probe_jsx.py` is a minimal JSX-to-Python diagnostic. `test_runner_inputs.py` checks, without Photoshop, that a transparent or planar export stops before AEL runs, and that the probe refuses a Python without psd-tools or with a psd-tools that cannot be imported.

The registration has its own tests, without Photoshop. `workflow_lunar_motion.py`: the telescope drifts and the Moon moves 1.6 and 3.2 px across the Sun, with and without photon noise and a saturated inner corona; the gate is 0.1 px against the Sun, and another corona with the Moon in the same place must be refused. `workflow_lunar_noise.py`, written separately: shorter exposures (0.01–0.04 s), a Moon moving 4 px, an unrelated corona, and a noisy gate of three times the noise floor measured in the same run. A registration on the lunar limb fails both with errors equal to the lunar motion. `workflow_dark_guard.py` checks the dark refusal.

## Limitations

- Tested only on macOS with Photoshop 2026 27.11.0. Windows, Linux and older Photoshop versions are untested.
- Python is required; this is not a self-contained native or UXP package.
- Real eclipse data, RAW/Bayer input, rotation and production dark/flat matching remain untested in this connector.
- **The registration on the Sun is not valid on real frames yet.** On real Vixen R6 III totality frames (2026-08-12, read without dark or flat), it lands 0.07–2.2 px from the reference registration (lunar limb plus the DE440s ephemeris, which an independent phase correlation of the corona confirms within 0.04–0.46 px), and up to 3.3 px at 10 s; the error grows with the time between frames. Frames of 1/500 s and shorter do not converge, and the structure check accepts frames registered 1–3 px wrong. The cause has not been found: neither the lunar margin, the outer radius, the weighting, pre-smoothing, a planar extinction term nor field rotation explains it. Do not use the automatic master on real frames.
- AEL products carry no ICC profile. Photoshop applies its own missing-profile policy when it opens them, and that policy may ask in a dialog even when scripts suppress dialogs.
- Byte-for-byte ICC preservation has not been tested. The receipt records the embedded ICC byte count; no intentional colour conversion is performed.
- The layered PSB is the one AEL writes with psd-tools; Photoshop only opens and reads it. No existing Photoshop document receives new layers.
- AEL's structure product is, by AEL's design, a 16:9 crop 6.4 solar radii high around the Sun, written with the geometry of the crop. The other products keep the whole canvas.
- ExtendScript `app.system` is synchronous. Photoshop waits while AEL runs.
- The connector has not been signed, packaged for automatic updates or published.
