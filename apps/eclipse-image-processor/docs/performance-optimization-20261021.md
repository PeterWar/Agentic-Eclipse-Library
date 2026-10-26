# CPU optimization integration — 2026-10-21

> Historical report. This document preserves its original research, measurements and implementation context. Controls, defaults, sequential processing and export behaviour described below may have changed. Use the [current technical guides](README.md) and [validation boundaries](validation.md) for the active application.

The active calculation paths now include the optimizations validated against a
snapshot of the previous implementation. No new dependencies were added.

## Changes

- **MGN:** independent scales run on at most four helper threads. Small images
  remain serial. An approximate scratch-memory budget lowers concurrency on
  larger images. Reduction retains the original scale order. Each task receives
  its own copy of the caller's cancellation context. Masked MGN computes the
  Gaussian support once per scale and reuses it for both signal convolutions.
- **Masked WOW:** dilated nonbilateral B3-spline convolutions use their five
  nonzero coefficients per axis for steps >= 8. Smaller steps keep SciPy's
  direct convolution. Half-sample reflection and double accumulation followed
  by rounding once per axis preserve the original dtype behavior. The bilateral
  signal filter is unchanged; its nonbilateral power filter benefits too.
- **Tangential:** wide angular kernels use a periodic FFT convolution. The
  kernel is the same finite Gaussian with truncate=3, not an ideal spectral
  Gaussian. Its transform is reused for signal/support; narrow kernels retain
  the direct filter. FFT workers are capped at four.
- **Continuous FNRGF:** radial interpolation indices/weights and angular bases
  are shared by mean and log-width models, in blocks of 32768 pixels. MAD,
  robust fitting, width floors, gap rules and coefficient summation order remain.
- **Larson–Sekanina:** a rotation matrix avoids per-pixel inverse trigonometry
  while retaining the inward radial shift, bilinear sampling and support rules.
- **Presentation:** Reveal=0/1 evaluates only the selected image branch.
- **Export:** `core/export.py` owns calculation and TIFF/JPEG/package writing.
  `gui/export_worker.py` executes it on a QThread from a settings/source snapshot.
  Native cached results remain reusable. Sidebar editing is disabled during
  export; closing the window waits for writing to finish. Exceptions return a
  visible error and restore the controls. Numerical preview scheduling is paused
  during export. The numerical log now says CPUs *available*, not CPUs used.

## Automated validation

167 unittest cases pass, including new checks for:

- sparse/dense starlet agreement in float32/float64, reflection, holes and kernels
  wider than the image;
- bit-identical serial/parallel MGN reduction, with and without a mask;
- cancellation propagated into masked and unmasked MGN helper threads;
- direct/FFT angular agreement for narrow/wide kernels, constants, subpixel
  centers and missing-data regions;
- export thread responsiveness, snapshot isolation, error handling and control
  restoration;
- existing independent numerical oracles, masked pipeline, TIFF/JPEG output,
  Photoshop layers and preview/export consistency.

## Real-image comparison

Input: the user's `Prueba.tiff`, RGB uint16, 2750 × 2084. Preview: 1500 × 1136.
Each filter was compared with the pre-change snapshot using the same parameters,
with lunar statistical exclusion. Full-size results from a paired run:

| Calculation | Before (s) | Integrated (s) | Speedup |
|---|---:|---:|---:|
| FNRGF continuous | 1.909 | 1.625 | 1.17× |
| MGN | 7.008 | 3.704 | 1.89× |
| WOW standard, masked | 18.978 | 1.671 | 11.36× |
| WOW edge-aware, masked | 16.941 | 8.009 | 2.12× |
| Tangential | 4.673 | 1.132 | 4.13× |
| Larson–Sekanina | 0.528 | 0.468 | 1.13× |
| Seven-filter sequential chain, 10% strengths | 33.479 | 17.592 | 1.90× |

These are illustrative paired timings, not guaranteed speedups or independent
benchmark medians. Small unit-test runs overlapped part of the comparison.
All compared preview results were bit-identical. At full size, Tangential alone
had maximum absolute difference 1.52587890625e-5 in input units and RMSE
6.373894416999934e-9. Other full-size cases, including the complete chain, were
bit-identical on this input. This does not imply bit identity for every possible
input or platform.

The actual GUI export was also exercised with all seven filters, native cache,
color calibration, Photoshop layers and source export enabled. The output was a
2750 × 2084 RGB uint16 TIFF, matching the expected presentation pixel for pixel,
plus JPEG, nine Photoshop layers (including the Linear Light Larson–Sekanina
layer and Color layer) and float32 source products. An event-loop timer fired
459 times during the approximately 23-second export. The original file hash
was unchanged. Results and measurements are in
`/tmp/eclipse-optimization-validation/` on the validation machine.

## Limits

No GPU backend, unbounded parallel branch export, ACHF kernel replacement,
persistent intermediate-image cache or asynchronous native display rendering
was introduced. These were audit proposals without an accepted implementation
and broader performance/correctness evidence. Windows/Linux and a rebuilt
standalone application have not been validated in this change. Memory budgeting
for MGN bounds task concurrency; it is not a hard process RSS limit.
