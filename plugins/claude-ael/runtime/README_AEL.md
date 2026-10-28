# `ael` — the runnable part of the Agentic Eclipse Library

The rest of this repository is the record of one project. `ael` is the part you can **run on your own
eclipse data**: linear stacking, filter layers and the structure, polar and motion products below.

| Product | What it is | Entry point |
|---|---|---|
| **Linear stack** | RAW/Bayer/RGB frames, declared calibration and registration, support and coverage | `python -m ael stack` |
| **Filter layers** | Three defaults or sixteen portable variants, optional verified 16-bit PSB | `python -m ael filters` |
| **Extinction-corrected stack** | The linear stack corrected for differential atmospheric extinction under a low Sun, after subtracting the sky | `python -m ael extinction` · `ael.extinction` |
| **Coronagraph check** | Your corona against K-Cor, SOHO/LASCO and SDO/AIA: angular structure ring by ring with its null, and brightness in mean solar brightness with both published LASCO C2 calibrations and K + F for K-Cor | `python -m ael coronagraph` · `ael.coronagraph` |
| **Structure image** | The corona's fine filaments from the limb to the edge of the field, in the style made famous by Miloslav Druckmüller's composites; mono, cool-toned or in the data's own colour | `python -m ael structure` · `ael.pipelines.structure_from_linear` |
| **Unrolled corona** | The corona in polar coordinates: the limb becomes a straight line and the streamers rise like curtains; around the Sun or around the Moon | `python -m ael polar` · `ael.pipelines.polar_views` |
| **Coronal motion** | Epochs of the same totality aligned on the Sun, displacement vectors with null tests, a visual-check sheet and GIF/MP4 animations | `python -m ael motion` · `ael.pipelines.motion_from_config` |
| **Motion GIF without waves** | The animation in the reference look (band-pass grey, real epochs only), with one or two instruments, built so that no ring or isophote "wave" appears between frames; optional arrows where two independent series see the same change | `"gif"` section of the motion config · `ael.pipelines.motion_gif` · `ael.animation` |

Everything follows one rule: **nothing invented, nothing mirrored.** Every filter reads only observed
pixels (normalised convolution); where there is no data the result is `NaN`, never a fill, a
continuation or a reflection; every product has a receipt with its parameters and gates.

## Install and check

```
pip install -e ".[raw]"      # from the repository root; 'raw' adds rawpy and astropy for RAW frames
python -m ael selftest       # known-truth tests, including negative controls; also works from the installed wheel
python -m ael demo-motion --out demo/   # what a detected motion looks like (synthetic data)
```

## Stack and develop

```sh
python -m ael stack --config stack.json --out stack_run/
python -m ael filters --config filters.json --out filter_run/
```

Start with [`docs/DEVELOP.md`](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/v1.3.3/docs/DEVELOP.md) and the JSON templates in `examples/`.
Registration and calibration must be measured and declared first. The default filters
are NRGF, WOW and isotropic ACHF; all sixteen variants are available on request.
These are portable recipes, not an exact replay of the author's final Photoshop image.

## Differential extinction under a low Sun (1.3.0)

When the Sun is low, the air mass changes across the corona. In 2026 the Sun stood about 9° high:
the air mass was about **5.75 two solar radii above the Sun** (towards the zenith), **6.05 at the Sun**
and **6.39 two radii below**. With the extinction coefficient measured during that totality
(0.40 mag per air mass), the side towards the horizon received about 9 % less light than the Sun's
own line of sight at 1.5 R☉ and about 23 % less at 4 R☉; the side towards the zenith about 9 % and
24 % more. It is a dipole across the corona that grows with radius. A global brightness or colour
scale does not remove it. It is born in the linear stack, so it is corrected there, and every
filter layer is then rebuilt from the corrected stack.

```sh
python -m ael stack      --config stack.json      --out stack_run/
python -m ael extinction --config extinction.json --out ext_run/   # see examples/extinction_config_template.json
python -m ael filters    --config filters.json    --out filter_run/  # input: ext_run/corrected_with_sky.npy
```

