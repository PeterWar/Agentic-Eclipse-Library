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

## Limitations

- Tested only on macOS with PixInsight 1.9.4. Windows and Linux have not been tested.
- Python must be installed separately; this is not a self-contained package or a native C++ module.
- Only `structure` and `polar` are in scope. Other AEL commands are not exposed.
- ICC profiles are read from the source file and copied unchanged to the temporary TIFF. An unsaved image, or a profile assigned only in memory after reading the file, cannot be verified or preserved reliably by this prototype. The receipt records the ICC origin and byte counts.
- `polar` expects display-range data in [0, 1]. `structure` expects a linear composite with valid geometry and enough outer field for its sky model.
- The connector has not been signed or packaged for automatic updates.
