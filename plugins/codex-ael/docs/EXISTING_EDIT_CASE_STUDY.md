# Keeping an existing eclipse edit while adding adjustable detail

This presentation case study uses an independent FRA400 and variable-focal-length
camera data set, without darks or flats. It concerns an edited RGB Photoshop
document, not calibrated radiance or a new RAW stacking method. It refines the
initial report in [issue #1](https://github.com/PeterWar/Agentic-Eclipse-Library/issues/1).

Measurements were checked against retained local receipts. Photographs, RAWs,
pixel arrays and native Photoshop files are not published here; these measurements
cannot be reproduced from this repository alone. The [aggregate receipt](case-studies/existing-edit-summary.json)
includes negative results. It is not a test fixture or an uncertainty budget.

## What was already covered

[DEVELOP.md](DEVELOP.md) already distinguishes geometric coverage from saturation
weights, requires measured registration, removes a smooth radial profile before
isotropic filtering, and separates a PSB roundtrip from a native Photoshop check.
Historical artefact and earthshine notes already warn about radial rings and limb
seams. This case adds a workflow for a preferred existing edit whose scale differs
from the base and filters, rather than another general ring correction or earthshine
reconstruction.

## Two different requests

Recomputing detail directly on a preferred edit can preserve its appearance without
aligning it to another document. That was aesthetically useful here, but the
photographer subsequently needed each existing filter's opacity to work against
the same base. A Normal layer with enhancement baked into it did not meet that request.

For the second request, declare the reference geometry and layer contract first:

1. Preserve the input and manual layers; work in a new document.
2. Keep a copy of the reference base below the aligned preferred edit.
3. Put each aligned filter above it, with its intended blend mode and independent
   opacity. Check the controls in Photoshop, not only the layer records.
4. When retaining the preferred look is the initial goal, start the added filters
   at zero opacity. This is optional, not a change to AEL's default filter recipe.

The result had 24 layers: 17 retained layers, a base copy, an aligned preferred edit
and five filters. ACHF/MGN/WOW used Overlay; NRGF/RHEF used Multiply. Each filter was
previewed independently at 20% with the others at zero, then all were restored to
zero. These values describe a UI check, not recommended strengths.

## A filter mask is not a measured lunar edge

The filter mask's half-alpha radius was about 500.65 px, against a fitted visible
reference edge radius of about 505.56 px. Using the mask to guide the preferred edit
gave the wrong disk size. Refitting the visible edge on rendered pixels gave
differences of about 0.075 px in centre and 0.035 px in radius.

These are differences between fitted parameters, not sub-tenth-pixel accuracy of
the entire limb: candidate edge-profile residual MAD was about 0.526 px. The fit
used a logistic edge of explicit width, decaying corona and local pedestal on this
edited document. It does not replace `ael.geometry.fit_limb` on linear data or
measure the physical lunar surface. Record mask support, displayed edge and
ephemeris limb separately. PSF and tone processing are possible explanations;
their individual contributions were not established.

## Good disk agreement did not prove coronal alignment

A common affine corrected the filters' small scale mismatch to the base. ACHF/MGN
used even angular sectors for fitting and odd sectors for validation in six radial
bands. Maximum held-out p90 was about 0.312 px. A co-located operator control gave
maximum p90 0.2123 px; a known-affine injection gave 0.0483 px. This helped rule out
operator bias as the explanation for the earlier roughly 4–6 px mismatch. NRGF/RHEF/WOW
inherited the common geometry; ACHF/MGN texture checks do not independently validate
those three operators.

The preferred edit used a separate affine plus smooth thin-plate-spline warp, with
regularisation selected by cross-validation within training data. The frozen
held-out p90 limit stayed at 1 px. Direct checks on rendered pixels gave:

| Radius, reference pixels | Phase p90, px | ECC p90, px |
| --- | ---: | ---: |
| 550 | 0.9521 | **1.1278 — fail** |
| 600 | 0.8154 | 0.7292 |
| 660 | 0.5336 | 0.5350 |
| 760 | 0.6258 | 0.5617 |
| 1100 | **1.0947 — fail** | 0.6266 |
| 1450 | **1.3036 — fail** | 0.8692 |

ECC used the same pixels: it was an alternative estimator, not an independent
instrument or exposure. Wider windows did not erase these failures; one wide-window
band still failed at 1.0210 px. The result remained **CANDIDATE: global alignment
failed**. A good disk fit or visual approval does not establish perfect full-field
registration. Optical differences, timing and edits are hypotheses for residuals,
not individually proven causes. This presentation warp is not a calibrated
inter-instrument distortion model for `ael stack`.

## Preserve pixels, support and the meaning of each check

The existing filter RGB channels were not exactly equal. Resample all three actual
channels using the same map; do not silently reduce an imported colour layer to grey.
This concerns transport of existing layers, not computing ACHF separately per colour
channel. One bilinear interpolation with premultiplied alpha and transparent exterior
retained observed support without reflected or invented texture in this case.

The canvas stayed 6106 × 4078. Transformed layers retained off-canvas pixels in
their bounds, including negative coordinates, using a custom case writer.
`ael.photoshop.add_layer` currently requires full-canvas arrays; this note does not
claim its public API supports off-canvas layer bounds.

A native save to a new path preserved every decoded channel of the 17 retained
layers and base copy exactly relative to the premount. Layer metadata and ICC
matched; the old unaligned edit was hidden only in the copy. New RGBA and flattened
cache changed by at most 1 DN16, within the 2 DN16 tolerance declared before saving:

- retained manual/base pixels: pass;
- native numerical compatibility within the declared tolerance: pass;
- exact new RGBA/cache identity: **fail**;
- perfect full-field alignment: **fail**.

Compare decoded channels, alpha, bounds, modes, opacity and ICC after a native save.
A different recompressed file hash alone does not show pixel loss. A reader accepting
a PSB does not show that its controls or native appearance work. Keep the float
linear input as HDR authority: Exposure 0/Gamma 1 in a conversion dialog does not
prove that a preferred 32-bit preview survives 16-bit tone mapping. Earthshine
remains limited to measured support; filling a disk does not validate previously
unmeasured lunar detail.

Processed with Agentic Eclipse Library by Pere Guerra — https://github.com/PeterWar/Agentic-Eclipse-Library