What is observed is `I = C·10^(−0.4·k·X) + S`: the corona `C` dimmed along each line of sight, plus
the sky `S`, which is light scattered *in* the atmosphere. So the correction is made in linear light
**after subtracting the sky**, and the sky itself is not corrected:

    I_corr = (I − S)·10^(0.4·k·(X − X_ref))

- **Air mass per pixel** (`ael.extinction`): Kasten & Young (1989) on the apparent altitude of each
  line of sight. Either from the site and the time with astropy (`airmass_map_from_site`: the Sun's
  altitude with refraction and the position angle of the zenith, projected with the image's
  north/east vectors), from a plate solution (`airmass_map_from_wcs`), or directly from the Sun's
  apparent altitude, the zenith direction and the plate scale (`airmass_map`). On an alt-azimuth
  mount with a level camera the zenith is simply image up. Use the optical plate scale, not the Sun's
  vertical diameter, which refraction compresses. Below the horizon the result is `NaN`.
- **`X_ref`** is the air mass at the Sun, or the one at which your photometric zero point was
  evaluated. Write it down: with k = 0.40, an error of 0.03 in `X_ref` moves the whole level by 1 %.
- **`k` is an input, not a result.** Measure it from the dimming of the corona during totality: two
  frames of the same exposure and ISO, as far apart in time as possible, registered on the Sun; ring
  profiles fitted as `later = a·earlier + b`; `k = −2.5·log10(a)/ΔX` (`dimming_k`). In 2026,
  14 pairs at eight exposure times gave **0.402 ± 0.036 mag per air mass** (mean and scatter
  between pairs; research note 78 in `3-RECERCA/`, in Catalan). This measures every
  multiplicative change between the frames: it is the extinction only if the transparency was steady.
- **Achromatic by default**: one `k` for all channels keeps every colour ratio. Extinction is
  chromatic, so one `k` per channel is possible; it changes the image's colour. Compare full canvases
  side by side before adopting either for an image someone has already seen.

### The lesson: sky and extinction are degenerate

The sky and the extinction leave similar marks on the corona. A sky plane fitted on uncorrected data
where corona is still present takes the corona's extinction dipole as a sky gradient. A constant sky
estimated a few solar radii from the Sun contains corona, and the correction then amplifies the
over-subtraction on the horizon side. A joint fit of sky, corona and `k` was degenerate on the 2026
data. So:

1. fit the sky where the corona is negligible (e.g. r ≥ 8 R☉; `sky.fit` in the recipe); if the field
   is smaller, say so, and estimate the corona left in the sky region by passing a corona model through
   the same sky fit;
2. measure `k` independently (dimming during totality);
3. treat the correction as a **consistency test**, not as a measurement of `k`: against a reference
   without atmosphere (for instance a coronagraph image of the same day, scaled to your field), one `k`
   must cancel the zenith dipole in every ring (`k_nulling_dipole`, gate `k_consistency`). A `k_null`
   that drifts with radius means sky and extinction are being confused: a sky gradient that absorbed
   part of the dipole pulls it down, a sky level that contains corona or a missing sky gradient
   pushes it up, and the two can cancel.

On the 2026 data the uncorrected dipole against a space coronagraph pointed within a few degrees of
the zenith, and the `k` that cancelled it depended on the sky model; the correction was therefore
kept as a consistency test conditional on the sky plane fitted beyond 8 R☉. A pass of the gate is
consistency, not proof: in the tests, a plane fitted on a corona tail and the same tail raising the
sky level compensate each other, the gate passes, and the level is still 7 % low at 3–4 R☉ and
15 % low at 4–5 R☉.

The tests use synthetic coronae with known truth: exact recovery with the true sky; recovery within
0.5 % in level and dipole when the sky region holds no corona; and three wrong sky models (a plane
fitted where corona is present, a constant sky from 3–4 R☉, a constant sky that misses a gradient)
that the same gate rejects with the same thresholds.

## Checking against coronagraphs (1.3.0)

