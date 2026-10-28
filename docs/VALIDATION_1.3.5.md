# Validation of 1.3.5 (28 October 2026)

This release changes no operator. By decision of the author it makes the edge-aware WOW the default WOW layer, gives it
the name Auchère et al. (2023) use for their variant of WOW with a bilateral smoothing, and makes the plain WOW of 1.3.4
optional. The measurements are those of 1.3.4, where this layer is called WOW bilateral
([`VALIDATION_1.3.4.md`](VALIDATION_1.3.4.md#wow-bilateral-with-guided-range-weights)).

## What changed

1. `ael.filterbank.DEFAULTS` is NRGF, the edge-aware WOW (`wow_edge_aware`) and isotropic ACHF 04, with the starting
   opacities 0.39, 0.37 and 0.08 (`ael.develop.DEFAULT_OPACITY`).
2. `wow_bilateral` becomes `wow_edge_aware`. The old name is still accepted in a filters recipe (`filters`, `visible`,
   `opacities`) and from Python (`ael.filterbank.wow_bilateral` is the same function, and `make_filter('wow_bilateral',
   ...)` makes the edge-aware layer). A recipe that lists both names is refused: it would be the same layer twice.
3. The plain WOW (`wow`, `ael.filterbank.wow_measured`), the default of 1.3.4, is optional. A recipe that lists it
   without the edge-aware WOW keeps it visible at 0.37; listed next to the edge-aware WOW, it is a hidden layer.

## Why, and what it costs

| | Edge-aware WOW (default) | Plain WOW (optional) |
|---|---|---|
| Author's image: rings at 0–30 px from the limb, 15° sectors (times their null) | 1.2 | 2.9–3.4 |
| Author's image: texture 6 px from the edge of the data (times the texture far out) | 0.69 | 0.39–0.55 |
| Author's image: streaks along the limb at 6 px (radial over tangential gradient; 1 = none) | 1.03 | 1.75–1.86 |
| Edu's gate on the Sony: clear detail inverted per ring, 1.2–2 R☉ | 3.9–5.3 % | 0.6–2.4 % |
| Edu's gate: worst 45° sector (limit 10 %) | 8.5–17.9 % (fails at 1.3–2 R☉) | 2.2–8.4 % |
| Library gate, crosswise: per ring / worst sector | 5.3–8.3 % / 19.6 % (fails) | 1.3–2.9 % / 9.2 % |
| Ring gate on the Sony | fails: 2.5 and 4.4–4.7 R☉, up to 0.017 | −0.007 to +0.006 at 4.4–5.1 R☉ |

The author looked at his own image with the edge-aware WOW and saw no rings. The rule fixed before the gates of 1.3.4
kept the plain WOW as the default; this release departs from it by the author's decision, and says so. Issue #4 stays
open for the worst sectors of the edge-aware WOW.

## Recommendation

**Recommendation** (the author's, from his 2026 image; it agrees with Auchère et al. 2023, who found that the
edge-aware variant gives better results with spikes or edges): where the corona data reach the lunar limb, use the
edge-aware WOW, because the plain WOW draws concentric rings and a band of weaker texture there. If you prefer the
plain WOW further out, where it keeps faint fine detail more faithfully, use both layers and blend them with a
feathered mask: the edge-aware WOW next to the limb, over at least the first 0.5 R☉ (in the author's image the rings
of the plain WOW reach about 200 px from the edge of the data, 0.45 R☉), the plain WOW beyond, and a feather of
several tenths of R☉, so that the change of texture leaves no radial frontier. Blend them as two layers with masks in
Photoshop, never inside one layer. This blend has not been measured yet.

## Checks

- `python -m ael selftest`: **107 of 107**, in the source tree and from the installed wheel, with and without network.
  No test is new. Four tests follow the change: the table of defaults (now including the starting opacity of the plain
  WOW), the recipes written for older defaults (a 1.3.3 recipe gets the edge-aware layer under its old name, a 1.3.4
  recipe keeps the plain WOW, and both names together are refused), the sign test and the synthetic fine-detail gate
  (with the new name).
- The plugins carry the new defaults (Codex plugin 1.1.2, Claude plugin 1.3.5).

## Limits

- Those of 1.3.4. The edge-aware WOW still inverts up to 18–20 % of the clear detail in its worst sector on the author's
  Sony, and the ring gate flags rings there; by eye, in the author's image, no ring shows.
- The recommended blend of both layers with a feathered mask has not been measured.
