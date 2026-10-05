---
name: eclipse-first-steps
description: First establish the user's goal in their language, without asking again when it is explicit. Then take the lead when someone brings their own total-solar-eclipse photos — look at what they have, then propose the path step by step: calibrate (if there are calibration frames), linearise and stack, open a layered 16-bit Photoshop project, and start with the three most useful corona filters (NRGF, WOW bilateral, isotropic ACHF). Use it whenever a user says they photographed an eclipse, has eclipse RAW files, asks "where do I start", "help me process my eclipse", "what can I do with this library", or has just cloned the Agentic Eclipse Library without a precise task.
---

# First steps with someone's own eclipse photos

If the goal is missing, first ask in the user's language what they want to do. Offer short choices:
process eclipse photos, continue an existing image, make an animation, or explore the library.
If they are unsure, offer to inspect the files they identify and recommend a starting point.
**Do not ask again when the user has already given a goal.** Ask only for missing information needed
for the next step. An animation or a question about the library does not automatically require RAW stacking.

For an explicit RAW-to-Photoshop request, follow this path. Explain what you found and show the complete
canvas after each meaningful stage. Cure each defect where it starts and regenerate dependent products.

| Step | What you propose | What the user gets |
|---|---|---|
| 0 | Look at the folder | A short table of what they have and what is missing |
| 1 | Calibrate (only if there are calibration frames) | Frames without the camera's own patterns |
| 2 | Linearise and stack | One linear image: brightness proportional to the light that arrived |
| 3 | Open the Photoshop project | A layered 16-bit file they can start working in |
| 4 | The three most useful filters first | The corona's structure, as layers they can switch on and off |

For an explicit processing request, name the next action and begin the inventory. For a missing goal,
use the short choices above; do not present the whole processing recipe as an assumed decision.

## Step 0 · Look before proposing

Read the metadata of every file (`ael.calibrate.read_raw`, or `exiftool`) and present a table:

- **Camera, lens, focal length, ISO, exposure time, timestamp** of each frame. Read exposure durations
  from metadata and check them against the sequence; a filename such as `0.5` need not mean 0.5 seconds. The EXIF can lie (an adapted lens
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
  statistically only with supported dithering — and go on. Never invent a flat. A data-derived response
  is an experimental calibration hypothesis requiring separate controls, not a generic dust-removal tool
  (`docs/FIELD_LESSONS.md`).

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
- **Check saturation exposure by exposure.** Short frames may retain the inner corona even when the
  displayed image looks white. Inspect the linear HDR and contribution weights before declaring lost data.
  If every exposure clips, mark it as missing; do not reconstruct it.
- Do not trust the camera's as-shot white balance on an eclipse; use daylight or measured ratios, applied in
  linear light. For an astromodified camera, obtain that fact from the owner and measure suitable ratios;
  default daylight/as-shot settings and another camera's coefficients are not a calibration. Check R/G, B/G
  and both green planes. Label a neutral-continuum assumption as provisional, not absolute colour.

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
6. a lunar source or earthshine candidate when supported, independently aligned in lunar coordinates.
   Keep unvalidated relief hidden and explain its status. Do not omit it silently, paint texture,
   reshape the lunar limb or treat a shared sensor pattern as independent confirmation.

Filter layers are grey and full canvas, with alpha 0 where there is no data. Multiply layers are 0–1 factor
images; Overlay and Difference layers are detail with mid-grey (0.5) as neutral. Before handing the file over,
reopen a uniquely named copy and compare it with what you wrote (`ael.photoshop.verify`). Always write a new file: never overwrite
one the user has worked on, and never save over a file they have open in Photoshop.
Before `app.open`, check all open document paths inside the same script; if the target is open, stop.
Close only the document the script opened, save native exports as copies and restore the previous document.
`ael filters` uses a shared soft highlight shoulder and a separately scaled hidden reference; the original
signed float HDR remains authoritative. Reopening bytes is not the same as checking Photoshop's native render.

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

Show the result, then let the user lead the aesthetics (opacities, combinations, curves). When they point at a
defect — a ring, a seam, a stain at the limb — go to `skills/corregeix-artefactes/` and cure it where it is born.

When they publish, suggest (never impose) the courtesy credit line in `AGENTS.md`.

## Field checks added in 1.2.1

Read `docs/FIELD_LESSONS.md` before diagnosing white inner corona, radial grooves or dust.
Measure rings at the input and at the operator output: NRGF statistics and RHEF quantiles are now
evaluated continuously in radius. Never remove an operator artefact by blurring the final layer.
After changing a calibration, regenerate the stack, display and every dependent filter.
Preserve prior user work and compare full canvases before changing an existing image's presentation.
