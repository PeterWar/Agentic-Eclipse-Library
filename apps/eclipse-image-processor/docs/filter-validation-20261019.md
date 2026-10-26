# Filter validation on Prueba.tiff — 2026-10-19

> Historical report. This document preserves its original research, measurements and implementation context. Controls, defaults, sequential processing and export behaviour described below may have changed. Use the [current technical guides](README.md) and [validation boundaries](validation.md) for the active application.

Later implementation and updated validation: [filter controls and implementation checks](filter-controls-20261019.md). This document records the preceding review.
The numerical suite passes after correcting one masked-WOW overflow. Visual acceptance is **not complete**: FNRGF produces conspicuous circular bands with the tested settings, and standard WOW has a large preview/full-resolution difference. Passing arithmetic and integration checks does not certify artifact-free enhancement or quantitative scientific validity.

## Input and environment

- User-selected `Prueba.tiff`: 2750 × 2084 RGB, uint16, no nonfinite samples.
- SHA-256 before and after: `8438909c59b29596a8f98257a4c2f20aac87f6ace62545e2ef56d8f244191f2a`. The source was not modified.
- One channel sample reaches 65535; 736,273 channel samples are zero. These counts alone establish neither physical saturation nor missing-data semantics. Zeros remain observed values.
- Processing luminance is float32. The application's actual loader and parameter collector were used, with a 1500 × 1136 preview.
- Detected geometry: x=1366, y=1042, radius=279 full-resolution pixels. The circle visually follows the image limb; this is not independent solar astrometry.
- Python 3.14.8; NumPy 2.5.4, SciPy 1.18.1, OpenCV 5.0.0.93, PySide6 6.12.0, tifffile 2026.10.15, watroo 0.0.4.

## Automated tests

The original 98 tests passed. Treating RuntimeWarning as an error exposed an additional failure in an existing constant-image/mask test. After the correction and six new test methods, **104 tests passed in 5.617 seconds**, with RuntimeWarning treated as an error.

Existing coverage includes numerical references for MGN/FNRGF/RHEF, continuous RHEF quantiles and injected rings/detail, WOW backend comparisons, filter boundaries and extreme intensity units, masks, pipeline ordering, Qt worker interactions, display blending, colour, source exports and Photoshop layer reconstruction.

The added checks use:

- A scalar ACHF implementation that explicitly accumulates the local weighted mean, independently of production vectorized residual accumulation. Cases include singleton axes, borders, region boundaries, thresholds, fractional support and spatially scaled minimum Gaussian width.
- Direct Gaussian convolution for USM, with explicit symmetric boundary padding and clipping.
- Scalar Asinh/logarithmic formulas on signed input.
- Masked bilateral-starlet constant-input checks with arbitrary missing buffers, including NaN, and floating-point overflow/invalid/divide errors enabled.
- A scalar 25-tap bilateral-starlet reference with missing neighbours, three step sizes and three bilateral parameters.

### Corrected defect

`MaskedWorker.starlet_blur` divided differences involving missing transport buffers by an effectively zero bilateral sigma on a constant observed image. This emitted overflow warnings even though later zero weighting often hid the problem. The correction excludes unobserved pairs before arithmetic, bounds Gaussian distances before division (40 sigma already has zero Gaussian weight in float64), and avoids multiplying zero weights by missing NaNs. Scalar-reference tests verify the observed output remains correct. This is the only production filter change in this audit.

## Real-image checks

Thirteen configurations were run at both preview and full resolution: the nine isolated stages, logarithmic pre-stretch, continuous RHEF, bilateral WOW with denoising, and the combined pipeline. Isolated enhancement stages used Strength 100%; the combined stress test used Strength 10% per enhancement stage. Pre-stretch used its collected GUI value. This is a diagnostic stress test, not a recommended processing recipe.

All 26 principal results had the expected shape, finite output and no RuntimeWarning. For each isolated enhancement configuration, Strength zero preserved pixels exactly at both resolutions. Preview runs additionally verified exact repeatability and the 37% linear blend against the full-effect result. FNRGF and both RHEF modes preserved pixels inside their application radii. The source/preview arrays and source-file hash were unchanged.

Eighteen extra comparisons used outer-corona, limb and lunar-disk crops of the actual image: MGN core matched the independent test transcription exactly; standard/bilateral WOW with and without denoising matched the installed backend plus documented presentation mapping exactly; scalar ACHF matched within rtol=2e-6, atol=2e-5 (largest absolute difference 3.81e-06). The MGN oracle is a separate transcription, not an installed sunkit-image comparison. WOW's backend comparison verifies wrapper integration, not an independent derivation of watroo's mathematics.

