# Field lessons in 1.2.1

A nine-exposure RAW processing case exposed two reproducible software defects and several
limits that the software must state. This note contains no private photographs or camera
identifiers. The portable tests use synthetic scenes with known truth.

## White inner corona: identify the stage that clips

A bright displayed region is not evidence that every RAW saturated. Compare the shortest
frames, per-frame saturation taper and contribution weights, linear HDR and display output.
The 1.2.0 asinh display hard-clipped positive RGB at one; this could erase differences that
were present in the HDR. Version 1.2.1 applies a shared exponential shoulder after asinh,
with a declared ceiling below one. It does not recover saturated RAW data or alter the stack.
The hidden reference has a separate recorded scale so its positive range fits in 16 bits.
Negative colour-matrix values cannot be represented there; the signed float input is authoritative.
A software test checks actual PSB layer pixels, ordering of bright values and the display receipt.

## Gramophone grooves: do not assume the flat or the filter is innocent

Trace the defect through individual frames, calibration, HDR weighting and filter outputs.
The 1.2.0 NRGF and RHEF operators could produce coherent two-pixel rings on an input without
radial rings: an independent histogram or a mean/spread lookup for each annulus has boundaries.

- NRGF now evaluates mean and spread continuously at the pixel radius with PCHIP. Statistics
  come from populated annuli at their measured radial coordinates. Gaps remain undefined.
- RHEF interpolates 257 measured log-intensity quantiles in radius and angle, then inverts
  that monotone distribution. Tied/constant samples and sparse support are checked explicitly.
- Neither remedy spatially smooths the photograph. Both operate on the full observed rectangle.

The tests keep the actual old operators as negative controls. With frozen thresholds, a
seeded angular injection must retain at least 90% of the old response and the coherent
period-two amplitude must fall below 10% of the old value. These are bounded regression
checks, not a claim that all possible rings or calibration artefacts are gone. Local RHEF
may change contrast; review the resulting layers before adjusting opacity on an existing image.
An earlier overlapping-CDF pilot reduced injected detail by 14–31% and was rejected.

## Dust: an internal response estimate is a hypothesis

Use matching flats from the same optical configuration when available, divided before
registration. A flat from a different camera, focus or dust state does not qualify.
Without flats, test whether sensor-coordinate shadows move relative to the sky across
exposures. A fixed artefact can cancel in frame differences; agreement between frames
is not automatically an independent witness.

In the field pilot, templates measured in one set of green photosites were tested against
scene-registered exposure differences. A holdout using short exposures was too noisy:
0 of 24 candidates passed. That negative was retained. A separate check using the other
green photosites accepted 8 candidates, with zero accepted among 300 displaced controls;
red and blue were checked as well. The inferred response was applied before stacking.
The local background model, small pointing shifts and correlated RAW compression limit
this inference. It is not an externally measured flat or a general calibration algorithm.

At those eight locations the measured RAW-domain shadow decreased by 57–96%. The final
filtered image still showed residual shadows/halos and abundant other dust. **That range
is neither a whole-image removal percentage nor a measure of perceived cleanliness.**
The experimental fitter is deliberately not enabled as a production dust-removal command.
Freeze candidates and thresholds, hold out data, retain negatives, check colour/noise gain,
look at the native composite and report remaining dust. Do not replace the sky under a
mote with a smooth model, clone another patch or hide it with a final-image correction.

## Metadata, colour, geometry and the Moon

- Exposure filenames can disagree with recorded durations. Inventory metadata and verify
  the exposure ladder before dividing by time; report any disagreement.
- Ask whether the camera was astromodified. Measure colour ratios in linear data, inspect
  the Bayer sites and record the assumption used. Do not copy white-balance multipliers
  between cameras or call a neutral-corona assumption absolute spectral calibration.
- Preserve the agreed canvas. `stack.canvas: "reference"` fixes the full reference rectangle;
  `"union"` retains the full transformed footprint union. Both keep observed sampling and
  gaps explicit. Changing the field of an existing image requires the owner's decision.
- Corona registration and lunar registration are separate. Earthshine must have its own
  observed source, limb and support. Compare possible texture with detector-fixed patterns
  and scattered coronal light. Supply an explicitly labelled hidden candidate if useful;
  a failed relief check is not proof that the lunar signal is zero.

## Low Sun: sky and extinction are degenerate (unreleased)

This lesson comes from the author's 2026 data (Sun about 9° high), not from the nine-exposure case.
Across a corona photographed through 5.75 to 6.39 air masses within two solar radii, the
horizon side is dimmer and the zenith side brighter than the Sun's own line of sight. A global
colour vector cannot correct that; it was declared in the processing chain and never applied
to the image. The cure belongs to the linear stack, after the sky is subtracted, followed by a
rebuild of every filter layer (`ael extinction`, `docs/DEVELOP.md`).

- **Measure `k` on its own.** The corona dimmed by 4–6 % between second and third contact,
  multiplicatively and uniformly in azimuth, while the Sun's air mass rose from 6.02 to 6.20.
  Same-exposure pairs gave 0.402 ± 0.036 mag per air mass. Pairs only seconds apart carry too
  small an air-mass change to say anything and were left out.
- **The sky absorbs what the model lets it.** A sky plane fitted on uncorrected data takes the
  extinction dipole of whatever corona remains in the fitting region as a sky gradient. A
  constant sky estimated a few solar radii from the Sun contains corona; the correction then
  amplifies the over-subtraction on the horizon side. A joint fit of sky, corona and `k` was
  degenerate on these data and was kept as a negative result.
- **Use the correction as a consistency test.** Against a space coronagraph, the uncorrected
  dipole pointed within a few degrees of the zenith. The `k` that cancelled it ring by ring
  depended on the sky model, falling outwards with a plane fitted beyond 8 R☉ and rising
  outwards with a constant sky. The adopted wording became a consistency test conditional on
  the sky plane, not an independent measurement of `k`.
- **A pass is not proof of the level.** In the synthetic tests, a plane fitted on a corona tail
  and the same tail raising the sky level compensate in the dipole: the gate passes while the
  level is 7 % low at 3–4 R☉ and 15 % low at 4–5 R☉. Estimate that bias by passing a corona model
  through the same sky fit, and declare it.
- **Keep `X_ref` explicit.** Bring every pixel to the air mass at which the photometric zero
  point was evaluated; with k = 0.40, an error of 0.03 in `X_ref` moves the whole level by 1 %.

## Deliver and describe the actual file

Rebuild every dependent product when a source calibration or operator changes. Preserve
manual masks and alignments, old files and the negative pilot. Compare the delivered layer
pixels with their producers; never call a new layer above an old defect a causal repair.
For native Photoshop checking, use a uniquely named copy, verify it is not already open,
close only the script-owned document and save exports as copies. Check the native render
as well as merged file data. Report method, file integrity and visual/scientific validation
as separate verdicts; a passing roundtrip is not a scientific certification.
