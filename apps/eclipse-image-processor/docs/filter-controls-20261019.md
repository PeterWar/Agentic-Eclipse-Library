# Filter controls and implementation checks — 2026-10-19

> Historical report. This document preserves its original research, measurements and implementation context. Controls, defaults, sequential processing and export behaviour described below may have changed. Use the [current technical guides](README.md) and [validation boundaries](validation.md) for the active application.

The four adopted ideas are now implemented: a native-resolution verification preview with a reusable numerical cache; an optional continuous/support-aware FNRGF (now the GUI default); tangential detail replacing USM in the UI; and statistical exclusions separate from missing-data validity. Historical USM API recipes and the reference-compatible FNRGF core remain available for compatibility.

The implementation is independent; no source from the two reviewed upstream repositories was incorporated. Background reading and exact upstream revisions are in [the research notes](external-filter-ideas-20261019.md).

## Processing and preview

The stage order is preparation → FNRGF → MGN → WOW → RHEF → tangential detail → ACHF. Sections start disabled, with Strength 10%.

Verification mode is enabled by default. It calculates native numerical output in the Qt worker, performs presentation stretching and RGB composition at native resolution, then reduces the final presentation by area averaging. The numerical cache includes the source-array identity and a signature of all numerical parameters and array-valued masks. Recipe/source revisions reject obsolete worker results. Export reuses a matching result; presentation changes reuse numerical output. Keyboard/drag edits are debounced for rendering without starting a numerical job. Colour-neutralization errors are reported and the failed option is disabled. Export is disabled while the numerical worker is busy.

Fast mode independently processes the reduced image and is explicitly approximate. Nonlinear filters, rank populations, affine mappings and wavelet sampling can differ at that resolution. Verification does not hide this difference by changing the scientific core.

Spatial sigma/support/fade controls use preview pixels unless stated otherwise and are converted to native pixels for export/verification. FNRGF ring width is instead in pixels of each processing resolution. Tangential widths are angles; their arc length grows with radius. WOW controls now refer to native wavelet bands, including every available denoising threshold; fast mode shifts bands approximately.

## Effective control ranges

Every active enhancement has Strength 0–100%; zero is an exact bypass. All slider labels display physical parameter values directly, including fractional coefficients, actual angular segment counts and logarithmic K. Integer ticks remain an internal implementation detail. Mouse-wheel and trackpad scrolling over sliders or closed dropdowns moves the sidebar without changing parameters, including when the control has keyboard focus. Dragging and keyboard arrows still edit sliders.

| Stage | Controls and effective units/ranges |
| --- | --- |
| Pre-stretch | Asinh factor 1–100; logarithmic K 1–1000000, displayed directly with logarithmic steps. |
| Radial noise gate | Base local-contrast SNR threshold 0–5 (0 bypasses); local Gaussian sigma 0.5–20 preview px; gate smoothing sigma 0–20 preview px (0 disables smoothing). |
| Edge-preserving denoise | Gaussian sigma 0.5–20 preview px; edge sensitivity 0–1. The unused historical sigma-colour API argument is not presented as an effective control. This stage is gradient-weighted Gaussian smoothing. |
| FNRGF geometry | Inner radius 0.5–2.5 reference radii. Outer radius must exceed it by at least 0.1 and has a dynamic maximum reaching the farthest image corner, including an off-centre disk. Ring width 1–32 target-image px; linear or logarithmic spacing. |
| FNRGF angular model | Fourier order 1–24. Segments are powers of two, up to 1024, with dynamic minimum >= 2*order+1. A higher manually selected count survives order changes. Remove 0–order+1 final coefficients; STD or MAD sector spread. Separate final mean/width harmonic weights 0–1. |
| FNRGF support/continuity | Minimum sector population 1–32 (widths always need at least two samples); width floor 0–1 of typical annular spread; continuous-model radial sigma 0–64 preview px; harmonic regularization 0–1; robust reweighting 0–5 passes; boundary fade 0–128 preview px. Continuous-only controls are disabled in compatible mode. |
| FNRGF limb protection | 0–100%, within the existing triangular band 0.95–1.05 reference radii. This presentation protection is distinct from statistical exclusions. |
| MGN | Gamma 0.1–10; k 0–5; global weight h 0–1; Gaussian truncation 1–6 sigma. Six independent sigma controls, each 0.25–128 preview px, and six independent weights 0–2. Zero weight removes that scale's contribution; normalization still divides by six. |
| WOW | 0 = automatic; otherwise 1–min(10, round(log2(min(native shape)/5))) scales. Each native band has a 0–10 sigma threshold in 0.1 steps. Controls beyond the selected count are disabled and omitted from the recipe. Standard or bilateral averaging; bilateral parameter 0.1–5. WOW cannot be enabled for native dimensions below 10 px. |
| RHEF | Inner radius 0–10 reference radii; ring width 0.5–10 preview px. Lower/upper Upsilon exponents 0.01–5, linked by default; 1 is identity for that tail. Compatible or continuous-global mode. Continuous mode exposes 2–128 minimum samples and 17–1025 quantile nodes. Optional confidence threshold 0–10 (0 off). |
| Tangential detail | Angular Gaussian sigma 0.1–30 degrees; signed-detail gain 0–5; soft noise threshold 0–10 estimated sigma; inner radius 0–4 reference radii. Optional outer boundary has dynamic minimum > inner radius and maximum 20 reference radii; unchecked means full observed frame. Boundary fade 0–128 preview px. |
| ACHF | Circular support radius 1–20 preview px; signed-detail gain 0–5; intensity rejection threshold 0–100% of current input span; background retention 0–100%. Gain 0 with background 100% is identity. |
| Statistics support | Lunar exclusion enabled by default, guard 0–64 preview px. Optional bright-limb exclusion uses percentile 90–100 in annulus 1–1.1…3 reference radii; 100 excludes no bright samples. This is a brightness heuristic, not a scientific prominence classifier. |
| Final presentation | Asinh intensity 1–100; logarithmic K 1–1000000. Original GHS stretch factor ln(D+1) 0–20 (step 0.001), b −5–15 (step 0.01), SP 0–1 (step 0.0005), LP 0–SP and HP SP–1 (step 0.0005). Optional separate post-stretch linear BP −1 to below WP, WP above BP to 2 (step 0.001), default 0/1. Reveal 0–100%. See [GHS validation](ghs-reference-20261019.md). |

