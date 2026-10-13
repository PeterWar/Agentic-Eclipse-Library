# Validation of version 1.3.0 — 2026-10-13

## Software

- Built-in tests: 67/67 passed with no skips, in the source tree and from the built wheel imported
  outside the repository (Python 3.12, numpy 2.5, scipy 1.18, astropy 8.0). The wheel's 29 Python files
  are byte-identical to the source.
- New in 1.3.0: 20 tests for `ael.coronagraph` and the 12 tests for `ael.extinction`; the 35 earlier
  tests (27 from 1.2.0 and those prepared as 1.2.1) are unchanged and pass.
- The coronagraph tests use synthetic coronae and published constants only. They include negative
  controls: the perpendicular-axes trap on an affine plate, another corona that must not agree, the same
  streamers with other rays (whole profiles agree, fine detail much less), a radial tone curve that the
  structure test cannot see, a pylon run across 0°, a seed that is not dark, cells that must be dropped,
  and a command that must refuse an existing directory, unknown keys, a geometry for another canvas, a
  missing mask, clashing names and a frame without a P angle.
- Two independent reviews before release, one of the code and physics, one of everything published. The
  code review found a call that needed NumPy 2 (the package declares NumPy ≥ 1.24), a line-of-sight
  integral cut at 20 R☉, an unchecked LASCO summing and polariser case, and gaps in the command's checks;
  all were corrected and tested. Of 27 deliberate mutations of the module (signs, constants, the median,
  the pylon, the command's options), every one makes at least one test fail. The tests ran on NumPy 2.5
  only; NumPy 1.x was not installed to check.

## Real data (12 August 2026)

The module was run, as another user would run it, on the research's calibrated map of the 2026 corona (a
FITS file binned 2×2, with a helioprojective header and a flag plane; it is not distributed), on seven K-Cor
level-2 pB frames inside totality, and on the two LASCO C2 level-0.5 images before and after totality. The
research results it should reproduce (notes 180 and 185) were made with independent code on the
full-resolution map.

| Check | Research | `ael.coronagraph` |
|---|---|---|
| Plate axes, from the map's own FITS header | 90.43° | 90.430° |
| K-Cor, ratio of medians, 1.15–1.25 / 1.25–1.40 / 1.40–1.70 R☉ | 1.0584 / 1.0635 / 1.1199 | 1.0645 / 1.0649 / 1.1191 |
| K-Cor, median of ratios | 1.0952 / 1.1023 / 1.1914 | 1.0941 / 1.1108 / 1.1912 |
| C2, Colaninno & Howard, six rings 2.4–5.5 R☉ | 1.1400 / 1.2726 / 1.3210 / 1.3527 / 1.3688 / 1.4001 | 1.1381 / 1.2737 / 1.3213 / 1.3534 / 1.3686 / 1.3990 |
| C2, SolarSoft | 1.3185 / 1.4719 / 1.5278 / 1.5645 / 1.5831 / 1.6194 | 1.3163 / 1.4732 / 1.5282 / 1.5653 / 1.5830 / 1.6181 |
| K-Cor without the F corona (the first comparison's mistake) | excess of 13–15 % | 1.187 / 1.210 / 1.432 |

The largest differences are 0.0022 for C2 and 0.0085 for K-Cor.

The structure test was run on the linear map rather than on the display image used in the research,
and on K-Cor pB rather than its NRGF GIF, so similar values were expected, not equal ones. Against
K-Cor: 0.96 / 0.98 / 0.97 / 0.83 at 1.15–1.98 R☉ (fine detail 0.97–0.98; nulls of 0.25–0.58). Against C2:
0.97 / 0.97 / 0.94 / 0.88 / 0.78 at 2.4–6 R☉ (fine detail 0.97 / 0.94 / 0.96 / 0.86 / 0.69 against nulls
of 0.29–0.58). At 4–5 and 5–6 R☉ the whole-profile null reaches 0.89 and 0.93, above the observed 0.88 and
0.78: there only the fine detail discriminates, as the skill says. At 5–6 R☉ the best whole-profile rotation
is +10°, the edge of the search, and the command flags it (`at_search_edge`). The pylon mask took 74.5° around
PA 288–360° and 0–2° (it crosses north), as in the research (72°).

The receipt with every number, the frames and the SHA-256 of every input stays with the author, because the
map and the downloaded data are not distributed.

## What this does not show

These checks separate software regression, agreement with the research pipeline and the limits of the
method. They do not make the 2026 calibration more certain than its own uncertainty (−20 %/+11 % at
1.15–1.9 R☉), do not resolve the cause of the C2 level difference, and do not certify any image. The
structure test compares position angles only.
