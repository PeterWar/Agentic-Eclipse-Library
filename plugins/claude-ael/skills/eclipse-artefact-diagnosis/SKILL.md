---
name: eclipse-artefact-diagnosis
description: Trace rings, seams, ghosts, striping or limb fringes in an eclipse image to their source and test a causal correction without hiding the defect or changing manual edits.
---

# Diagnose an eclipse artefact

Read [setup and operating instructions](../../docs/USAGE.md) before running AEL. This plugin holds instructions only: run the AEL 1.5.0 engine installed and checked as that guide describes. Respond in the user's language. Work on user-selected inputs and write new output directories.

Start from the user's marked defect and the available data lineage. Read [field lessons](../../docs/FIELD_LESSONS.md), especially the boundary bands that remain (both WOW layers; the ACHF along straight coverage or frame edges), the rings of the plain WOW next to a lunar limb that the data reach, and the fine-detail sign inversion that the edge-aware WOW keeps in its worst sectors. A visible ring is not automatically a calibration problem. For a rim on a prominence or a bead, or a band parallel to the lunar limb in a filter layer, read [the inner limit](../../docs/INNER_LIMIT.md) first: since AEL 1.5.0 `filters` keeps the layers off what is not corona and reports a verdict; a band along an edge is tested on the operator with a false hole (`ael.gates.false_hole`; its `absolute` verdict fails for nearly every layer, so read the bands and compare a change with what it replaces, `false_hole_regression`), and fine concentric rings against the plain layer as control (`ael.gates.gramophone`).

1. Identify the source files, hashes, geometry, recipes, manual edits and first stage where the defect appears. Compare raw/calibrated data, stack, support/weights, operator output and final display with the same views and measurements.
2. Use independent exposures or sensor positions where available. Shared sensor structure and witnesses fitted to the same total stack are not independent evidence. Check dark/flat response, saturation taper, spatial clouds, coverage edges and the operator's radial statistics as appropriate.
3. Fix only a demonstrated cause. Rebuild all dependent products; a new layer above an unchanged defective layer is not a causal repair. Keep the original files and the failed experiment.
4. Use a null, injected controls where meaningful, a baseline known to fail and unchanged thresholds. A good aggregate does not cancel a local failure. State when the available data cannot identify the cause.
5. Inspect the delivered pixels at the limb, boundaries and corners, with the full canvas available. Report method, file integrity and visual/scientific validation separately.

No cosmetic blur, filled gaps, mirrored texture, repainted stars, altered lunar geometry or borrowed reference pixels. Do not loosen a threshold to pass a candidate. For corrections that change a familiar colour or look, show the proposed full-canvas comparison and obtain the user's choice before adopting it. Use [the recipe guide](../../docs/DEVELOP.md) to regenerate maintained AEL stages; historical scripts are not bundled or guaranteed to replay.

