# Validation of 1.3.2 (prepared 2026-10-15, not released)

- `python -m ael selftest`: **74 of 74** (69 from 1.3.1 and 5 new in `ael/_tests/test_review.py`).
- The detail-transfer regression of the sixteen filters (`test_filters_keep_injected_fine_detail_with_its_sign_and_strength`)
  still passes against the 1.3.0 values: the NRGF change leaves the transfer of faint detail as it was
  (0.644 and 0.621 against 0.64 and 0.62).

## Concentric ripple with faint structure

Scene: I = r⁻³·(1 + 0.02·cos 5θ), off-centre Sun, data from 1.05 to 2.6 R☉. Metric: the standard deviation of the
azimuthal mean in 0.25-px radial steps between 1.05 and 1.6 R☉, after removing anything slower than ~6 px. The floor
is the same layer computed on the exactly flattened input I·r³ (the sampling noise of the pixel grid).

| Sun radius | Layer | Floor | 1.3.2 | 1.2.0 (hard bins) |
|---|---|---|---|---|
| 120 px | RHEF, whole ring | 0.0198 | 0.0163 (0.82×) | 0.1735 (8.8×) |
| 120 px | RHEF, 30° sectors | 0.0161 | 0.0072 (0.45×) | 0.2399 (14.9×) |
| 120 px | NRGF | 0.0083 | 0.0085 (1.01×) | 0.0967 (11.6×) |
| 200 px | RHEF, whole ring | 0.0157 | 0.0138 (0.88×) | 0.1217 (7.8×) |
| 200 px | RHEF, 30° sectors | 0.0131 | 0.0074 (0.56×) | 0.1919 (14.6×) |
| 200 px | NRGF | 0.0065 | 0.0065 (1.00×) | 0.0652 (10.0×) |

The 1.3.1 NRGF gave 2.5× (120 px) and 1.9× (200 px): its ring profiles were smoothed with a plain Gaussian, which
biases a steep, curved profile. The 1.3.1 radial rank was already at the floor and is unchanged.

## Mutations

Each new test was checked against a deliberate fault that it must detect:

| Mutation | Test | Result |
|---|---|---|
| Plain Gaussian smoothing of the NRGF profile (the 1.3.1 behaviour) | faint structure on a steep profile | detected |
| Upsilon with the low exponent on both sides | the Upsilon curve | detected |
| `make_filter` ignoring `upsilon_curve` | local RHEF with Upsilon | detected |
| A fixed seam at 24 cycles per turn added to every ring layer | structureless corona | detected |
| Fixed rings of 7 px added to every ring layer | structureless corona | detected |

Logs and scripts are kept with the author (`3-AEL/proves/validacio_1.3.2/`).
