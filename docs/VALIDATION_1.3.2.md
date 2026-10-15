# Validation of 1.3.2 (prepared 2026-10-15, not released)

- `python -m ael selftest`: **84 of 84** (69 from 1.3.1 and 15 new in `ael/_tests/test_review.py`).
- The detail-transfer regression of the sixteen filters (`test_filters_keep_injected_fine_detail_with_its_sign_and_strength`)
  still passes against the 1.3.0 values: 0.644 and 0.622 for the NRGF and its logarithmic form (0.64 and 0.62 in 1.3.0).
- `spread_about='bin'` gives the 1.3.1 output bit for bit: 24 of 24 outputs over four scenes, both statistics and three
  parameter sets (`p12_bin_igual_que_131_i_temps.log`).
- The new NRGF takes about five times as long as that of 1.3.1: 2.66 s against 0.56 s on a 2000 × 2000 image with the
  filter bank's parameters (same log).

The logs and scripts named below are kept with the author (`3-AEL/proves/validacio_1.3.2/`).

## The NRGF of 1.3.2 in brief

- Each 2-pixel annulus gives a node at the mean radius of its own pixels. Inside the annulus, the profile's slope and
  curvature are removed before the median (or mean) is taken. Both come from the quartic through the five nearest
  median nodes (the cubic through four next to the ends of a run), refined up to four times; with the mean statistic
  only the level of each node is a mean.
- A cubic Hermite curve through the nodes, with those slopes, gives the profile at every pixel's radius and continues
  it inside the end annuli; a node moves only the two intervals beside it. The spread is measured about that profile
  and interpolated without overshoot (PCHIP on its logarithm), held at the end nodes.
- Each run is modelled on the values and on their logarithm, or, when a node is not positive (a subtracted sky taking
  the far corona through zero), on asinh(I/s) with s the median size of the nodes. The run keeps the model with the
  smaller score: the sum over its annuli of the logarithm of the mean square residual about the profile (residuals
  clipped at five spreads; a float32 floor added).
