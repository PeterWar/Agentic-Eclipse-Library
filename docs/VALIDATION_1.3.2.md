# Validation of 1.3.2 (prepared 2026-10-15, not released)

- `python -m ael selftest`: **79 of 79** (69 from 1.3.1 and 10 new in `ael/_tests/test_review.py`).
- The detail-transfer regression of the sixteen filters (`test_filters_keep_injected_fine_detail_with_its_sign_and_strength`)
  still passes against the 1.3.0 values: 0.644 and 0.622 for the NRGF and its logarithmic form (0.64 and 0.62 in 1.3.0).
- `spread_about='bin'` gives the 1.3.1 output bit for bit: 24 of 24 outputs over four scenes, both statistics and three
  parameter sets (`p12_bin_igual_que_131_i_temps.log`).
- The new NRGF takes about three times as long as that of 1.3.1: 1.27 s against 0.37 s on a 2000 × 2000 image with the
  filter bank's parameters (same log).

## The NRGF of 1.3.2 in brief

- Each 2-pixel annulus gives a node at the mean radius of its own pixels. Inside the annulus, the profile's slope and
  curvature are removed before the median (or mean) is taken; both come from the parabola through the node and its two
  neighbours, and at the two end nodes of a run from the cubic through the four nearest nodes, refined up to four times.
- A not-a-knot cubic spline through the nodes gives the profile at every pixel's radius, and continues it inside the end
  annuli of a run.
- Each run is modelled both on the values and on their logarithm (the node statistics must be positive; single
  non-positive pixels are allowed) and keeps the model with the smaller mean square misfit, annulus by annulus.
- The spread is measured about that continuous profile. An annulus whose residuals, once a cubic in radius is removed
  inside it, spread less than one float32 step of its own operands (the median size of its values, and its slope
  times the radius; at least the smallest subnormal) has no angular signal and gives no output. So does a run of
  fewer than three annuli.
- The nodes are not smoothed by default (`smooth_bins=0`, also in `make_filter`).

## How the reviews shaped it

The first commit of 1.3.2 replaced the Gaussian smoothing of 1.3.1 with nodes at the exact centre of each annulus,
the annulus' own slope removed, and a local polynomial. Four rounds of review by an independent agent at high reasoning
effort, and one adversarial check with four readers and a verifier, found the following; all of it is fixed:

1. A constant input gave an output; the profile was held flat next to gaps; a straight-line fit at the ends of short
   runs; a slope that one pixel could move; in Upsilon, missing values became mid grey and `rhef_upsilon` ignored an
   explicit curve.
2. The test for a spread that is zero to rounding compared each annulus with the brightest of its run, so a profile
   falling six decades lost its faintest annuli.
3. A straight profile through zero passed rounding as structure. Checking it showed that the node removed the slope but
   not the curvature: on a clean stack, an offset of several sigma.
4. The adversarial check of that version confirmed 18 defects and rejected 2 (`verificacio_adversa_4c1fe12.json`):
   - one non-positive pixel anywhere in a run switched the whole run to the model on the values, which the node
     smoothing then biased by up to 10 sigma;
   - the node smoothing itself left 2.5 sigma on a Baumbach corona and up to 13 sigma on a Sun of 15 to 25 px;
   - where an edge cut an annulus, the node was extrapolated from its data to the annulus' centre (up to 4 sigma);
   - with the median, the slope from the two halves of an annulus was thrown off by angular structure, because the
     halves see different angles (up to 1.3 sigma);
   - one bright pixel switched off its annulus through the mean size of the values in the numerical floor, and
     subnormal inputs passed rounding as structure;
   - noiseless, purely radial curved profiles gave rings of up to 47 sigma;
   - three numbers in these documents were wrong.
5. Checking those fixes showed two more: near a dip in the profile, the median nodes needed more refinements (0.43
   sigma with two), and a sky-subtracted corona, modelled on the values, kept 0.6 sigma at its bright end until the
   end nodes used a cubic.

