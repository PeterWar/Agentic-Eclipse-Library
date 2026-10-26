# Continuous global RHEF

RHEF offers **Legacy / compatible** and **Continuous global**. Continuous global is the prepared default; the filter itself starts inactive at opacity 20%. Both are independent Overlay layers over the shared working input. There is no Strength slider or sequential preprocessing chain.

## Continuous operator

The continuous mode estimates 257 log-intensity quantiles per radial ring, interpolates distributions between populated neighbouring radii and inverts the local distribution at each pixel. It does not blur the image. Controls include App Radius, Upsilon and Ring Width; opacity controls composition separately.

Only positive finite selected samples enter the distribution. A ring needs at least 12 samples. Statistics are not interpolated across empty rings, and absent observations are not fabricated. The rank core returns NaN where undefined; unsupported layer pixels remain transparent so the composition preserves its base there. The interior of App Radius is unaffected. Constant distributions map to 0.5; ties use quantile-interval midpoints. Quantile approximation is not identical to exact `rankdata`.

The compatible mode ranks within individual rings using its established branch conventions. It remains selectable, but is not a separate legacy application pipeline. Native/preview spatial adaptation is shared through `prepare_parameters`; resampling can change ranks and noise statistics.

## Provenance and checks

Continuous radial interpolation was studied in AEL 1.3.2 by Pere Guerra Serra; this quantile core is implemented locally without importing AEL. See [historical research](ael-filter-review.md) and [full credits](../README.md#algorithm-credits-scientific-references-and-acknowledgments).

Tests cover a scalar quantile reference, ties, constants, masks, nonpositive samples, empty/sparse rings, unit rescaling, injected structure and radial-profile controls. Shared pipeline, cache and export tests cover integration. See [current validation](validation.md); older end-to-end sequential comparisons are historical, not the active contract.
