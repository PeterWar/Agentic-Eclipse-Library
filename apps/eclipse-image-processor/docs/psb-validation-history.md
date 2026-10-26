# Historical PSB validation report

> Archived 26 October 2026 from the previous PSB guide. Measurements below concern earlier implementations. In particular, TIFF/PSB equality, default values, sequential API availability and profile statements are historical. They do not describe the current presentation/reference model. See [current PSB guide](psb-export.md) and [validation limits](validation.md).

# Integrated PSB16 export

Validated 24 October 2026 with psd-tools 1.26.0 and Adobe Photoshop 2026 on macOS.

## Use

Enable **Also export editable Photoshop layers**, then select **Photoshop · PSB (16-bit layers)** (the default). Saving writes the regular final TIFF, companion JPEG and matching settings JSON plus `<destination>_PS_layers.psb`. Preview, native verification, TIFF/JPEG and PSB share the [independent layer composition](layer-composition.md). The alternative TIFF package and Photoshop JSX remain available. All active ACHF variants are exported automatically, each with its saved parameters. Excluded variants are omitted; zero-Strength variants are hidden.

The export worker snapshots the format with the other settings. Layer generation and PSB verification/publication complete before the final composition is formed from cached layers and the final TIFF/JPEG are written. A layer-export failure therefore leaves no new final TIFF/JPEG. If final-image writing subsequently fails, the completed layer output remains available. Independent cache misses are calculated concurrently before ordered layer writing. PSB preparation uses a temporary TIFF package, removed on completion or failure. The PSB is reopened and checked before publication. Existing destinations are never overwritten: the application chooses a numbered alternative. Cancellation or failed verification does not publish an incomplete PSB. Publication uses a same-directory hard link; the destination filesystem must support hard links.

## Black background

PSB export now adds a visible, opaque **00_BACKGROUND_Black** layer below all image layers. Missing-data regions appear black while the original image-layer alpha remains intact. Hide the background in Photoshop to recover transparency. The cached RGB preview is the reference composite over black, including fractional alpha. The TIFF loader also receives a black backdrop. Existing PSBs are not modified.

## Data and attribution

The writer always uses PSB version 2, 16-bit RGB, full-canvas layers and separate 16-bit alpha channels. Names, order, Normal/Multiply/Overlay/Color/Linear Light modes, visibility and byte opacity are retained. The existing layer recipe is embedded as XMP. The merged cached image is opaque RGB, composited over black. Original image-layer channels are checked byte for byte against their source TIFF; the black layer and the cached composite over black are also checked before publication. Manifest hashes are checked when supplied.

The low-level writer is copied and adapted from AEL 1.3.3, by Pere Guerra Serra, under MIT. See [attribution](../ATTRIBUTIONS.md) and [retained license](third-party/AEL-MIT.txt). No installed AEL runtime is needed by the application. psd-tools is pinned because this code uses its low-level structures.

Photoshop requires the `Mt16` merged-transparency block **before** `Lr16`. The initially tested reverse order passed structural reading but produced a native Photoshop program error. The earlier transparent export used the native ordering and positive layer count. The current opaque black-backed composite needs no merged-transparency block.

## Validation

The native real-case measurements below describe the original transparent PSB. The subsequent black-background change is covered by automated pixel, opacity, visibility, layer-order and cached-composite tests; it has not been revalidated natively on that real case.

- Synthetic fixtures: non-8-bit-aligned RGB16, fractional alpha, missing-data holes, Unicode names, hidden layers, four blend modes and quantized opacity. An independent byte parser checks compressed layer planes and merged image.
- Integration: regular TIFF/JPEG plus PSB, opaque and transparent merged images, no overwrite, cancellation, failed verification, unsafe paths and GUI export snapshots.
- Real supplied package: nine layers, 5608 × 3744, approximately 1.1 GB PSB. Generation and exact verification completed in about 35 seconds. Original files were read without modification.
- Native Photoshop: opened the real PSB, inspected the nine editable RGB16 layers and transparent hole, hid and restored the Color layer to force recomposition, then saved a separate owned copy with compatibility enabled.
- Native saved copy: alpha remained exact in all layers and merged image. RGB values changed by at most one 16-bit level per layer. Recomputed merged RGB differed from the reference by at most 13/65535 (0.020% of full scale), mean about 1.5 levels and 99th percentile five levels on opaque valid pixels. Native recomposition is therefore close, not bit-exact. The original generated PSB channels and cached reference remain exact.

