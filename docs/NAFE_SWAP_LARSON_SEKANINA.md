# NAFE, the SWAP filter and the Larson–Sekanina gradient

Three filters from the literature that the author tried as hidden test layers on his image of 12 August 2026, now in
the library (1.4.2). Like the structure layers of 1.4.1 ([`STRUCTURE_FILTERS.md`](STRUCTURE_FILTERS.md)), they are
extra layers: `python -m ael filters` and the connectors never add them on their own (they are neither in `"all"` nor
in the defaults); a recipe lists them by name, and they come hidden unless the recipe makes them visible.

```json
{"filters": ["nrgf", "wow_edge_aware", "achf_iso_04", "nafe", "swap", "larson_sekanina_1"],
 "visible": ["nrgf", "wow_edge_aware", "achf_iso_04"]}
```

| Name | Photoshop layer | Mode, starting opacity | What it does | Source |
|---|---|---|---|---|
| `nafe` | 09 NAFE | Overlay, 79 % | The equalized image E of the noise adaptive fuzzy equalization: at each pixel, the weighted share of its neighbours that are fainter than it, in a fuzzy neighbourhood of 129 px (twelve Gaussians, eq. 12–14), with the comparison softened by a Gaussian of σ along the intensity axis. σ is the noise gate: 12 times the pixel noise measured beyond 4 R☉ (the paper: 2–12 times). Where the neighbours differ by much less than σ, E stays near mid grey; where they differ by much more, the gate changes little. Eq. 13 is used as printed, with (2π√σ_m)⁻¹ where a normalised Gaussian would have (2πσ_m²)⁻¹: the wide Gaussians weigh more, and half of the neighbourhood's weight lies beyond 32 px. The paper blends (1 − w)·γ + w·E with w ≈ 0.2. Here E is a layer in Overlay, where the opacity plays a role like w; 79 % in Overlay is not w = 0.79 in the paper's linear blend. 79 % is the opacity of the author's test layer, chosen so that it adds, at 1.3–3 R☉, the contrast his edge-aware WOW adds at 37 %. Written from the paper's equations; it uses no other implementation. | Druckmüller (2013), ApJS 207, 25 |
| `swap` | 16 SWAP filter | Normal, 100 % | The image divided by a smoothed copy of itself: I/F′ with F′ = (F + t0)^0.75 (eq. 1 and 2), where F is a running median along each circle around the Sun over ±15° of position angle, blurred by a Gaussian of σ = 4 px; c0 = 0.75 keeps part of the fall of brightness with height; t0 is, as the paper advises, about the median of the filter image. Shown as the paper shows it (eq. 2), with one adaptation: the fourth root, from 0.5 to 2.0, after dividing I/F′ by its median, so that the range does not depend on the units. A complete image to look at on its own (at 100 % it covers the layers below), not a detail layer to blend. Only the paper's branch above the limb: in an eclipse the Moon covers the disc. | Seaton, Berghmans, Bloomfield et al. (2023), Solar Physics 298, 92 |
| `larson_sekanina_1`, `larson_sekanina_0.4` | 15a Larson-Sekanina 1°, 15b Larson-Sekanina 0.4° | Overlay, 20 % | The rotational gradient around the Sun, LS = 2·ℓ(r, θ) − ℓ(r, θ + Δθ) − ℓ(r, θ − Δθ), with ℓ = ln L smoothed by a Gaussian of σ = 1.5, 3, 6 or 12 px as the signal-to-noise ratio falls (changing at 1.6, 2.5 and 4 R☉), and Δθ = 1° or 0.4°. The two turned values ℓ(r, θ ± Δθ) are read by Keys' cubic convolution (a = −0.5) at their exact positions; a pixel keeps a value only where the sixteen pixels read for each of them are observed. Shown as 0.5 + 0.5·tanh(LS/s0), one s0 for the layer, fading to mid grey (no change in Overlay) over the last 16 px before the edge of its domain. | Larson & Sekanina (1984), AJ 89, 571 |

The primitives are in `ael.filters` (`nafe`, `nafe_neighbourhood`, `swap_filter`, `larson_sekanina`); the layers in
`ael.filterbank` (`make_filter`, `nafe_noise_sigma`, `swap_layer`, `larson_sekanina_layer`, `red_excess_mask`).
`make_filter('nafe', …, nafe_sigma=…)` takes a given σ in the units of the input.

## What the Larson–Sekanina gradient does to a corona

