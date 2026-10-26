# Validation and evidence boundaries

Updated 26 October 2026. Test counts describe a particular checkout, not a permanent feature guarantee.

## Automated checks

From the project root with runtime dependencies installed:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests -v
```

On Windows set the environment variable using PowerShell syntax, or run with a desktop session. The complete suite passed **296 tests** in 135.824 seconds on the local macOS development environment during this documentation update. After updating the generated layer-package documentation text, all nine layer-export tests also passed.

Coverage includes numerical independent references and AEL fixtures, missing/statistical support, native/preview scaling, independent layer inputs/order/blends, bounded caches, cancellation, colour preparation, export separation, PSB structure/bytes, optional Color Correction, JSON v4 validation, GUI interaction/responsiveness, zoom and overlay painting. It does not establish astrophysical truth or pixel identity after native Photoshop recomposition.

## Real-image validation tool

Inspect the current options before running:

```bash
.venv/bin/python scripts/validate_real_image.py --help
```

For example, with a source file and an output directory that does not yet exist:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/validate_real_image.py /path/to/master.fits /path/to/new-validation-directory
```

The tool loads supported image input, exercises filters/combined output and writes validation artifacts to the requested output location. Use a separate output directory, keep source files unchanged and retain the generated measurements alongside exact settings and environment versions. Large native runs can take significant memory and time.

The most recent full real-data cleanup check used a 5608 × 3744 RGB float32 FITS with 273,060 missing pixels. Native and reduced tests exercised eight filter families and combined output; the source-file hash remained unchanged. The GUI-produced RGB16 TIFF matched the expected un-stretched composition pixel for pixel. The native JPEG differed from its expected floating presentation by mean absolute error 1.9881 levels on an 8-bit scale, consistent with lossy storage. Layer export was disabled in that check: it supplies no current native PSB/Photoshop evidence.

After the latest UI changes, 56 focused tests passed for interactions, image painting and responsiveness. Offscreen synthetic captures of Disk overlay on/off confirmed the circle and cross toggle together, without numerical recomputation, and reset visible when loading an image. These captures do not substitute for testing every native desktop/display configuration.

## Historical and unperformed checks

Earlier native Photoshop 2026 tests are preserved in [PSB validation history](psb-validation-history.md) and the [colour-correction report](propuesta-color-atardecer-psb.md). Their measured layer/pixel results belong to those older exports. Current automatic exposure/hidden-reference output has structural automated coverage but has not been opened and recomposed in Photoshop for this revision.

The [19 October filter report](filter-validation-20261019.md) and [21 October performance report](performance-optimization-20261021.md) retain historical datasets/timings. They are not benchmarks of the current full pipeline. No new performance benchmark, Windows/macOS package build, signing/notarization, external scientific-link check or native Photoshop run was performed for the documentation update.
