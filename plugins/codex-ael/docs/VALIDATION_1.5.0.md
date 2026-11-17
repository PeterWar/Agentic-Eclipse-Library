# Validation of AEL 1.5.0

*17 November 2026. What was checked before release, on which data, and what was not. Method and reading guide:
[`INNER_LIMIT.md`](INNER_LIMIT.md).*

Three verdicts are kept apart, as in every validation of this library: the **method** (does it do the right thing?),
the **integrity** of what is delivered (is the file what the receipt says?) and the **visual or scientific**
validation (did a person or an independent measurement accept the result?). A passing software test is not the third.

## 1. Known-truth tests

`python -m ael selftest`: **157 of 157**, from the source tree and from the installed wheel, with and without network
access. Twenty tests are new since 1.4.2: fifteen in `ael/_tests/test_inner_limit.py`, three in `test_structure.py`
and two in `test_extinction.py`; one of `test_nafe_swap_larson.py` was extended for the new defaults. Each check of
the inner limit has its negative control:

| What is checked | Truth | Negative control |
|---|---|---|
| The map holds the emission, the white rim and the beads, and leaves the corona and the pocket inside an arch | `synthetic.inner_scene`, 220 px per solar radius | the same map grown by 9 px fails on the pocket and on the corona; the map without its white rim fails on the rim |
| A hole in the data away from the Moon is no lunar limb; a mono input says it found no emission | a masked "star"; the luminance alone | — |
| `local_fit` is the plain mean where the kernel is whole, and exact for a quadratic surface at an edge | an analytic surface | the plain mean is off by 5 units where order 2 is off by 0.009 |
| MGN of order 2 next to the limb | the MGN of the same corona without the hole | the plain mean is more than twice as far from it |
| Dense starlet: exact reconstruction, the à-trous transform away from edges, closer coefficients next to the hole | the transform without the hole | the à-trous coefficients |
| Radial profile in chain | the residual of the same corona with every annulus whole | observed medians: 0.106 rms in the most cut annuli against 0.043 in chain |
| FNRGF: defined on the cut annuli, mean 0 on the whole ones, a bright sector not lifted as a whole | — | the NRGF lifts it; a strip of data with no whole annulus is refused |
| Local RHEF in chain: the usual rank where windows are whole; windows the frame cuts are left as observed | a centred Moon (identical arrays) | an off-centre Moon changes only the annuli it cuts |
| `edges`: the changed layers differ next to an edge and not away from it; both WOW layers, the angular ACHF and the NRGF are the same with either value | — | — |
| ACHF and Hessian `unbiased` against the 1.4.2 operators next to the hole; the plain WOW left alone | each layer made with the data whole | the 1.4.2 operators are more than 2.5 times further; the dense-kernel WOW is more than 1.5 times further than the default (measured: about three times) |
| False hole | — | the plain mean fails the absolute verdict; the cure undone is a regression; losing coverage is a failure |
| Gramophone gate | a smooth random layer | injected rings of level and of grain fail; the same rings in the control do not; rings about another centre do not |
| Inner-limit gate | three good synthetic layers on the scene's map | detail inside the core fails; a layer that starts 15 px late fails; a layer that is flat over its first 15 px fails at any level; layers that start in different places fail together |
| `ael filters` end to end | the scene's map | a layer with a rule of its own at the limb (Larson–Sekanina) fails and is written switched off; `"gates": "report"` leaves it on and says so; `inner_limit: false` with `edges: "classic"` gives the array that `make_filter(..., edges="classic")` gives for the isotropic ACHF, bit for bit; a mono input and a map that cannot be measured are reported |

**The commands in other hands.** A smaller language model than the one that wrote this version was given the
repository's documents, an installed 1.5.0 and a folder with a synthetic stack (no geometry file), and asked for the
filter layers and whether they could be trusted. It ran `python -m ael geometry` and `python -m ael filters`, read
the verdict (`WARN`: the level of the NRGF through the core) with its meaning, opened the map and described the
prominences on it, and added no margin. Its map had the same pixel counts as the author's run of the same recipe.
One trial, on one scene.

