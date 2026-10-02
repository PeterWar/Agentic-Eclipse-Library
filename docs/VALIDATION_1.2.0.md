# 1.2.0 validation — 2026-10-03

This is a local release candidate, not a publication record.

## Software checks

- 27/27 known-truth tests passed, no skips, from the built wheel installed outside
  the repository. Dependencies were reused from a local Python 3.12 environment;
  this was not a test of every supported dependency version or operating system.
- The installed `ael filters` command produced all sixteen variants, a preview,
  a receipt and a 19-layer 16-bit PSB from a synthetic fixture.
- The new fixture opened in native Photoshop: **240 x 180, 19 layers, 16 bits**.
  Only the fixture opened by the check was closed; document count before/after: 0/0.
  psd-tools compared layer pixels/properties; the system image reader also returned
  the correct dimensions. Native opening proves readability, not scientific accuracy.
- Regression controls cover CFA/affine half-pixel shifts, saturation shared between
  colours, geometric support independent of tapers, persistent hot pixels with local
  noise, hot pixels not killing valid neighbours, smooth radial subtraction with an
  off-centre Moon, no data invention, matched Multiply alpha, two-band cloud weighting,
  invalid parameters and refusal to overwrite output directories.
- Existing motion, polar, structure, Photoshop and animation tests remain included.
  The previously failed mixed-instrument grain threshold remains unchanged.

## Real data integration

- Ten Canon CR2 totality frames, frozen coronal registration and measured black/white
  levels: the stack command produced a full union canvas of **5641 x 3711** pixels,
  linear TIFF/NPY, valid/support/geometric coverage maps, alpha and hashed receipts.
  The first three filters were also run on the native canvas and visually inspected.
  A later hot-pixel taper correction was checked in a second RAW stack and a targeted
  regression. The test does not reconstruct the saturated inner corona.
- The isotropic ACHF was run on an existing, frozen ARW-derived 2024 master at
  **6095 x 4035**, with an off-centre Moon. Two explicit display settings were
  inspected; the first clipped the inner display strongly and remains a negative
  diagnostic. This is **not a RAW-to-final replay** of the earlier 2024 processing,
  nor a validation of newly fitted cloud corrections.

Real photographs and detailed private receipts are not part of the public package.
The full-field Canon preview shows low-coverage sensor boundaries and noise, while
saturated pixels remain missing. Those observations are recorded rather than promoted
as a finished photograph or an artefact-free result.

## Limits retained

Registration, true camera linearity, geometry, colour calibration and spatial cloud
corrections are inputs that must be measured. The two-band variance is a weighting
model, not a complete propagated uncertainty budget. These general-purpose filter
variants differ from historical manually tuned operators (see `DEVELOP.md`).
No new independent astronomical validation, automatic end-to-end scientific approval,
or fresh-agent usability trial was performed. No Git push, tag or release was made.
