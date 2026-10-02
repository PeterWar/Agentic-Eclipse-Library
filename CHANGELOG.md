# Changelog

## 1.2.0 — 2026-10-03

- `ael stack`: one-pass CFA interpolation, explicit calibration and affine registration,
  full union canvas, geometric coverage, shared saturation taper and optional two-band
  weighting with frozen cloud corrections. Persistent hot-pixel detection uses local noise.
- `ael filters`: the three first-step filters by default, sixteen portable variants on
  request, observed-domain masks, explicit display parameters, optional verified 16-bit PSB.
- Isotropic ACHF subtracts a smooth radial log-luminance spline before high-pass;
  Multiply layers retain the base's limb alpha. No saturated-pixel reconstruction.
- Selftests ship inside the wheel and work outside the source tree.
- Includes the previously local motion GIF changes: common recipe/grain and unchanged
  grain-uniformity and concentric-band gates. A known mixed-instrument run measured
  1.105 against a 1.10 grain threshold and remains a failed gate.

See `docs/DEVELOP.md` for parameter conventions, differences from historical filter
recipes and limits. Registration, physical calibration and spatial cloud-map fitting
remain explicit upstream tasks. File integrity is distinct from native application
and scientific validation.