Default MGN sigmas are (1.25, 2.5, 5, 10, 20, 40), with equal weights. WOW thresholds default to zero. Tangential detail defaults to angular sigma 3 degrees, gain 1, no noise threshold, inner radius 1 and boundary fade 8 preview px. Continuous FNRGF defaults to smoothing 8 preview px, regularization 0.01, width floor 0.05, two robust passes and fade 8 preview px.

## Numerical behavior and boundaries

Continuous FNRGF fits populated sector means and log-widths with weighted, optionally robust regularized least squares. Regularization increases when angular coverage falls. Radial smoothing/interpolation runs within contiguous populated model ranges. The log-width model stays positive. It changes the enhancement method; it is not claimed to be byte-equivalent to the compatible core.

Tangential detail uses periodic angular Gaussian convolution normalized by observed support. Processing is tiled radially to bound memory. Only the residual is returned to the Cartesian grid; the base is retained. Tests explicitly cover non-contiguous/rotated arrays, polar periodicity, partial support and radial tile boundaries. Off-frame samples are never treated as measured pixels. Signed negative detail is retained numerically.

Missing-data validity controls NaN/alpha. Statistical exclusions instead keep finite samples in the base/output, while removing them from the filtering domain/support. The Photoshop package saves both VALID and STATISTICS_SUPPORT TIFFs, and exports tangential signed residuals as an independent Overlay layer. The common statistical mask is retained across preparation and independent branches. Missing/statistical masks select the observed-support WOW variant; that variant is not identical to watroo, and its noise thresholds remain approximate.

The RHEF confidence option attenuates the final blend toward the input rather than changing ranks. Its adjacent-pixel noise estimate can be inaccurate on correlated, stretched or spatially varying noise. It defaults off.

## Verification results

- 130 unittest methods passed with RuntimeWarning promoted to an error. Added tests include an analytic Fourier mean/log-width oracle, radial step detection with an independent-ring baseline that must fail, angular-harmonic transfer, radial nulls, 90-degree rotations, mask noninterference, slider endpoint/recipe checks, every MGN scale, native WOW band mapping, RGB preview/export equality and stale-result/cache rejection.
- The supplied 2750 × 2084 RGB uint16 TIFF was processed in 15 configurations at preview and native resolution. All principal outputs were finite and emitted no RuntimeWarning. The source and loaded buffers were unchanged, including the source SHA-256.
- The actual native background worker, RGB TIFF/JPEG export and verification rendering were exercised. A real-image Photoshop package with base, FNRGF, tangential and RGB Color layers was also reconstructed with zero uint16 error. TIFF shape and uint16 pixels matched the expected native presentation exactly. Maximum verification-preview error versus the reduced final RGB presentation was 1.03e-7 on a 0–1 scale (rounding in float32 area reduction).
- On this image, the continuous FNRGF removes the conspicuous large concentric bands seen in the compatible-mode diagnostic. The fixed-scale montage still shows substantial noise amplification at 100% Strength; this is not a recommended finishing preset or a claim of artifact-free science.
- Fast-versus-native RMSE remains nonzero by design. The new verification view resolves presentation consistency by showing the actual native calculation, rather than making an unverified claim that WOW now commutes with resampling.

Local run artifacts, numerical TIFFs, recipes, logs and GUI screenshots are in the ignored `.cache/filter-upgrade-20261019/` directory. The final numerical run is `final-validation/`; the before/after image is `fnrgf_comparison.png`. The full automated/real-image runner is `scripts/validate_real_image.py`.

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -W error::RuntimeWarning -m unittest discover -s tests -v
QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/validate_real_image.py /path/to/Prueba.tiff /path/to/new-output-directory
```

No RAWs were re-stacked, and no HDR merging stage was added to this single-master enhancement application. The earlier HDR-fusion research item remains a separate input-stage project. Native Photoshop rendering and photometric/scientific validity still require independent checks.

### Physical values and sidebar scrolling

The updated interface passes all 134 unittest cases, including endpoint display checks for every factory slider, direct logarithmic K, power-of-two segment counts, GHS symmetry-point precision, wheel routing with and without focus, dropdown protection and keyboard editing. An offscreen GUI screenshot was also inspected. Verification log: `.cache/slider-controls-20261019/tests.log`. Numerical filter algorithms and parameter steps are unchanged by this interface update.
