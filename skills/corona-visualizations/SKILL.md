---
name: corona-visualizations
description: >-
  Make the three modern products of a total-solar-eclipse corona from linear data with the Agentic Eclipse
  Library's runnable package `ael`: Druckmüller-style STRUCTURE images (mono, cool-toned, or in the data's own
  measured colour), UNROLLED polar views of the corona around the Sun or the Moon, and CORONAL-MOTION
  analyses and animations from exposure ladders repeated during totality — each with its gates (nothing
  invented, noise measured per scale, sensor-fixed and Moon-fixed false motion rejected, visual check) and a
  receipt — and the MOTION GIF in the reference look without "waves" (one or two cameras, same recipe and same
  grain in every frame, arrows where two independent series see the same change). Use it for "structure
  image", "Druckmüller look", "fine filaments", "unrolled / polar / panoramic corona", "coronal motions",
  "animation like …", "motion GIF", "blink", "motion vectors", "does the corona move", "waves / rings in the
  animation", or to judge such a product made by someone else.
---

# Corona visualizations with `ael`

The package lives at the repository root (`ael/`, `pyproject.toml`) of
https://github.com/PeterWar/Agentic-Eclipse-Library; in the author's project it is `3-RECERCA/tools/ael/`, and
the scripts that made the 2026 products are in `3-RECERCA/tools/ael_2026/` (`p0`–`p4`).

**Read this whole file before running anything.** Then run `python -m ael selftest` (17 tests with known
truth; each gate has a negative control). If a test fails, stop: the environment is not the one this was
validated on.

## 0 · Five rules that are not negotiable

1. **Nothing invented, nothing mirrored.** Every pixel of a product comes from observed data. Where there is
   none, the product is `NaN`/transparent/black and you say so. No inpainting, no continuation, no
   interpolated frames between epochs of an animation.
2. **Declare what is designed.** The structure image replaces the radial fall-off with a display profile
   `B(r)` and may add a cool tint: both are presentation choices, written in the receipt; put them in the
   caption ("radial gradient compressed; colour of the sky is a display choice").
3. **Measure, don't assume, the noise.** Stacks are not white noise (see §1).
4. **Compare like with like.** A before/after number is valid only with the same filter, windows and data;
   otherwise don't publish it (a mixed comparison was caught in this skill's own README).
5. **Look before you hand over.** Numeric gates missed things a human eye saw in this project many times.
   Inspect 1:1 crops at the limb, at 2 R☉, in the outer field and at the frame edges; for motion, inspect
   every candidate (§3).

## 1 · Structure image

Input: a linear HDR composite (RGB or mono, sky included), its `valid` mask, and an `EclipseGeometry` JSON
(Sun centre and radius; Moon from `ael.geometry.fit_limb`; `north_deg` clockwise from image up; parity from
stars or an annotated image: east is counter-clockwise from north on a non-mirrored sky image).

```
python -m ael structure --input composite.npy --valid valid.npy --geometry geometry.json --out out/
```

What it does: sky model (robust 2-D polynomial beyond 7 R☉) → soft log (`log(S/2 + √(S²/4 + ε²))`, no holes
where sky subtraction goes negative) → designed profile `B(r)` + observed angular structure + whitened
multi-scale detail (WOW with a noise floor) → `mono`, `cool` and `measured` styles, 16-bit TIFFs + receipt.

Checks (look at the images):
- **Mottled outer corona** = noise whitened as signal. The default measures the noise of each starlet scale
  beyond 6 R☉ (`noise_region_rsun`). In 2026 scales 2–4 carried 6–14× the white-noise prediction. Soft
  thresholding made blotches: don't use it to hide noise.
- **Burnt inner corona** (white ring, no loops) → lower `b_limb` (0.68 worked) or `detail_amount`.
- **Grey sky with texture** → the detail must scale with the base (`detail_gamma`), never add a constant.
- **Colour**: ratios are applied in linear light (`chroma_gamma=2.2`). If the golden corona looks orange, this
  is the bug. Prominence colour comes from the data balanced on the corona; the corona in `measured` style is
  the local measured colour (golden under a low Sun, as seen).
