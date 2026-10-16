---
name: eclipse-calibration-stacking
description: Calibrate and stack total solar eclipse RAW, Bayer or linear RGB data using measured registration, calibration, saturation and geometric coverage.
---

# Calibrate and stack

Read [setup and operating instructions](../../docs/USAGE.md) before running AEL. Resolve this plugin's root from this skill file and use its bundled launcher. Respond in the user's language. Work on user-selected inputs and write new output directories.

Read [stacking and extinction recipes](../../docs/DEVELOP.md) and the template at [stack_config_template.json](../../examples/stack_config_template.json). The CLI executes a declared recipe; registration and calibration must be measured beforehand.

- Group by optical train and ISO. Check exposures against metadata and sequence, totality membership, black/white levels and the mosaic's two green planes. Use matched darks/flats if supplied; never invent a flat or call an unvalidated response fit a calibration.
- Preserve linearity: subtract black, apply declared calibration and channel ratios, and avoid gamma or a raw-converter tone curve. Measure the linear ceiling. Separate geometric coverage from saturation/exposure weights.
- Register the corona in the solar frame. The moving Moon is not a fixed registration target. Preserve manual lunar geometry. Reference-to-input affines map native pixel centres; do not add a second half-pixel offset. Correct each optical train's distortion before fusion.
- Keep the user's chosen full canvas. Record a reference or union canvas explicitly; do not choose a crop to hide coverage boundaries. No extrapolation or reconstruction where every exposure clips.
- Statistical hot-pixel rejection requires supported dithering. Clouds require measured spatial transmission/background maps frozen before testing and independently fitted for independent witnesses; one scalar per frame is insufficient.

Run `stack --config RECIPE --out NEW_DIR` through the launcher. Check the linear result, coverage, support, weights, alpha and geometry at the limb and all boundaries. Keep input hashes and the receipt. The package's variance model is not a complete photometric uncertainty budget.

For differential extinction under a low Sun, read the extinction section and [template](../../examples/extinction_config_template.json). Subtract the sky and use a measured extinction coefficient on the linear stack; sky/extinction degeneracy must be declared. Rebuild dependent layers. See [field lessons](../../docs/FIELD_LESSONS.md) for failed controls and limitations.

