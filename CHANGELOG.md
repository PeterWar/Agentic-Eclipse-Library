# Changelog

## 1.2.1 — 2026-10-06 (local, unpublished)

- Fix radial lookup discontinuities in both NRGF variants and four RHEF variants.
  NRGF evaluates measured annular statistics continuously; RHEF interpolates
  log-intensity quantile functions before inversion. No spatial image blur.
- Replace hard-clipped asinh display with a shared soft highlight shoulder and
  independently scale the hidden 16-bit linear reference. Effective parameters
  and clipping/negative-channel counts are recorded; signed float HDR stays authoritative.
- Add explicit `stack.canvas: "reference"` alongside the existing union default,
  preserving the agreed native rectangle without per-project monkey-patching.
- Add installed regression tests: frozen 1.2.0 ring-producing negative operators,
  seeded angular detail, missing/constant/tied data, bright PSB pixels and receipts,
  native flat-before-warp calibration with a wrong-stage control, and canvas choice.
- Implement the planned goal-first guidance in both `AGENTS.md` and the first-steps
  skill. Review three sample first replies (missing, explicit and unsure goal);
  this is a manual instruction review, not an independent model benchmark.
- Document astromodified colour assumptions, exposure-name disagreements, separate
  lunar/earthshine sources, native Photoshop checks and the limited dust pilot.
  The experimental dust fitter is not promoted to an automatic cleanup command.

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