The readers' own scripts, rerun on the final code with the filter bank's present parameters
(`verificacio_adversa_guions_dels_lectors_banc.log`): every case they built stays within 0.15 sigma per annulus, and where
there is no angular signal there is no output. With the node smoothing
they were written with (three annuli; `verificacio_adversa_guions_dels_lectors.log`), steep profiles still bend, as
documented under Limits.

## Concentric ripple with faint structure

Scene: I = r⁻³·(1 + 0.02·cos 5θ), off-centre Sun, data from 1.05 to 2.6 R☉. Metric: the standard deviation of the
azimuthal mean in 0.25-px radial steps between 1.05 and 1.6 R☉, after removing anything slower than ~6 px; 7.5 px at
each end of the range are left out, and the edges of the data are checked separately. The floor is the same layer
computed on the exactly flattened input I·r³ (the sampling noise of the pixel grid). `ondulacio_terra.log`.

| Sun radius | Layer | Floor | 1.3.2 | 1.2.0 (hard bins) |
|---|---|---|---|---|
| 120 px | RHEF, whole ring | 0.0198 | 0.0163 (0.82×) | 0.1735 (8.8×) |
| 120 px | RHEF, 30° sectors | 0.0161 | 0.0072 (0.45×) | 0.2399 (14.9×) |
| 120 px | NRGF | 0.0083 | 0.0083 (1.00×) | 0.0967 (11.6×) |
| 200 px | RHEF, whole ring | 0.0157 | 0.0138 (0.88×) | 0.1217 (7.8×) |
| 200 px | RHEF, 30° sectors | 0.0131 | 0.0074 (0.56×) | 0.1919 (14.6×) |
| 200 px | NRGF | 0.0065 | 0.0065 (1.00×) | 0.0652 (10.0×) |

The 1.3.1 NRGF gave 2.5× (120 px) and 1.9× (200 px). The 1.3.1 radial rank was already at the floor and is unchanged.

## A clean corona without structure

r⁻³ with noise only, data from 1.05 to 2.6 R☉: the largest azimuthal mean of the NRGF over the 2-px annuli, in sigma.
An unbiased profile gives ~0. Filter-bank parameters, median statistics; `p6_biaix_sense_estructura.log`.

| Sun radius | Noise 10⁻² | Noise 10⁻³ | Noise 10⁻⁴ |
|---|---|---|---|
| 60 px | 0.05 | 0.05 | 0.08 |
| 120 px | 0.05 | 0.04 | 0.04 |
| 200 px | 0.04 | 0.03 | 0.03 |
| 60 px, earlier draft (`875e817`) | 0.19 | 0.76 | 6.1 |
| 60 px, nodes smoothed over 3 annuli | 0.08 | 0.06 | 0.61 |

With the mean statistic every cell is at most 0.06. Over ten noise seeds (Sun of 120 px, noise 10⁻⁴), the worst annulus
stays at or below 0.07 with the median and 0.01 with the mean; with the data starting at 62, 62.5, 63 and 63.5 px around
a 60-px Sun, or anywhere inside the first annulus of a 120-px Sun, the first annulus averages within 0.01 over eight
seeds (`p10_llavors_i_vores.log`).

## Edges of the data

Steep profile (60-px Sun, r⁻³, 2 % structure) with a gap in the data between 100 and 104 px: median of the NRGF on
the 4 px on each side of the gap (`p8_vores_buit.log`; the mean statistic agrees within 0.01).

| | Inside edge | Outside edge |
|---|---|---|
| 1.3.1, nodes smoothed over 3 annuli | −2.85 | +2.13 |
| 1.3.1, no smoothing | −0.19 | +0.19 |
| 1.3.2 | 0.000 | 0.000 |

## Faint structure on curved profiles

cos 5θ structure on a 60-pixel Sun, noiseless: correlation of the NRGF with the structure (`p7_estructura_feble.log`).

| Profile, structure | Earlier draft (`875e817`) | 1.3.2 |
|---|---|---|
| Six decades (exponential), 10⁻⁴ | 0.08 | 1.00 |
| Six decades, 10⁻² | 0.99 | 1.00 |
| r⁻³, 10⁻⁴ | 0.42 | 1.00 |
| r⁻³, 10⁻³ | 0.97 | 1.00 |

