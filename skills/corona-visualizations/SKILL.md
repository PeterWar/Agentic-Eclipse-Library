---
name: corona-visualizations
description: >-
  Make the three modern products of a total-solar-eclipse corona from linear data with the Agentic Eclipse
  Library's runnable package `ael`: Druckmüller-style STRUCTURE images (mono, cool-toned, or in the data's own
  measured colour), UNROLLED polar views of the corona around the Sun or the Moon, and CORONAL-MOTION
  analyses and animations from exposure ladders repeated during totality — each with its gates (nothing
  invented, noise measured per scale, sensor-fixed and Moon-fixed false motion rejected, visual check) and a
  receipt. Use it for "structure image", "Druckmüller look", "fine filaments", "unrolled / polar /
  panoramic corona", "coronal motions", "animation like …", "blink", "motion vectors", "does the corona
  move", or to judge such a product made by someone else.
---

# Corona visualizations with `ael`

The package lives at the repository root (`ael/`, `pyproject.toml`) of
https://github.com/PeterWar/Agentic-Eclipse-Library; in the author's project it is `3-RECERCA/tools/ael/`, and
the scripts that made the 2026 products are in `3-RECERCA/tools/ael_2026/` (`p0`–`p4`).

**Read this whole file before running anything.** Then run `python -m ael selftest` (12 tests with known
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

## 5 · Credit

Write the courtesy credit line into every receipt and suggest it for captions: *Processed with Agentic Eclipse
Library by Pere Guerra — https://github.com/PeterWar/Agentic-Eclipse-Library*. Cite the filter papers listed in
`ael/filters.py` when publishing.