### Preview versus full resolution

Full output was area-reduced to preview dimensions and compared with directly processed preview data. The following metric is RMSE divided by the full input luminance range (31207.24 units), expressed as a percentage. These are measurements at the tested settings, **not correctness thresholds**. Gaussian sampling, rank populations, global range mapping and dyadic wavelet support can all change results across resolutions.

| Configuration | Normalized RMSE | Full-resolution seconds |
| --- | ---: | ---: |
| pre_stretch | 0.0690% | 0.06 |
| noise_gate | 0.0040% | 0.30 |
| bilateral | 0.0200% | 0.11 |
| fnrgf | 5.3734% | 0.70 |
| mgn | 3.5477% | 3.54 |
| wow | 17.9873% | 1.83 |
| rhef | 4.0673% | 0.62 |
| usm | 0.1069% | 0.09 |
| achf | 0.0749% | 5.99 |
| pre_log | 0.0833% | 0.04 |
| rhef_continuous | 4.0727% | 1.97 |
| wow_bilateral | 1.1288% | 4.88 |
| combined | 1.6263% | 16.23 |

Standard WOW used no denoising and 8 preview / 9 full-resolution scales. Its observed median output changed from about 10533.5 to 5259.7 input units. The bilateral WOW case also enabled [1, 2, 3] denoising thresholds, so its smaller difference cannot be attributed to bilateral mode alone. Automatic input/output range mapping and scale selection merit further investigation; this audit does not identify a unique cause or change them.

### Visual observations

All montage panels use the same source intensity limits and Asinh factor 100; no individual panel normalization hides brightness differences. Signed numeric outputs are retained separately, before display clipping.

- FNRGF has clear concentric bands and outer-frame discontinuities. Related bands remain visible in the combined stress test. This configuration is **not visually accepted** for the supplied image. No causal correction for these bands was attempted.
- MGN/WOW enhance background texture/noise and modify finite lunar-disk values. They do not automatically exclude the Moon; this is not evidence of recovered lunar detail.
- RHEF strongly lifts the background at 100% Strength. Both legacy and continuous modes preserve the application-radius interior but remain resolution-dependent.
- ACHF produced 2813 negative output pixels at full effect. Its signed detail output is intentional; the montage clips negative values for display. Numerical files retain them.
- The full-canvas inspection does not prove absence of small limb artifacts. No independent exposures, raw calibration frames or ground truth were supplied.

## Actual GUI export

The real GUI export action was exercised headlessly with this RGB image and MGN + USM at 10%. The TIFF is 2750 × 2084 × 3, uint16, and matches the expected presentation pixels exactly. The companion JPEG has the same dimensions, with mean absolute error 1.430 on the 0–255 scale relative to the pre-JPEG RGB buffer. TIFF and JPEG colour order was checked.

The expected export uses the shared numerical/presentation functions, so this validates export integration rather than independently establishing the filters' formulas. Photoshop layer export and linear-source export were covered by synthetic integration tests, not repeated on the full real image. Native Photoshop rendering and interactive desktop operation were not verified.

## Reproduction and local artifacts

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -W error::RuntimeWarning -m unittest discover -s tests -v
QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/validate_real_image.py /path/to/Prueba.tiff /path/to/new-output-directory
```

The opt-in image runner refuses an existing output directory and never writes to the source. Principal artifacts from this run are in the ignored local directory `.cache/filter-validation-20261019/`:

- `tests.log` and `tests-before-fix-strict.log`: successful final suite and original strict failure.
- `real-image.log`, `results/measurements.json`: execution log, source hash, effective recipes, timing and error measurements.
- `real-reference-comparisons.json`: the 18 crop-reference measurements.
- `results/comparison.png`, `results/geometry.png`, `results/preview-export-comparison.png`: full-canvas montage, fitted-limb witness and FNRGF/WOW resolution comparison.
- `results/*_numeric.tiff`, `results/*_preview_numeric.tiff`: full/preview float32 filter outputs.
- `results/actual_gui_export.tiff` and companion JPEG: actual GUI export.

These local images are not intended for version control. The original README edits from the preceding task were preserved.

## Remaining validation limits

No installed sunkit-image environment was available, and no new external scientific-reference audit was performed. Mathematical equivalence is limited to the references and cases tested. FNRGF visual bands and standard WOW resolution consistency remain open findings; they should be investigated before claiming overall visual acceptance. The test suite does not establish photometric accuracy, true coronal structure or scientific measurement validity.