Local validation artifacts are in `/tmp/eclipse-psb-real-validation`: `eclipse_9_layers_v2.psb` is the compatible generated result, `eclipse_9_layers_photoshop_recomposed.psb` is the separate native save, and `report_v2.json` / `native_compare.json` hold measurements. The earlier `eclipse_9_layers.psb` predates the block-order correction and is retained only as a failed experiment.

## Limits

Files exceeding 2 GB and the 300,000-pixel dimension limit have not been stress tested. Temporary package, compressed layer buffers, merged image and verification need substantial disk space and memory. No new ICC profile is assigned: the current layer package is untagged, and native testing chose Photoshop's “leave as is” policy. This is not a general ICC-managed color-match guarantee. Native validation covered this macOS Photoshop version, not every reader or platform.

## Upstream citation

**Credit:** Pere Guerra Serra (2026), *Agentic Eclipse Library*, version 1.3.3. The low-level 16-bit PSB writer contains code copied and adapted from AEL under the MIT license; see [full attribution](../ATTRIBUTIONS.md).

## Timing log

Console messages identify each independent `LAYER` calculation, encoding and cache reuse, final presentation, and `PSB`. The historical sequential path remains available only to compatibility API callers. Each layer reports filter calculation, display encoding, TIFF writing and reference composition separately, including direct AEL and Larson–Sekanina paths. PSB reports per-layer read/hash/encoding, cached composite/metadata, disk writing, per-layer verification, verification total and PSB total. Cached native final results are explicitly identified. Package and PSB totals include their nested stages; do not add totals to their constituent timings. The final export total also includes color preparation and temporary-file cleanup.

The current independent-layer model was also checked on a 640×427 reduction of the real master with all four ACHF variants; final TIFF and PSB cached RGB16 matched exactly. See [model validation and limits](validation.md).

## Restoring a session

A GUI export to `name.tif` also writes `name.json`. Open the JSON through **Open Image** to restore the original source and all GUI adjustments, including inactive ACHF variants and advanced controls. Source paths are relative with an absolute fallback. Source pixels and caches are not embedded; the image must still be available. The JSON is published atomically after final TIFF/JPEG writing. If JSON writing fails, previously completed image/layer outputs remain available. New filter/variant opacity controls default to 50%; restored projects use their saved values.

During export, a general progress bar advances through completed stages: preparation, filter calculation, layer-package writing, PSB writing and verification, final composition, TIFF, JPEG and settings JSON. Only applicable stages are included. The percentage measures stages completed, not elapsed or remaining time; long calculations can stay at the same stage until finished. Failures retain the reached position and display “Export failed”.

## Additional earlier independent-layer measurements

The previous layer guide recorded the following separate cases. They predate the current PSB presentation/reference model and are retained as historical evidence only.

- A 640 × 427 reduction of a real linear master with all filters and four ACHF variants produced matching TIFF/cached PSB RGB16 under the then-shared base. Photoshop 2026 opened the 13-layer PSB and saved a separate copy after toggling the Color layer. Names, modes, opacity and visibility were retained; native recomposition differed by at most 24/65535, with means about 1.6–1.7 levels and 99th percentiles of six levels per channel.
- A 200 × 200 native-pixel crop from a 2750 × 2084 source was inspected at 3× after edge antialias. Photoshop 2026 retained Edge Antialias in Normal at 100%, with native recomposition differing from that older TIFF by at most 3/65535. This did not measure whole-image native performance.
- A two-filter MGN/WOW preparation benchmark on 5608 × 3744 mono data measured 83.610 seconds serial and 51.892 seconds with two concurrent filters (1.61×), with byte-identical encoded layers. It used a 10-logical-CPU, 24 GiB machine, scaled MGN sigmas and ten native WOW scales with bilateral intensity 1. The test predates the current MGN native-unit convention and is not a current full-export benchmark.

Temporary artifact paths in old reports identify local experiment locations; they are not distributed fixtures or guaranteed to remain available.
