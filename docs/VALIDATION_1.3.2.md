# Validation of 1.3.2 (prepared 2026-10-15, not released)

- `python -m ael selftest`: **76 of 76** (69 from 1.3.1 and 7 new in `ael/_tests/test_review.py`).
- The detail-transfer regression of the sixteen filters (`test_filters_keep_injected_fine_detail_with_its_sign_and_strength`)
  still passes against the 1.3.0 values: the NRGF change leaves the transfer of faint detail as it was
  (0.644 and 0.621 against 0.64 and 0.62).
- The review of this version found four faults in its first commit (a constant input gave an output, flat profile
  ends next to gaps, a linear fit at the ends of short runs, a non-robust slope), plus two in Upsilon (missing values
  turned into mid grey with a zero exponent, an explicit curve ignored by `rhef_upsilon`). All six are fixed and now
  have tests or mutations below.
- A second review found one more: the test for a spread that is zero to rounding compared each annulus with the
  brightest annulus of its run, so on a profile that falls by six decades the faintest annuli were dropped although
  they carried real structure. The tolerance now uses each annulus' own level; the test and mutation M8 below cover
  it, and the ripple table is unchanged.

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
the 4 px on each side of the gap.

| | Inside edge | Outside edge |
|---|---|---|
| 1.3.1 | −2.85 | +2.93 |
| 1.3.2 | −0.01 | −0.003 |

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
| Zero-spread tolerance from the brightest annulus of the run (M8) | faint annuli beside bright ones; Upsilon options |
| `rhef_upsilon` ignoring an explicit `upsilon_curve` | faint annuli beside bright ones; Upsilon options |
| A filter other than the RHEF accepting `upsilon_curve` silently | faint annuli beside bright ones; Upsilon options |

All ten were detected. The blend-algebra test has no mutation: it checks an identity and carries its own negative
control (Overlay at the same opacity).

Logs and scripts are kept with the author (`3-AEL/proves/validacio_1.3.2/`).
