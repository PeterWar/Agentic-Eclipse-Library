---
name: corona-filter-layers
description: Create full-canvas solar corona filter layers and optional layered 16-bit Photoshop files from linear eclipse data, preserving existing edits and missing-data masks.
---

# Corona filter layers

Read [setup and operating instructions](../../docs/USAGE.md) before running AEL. Resolve this plugin's root from this skill file and use its bundled launcher. Respond in the user's language. Work on user-selected inputs and write new output directories.

Read [filter recipes](../../docs/DEVELOP.md), [field lessons](../../docs/FIELD_LESSONS.md), and [paper versus library](../../docs/PAPER_AND_LIBRARY.md). Copy [filters_config_template.json](../../examples/filters_config_template.json) to the workspace and replace its sample settings with measured values.

Inputs are a linear image, geometry, validity, geometric coverage and base alpha. A stretched JPEG or finished Photoshop composite is not a linear HDR master. If the user wants to keep a finished edit, preserve it and describe separately whether new detail is recomputed or an existing layer is aligned; consult the [existing-edit case study](../../docs/EXISTING_EDIT_CASE_STUDY.md).

Run `filters --config RECIPE --out NEW_DIR` through the launcher. Use the requested filters, or explain the three default variants (NRGF, the edge-aware WOW and isotropic ACHF). Since 1.3.5 the default WOW is the edge-aware one (`wow_edge_aware`, called `wow_bilateral` up to 1.3.4), the author's operator with range weights taken from a guide; the plain WOW (`wow`, the default in 1.3.4) is optional. Next to a lunar limb that the data reach, recommend the edge-aware WOW; to use the plain WOW further out, suggest blending both layers with a feathered mask in Photoshop, never inside one layer. The ACHF layers are shown with a level and a spread per ring (`"achf_display": "global"` keeps the old display). The author's opacities are examples for his image, not calibrated settings for another eclipse. Known limitations: ACHF/WOW can make bands along straight data edges; the plain WOW draws rings and a band of weaker texture next to a lunar limb that the data reach; the edge-aware WOW keeps the limb clean but still inverts some faint detail in its worst sectors. With two independent stacks, check a layer's fine detail with `ael.gates.fine_detail_fidelity`. Inspect these areas and retain negative checks rather than claiming an artefact-free image.

Apply filters across the whole observed rectangle. Exclude the data-mixing band caused by the moving Moon from the filter input; measure its width for this observation. Do not replace missing data with reflected or generated pixels. ACHF works on log luminance after a smooth radial-profile subtraction, not independently on colour channels. Do not hide artefacts with new masks or smoothing.

Set `photoshop: true` only when a layered Photoshop file is wanted and the dependency is available. The 16-bit display/PSB is not the authoritative signed float master. Retain the NPY arrays, float TIFF, alpha and validity for scientific use. For PixInsight use `photoshop: false` and explicitly export/re-read float TIFF when needed.

Preserve the user's colour profile, masks, manual alignment and limb. Each proposed change is a separate layer or file. Verify PSB bytes with `ael.photoshop.verify` and distinguish that from native Photoshop rendering. Before opening a file in Photoshop, check inside the same script that it is not already open; use a uniquely named copy, save as a copy and close only the document opened by that script.

