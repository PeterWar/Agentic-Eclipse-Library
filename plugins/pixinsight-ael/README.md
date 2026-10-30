# PixInsight bridge for Agentic Eclipse Library

This experimental connector runs the Agentic Eclipse Library (AEL) `structure` and `polar` commands from PixInsight (the bridge) and builds AEL's filter layers, with an adjustable PixelMath composite, from a linear stack (the workflow). It applies AEL's fixed recipes, gates and receipts; it does not make agent decisions and does not change the AEL algorithms.

The source view is never edited. Each resulting image opens in a new PixInsight window and is also written to disk.

## Requirements

- PixInsight 1.9.4 or later.
- Python 3.10 or later with AEL's dependencies: `python -m pip install numpy scipy opencv-python-headless pillow tifffile imageio`. AEL itself is not on PyPI.
- **AEL 1.3.6 or later.** The package built by `tools/build_package.py` carries it under `runtime/ael` and the connector uses it with no setting at all. In a source checkout the repository root, which holds `ael/`, is used the same way. An older AEL, or one whose version cannot be read, is refused before anything is processed: 1.3.6 has the soft-log and MGN corrections that the structure image and the filter layers depend on, and 1.3.5 the edge-aware WOW and the layer names per family.

### Finding Python

Leave **Python executable** empty and the connector looks for one, in this order: the path saved by the last successful run, `AEL_PYTHON`, `python3` and `python3.N` (newest first) in the Homebrew and system folders, the virtual environments in `~/.venvs`, `~/.virtualenvs` and `~/venvs` (and `~/venv`, `~/.venv`), pyenv, conda and Apple's `python3`. Each one is probed before it is used: Python 3.10 or later, and `import ael` works with the selected AEL folder, which needs NumPy and the rest. The first that passes is used and saved. If none does, the message lists every interpreter that was tried and why it failed. A Python without the dependencies is skipped, not used.

## Local installation

1. Keep the folder `pixinsight-ael/` together: the scripts, `python/` and `runtime/` with their relative paths.
2. In PixInsight, choose **Script > Feature Scripts…**.
3. Click **Add** (it asks for a folder), choose the folder `pixinsight-ael/`, and the dialog lists `AELBridge.js` and `AELWorkflow.js`, enabled. Click **Done**.
4. Open **Utilities > Agentic Eclipse Library** (the bridge) and **Utilities > AEL Linear Master and Filters** (the workflow).

This is a local build for testing, not a signed update repository. `tools/build_package.py --out FOLDER [--zip FILE]` assembles the folder, with `runtime/ael` copied from the checkout and checked byte by byte, `runtime/VERSION.json` (AEL version and source commit) and the synthetic files of `demo/`.

## Use

1. Open a monochrome or three-channel RGB image and select it in the dialog (for a floating-point TIFF with values outside 0–1, or one without data in its last sample, see **When PixInsight does not hold the file as it is stored**).
2. Choose `structure` or `polar`.
3. Choose an output folder. Each run creates a new timestamped subfolder, so previous runs are not overwritten.
4. Leave **Python executable** empty to have one found (see above), or select one. The interpreter that worked is saved in PixInsight settings.
5. **AEL folder** starts with the AEL that comes with the connector, whatever an earlier run saved. Select another folder only to use another AEL for that run; it is passed through `PYTHONPATH`, no shell is used.
6. Type the path of an `EclipseGeometry` JSON file, or click **Load JSON** to see its values, or complete the geometry fields. Image shape is taken from the selected view. Pixel coordinates are x-right and y-down.
7. For `structure`, optionally select a boolean `.npy` valid-data mask. For `polar`, set the outer radius in solar radii.
8. Click **Run AEL**.

The bridge writes a 32-bit floating-point, interleaved TIFF in a unique temporary directory. A preflight check rejects planar RGB, unexpected shapes, incorrect sample types and missing ICC data before AEL runs. If PixInsight changes ICC header flags while writing TIFF, the helper restores the original profile and verifies that every image sample remains unchanged. The receipt records this repair. The temporary directory is removed afterwards.

The output folder contains the AEL products, `input_geometry.json` and `AEL_BRIDGE_RECEIPT.json`. The bridge receipt records the command, Python and AEL paths and versions, input TIFF SHA-256, layout, ICC information, files and gate result. `structure` also writes AEL's own `structure_RECEIPT.json`; because `polar` does not currently write an AEL receipt, the bridge receipt is the run record for that command. Receipts are printed to the Process Console.

## Validation

The tests and tools are in the repository (`plugins/pixinsight-ael/tests` and `tools`); the delivered package does not carry them.

The test launcher looks for an interpreter in the same places as the dialog (see **Finding Python**); `AEL_PYTHON` selects one explicitly. It uses only synthetic data and starts new PixInsight instances with `-n --automation-mode` and `--force-exit`, which never send a script to an instance that is already open (without `-n`, PixInsight yields the command to a running instance). A test that is stopped by its timeout stops only its own instance.

