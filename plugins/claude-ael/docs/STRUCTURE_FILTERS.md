# Structure-aware detail layers

Five filter families from the solar and astronomical image-processing literature that AEL did not have, found by
a literature survey made with Gemini (Google) on 30 October 2026 and implemented here. They are extra layers:
`python -m ael filters` and the connectors never add them on their own (they are neither in `"all"` nor in the
defaults); a recipe lists them by name.

```json
{"filters": ["nrgf", "wow_edge_aware", "achf_iso_04", "steerable_g2", "mmt"], "visible": ["nrgf", "wow_edge_aware", "achf_iso_04"]}
```

Every one of them starts from the residual of ln L about its smooth radial profile, as the isotropic ACHF does,
reads only observed pixels, returns nothing where there is no data, and ends with the display per ring of the ACHF
layers. Four of them are ACHF iso 04 (the default detail layer) with one change each, so that a comparison with ACHF
iso 04 tells what the change brings.

| Name | Photoshop layer | What it does | Source |
|---|---|---|---|
| `hessian_ridge` | 10 Hessian ridge | ACHF iso 04 times a curvilinear weight in [0, 1]: the Frangi measure of the scale-normalised Hessian (σ 1.5, 3 and 6 px), for bright rays and dark lanes alike. A weight never adds anything; it lowers isotropic grain and keeps elongated structure at any angle. | Frangi, Niessen, Vincken & Viergever (1998), MICCAI, LNCS 1496, 130 |
| `steerable_g2` | 11 Steerable G2 | The second derivative of the residual steered, pixel by pixel, across the local structure: three base convolutions give every angle, and the angle comes from the structure tensor smoothed over twice the scale, so it follows a ray, a loop or a cavity edge whatever its angle to the radius. σ 1.5, 3, 6 and 12 px. | Freeman & Adelson (1991), IEEE PAMI 13, 891 |
| `mmt` | 12 Median transform | The ACHF iso 04 bands taken from the pyramidal median transform (5×5 medians of observed pixels, five scales) instead of Gaussians. A median ignores a few extreme pixels, so a star, a prominence or the edge of the data does not spread a dark ring into the scales around it. | Starck, Murtagh & Bijaoui (1998), *Image Processing and Data Analysis: The Multiscale Approach* |
| `noise_gate` | 13 Noise gating | ACHF iso 04 of the residual after Fourier noise gating on overlapping 32-pixel tiles of the corona unrolled in (ln r, position angle). The noise level of each row of tiles is measured on the high frequencies off the two axes of the spectrum (where rays and arcs put their energy); each coefficient gets the non-negative garrote gain `max(0, 1 − (3N)² / |F|²)`. What the gate removes is mapped back and subtracted. | DeForest (2017), ApJ 838, 155; Breiman (1995), Technometrics 37, 373 |
| `coherence_diffusion` | 14 Coherence diffusion | The 8–32 px band of the residual after coherence-enhancing diffusion: the image smooths along the local orientation only where that orientation is coherent, and not across it. Computed on a copy reduced to at most 6 Mpx; no flux enters or leaves the observed pixels. | Weickert (1999), Int. J. Computer Vision 31, 111 |

The primitives are in `ael.filters` (`ridge_weight`, `steerable_g2`, `multiscale_median`, `noise_gate`,
`coherence_diffusion`, with `hessian` and `hessian_eigen`); the layers in `ael.filterbank.structure_filter`.

## What was checked

**Synthetic scenes** (`ael/_tests/test_structure.py`, part of `python -m ael selftest`): a power-law corona around an
off-centre Moon, 3 % noise per pixel.

- Every layer is defined on every observed pixel, edges included, and on no other pixel.
- Null control: the layers of two independent noise realisations do not correlate (|r| < 0.15; measured −0.01 to
  0.11, the same as ACHF iso 04 within the spread of the realisations).
- Thin rays every 12° and a thin loop off the Sun, at a per-pixel S/N of 1: `hessian_ridge`, `steerable_g2` and `mmt`
  correlate with the injected structure better than ACHF iso 04 (rays 0.55, 0.61 and 0.53 against 0.52; loop 0.30,
  0.33 and 0.31 against 0.27). `noise_gate` finds less (0.32 and 0.21): a ray one pixel wide at S/N 1 per pixel gives
  each Fourier coefficient about as much ray as noise, and the gate removes it with the noise.
