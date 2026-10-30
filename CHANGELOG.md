# Changelog

## 1.4.0 — 2026-10-30

Two experimental connectors run `ael` from inside PixInsight and Photoshop, and `ael` measures the geometry of an
eclipse image on the image itself, so that nobody has to write a geometry file to start. The Codex plugin goes to 1.1.4; the Claude Code plugin of this repository's marketplace and the
Claude plugin folder `plugins/claude-ael/` go to 1.4.0.

- **Geometry measured on the image** (`ael.geometry.find_disc` and `measure_geometry`, `python -m ael geometry`, and
  `--geometry auto` for `structure` and `polar`). It finds the lunar disc with no input, after the lunar detection of
  Francisco Bitto's *Eclipse Image Processor*: a closed, nearly round region without data (NaN, an alpha channel or
  exactly zero), or else the darkest disc inside a bright ring among the circles of a Hough search, refined on the full
  image with `fit_limb`. There is never a default circle: an image without a lunar disc is refused. The Sun is placed
  at the centre of the measured circle with its radius, and north, parity and plate scale stay unknown unless they
  are given; the geometry's note says what was measured and what was assumed. On real stacks of 2024 and 2026 the
  circle lands within 0.4–1.2 px of the measured Moon (or 4 px of the Sun, where only the region the Moon covered all
  along was left without data); on single RAW frames of both eclipses it holds from 1/8000 s to 2 s, unless the lunar
  disc itself is saturated; on 660 synthetic eclipses (lunar radius 25–420 px, Moon 1.00–1.08 times the Sun, off by
  up to the difference of the radii, partly outside the frame, saturated, colour or mono) it is within max(1 px, 1 %
  of the radius) in 631, and every failure is a Moon of 25 px.
- **`plugins/pixinsight-ael/`, for PixInsight 1.9.** One menu entry, **Utilities > Agentic Eclipse Library**, with
  one dialog: it runs `structure` and `polar` on the active image, makes AEL's filter layers from the active image, or
  a linear master from frames, and opens every product in a new window. The filter layers come with the
  PixelMath expressions that compose them, starting from the same floating-point values AEL starts from (0.504 of a
  16-bit step from AEL's composite, against a gate of one step). When PixInsight does not hold an image as its file
  stores it (it rescales a floating-point TIFF with values outside 0–1, writes NaN as 1.0 and reads a TIFF whose last
  sample is NaN as black), the bridge has AEL read the file itself, so its AEL products stay those of
  `python -m ael`.
- **`plugins/photoshop-ael/`, for Photoshop 2026.** The same operations. The filter layers arrive as one layered
  16-bit PSB written and verified by `ael.photoshop`; Photoshop reads it again and compares every layer's name, mode,
  opacity byte and visibility with what AEL wrote, and a difference stops the run. Photoshop's own composite of that
  file stays within 5 of 65,535 of AEL's (99.9th percentile 4), the effect of its 15-bit arithmetic.
- **Packages.** Each connector's `tools/build_package.py` writes a folder with the AEL engine inside (`runtime/ael`,
  checked byte by byte), synthetic demonstration files and a deterministic ZIP. Neither connector names an
  interpreter: each finds a Python that can import the AEL it carries and its dependencies, and both refuse an AEL
  older than 1.4.0.
- **No geometry or camera file needed.** The PixInsight dialog asks only for the operation, the image (or the
  files) and the output folder, which starts at Downloads and has a **Browse…** button: no Python, AEL folder,
  geometry or camera profile. Its file lists take several files at once: RAW (CR2, CR3, NEF, ARW, DNG and others),
  TIFF or FITS. AEL measures the geometry on the
  image and a new window draws the circle it found; each RAW file gives its levels (the black measured on the sensor's covered
  border, which LibRaw misreports for the Canon EOS R6 Mark III, and 85 % of the range counted as linear), and a
  calibrated TIFF or FITS frame is measured (black 0; saturation where many samples share the highest value). The
  shared helper takes the same "auto" for the Photoshop connector, whose dialog still asks for a geometry file. The linear master takes a frame whose
  lunar limb can be measured as its reference when the first one cannot (a long exposure can saturate the lunar disc).
  A FITS frame gives its exposure and gain from its header. The lunar drift allowed between frames is 0.16 lunar
  radii, which holds for every total eclipse (the Moon crosses at most twice the difference of the radii, and it never
  looks more than about 8 % larger than the Sun); it was 0.1 radii, which a long totality such as 2027's exceeds.
  When the frames record when they were taken, the bound is how far the Moon can cross the Sun in that time (0.65″ a
  second, for a Moon at least 944″ in radius), so a registration that would make it jump is refused.
