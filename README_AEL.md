# `ael` — the runnable part of the Agentic Eclipse Library

The rest of this repository is the record of one project. `ael` is the part you can **run on your own
eclipse data**: three products that serious eclipse imagers now publish, each with the gates that keep
it honest.

| Product | What it is | Entry point |
|---|---|---|
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
python -m ael selftest       # 17 tests with known truth, each gate with its negative control
python -m ael demo-motion --out demo/   # what a detected motion looks like (synthetic data)
```

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

- **Measure the noise of every scale.** Real stacks have correlated noise (registration, drizzle,
  warping). On the 2026 composite, starlet scales 2–4 carried 6–14× the noise that white noise would
  put there; whitened with white-noise factors, the outer corona became mottle. `noise_factors` measures
  them beyond 6 R☉.
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
Buchlin (2023, WOW); Druckmüller, Rušin & Minarovjech (2006, adaptive circular filters); Starck,
Fadili & Murtagh (2007, starlet); Knutsson & Westin (1993, normalised convolution).