Two tests of earlier versions changed. The recipe test of 1.4.2 (NAFE covers a red knot) now asks for
`inner_limit: false`, and checks that by default the knot is in the core and no layer covers it. The test of the level
that a WOW layer draws along an edge (1.3.4) is unchanged and decided a default: the dense-kernel variant of the plain
WOW fails it.

## 2. The library against the research code it was ported from

The map and the operators were written first as scripts on the author's 2026 canvas, with its centres and sizes fixed
in the code. The library's versions take any geometry. On the same input:

| | Compared with | Result |
|---|---|---|
| `inner_zones` on the 2026 linear image (10 551 × 7 506 px) | the map of the author's accepted layers | core identical (24 105 px, none different); classes identical; support for the filters identical |
| The clean input | the same | the same 26 286 pixels changed; values within 9·10⁻⁶ of their own size (float32 rounding of an angle) |
| The local part of the MGN (order 2), isotropic ACHF, FNRGF (2000 px crop) | the research operators | same domain; largest difference 1.4·10⁻⁵ of the layer's spread or less |
| Local RHEF 30° and 60°, with the quantiles smoothed over nine annuli as in the research layers (`smooth_bins=9`; `make_filter` does not smooth them) | the same | identical within 400 px of the Moon; beyond 950 px from the Sun, where the frame of the crop cuts the windows, different on purpose (below) |
| Hessian layer | the same | largest difference 0.004 of the spread, at isolated pixels (its weight is a non-linear function of the smoothed image) |
| Dense-kernel plain WOW (the option), on the residual of the radial profile in chain | the same | largest difference 7·10⁻⁷ of the spread |
| Gate D (gramophone) | the project's gate on the same layer | all 20 measures identical |
| Gate F (false hole): local part of the MGN, isotropic ACHF, Hessian, local RHEF 30° and 60° | the project's table for the same layers | 2.09 → 0.23, 3.01 → 0.58, 3.75 → 0.75, 0.88 → 0.42, 0.61 → 0.28 at 3–6 px, against 2.09 → 0.23, 3.04 → 0.59, 3.25 → 0.66, 0.87 → 0.42, 0.63 → 0.31 measured on a 2400 px crop |

The local fit is solved only where an edge cuts the kernel (elsewhere it is the plain mean, exactly). That is what
the differences of 10⁻⁵ are; the run is shorter, and the moments are no longer held for the whole canvas at once.

**One departure from the research code, on purpose.** The chain of the local RHEF was also applied to the windows
that the *frame* cuts, bridging them from the outside in, which anchors them on the corner of the image instead of on
a whole window (on a small test image that moved ranks by up to 0.47). The library bridges only inwards from a whole
window, which is what the Moon's side needs; frame-cut windows are left as observed. Next to the Moon nothing changes.

## 3. The 2026 image through `ael filters`

The whole canvas (79 megapixels, 440.6 px per solar radius), ten layers, from one recipe with no key about the inner
limit and `"moon_margin_px": 0` (the default is 2):

- **Map:** 3 243 limb and rim pixels, 5 103 of chromosphere, 4 003 of prominences, 482 of beads; 1 925 corona pixels
  with their input cleaned. One warning: no brightness trend could be fitted along 2° of the limb. The command
  removes the Moon's disc first, so its map is not the one of §2 (which is made with the data that reach inside the
  Moon's circle left in): outside the circle the command's core has 12 831 pixels against 11 306, 1 582 more (nine in
  ten of them within 1.2 px of the circle, the furthest at 10 px) and 57 fewer.
- **Gate L:** `PASS` for all ten (`nrgf`, `wow_edge_aware`, `achf_iso_04`, `fnrgf`, `mgn`, `rhef_local30`,
  `rhef_local60`, `wow`, `hessian_ridge`, `achf_angular`). Every layer starts at the first pixel outside the core (one
  pixel later for the MGN and the angular ACHF) and the starts of the ten differ by at most 1 px in all twelve sectors. Detail inside the core:
  0 for the Overlay layers (transparent there); 0.12–0.26 levels of 255 for the Multiply layers (their level).
  (The gate was corrected after an independent reading of the code: it measured the detail of a layer with a plain
  blur, which read the step between a layer's level and the void beside it as detail and passed a layer that was flat
  at the limit. It now uses the mean over the pixels the layer has; the figures here are with the corrected gate.)
