# Processing settings JSON

Only **version 4** is accepted. Older versions, retired controls and unknown controls are rejected; there is no migration layer.

Save Settings Only writes controls and a source reference without running filters. Image export writes the same reloadable settings after TIFF/JPEG. Open Image / Settings restores the referenced original source and settings; pixels and numerical caches are not embedded.

## File envelope

`core/project_settings.py` owns the envelope:

| Field | Meaning |
| --- | --- |
| `format` | `eclipse-image-processor-settings` |
| `version` | Integer 4 |
| `source` | Absolute source path |
| `source_relative` | Relative source path, preferred on reopen when resolvable |
| `settings` | Validated GUI snapshot |
| `parameters` | Numerical parameter receipt |
| `display` | Display receipt; not a second set of GUI controls |

The source must exist and cannot itself be JSON. The reader limits files to 2 MiB. Writes reject nonfinite JSON numbers and publish through a same-directory temporary file, fsync and replace. The image and JSON can move together using the relative source path, with the absolute path as fallback.

## GUI snapshot

`gui/project_settings.py` validates exactly these top-level settings keys: `background_samples`, `controls`, `sections`, `geometry`, `auto_calculate`.

- Controls identify widget kind and value; combo boxes also carry validated text/index information. Slider values use raw integer ticks, not formatted physical-unit labels.
- Non-filter/global controls are required. Filter controls and sections can be omitted: filters reset to prepared defaults first, absent filter sections remain disabled, and absent ACHF Include flags remain unchecked. Previous-image edits are never inherited for omitted filters.
- Geometry contains integer-string x, y and radius, with positive radius. Section states and auto-calculation are booleans. Geometry section state is required.
- Background samples are null or a list of native integer coordinate pairs, at most 5000 points.

Explicit values must match supported controls and types. Slider restoration respects current bounds, with the supported dynamic upper bounds for FNRGF maximum radius/MGN sigma. Restoration uses two passes for linked slider bounds and rolls widgets/ranges back if restoration fails. Use a generated current JSON as a template rather than inventing control identifiers.

Disk-overlay visibility, zoom, View Original and the PSB-preview toggle are transient and not saved. Exposure and export options are saved. Source load resets the red circle/cross to visible.

Directly loading another image is a separate action from restoring JSON: it retains current filter settings and active/include flags, detects new geometry and regenerates background samples. First-load defaults are listed in [layer composition](layer-composition.md).

## Export failure boundaries

Settings-only publication is atomic. Image export writes layers first, TIFF/JPEG next, JSON last. Failure at a later stage can leave previously completed outputs; the complete multi-file export is not a single atomic transaction. The JSON is a recipe for the original source, not an instruction to reprocess its rendered output.