Two questions, kept apart because they fail differently. **Structure:** are the rays and streamers where
an independent instrument sees them? **Brightness:** how bright is the corona in mean solar brightness
(MSB, B/B☉)? The agent's recipe, with the data to ask for and the traps, is the skill
[`skills/coronagraph-comparison/`](https://github.com/PeterWar/Agentic-Eclipse-Library/tree/v1.3.3/skills/coronagraph-comparison/).

```sh
python -m ael coronagraph --config coronagraph.json --out cmp_run/   # see examples/coronagraph_config_template.json
```

- **One solar frame per image** (`SolarFrame`): the Sun's centre and the pixel offsets of 1 R☉ towards
  solar north and east *as seen by that observer*. The two axes may be non-perpendicular: the 2026 plate,
  solved on stars with the Sun 9° high, had them 90.43° apart, and treating them as perpendicular moved
  points 3 px at the limb and 20 px at 6 R☉. Frames come from an `ael` geometry and the P angle, from an
  affine plate solution, from a helioprojective FITS header (K-Cor level 2, AIA level 1.5), or from three
  pixel positions (LASCO level 0.5 through sunpy, with SOHO's own R☉: `rsun_arcsec`; SOHO sees the Sun
  1.1 % larger than the Earth).
- **Structure** (`unroll`, `nrgf_rows`, `compare_structure`): each image unrolled in its own coordinates,
  normalised radius by radius, angular profiles per ring correlated at zero rotation and at the best
  rotation within ±10°, with a null from rotations of 30–330° and a fine-detail version (angular
  high-pass below 12°). `dark_sector` masks an occulter pylon as the one dark run that contains a seed angle,
  never with a global threshold that would also remove coronal holes. The test compares angles only: a
  radial tone curve `a(r)·I + b(r)` passes it unchanged (a test shows it). A best rotation at the edge of the
  search is flagged (`at_search_edge`): it is the broad shape, not an orientation.
- **Brightness** (`cell_medians`, `level_ratios`, `ratio_band`): medians in 1° cells of each ring, each image
  in its own frame, without resampling; cells that touch the lunar-motion band, the gap at the limb or a
  prominence are dropped whole (`drop_touching`). K-Cor measures pB: `kcor_total_msb` turns it into what a
  photograph sees, pB/p(r) for the K corona (Thomson polarisation integrated along the line of sight with
  the van de Hulst coefficients, Baumbach–Allen or Saito densities) **plus the F corona** (van de Hulst 1950).
  LASCO C2: `lasco_c2_msb_per_dn` gives both published calibrations (Colaninno & Howard 2015 and SolarSoft),
  13.5 % apart in level for August 2026, for the Orange filter; a summed image divides the factor
  (`lasco_c2_summing`), and polariser images are calibrated by SolarSoft only. `ratio_band(σ_lo, σ_hi)` is the 1σ band of ours/reference when the
  photograph's uncertainty is asymmetric: for −20 %/+11 %, 0.90–1.25.

Checked on the 2026 data (`docs/VALIDATION_1.3.0.md`), from the research's calibrated MSB map (a FITS file
binned 2×2, not distributed): the module reproduces the research ratios within 0.003 for LASCO C2 (1.14 to 1.40
with Colaninno & Howard, 1.32 to 1.62 with SolarSoft) and within 0.009 for K-Cor (1.06/1.06/1.12 at
1.15–1.70 R☉), and the plate's 90.43° comes out of the map's own FITS header. Without the F corona the K-Cor
ratios would be 1.19/1.21/1.43: leaving out the F corona is what made the first comparison's excess
(+13–15 %).

## Geometry

Every product needs an `EclipseGeometry` (JSON): image shape, Sun centre and radius in pixels, Moon
centre and radius, the direction of celestial north (degrees clockwise from image up), parity and
scale. `ael.geometry.fit_limb` measures the Moon from the image (linear intensity: on the log image
the edge slides into the dark tail of the blur — 3 px on a 62 px Moon in the tests).

```json
{"shape": [7506, 10551], "sun_xy": [5361.77, 3775.75], "sun_radius_px": 440.6,
 "moon_xy": [5391.24, 3777.41], "moon_radius_px": 469.2, "north_deg": 45.25, "mirrored": false,
 "arcsec_per_px": 2.1504}
```

## 1 · Structure images

```
python -m ael structure --input fusion_linear.npy --valid support.npy --geometry geometry.json --out out/
```

