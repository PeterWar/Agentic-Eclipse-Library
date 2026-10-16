---
name: coronagraph-comparison
description: Compare eclipse observations with K-Cor, SOHO/LASCO and SDO/AIA using independent solar geometry, angular-structure nulls and correctly separated brightness measurements.
---

# Compare with coronagraphs

Read [setup and operating instructions](../../docs/USAGE.md) before running AEL. Resolve this plugin's root from this skill file and use its bundled launcher. Respond in the user's language. Work on user-selected inputs and write new output directories.

Read [the package guide](../../docs/README_AEL.md), [field lessons](../../docs/FIELD_LESSONS.md), and [the comparison template](../../examples/coronagraph_config_template.json). Detailed instrument guidance is in [coronagraph-method.md](../../docs/coronagraph-method.md).

Establish which question the data can answer:

- Structure: compare angular detail in separate solar frames, with orientation checks and null rotations. A good correlation after radial normalisation does not measure brightness or exclude every local artefact.
- Brightness: requires linear, sky-subtracted, extinction-corrected and photometrically calibrated data with uncertainty. A JPEG, filtered layer or display composite cannot be treated as mean solar brightness.

Use local reference files when provided. Before downloading observations or calibration tables, state their source, time range, purpose and approximate size and obtain authorization unless that exact download is already authorized. Use the observing date, not the 2026 example date. Reference pixels never enter the user's photograph.

Assign a separate `ael.coronagraph.SolarFrame` to each instrument. Preserve affine north/east axes from a plate solution; a pure rotation can be wrong. SOHO's apparent solar radius differs from Earth's. Check metadata, image scale, pylon/occulter masks and angular orientation before trusting a number.

Use `coronagraph --config RECIPE --out NEW_DIR` for structure. Report the zero-shift result, orientation search, fine-detail comparison and null maximum, including failures. Brightness work uses the `ael.coronagraph` Python API: K-Cor pB converted through p(r) gives K alone, while a photograph sees K+F; LASCO C2 has alternative published calibrations that must remain distinct. Do not tune a calibration to force agreement.

Keep input provenance, hashes, excluded regions, methods and uncertainty. Show diagnostic sheets. State the radius range tested and what remains unvalidated; external agreement is not a global certificate.

