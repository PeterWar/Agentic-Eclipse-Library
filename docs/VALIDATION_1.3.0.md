# Validation of version 1.3.0 — 2026-10-13

## Software

- Built-in tests: 61/61 passed with no skips, in the source tree and from the built wheel imported
  outside the repository (Python 3.12, numpy 2.5, scipy 1.18, astropy 8.0). The wheel's 29 Python files
  are byte-identical to the source.
- New in 1.3.0: 14 tests for `ael.coronagraph` and the 12 tests for `ael.extinction`; the 35 earlier
  tests (27 from 1.2.0 and those prepared as 1.2.1) are unchanged and pass.
- The coronagraph tests use synthetic coronae and published constants only. They include negative
  controls: the perpendicular-axes trap on an affine plate, another corona that must not agree, the same
  streamers with other rays (whole profiles agree, fine detail much less), a radial tone curve that the
  structure test cannot see, a pylon run across 0°, a seed that is not dark, cells that must be dropped,
  and a command that must refuse an existing directory, an unknown key and a frame without a P angle.

## Real data (12 August 2026)

The module was run, as another user would run it, on the published calibrated map of the 2026 corona
(a FITS file with a helioprojective header and a flag plane), on seven K-Cor level-2 pB frames inside
totality, and on the two LASCO C2 level-0.5 images before and after totality. The research results it
should reproduce (notes 180 and 185) were made with independent code on the full-resolution map; here
the map is binned 2×2.

| Check | Research | `ael.coronagraph` |
|---|---|---|
| Plate axes, from the map's own FITS header | 90.43° | 90.430° |
| K-Cor, ratio of medians, 1.15–1.25 / 1.25–1.40 / 1.40–1.70 R☉ | 1.06 / 1.06 / 1.12 | 1.065 / 1.065 / 1.119 |
| K-Cor, median of ratios | 1.10 / 1.10 / 1.19 | 1.094 / 1.111 / 1.191 |
| C2, Colaninno & Howard, six rings 2.4–5.5 R☉ | 1.14 / 1.27 / 1.32 / 1.35 / 1.37 / 1.40 | 1.138 / 1.274 / 1.321 / 1.353 / 1.369 / 1.399 |
| C2, SolarSoft | 1.32 / 1.47 / 1.53 / 1.57 / 1.58 / 1.62 | 1.316 / 1.473 / 1.528 / 1.565 / 1.583 / 1.618 |
| K-Cor without the F corona (the first comparison's mistake) | "+13–15 %" | 1.187 / 1.210 / 1.432 |

The structure test was run on the linear map rather than on the display image used in the research,
and on K-Cor pB rather than its NRGF GIF, so similar values were expected, not equal ones. Against
K-Cor: 0.97 / 0.98 / 0.97 / 0.84 at 1.15–1.98 R☉ (fine detail 0.97–0.98; nulls below 0.6). Against C2:
0.97 / 0.97 / 0.94 / 0.88 / 0.78 at 2.4–6 R☉ (fine detail 0.98 / 0.94 / 0.96 / 0.86 / 0.70 against nulls
of 0.29–0.58). At 5–6 R☉ the whole-profile null reaches 0.93, above the observed 0.78: there only the
fine detail discriminates, as the skill says. The pylon mask took 74.5° around PA 288–360°, as in the
research (72°).

The receipt with every number, the frames and the SHA-256 of every input stays with the author
(`3-AEL/proves/validacio_1.3.0/` in the project), because the map and the downloaded data are not
distributed.

## What this does not show

These checks separate software regression, agreement with the research pipeline and the limits of the
method. They do not make the 2026 calibration more certain than its own uncertainty (−20 %/+11 % at
1.15–1.9 R☉), do not resolve the cause of the C2 level difference, and do not certify any image. The
structure test compares position angles only.