`structure = B(r) + g·(ℓ − ⟨ℓ⟩(r)) + a·d·B(r)^γ`, where `ℓ` is a soft logarithm of the sky-subtracted
luminance, `⟨ℓ⟩(r)` its median per annulus, `B(r)` a *declared* display profile that replaces the
corona's steep radial fall-off (brightness per radius only, never structure) and `d` the whitened
multi-scale detail (WOW, Auchère et al. 2023) whose gain follows the signal-to-noise ratio.

What the 2026 data taught (and the code now does by default):

- **Measure the noise of the scales.** Real stacks have correlated noise (registration, drizzle,
  warping). On the 2026 fusion, starlet scales 1–3 (counted from 0; 2–8 px) carried 6–15× the noise that
  white noise would put there; whitened with white-noise factors, the outer corona became mottle.
  `noise_factors` measures them beyond 6 R☉ (coarser scales, which carry faint corona there, are
  extrapolated); since 1.3.4 the default WOW layer uses them.
- **Apply colour in linear light.** Multiplying a display-encoded grey by linear colour ratios
  over-saturates by the display gamma (the golden corona came out bright orange). With the ratios
  converted (`chroma_gamma = 2.2`), the measured corona colour in display space was R/G 1.30, B/G 0.52
  at 1.15–1.6 R☉, against 1.33–1.35 and 0.46–0.48 at 1.1–1.8 R☉ in the photographer's approved image.
- A cool tint for the sky is a presentation choice: the pipeline calls it so in the receipt; say so in
  the caption.

## 2 · Unrolled views

```
python -m ael polar --input out/structure_cool.tif --geometry out/structure_geometry.json --out out/ --rmax 4
```

`ael.polar.to_polar` / `from_polar` are exact inverses (round-trip test ≤ 1 %), anti-aliased (each
output pixel averages enough sub-samples to keep the input spacing under 0.7 px — without it, fine rays
alias into false patterns, tested) and `NaN` wherever the interpolation support leaves the data. Centre
on the Sun for science (heights in solar radii above the photosphere); on the Moon for a flat limb.
120° panels of a 360° × 3 R☉ unroll are close to 16:9.

## 3 · Coronal motion

A totality lasts minutes: time enough for the inner corona to move, if the exposure ladder was repeated.

```
python -m ael motion --config motion_config.json --out out/     # see examples/motion_config_template.json
```

The pipeline: calibrate each RAW (dark of its exposure, flat, **fine sensor sensitivity map**,
saturation on the raw value, green quincunx), merge each epoch in the **Sun's frame** (not the Moon's),
match the epochs photometrically (the Sun sets: the corona faded 4.7–6.1 % in 80 s in 2026), band-pass
them, measure local displacements, and classify every vector:

| Class | Meaning |
|---|---|
| `sensor` | moves with minus the telescope drift: fixed on the sensor (flat-field errors, dust, pixel sensitivity) |
| `lunar` | moves with the Moon: the limb, prominences being covered or uncovered |
| `still` | below the null-test threshold |
| `aperture` | a ray sliding along itself: only the component across the ray is measured |
| `coronal` | everything else — then confirmed by local nulls and by a **second pair of epochs with no frame in common** |

Nothing is claimed before the **visual check**: `candidates_visual_check.png` shows every candidate in
both pairs; a real motion is a feature visibly displaced.

### What happened on the 2026 data (Vixen VSD90SS + Canon R6 III, 2.15″/px, six epochs over 81 s)

- **The sensor was the loudest "motion".** Before correcting the fine pixel sensitivity (1.1 % rms in
  green, rebuilt from 125 flats), 68 % of the windows (3,601 of 5,282) moved exactly with the telescope
  drift; with the same windows and filter after the correction, 3.5 % (185).  (A trap on the way: the
  correlation between two epochs 6 s apart is *not* a fair measure of this cure — both share the fixed
  pattern, shifted only 1.6 px, and it barely changes.)
- **The Moon was the next.** Near the limb the early and late epochs differ (correlation 0.4–0.6): the
  Moon, which moved 21 px relative to the Sun, hides a large prominence on one side and uncovers the
  chromosphere on the other.
