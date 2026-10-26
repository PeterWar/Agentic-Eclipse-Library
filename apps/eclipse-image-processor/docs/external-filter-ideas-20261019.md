# Ideas from EclipseForgeHDR and Eclipse_HDR

> Historical report. This document preserves its original research, measurements and implementation context. Controls, defaults, sequential processing and export behaviour described below may have changed. Use the [current technical guides](README.md) and [validation boundaries](validation.md) for the active application.

Later implementation and updated validation: [filter controls and implementation checks](filter-controls-20261019.md). This document records the preceding review.
Reviewed on 2026-10-19 against the local findings in [the filter validation report](filter-validation-20261019.md). This is a source review and a proposed experiment plan. No upstream software was executed and no filter behavior was changed by this review.

## Reviewed revisions

- EclipseForgeHDR: `8d68626077bff056c8b8773a210b0226325b8699`. Reviewed `detail.py`, `render.py`, relevant changelog entries and LICENSE.
- Eclipse_HDR: `1d5b9b10ce0320ad7a331fab65763d50fd3827c0`. Reviewed `Corona_v1.1.py`, the original `Corona.py`, relevant `FusionHDR_v1.2.py` sections and LICENSE.

Exact source snapshots and GitHub tree manifests are stored locally under the ignored `.cache/repository-review-20261019/` directory. The two repositories' current `main` branches can change independently of this report.

## First priority: make the preview represent the export

EclipseForgeHDR caches full-resolution layers and derives previews with area averaging. Its renderer also addresses the fact that shrinking a detail layer changes its amplitude relative to a noise threshold. See [`render.py`, `_decim` and `Layers`](https://github.com/naugustin77/EclipseForgeHDR/blob/8d68626077bff056c8b8773a210b0226325b8699/src/eclipseforgehdr/render.py#L304).

Our pipeline is shared, but currently runs nonlinear filters independently on the reduced and full inputs. Shared code cannot make those operations commute with resizing. This matters for the measured standard-WOW discrepancy.

Proposed experiment: offer a full-resolution verification preview that renders the actual full-resolution numerical result and then reduces the final presentation. Cache it by source identity, mask, geometry, filter parameters and implementation version. A fast, independently filtered preview can remain available while computing it.

Compare three products separately: filter core output, the affine intensity mapping, and the final presentation. This will help locate WOW's discrepancy rather than assuming all of it comes from wavelet-scale rounding. Reusing full-resolution layers alone does not guarantee identical previews when subsequent nonlinear transforms run at different resolutions.

Acceptance: the verification preview must match an area reduction of the exported presentation before TIFF/JPEG quantization. Tests must include denoising, partial Strength and display stretching. This addresses consistency; it does not certify the filter's scientific correctness.

## Second priority: continuous FNRGF models with measured support

EclipseForgeHDR's `fnrgf_robust` uses robust fitting, coverage-dependent model complexity, damping, radial smoothing of the mean/width fields and interpolated evaluation. Its `fourier_background` uses continuous regularization as coverage falls. These are related but distinct implementations; the former still changes order discretely. See [`detail.py`](https://github.com/naugustin77/EclipseForgeHDR/blob/8d68626077bff056c8b8773a210b0226325b8699/src/eclipseforgehdr/detail.py#L1344).

Eclipse_HDR smooths its Fourier coefficient profiles along radius and imposes a noise floor on the reconstructed width. Its variance comes from Fourier models of intensity and intensity squared, followed by percentile presentation mapping. This differs from our sector-width/reference convention. See [`Corona_v1.1.py`, `fnrgf`](https://github.com/LaurentVoillot/Eclipse_HDR/blob/1d5b9b10ce0320ad7a331fab65763d50fd3827c0/scripts/Corona_v1.1.py#L370).

Our candidate should be an explicit experimental variant. Fit only observed support, record coverage/conditioning, regularize unstable harmonics and connect adjacent radial models. Smooth/interpolate the background statistics, not the final enhanced image. Preserve the current reference-compatible core for comparison.

Acceptance: test a smooth radial null, injected angular detail, genuine circular features, a bright compact source, partial annuli and a slightly wrong center. Measure unwanted ring jumps, signal recovery and corner behavior together. A lower ring metric alone could reward erasing real circular structures. A noise floor must state its units and assumptions; values from another dataset should not become universal defaults.

## Third priority: tangential detail as a separate method

Eclipse_HDR's `tangential_detail` subtracts an angular blur in polar coordinates, thresholds the residual, resamples only that residual back to Cartesian coordinates and adds it to the untouched base. See [the function](https://github.com/LaurentVoillot/Eclipse_HDR/blob/1d5b9b10ce0320ad7a331fab65763d50fd3827c0/scripts/Corona_v1.1.py#L434).

This is a useful additional detail method, distinct from our symmetric adaptive circular ACHF. Give it a separate name and controls. Require an observed-support mask, periodic angular boundaries and support-aware handling at frame edges. The upstream nearest-edge sampling is not a reason to treat samples outside our frame as observations.

Acceptance: a radial null should yield negligible angular detail; injected streamers should keep their orientation; no seam may appear at 0/360 degrees. Test noise amplification and geometry errors. An angular width has a radius-dependent footprint in image pixels, which must be explained in the control units.

## Masks and noise confidence

Both approaches suggest separating samples used to estimate a background from pixels retained in the output. An optional user-visible lunar/prominence exclusion can prevent bright structures from controlling surrounding statistics without deleting them from the source. Keep this separate from the missing-data mask. Our current masks already exclude missing samples; finite lunar pixels are still observations.

Eclipse_HDR's RHEF gates ring contrast using measured spread relative to an estimated noise level. This is worth testing as an optional presentation weight, with correlated-noise and weak-signal controls. It is not a calibrated detector model, and angular brightness variation is not automatically signal rather than noise. Do not change the ranking core silently.

## HDR ideas for a later input stage

`FusionHDR_v1.2.py` combines exposure-normalized inputs using saturation masks expanded by a margin and feathered by distance. It tracks lunar geometry per exposure so a moving dark disk does not override exposed coronal pixels. See [the merge code](https://github.com/LaurentVoillot/Eclipse_HDR/blob/1d5b9b10ce0320ad7a331fab65763d50fd3827c0/scripts/FusionHDR_v1.2.py#L681).

These ideas are relevant if this application later accepts bracketed exposures. They cannot recover clipped signal or prove exposure linearity from the single supplied TIFF. Keep HDR fusion, numerical enhancement and presentation as separate stages.

## Adoption boundaries and proposed order

EclipseForgeHDR's [LICENSE](https://github.com/naugustin77/EclipseForgeHDR/blob/8d68626077bff056c8b8773a210b0226325b8699/LICENSE) permits personal execution/modification but does not grant redistribution or bundling into another product. Eclipse_HDR declares [GPL-3.0-or-later](https://github.com/LaurentVoillot/Eclipse_HDR/blob/1d5b9b10ce0320ad7a331fab65763d50fd3827c0/README.md#licence). This review imported no source code into the application. Use these as research leads and return to the cited scientific methods for an independent implementation; copying would require resolving the applicable terms.

Recommended order: full-resolution verification preview; experimental continuous/support-aware FNRGF; optional tangential detail; explicit statistics masks and measured noise confidence. HDR fusion is a separate future feature. Nothing in this review proves either upstream implementation is universally correct or resolves our measured WOW discrepancy by itself.
