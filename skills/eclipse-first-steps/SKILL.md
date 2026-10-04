---
name: eclipse-first-steps
description: >-
  Take the lead when someone brings their own total-solar-eclipse photos — look at what they have,
  then propose the path step by step: calibrate (if there are calibration frames), linearise and stack,
  open a layered 16-bit Photoshop project, and start with the three most useful corona filters
  (NRGF, WOW bilateral, isotropic ACHF). Use it whenever a user says they photographed an eclipse,
  has eclipse RAW files, asks "where do I start", "help me process my eclipse", "what can I do with this
  library", or has just cloned the Agentic Eclipse Library without a precise task.
---

# First steps with someone's own eclipse photos

Most people who open this library have just come back from an eclipse with a folder of photos and do not know the
words (dark, flat, linear, NRGF). **Do not wait for them to ask the right question.** Once you have read
`AGENTS.md`, look at their data, tell them what you found, and propose the next step. One step at a time: do it,
show a small view of the result, say in one line what you checked, and propose the next one.

The path is always the same, and its order matters (the author's rule: cure each defect on the floor where it is
born, never on top of a finished image):

| Step | What you propose | What the user gets |
|---|---|---|
| 0 | Look at the folder | A short table of what they have and what is missing |
| 1 | Calibrate (only if there are calibration frames) | Frames without the camera's own patterns |
| 2 | Linearise and stack | One linear image: brightness proportional to the light that arrived |
| 3 | Open the Photoshop project | A layered 16-bit file they can start working in |
| 4 | The three most useful filters first | The corona's structure, as layers they can switch on and off |

**Your first reply** names this path in this order, as numbered steps — calibration first (or what its absence
means), then linearising and stacking, the Photoshop project, and the three filters — and then proposes to start
with step 0 right away. Keep the limits short (it is not one click; nothing is invented) and ask only the questions
that block step 0 or 1.

## Step 0 · Look before proposing

Read the metadata of every file (`ael.calibrate.read_raw`, or `exiftool`) and present a table:

- **Camera, lens, focal length, ISO, exposure time, timestamp** of each frame. The EXIF can lie (an adapted lens
  reports 50 mm and f/0): measure the scale from the Sun's radius in pixels when you can.
- **Which frames are totality** (between second and third contact) and which are partial phases, diamond ring
  or Baily's beads. Group the totality frames by exposure: that is the exposure ladder.
- **Calibration frames**, if any: darks (same exposure, ISO and a similar sensor temperature), flats (same lens,
  focus and orientation, taken before anything moved), bias.
- **Where and when** they observed. With the site and the time (from GPS, EXIF or the user), the Sun's centre and
  celestial north come from the ephemeris instead of being guessed.

