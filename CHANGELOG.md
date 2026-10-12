# Changelog

## Unreleased (local branch, not published)

- Add `ael.extinction` and `ael extinction --config ... --out ...`: differential atmospheric
  extinction across the field under a low Sun. Per-pixel air mass from the site and time
  (astropy: the Sun's apparent altitude with refraction and the zenith's position angle,
  projected with the image's north/east vectors or a plate solution), or directly from the
  Sun's apparent altitude, the zenith direction and the plate scale. Air mass of Kasten &
  Young (1989), on apparent altitude; `NaN` below the horizon.
- The correction works in linear light after subtracting the sky:
  `(I − sky)·10^(0.4·k·(X − X_ref))`, with `X_ref` the air mass at the Sun or at the
  photometric zero point. Achromatic by default (colour ratios unchanged); one `k` per channel
  is optional and changes colour. `k` is an input; `dimming_k` measures it from the dimming of
  the corona between same-exposure frames of totality and refuses pairs too close in air mass.
- Consistency tests instead of a fitted `k`: `ring_dipole`, `k_nulling_dipole` and the gate
  `k_consistency` (one `k` must cancel the zenith dipole against a reference without
  atmosphere in every ring, with no radial trend). Documented lesson: sky and extinction are
  degenerate; fit the sky where the corona is negligible (e.g. r ≥ 8 R☉).
- Known-truth tests on synthetic coronae: exact recovery with the true sky; recovery within
  0.5 % with a sky plane fitted beyond 8 R☉ when no corona is there; negative tests where a
  sky plane fitted on uncorrected data absorbs the extinction dipole of the corona tail, a
  constant sky estimated at 3–4 R☉ contains corona, and a constant sky misses a sky gradient
  (all three detected by the same gate); air-mass sanity checks (zenith, horizon,
  plane-parallel limit, symmetry about the vertical, three equivalent orientations, the
  astropy and plate-solution routes).
- Fix `render.sky_background` on noise-free data: the robust scale was zero and a strict
  comparison clipped every pixel, returning a zero sky without warning.

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
