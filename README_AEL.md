# `ael` — the runnable part of the Agentic Eclipse Library

The rest of this repository is the record of one project. `ael` is the part you can **run on your own
eclipse data**: three products that serious eclipse imagers now publish, each with the gates that keep
it honest.

| Product | What it is | Entry point |
|---|---|---|
| **Structure image** | The corona's fine filaments from the limb to the edge of the field, in the style made famous by Miloslav Druckmüller's composites; mono, cool-toned or in the data's own colour | `python -m ael structure` · `ael.pipelines.structure_from_linear` |
| **Unrolled corona** | The corona in polar coordinates: the limb becomes a straight line and the streamers rise like curtains; around the Sun or around the Moon | `python -m ael polar` · `ael.pipelines.polar_views` |
| **Coronal motion** | Epochs of the same totality aligned on the Sun, displacement vectors with null tests, a visual-check sheet and GIF/MP4 animations | `python -m ael motion` · `ael.pipelines.motion_from_config` |

Everything follows one rule: **nothing invented, nothing mirrored.** Every filter reads only observed
pixels (normalised convolution); where there is no data the result is `NaN`, never a fill, a
continuation or a reflection; every product has a receipt with its parameters and gates.

## Install and check

```
pip install -e ".[raw]"      # from the repository root; 'raw' adds rawpy and astropy for RAW frames
python -m ael selftest       # 12 tests with known truth, each gate with its negative control
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
