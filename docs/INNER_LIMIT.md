# The inner limit of the corona filters

*Since 1.5.0. What it is, the one command that applies it, how to read its verdict, what was measured and what is not
solved. Everything here was found on one image — the total solar eclipse of 12 August 2026, two optics, 440 px per
solar radius, the Sun 9° above the horizon — where the author judged every version by eye, layer by layer.*

## The problem, in three sentences

Detail filters (NRGF, RHEF, MGN, ACHF, WOW…) were made for the corona. On the lunar limb they draw rims and dotted
lines along it, and on a prominence or a Baily's bead they saturate and ring, whatever the operator. And next to any
hole in the data — the Moon, a protected prominence, the frame — most of them draw bands parallel to the edge,
because the local reference each pixel is compared with is computed from a sample cut on one side.

Up to 1.4.2 the library protected nothing: every observed pixel went through every filter.

## What 1.5.0 does

1. **One map for all filters** — `ael.zones.inner_zones(rgb, valid, geometry)`. It classifies, pixel by pixel and
   from the data alone, what is corona and what is limb, chromosphere, prominence or bead. The pixels that are not
   corona are the **core**: no filter acts there and no filter *sees* it (it is taken out of every operator's
   support, so a bead that is the brightest value of the image cannot set an operator's global constants).
2. **A clean input** — around a prominence there is a faint haze of hydrogen light where the pixel is still 95 %
   corona. Those pixels stay in the filters' domain; the haze is taken out of what the filters read (red and blue
   clipped to the corona's colour, green corrected by a small measured term). Nothing is painted: the cleaned
   value is a linear combination of the three observed channels of the same pixel, and the display base still shows
   the prominence in its own colour.
3. **Operators that lean less on an edge** — `make_filter(..., edges='unbiased')`, the default. Two tools, neither
   of which invents a pixel (they only change the reference a pixel is compared with):
   - a **local polynomial fit** (`ael.filters.local_fit`): the mean a *whole* kernel would see of the polynomial
     fitted to the observed pixels. With the kernel whole it is the plain mean, so the filter is practically
     unchanged away from every edge;
   - the **chain**, for every statistic per annulus or per sector around the Sun: the *change* from one cut annulus
     to the next is measured on the angles both have, and summed inwards from the first whole annulus.
4. **Gates** in `ael.gates`: the inner limit (L), the false hole (F), gramophone grooves (D), and the map against a
   synthetic scene whose truth is known.

## The one command

```bash
python -m ael filters --config filters.json --out filter_run/
```

Nothing to add to the recipe: with the Moon in the geometry (`python -m ael geometry` measures it), the map, the
clean input and the unbiased operators are the default. The command prints a summary:

```json
"gates": {"verdict": "PASS", "layers": {"nrgf": {"inner_limit": "PASS"}, "…": {}}, "failed": [],
          "switched_off_by_a_gate": [], "between_layers": "PASS"},
"inner_limit": {"used": true, "map": "filter_run/inner_limit_map.png", "pixels": {"prominence": 4003, "…": 0},
                "warnings": []}
```

The receipt (`receipt.json`) keeps the whole of it under other names: `gates.layers.<name>.inner_limit` is an
object there, with `verdict`, `failures`, `warnings` and `notes`; `gates.inner_limit_between_layers` has the starts of the
layers sector by sector; and what the map measured is in `parameters.inner_limit` (with `why_not` when no map was
made).

### How to read it

| You see | It means | Do |
|---|---|---|
| `"verdict": "PASS"` | every layer starts where the map says and carries nothing inside the core | **look at `inner_limit_map.png`** (below), then use the layers |
| `"verdict": "WARN"` | a measurement is unusual; the layer is still on | read the warning next to the layer in the receipt (`gates.layers.<name>.inner_limit.warnings`) and look at that layer at 100 %, in Normal mode, where it says |
| `"verdict": "FAIL"` | a layer failed the gate (`failed` names it). If it was visible it is **in the file but switched off** and out of the preview (`switched_off_by_a_gate`); a layer that came hidden just stays hidden. With `failed` empty, the layers do not start at the same place (`between_layers`) | find the cause where it is born (the operator, the map, the stack); do not switch the layer on to "see if it looks fine". The Larson–Sekanina layers fail by construction: they leave out a band of their own next to the Moon |
| `"verdict": "NOT JUDGED"` | no map was made (`inner_limit.why_not` says why: no Moon in the geometry, the map could not be measured, or the recipe switched it off), or the recipe has no Overlay or Multiply layer | give the geometry the Moon and run again; without the map, filters act on every observed pixel, as in 1.4.2 |
| `inner_limit.warnings` not empty | the map could not measure something (a mono input: no colour, so no prominences; fewer than 150 px per solar radius; some degrees of the limb without a brightness trend) | read them aloud to the user; check the map by eye |

**Always open `inner_limit_map.png`**, enlarged (the map is to the pixel): corona grey, limb white, chromosphere
pink, prominences red, beads cyan, corona whose input was cleaned brown (and dark red, when `inner_zones` is called
directly on data that reach inside the Moon's circle, for core pixels inside it). Two questions: *is every red or pink pixel
emission?* and *is any corona coloured?* The gate of the pipeline cannot answer the second one (see "What the gates
cannot see").

### Five things never to do

1. **Never add a margin, a feather or a "safety" dilation to the core.** The corona between two prominences, inside
   the arch of one, or next to the limb with little signal is corona; a margin throws away exactly the fine inner
   detail one wants. If a rim shows at the edge of the core, the cause is in an operator or in the stack, not in the
   size of the core.
2. **Never use a detection threshold as a boundary.** "Five sigma redder than the corona" finds the haze of a
   prominence; it does not say the pixel is not corona.
3. **Never change a threshold to pass a layer** (`share`, `rim_share`, or any limit of a gate). If you believe a
   threshold is wrong, show it on a scene with the truth known, and say so.
4. **Never switch scales or filters off near an edge** to hide a band. That is a rule by fixed distance in disguise,
   and it draws its own band where it starts. The cure is an estimator without bias.
5. **Never touch the geometry of the lunar limb** (its position, its mask, its alpha) to make a filter look better.

### Recipe keys (all optional)

| Key | Values | |
|---|---|---|
| `"inner_limit"` | `"auto"` (default), `true`, `false` | `true` stops if the map cannot be made; `false`: filters act on every observed pixel, as in 1.4.2 |
| `"edges"` | `"unbiased"` (default), `"classic"` | `"classic"`: the operators of 1.4.2. One layer is not the 1.4.2 one with either value: the NRGF, whose chain over cut annuli is anchored on the whole ones since 1.5.0 (a correction) |
| `"gates"` | `"enforce"` (default), `"report"` | `"report"` leaves a failing layer on; the receipt says the gate was not enforced |

From Python: `inner_zones` returns the classes, the core, the clean input and what each criterion measured;
`zones.support(valid)` is the support for the filters; `ael.zones.zones_preview` makes the picture.

## How the map is made

Lengths are those of the 2026 image and scale with the Sun's radius in pixels, except those that are a matter of
sampling. "The contour" is the edge of the data around the Moon.

| Class | Criterion |
|---|---|
| Colour of the corona | per 10° sector around the Moon: 25th percentile of ln(R/G) and median of ln(B/G), 16–60 px from the contour; its noise, the MAD of the departures at 60–140 px |
| Detected emission (the input is cleaned there) | ln(R/G) above the corona's by more than 5 noises, in blobs of 6 px or more, within 160 px of the contour |
| **Core of emission** (chromosphere, prominences) | the light that is not corona — red excess plus blue excess — is **5 % of the pixel or more**; blobs of 6 px or more |
| **Beads** | within 40 px, single pixels 3 times brighter than the median of their arc (±8°), or bluer than the corona by more than 5 noises |
| **Limb** | the pixel at the edge of the data, and its **white rim**: per 2° angle, the brightness against the parabola of ln L fitted at 16–60 px of the same angle and continued inwards; rim where it exceeds that trend by **10 % or more**, from the contour up to where it stops doing so |

The white rim deserves a word. Where the Moon does not hide the base of the Sun, light of the limb scattered by the
optics leaves a rim one to three pixels wide that is not red: colour does not see it. On the 2026 image the brightness
follows the corona's trend up to 2 px from the real limb at the top, 3 px at the left, and jumps by 22–32 % below that;
at the right, where the Moon covered 26 px of low corona, there is no rim at all. Those pixels are not corona that a
stack could recover; passed to the filters as if they were, every operator drew a line on them.

`share` (5 %) and `rim_share` (10 %) are the two choices of the map. On the 2026 image a rim threshold of 5 % took
2 595 more pixels, up to 11 px from the limb, and part of a pocket of corona; moving the boundary one pixel "to the
foot of the step" improved one layer and worsened two. What is left at the first pixel outside the
core is each operator seeing one side only (see below), not the map.

## The operators

Each filter compares a pixel with a local reference: a mean, a spread, a rank among neighbours. Next to a hole that
reference comes from what is left, which is not a symmetric sample.

| Layer | With `edges='unbiased'` | Edge effect |
|---|---|---|
| `mgn` | the mean of each scale by local fit of **order 2** (the input is raw luminance, which falls steeply: order 1 still leaves a thin halo) | reduced, for its local part; its global term follows the extremes of the data |
| `achf_iso_*`, `hessian_ridge` | radial profile in chain; every Gaussian mean by local fit of order 2 | reduced |
| `nrgf`, `nrgf_log` | chain over cut annuli (since 1.4.1), anchored on the whole ones (1.5.0), with either value of `edges`. Where a 1° cell of an annulus holds fewer than six pixels (inside about 170 px from the Sun's centre) the chain does not act | reduced on a large image; unchanged on a small one |
| `fnrgf` (new) | inwards of the first whole annulus no Fourier series is fitted to a cut annulus: the ratio to the next annulus is fitted instead (with either value of `edges`) | small (see the table below) |
| `rhef_local60`, `rhef_local30` | the quantile table of a window the Moon cuts comes in chain from the next annulus | reduced (little changes on the 2026 limb: the effect was small) |
| `wow_edge_aware` (the default WOW) | **unchanged** | **not reduced**: three ways tried, all worse (below) |
| `wow` (plain) | **unchanged**; a dense-kernel variant exists as an option of `wow_measured` | **not reduced**: the variant the author's image uses fails a scene with the truth known (below) |
| `achf_angular*` | unchanged; it was already the layer with the least edge effect | — |
| `rhef`, `rhef_upsilon`, `steerable_g2`, `mmt`, `noise_gate`, `coherence_diffusion`, `nafe`, `swap`, Larson–Sekanina | unchanged; not examined | not examined |

Away from every edge a changed layer is practically the old one: the two tools reduce to the plain statistics where
the kernel, the annulus or the window is whole (the 1.4.2 operators approximate their Gaussians of 12 px or more on a
decimated grid, and the fits do not: that is the difference that remains). Measured on the 2026 layers the library's operators were ported from, 60 px or more
from the limb: correlation with the old layer 1.000 and a difference below 1 % of the layer's spread for the ACHF,
Hessian, FNRGF and RHEF; 0.999 and 4 % at 60–150 px for the MGN (1.000 and 1 % at 150–400 px).

Three more departures from the old layer, all measured: the chain of the radial profile is anchored on the first
annulus with 90 % of its pixels or more (on the 2026 canvas, the one at 458 px, with 9.8 % missing), not on a
complete one; the FNRGF evaluates its curves in a table of half a degree (0.0035 at most against the exact series);
and the chain of the local RHEF enters before the smoothing of the quantile tables along the radius, when that
smoothing is on.

### What the false hole measures (gate F)

Bands parallel to the limb cannot be told from corona by measuring the image; a measure of the image that tried gave
the opposite of what a person had marked. `ael.gates.false_hole` tests the *operator*: on the corona further out,
where all the data are there, pretend the hole is 80 px larger, and run the operator with the real hole and with the
false one. Outside the false hole every difference is an effect of the edge.

On a 2000 px crop of the 2026 linear image without its core, with the library's operators (differences in units of
the spread of each layer, per band of distance to the false hole; the smaller the better):

| Layer | Operator | 3–6 px | 6–12 px | 12–20 px | Against the 1.4.2 operator, hole grown by 80 px | by 160 px |
|---|---|---|---|---|---|---|
| `mgn` (its local part) | 1.4.2 (`classic`) | 2.09 | 1.57 | 1.12 |  |  |
| `mgn` (its local part) | **1.5.0 (`unbiased`)** | 0.23 | 0.20 | 0.19 | fails: 70-110 px: 0.07 → 0.10 | passes |
| `achf_iso_04` | 1.4.2 (`classic`) | 3.01 | 2.53 | 1.00 |  |  |
| `achf_iso_04` | **1.5.0 (`unbiased`)** | 0.58 | 0.37 | 0.16 | passes | passes |
| `hessian_ridge` | 1.4.2 (`classic`) | 3.75 | 3.21 | 1.23 |  |  |
| `hessian_ridge` | **1.5.0 (`unbiased`)** | 0.75 | 0.45 | 0.19 | passes | passes |
| `rhef_local30` | 1.4.2 (`classic`) | 0.88 | 0.70 | 0.46 |  |  |
| `rhef_local30` | **1.5.0 (`unbiased`)** | 0.42 | 0.32 | 0.23 | passes | passes |
| `rhef_local60` | 1.4.2 (`classic`) | 0.61 | 0.48 | 0.36 |  |  |
| `rhef_local60` | **1.5.0 (`unbiased`)** | 0.28 | 0.22 | 0.18 | passes | passes |
| `fnrgf` | new in 1.5.0 | 0.22 | 0.19 | 0.14 |  |  |
| `nrgf` | the same with either value of `edges` (not the 1.4.2 layer: its chain is anchored) | 0.11 | 0.10 | 0.04 |  |  |
| `wow_edge_aware` | the same in 1.4.2 and 1.5.0 | 0.52 | 0.43 | 0.34 |  |  |
| `achf_angular` | the same in 1.4.2 and 1.5.0 | 0.57 | 0.14 | 0.01 |  |  |
| `wow` | 1.3.4 (the default) | 0.86 | 0.73 | 0.56 |  |  |
| `wow` | dense-kernel option on the residual in chain, **not the default** | 0.33 | 0.25 | 0.18 | passes | passes |

What to keep from the table:

- The changes bring the edge effect down to between a half and a ninth. With the hole grown by 80 px **only the local
  part of the MGN passes the absolute verdict** of the gate (at most 0.5 of the fine detail from 3 px on); with 160 px
  the isotropic ACHF and the Hessian layer pass it too. The `mgn` layer as `ael filters` writes it, with its global
  term, reads 5.4 → 3.4 spreads at 3–6 px and fails with both values: the global term follows the extremes of the
  observed data, and a larger hole changes them. For the other layers the gate is an inventory of what is still owed, and the
  regression against the old operator is what decides.
- **One regression fails, as measured, and is shipped all the same:** the MGN of order 2 at 70–110 px with the hole
  grown by 80 px (0.07 → 0.10). It passes with 160 px and with the hole moved instead of grown: 80 px beyond the real
  hole, the "truth" still feels it at the two coarsest scales of the MGN, and the fit reaches further than the plain
  mean. (On the research layers the FNRGF in chain, against an FNRGF fitted annulus by annulus, also failed one band
  with the hole grown by 160 px, 0.49 → 0.56 of the detail at 20–36 px, and passed with 80 and 240; the library has
  only the chain.)
- The first pixel outside a hole stays the hardest: there every operator sees one side only (0.24–1.2 spreads of the
  layer at 1–3 px; 0.29–0.97 for the changed ones). That line of one to three pixels along the core is an operator's
  matter; moving the boundary only moves the line.

### The same question on a scene with the truth known

The false hole needs real data and still has a "truth" that feels the real hole. On a synthetic corona the truth is
exact: make the layer once with the corona going on under the Moon, once with the hole, and compare next to the hole
(a power law whose index changes with position angle, an off-centre Moon, 1 % noise; errors in spreads of the layer,
at 0–6 and 6–16 px from the edge, at 40 and at 160 px per solar radius):

| Layer | 1.4.2 operator | 1.5.0 `unbiased` |
|---|---|---|
| `achf_iso_04` | 3.9, 1.8 · 6.6, 3.2 | **0.75, 0.23 · 1.2, 0.34** |
| `hessian_ridge` | 8.0, 3.1 · 14, 7.0 | **1.4, 0.34 · 2.4, 0.79** |
| `rhef_local30` | 2.5, 0.0 · 3.5, 0.26 | 2.5, 0.0 · **1.7, 0.18** |
| `mgn` | 6.3, 4.5 · 4.1, 3.5 | 4.7, 3.5 · 2.8, 2.5 |
| `wow`, 1.3.4 (the default in both) | 0.79, 0.36 · 0.70, 0.49 | the same |
| `wow`, dense-kernel option | — | 2.3, 0.88 · 2.3, 1.4 (**worse**) |

The MGN improves little here: the scene is harsher than a real corona for a filter that works on raw luminance (what
the Moon hides is steeper than anything outside it), and no estimator can know it. The plain WOW is the case where
the two tests disagree, and the reason its dense-kernel variant is not the default (below).

### What was tried and did not work

- **The edge-aware WOW**, the default WOW layer, has no cure. Completing its coarse scales near the edge with
  dense-kernel coefficients made it much worse on luminance (0.64 → 1.42 at 3–6 px) and worse on the residual without
  the radial profile (0.91); working on the luminance divided by its radial profile was worse too (0.81, and 1.00 with
  the scales completed) and gave another layer (correlation 0.92–0.96 with the present one away from the limb). It
  works on raw luminance with range weights, and at 64–256 px what there is next to the hole is mostly profile.
  Curing it means rebuilding it on the residual, which would change it over the whole image.
- **The plain WOW without its fade near the edges.** The 1.3.4 WOW fades its coarse scales out where their kernel
  is cut; that fade is a change of regime at 16, 32 and 64 px of every edge, and on the 2026 layer it showed as
  straight bands. A starlet with the dense kernel of each scale and a local plane needs no fade
  (the residual of `radial_log_residual(partial_annuli='chain')` through
  `wow_measured(starlet_kernel='dense', edge_completeness=None)`): the false hole on the 2026 image reads 0.86 → 0.33
  spreads of the layer at 3–6 px, the author accepted the layer by eye, and his image uses it. But on synthetic
  coronae with the truth known, from 40 to 300 px per solar radius, it draws a level along the edge that the 1.3.4
  WOW does not — 0.18–0.24 of the display range against 0.02–0.09 in the first 16 px, and about three times the error
  against the same layer made with the data whole. A coarse coefficient computed from one side is biased, and the fade
  was hiding exactly that. The two measurements disagree; the default stays the 1.3.4 operator, the variant stays an
  option, and the plain WOW joins the edge-aware one among the layers without a cure.
- **An FNRGF with local statistics in polar coordinates** improved the gate and was another layer (correlation
  0.2–0.6 with the FNRGF away from the edge). The same for an RHEF as a local standardisation (0.7–0.8). Neither is a
  cure; both are ideas for filters.
- **Evaluating the polynomial at the pixel's own place** instead of taking its mean over the kernel: worse at the edge
  (a parabola extrapolated from one side is noisy).
- **A noise floor in the divisor** of the whitening or normalising layers does not improve the signal-to-noise ratio
  of any pixel: it lowers detail and noise alike, and it changes the brightness of layers such as the FNRGF. It is
  not a noise reduction. The library keeps it off by default (`wow_edge_aware(noise_floor=…)`).

## The gates

| Gate | Function | Asks | Run by `ael filters`? |
|---|---|---|---|
| **L** | `gates.inner_limit` | does each layer start where the map says, like the others, with nothing inside the core? | yes, enforced |
| **F** | `gates.false_hole`, `gates.false_hole_regression` | is a new or changed *operator* less sensitive to an edge than the one it replaces? | no: run it when you write or change an operator |
| **D** | `gates.gramophone` | did a new step add fine concentric rings to a layer? | no: run it **with the plain layer as `control`** |
| truth | `gates.zones_against_truth` on `synthetic.inner_scene` | does a map hold the emission *and* leave the corona, the pocket inside an arch included? | in the selftest; run it if you change `inner_zones` |

Notes on each:

- **L in the pipeline.** A Multiply layer is, inside the core, its own level (`filterbank.level_through_zones`); the
  first rule of the gate (L1, "nothing inside") reads the slope of that level across a core a few pixels wide as
  fine detail. For Multiply layers the pipeline reports an L1 failure as a warning and does not switch the layer
  off: on the 2026 image the author accepted by eye a layer that failed L1 this way. A layer that *starts* in the
  wrong place (L2) is switched off; with the library's layers that happens to those that keep a rule of their own
  at the limb (the Larson–Sekanina layers leave out a band next to the Moon).
- **"A streak follows the limb"** is reported by `ael filters` as a note, not a warning (called by itself,
  `gates.inner_limit` gives it as a warning): it is not calibrated, and nearly every layer has one at the first pixels.
- **D needs a control.** The exposure transitions of an HDR stack are concentric, and so are the cut annuli of a
  small frame: alone, the gate fails layers for rings the data carry (the plain NRGF of a 2000 px crop of the 2026 image
  fails it alone). With the same layer made the plain way as `control`, it finds the rings a step *adds*: a yardstick
  (level or spread per annulus) measured on a noisy layer and applied to a clean one, for instance. Use
  `filterbank.filter_detail` and `filterbank.frozen_display` to keep one yardstick for layers that must be compared.
  A filter with local sectors can draw arcs that differ from sector to sector; the gate compares sectors and does
  not see them.
- **Every gate has its negative control in the selftest**: a map with a 9 px margin, the plain mean at a false edge,
  injected rings, a layer that starts 15 px late.

### What the gates cannot see

- **A core that is too large.** Gate L checks that nothing is drawn inside the core, not that the core is no larger
  than it should be: a map with a margin passes it whole. On the 2026 image a rule "no zone by fixed distance" was
  written down, and three hours later a map with 9 px of margin was made; the gate passed it and a person
  found it, with a mark on a pocket of corona inside a prominence arch. That is why `zones_against_truth` exists,
  and why the map must be looked at.
- **That the corona is kept.** Gate F measures sensitivity to the hole. That a changed layer is still the old layer
  away from the edge is a separate comparison, and the two must be said together.
- **A real, irregular edge.** The grown false hole has a smooth edge; a cure that passed it drew rows of dots along
  the real one. `hole='shifted'` moves the real hole onto clean corona, for operators with local kernels. After any
  gate, look at the layer itself along the limb.

## Limits

- **One image.** The map, its two thresholds and every gate limit were set on the 2026 image, at 440 px per solar
  radius, with a golden corona under a low Sun and a camera whose colour matrix leaves the green almost free of
  hydrogen light. No second real image has been through `inner_zones`. On synthetic scenes the map recovers the
  truth at 150, 220 and 440 px per solar radius; below 150 px the map warns: the trend that finds the white rim is
  fitted on few pixels there, and no real image that small has been tried.
- **Small images.** The NRGF's chain does not act where a 1° cell of an annulus holds fewer than six pixels (inside
  about 170 px from the Sun's centre), and the FNRGF gives no output inside about 70 px (its cells are not scaled with
  the image) and needs linear brightness, not its logarithm.
- **Mono cameras**: without colour there are no prominences in the map; the limb, its rim and beads by brightness
  only.
- **The connectors for Photoshop and PixInsight keep the operators of 1.4.2** in this version (their NRGF layer
  carries the corrected chain): the inner limit has not been run inside the two programs.
- **`ael structure`** (the structure images of `ael.pipelines.structure_from_linear`) does not use the map.
- **Speed and memory.** The local fit is solved only where an edge cuts a kernel, band by band; on the 79-megapixel
  2026 canvas the ten layers of the validation run took 12.5 minutes.
- The dense starlet, the chain and the local fit change what a layer is within some tens of pixels of an edge.
  Compare with `"edges": "classic"` on the full canvas before adopting them for an image that already exists.

## Where things are

`ael/zones.py` · `ael/filters.py` (`local_fit`, `normalized_gaussian_fit`, `fnrgf`, `mgn(order=)`,
`starlet(kernel='dense')`) · `ael/filterbank.py` (`EDGES`, `radial_log_residual(partial_annuli='chain')`,
`level_through_zones`) · `ael/radial.py` (`radial_quantile_rank(partial_windows='chain')`) · `ael/gates.py` ·
`ael/synthetic.py` (`inner_scene`) · `ael/_tests/test_inner_limit.py` · figures:
[`VALIDATION_1.5.0.md`](VALIDATION_1.5.0.md).

References: Druckmüllerová, Morgan & Habbal (2011), ApJ 737, 88 (FNRGF); Morgan & Druckmüller (2014), Solar Physics
289, 2945 (MGN); Auchère et al. (2023), A&A 670, A66 (WOW); Gilly & Cranmer (2025) (RHEF); Cleveland (1979), JASA 74,
829, and Savitzky & Golay (1964), Anal. Chem. 36, 1627 (local polynomial regression).