- No output: in runs of fewer than four annuli; in annuli where half the pixels share one value (zeros, clipping,
  integers coarser than the noise: the MAD is zero); and in annuli without angular signal, that is, whose residuals,
  once a smooth function of radius is removed, spread less than one float32 step of the annulus' own operands (the
  median size of its values, and its slope times the radius; at least the smallest subnormal). The radii are exact
  (float64), so that their rounding does not pass for angular signal on a steep radial ripple. Two such functions are
  tried and the smaller spread is kept: one through the residuals, in radial bands a tenth of a pixel wide, and one
  through the values themselves (which have no kinks where the profile's pieces meet), in bands half as wide. Each
  band holds at least 24 samples at four or more different radii and gives the value at its centre of a parabola
  fitted inside it; a cubic spline joins the bands. The bands are too coarse to follow angular structure even where
  pixels at one radius are mirror images of each other (a centre on the pixel grid).
- The nodes are not smoothed by default (`smooth_bins=0`, also in `make_filter`). `make_filter('nrgf')` keeps pixels
  at or below zero; `nrgf_log` and the rank filters still need positive ones.

## How the reviews shaped it

The first commit of 1.3.2 replaced the Gaussian smoothing of 1.3.1 with nodes at the exact centre of each annulus,
the annulus' own slope removed, and a local polynomial. Ten rounds of review by an independent agent at high
reasoning effort, and two adversarial checks (four readers and a verifier, then three readers and a verifier), found
the following. Everything is fixed except what is listed under Limits.

1. A constant input gave an output; the profile was held flat next to gaps; a straight-line fit at the ends of short
   runs; a slope that one pixel could move; in Upsilon, missing values became mid grey and `rhef_upsilon` ignored an
   explicit curve.
2. The test for a spread that is zero to rounding compared each annulus with the brightest of its run, so a profile
   falling six decades lost its faintest annuli.
3. A straight profile through zero passed rounding as structure. Checking it showed that the node removed the slope but
   not the curvature: on a clean stack, an offset of several sigma.
4. The first adversarial check confirmed 18 defects (`verificacio_adversa_4c1fe12.json`), among them: one non-positive
   pixel switched the whole run to the model on the values, which the node smoothing then biased by up to 10 sigma; the
   node smoothing itself left 2.5 sigma on a Baumbach corona and up to 13 sigma on a Sun of 15 to 25 px; where an edge
   cut an annulus, the node was extrapolated to the annulus' centre (up to 4 sigma); with the median, a slope from the
   two halves of an annulus was thrown off by angular structure (up to 1.3 sigma); noiseless, purely radial curved
   profiles gave rings of up to 47 sigma.
5. A fifth review found that the spread, extrapolated by a cubic spline, could dip towards zero (|q| = 50 next to a
   narrow ring of structure; now 1.6), that the choice of model depended on the units of the data (correlation 0.82 at
   10⁻²⁸ of the original scale; now 0.9998), and that three annuli were too few on a Baumbach corona (correlation
   0.27; now no output, and 0.99 with four).
6. The second adversarial check confirmed 16 defects in the next commit (`verificacio_adversa_e82aa49.json`): exact
   ties (a zero-padded frame, a clipped inner corona, 8-bit data with noise below one grey level) reached |q| = 10³⁷;
   a sky subtracted slightly too deep left 0.3 to 0.8 sigma at the limb; `make_filter` dropped every pixel at or below
   zero (up to a third of a subtracted far corona); a radial step or kink inside an annulus gave rings without noise;
   no test checked the unit of q, the `min_count` boundary or a floor three times too high; sharp changes of curvature
   left up to 1.5 sigma on a clean stack; with the mean statistic, one bright pixel moved several annuli.
7. A sixth review found that the detector of angular signal then in use (each residual against the running median of
   its nine neighbours in radius) took structure with 4-fold symmetry for a radial profile when the centre sat on the
   pixel grid, and dropped 73 % of the data; and that `make_filter('nrgf')` refused an input negative everywhere.
   Checking how far a bright pixel reaches with the mean statistic showed that the global spline then used for the
   profile carried it about 1 sigma five annuli away; the profile is now local and its shape comes from median nodes.
8. A seventh review found that the plain mean of each radial band, which the next detector used, is off the profile
   by its curvature times the band width squared over 24: a noiseless radial ripple (2 %, period 6 px) then gave
   output everywhere. Each band now gives the value of a parabola fitted inside it.
9. An eighth review found that, around a 25-px Sun centred on a pixel corner, that ripple still gave output on 26 %
   of the field: many bands held only one or two different radii, where a parabola is not determined. Measuring the
   case over 15 geometries showed a wider limit than first declared: off the grid as well, up to 40 px with the
   6-px ripple and up to 60 px with a 3-px one; the profile's own kinks (where the pieces of the Hermite curve meet)
   also stayed in the residuals. Each band now holds four different radii or more, and a second function of radius
   is fitted to the values. Over 150 noiseless radial profiles the share of output fell from 0.235 to 0.154, with no
   output left at 60 or 100 px, and symmetric structure down to 3·10⁻⁶ kept its coverage
   (`p17_perfils_radials_sense_soroll.log`).
10. A ninth review found a strong radial ripple (20 %, period 4 px) giving output on 95 % of the field around a
   100-px Sun, without noise. The radius map was float32, and its rounding times the ripple's own slope (ten times
   the profile's) passed for angular signal. Raising the floor by that slope cured it, but a tenth review showed that
   it also dropped real structure of 10⁻⁵ on the same ripple (coverage 99 % → 0 around a 440-px Sun). The cure went
   one floor down: the new NRGF now works on exact radii and keeps the earlier floor. With the median, the ripple
   gives no output and the 10⁻⁵ structure keeps 99 % of the field (`p18_contraexemples_ronda12.log`,
   `p19_contraexemple_ronda13.log`).

The readers' scripts, rerun on the final code: `verificacio_adversa_guions_dels_lectors_banc.log` (first check, filter
bank's parameters), `verificacio_adversa_guions_dels_lectors.log` (first check, with the node smoothing they were
written with) and `verificacio_adversa_e82aa49_guions_dels_lectors.log` (second check).

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
| 60 px | 0.05 | 0.04 | 0.06 |
| 120 px | 0.05 | 0.04 | 0.04 |
| 200 px | 0.04 | 0.03 | 0.03 |
| 60 px, earlier draft (`875e817`) | 0.19 | 0.76 | 6.1 |
| 60 px, nodes smoothed over 3 annuli | 0.08 | 0.06 | 0.61 |

With the mean statistic every cell is at most 0.02. Over ten noise seeds (Sun of 120 px, noise 10⁻⁴) the worst annulus
stays at or below 0.08 with the median and 0.01 with the mean; with the data starting anywhere inside the first annulus
of a 60- or 120-px Sun, that annulus averages within 0.01 over eight seeds (`p10_llavors_i_vores.log`).

## Edges of the data

Steep profile (60-px Sun, r⁻³, 2 % structure) with a gap in the data between 100 and 104 px: median of the NRGF on
the 4 px on each side of the gap (`p8_vores_buit.log`; the mean statistic agrees within 0.01).

| | Inside edge | Outside edge |
|---|---|---|
| 1.3.1, nodes smoothed over 3 annuli | −2.85 | +2.13 |
| 1.3.1, no smoothing | −0.19 | +0.19 |
| 1.3.2 | 0.000 | 0.000 |

## Faint structure

cos 5θ structure on a 60-pixel Sun, noiseless: correlation of the NRGF with the structure (`p7_estructura_feble.log`).

