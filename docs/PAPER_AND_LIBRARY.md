# The published layers of the paper and the filters of this library

The paper *A Faithful Corona* describes the filter layers of the author's published image of 12 August 2026.
The package `ael` implements portable recipes of the same published methods. They are general-purpose
parameterisations and they are not byte replays of those layers. An external review of the paper draft
(October 2026) found that the paper, the code behind the published layers and the library described three
different operators for the NRGF and the RHEF. This page says what each one does, filter by filter.

"Production" means the code that made the layers of the published image, under `3-RECERCA/tools/` (the paper's
image is version V125 of the project). "Library" means `ael` 1.3.2.

## NRGF (Morgan, Habbal and Woo 2006)

| | Production (published layers) | Library (`make_filter('nrgf')`) |
|---|---|---|
| Input | Green channel of the linear composite, stars removed | Luminance; `nrgf_log` uses ln L |
| Rings | 1 px; partial rings completed from the 40 complete rings outside | 2 px |
| Statistics | Mean and standard deviation, interpolated linearly to each pixel's radius | Median and 1.4826·MAD (`robust=False`: mean and standard deviation), nodes at the exact ring centres with the local slope removed, spread measured about the continuous mean profile, profiles smoothed by a local quadratic fit and interpolated by PCHIP |
| Display | Affine stretch; the same NRGF twice, with two stretches | `0.5 + 0.5·tanh(q/(2.5·MAD))` |
| Limits | Local dark structure compressed to 0.2 (σ 400 px); a limiter that restrains darkening relative to an estimated sky level | None |
| Blend | Multiply, 39 % and 14 % | Multiply |
| Code | `v98_20260925/f3_filtres_v98.py` (stage E1), `v115_nrgf_20260929/g2_nrgf_fosc.py` (variant `Lk20_G_MAX_T_e30_W_H0`) | `ael/radial.py` (`continuous_nrgf`), `ael/filters.py` (`nrgf`) |

## RHEF (Gilly and Cranmer 2025)

| | Production (published layers) | Library (`make_filter('rhef_local30')` etc.) |
|---|---|---|
| Input | ln of the green channel minus a radial profile smoothed with σ = 16 px | ln of the luminance |
| Rings | Radii every 0.5 px, interpolated | 2 px annuli, 257 quantiles each, interpolated in radius |
| Local variant | Sectors of 60° or 30°, nodes every quarter sector, interpolated; symmetric sample pairs near the edges of the data | The same sectors and nodes; quantiles interpolated in angle |
| Limits | Ranks below 0.5 raised to 0.5, then the change smoothed with σ = 400 px subtracted again | None; Upsilon optional (`upsilon_curve=(low, high)`) |
| Blend | Multiply, 3 % (60°) and 12 % (30°) | Multiply |
| Code | `v112_20260928/rhef_mass.py`, `v115_nrgf_20260929/r2_rhef_fosc_local.py` | `ael/radial.py` (`radial_quantile_rank`), `ael/filterbank.py` |

Ranked within sectors, the RHEF becomes an adaptive histogram equalisation on a polar grid. It gives up the
whole-ring normalisation that defines the RHEF, and a brightness that changes steadily across a sector comes out
mid grey; the large-scale contrast between directions has to come from another layer (the NRGF, here).

## MGN, WOW and ACHF

| Filter | Production (published layers) | Library |
|---|---|---|
| MGN (Morgan and Druckmüller 2014) | Green channel; sizes 1.25–40 px, k 0.7, γ 3.2, global weight 0.7; Multiply 5 % | The same parameters; display from the 1st–99th percentiles; **Overlay** |
| WOW (Auchère et al. 2023) | Green channel; 8 scales, equal weights, no global noise threshold; edge-aware and standard; the edge-aware layer with a local preprocessing step from a fixed signal-to-noise map on its three finest scales; Overlay 37 % and 3 % | 6 scales on the residual of ln L about a smooth radial spline, a noise floor of 3× the measured noise; Overlay |
| ACHF (Druckmüller et al. 2006, as published in Druckmüllerová's thesis) | Isotropic on ln of the luminance; along-the-arc variants on the green of each instrument; Overlay 8 %, 2 % and 3 % | Isotropic on the residual of ln L about a smooth radial spline; along-the-arc on ln L; Overlay |

## Blending a layer centred on mid grey

For an opacity α and a layer value s, `1 − α + α·s = (1 − α/2)·[1 + α/(2 − α)·(2s − 1)]`. Multiply with a
layer centred on 0.5 is a darkening by (1 − α/2) times a modulation symmetric about mid grey. On a base no
brighter than mid grey, Overlay at α/(2 − α) gives the same structure and only the level changes; above mid grey
Overlay follows its screen branch and the tone differs (test
`test_multiply_is_a_uniform_darkening_times_a_modulation_symmetric_about_mid_grey`).

What deepens faint gaps between rays is the equalisation itself. A rank treats all differences alike, so a gap
0.5 % deep can take the same rank as one of 15 %; the RHEF paper says so in its discussion. Measured on the 2026
eclipse, on a reconstructed stack of the published layers (`3-RECERCA/`, October 2026), with the excess darkness
at ten places the photographer had marked, against a reference composite that had also been used to choose the
published limits (so it is not an independent judge):
- the published limits: 19.3;
- removing the RHEF limit, in Multiply: 29.4; in Overlay at matched strength: 29.4;
- Upsilon (0.35 on both sides) instead of the RHEF limit: 20.1.

Upsilon, the authors' own curve, tempers both tails of the ranks. Whether it recovers coronal structure better
than a one-sided limit has not been tested.

## Sky and extinction

A ring filter normalises every ring around the Sun. An additive sky gradient, or the differential extinction of
a low Sun (the side of the corona towards the horizon dimmed more than the side towards the zenith), becomes
apparent angular structure. Subtract a sky model first and correct the extinction (`ael.extinction`) when the
Sun is low. The published layers of the paper were computed without either correction.

## Controls added in 1.3.2

In `ael/_tests/test_review.py`:
- ring ripple with faint (2 %) structure on a steep r⁻³ profile, against the sampling floor of the flattened input, with the 1.2.0 operators and the 1.3.1 NRGF as negative controls;
- the blend algebra above, with Overlay at the same opacity as a negative control;
- the Upsilon curve against eq. 2 of the RHEF paper;
- a structureless corona (photon noise only, off-centre Moon, straight edge) through the ring filters: no rings and no seams at the quarter-sector nodes, measured as the correlation between two noise realisations, with positive controls;
- the local RHEF with Upsilon keeps the sign of faint detail, with a lower gain.
