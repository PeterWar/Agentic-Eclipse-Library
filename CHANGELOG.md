# Changelog

## Unreleased

- **A contribution by Raúl Hussein**, with RAW frames from Oscar Maseda and Carlos Oltra (pull requests
  [#5](https://github.com/PeterWar/Agentic-Eclipse-Library/pull/5),
  [#6](https://github.com/PeterWar/Agentic-Eclipse-Library/pull/6) and
  [#7](https://github.com/PeterWar/Agentic-Eclipse-Library/pull/7), merged as one):
  - **`skills/eclipse-astrophotography/`**, a seventh skill, also in both plugins: a whole eclipse case from the
    chosen frames to an editable master the photographer accepts. It brings rules already in AEL into one route
    and adds a stage table, five geometry and support roles and a case closeout.
  - **`docs/ASTRO_THREE_CAMERA_CASE_STUDY.md`**: Sony, Nikon and Canon cases of the same eclipse. The data are
    private; the study says what cannot be reproduced from this repository.
  - **`docs/FIELD_LESSONS.md`: the NRGF description follows 1.3.2.** The profile is a local cubic Hermite curve
    through slope- and curvature-corrected nodes; only the spread uses PCHIP, on its logarithm. The old sentence,
    written for 1.2.1, was still in the 1.3.2 release and in Codex plugin 1.0.1.
- **On top of that contribution:** the skill and the case study say that different optical trains are never fused
  without a calibrated distortion model for each, even for a presentation; colour propagated for display is a declared
  reconstruction in its own layer; the skill's links point to the copies in the package; the credit moves to the
  README's Contributors section; the plugins, their receipt and the workflow counts are brought up to date.
- **README: "What this plugin runs, fetches and sends".** The packages that `pip` installs, the public coronagraph
  data that one skill downloads after the user approves it, the Skyfield ephemeris, and two research scripts that
  reach the network: a star-catalogue download and the OpenRouter client the project used to consult other models.
- **`postprocessat-corona`:** the line about the author's private tool for consulting Codex is removed from the skill
  and from its two older copies in `references/`, with an "Editat per a la publicació" mark.

## 1.3.2 — 2026-10-16

In October 2026 Chris Gilly (NorthWest Research Associates), first author of the RHEF paper (Gilly & Cranmer
2025), reviewed the draft of the author's paper *A Faithful Corona* and this library. This version answers his
review. His synthetic test, a corona falling as r⁻³ with faint structure, repeated on 1.3.1, showed that its NRGF
still left rings. The sixteen filters of `ael filters` keep their names; the NRGF output changes where the radial
profile is steep.

- **Reduced NRGF profile bias in the tested scenes.** In 1.3.1 the ring profiles were smoothed with a plain Gaussian
  (`smooth_bins=3` in the filter bank). On a steep, curved profile that biases the mean (about 1 % of the brightness,
  half a ring sigma with 2 % structure, 0.2 R☉ above the limb of a 120-pixel Sun) and leaves broad false rings. Now:
  - each 2-px annulus gives a node at the mean radius of its own pixels, with the profile's slope and curvature
    removed inside it; both come from the neighbouring median nodes (a quartic, and a cubic next to the ends of a run);
  - a local cubic Hermite curve through the nodes gives the profile at every pixel's radius; the spread is measured
    about it and interpolated without overshoot;
  - each run is modelled on the values and on their logarithm (or on asinh when a subtracted sky takes it through
    zero), and keeps the model that fits it better;
  - the filter bank no longer smooths the nodes, and `make_filter('nrgf')` keeps pixels at or below zero;
  - no output in runs of fewer than four annuli, in annuli where half the pixels share one value (zeros, clipping,
    coarse integers), or where the residuals, once a smooth function of radius is removed, have no part above one
    float32 step (structure with mirror symmetry about a centre on the pixel grid is kept). That smooth function is
    fitted twice, to the residuals and to the values, in radial bands that each hold four different radii or more;
  - the new NRGF works on exact (float64) radii: a float32 radius, times the slope of a steep radial ripple, passed
    for angular signal.

  With 2 % angular structure on an r⁻³ profile, the concentric ripple stays at the sampling floor of the flattened
  input (1.00×; 1.3.1: 1.9–2.5×; 1.2.0: 10–12×). Next to a gap in the data, the median of the 1.3.1 NRGF was −2.8 and
  +2.1 sigma on the two sides; it is now 0.000. On a clean structureless corona every annulus averages within 0.06
  sigma (Sun of 60 to 200 px, noise 10⁻² to 10⁻⁴, median statistic). Faint structure (10⁻⁴) on r⁻³ or on an exponential
  falling six decades is recovered (correlation 1.00). With the robust statistic (the default), one bad pixel 10 to 10⁷
  times too bright changes the layer outside its own annulus by less than 0.004 sigma; with the mean statistic it
  moves the next annulus and, less, the one after, as in 1.3.1. Constants, straight profiles and smooth noiseless
  radial profiles give no output in the tested scenes; a noiseless radial feature a few pixels long can still give
  output around a small Sun, and on a very clean stack radial structure a few annuli wide stays in the layer as
  rings (limits in `docs/VALIDATION_1.3.2.md`).
  The new operator takes about five times as long. With the same arguments, `spread_about='bin'` in
  `ael.filters.nrgf` gives the 1.3.1 output bit for bit; `make_filter` has no such option and no longer smooths
  the nodes. Details and limits: `docs/VALIDATION_1.3.2.md`.
- **Upsilon with an exponent for each side**: `ael.filterbank.upsilon(q, low, high)` (eq. 2 of Gilly & Cranmer
  2025; exponents must be positive, missing values stay missing), and `make_filter(..., upsilon_curve=(low, high))`
  for any RHEF layer, including the local ones (refused for other filters).
- **`docs/PAPER_AND_LIBRARY.md`**: what the published layers of the paper did and what the library does, filter by
  filter (input channel, rings, statistics, limits, blend), the algebra of blending a layer centred on mid grey,
  and the sky and extinction that ring filters turn into structure.
- **New controls** (`ael/_tests/test_review.py`): faint structure on a steep profile against the sampling floor,
  with the 1.2.0 operators and the 1.3.1 NRGF as negative controls; the blend algebra; the Upsilon curve; a
  structureless corona through the ring filters (no rings, no seams at the sector nodes; positive controls); the
  local RHEF with Upsilon; the NRGF on constants, next to a gap and with an outlier; faint annuli beside bright
  ones; the explicit Upsilon option and its refusal for other filters; a clean corona, a profile with a dip, a
  sky-subtracted corona, faint structure over six decades, straight, curved, stepped and purely radial profiles,
  subnormal values and strong streamers; the filter bank without node smoothing on a 15-px Sun; bad pixels, data
  edges inside an annulus and runs of one to five annuli; ties (zeros, clipping, 8-bit data); a sky subtracted too
  deep; the unit of q and the `min_count` boundary; symmetric structure about a centre on the pixel grid; an input
  negative everywhere; a bright pixel with the mean statistic; noiseless radial profiles around small Suns. 84 of 84
  tests; 43 of 43 mutations detected. The NRGF went through twelve rounds of review by another AI coding agent
  (Codex) and two adversarial checks by AI agents (independent readers and a verifier); their scripts are rerun
  on the final code (`docs/VALIDATION_1.3.2.md`).
- The test of the solar route uses the IERS tables bundled with Astropy, so the self-test also passes offline.
  Offline use of `ael.extinction` with a site and a time needs the same two settings:
  `iers.conf.auto_download = False` and `iers.conf.auto_max_age = None` (`docs/VALIDATION_1.3.2.md`).
- The radial rank (RHEF), with continuous statistics since 1.3.0, already reaches the sampling floor on the same
  scene (0.45–0.88×); unchanged.

## 1.3.1 — 2026-10-13

Documentation and new controls from the field report of NLFotografia
([issue #1](https://github.com/PeterWar/Agentic-Eclipse-Library/issues/1)). No filter, stacking or
coronagraph code changes its output.

- `docs/FIELD_LESSONS.md`: the case (an FRA400 and a camera at several focal lengths and framings, without
  darks or flats), kept apart in three lists: what the case reported, what was checked in the package, and
  what was reproduced in the package and is not fixed yet. The skills for first steps, post-processing and
  artefact repair point to it, and the README credits it.
- New tests for the sixteen filters of `ael filters`, on one synthetic scene (a ring-free corona with angular
  structure, the Moon on the Sun's centre, a straight coverage edge): two-pixel grooves and a 2–16 px ring
  metric over whole rings at the limb, in the middle and in an outer zone clear of the edges, and in 45° sectors
  of the middle and outer zones, with positive controls (the old stepped NRGF at 2 and 10 px, rings of 8–10 px
  added to a layer); support band by band from the limb and from the edge; and, with 0.3 % noise, a faint
  injected pattern returned with its sign and within ±25 % of its 1.3.0 strength. WOW bilateral is left out of
  the sector and detail checks, for the reasons in its issue.
- Two limitations found while checking the report, reported and not fixed: ACHF and WOW make bands along the
  edges of the data (the lunar limb when the Moon is off the Sun's centre, and straight frame or coverage
  edges), mainly from the Sun-centred radial profile (issue #3); and WOW bilateral can return faint
  fine detail with the opposite sign and draws isophote lines on a smooth, noise-free corona (issue #4).
- `ael stack` is documented as writing no propagated variance and as registering with affine transforms
  (correct each optic's distortion first).

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
- Known-truth tests (20): the affine trap (3.3 px at the limb, ~20 px at 6 R☉), SOHO's larger Sun,
  the P angle (frames and command), an affine celestial plate, helioprojective headers (`RSUN_OBS` or
  `DSUN_OBS`), agreement and a recovered 5° rotation, a negative control (another corona) and the same
  broad shape with other rays, blindness to a radial tone curve, the pylon (across 0°, longer than 180°,
  inside the command), the polarisation against a quadrature to infinity, the published van de Hulst
  constants, K + F, the band transfer, the C2 calibrations in 2026 and 2013 with summing and polariser,
  medians and dropped cells, the ratio band, binning, masks and every refusal of the command. All 27
  deliberate mutations of the module tried before release make at least one test fail.
- After an independent review: the line-of-sight integral uses SciPy (the package still runs on
  NumPy 1.24) and goes to 2000 R☉ (stopping at 20 R☉ had raised p by 6 % at 8 R☉); the P angle is
  required; overlapping rings, unknown keys at any level, a geometry for another canvas and duplicate
  reference names are refused; the receipt hashes the recipe, geometries and masks and has gates;
  missing values are written as `null`.
- Checked on the 2026 data (`docs/VALIDATION_1.3.0.md`), from the research's calibrated map (a FITS file
  binned 2×2, not distributed): it reproduces the research ratios within 0.003 for LASCO C2 and 0.009 for
  K-Cor, and reads the plate's 90.43° from the map's own FITS header.

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
  181–184 start from or build on other photographers' images and presentations and are not published.
  Names of private correspondents, the words of a private message and a private link were removed from
  three passages of note 180, one of note 185 and a few lines of their code; each edit in a note is marked.
- Six skills: `coronagraph-comparison` is new; the first-steps skill points to it.
- `docs/EXISTING_EDIT_CASE_STUDY.md`: a case study on adding adjustable filters to an existing edit, contributed
  by NLFotografia ([pull request #2](https://github.com/PeterWar/Agentic-Eclipse-Library/pull/2)).

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