```bash
PYTHONDONTWRITEBYTECODE=1 python plugins/pixinsight-ael/tests/run_tests.py \
  --output /path/to/validation-output
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python plugins/pixinsight-ael/tests/dialog_flow.py \
  --repo . --python "$(which python)" --output /path/to/dialog-output
PYTHONDONTWRITEBYTECODE=1 python plugins/pixinsight-ael/tests/entry_scripts.py \
  --repo . --output /path/to/entry-output
```

`run_tests.py` covers:

- exact float32 RGB and monochrome TIFF round trips, shape and orientation;
- negative orientation tests;
- exact ICC preservation from a source TIFF;
- identical output pixels from direct AEL and bridge executions of both commands;
- unchanged source pixels;
- clear errors for a missing executable, missing AEL, an old Python and an old AEL (1.3.3 and an unreadable version are refused, 1.10.0 is accepted: versions compare as numbers);
- the interpreter detection with nothing chosen, from a clean saved-settings state and without `AEL_PYTHON`;
- paths containing spaces and accented characters;
- samples without data (NaN): the file PixInsight's writer makes has them as 1.0 (the control), the file the bridge hands to AEL has them as NaN again, and the structure image of a scene with a band, a block and a patch without data equals the one `python -m ael` makes from the file, while AEL on the file as PixInsight writes it gives three different images;
- a file with values outside 0–1 (which PixInsight rescales) and a file whose last sample is NaN (which it reads as black): the bridge runs AEL on the file itself, its structure image equals the one `python -m ael` makes from the file, and the file is left as it was;
- dialog and result images rendered by PixInsight.

`dialog_flow.py` builds both dialogs in PixInsight, fills their fields, presses **Run** and checks the windows and files each one leaves, the pixels against `python -m ael` and `python -m ael filters` from the terminal, the PixelMath composite, and that no message box appears. The same test on the previous dialog code fails: a geometry file typed but not loaded stopped the run, and the box "Generate all 16 filters" had no effect.

`entry_scripts.py` runs `AELBridge.js` and `AELWorkflow.js`, the two files that the Script menu starts, unchanged and each in its own new PixInsight instance, and checks that the dialog appears with its title, its Run button, its fields and the AEL folder that comes with the connector, then closes it with Cancel. The same check on a copy whose bridge entry has lost the include of its dialog fails (`ReferenceError: AELBridgeDialog is not defined`), so a broken entry file cannot pass. For a built package: `--plugin PACKAGE/pixinsight-ael --expect-root PACKAGE/pixinsight-ael/runtime`.

`VALIDATION.json` contains the gates and exact commands. A missing PixInsight executable or a failed gate makes the complete validation fail. `--skip-pixinsight` runs only direct AEL checks and is not a complete bridge validation. `--skip-captures` omits only the visual captures.

### Size and memory

`structure` was run through the bridge on a synthetic corona of 7,506 × 10,551 pixels (80 million, the size of the 2026 composites): 49 s from the click to the three result windows on an Apple-silicon Mac with 64 GB, and the three outputs equal those of `python -m ael` on the same file bit by bit (SHA-256). The peak was **30 GB of memory** (PixInsight with the image, plus the Python process that runs AEL; the terminal run alone peaks at 29 GB), so plan on that for images of this size. The filter workflow was not run at that size.

### When PixInsight does not hold the file as it is stored

PixInsight does not always read a floating-point TIFF faithfully. A file with values outside 0–1 is rescaled to exactly 0–1, `(x − min) / (max − min)`, so the view holds numbers that are not in the file; and a file whose last sample is NaN (no data in the bottom-right corner, which a registered stack often has) is read as a completely black image, with no message. AEL does not give the same result on those numbers (its structure image depends on the scale and on the zero: a plain ×0.5 changes 30,924 of the 786,816 samples of a test image).

A view that is still its file (not processed since it was opened) is therefore compared with it before anything is exported: the size, the count of samples with and without data, the smallest and largest value and the sum of the finite values must agree, and the file must not leave 0–1. If they do not, the bridge runs AEL on the file itself, as `python -m ael` reads it. It says so in the Process Console, and the receipt records the file, its SHA-256 and the reasons (`source.ael_input`, `source.file_reasons`, `input_file`). The file is never written or removed. An AEL stack (a `linear.tif` with values far above 1 and NaN outside its coverage) can thus be opened as it is, and the result is the one `python -m ael` gives on that file, which the tests check pixel by pixel. A view that has been processed since it was opened is exported, so AEL gets what you see. Only TIFF files are compared; an image from another format is exported. The workflow dialog is not affected: it reads its files from Python.

### Pixels without data (NaN)