- **Darks and flats for the linear master.** Several darks make one master dark for each exposure (each frame takes
  the master of its own exposure and ISO, and a frame whose exposure has no dark stops the run); several flats make one
  master flat (`ael.calibrate.master_flat` for RAW flats). One file is taken as the master itself. The frames are
  registered calibrated, as they are stacked. Where a flat has no value (a dead pixel, a sensor side with an odd
  number of pixels) the stack leaves the pixel without data: `ael.stack` accepts NaN in a flat for that.
- **The linear master registers on the Moon and the corona.** Each frame's Moon, fitted on its limb, places its Sun
  within the distance the Moon can have moved since the reference frame, and the corona, band-passed at scales that
  follow the Moon's size, is correlated within that window (a masked normalised cross-correlation in the Fourier
  domain). With the frames' times, the lunar velocity from the frames whose corona holds places every frame's Sun from
  its own Moon, the 1/3200 s frames included. The reference frame is chosen at the middle of the exposure ladder. On
  real frames of three cameras the frames lie within 0.45–0.9 px of the Moon's straight path, and on the Vixen the
  lunar velocity is the ephemeris's within 0.1 %; the Gauss-Newton fit of the logarithm it replaces put the Moon up to
  33 px off on Canon EOS 6D frames of 2024. A frame whose limb fit fails, or whose corona disagrees with its Moon by
  more than 3 px, stops the run with its name, and so do shuffled times.
- **The linear master is experimental.** Its registration has not been compared frame by frame with an independent
  one. Both dialogs say so.
- **`tools/check_connectors.py`** fails when the shared parts of the two connectors drift apart, and runs both probes
  against stand-in AEL packages to check that each refuses an AEL older than 1.4.0.
- Measurements and tests: [`docs/VALIDATION_1.4.0.md`](docs/VALIDATION_1.4.0.md).

## 1.3.6 — 2026-10-29

