# Validation of 1.3.2 (prepared 2026-10-15, not released)

- `python -m ael selftest`: **77 of 77** (69 from 1.3.1 and 8 new in `ael/_tests/test_review.py`).
- The detail-transfer regression of the sixteen filters (`test_filters_keep_injected_fine_detail_with_its_sign_and_strength`)
  still passes against the 1.3.0 values: the NRGF change leaves the transfer of faint detail as it was
  (0.644 and 0.621 against 0.64 and 0.62).
- The review of this version found four faults in its first commit (a constant input gave an output, flat profile
  ends next to gaps, a linear fit at the ends of short runs, a non-robust slope), plus two in Upsilon (missing values
  turned into mid grey with a zero exponent, an explicit curve ignored by `rhef_upsilon`). All six are fixed and now
  have tests or mutations below.
- A second review found one more: the test for a spread that is zero to rounding compared each annulus with the
  brightest annulus of its run, so on a profile that falls by six decades the faintest annuli were dropped although
  they carried real structure.
- A third review found that a straight profile crossing zero inside an annulus passed rounding as structure. Checking
  it showed a larger fault of the first commit: each node removed its annulus' slope but not its curvature, which
  left ~I''·<Δr²>/2 in the node and, on a very clean stack, a broad offset of several sigma. Now the node removes the
  local curvature as well; a run of positive annuli is also modelled on the logarithm and keeps the less biased
  model; the smoothing window is symmetric about each node; and a spread below four float32 steps of the annulus'
  own operands (its values, and its slope times the radius) is undefined. The ripple table is unchanged.

## Concentric ripple with faint structure

Scene: I = r⁻³·(1 + 0.02·cos 5θ), off-centre Sun, data from 1.05 to 2.6 R☉. Metric: the standard deviation of the
azimuthal mean in 0.25-px radial steps between 1.05 and 1.6 R☉, after removing anything slower than ~6 px; 7.5 px at
each end of the range are left out, and the edges of the data are checked by the gap test below. The floor is the
same layer computed on the exactly flattened input I·r³ (the sampling noise of the pixel grid).

| Sun radius | Layer | Floor | 1.3.2 | 1.2.0 (hard bins) |
|---|---|---|---|---|
| 120 px | RHEF, whole ring | 0.0198 | 0.0163 (0.82×) | 0.1735 (8.8×) |
| 120 px | RHEF, 30° sectors | 0.0161 | 0.0072 (0.45×) | 0.2399 (14.9×) |
| 120 px | NRGF | 0.0083 | 0.0083 (1.00×) | 0.0967 (11.6×) |
| 200 px | RHEF, whole ring | 0.0157 | 0.0138 (0.88×) | 0.1217 (7.8×) |
| 200 px | RHEF, 30° sectors | 0.0131 | 0.0074 (0.56×) | 0.1919 (14.6×) |
| 200 px | NRGF | 0.0065 | 0.0065 (1.00×) | 0.0652 (10.0×) |

The 1.3.1 NRGF gave 2.5× (120 px) and 1.9× (200 px). The 1.3.1 radial rank was already at the floor and is unchanged.

## Edges of the data

Steep profile (60-px Sun, r⁻³, 2 % structure) with a gap in the data between 100 and 104 px: median of the NRGF on
the 4 px on each side of the gap (`p8_vores_buit.log`; median statistics, the mean ones agree).

| | Inside edge | Outside edge |
|---|---|---|
| 1.3.1 | −2.85 | +2.13 |
| 1.3.2 | −0.004 | +0.002 |

`spread_about='bin'` reproduces the 1.3.1 output bit for bit (checked on this scene with both statistics).

## A clean corona without structure

r⁻³ with noise only, data from 1.05 to 2.6 R☉: the largest azimuthal mean of the NRGF over the 2-px annuli, in
sigma (an unbiased profile gives ~0; `p6_biaix_sense_estructura.log`, median statistics).

| Sun radius | Noise 10⁻² | Noise 10⁻³ | Noise 10⁻⁴ |
|---|---|---|---|
| 60 px, earlier 1.3.2 draft | 0.19 | 0.76 | 6.1 |
| 60 px, 1.3.2 | 0.20 | 0.40 | 1.38 |
| 120 px, earlier draft | 0.07 | 0.19 | 1.63 |
| 120 px, 1.3.2 | 0.06 | 0.09 | 0.09 |
| 200 px, earlier draft | 0.04 | 0.07 | 0.58 |
| 200 px, 1.3.2 | 0.04 | 0.04 | 0.07 |

What remains at a 60-pixel Sun with noise 10⁻⁴ is the fourth-order bias of the smoothing (σ = 3 annuli); it falls
with the fourth power of the window.

## Faint structure on curved profiles

cos 5θ structure on a 60-pixel Sun, noiseless: correlation of the NRGF with the structure (`p7_estructura_feble.log`).

| Profile, structure | Earlier 1.3.2 draft | 1.3.2 |
|---|---|---|
| Six decades (exponential), 10⁻⁴ | 0.08 | 0.99 |
| Six decades, 10⁻² | 0.99 | 1.00 |
| r⁻³, 10⁻⁴ | 0.42 | 0.97 |
| r⁻³, 10⁻³ | 0.97 | 1.00 |

A parabola above zero with noise 10⁻³ (a dip in the profile): largest annulus mean 0.83 sigma (10 sigma when the dip
is modelled on the logarithm).

## Numerical inputs

Constants (3, −3, 0) and straight profiles through zero (at 100, 101 and 101.3 px; scales 10⁻⁶ to 10⁶; float32
and exact radii) give no output with either statistic and with or without smoothing (`p6_biaix_sense_estructura.log`).

## Mutations

Each fault must be detected by a test:

| Mutation | Test that detects it |
|---|---|
| Plain Gaussian smoothing of the NRGF profile (the 1.3.1 behaviour) | faint structure on a steep profile |
| Upsilon with the low exponent on both sides | the Upsilon curve |
| `make_filter` ignoring `upsilon_curve` | local RHEF with Upsilon |
| A fixed seam at 24 cycles per turn added to every ring layer | structureless corona |
| Fixed rings of 7 px added to every ring layer | structureless corona |
| Profile held flat at the ends of each run (no slope of its own) | NRGF constants, gaps, short runs, outlier |
| A three-node mean instead of the local polynomial | NRGF constants, gaps, short runs, outlier |
| Numerical floor from the brightest annulus of the run | faint annuli beside bright ones; Upsilon options |
| `rhef_upsilon` ignoring an explicit `upsilon_curve` | faint annuli beside bright ones; Upsilon options |
| A filter other than the RHEF accepting `upsilon_curve` silently | faint annuli beside bright ones; Upsilon options |
| Numerical floor without the slope times the radius | unbiased on clean curved profiles; nothing for rounding |
| Node without the local curvature removed | unbiased on clean curved profiles; nothing for rounding |
| A positive run always modelled on the logarithm | unbiased on clean curved profiles; nothing for rounding |
| Every run modelled on the values | unbiased on clean curved profiles; nothing for rounding |
| The model chosen by its spread instead of its bias | unbiased on clean curved profiles; nothing for rounding |
| Smoothing window cut on one side near the ends (earlier draft) | NRGF constants, gaps, short runs, outlier |

All sixteen were detected (`mutacions.log`). The blend-algebra test has no mutation: it checks an identity and carries its own negative
control (Overlay at the same opacity).

Logs and scripts are kept with the author (`3-AEL/proves/validacio_1.3.2/`).
