# PixInsight bridge for Agentic Eclipse Library

This prototype runs the Agentic Eclipse Library (AEL) `structure` and `polar` commands from PixInsight. It applies AEL's fixed recipes, gates and receipts; it does not make agent decisions and does not change the AEL algorithms.

The source view is never edited. Each resulting image opens in a new PixInsight window and is also written to disk.

## Requirements

- PixInsight 1.9.4 or later.
- Python 3.10 or later with AEL and its dependencies.
- AEL installed in that Python environment, or a source checkout containing the `ael` package.

Install AEL in the selected Python environment:

```bash
python -m pip install agentic-eclipse-library
```

For a source checkout, select the checkout's root directory as **AEL folder (optional)** instead. Do not install a shared environment in editable mode just for this bridge.

## Local installation

1. Keep `AELBridge.js`, `AELBridgeCore.jsh`, `AELBridgeDialog.jsh` and `python/ael_bridge_check.py` together with their relative paths.
2. In PixInsight, choose **Script > Feature Scripts…**.
3. Add `AELBridge.js` and click **Install**.
4. Open **Utilities > Agentic Eclipse Library**.

This is a local prototype, not a signed update repository.

## Use

1. Open a monochrome or three-channel RGB image and select it in the dialog.
2. Choose `structure` or `polar`.
3. Choose an output folder. Each run creates a new timestamped subfolder, so previous runs are not overwritten.
4. Select a Python executable. The bridge checks that it is Python 3.10+ and can import AEL before processing. The selected path is saved in PixInsight settings.
5. If necessary, select the AEL source checkout folder. It is passed through `PYTHONPATH`; no shell is used.
6. Load an `EclipseGeometry` JSON file or complete the geometry fields. Image shape is taken from the selected view. Pixel coordinates are x-right and y-down.
7. For `structure`, optionally select a boolean `.npy` valid-data mask. For `polar`, set the outer radius in solar radii.
8. Click **Run AEL**.

The bridge writes a 32-bit floating-point, interleaved TIFF in a unique temporary directory. A preflight check rejects planar RGB, unexpected shapes, incorrect sample types and missing ICC data before AEL runs. If PixInsight changes ICC header flags while writing TIFF, the helper restores the original profile and verifies that every image sample remains unchanged. The receipt records this repair. The temporary directory is removed afterwards.

The output folder contains the AEL products, `input_geometry.json` and `AEL_BRIDGE_RECEIPT.json`. The bridge receipt records the command, Python and AEL paths and versions, input TIFF SHA-256, layout, ICC information, files and gate result. `structure` also writes AEL's own `structure_RECEIPT.json`; because `polar` does not currently write an AEL receipt, the bridge receipt is the run record for that command. Receipts are printed to the Process Console.

## Validation

The test launcher detects a suitable interpreter; `AEL_PYTHON` can select one explicitly. It uses only synthetic data and starts new PixInsight instances with `--automation-mode` and `--force-exit`. It never sends scripts to an existing instance.

```bash
PYTHONDONTWRITEBYTECODE=1 python plugins/pixinsight-ael/tests/run_tests.py \
  --output /path/to/validation-output
```

The validation covers:

- exact float32 RGB and monochrome TIFF round trips, shape and orientation;
- negative orientation tests;
- exact ICC preservation from a source TIFF;
- identical output pixels from direct AEL and bridge executions of both commands;
- unchanged source pixels;
- clear errors for a missing executable, missing AEL and an old Python;
- paths containing spaces and accented characters;
- dialog and result images rendered by PixInsight.

`VALIDATION.json` contains the gates and exact commands. A missing PixInsight executable or a failed gate makes the complete validation fail. `--skip-pixinsight` runs only direct AEL checks and is not a complete bridge validation. `--skip-captures` omits only the visual captures.

## Automated linear-master and filter workflow

`AELWorkflow.js` adds **Utilities > AEL Linear Master and Filters**. Keep `AELWorkflowCore.jsh`, `AELWorkflowDialog.jsh` and `python/ael_workflow.py` beside the bridge files.

### Filter layers from an existing linear stack — validated

Select **Filter layers from linear.npy**. The helper finds `geometry.json`, `valid.npy`, `coverage.npy` and `alpha.npy` beside the input, measures a display scale from observed corona pixels, and generates all sixteen portable AEL filters by default. It writes:

- float NPY layers and alpha arrays from AEL;
- separate 16-bit TIFF views `AEL_L_<filter>` and `AEL_A_<filter>`;
- `AEL_DISPLAY`, the display base before any filter, and an independent `AEL_COMPOSITE` duplicate;
- `pixelmath.json` and `PIXELMATH.md` with the expressions, which name the layer and alpha views directly (PixelMath symbols accept constants only);
- AEL and workflow receipts.

The default composite applies NRGF, bilateral WOW and isotropic ACHF 04 with their documented opacities, rounded to 8 bits as AEL and Photoshop store them. The other filters remain separate for manual use. PixelMath touches only the composite, never the display base or linear master, and a PixelMath run that fails stops the workflow. The synthetic validation starts from the display base and compares the PixelMath result with AEL's own composite (`ael/display.tif`); it also checks that the two starting images differ, so a PixelMath that changes nothing cannot pass.

