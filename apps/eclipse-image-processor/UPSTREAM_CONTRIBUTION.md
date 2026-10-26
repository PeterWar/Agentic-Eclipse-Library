# Desktop application contribution

This directory contributes Eclipse Image Processor 0.6.0 by Francisco Bitto as an optional standalone desktop application. Source snapshot: [fbitto/Eclipse-Image-Processor, commit 46ec785](https://github.com/fbitto/Eclipse-Image-Processor/commit/46ec785).

## Scope

The application uses Python 3.14+, PySide6, NumPy/SciPy and the dependencies in its own requirements files. Run installation, launch, tests and packaging commands from this directory, not from the AEL repository root. Its top-level `core`, `gui`, `config` and `utils` imports assume that working directory.

The contribution includes runtime code, filter tests and synthetic fixtures, development/validation/build tools, documentation, icons and existing illustrative screenshots. Local editor/agent configuration and machine-specific skill locks are excluded. Two private reference-PDF paths in a historical design note were generalized; pre-existing trailing whitespace was normalized in the contributed copy. No private astronomical source data, FITS masters, exported TIFF/PSB files, virtual environments or build products are included. Real-image validation described in the documentation cannot be reproduced without separately supplied private data.

The application retains independent implementations and bundled AEL 1.3.3 adaptations; it is not a refactor of AEL's current engine or a wrapper around its public API. Numerical deduplication and shared API integration would be follow-up work agreed with the maintainer. GUI defaults are application choices, not proposed changes to AEL defaults. Rendering is for visualization, not calibrated photometry.

## Validation

Run the application suite in a separate environment containing its requirements:

```bash
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
```

Windows requires the equivalent PowerShell environment syntax, or a desktop session. See [validation evidence and limits](docs/validation.md). Previously recorded real-data and Photoshop checks remain dated evidence; the current automatic presentation/hidden-reference combination has not been revalidated in native Photoshop. No new Windows/macOS standalone build or signing/notarization check accompanies this contribution.

On this contributed snapshot, the application suite passed 296 tests in 125.385 seconds using offscreen Qt in the existing macOS development environment. Upstream `python -m ael selftest` passed 84/84 with zero skipped checks. These checks do not establish native Photoshop compatibility or astrophysical validity.

## Ownership and licences

The application remains copyrighted by Francisco Bitto under its included MIT licence. Original AEL copyright and MIT notices are retained for the adapted filters, presentation curve and low-level PSB writer; see [ATTRIBUTIONS.md](ATTRIBUTIONS.md). Other third-party authorship and method references remain intact. This contribution does not transfer ownership of AEL or imply maintainer endorsement or scientific validation.
