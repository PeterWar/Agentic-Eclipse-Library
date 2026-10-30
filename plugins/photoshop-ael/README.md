# Adobe Photoshop bridge for Agentic Eclipse Library

This prototype runs Agentic Eclipse Library (AEL) operations from Adobe Photoshop through ExtendScript and a small Python runner. AEL remains the only implementation of the calculations, recipes and scientific gates.

The source document is never edited, saved or closed. The bridge duplicates it temporarily to export a TIFF, closes only that duplicate, and opens every result as a new document. Each run uses a new output directory; previous results are not overwritten.

## Requirements

- macOS with Adobe Photoshop 2026. Version 27.11.0 was used for validation.
- Python 3.10 or later with AEL and its dependencies.
- An AEL installation in that Python environment, or a source checkout containing the `ael` package.
- ExifTool for the automatic linear-master workflow.

Install AEL in the selected Python environment:

```bash
python -m pip install agentic-eclipse-library
```

For a source checkout, select its root as **AEL folder (optional)**. The bridge passes it through `PYTHONPATH`; it does not install or modify AEL.

## Local installation

Keep `AELPhotoshop.jsx`, `AELPhotoshopCore.jsx`, `AELPhotoshopDialog.jsx` and `python/` together with their relative paths.

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

Choose `filters` and select `linear.npy`. The helper finds `geometry.json`, `valid.npy`, `coverage.npy` and `alpha.npy` beside it, measures a display scale from observed corona pixels, and generates all sixteen portable AEL filters by default.

It writes the authoritative NPY products, sixteen 16-bit filter TIFFs, sixteen alpha TIFFs and a display TIFF. Every TIFF opens in a separate new Photoshop document. `display.tif` is the display base alone, rendered by AEL with the same scale and no visible filter, so the filter layers can be stacked on it with the blend mode and opacity listed for each one; AEL's finished display, filters included, stays in `ael/display.tif`. `pixelmath.json` and `PIXELMATH.md` are the same recipe written for PixInsight's PixelMath. This prototype does not automatically build a layered composite or alter an existing PSB/PSD.

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

The workflow reads exposure and ISO with ExifTool, rejects mixed cameras or ISO values, registers every frame on the Sun, runs the frozen AEL stack recipe, and continues into filter layers.

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
- a refused run, before AEL, for a document with transparent pixels;
- export of a document without a colour profile;
- a result file that is not plain JSON is refused instead of evaluated;
- a clear error for an explicitly invalid Python path;
- synthetic master registration on the Sun and comparison with known truth;
- sixteen filter TIFFs and sixteen alpha TIFFs;
- the expected number of newly opened result documents;
- cleanup of only documents created by the test.

`--skip-photoshop` checks only the direct Python/AEL operations and is not a complete bridge validation. `probe_jsx.py` is a minimal JSX-to-Python diagnostic. `test_runner_inputs.py` checks, without Photoshop, that a transparent or planar export stops before AEL runs.

The registration has its own tests, without Photoshop. `workflow_lunar_motion.py`: the telescope drifts and the Moon moves 1.6 and 3.2 px across the Sun, with and without photon noise and a saturated inner corona; the gate is 0.1 px against the Sun, and another corona with the Moon in the same place must be refused. `workflow_lunar_noise.py`, written separately: shorter exposures (0.01–0.04 s), a Moon moving 4 px, an unrelated corona, and a noisy gate of three times the noise floor measured in the same run. A registration on the lunar limb fails both with errors equal to the lunar motion. `workflow_dark_guard.py` checks the dark refusal.

## Limitations

- Tested only on macOS with Photoshop 2026 27.11.0. Windows, Linux and older Photoshop versions are untested.
- Python is required; this is not a self-contained native or UXP package.
- Real eclipse data, RAW/Bayer input, rotation and production dark/flat matching remain untested in this connector.
- **The registration on the Sun is not valid on real frames yet.** On real Vixen R6 III totality frames (2026-08-12, read without dark or flat), it lands 0.07–2.2 px from the reference registration (lunar limb plus the DE440s ephemeris, which an independent phase correlation of the corona confirms within 0.04–0.46 px), and up to 3.3 px at 10 s; the error grows with the time between frames. Frames of 1/500 s and shorter do not converge, and the structure check accepts frames registered 1–3 px wrong. The cause has not been found: neither the lunar margin, the outer radius, the weighting, pre-smoothing, a planar extinction term nor field rotation explains it. Do not use the automatic master on real frames.
- AEL products carry no ICC profile. Photoshop applies its own missing-profile policy when it opens them, and that policy may ask in a dialog even when scripts suppress dialogs.
- Byte-for-byte ICC preservation has not been tested. The receipt records the embedded ICC byte count; no intentional colour conversion is performed.
- Results open as separate documents. No automatic layered composite is created, and no existing Photoshop document receives new layers.
- ExtendScript `app.system` is synchronous. Photoshop waits while AEL runs.
- The connector has not been signed, packaged for automatic updates or published.
