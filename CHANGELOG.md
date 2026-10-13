# Changelog

## 1.3.0 — 2026-10-13

Coronagraph checks and differential extinction, plus the fixes prepared as 1.2.1 (never released
on their own). Research notes 180 and 185 and the code behind them are added to `3-RECERCA/`.

### Coronagraph comparison (`ael.coronagraph`, `ael coronagraph`, skill `coronagraph-comparison`)

- `SolarFrame`: solar coordinates of each image as seen by its own observer, with axes that may be
  non-perpendicular (an affine star plate) and an exact 2×2 inverse; built from an `ael` geometry and
  the P angle, an affine plate solution, a helioprojective FITS header (K-Cor level 2, AIA level 1.5)
  or three pixel positions (LASCO level 0.5 through sunpy). `rsun_arcsec` gives each observer's Sun.
- Structure: `unroll` (optional supersampling; nothing interpolated across missing data), `nrgf_rows`,
  `angular_profile`, `angular_highpass`, `circular_correlation`, `rotation_null`, `compare_structure`
  (zero and best rotation, a null from 30–330° rotations, fine detail below 12°), `dark_sector` for an
  occulter pylon (only the dark run that contains the seed angle) and `subtract_low_harmonics` for
  displaying LASCO level 0.5.
- Brightness in mean solar brightness: `thomson_polarization` (van de Hulst coefficients integrated
  along the line of sight; Baumbach–Allen, Saito or any density), `kcor_total_msb` (K-Cor pB/p plus
  the F corona), `k_band_transfer`, van de Hulst (1950) K and F coronae, `lasco_c2_msb_per_dn` with the
  Colaninno & Howard (2015) and SolarSoft calibrations, `cell_medians` (each image in its own frame,
  no resampling; `drop_touching` drops a cell that touches the lunar-motion band), `level_ratios` and
  `ratio_band` (the asymmetric 1σ band of a ratio).
- `python -m ael coronagraph --config ... --out ...`: declared structure comparison with a JSON
  receipt and one check sheet per reference; every input is read and checked before anything is
  written. Template: `examples/coronagraph_config_template.json`.
- Known-truth tests (14): the affine trap (3.3 px at the limb, ~20 px at 6 R☉), SOHO's larger Sun,
  the P angle, a helioprojective header, agreement and a recovered 5° rotation, a negative control
  (another corona) and the same broad shape with other rays, blindness to a radial tone curve, the
  pylon including a run across 0°, the polarisation regression and limits, K + F, the two C2
  calibrations in 2026 and 2013, a known brightness scale with dropped cells, the ratio band and the
  command with its refusals.
- Validated on the 2026 data from the published calibrated map (`docs/VALIDATION_1.3.0.md`): LASCO C2
  ratios within 0.005 and K-Cor within 0.01 of the research results; the plate's 90.43° read from the
  map's own FITS header.

### Differential extinction (`ael.extinction`, `ael extinction`)

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
- The sky may be one value, one value per channel, or an (H, W) or (H, W, C) map, on images
  of any height (the correction runs by blocks of rows; a constant sky is never sliced). The
  command checks every input and computes every output before it creates the output
  directory, and refuses an existing one. Regression tests cover each sky form with several
  block sizes and the refusals.
- Fix `render.sky_background` on noise-free data: the robust scale was zero and a strict
  comparison clipped every pixel, returning a zero sky without warning.

### Documentation and research

- `docs/FIELD_LESSONS.md`: coronagraphs (structure is not brightness; pB is not what a camera sees;
  two C2 calibrations; asymmetric bands; each observer's Sun), a rotational-gradient
  (Larson–Sekanina) layer that copies rays, and adding layers to someone's file without rewriting
  theirs (psd-tools re-serialised an adjustment-layer record). `ael.photoshop` says it only writes
  new files.
- Research notes 180 (structure against SDO/AIA, LASCO and K-Cor) and 185 (corrections to the
  absolute calibration and differential extinction), and five research folders in `3-RECERCA/tools/`:
  `comparacio_sdo_lasco_20261001`, `msb_calibrat_20261011`, `extincio_diferencial_20261012`,
  `larson_sekanina_20261002` and `v128_extincio_20261012` (the byte-preserving PSB writer). Notes
  181–184 started from other photographers' images and are not published; the names of private
  correspondents were removed from notes 180 and 185 and from a few lines of their code.
- Six skills: `coronagraph-comparison` is new; the first-steps skill points to it.

### Fixes and lessons prepared as 1.2.1 (2026-10-06)

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