Runs of three, four and five annuli keep 10⁻⁴ structure (correlation 0.98, 1.00, 1.00); runs of one or two give no
output (`p9_contraexemples_ronda7.log`).

## Bad pixels and numerical inputs

- One zero or negative pixel at 71 px on the six-decade profile: the layer beyond 100 px does not change (it changed by
  7.9 sigma in the previous commit). One pixel 10⁷ times too bright leaves the rest of its annulus finite.
- Constants (3, −3, 0), straight profiles through zero (at 100, 101 and 101.3 px; scales 10⁻⁶ to 10⁶; float32 and exact
  radii), noiseless r⁻³ and Baumbach profiles, and the same at subnormal scale give no output with either statistic.
- The floor removes angular structure only when it is fainter than about 10⁻⁶ of the brightness: from 3·10⁻⁷ on r⁻³
  to 3·10⁻⁶ on an exponential falling six decades, about ten float32 steps; on a bright pedestal 3·10⁻⁷ survives
  (`p13_sol_i_estructura_feble.log`).

## Limits

- Explicit node smoothing (`smooth_bins` > 0) bends a profile whose power-law index changes: 2.4 sigma on a Baumbach
  corona (120-px Sun, noise 10⁻⁴) and 1.6 sigma on a 15-px Sun at three annuli. The nodes average hundreds of pixels,
  so their own noise is a few hundredths of sigma without it.
- A run of fewer than three annuli gives no output: inside one annulus, faint structure and the profile's curvature
  cannot be told apart.
- The new operator is about three times slower than that of 1.3.1.

## Mutations

Each fault must be detected by a test (`mutacions.log`):

| Mutation | Test that detects it |
|---|---|
| The 1.3.1 NRGF (`spread_about='bin'`) | faint structure on a steep profile |
| Upsilon with the low exponent on both sides | the Upsilon curve |
| `make_filter` ignoring `upsilon_curve` | local RHEF with Upsilon |
| A fixed seam at 24 cycles per turn added to every ring layer | structureless corona |
| Fixed rings of 7 px added to every ring layer | structureless corona |
| Nodes without slope or curvature removed | unbiased on clean curved profiles |
| A three-node mean instead of the local parabola | constants, gaps, short runs, outlier |
| Numerical floor from the brightest annulus of the run | faint annuli beside bright ones |
| `rhef_upsilon` ignoring an explicit `upsilon_curve` | faint annuli beside bright ones |
| A filter other than the RHEF accepting `upsilon_curve` silently | faint annuli beside bright ones |
| Numerical floor without the slope times the radius | unbiased on clean curved profiles |
| Nodes without the curvature removed | unbiased on clean curved profiles |
| A positive run always modelled on the logarithm | unbiased on clean curved profiles |
| Every run modelled on the values | unbiased on clean curved profiles |
| Smoothing window cut on one side near the ends | constants, gaps, short runs, outlier |
| Node at the annulus' centre, not at the mean radius of its pixels | bad pixels, partial annuli, short runs |
| PCHIP instead of the cubic spline | unbiased on clean curved profiles |
| The logarithm requiring every pixel to be positive | bad pixels, partial annuli, short runs |
| Numerical floor from the mean size of the values | bad pixels, partial annuli, short runs |
| Runs of one or two annuli giving output | bad pixels, partial annuli, short runs (the code fails) |
| Slope from the two halves of the annulus | unbiased on clean curved profiles |
| End nodes from a one-sided parabola | unbiased on clean curved profiles |
| No-output decision on the total spread, not the angular spread | unbiased on clean curved profiles |
| Node smoothing over 3 annuli in the filter bank | filter bank without node smoothing |
| Numerical floor without the subnormal step | unbiased on clean curved profiles |
| A single refinement of the nodes | unbiased on clean curved profiles |

All 26 were detected. One more mutation was not: choosing the model by the spread of the residuals instead of their
mean square misfit. With the present nodes, both criteria choose the same model in every test scene. The blend-algebra
test has no mutation: it checks an identity and carries its own negative control (Overlay at the same opacity).

Logs and scripts are kept with the author (`3-AEL/proves/validacio_1.3.2/`).