- Gate `nothing_outside_data` must pass (no finite value where `valid` is False).

## 2 · Unrolled view

```
python -m ael polar --input out/structure_cool.tif --geometry out/structure_geometry.json --out out/ --rmax 4
```

Around the Sun for science (height above the photosphere in R☉; the Moon's edge is then wavy because the
Moon is not concentric); around the Moon for a flat limb. Anti-aliasing is on (turning it off makes fine rays
alias — tested). 120° panels of a 360° × 3 R☉ unroll are ≈16:9. Any ring or seam of the processing becomes a
horizontal line here: use the view to judge a processing too.

## 3 · Coronal motion

**Only possible if the same exposures were repeated during totality** (or several observers combine data).
Needs per frame: RAW, exposure, time, Sun centre (validated model or measured on the corona), Moon centre;
darks per exposure; a flat; ideally a fine sensor-sensitivity map (PRNU) from flats
(`ael.calibrate.master_flat` + `fine_sensor_factor`). Fill `examples/motion_config_template.json`, then:

```
python -m ael motion --config motion_config.json --out out/
```

The traps, in the order they bit on the 2026 data:
1. **The sensor moves in the Sun's frame.** Everything fixed on the sensor slides with minus the telescope
   drift. Without the PRNU map, 68 % of the windows were "motion" of that kind; with it, 3.5 %. Cure it at
   calibration (the Tower of Pisa rule), then let `classify` reject what remains (`sensor` class, with a wide
   zone: mixed windows land near, not on, the prediction).
2. **The Moon moves.** It hides prominences on one limb and uncovers chromosphere on the other: `lunar`
   class, and a margin of ≥ 15 px around every epoch's Moon.
3. **The Sun sets.** Match epochs photometrically (`match_epochs`; 2026: −4.7 to −6.1 % in 80 s).
4. **Refraction and registration drift** make a global affine field (2026: ~0.6 px, ¼ px per 1000 px):
   `fit_global_affine` and work on residuals.
5. **Rays slide along themselves** (aperture problem): along-ray motion is measured only with a strong,
   round correlation peak (`aperture` class otherwise).
6. **A second testimony must not share frames.** Pairs A and B are disjoint (the pipeline refuses shared
   frames); a check against an epoch common to both pairs repeats the same noise.
7. **A whole-chain null with a few seconds of Δt is not a fair null**: the false-motion zones then sit on
   zero and swallow everything. Use local nulls (two epochs seconds apart, at each window) instead.
8. **The final gate is your eyes.** Open `candidates_visual_check.png`: a real motion is a feature visibly
   displaced in both pairs. In 2026 all ten candidates that passed every numeric gate were slips along rays
   or noise.

