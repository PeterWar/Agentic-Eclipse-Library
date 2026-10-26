# Technical documentation

Current implementation: Eclipse Image Processor 0.6.0. Updated 26 October 2026 from the application source. The guides below describe the active pipeline; dated reports record earlier experiments and do not override these guides.

## Current guides

| Guide | Scope |
| --- | --- |
| [Application README](../README.md) | Installation, workflow, initial settings, outputs and scientific credits |
| [Architecture](architecture.md) | Modules, working data, threads, cancellation and resolution handling |
| [Layer composition](layer-composition.md) | Independent filters, blend modes, controls and caches |
| [Background extraction](background-extraction.md) | Sky samples, robust plane fitting and slope subtraction |
| [Settings JSON](settings.md) | Version 4 schema, restoration and source paths |
| [PSB export](psb-export.md) | Presentation, layer files, verification, colour correction and limits |
| [AEL ACHF](achf-ael.md) | ISO 01, ISO 04 and Angular implementation |
| [Larson–Sekanina](larson-sekanina.md) | Rotational residual, Gain and Linear Light encoding |
| [Continuous RHEF](rhef-continuous.md) | Quantile interpolation and support rules |
| [Validation](validation.md) | Reproducible checks and the limits of existing evidence |
| [macOS build](build-macos.md) / [Windows build](build-windows.md) | Platform packaging |
| [Third-party attribution](../ATTRIBUTIONS.md) | Copied/adapted code and retained licence notices |

## Historical research and implementation reports

These documents retain their original measurements and design decisions. They can mention removed controls, sequential processing, previous defaults and export contracts that no longer apply.

- [AEL filter review](ael-filter-review.md): AEL 1.3.2 research.
- [External filter ideas, 19 October](external-filter-ideas-20261019.md).
- [Filter controls, 19 October](filter-controls-20261019.md).
- [Filter validation, 19 October](filter-validation-20261019.md).
- [GHS reference, 19 October](ghs-reference-20261019.md): retired presentation path.
- [Performance measurements, 21 October](performance-optimization-20261021.md).
- [Photoshop colour proposal](propuesta-color-atardecer-psb.md): design and earlier native checks.
- [PSB writer probe](psb-writer-probe.md): feasibility experiment using an installed AEL runtime.
- [Earlier native PSB measurements](psb-validation-history.md): previous transparent, black-backed and antialiased exports.

Screenshots are illustrative captures, not an inventory of current controls. Scientific references identify sources used during development; their external URLs have not been revalidated in this documentation update.
