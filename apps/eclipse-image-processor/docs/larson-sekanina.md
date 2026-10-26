# Larson–Sekanina rotational detail

Larson–Sekanina sits between Tangential Detail and ACHF. Initially off, it has **Gain 25%**, **Opacity 75%** and **Angular increment 3°**. Gain ranges from 0 to 200%. The GUI fixes radial increment at zero in preview and export and exposes no radial slider.

## Numerical operator

```text
D(r, theta) = 2 I(r, theta)
              - I(r-dr, theta-da) - I(r-dr, theta+da)
```

The application uses `dr = 0`: symmetric angular differences around the reference centre. The numerical helper still accepts an inward radial offset for developer experiments. Angles do not scale with resolution. Bilinear sampling operates directly on Cartesian input in cancellable row tiles.

Only targets outside the reference lunar disk with both interpolation footprints fully observed and outside the disk receive detail. Statistical exclusions also restrict sampling when enabled. Unsupported targets retain their numerical input; missing data remain missing. Both increments zero give zero residual. The direct numerical helper returns `I + strength/100 * D` without clipping or normalization; this helper return is not the GUI composition contract.

## Layer encoding

The independent branch computes signed detail from the shared working input. It encodes `L = 0.5 + D/(2*S)`, where S is the larger of the observed working-input range and maximum absolute supported residual. The receipt records this scale. Gain scales the displacement from neutral grey before quantization/clipping; it is distinct from opacity.

With Linear Light and Fill 100%, the display blend is `clip(base + 2*L - 1, 0, 1)`. Layer opacity and alpha then mix that clipped result with the base. Consequently Gain above 100% is useful but can clip detail; opacity cannot undo all effects of that clipping. The layer is RGB16 with unassociated alpha, and opacity is quantized to 1/255. Neutral 0.5 quantizes to 32768/65535, leaving a small rounding offset. There is no global Reveal multiplier.

Main TIFF uses an un-stretched normalized base; PSB uses its presentation base. Neither is an exact reconstruction of the direct numerical helper. See [composition](layer-composition.md), [export](psb-export.md) and [validation](validation.md).

Small angles, incorrect centres and bright edges can create misleading residuals. This application implements the symmetric operator for corona visualization, without claiming PixInsight-specific extensions.

References: [Larson and Sekanina (1984)](https://doi.org/10.1086/113551); [Vincent, section 2.2.2.1](https://www2.mps.mpg.de/solar-system-school/alumni/vincent.pdf); [Adobe blend-mode descriptions](https://helpx.adobe.com/photoshop/desktop/repair-retouch/adjust-light-tone/blending-mode-descriptions.html).