AEL marks a pixel without data as NaN, and every stack that AEL writes has them outside its coverage. PixInsight keeps a NaN in the view but writes it to a TIFF as 1.0, so AEL would read a bright area where the file has none: on a real stack of 12 million pixels with 253,851 NaN samples, every sample of the three structure images differed from those that `python -m ael` makes from the file. The bridge therefore reads the positions of the view's non-finite samples and gives them to the helper, which puts them back as NaN in the temporary TIFF before AEL runs. The bridge receipt records how many there were and that PixInsight had written them as 1.0. With this, the same stack gives three structure images equal, sample by sample, to those of `python -m ael` on the file. Infinities are put back as NaN too (AEL takes both as no data).

## Automated linear-master and filter workflow

`AELWorkflow.js` adds **Utilities > AEL Linear Master and Filters**. Keep `AELWorkflowCore.jsh`, `AELWorkflowDialog.jsh` and `python/ael_workflow.py` beside the bridge files.

### Filter layers from an existing linear stack — validated

Select **Filter layers from linear.npy**. The helper finds `geometry.json`, `valid.npy`, `coverage.npy` and `alpha.npy` beside the input, measures a display scale from observed corona pixels, and generates all sixteen portable AEL filters by default (the box **Generate all 16 filters** unticked makes only AEL's default layers, read from `ael.filterbank.DEFAULTS`: NRGF, the edge-aware WOW and ACHF 04). It writes:

- float NPY layers and alpha arrays from AEL;
- separate 16-bit TIFF views `AEL_L_<filter>` and `AEL_A_<filter>`;
- `AEL_DISPLAY`, the display base over black with its alpha as a 32-bit float image, which is exactly where AEL starts its own composite, and an independent `AEL_COMPOSITE` duplicate;
- `pixelmath.json` and `PIXELMATH.md` with the expressions, which name the layer and alpha views directly (PixelMath symbols accept constants only);
- AEL and workflow receipts.

The default composite applies NRGF, the edge-aware WOW and isotropic ACHF 04 with their documented opacities, rounded to 8 bits as AEL and Photoshop store them. (Up to AEL 1.3.4 the default WOW layer was the bilateral one; `wow_bilateral` is still accepted as a name for the edge-aware WOW.) The other filters remain separate for manual use. PixelMath touches only the composite, never the display base or linear master, and a PixelMath run that fails stops the workflow. The synthetic validation starts from the display base and compares the PixelMath result with AEL's own composite (`ael/display.tif`); it also checks that the two starting images differ, so a PixelMath that changes nothing cannot pass. AEL composites in floating point from the 16-bit layer images and alpha and rounds once, at the end; the replay starts from the same float32 and so differs from `display.tif` only by that final rounding: 0.50 of a 16-bit step measured, gate one step. A layer with the wrong opacity (one 8-bit step) or the wrong blend mode, built in PixInsight, differs by about 150 and about 11,000 steps and fails the gate.

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

`tests/workflow_synthetic.py` passes all gates on AEL 1.3.6: 0.003 px worst translation error (gate 0.1 px), 0.0203% median relative master difference (gate 0.1%), sixteen filters and alpha maps, and a PixelMath composite within one 16-bit step of AEL's composite (gate `1/65535`; 0.50 steps measured). The unrelated-image registration control is rejected. `tests/workflow_dark_guard.py` checks the dark refusal. On a 24-megapixel synthetic frame, registration takes about 3 s without noise and about 10 s with short noisy exposures, a 26 px drift and a Moon moved 12.6 px (error 0.023 px; the structure check takes 0.5 s of it). Windows, Linux and real eclipse data remain untested; real frames add seeing, lunar relief, prominences and sensor patterns that the synthetic scenes do not have.

## Limitations

- **The registration on the Sun is not valid on real frames yet.** On real Vixen R6 III totality frames (2026-08-12, read without dark or flat), it lands 0.07–2.2 px from the reference registration (lunar limb plus the DE440s ephemeris, which an independent phase correlation of the corona confirms within 0.04–0.46 px), and up to 3.3 px at 10 s; the error grows with the time between frames. Frames of 1/500 s and shorter do not converge, and the structure check accepts frames registered 1–3 px wrong. The cause has not been found: neither the lunar margin, the outer radius, the weighting, pre-smoothing, a planar extinction term nor field rotation explains it. Do not use the automatic master on real frames.
- Tested only on macOS (Apple silicon) with PixInsight 1.9.4 and AEL 1.3.6. Windows and Linux have not been tested; the interpreter search lists Unix-style folders.
- Python must be installed separately (the package carries AEL, not Python or its dependencies); this is not a native C++ module.
- `structure` and `polar` are covered by the original bridge. The complete master/filter workflow is validated with synthetic data only; real eclipse data require separate validation.
- The automatic master holds every frame's luminance in memory at once: plan on several gigabytes for dozens of full-size RAW frames.
- ICC profiles are read from the source file and copied unchanged to the temporary TIFF. An unsaved image, or a profile assigned only in memory after reading the file, cannot be verified or preserved reliably by this prototype. The receipt records the ICC origin and byte counts.
- `polar` expects display-range data in [0, 1]. `structure` expects a linear composite with valid geometry and enough outer field for its sky model.
- The connector has not been signed or packaged for automatic updates.