It is a difference between the image and the same image turned by ±Δθ about the Sun, so it answers one question:
how much does a pixel stand out from its neighbours along the circle. Two consequences:

- **A structure narrower than Δθ comes out bright with two dark copies at ±Δθ, each of about half its peak.** That
  is the filter, not the data. The layer is not a picture of the corona; it is a map of where brightness changes along
  the circle.
- **A compact, bright object gives saturated light and dark copies.** On the 2026 image the prominences and the band
  of corona next to the Moon did that. The layer therefore always leaves out of its input the band of 0.035 R☉ next to
  the Moon (when the geometry has the Moon). A recipe also leaves out the prominences, found by their colour
  (`red_excess_mask`: R/G above 1.12 times the median R/G of its annulus of 0.01 R☉, out to 1.4 R☉, dilated by 6 px;
  H-alpha makes a prominence red against the white corona). With a mono input the three channels are equal, R/G is 1
  everywhere, and no prominence is found: then the prominences stay in. Where an excluded pixel would be one of the two
  turned values, the layer has no value. Stars do the same: give a starless input. From Python,
  `make_filter('larson_sekanina_1', …, exclude=mask)` leaves any mask out of that layer's input only; the recipe key
  `exclude` removes pixels from every layer.

## What was checked

**Synthetic scenes** (`ael/_tests/test_nafe_swap_larson.py`, part of `python -m ael selftest`):

- **NAFE.** The neighbourhood is 1 at its centre and half of its weight lies beyond 32 px, as eq. 13 is printed. The
  fast computation (levels of intensity, one convolution each) agrees with the paper's sum over the neighbours within
  0.01 at 150 pixels of a corona with noise, a hole and an edge, with a narrow and a wide gate. A flat input gives 0.5
  everywhere. On pure noise a nearly closed gate spreads the noise over the whole range, and the default gate brings it
  below a third of that; where the scene has 200 times the noise in contrast, the gate changes the layer little. The
  measured σ is 12 times the noise put in (within 10 %).
- **SWAP.** With no angular structure the filtered image equals I/(I + t0)^0.75 pixel by pixel within 2 % at
  1.3–2.5 R☉, and the same along every circle (the spread of the ratio between the two along a thin ring is below 1e-4;
  1.1e-5 measured). A ray of σ = 1° keeps at least 90 % of its contrast (1.00 measured); a modulation with a period of
  180° keeps less than half (0.44 measured: the 0.75 crush and t0 leave that much). Every observed pixel of a ragged
  field gets a value, isolated pixels included; none outside the data.
- **Larson–Sekanina.** A corona with no angular structure gives 0 (below 1e-4 in ln L). For ln L = f(r) + A cos(kθ)
  the layer's gradient is A cos(kθ)(2 − 2 cos kΔθ) (correlation above 0.99, amplitude within 6 %). A ray of σ = 0.3°
  gives two dark copies at ±1° between 0.35 and 0.65 of its peak. A small red blob at 1.3 R☉ is found by
  `red_excess_mask`; left in, it gives saturated dark copies at ±1°; left out, the layer has no value over the blob,
  and where its copies would fall it has no value or no dark copy. Two noise realisations share nothing (correlation
  below 0.15).
- **All three** make no rings on the ring-free scene of `ael/_tests/test_lessons.py`, with the same ring measures and
  thresholds as the other filters (the support from the limb is checked from 3 px for Larson–Sekanina, and not from
  the straight edge). They keep the sign of a faint injected angular pattern, with the strength measured when they
  entered within 25 %: a check against later changes, not an independent measure. Through a recipe they come hidden,
  with their opacities, and the prominence leaves only the Larson–Sekanina input.

**On the 2026 stacks**, each against the author's research version of it: see [`VALIDATION_1.4.2.md`](VALIDATION_1.4.2.md).

## Limits

- NAFE draws a light ring next to the lunar limb: there all the neighbours that exist are fainter. Beyond 4 R☉ its
  grain is low but visible.
- SWAP's 0.5–2.0 display range is the paper's choice for EUV images; with the corona of an eclipse part of the field
  may fall outside it (the receipt gives the share below and above; on the author's 2026 crop, none below and
  0.007 % above).
- The Larson–Sekanina layers do not reach the band next to the Moon nor the places whose turned values fall on an
  excluded pixel or outside the data; their copies at ±Δθ are part of what they show.
- Beyond about 4 R☉ the 0.4° Larson–Sekanina layer turns the smoothed noise of the outer corona and the sky into a
  texture like relief; the 1° layer shows less of it.
