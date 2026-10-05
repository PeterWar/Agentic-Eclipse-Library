# Validation of local version 1.2.1 — 2026-10-06

- Baseline 1.2.0: 27/27 built-in tests passed.
- Updated source: 35/35 tests passed, with no skips. The built-in runner executes
  the test functions directly; the optional pytest package was unavailable.
- Built wheel imported outside the repository: 35/35 passed, with no skips.
  Its Python source files were compared byte for byte with the working source.
- All sixteen filters from that wheel produced a synthetic 400×300, RGB16,
  19-layer PSB. Photoshop opened it and exported a native TIFF as a copy; the
  full canvas was inspected. Native rendering differed from the emulated merged
  image by at most 5 DN16, with zero fully clipped positive pixels. The script
  closed its own document and restored the previous document when present.
- The six corrected radial operators were also evaluated on a private frozen
  field input. Period-two amplitude was 0.0062–0.0097 times the old defective
  operators' value, without losing the previously finite output support.
  That private input is not distributed; the public synthetic tests reproduce
  the failure and verify detail retention without it.
- Missing, explicit and uncertain user goals were reviewed as written examples
  in `ONBOARDING_CHECKS.md`. No independent model evaluation was run.

These checks distinguish software regression, native-file compatibility and the
limits of field evidence. They do not certify a scientific image, complete dust
removal, calibrated spectral colour or recovered lunar relief. The internal dust
response fitter remains an experimental, documented lesson outside the production API.

This records a local version. A commit and wheel are not a published GitHub release.
