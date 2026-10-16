---
name: corona-views-motion
description: Make full-canvas corona structure displays, unrolled polar views and motion analyses or animations from eclipse observations, with known-truth controls and explicit display choices.
---

# Corona views and motion

Read [setup and operating instructions](../../docs/USAGE.md) before running AEL. Resolve this plugin's root from this skill file and use its bundled launcher. Respond in the user's language. Work on user-selected inputs and write new output directories.

Read [the runnable package guide](../../docs/README_AEL.md) and the corresponding maintained source under `runtime/ael/` for API parameters. Run `selftest` before the first analysis.

For structure, use the plugin launcher `structure --input ARRAY --valid MASK --geometry GEOMETRY --out NEW_DIR`. It preserves the full canvas and defaults to mono. The radial brightness compression is a display transformation, not an absolute brightness measurement. Choose measured colour only for justified RGB data; a cool tint is an optional illustration style that needs the user's choice. Use a sky region supported by the field, never move it into the corona to force success.

For polar views, use `polar --input IMAGE --geometry GEOMETRY --out NEW_DIR`. Confirm the solar and lunar centres, orientation, parities and coverage. A polar transform is a derived view alongside the full original, not an authorisation to crop or change it.

For motion, read [the recipe template](../../examples/motion_config_template.json). Time-stamped exposure ladders form epochs aligned on the Sun. Compare short-time nulls and an intermediate epoch; reject sensor-fixed and Moon-fixed false motion and retain sensitivity limits. Correlation alone is not motion detection. Inspect the candidate check sheet before showing vectors as measured motion.

For an animation in an existing look, use `ael.pipelines.motion_gif` with the same recipe and noise treatment at each radius in every frame. Check grain uniformity (max/min <= 1.10) and changes unrolled in polar coordinates. Retain failures. No generated in-between observations. A second optical train already in the composite cannot be an independent judge of that domain.

For an exploration request use `demo-motion --out NEW_DIR`, whose output is labelled SYNTHETIC TEST DATA. Do not mix simulated pixels with real observations or advertise that demonstration as an astronomical discovery.

