# AEL ACHF variants

The bundled port in `core/ael_achf.py` copies/adapts Agentic Eclipse Library 1.3.3, by Pere Guerra Serra, under MIT. See [attribution](../ATTRIBUTIONS.md) and the [retained notice](third-party/AEL-MIT.txt). No installed AEL package is required at runtime.

## Operators

ISO 01 and ISO 04 use positive observed log-luminance. They remove a cubic-spline radial profile fitted to annular log-intensity medians in log radius, average five Gaussian high-pass residuals and apply outer Gaussian smoothing.

| Variant | Native Gaussian sigmas | Outer sigma | Initial inclusion / opacity |
| --- | --- | --- | --- |
| ISO 01 | 2, 4, 8, 16, 32 px | 3 px | Off / 10% |
| ISO 04 | 1, 2, 4, 8, 16 px | 1.5 px | On / 10% |
| Angular | 1° angular Gaussian | 4 px | On / 10% |

Angular subtracts an angular Gaussian in log-luminance on a linear polar grid, maps detail back with complete bilinear observed support, and smooths in Cartesian space. Polar rows are tiled. The encoding is `0.5 + 0.5*tanh(detail/(2.5*scale))`, with upstream MAD floor 1e-5 and no median subtraction. Observed-support Gaussian approximations follow upstream. Nonpositive samples do not enter the logarithm; missing data are not filled. Insufficient radial-profile support raises an explicit error.

## GUI and composition

All variants start from the shared working mono input, not a preceding enhancement or a tone-mapped image. Native-pixel widths scale down for fast preview; angular widths stay in degrees. Reduced annular statistics are approximate.

The editing selector initially shows ISO 04. Each variant has independent parameters, opacity and Include state; the ACHF master Active checkbox gates them together. ISO 04 and Angular start included at internal strength 100 and opacity 10%. There are no per-variant Strength sliders. Adaptive is a separate application implementation, initially excluded at opacity 19%. An Angular 8 variant is not exposed.

Encoded AEL layers use Overlay unchanged by adaptive ACHF's Background Retention or the application's other neutral-detail normalizers. Export writes active variants only. Main TIFF and PSB share filter layers but use different base presentations; see [composition](layer-composition.md) and [PSB export](psb-export.md).

The numerical blend helper can return results in input units for developer use; the GUI uses encoded independent layers. Recipes retain variant, widths, target scale, spline diagnostics and display scale.

## Evidence and limits

Frozen AEL 1.3.3 fixtures cover ISO 01, ISO 04 and Angular, with finite-pixel agreement within absolute 1e-7. See [fixture provenance](../tests/fixtures/ael_achf_iso04.md). Tests also cover support contamination, nonpositive/sparse/constant inputs, geometry, scaling, inclusion, encoding and exported alpha. Current suite results are in [validation](validation.md).

Partial radial coverage and the lunar boundary can bias the profile and produce bands. A protective geometry circle need not be a physical solar-radius measurement. These filters are visualization operators, not calibrated photometric products.