- **Notes** (not warnings): nine of the ten have "a streak follows the limb" at the first 1–7 px (5.6 to 24.7 levels,
  6 to 16 times the spread of the layer's median beyond 12 px). It is the first pixels of each operator next to the
  core.
- **Time:** 12.5 minutes for the ten layers with the map and the unbiased operators, 9.4 minutes for nine layers with
  `inner_limit: false` and `edges: "classic"`, on the same machine while it ran other jobs.
- **Gate D without a control**, on the plain NRGF of a 2000 px crop of the same image: FAIL (coherence 0.27–0.33 in
  the fine rings of level, 0.26 in those of grain). The gate is right about the rings and cannot say whose they are; that is why `ael filters` does not run it.

**Visual validation:** the layers the author accepted by eye on 12 November were those of the research code (§2:
the library gives the same map, and the same operators to within 1.4·10⁻⁵ of the spread, 0.004 for the Hessian layer,
the local RHEF within 400 px of the Moon). The layers written by `ael filters` in
this run — with the library's display curves, not the frozen curves of his file — have not been looked at by him.

## 4. Decisions the measurements made

- **The plain WOW keeps its 1.3.4 operator.** Its dense-kernel variant improves the false hole on the 2026 image and
  fails the 1.3.4 test with the truth known (§1; figures in `INNER_LIMIT.md`). Two tests that disagree do not make a
  default.
- **`ael filters` enforces gate L only.** Gate D needs a control (§3). In gate L, the rule "nothing inside the core"
  is not enforced for Multiply layers, whose level it reads as detail; it is reported.
- **The connectors keep the operators of 1.4.2.** Their engine asks for `inner_limit: false` and `edges: "classic"`.
  Their NRGF layer still changes, by the corrected chain (§5).

## 5. Packages

What the release carries, and how each piece is checked before it is published (the results of that run are in the
release notes and in the `SHA256SUMS` files of the release, which are made from the tagged commit):

- **The wheel** is built from the tagged commit with `SOURCE_DATE_EPOCH=1794873600`, so that anyone can build the same
  bytes; the selftest runs from the source tree and from the installed wheel, with and without network access.
- **The Codex plugin 1.1.7** bundles the engine, this document and `INNER_LIMIT.md`; its skill for filter layers
  reads the verdict of `filters` in three steps. Its ZIP goes through the seventeen integration checks of
  `tools/test_codex_plugin.py`, which run the bundled selftest.
- **The Claude plugin folder** (instructions only) installs this wheel by its SHA-256 fingerprint;
  `tools/build_claude_plugin.py --check` compares it with the Codex plugin and with what Claude's directory accepts.
- **The connectors for PixInsight and Photoshop**: scripts and dialogs unchanged. Two places of their Python engine
  are new (`python/ael_auto.py`, `python/ael_workflow.py`: they ask the library for `inner_limit: false` and
  `edges: "classic"`), and the packages carry the 1.5.0 library. `tools/check_connectors.py` and the tests that
  need no program run on both. On six frames of the 2026 eclipse the engine of both packages gives the same linear
  master and the same edge-aware WOW and isotropic ACHF layers as the 1.4.2 packages, pixel for pixel; the NRGF
  layer differs by 0.2 % of the display range in the median and 1 % at most (its chain is anchored on the whole
  annuli). They were **not** opened inside PixInsight or Photoshop for this version.

## 6. Not validated

- **A second real image.** Everything in §2–§3 is the 2026 eclipse. The map's two thresholds (5 % and 10 %) and the
  limits of the gates were set on it.
- **Other samplings on real data.** Synthetic scenes at 150, 220 and 440 px per solar radius recover the truth; no
  real image at another scale has been tried.
- **The inner limit inside PixInsight or Photoshop.**
- **The absolute errors of "practically the same".** Away from the edges the changed layers were compared with the old
  ones by correlation and by difference over the spread (figures in `INNER_LIMIT.md`), on the research layers, not
  pixel by pixel on the library's.
- **Annuli missing in the middle of the data, and the seam of the angle** in the chains: the FNRGF refuses a ring
  without data between fitted rings; the others have no test for it.
- **Native Photoshop.** As before, the PSB is verified by reopening it with the library, not by the application.