| Profile, structure | Earlier draft (`875e817`) | 1.3.2 |
|---|---|---|
| Six decades (exponential), 10⁻⁴ | 0.08 | 1.00 |
| Six decades, 10⁻² | 0.99 | 1.00 |
| r⁻³, 10⁻⁴ | 0.42 | 1.00 |
| r⁻³, 10⁻³ | 0.97 | 1.00 |

Runs of four and five annuli keep 10⁻⁴ structure (correlation 1.00 on r⁻³; 0.99 and 0.98 on a Baumbach corona); runs
of one to three give no output (`p9_contraexemples_ronda7.log`, `p14_contraexemples_ronda8.log`). The same six-decade
scene scaled by 10⁻²⁸ or 10²⁸ gives the same correlation (0.9998).

## Bad pixels, ties and numerical inputs

- One zero or negative pixel at 71 px on the six-decade profile leaves the layer beyond 100 px unchanged. With the
  median, one pixel 10 to 10⁷ times too bright changes the rest of its annulus by less than 0.01 sigma and the other
  annuli by less than 0.004 (`p15_pixel_dolent_i_simetria.log`).
- Structure with 2-, 4- or 8-fold symmetry, with the centre on the pixel grid, on half a pixel or off it, is kept
  whole (correlation 0.999 or more); `make_filter('nrgf')` takes an input negative everywhere (same log).
- Constants (3, −3, 0), straight profiles through zero (at 100, 101 and 101.3 px; scales 10⁻⁶ to 10⁶; float32 and exact
  radii), noiseless r⁻³ and Baumbach profiles, a radial step or kink inside an annulus, and the same at subnormal
  scale give no output with either statistic; so does a noiseless corona around a 15-px Sun.
- Ties: a zero-padded frame and a clipped inner corona give no output where half or more of an annulus is tied; 8-bit
  data keep their output when the noise is one grey level or more (|q| ≤ 4) and give none at half a level.
- A sky subtracted too deep (a Baumbach corona whose far annuli average below zero) is modelled on asinh: every annulus
  within 0.05 sigma (on the values it kept 0.63).
- Noiseless, the floor removes angular structure only when it is fainter than about 10⁻⁶ of the brightness: from
  3·10⁻⁷ on r⁻³ to about 10⁻⁶ on steep exponentials, about ten float32 steps; on a bright pedestal 3·10⁻⁷ survives
  (`p13_sol_i_estructura_feble.log`).

## Limits

- Explicit node smoothing (`smooth_bins` > 0) bends a profile whose power-law index changes. At three annuli: 2.4 sigma
  on a Baumbach corona (120-px Sun, noise 10⁻⁴); 1.6 sigma on a 15-px Sun at noise 10⁻³ and 6.7 sigma at 10⁻⁴. The nodes
  average hundreds of pixels, so without smoothing their own noise is a few hundredths of sigma.
- Where the curvature of the profile changes within a few pixels (an exponential of 6-px scale meeting a sky floor), a
  very clean stack (noise 10⁻⁴) keeps up to 0.5 sigma in a few annuli; at noise 10⁻³ every annulus is within 0.15.
- With the mean statistic (`robust=False`, the original form of Morgan, Habbal and Woo), one bright pixel also moves
  the next annulus and, less, the one after, as in 1.3.1. In the second check's scene, a pixel 1000 times too bright
  changes the layer by 0.73, 0.08 and 0.001 sigma on average one, two and three annuli away (1.3.1: 0.42, 0.06 and 0);
  10 times too bright, by 0.17, 0.001 and 0 (1.3.1: 0.17, 0.004 and 0) (`verificacio_adversa_e82aa49_guions_dels_lectors.log`). Where the Moon is off-centre and streamers cross the
  crescent, the first annulus averages up to 0.6 sigma low and the inner half of it up to 2.5 sigma low
  (`verificacio_adversa_e82aa49_guions_dels_lectors.log`). With the median, the default, that annulus stays within
  0.01 and its inner half within +0.9.
- Around a 15-px Sun with the data starting exactly at 16 px, the first annulus can sit 0.4 sigma high with the median
  on a very clean stack (noise 10⁻⁴).
- In noiseless data, a purely radial feature a few pixels long can still give output around a small Sun: in the
  scenes measured, a 2 % ripple with a 3-px period up to a 40-px Sun (the whole field at 15 to 25 px with the mean
  statistic), a 6-px period up to 20 px, a 1-px step at 10 px; at 60 and 100 px, none
  (`p17_perfils_radials_sense_soroll.log`; on a pixel corner, `p16_sol_petit_centrat_sense_soroll.log`). The function
  of radius cannot follow such a feature down to float32 rounding; |q| reached 6.5 there, and 8.4 in a scene of the
  ninth review with the Moon off-centre. On the pixel grid, mirror-image pixels share so few distinct radii that a
  narrower function of radius would also absorb mirror-symmetric angular structure, which is kept.
