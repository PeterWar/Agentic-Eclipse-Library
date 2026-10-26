# Background gradient extraction

The optional Background Gradient section is off initially and available only for input declared linear. It equalizes a first-order sky gradient while retaining the fitted mean sky level. It does not subtract a constant background or neutralize a colour cast.

## Selecting samples

The initial 16 × 16 grid excludes six reference lunar radii. This is an adjustable starting point; faint corona can extend into the sample field. Review green sample squares and the dashed yellow exclusion circle. In sample-edit mode, left-click adds a point, right-click removes a nearby point and middle-drag pans. Changing grid density or exclusion radius regenerates samples. A new image receives new samples; JSON preserves explicit native-pixel coordinates.

Each patch has half-width `max(2, min(32, int(min(height, width)/200)))` native pixels. The whole square must clear the circular exclusion (using its half diagonal). At least 90% of patch pixels must be finite and nonzero; an RGB pixel is nonzero if any channel is nonzero. Patch medians provide the fitted values.

## Robust plane

`core/background.py` fits `a + b*u + c*v` per channel, with pixel-centre coordinates `u = 2*(x+0.5)/width - 1` and corresponding `v`. At least six accepted samples, a 0.4 span on each normalized axis, rank three and condition number at most 1e6 are required.

Twelve robust IRLS iterations use Tukey weights with cutoff 4.685. RGB channels share sample weights; per-channel MAD scales have relative/absolute floors. The fitted slopes are subtracted relative to the weighted sample centroid. The constant sky level at that anchor is retained. A first-order model intentionally cannot remove curved illumination patterns.

Correction is tiled in 128-row strips. Missing values and zero-filled regions retain their support and storage behaviour; negative corrected floats are permitted. RGB correction precedes mono recomputation. The native corrected working source, normalization bounds, calibration, filters, presentation and exports share this result; fast preview reduces that prepared source.

## Reproducibility and limits

The source arrays are unchanged and used again when correction is disabled. Recipes record coefficients, anchor, counts, inliers, RMS, patch size and exclusion radius. Reopening a JSON loads the original source and applies its correction once. Do not use an already corrected exported TIFF as the original source for that recipe.

No robust estimator can reliably distinguish smooth faint corona from background when all sky samples are contaminated. Reject problematic samples and inspect native results. This correction is not a flat-field calibration or photometric sky measurement.

The design was informed by [Siril background extraction](https://siril.readthedocs.io/en/stable/processing/background.html) and [Seti Astro ABE](https://github.com/setiastro/setiastrosuitepro/blob/main/src/setiastro/saspro/abe.py); the application uses its own restricted plane model and slope-only subtraction.
