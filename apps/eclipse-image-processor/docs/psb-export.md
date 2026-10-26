# PSB presentation and export

The application uses independent encoded layers for fast/native preview and export. **The main TIFF and PSB have different bases.** No installed AEL runtime is required. The PSB writer adapts AEL 1.3.3 by Pere Guerra Serra under MIT and uses pinned psd-tools 1.26.0; see [attribution](../ATTRIBUTIONS.md).

## Output contracts

| Product | Base / presentation |
| --- | --- |
| Main full-resolution TIFF | Linearly normalized working base plus filter layers, no presentation stretch |
| Preview JPEG | Selected GUI view: PSB presentation when enabled, un-stretched composition otherwise; native dimensions, 8-bit, quality 95 |
| PSB or TIFF layer package | PSB presentation base plus active filter layers, independent of preview toggle |
| Hidden linear reference | Working RGB/mono scaled for 16-bit storage; scale recorded, no Asinh curve |
| Working float source and validity | Numerical working mono units, missing samples zero plus separate support |

The main TIFF is an enhanced composition, not a photometric linear master. JPEG has no additional gamma transform. PSB Exposure changes presentation preview, its JPEG and layer export, never the main TIFF.

## Automatic presentation

Preview PSB presentation starts enabled, with exposure 0 EV. Controls sit above export options and remain usable when layer export is off. Double-click Exposure restores 0 EV; no separate reset button or Display Stretch selector exists.

`core/presentation.py` estimates P99.5 from positive native luminance outside 1.2 reference-disk radii, sampled at stride `ceil(max(shape)/1024)`. RGB estimation uses weights 0.25/0.5/0.25 and follows enabled background preparation/calibration. The scale is `automatic_scale * 2**(-EV)`, with EV from −6 to +6. Empty positive sample domains fall back to scale 1. **Automatic scale selection is an application heuristic, not an AEL default.** The native scale is shared across resolutions and export.

The tone curve follows AEL 1.3.3 `ael.develop.tone_map`:

```text
u = asinh(max(RGB, 0) / scale * 10) / asinh(10)
peak = max(u across RGB channels)
shoulder = 0.9 * (1 - exp(-peak / 0.9))
mapped = u * shoulder / peak       # zero at peak = 0
```

Positive values above scale are not pre-clipped. A shared shoulder preserves the post-Asinh channel ratios. Row tiles bound float temporary storage. Mapped RGB is quantized to 16 bits; its 0.30/0.59/0.11 luminance forms Display base and a Color layer supplies RGB. This mono-base/Color architecture is application-specific, not a copy of AEL's complete workflow. Fast preview tone-maps reduced data; native verification tone-maps natively before reducing, so the latter is authoritative.

## Package and layers

Enable Also export editable Photoshop layers and select PSB (the default) or the TIFF package. The stack contains:

1. Opaque **00_BACKGROUND_Black**.
2. Hidden **Linear reference / receipt scale**.
3. Visible **Display base**.
4. Active filter layers in [fixed order](layer-composition.md), with their modes, opacity and alpha.
5. RGB Color layer when applicable.
6. Display-only **Edge Antialias** when needed.
7. Optional Photoshop-only **Color Correction** group.

The working linear reference includes enabled background correction and RGB calibration. Its positive observed maximum is divided by 0.98 to obtain the recorded storage scale. Mono is repeated into RGB when needed. Negative values clip in this 16-bit reference; it is not an untouched original or a replacement for floating input.

The TIFF package includes `01_LINEAR_REFERENCE_Normal.tif`, numbered base/filter files, `REFERENCE_COMBINED.tif` (the PSB presentation), `SOURCE_float32.tif` (working mono), `VALID.tif`, `STATISTICS_SUPPORT.tif`, `recipe.json`, `Load_layers_Photoshop.jsx` and `Layers.md`. Missing float samples store zero; VALID distinguishes missing observations from measured black. Developer-only linear-source export helpers are not exposed as a GUI option.

The PSB temporary package is removed on success or failure; a selected TIFF directory persists. Hide the black background to inspect transparency; original layer alpha remains separate.

## Optional Color Correction and profile

Add Color Correction to PSB (sRGB) starts off, appears directly below Also export, and is enabled only for PSB layer export. It adds a **Color Correction** group in Normal at byte opacity 128/255, containing a base snapshot, a Copper Gold Ivory Gradient Map (Color, 30%), Color Balance (Color, 30%) and sky Hue/Saturation (Normal, 100%). Native editable 16-bit masks separate sky/corona and exclude the lunar region; inspect them in Photoshop.

Color Balance uses midtones `(8, -2, -8)` and highlights `(4, 0, -6)` with luminosity preserved. Sky saturation reduces cyan by 10 and blue by 20. The group uses the palette in `core/color_correction.py`; the [historical design](propuesta-color-atardecer-psb.md) explains its origin.

This option embeds **sRGB** for assumed-sRGB application display RGB. Without this option, the PSB writer does not assign a new ICC profile. Neither path performs general source-ICC conversion. The group is absent from GUI preview and main TIFF/JPEG. Its cached merged RGB is the uncorrected reference and is explicitly marked as requiring native Photoshop recomposition. Third-party flattened previews may omit the correction. Rebuild the snapshot group after changing underlying filter layers.

## Verification and publication

The writer creates PSB version 2, RGB16, full-canvas layers, separate 16-bit alpha and Lr16 records; its current opaque merged RGB needs no Mt16 merged-transparency block. Recipe metadata is embedded in XMP. Reopening verifies dimensions, names, modes, visibility, byte opacity, original channel bytes, hashes when supplied, background and cached reference. Optional adjustment/profile structures are verified separately. This is structural/pixel verification, not proof of Photoshop colour-managed recomposition.

Layers are generated/verified before final TIFF/JPEG. A layer failure prevents new final images; a later image/JSON failure can leave earlier completed outputs. PSB publication uses a same-directory hard link and therefore requires filesystem hard-link support. Existing layer destinations receive numbered suffixes. Main TIFF/JSON may be replaced after the save dialog. Settings JSON is published atomically last; the overall multi-file export is not atomic.

Progress reports completed stages rather than remaining time. Filter timings overlap when prepared in parallel; PSB/package totals include nested stages. Memory and disk demands can be substantial. Files above 2 GB and the 300,000-pixel dimension limit have not been stress-tested.

## Validation boundary

Current automated tests cover writer bytes, masks, blend modes, cancellation, output separation, settings and optional adjustments. The latest full real-image check confirms the un-stretched TIFF contract and selected JPEG, without producing a PSB. Earlier exports opened successfully in Photoshop 2026, but those measurements predate the current automatic presentation and hidden reference. **The current presentation/reference combination has not been revalidated by opening it in Photoshop.** See [current validation](validation.md) and [archived native measurements](psb-validation-history.md).