- Radial structure only a few annuli wide is followed in part by a profile measured on 2-px annuli; what the profile
  misses stays in the layer as rings, in units of the estimated residual spread. A 2 % ripple of 6 px gives annulus means up to 11 sigma
  around a 15-px Sun on a very clean stack (noise 3·10⁻⁶), 0.7 sigma at noise 10⁻⁴ and 0.2 at 10⁻²; around a 60-px
  Sun, up to 0.75 sigma. 1.3.1 measured the spread about each annulus' own median, which absorbs such a ripple
  (0.3–0.5 sigma).
- With the mean statistic, that 20 % ripple of 4 px (two annuli per period) still gives output on about a tenth of
  the field around a 100-px Sun: the function of radius cannot follow it to rounding, and the standard deviation
  picks up its largest misses (`p18_contraexemples_ronda12.log`).
- An input made on float32 radii (as `radius_map()` gives by default) carries that rounding times its slope: on a
  steep radial ripple it is real jitter at about 10⁻⁶ of the brightness, and the layer shows it.
- A run of fewer than four annuli gives no output: the end nodes need the cubic through four nodes.
- The new operator is about five times slower than that of 1.3.1.

## Mutations

Each fault must be detected by a test (`mutacions.log`). "NRGF tests" means the eleven review tests of the NRGF run
together.

| Mutation | Test that detects it |
|---|---|
| The 1.3.1 NRGF (`spread_about='bin'`) | faint structure on a steep profile |
| Upsilon with the low exponent on both sides | the Upsilon curve |
| `make_filter` ignoring `upsilon_curve` | local RHEF with Upsilon |
| A fixed seam at 24 cycles per turn added to every ring layer | structureless corona |
| Fixed rings of 7 px added to every ring layer | structureless corona |
| Nodes without slope or curvature removed | NRGF tests |
| A three-node mean instead of the local parabola (smoothing) | constants, gaps, short runs, outlier |
| Numerical floor from the brightest annulus of the run | NRGF tests |
| `rhef_upsilon` ignoring an explicit `upsilon_curve` | faint annuli beside bright ones |
| A filter other than the RHEF accepting `upsilon_curve` silently | faint annuli beside bright ones |
| Numerical floor without the slope times the radius | NRGF tests |
| Nodes without the curvature removed | NRGF tests |
| The logarithm always preferred when it can be used | NRGF tests |
| Every run modelled on the values | NRGF tests |
| The model chosen by the spread instead of the mean square misfit | bad pixels, partial annuli and short runs |
| Smoothing window cut on one side near the ends | constants, gaps, short runs, outlier |
| Node at the annulus' centre, not at the mean radius of its pixels | NRGF tests |
| PCHIP instead of the Hermite curve for the profile | NRGF tests |
| The logarithm requiring every pixel to be positive | NRGF tests |
| Numerical floor from the mean size of the values | NRGF tests |
| Runs of one to three annuli giving output | NRGF tests (the code fails) |
| Slope from the two halves of the annulus | NRGF tests |
| Derivatives from the three-node parabola, also at the ends | NRGF tests |
| No-output decision on the total spread, not the angular spread | NRGF tests |
| Node smoothing over 3 annuli in the filter bank | filter bank without node smoothing |
| Numerical floor without the subnormal step | NRGF tests |
| A single refinement of the nodes | NRGF tests |
| Angular part from the running median of nine pixels in radius, not the bands | NRGF tests |
| The spread from the cubic spline, extrapolated at the ends | NRGF tests |
| No asinh model | NRGF tests |
| No rule for ties | NRGF tests |
| Spread ten times too large | NRGF tests |
| MAD without its factor 1.4826 | NRGF tests |
| `min_count` off by one | NRGF tests |
| Numerical floor three times too high | NRGF tests |
| `make_filter('nrgf')` dropping pixels at or below zero | ties, zeros, clipping, a sky below zero; negative input |
| A global spline instead of the local Hermite curve | NRGF tests |
| With the mean statistic, the shape from mean nodes | NRGF tests |
| Plain means of the radial bands instead of the parabola inside each | NRGF tests |
| Bands without the minimum of four different radii | NRGF tests |
| Angular part from the function of radius of the residuals only | NRGF tests |
| Angular part from the function of radius of the values only | NRGF tests |
| The new NRGF on float32 radii instead of exact ones | NRGF tests |

All 43 were detected, one of them because the mutated code fails. Choosing the model by the spread changes the output in 17 of 128 calls of the review tests; a five-annulus run on r⁻³ drops from correlation 0.9996 to 0.959, which the test of short runs now catches (it asks 0.99 on r⁻³). The blend-algebra test has no mutation: it checks
an identity and carries its own negative control (Overlay at the same opacity).
