---
name: eclipse-first-steps
description: Guide a newcomer through inspecting and processing their own total solar eclipse photos, or demonstrate Agentic Eclipse Library with labelled synthetic data.
---

# First steps with eclipse photographs

Read [setup and operating instructions](../../docs/USAGE.md) before running AEL. Resolve this plugin's root from this skill file and use its bundled launcher. Respond in the user's language. Work on user-selected inputs and write new output directories.

Use an already-stated goal. Otherwise ask whether the user wants to process photos, continue an existing edit, make an animation, or explore the library. A library question does not imply permission to process every image on disk.

1. Inventory the chosen folder: camera, optical train, ISO, exposure, timestamp, dimensions, totality interval and calibration frames. Ask only for information that affects the next action, including observing place/time when geometry needs it.
2. Check Python dependencies with `scripts/run_ael.py --check`, then run `selftest`. For an exploration request, `demo-motion --out NEW_DIR` needs no private photographs and must be described as synthetic test data.
3. For processing, read [the recipe guide](../../docs/DEVELOP.md). Measure black level, linearity/saturation, registration, solar geometry and colour response. Do not reuse the author's camera settings or guess them from filenames. Separate optical trains and correct distortion before fusion.
4. Preserve the linear result, valid mask, coverage, geometry and receipt. Explain missing calibration and clipped regions. Keep missing data empty.
5. Add requested filter layers or a full-canvas structure view. Explain the default filters and the unresolved ACHF/WOW boundary effects in [field lessons](../../docs/FIELD_LESSONS.md), that the default WOW is the edge-aware one since 1.3.5 (WOW bilateral, with guided range weights, renamed), and that where the data reach the lunar limb the plain WOW draws rings next to it and the edge-aware WOW does not; do not silently present these as proven fine structure. Show the result before adopting a change to an existing look.

Choose the matching bundled skill for the stage: `eclipse-calibration-stacking`, `corona-filter-layers`, `eclipse-artefact-diagnosis`, `corona-views-motion`, or `coronagraph-comparison`. The package's synthetic tests do not replace validation of the user's observation.