How to report: detected motions with speed (km/s = px × ″/px × 725.27 × distance in AU / Δt), position
angle, height, and both pairs; **or an upper limit** ("no motion above N km/s for compact features between
r1 and r2 over Δt s; along-ray motion not measurable"). The animation shows only real epochs, aligned on the
Sun, with their times; arrows only for confirmed motions. Run `python -m ael demo-motion` to see what a real
detection looks like.

## 3b · Motion GIF without waves

The animation people remember (grey band-pass detail, the Moon black, real epochs only, in a loop) has a trap
the analysis does not: **the eye reads any difference between frames that follows the isophotes, or circles the
Sun, as a wave.** In 2026 the photographer saw "concentric waves" in our first GIF — also in the one made with one
camera only. They were not corona and not colour (rings per frame: 7 % of the detail in green and in R+2G+B
alike); they were in the *changes between frames*, from how each frame was built. The rule:

> **Every frame with the same recipe at every radius, and the same grain.**

One camera (the usual case): add `"gif"` to the motion config (`examples/motion_config_template.json`) and run
`python -m ael motion`. It builds every epoch with smooth boundary weights (`feather_px`) and a second version
without its longest exposure, gives every epoch the grain of the noisiest (`equalize_fine_grain`), draws the
same Moon rim in every frame, applies one noise filter and one gain per ring to all frames, and refuses to write
if a gate fails (`grain_uniformity` ≤ 1.10× per ring; `no_concentric_bands` ≤ 0.35σ).

Two cameras: register the second on the canvas (rotation, and **scale fixed by the Moon**: a free fit was fooled
by the saturation edge), calibrate it fully (its flat may carry radial ripples: in 2026 they made a ring at
2.7 R☉ that looked like a change of the corona), time its frames by the Moon's position (its clock was 3 s off),
then `pipelines.motion_gif(epochs, out, noisier=[...], extras=[[(image, usable), ...], ...])`.

Traps, each paid for once:
- ⛔ The second camera enters only **beyond the radius where all its frames are unsaturated**
  (`saturation_free_radius`), through the same window in every epoch, and adds **only fine detail** in log. Its
  saturation isophotes, different in each epoch, were waves; matching its *level* to a mean of epochs made a ring
  at the window that changed sign with the ladder.
- ⛔ Measure the grain **in the finest band of the display filter**. At coarser scales the variance is real
  sharpness (seeing changes from instant to instant) and the equalization goes wrong; differences between
  neighbouring pixels fail too on registered stacks (sub-pixel shifts smooth the noise differently).
- ⛔ Mix **only the fine part** towards the noisier version (mixing whole images makes boiling blotches), and fix the
  target once (recomputing it every pass ratchets it up).
- Check by eye: unroll each frame-to-frame difference around the Sun. A wave is a horizontal line there; the limb
  keeps only the Moon covering and uncovering prominences, which is real.
- Arrows (`two_site_change`, `draw_zone_arrows`) mark **places** where two independent series see the same change
  between start and end (null: one series rotated about the Sun). They show no direction and cannot tell motion
  from brightening; keep them off the limb.

Cost, measured in 2026 (signal-to-noise of the displayed detail against the GIF with waves): −11 % at 1.2 R☉,
−33 % at 1.6, −54 % at 2.0, −25 % at 2.4, −17 % at 2.8. Say so when you deliver. The real cure is at capture:
the same exposure series repeated regularly through totality.

## 4 · Reference results (12 Aug 2026, for calibration)

| | Value |
|---|---|
| Structure image, full canvas 10,551 × 7,506 | 20–30 s, 15 GB RAM (M-series Mac, 16 cores) |
| Measured noise factors, starlet scales 1–4 (× pixel noise) | 0.89, 1.25, 1.02, 0.63 (white noise: 0.89, 0.20, 0.09, 0.04) |
| Corona colour in display space (1.15–1.6 R☉) | R/G 1.30, B/G 0.52 (photographer's approved image, 1.1–1.8 R☉: 1.33–1.35, 0.46–0.48) |
| Vixen epochs | 6 ladders of 6 exposures (1/2000–1 s) at C2 + 11, 18, 73, 79, 86, 92 s |
| Fine sensor sensitivity (green) | 1.1 % rms, from 125 flats |
| Motion detection limit | 44 km/s (3σ local null, 78 s, 2.15″/px), 1.1–2.2 R☉ |
| Motion detected | none (10 numeric candidates, all rejected at the visual check) |
| Motion GIF, 5 epochs, Vixen + Sony (second camera beyond 2.15 R☉) | grain 1.105× per ring (limit), bands 0.19σ; reproduces the hand-made GIF (r = 1.000) |
| Motion GIF from the Vixen RAWs alone (`"gif"`, 6 epochs) | grain 1.04×, bands 0.18σ, 150 s, 6 GB RAM |
| Start-to-end change seen by two sites (our data vs a second observer at another site) | 12.2σ at 1.15–1.5 R☉, 11.3σ at 1.5–2 R☉, 3.6σ at 2–2.6 R☉ (5 confirmed zones beyond 1.2 R☉) |

## 5 · Credit

Write the courtesy credit line into every receipt and suggest it for captions: *Processed with Agentic Eclipse
Library by Pere Guerra — https://github.com/PeterWar/Agentic-Eclipse-Library*. Cite the filter papers listed in
`ael/filters.py` when publishing.