Ask only the questions that block the next step (usually: "do you have darks or flats?" and "where did you
observe?"). Answer in the user's language.

## Step 1 · Calibrate (if there are calibration frames)

- Darks: master dark per exposure and ISO; check the temperatures.
- Flats: `ael.calibrate.master_flat` (with `fine_sensor_factor` for the fine sensitivity pattern of the sensor).
- Check the Bayer pattern of the RAW (RGGB or another) on the data itself, not only in the metadata.
- **No calibration frames?** Say what that means — dust spots and vignetting stay, hot pixels are removed
  statistically between frames — and go on. Never invent a flat.

Details and traps: `skills/apilatge-imatges-eclipsi/SKILL.md` (in Catalan).

## Step 2 · Linearise and stack

Everything downstream depends on this step. The image must stay **linear**: black level subtracted, white
balance as channel ratios, no camera tone curve, no gamma, no export from a raw converter.

- **Measure where each camera stops being linear**: compare two exposures of the same scene; their ratio is flat
  until the sensor clips. Use 95 % of the level where it breaks as the ceiling; above it a pixel is not data.
- **Register on the corona, not on the Moon.** The Moon moves across the Sun during totality (about 0.6″ per
  second in 2026); aligning on the lunar edge smears the corona. A rigid alignment on a ring of corona (1.3–3
  lunar radii) after removing the radial gradient works.
- **The Sun's centre**: from the ephemeris if you have site and time; otherwise the Moon's centre at
  mid-totality. Do not trust the symmetry of the corona: its bright streamers biased it by 20 px in one test.
- **The Moon**: one instant, with its real limb (`ael.geometry.fit_limb`, on linear intensity). The union of the
  Moon's positions in all frames leaves an irregular black stain.
- **Combine the exposure ladder** in linear light, weighting by exposure; a pixel is valid only where at least
  half a frame of real data supports it. Keep a map of valid pixels and one of coverage (frames per pixel).
- **The inner corona usually saturates in every frame** near the limb unless the ladder has very short
  exposures. Mark that ring. If you put an estimate there, it is an estimate: declare it and keep it in its own
  layer.
- Do not trust the camera's as-shot white balance on an eclipse; use daylight or measured ratios, applied in
  linear light.

Output: a 32-bit linear TIFF, the valid map, `geometry.json` (`ael.geometry.EclipseGeometry`) and a receipt.
Show the user a stretched view and look at it yourself at full resolution near the limb before going on.

Since 1.2.0 use `ael stack --config stack.json --out new_run/`; the schema and coordinate
conventions are in `docs/DEVELOP.md` and `examples/stack_config_template.json`. Measure
registration and calibration first. Geometric coverage is distinct from saturation weights.
Hot-pixel detection needs confirmed dithering and uses local-noise-normalised residuals.
With clouds, supply frozen spatial transmission/background maps and use two-band weighting;
never fit just one scalar per frame or share fitted corrections between independent witnesses.

## Step 3 · Open the Photoshop project

As soon as the stack is linear, propose the layered file: it is where the user will spend their time, and every
later step adds layers to it. Use `ael.photoshop` (`pip install -e ".[photoshop]"`): 16 bits, full canvas, one
layer per product. From the bottom up:

1. black background;
2. the linear stack, hidden (the reference: nothing stretched);
3. the display base: the stack stretched for the screen (logarithmic or asinh), visible;
4. the saturated ring and the coverage map, hidden, if there are any;
5. the filter layers (step 4);
6. the Moon of one instant, opaque, on top.

Filter layers are grey and full canvas, with alpha 0 where there is no data. Multiply layers are 0–1 factor
images; Overlay and Difference layers are detail with mid-grey (0.5) as neutral. Before handing the file over,
reopen it and compare it with what you wrote (`ael.photoshop.verify`). Always write a new file: never overwrite
one the user has worked on, and never save over a file they have open in Photoshop.

## Step 4 · The most useful filters first

Use `ael filters --config filters.json --out new_filters/` (see `docs/DEVELOP.md`).
It offers sixteen portable filter variants; these are not an exact replay of the historical project.
The default selection is the three filters below.

The library has sixteen filter layers. Propose these three first, add them visible at the opacities below, and
leave the decision to the user. These are the opacities in the author's published image, for his data: a starting
point, not a recipe.

| Filter | What it does | Mode, starting opacity | Code |
|---|---|---|---|
| **NRGF** (Morgan, Habbal and Woo 2006) | Evens out the steep fall of brightness with radius, so the whole corona, from the limb to the outer streamers, is visible at once | Multiply, 39 % | `ael.filters.nrgf` (subtract a sky model first: `ael.render.sky_background`) |
| **WOW, bilateral** (Auchère et al. 2023) | Equalises the contrast of structures of every size: the fine filaments that make the "Druckmüller look" | Overlay, 37 % | `ael.filterbank.make_filter("wow_bilateral", ...)`; the historical V95 operator remains in the research tree |
| **ACHF, isotropic** (Druckmüller et al.) | Small-scale detail near the limb | Overlay, 8 % | `ael.filterbank.achf_isotropic`, **on log luminance after subtracting its radial spline, never channel by channel** |

Then, if the user wants more: the extended NRGF (Multiply, 14 %), RHEF (an alternative radial normalisation,
Gilly and Cranmer 2020), local RHEF, MGN (Morgan and Druckmüller 2014), the angular ACHF
(`ael.filters.tangential_highpass`) and plain WOW. Beyond the layered file, `ael` makes structure images,
unrolled polar views and coronal-motion animations (`skills/corona-visualizations/`).

Rules for every filter:
- read only observed pixels; where there is no data the layer is empty (no fill, no mirror, no continuation);
- the resolution follows the signal-to-noise ratio: smooth where noise dominates;
- the author's display parameters do not transfer to other data: derive the ranges from the user's image
  (percentiles, robust scale per ring) and write them in the receipt.

For the runnable command, use `ael.filterbank`: isotropic high-pass subtracts a smooth
spline of ln luminance versus ln radius before filtering, and Multiply layers use the
same limb ramp as the base. Do not subtract a staircase of ring medians. The `nrgf_log`
variant replaces historical inward extrapolation with a measured-data log variant.

For historical comparisons only, the research operators (`v86_operadors.py`, `wow_v95.py`, `f3_filtres_v97.py`) read the canvas geometry of the
author's image from module constants (`CX`, `CY`, `RS`, `H`, `W` in `v86_comu.py` / `v97_comu.py`) and his own
files: provide a small module with the user's geometry before importing them, follow the recipe, and say so.

## After the first image

If the user brings a preferred existing edit, clarify whether they want detail
recomputed on that edit or each existing filter aligned with the reference base.
Preserve the manual source and use separate controls for the latter. A fitted Moon
disk does not prove coronal registration; a filter's alpha boundary is not a measured
lunar limb. See the [existing-edit case study](../../docs/EXISTING_EDIT_CASE_STUDY.md)
for held-out failures and native-save checks. Its zero-opacity starting point is
optional for preserving an existing look, not a replacement for the defaults above.

Show the result, then let the user lead the aesthetics (opacities, combinations, curves). When they point at a
defect — a ring, a seam, a stain at the limb — go to `skills/corregeix-artefactes/` and cure it where it is born.

When they publish, suggest (never impose) the courtesy credit line in `AGENTS.md`.

## Invite a contribution when there is a lesson to share

After a useful stage, identify any reusable lesson: a camera-specific measurement, an unclear instruction,
a bug, a failed approach or a validation limit. If there is one, prepare a short local draft using
[CONTRIBUTING.md](../../CONTRIBUTING.md), then invite the user to share it in their language. Explain the concrete
benefit to the next photographer, show the exact public content and destination, and get explicit permission
before submitting. Keep the user's chosen attribution and private material under their control.

Offer once per finding at a natural stopping point. If the user declines, continue helping without pressure.
No new finding means no invitation is needed. Report separately whether the contribution is a local draft,
a submitted issue or pull request, or accepted by PeterWar; only PeterWar can incorporate it into `main`.