- **Systematics:** a global affine term — about 0.6 px of translation and a quarter of a pixel per
  1000 px of compression (refraction changing as the Sun set, registration drift) — is fitted and
  removed before any local claim.
- **Result:** no coronal motion above **44 km/s** (3σ of the local null over 78 s) was detected for
  compact features between 1.1 and 2.2 R☉; ten automated candidates passed every numeric gate and were
  rejected at the visual check (slips along rays, noise). Motion along a ray cannot be measured with
  this sampling.
- **For a future eclipse:** repeat a short ladder every ~10 s through totality and use more aperture or
  longer exposures at 1.5–3 R☉; the displacement grows with time and the detection limit falls with the
  number of epochs.

The same analysis run on synthetic data with known truth finds the moving blob at the right speed and
direction and never marks the sensor dust or the lunar limb (`tests/`, `python -m ael demo-motion`).

### Motion GIF without waves (`ael.animation`, `ael.pipelines.motion_gif`)

An animation shows every difference between its frames, and the eye reads any difference that follows
the corona's isophotes, or circles the Sun, as a **wave**. On the 2026 data the waves came from how the
frames were built, not from the corona, and not from working in colour (rings per frame were 7 % of the
detail both in green and in R+2G+B). Four causes, the first two inside a single camera:

1. the Moon's edge, made bright by the detail filter, changed thickness between epochs and pulsed;
2. the epochs alternated two exposure ladders (up to 1/2 s and up to 1 s), each with its own saturation
   boundaries (they follow isophotes) and its own grain: up to 1.35× from one frame to the next;
3. a second camera whose frames saturated at different radii in different epochs: at each saturation
   isophote the sharpness and the grain changed;
4. different grain in each final frame.

One rule cures them: **every frame with the same recipe at every radius, and the same grain.**

| Step | Function |
|---|---|
| Saturation and Moon boundaries enter with smooth weights | `motion.merge_epoch(..., feather_px=...)` |
| Every epoch gets the grain of the noisiest one: the fine part is mixed towards the same epoch made from fewer frames (nothing is added, data only lose weight) | `animation.equalize_fine_grain` |
| A second camera adds only fine detail, beyond the radius where all its frames are unsaturated, through the same window in every epoch; the large scale is the main camera's | `animation.saturation_free_radius`, `animation.add_fine_detail` |
| The same rim at the Moon's edge in every frame | `animation.uniform_moon_edge` |
| One noise filter and one gain per ring for all frames (from pairs of epochs seconds apart) | `animation.common_noise_filter`, `animation.render_frames` |
| Gates: grain per ring within 1.10× between frames; no ring appearing between frames (≤ 0.35σ) | `gates.grain_uniformity`, `gates.no_concentric_bands` |
| Arrows where two independent series (two cameras or two sites) see the same change between start and end. **They mark a place, not a direction**, and cannot tell motion from brightening | `animation.two_site_change`, `animation.draw_zone_arrows` |

With one camera, add a `"gif"` section to the motion config (see `examples/motion_config_template.json`):
the pipeline then also writes `gif/motion_gif.gif`, its frames, an MP4 and a receipt, building for every
epoch a second version without its longest exposure. With two cameras, register the second one on the
canvas, match it photometrically and call `motion_gif(epochs, out, noisier=..., extras=...)`. Scales are
in arcseconds (validated at 4.3″/px; `scale` adapts them).

**What it costs, measured on the 2026 data** (signal-to-noise per point of the displayed detail): against
the same GIF with waves, −11 % at 1.2 R☉, −33 % at 1.6, −54 % at 2.0, −25 % at 2.4 and −17 % at 2.8 R☉,
because the second camera is left out where its saturation boundaries would move and every epoch is
brought down to the noisiest. In an animation a constant grain is far less visible than one that changes.
The best cure is at capture: repeat the same exposure series regularly through totality.

On the 2026 data `motion_gif` reproduces the hand-made GIF exactly (correlation 1.000); its grain gate
sits at the limit there (1.105 for a tolerance of 1.10, a residual of real fine structure in the grain
measure, probably seeing that changes from instant to instant); from the RAW frames of one camera alone
(`python -m ael motion` with `"gif"`) both gates pass (1.04 and 0.18σ).

## 4 · Layered Photoshop files