Two corrections found by Francisco Bitto in his review of the AEL code (pull request #8). Values that were already
right do not change. The Codex plugin goes to 1.1.3; the Claude Code plugin of this repository's marketplace and the
Claude plugin folder `plugins/claude-ael/` go to 1.3.6.

- **`ael.render.soft_log` no longer returns −∞ for strongly negative values.** In float32 the sum
  `S/2 + sqrt(S²/4 + ε²)` cancels: −∞ for S = −10⁴ and ε = 1. Negative values now use the same function written
  without the cancellation, `log(ε² / (sqrt(S²/4 + ε²) − S/2))`; values at or above zero are computed as before, bit
  for bit. The docstring said the curve stays flat at `log ε` below the noise; it falls slowly, as `log(ε²/|S|)`, and
  now says so.
- **`ael.filters.mgn` no longer depends on the units of the input.** An absolute floor of 1e-12 on the local spread
  changed the layer by up to 0.40 when the input was multiplied by 1e-8. The floors are gone; in ordinary units the
  MGN is bit-identical to 1.3.5, and at 1e-8, 1e-4 and 1e4 times the input it agrees within 1e-4.
- **Contributors:** Francisco Bitto and his Eclipse Image Processor, which stays in his own repository. Eduardo Piñas
  and Codex are co-authors of a commit, so that GitHub lists them among the contributors; the README names Claude next
  to Codex.
- Measurements and tests: [`docs/VALIDATION_1.3.6.md`](docs/VALIDATION_1.3.6.md).

## 1.3.5 — 2026-10-28

The author's decision on the WOW layers, and the names of the Photoshop layers. The `ael` operators do not change. The
Codex plugin goes to 1.1.2; the Claude Code plugin of this repository's marketplace and the Claude plugin folder
`plugins/claude-ael/` go to 1.3.5.

- **The edge-aware WOW is the default WOW layer** (`wow_edge_aware`). It is the layer called WOW bilateral in 1.3.4: the
  operator of the author's own WOW layer, with range weights taken from a guide. It takes the name Auchère et al. (2023)
  give to their variant of WOW with a bilateral smoothing. `wow_bilateral` is still accepted as its old name, in recipes
  and from Python. The author chose it after looking at his own 2026 image: there it keeps the lunar limb clean, and he
  sees no rings. The choice is declared against the numbers of 1.3.4: on the author's Sony it fails the worst 45° sector
  of Edu's gate (up to 18–20 % of the clear detail inverted, against a limit of 10 %) and the ring gate, which the plain
  WOW passes. Under the rule fixed before those gates the default would not have changed; it changed by the author's
  decision.
- **The plain WOW (`wow`, the default of 1.3.4) is optional.** A recipe that lists it without the edge-aware WOW keeps it
  visible at 0.37; listed next to it, it is a hidden layer to compare with.
- **Recommendation** (the author's, from his 2026 image; it agrees with Auchère et al. 2023, who found that the
  edge-aware variant gives better results with spikes or edges): where the corona data reach the lunar limb, use the
  edge-aware WOW, because the plain WOW draws concentric rings and a band of weaker texture there. If you prefer the
  plain WOW further out, where it keeps faint fine detail more faithfully, use both layers and blend them with a
  feathered mask: the edge-aware WOW next to the limb, over at least the first 0.5 R☉ (in the author's image the rings
  of the plain WOW reach about 200 px from the edge of the data, 0.45 R☉), the plain WOW beyond, and a feather of
  several tenths of R☉, so that the change of texture leaves no radial frontier. Blend them as two layers with masks
  in Photoshop, never inside one layer. This blend has not been measured yet.
- **Photoshop layer names.** The layers of `corona.psb` take the names of the author's own files: the number is the
  family, in the order of his stack (00 for the display base, then 01 NRGF, 02 RHEF, 03 MGN, 04 ACHF and 05 WOW), a
  letter tells the variants of one family apart from the bottom up, and the name ends with the parameter that
  distinguishes the layer. The defaults give `01 NRGF`, `05 WOW edge-aware` and `04 ACHF iso 1–16 px`. The layers keep
  the order of the recipe. The receipt keeps the code name of every layer (`parameters.layers[].name`, with the
  Photoshop name in `.layer`), and so do the file names of the arrays. `ael.develop.layer_names` returns the names.
- **Contributors.** Eduardo Piñas (@edu27) is credited with his full name, at his request (issue #4).
- Tests: the defaults, the old-recipe and the sign tests use the new name and default, and a new test checks the layer
  names; selftest 108 of 108. Checks and limits: `docs/VALIDATION_1.3.5.md`.

## 1.3.4 — 2026-10-28

Three reports by Eduardo Piñas (@edu27): a real-data check of issue #4 and issues #9 and #10. The `ael` package changes its
default WOW layer and the display of its ACHF layers, and rebuilds WOW bilateral. The Codex plugin goes to 1.1.1; the
Claude Code plugin of this repository's marketplace and the Claude plugin folder `plugins/claude-ael/` go to 1.3.4.

- **A new default WOW layer** (issue #4). WOW bilateral, the default Overlay layer up to 1.3.3, does not follow faint
  fine detail: with two independent half-stacks of the author's 2026 data (the layer of one against the band-pass of
  the other), its fine detail correlated at 0.08–0.20 with the data's own and 38–46 % of the clear detail came out
  inverted, as Edu measured on his frames. The default is now `wow`, made by `ael.filterbank.wow_measured`:
  - the noise of scales 1–3 is measured beyond 6 R☉ (`ael.filters.noise_factors`), relative to scale 0, and the coarser
    scales are extrapolated, half per scale. With the white-noise factors of 1.3.3, the correlated noise of a real
    stack (6–15 times white noise at scales 1–3, 2–8 px, on the 2026 fusion) was whitened into coarse blotches in the
    outer field. With 20 000 observed pixels or fewer beyond 6 R☉, or nothing left to measure there, white-noise
    factors are used and the parameters say so;
  - from scale 3 up, the local mean along each circle around the Sun is removed (a Gaussian of 45°): the radial curve
    subtracted before the WOW leaves ring-shaped residuals (up to about ±0.5–0.8 % in ln L at 3–9 R☉ on the 2026 data)
    that plain WOW turned into a dark ring at 4.75 R☉, marked by the author; a curve with denser knots made it worse.
    A narrower window (10°, in a first draft) darkened the circle beside compact bright features;
  - at an edge of the data (the Moon, an excluded band, the frame) the starlet averages symmetric observed pairs only,
    and each scale from 8 px up enters with the observed fraction of its kernel: a kernel cut by the edge sees one side
    only, and drew a level of up to ±6.6 % in the first 24 px outside the excluded lunar band of the 2026 data (found
    when this release was applied to the author's own final image);
  - the display spread is measured at 1.1–2 R☉, and the starting opacity stays at 0.37 (`ael.develop.DEFAULT_OPACITY`).
    At that opacity the new layer has about the fine contrast of WOW bilateral at 1.1–2 R☉ and less beyond (0.62 of it
    at 2–4 R☉, 0.33–0.39 at 4–8 R☉ on the author's data): the default image is softer there.
  On the author's data it passes Edu's gate (ρ 0.77–0.84 and 1.3–2.9 % inverted; in the worst 45° sector ρ ≥ 0.65 and
  at most 9.2 %, against a limit of 10 %), and the ring check on the author's fusion flags no ring (its lowest ring
  level at 4.3–5.1 R☉ is −0.004, where plain WOW made −0.036).
  `wow_bilateral` is still available and keeps its starting opacity of 0.37; a recipe that lists it without the new
  WOW keeps it visible, as in 1.3.3. The plain WOW of 1.3.3 is replaced.
- **WOW bilateral, rebuilt with guided range weights** (issue #4). `wow_bilateral` is now the operator of the WOW
  bilateral layer of the author's own 2026 image (B3 scales over symmetric observed pairs with range weights, eight
  scales, linear input, the local level of each scale removed), with one change: the range weights of each scale come
  from that scale smoothed without range weights, and the mean still comes from the data. In the scene of issue #4
  (flat profile, no noise) the faint pattern now comes out at +0.35; with range weights from the data the same
  operator gives −0.32, and WOW bilateral up to 1.3.3 −0.27. On the author's Sony, with Edu's gate, 3.9–5.3 % of the
  clear detail comes out inverted per ring (1.3.3: 38–47 %), but up to 17.9 % in the worst 45° sector, over the limit
  of 10 % (crosswise, one stack against the other: 5.3–8.3 % and up to 19.6 %), and the ring gate flags rings at 2.5
  and 4.4–4.7 R☉ (up to 0.017). It is therefore not the default, and
  issue #4 stays open for its worst sectors. It is the layer that keeps a lunar limb clean where the data reach it
  (next item); the author chose it for his own image.
- **The default WOW next to a lunar limb that the data reach** (not fixed). In the author's final image the corona data
  reach the Moon's limb: the band the Moon swept during totality was rebuilt frame by frame from clean data. There the
  default WOW draws concentric rings in the first 30 px from the edge of the data (2.9–3.4 times its own level far
  from the limb, in 15° sectors; the author's WOW bilateral layer: 1.4) and a band of 20–30 px where its texture is
  weaker (6 px from the edge, 0.4–0.55 of the texture far out; the author's layer: 0.7), with streaks along the limb.
  Ablations point mainly to its noise floor (next to the limb the data are single-instant frames, noisier, and the
  measured floor follows that noise) and to its log input. For such data, use `wow_bilateral`.
- **The ACHF layers no longer burn next to the limb** (issue #9). `display_detail` used one spread for the whole
  image. When the sky is left in the stack, that spread is set by the faint outer field and the detail near the limb
  saturates: on the author's calibrated map with its sky model added back, 27 % of the pixels at 0 and 60 % at 1 at
  1.08–1.2 R☉. The ACHF layers now take a level and a spread per ring (`display_detail_rings`), which also evens their
  contrast across radius. `"achf_display": "global"` in a filters recipe, or `make_filter(..., achf_display='global')`,
  keeps the 1.3.3 display. The per-ring display does not change the sign problems of the other ACHF variants.
- **`ael.gates.fine_detail_fidelity`**, the real-data gate Edu proposed (optional, for anyone with two independent
  stacks): a filter-free band-pass reference accredited ring by ring with a rotation null, the layer of one stack
  compared with the reference of the other, and the worst sector. Its default rings leave out the ring next to the
  Moon (1.12–1.2 R☉), where on the author's data the reference fails its own null.
- **Mirrored frames** (issue #10): `ael.coronagraph.scan_mirror` and the `"scan_mirror"` recipe key (always with the
  12° high-pass; validated against LASCO C2). `ael motion` recipes read `"mirrored"` and refuse unknown keys before
  writing anything; it was ignored without warning, and since no output of `ael motion` carries a position angle, no
  1.3.3 result changes. The coronagraph skill starts from the optics (an odd number of reflections mirrors the image)
  and decides the parity on the fine detail. A second check is optional.
- Tests: 23 new, each with a negative control (16 in `ael/_tests/test_lessons.py`, six in `test_coronagraph.py` and one
  in `test_ael.py`); selftest 107 of 107. Checks and limits: `docs/VALIDATION_1.3.4.md`. Edu's case:
  `docs/FIELD_LESSONS.md`.

## 1.3.3 — 2026-10-18

A contribution from outside the project, merged as one, and a rule for all of AEL. The `ael` package does not
change (its version number only; 84 of 84 tests). The Codex plugin goes to 1.1.0; the Claude Code plugin of this
repository's marketplace and the Claude plugin folder `plugins/claude-ael/` go to 1.3.3, with seven skills. That folder,
built from the Codex plugin by `tools/build_claude_plugin.py`, is in a library release for the first time.

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
- **A rule for all of AEL: correct each optic before fusing.** Different lenses, telescopes or cameras are never
  combined until each one's calibrated distortion correction has been applied, not even for a presentation
  (`AGENTS.md`, rule 11, and `docs/DEVELOP.md`). The new skill and the case study say the same.
- **Changes by the maintainer on top of that contribution:** colour propagated for display is a declared
  reconstruction in its own layer; the skill's links point to the copies in the package; the credit block moves from
  "Credit" to the README's Contributors section, and the authorship clauses in the skill and the case study become one
  line and a short Contributors section; the case study gains a maintainer's note on what came from private scripts;
  both plugins, the Codex receipt and the workflow counts are brought up to date.
Also since 1.3.2:

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