- A star 50 times brighter than the corona around it: ACHF iso 04 draws a dark ring 5–12 px around it (−0.11 of
  the layer's range); the median transform does not (+0.04). `hessian_ridge` makes that ring deeper (−0.17): a ring
  is a curve, and the weight keeps it.
- The diffusion keeps the sum of the observed residual exactly and leaves the unobserved pixels empty. The gate
  removes 21 % of the rms of pure noise and 4.5 % of a scene with no noise at all (the part of the thin rays that
  falls off the spectrum's axes).
- A linear ramp has no detail at any scale. On a canvas of odd size (389 × 515) every plane of the median transform,
  and the copy reduced and enlarged back that the diffusion works on, stays at zero inside the data (5 × 10⁻⁷, the
  float precision). A first, unpublished version cropped the odd row and stretched the rest back: the ramp leaked
  into its planes (6 × 10⁻³ to 10⁻², a shift of 1.4–2.9 px), and on the 2026 stacks the coarse scales slid by up to
  12 px. An audit of all of AEL's filters found it; the median transform and the diffusion's reduced copy now pad
  with no data to whole blocks. The scenes above are 320 px, a whole number of blocks, and did not see it.

**Two independent optics.** Each layer was made on its own from two stacks of the same corona of 12 August 2026,
one from a 300 mm telephoto lens (Sony A7R III) and one from a 90 mm refractor (Vixen VSD90SS with a Canon R6 Mark
III), the refractor blurred to the telephoto's resolution and both on the same canvas. For each band of the layer
and each range of radius, κ = 2·cov / (var₁ + var₂) is the part of what the layer shows that is the same in both
optics: what two instruments see alike is corona, what only one sees is noise or a defect of that instrument. A
null control turns one layer 30° about the Sun; its κ stays within 0.04 of zero for every layer and band. In the
table, κ and, in brackets, the confirmed contrast (κ times the rms of the band, in units of the layer's range). The
rows of `mmt` and `coherence_diffusion` were measured again with the code as released; ACHF iso 04, measured again
with them, gave the same figures.

| Layer | fine 1.5–4 px at 1.5–2.5 R☉ | medium 4–12 px at 1.5–2.5 R☉ | medium 4–12 px at 2.5–4 R☉ | coarse 12–36 px at 2.5–4 R☉ |
|---|---|---|---|---|
| ACHF iso 04 (the default) | 0.53 (0.026) | 0.94 (0.080) | 0.43 (0.026) | 0.92 (0.038) |
| `hessian_ridge` | 0.57 (0.030) | 0.94 (0.089) | 0.46 (0.036) | 0.92 (0.046) |
| `steerable_g2` | 0.71 (0.025) | 0.97 (0.084) | 0.59 (0.042) | 0.95 (0.064) |
| `mmt` | 0.69 (0.015) | 0.97 (0.059) | 0.50 (0.033) | 0.93 (0.072) |
| `noise_gate` | 0.53 (0.026) | 0.94 (0.080) | 0.42 (0.028) | 0.92 (0.041) |
| `coherence_diffusion` | 0.99 (0.006) | 0.99 (0.036) | 0.81 (0.036) | 0.95 (0.099) |

- `steerable_g2` shows as much confirmed fine detail as ACHF iso 04 with less than half the unconfirmed part, and
  more of the medium and coarse structure beyond 2.5 R☉ is confirmed.
- `mmt` is cleaner than ACHF iso 04 in the fine band but shows less fine detail; beyond 2.5 R☉ more of its medium
  and coarse structure is confirmed.
- `hessian_ridge` adds a little confirmed contrast and a little noise. An audit that compared every layer of AEL
  with every other on the same stacks found `hessian_ridge` nearly the same layer as ACHF iso 04 (correlation
  0.98–1.00) and `noise_gate` the same (1.000 up to 4 R☉).
- `coherence_diffusion` has almost no fine detail by design; between 2.5 and 4 R☉ it shows the medium structure
  with twice the confirmed share of ACHF iso 04.
- `noise_gate` brings no measurable gain on these stacks: their noise is already low (0.15–0.3 % per pixel inside
  4 R☉), and from 4 to 6 R☉ no layer shows fine or medium detail that both optics confirm.

## Limits

- The yardstick counts as confirmed a defect that a filter makes alike in both optics (a halo around a real ray,
  for example). Fine detail more than 2.5 R☉ from the Sun is noise in every layer on these stacks.
- The diffusion only smooths, but on pure noise it organises the noise into strokes; between 4 and 6 R☉ the
  yardstick confirms only 14 % of its medium band. Judge it with a null control on your data.
- Each layer is shown with a level and a spread per ring, like the ACHF layers: far from the Sun, where the sky is
  noise, that display gives the noise almost the same contrast as the corona. Lower the opacity or keep the layer off
  the sky.
- Two stacks of one eclipse; other optics and noise levels may rank the layers differently.
