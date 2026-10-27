# Validation of the next release (prepared as 1.3.4)

This release answers three reports by Edu ([@edu27](https://github.com/edu27)), who photographed the 2026 eclipse
from northern Spain and tested AEL 1.3.3 on his frames: a real-data check of
[issue #4](https://github.com/PeterWar/Agentic-Eclipse-Library/issues/4) (WOW bilateral),
[issue #9](https://github.com/PeterWar/Agentic-Eclipse-Library/issues/9) (ACHF next to the limb) and
[issue #10](https://github.com/PeterWar/Agentic-Eclipse-Library/issues/10) (mirrored frames). His photographs are not
public, so his numbers cannot be reproduced here. Everything below was measured again on the author's own data of
the same eclipse: a Sony 300 mm train in two pointings, a Vixen refractor train, and their fusion.

- `python -m ael selftest`: **90 of 90** (84 from 1.3.3 and 6 new). Each new test has a negative control, and each
  fix was removed in a copy to check that its test then fails: going back to WOW bilateral as a default, to the
  WOW without its tangential step, or to one spread for the whole ACHF layer, fails 1, 3 and 1 tests.
- The detail-transfer regression of 1.3.0 (`test_filters_keep_injected_fine_detail_with_its_sign_and_strength`)
  passes unchanged with the new WOW and the per-ring ACHF display.

The logs, scripts and receipts named below are kept with the author
(`3-AEL/proves/contribucio_edu27_20261027/`). The gates were written down before the numbers they judge were computed
(`PORTES_FIXADES.json`, `PORTES_FIXADES_v2.json` there); where a check came after looking, it says so.

## What changed

1. **The default Overlay layer is a new WOW** (`ael.filterbank.wow_measured`, filter name `wow`), in place of WOW
   bilateral. It differs from the plain WOW of 1.3.3 in three ways:
   - the noise of each starlet scale is measured beyond 6 R☉ (`ael.filters.noise_factors`) instead of assumed white;
   - from scale 3 up (8 px and coarser), the local mean along each circle around the Sun is removed (a Gaussian of 10°);
   - the display spread is measured at 1.1–2 R☉ instead of over the whole frame.
   The starting opacity stays at 0.37. `wow_bilateral` is still available; the plain WOW of 1.3.3 is replaced.
2. **The ACHF layers get a level and a spread per ring** (`display_detail_rings`): medians and spreads in annuli of
   2 px, averaged over three annuli and interpolated in radius. `achf_display: "global"` keeps the 1.3.3 display.
3. **`ael.gates.fine_detail_fidelity`**, the real-data gate Edu proposed for issue #4.

## Issue #4: WOW bilateral and the new WOW

**Edu's gate on the author's data.** Two independent stacks: the Sony's pointing A (9 frames) and pointing B
(12 frames, none shared), about 750 sensor pixels apart after a mount jump, on one canvas binned 2 × 2 (4.30″/px,
R☉ = 220 px). The reference is the data's own fine detail without any filter (band-pass σ 1.5 → 6 px of ln L). It is
real at 1.2–2.0 R☉: the two stacks agree at ρ = 0.95–0.98, and a rotation of 30° about the Sun brings that to 0.02.
At 1.12–1.2 R☉ it is not: the rotation null gives 0.50, because the band-pass picks up a bias within about 14 px of
the edge without data (+3.9σ at 6–8 px). That ring is not judged.

| Layer | ρ with the reference | Clear detail inverted | ρ between the stacks | Worst 45° sector |
|---|---|---|---|---|
| WOW bilateral (1.3.3 default) | 0.08–0.20 | 38–47 % | 0.77–0.92 | ρ −0.16, 57 % inverted |
| Plain WOW (1.3.3) | 0.78–0.84 | 0.5–1.1 % | 0.84–0.95 | ρ ≥ 0.65, ≤ 7.4 % |
| WOW of this release | 0.82–0.86 | 0.6–1.6 % | 0.87–0.96 | ρ ≥ 0.70, ≤ 9.5 % |

Rings 1.2–1.3, 1.3–1.5 and 1.5–2.0 R☉; thresholds fixed before (ρ ≥ 0.5, at most 10 % inverted, ρ between stacks
≥ 0.5). The Vixen train gives the same picture at full resolution (WOW bilateral 41–45 % inverted). A layer unrelated
to the data inverts about 50 %, so WOW bilateral's fine detail has almost nothing to do with the data's; it is the
same in both stacks, so it comes from the operator. `ael.gates.fine_detail_fidelity` (crosswise: the layer of one stack
against the reference of the other) gives the WOW of this release ρ 0.76–0.83, 1.3–2.6 % inverted, worst sector
ρ ≥ 0.66 and ≤ 9.4 %: it passes. WOW bilateral and the new WOW with its detail inverted fail.

With a coarse band-pass (6 → 24 px), the crosswise correlation is 0.08–0.15 for WOW bilateral, 0.45 / 0.73 / 0.57 for
plain WOW and 0.43 / 0.71 / 0.60 for the new one (1.2–1.5, 1.5–2, 2–3 R☉): the tangential step keeps loops and arcs at
the coarse scales.

**Blotches in the outer field.** On the author's fusion, plain WOW filled the outer field with coarse blotches. Its
noise floor assumes white noise; the noise of the stack is correlated (registration, fusion). Measured beyond
6 R☉, the noise of scales 0–5 relative to the pixel noise is 0.89, 1.25, 1.01, 0.62, 0.31 and 0.15, against 0.89,
0.20, 0.086, 0.041, 0.021 and 0.010 for white noise: 6 to 15 times more at scales 1–3. `render.structure_image`
already measured it; the filter bank did not.

**A ring at 4.75 R☉.** The author marked a dark ring at 4.3–5.0 R☉ (and a piece at 7.3 R☉) on a full-canvas view of
plain WOW. It is not in the data: the level, the grain and the coverage of the fusion have no step there. It comes from
the radial curve the library subtracts before the WOW (`radial_log_residual`, a cubic spline in ln r with fixed knots
up to 6 R☉): its residual per ring is −0.5 % at 4.6–4.8 R☉, +0.5 % at 5.9 and −0.7 % at 8.2, and the level of plain
WOW per ring follows it (−0.036 at 4.8 R☉, +0.025 at 5.9). It is also in 1.3.3, weaker in WOW bilateral, which
removes the smooth bias inside its coarse scales.

What did not cure it:
- **More knots.** With knots every 0.06 in ln r the residual smoothed over 45 px fell from 0.50 % to 0.013 % at
  4–5.5 R☉, but every WOW layer, WOW bilateral included, filled with rings at all radii: the curve then follows the
  ripples of the ring medians, which change with the mix of rays and gaps in each annulus, and prints them on every
  angle.
- **Other curves** (ring means instead of medians, a sky plane fitted together with the curve, dense knots only where
  an annulus is fully covered) were better on the Sony and worse on the Vixen, where the change from dense to sparse
  knots made a new ring. A radially symmetric curve fitted to one eclipse is not robust across data sets.
- **Removing an isotropic local mean** from the coarse scales (as WOW bilateral does) brought the ring down to a
  third, −0.012.
- **A guide for the bilateral weights** (range weights from the data smoothed at each scale's step) cured most of the
  sign problem (ρ 0.61–0.71) but left 8–13 % of the detail inverted, 15–24 % in the worst sector, and more rings.

What cured it: removing, from scale 3 up, the local mean along each circle around the Sun. A ring is constant along
its circle; a ray or a loop varies along it. Ring level per 0.05 R☉ (median of 16 sectors) on the author's fusion at
full resolution, 1.2–9 R☉: RMS 0.0022 for WOW bilateral, 0.0142 for plain WOW and 0.0039 for the new WOW; at
4.3–5.1 R☉ its lowest ring is −0.0045 (WOW bilateral −0.0034, plain WOW −0.036). It leaves no radial streaks: in the
outer field (6–8 R☉) the correlation at 2 and 4 px is the same along the radius and along the circle (index 0.996 and
0.994, as without the step).

**Ring gate with a null.** On the Sony, with all layers made on the mask common to both pointings and the noise of a
ring level calibrated from WOW bilateral on pointing A against pointing B (the null passes), the new WOW is clean at
4.4–5.1 R☉ (|level| ≤ 0.005, where WOW bilateral has +0.02–0.03 and plain WOW +0.05–0.09). The gate as written still
fails it: at 2.5–2.9 R☉ its median per ring is −0.010 to −0.020, where WOW bilateral is near 0, and its own A-against-B
null fails at 1.875 R☉. A check made after seeing this: there the layer's mean is −0.0015 and its skewness +0.23, so
the low median comes from bright narrow rays on a slightly negative background, which a median per ring reads as a
level. The gate also missed a ring of 0.01 injected at 4.75 R☉: depending on the radius, it cannot see rings smaller
than 0.01–0.02 (more where WOW bilateral itself differs between the two pointings).

## Issue #9: ACHF next to the limb

`display_detail` used one robust spread for the whole layer. With the sky in the frame most pixels are faint outer
field, the spread is small, and the high-pass detail next to the limb saturates. On the author's calibrated map with
the sky added back (binned 2 × 2), `achf_iso_04` put 27 % of the pixels at 0 and 60 % at 1 at 1.08–1.2 R☉, and 41 %
and 35 % at 1.2–1.5 R☉. With Edu's level and spread per ring, every ring has a median of 0.50 ± 0.013 and less than
1 % at either end, on that map and on a synthetic corona with sky. Both halves are needed: the level alone still clips
20–31 % at each end, the spread alone leaves the median at 0.58 next to the limb. The same global display made the
angular ACHF layers fail in the same way; they also take the per-ring display. The per-ring display equalises the
contrast across radius: on the author's data the outer corona comes out two to four times stronger in these layers.

## Issue #3 with the new defaults

The scene of issue #3 (a smooth corona, the Moon 9 px off the Sun's centre at R☉ = 60 px, a straight coverage edge):
the default ACHF layer is now 0.07 brighter 5 px from the lunar data edge (0.19 in 1.3.3) and 0.52 brighter next to
the straight edge (0.61); the new WOW, at most −0.06 at the limb (1 px) and 0.26 next to the straight edge (plain WOW:
0.03 and 0.34). The bands along straight edges remain open.

## Limits

- One eclipse. The two trains and their fusion share the Sony outer field; the curves for the ring were chosen on the
  Sony and the Vixen binned, and the gates were run on the Sony and on the fusion.
- The tangential step removes, at 8 px and coarser, whatever is constant along circles around the Sun over about 10°.
  The corona has no such rings, but a long tangential arc at those scales would be weakened; the coarse correlation
  above did not drop.
- The display spread of the new WOW comes from 1.1–2 R☉ (from every pixel when fewer than 1000 pixels are there).
- WOW bilateral keeps its sign problem; issue #4 stays open for it. Issue #3 stays open.
- The ring gate is coarse (0.01–0.02) and reads skewed detail as a level; a better null and a statistic that is not
  fooled by rays are still to be written.