### Automatic linear master — validated with synthetic data

This mode reads exposure and ISO with ExifTool, checks one camera/ISO, registers every frame on the Sun, writes the frozen AEL stack recipe, and can continue into filter layers.

The corona is fixed on the Sun, and during totality the Moon moves across it (28.5 px in 105 s on one 2026 train). Registration therefore measures a translation on the corona: the logarithm of the unsaturated corona within 3 solar radii, weighted by its signal, fitted coarse to fine with a free exposure offset. Each frame leaves out its own Moon, fitted on its own limb at full resolution, plus a margin for the blurred lunar edge (6 px or 1.5 % of the lunar radius). The limb gives only the starting point and each frame's lunar mask. Two gates follow. The coronal structure must match: a band-pass of the corona (linear smoothing first, so short noisy exposures keep their structure) is correlated where both frames have data over the filter's whole support, and compared with the same frame turned 90° and 270° about the Sun, which keeps the radial statistics and loses the structure; the structure score `(c − c_turned) / (1 − c_turned)` must reach 0.25. And the Moon may not have moved more than 0.1 lunar radii + 2 px relative to the Sun. Rotation is not supported. It requires a reference geometry JSON and a camera profile:

```json
{
  "black": 512,
  "white": 16000,
  "linearity_fraction": 0.95,
  "train": "camera and optics identifier"
}
```

Black, white and the linear ceiling are measured calibration values; they are never inferred from libraw. Optional master dark and flat files must already match the optical train and native geometry. AEL subtracts the dark before dividing by each frame's exposure, so one dark matches one exposure: the workflow refuses a dark when the frames have different exposures. Cloud transmission, colour calibration and mixed-optics distortion are not inferred.

`tests/workflow_lunar_motion.py` is the gate for this registration. Between three frames the telescope drifts and the Moon moves another 1.6 and 3.2 px across the Sun (0.07 lunar radii, about one totality), always covering it. With a still Moon, a moving Moon, and a moving Moon with photon and read noise and a saturated inner corona, the worst error against the Sun is 0.016 px (gate 0.1 px). Another corona with the Moon in the same place is rejected. An earlier version registered on the lunar limb and failed this test with errors equal to the lunar motion.

`tests/workflow_lunar_noise.py` is a second, separately written judge with shorter exposures (0.01–0.04 s), where the outer corona of the reference is close to the read noise, a Moon moving 4 px, and a frame of an unrelated corona with other streamers and orientation. Its noisy gate is three times the noise floor measured in the same run. The structure check of an earlier version (high-pass correlation of the fine structure ≥ 0.25) refused every good frame of this test, even frames that did not move, because at these exposures the fine structure is mostly noise; the turned-frame score passes them and still refuses the unrelated corona.

Two independent runs of `tests/workflow_synthetic.py` pass all gates: 0.003 px worst translation error (gate 0.1 px), 0.0203% median relative master difference (gate 0.1%), sixteen filters and alpha maps, and a PixelMath composite within one 16-bit step of AEL's composite (gate `1/65535`). The unrelated-image registration control is rejected. `tests/workflow_dark_guard.py` checks the dark refusal. On a 24-megapixel synthetic frame, registration takes about 3 s without noise and about 10 s with short noisy exposures, a 26 px drift and a Moon moved 12.6 px (error 0.023 px; the structure check takes 0.5 s of it). Windows, Linux and real eclipse data remain untested; real frames add seeing, lunar relief, prominences and sensor patterns that the synthetic scenes do not have.

## Limitations

- **The registration on the Sun is not valid on real frames yet.** On real Vixen R6 III totality frames (2026-08-12, read without dark or flat), it lands 0.07–2.2 px from the reference registration (lunar limb plus the DE440s ephemeris, which an independent phase correlation of the corona confirms within 0.04–0.46 px), and up to 3.3 px at 10 s; the error grows with the time between frames. Frames of 1/500 s and shorter do not converge, and the structure check accepts frames registered 1–3 px wrong. The cause has not been found: neither the lunar margin, the outer radius, the weighting, pre-smoothing, a planar extinction term nor field rotation explains it. Do not use the automatic master on real frames.
- Tested only on macOS with PixInsight 1.9.4. Windows and Linux have not been tested.
- Python must be installed separately; this is not a self-contained package or a native C++ module.
- `structure` and `polar` are covered by the original bridge. The complete master/filter workflow is validated with synthetic data only; real eclipse data require separate validation.
- The automatic master holds every frame's luminance in memory at once: plan on several gigabytes for dozens of full-size RAW frames.
- ICC profiles are read from the source file and copied unchanged to the temporary TIFF. An unsaved image, or a profile assigned only in memory after reading the file, cannot be verified or preserved reliably by this prototype. The receipt records the ICC origin and byte counts.
- `polar` expects display-range data in [0, 1]. `structure` expects a linear composite with valid geometry and enough outer field for its sky model.
- The connector has not been signed or packaged for automatic updates.
