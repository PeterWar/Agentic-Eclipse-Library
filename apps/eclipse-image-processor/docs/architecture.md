# Application architecture

This guide describes the active 0.6.0 implementation. See the [documentation index](README.md) for algorithm and export details.

## Entry point and responsibilities

| Module | Responsibility |
| --- | --- |
| `main.py`, `config.py` | CPU pool initialization before NumPy, application startup, styles and constants |
| `gui/app.py` | Window, source state, geometry, parameter snapshots and task coordination |
| `gui/filter_controls.py`, `gui/factories.py`, `gui/components.py` | Filter controls, units, resets and widget construction |
| `gui/image_view.py` | ROI painting, zoom, panning and overlays |
| `gui/background_controls.py`, `gui/background_tasks.py` | Sample editing and asynchronous preparation/presentation jobs |
| `core/image_data.py` | Observed support, native normalization bounds and support-aware resizing |
| `core/background.py`, `core/colour.py` | Working-data gradient correction and optional RGB gain calibration |
| `core/pipeline.py`, `core/layer_engine.py` | Resolution adaptation, independent numerical branches and composition |
| `core/filters.py`, `core/masked_filters.py` | Numerical operators, support-aware paths and persistent `FilterWorker` |
| `core/nrgf.py`, `core/ael_wow.py`, `core/ael_achf.py` | Bundled AEL-derived filters |
| `core/presentation.py` | PSB tone mapping, un-stretched base and display edge treatment |
| `core/export.py`, `core/layer_package.py`, `core/psb_export.py` | Export orchestration, layer-package writing and PSB serialization |
| `core/layer_export.py` | Quantization, blend/encoding helpers, JSX and package-entry alias |
| `core/project_settings.py`, `gui/project_settings.py` | JSON envelope and validated widget snapshots/restoration |
| `core/cancellation.py`, `core/parallelism.py` | Cooperative cancellation and bounded numerical concurrency |

## Data flow

1. Load source pixels and observed support. Retain immutable source arrays.
2. Optionally fit/subtract background slopes on native working data. Recompute mono from corrected RGB.
3. Establish normalization bounds from the native working image. Filters use float32 mono, with RGB luminance `0.299 R + 0.587 G + 0.114 B`.
4. Calculate each enabled filter independently from that shared mono input. Numerical branches never receive a preceding filter's output or a presentation curve.
5. Encode and compose cached layers. Choose an un-stretched linearly normalized base for the main TIFF, or a PSB presentation base for presentation preview/layer export.
6. Apply RGB presentation using the native calibrated RGB when calibration is enabled, then display-only edge antialias over black.

The linear input declaration is an assumption. It does not invert a transfer curve in an already stretched file. Enhanced composites are not photometric linear masters.

Observed support and statistical support are distinct: missing samples cannot be reconstructed by excluding the Moon from statistics. Float export stores missing samples as zero with a separate validity mask. Native source units remain available in working float products; they are not the original file if background correction is enabled.

## Resolutions and viewing

Fast editing reduces the longest side to at most 1500 pixels using observed-support area reduction. `prepare_parameters` maps pixel centres as `(x + 0.5) * scale - 0.5`, with separate axis factors; circular widths use their geometric mean. Native-unit controls are scaled down for preview; controls explicitly labelled preview pixels scale up for native processing. Angles remain degrees. Resampling changes filter statistics, so fast preview is approximate.

Fit selects the reduced view unless full-resolution verification is checked. 100%/200% request native results asynchronously, then reuse the rendered pixels for zoom/pan. Zoom denotes physical screen pixels, accounting for display pixel ratio. The painter crops the visible ROI; 200% does not allocate an enlarged full image and shows pixel blocks.

View Original bypasses detail layers but uses the prepared source and selected colour calibration. Disk overlay toggles only red geometry painting; it never changes pixels, statistics or filter signatures. It resets visible on each load. Sky-sample overlays have separate controls. All overlays are absent from export.

## Threads and stale results

The persistent `FilterWorker` runs numerical processing in a QThread. Task threads handle source loading, geometry, background preparation and presentation; `ExportThread` owns export snapshots. Workers operate on arrays and scalar settings, not widgets or QPixmaps. GUI callbacks validate source identities and revisions before accepting results. Load invalidation also occurs with Auto Calculate off.

Auto Calculate waits 650 ms after numerical edits. Layer-mix edits wait 250 ms after the last edit; PSB presentation edits use a 100 ms timer. Disabled auto mode requires a manual calculation for numerical edits. Closing cancels jobs and waits asynchronously rather than blocking the event loop.

Independent filter cache misses run concurrently within CPU and memory budgets; composition and file numbering remain ordered. Main initializes BLAS/OpenMP pools to one thread and OpenCV to at most two. Direct numerical callers must configure native pools themselves. See [layer cache and concurrency](layer-composition.md).

There is no sequential filter pipeline, Display Stretch/GHS route, Reveal slider or old settings migration. `apply_filter` accepts at most one active numerical operator; `execute_pipeline` always invokes the independent layer engine. Development tools and scientific fixtures are retained separately from runtime paths.
