# Validation of 1.3.6 (29 October 2026)

This release corrects two problems that Francisco Bitto found while reviewing the AEL code for his Eclipse Image
Processor ([pull request #8](https://github.com/PeterWar/Agentic-Eclipse-Library/pull/8)). Values that were already
right do not change.

## What changed

1. **`ael.render.soft_log`.** The sum `S/2 + sqrt(S²/4 + ε²)` cancels in float32 for strongly negative S, and the
   logarithm returned −∞: for S = −10⁴ and ε = 1, the exact value is −9.2103. Negative values now go through
   `log(ε² / (sqrt(S²/4 + ε²) − S/2))`, the same function without the cancellation. Values at or above zero are
   computed with the expression of 1.3.5, bit for bit. Below the noise the curve falls slowly, as `log(ε²/|S|)`; the
   docstring said it stayed flat at `log ε`, and now describes it.
2. **`ael.filters.mgn`.** An absolute floor of 1e-12 on the local spread (and another on the range of the global
   image) made the result depend on the units of the input. On a synthetic corona multiplied by 1e-8 the layer
   changed by up to 0.40. The floors are gone: a spread of zero still gives no value, as before.

## Checks

| | 1.3.5 | 1.3.6 |
|---|---|---|
| `soft_log(−10⁴, ε = 1)` | −∞ | −9.2103 (exact −9.2103) |
| `soft_log`, S from −10⁶ to 10⁶, ε = 1, 3 and 0.001: largest error against `log ε + asinh(S/2ε)` | −∞ for S ≤ −10⁴ | ≤ 2·10⁻⁶ relative |
| `soft_log`, S ≥ 0 | | bit-identical to 1.3.5 |
| MGN, input × 1e-8: largest change of `mgn` (h = 0.7) | 0.40 | < 10⁻⁴ |
| MGN, input × 1e-4 and × 1e4 | < 10⁻⁴ | < 10⁻⁴ |
| MGN in ordinary units | | bit-identical to 1.3.5 |

- `python -m ael selftest`: **110 of 110**, in the source tree and from the installed wheel, with and without network.
  Two tests are new, `test_soft_log_has_no_cancellation_below_the_noise` and
  `test_mgn_does_not_depend_on_the_units_of_the_input`. Both fail on 1.3.5, and both keep the formulas of 1.3.5 as
  negative controls.
- The tests check the software; a new astronomical observation needs its own validation.

## Not in this release

The angular ACHF still leaves the first and last rows of the canvas without a value. The loss comes from the polar
resampling (`ael.polar`), which other products share; it belongs with the boundary bands of
[issue #3](https://github.com/PeterWar/Agentic-Eclipse-Library/issues/3).