`ael.photoshop` writes 16-bit PSD/PSB files with full-canvas layers (Unicode name, blend mode, opacity,
visibility, alpha 0 where there is no data) and reads them back to compare (`pip install -e ".[photoshop]"`):

```python
from ael import photoshop as ps
doc = ps.new_document(width, height, psb=True)
ps.add_layer(doc, "Linear stack", ps.to_u16(stack01), visible=False)
ps.add_layer(doc, "Display base", ps.to_u16(base01))
ps.add_layer(doc, "NRGF", ps.to_u16(nrgf01), ps.to_u16(valid), mode="multiply", opacity=0.39)
ps.save(doc, "corona.psb", ps.to_u16(base01))          # refuses to overwrite an existing file
ps.verify("corona.psb", [dict(name="Linear stack"), dict(name="Display base"), dict(name="NRGF", mode="multiply")])
```

At 16 bits Photoshop keeps the layers in the "Lr16" block; psd-tools reads them from there but writes them
elsewhere, so `save` moves them. Never call psd-tools' own `save()` on these documents: it recomposes the
flattened image at 8 bits.

## Credit

MIT licence. If you publish an image made with this code, a mention would be appreciated (a courtesy,
not a condition): *Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library*. The filters come from published work:
Morgan, Habbal & Woo (2006, NRGF); Morgan & Druckmüller (2014, MGN); Auchère, Soubrié, Pelouze &
Buchlin (2023, WOW); Druckmüller, Rušin & Minarovjech (2006, adaptive circular filters) and
Druckmüllerová (2014, thesis: the published kernel); Gilly & Cranmer (2025, RHEF); Starck,
Fadili & Murtagh (2007, starlet); Knutsson & Westin (1993, normalised convolution). The air mass
is that of Kasten & Young (1989, *Applied Optics* 28, 4735). The coronagraph comparison uses the
scattering coefficients and the F and K coronae of van de Hulst (1950, *BAN* 11, 135), the line-of-sight
integral of Billings (1966), the Baumbach–Allen and Saito (1977) electron densities, and the LASCO C2
calibrations of Colaninno & Howard (2015, *Solar Physics* 290, 997) and SolarSoft; K-Cor data: K-Cor Team
(2013), doi:10.5065/D69G5JV8.

Contributors: Chris Gilly (NorthWest Research Associates), first author of the RHEF paper, reviewed the draft
of the author's paper *A Faithful Corona* and this library in October 2026; version 1.3.2 answers his review.
Raúl Hussein contributed the `eclipse-astrophotography` skill and a three-camera case study, with RAW frames
from Oscar Maseda and Carlos Oltra, and corrected the NRGF description in the field lessons (1.3.3).
Edu (@edu27) tested 1.3.3 on his own frames; his reports led to the new default WOW, the per-ring ACHF display,
`ael.gates.fine_detail_fidelity` and the mirror scan (1.3.4).
Other contributions are listed in the repository [README](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/v1.3.3/README.md#contributors).

Version 1.3.0 adds `ael extinction` and `ael coronagraph`, corrects stepped radial statistics and
clipped display highlights (prepared as 1.2.1), adds an explicit native-reference canvas option and
documents the limits of internal dust calibration. See [field lessons](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/v1.3.3/docs/FIELD_LESSONS.md) and
[recipe details](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/v1.3.3/docs/DEVELOP.md). Version 1.3.2 replaces the smoothed ring profile of the NRGF, which
biased steep profiles, lets any RHEF layer made with `make_filter` use the Upsilon curve with an exponent for
each side, and
documents how the library's filters differ from the paper's published layers
([`docs/PAPER_AND_LIBRARY.md`](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/v1.3.3/docs/PAPER_AND_LIBRARY.md)). Version 1.3.4 replaces the default
WOW layer (WOW bilateral could invert faint fine detail), rebuilds WOW bilateral with guided range weights for data
that reach the lunar limb, shows the ACHF layers with a level and a spread per ring,
adds `ael.gates.fine_detail_fidelity` and `ael.coronagraph.scan_mirror`, and makes `ael motion` read `"mirrored"`.
Existing images are not rewritten; compare the new numerical recipe before adopting it.
