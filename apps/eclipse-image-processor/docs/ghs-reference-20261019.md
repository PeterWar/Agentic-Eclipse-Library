# Reference GHS curve and validation

> Historical report. This document preserves its original research, measurements and implementation context. Controls, defaults, sequential processing and export behaviour described below may have changed. Use the [current technical guides](README.md) and [validation boundaries](validation.md) for the active application.

The current GUI uses only PSB presentation. Display Stretch, including the GHS controls and picker, has been removed; the old numerical implementation and its tests have also been retired. This document is a historical record, not a description of the current pipeline. Settings with retired controls are no longer supported.

The former `core/ghs.py` replaced the former Asinh-based approximation with an independent implementation of the mathematical GHS curve described by David Payne and Mike Cranfield. Sources: [official process documentation, sections 3.7–3.11 and 5.2](https://www.ghsastro.co.uk/doc/tools/GeneralizedHyperbolicStretch/GeneralizedHyperbolicStretch.html) and [author's script implementation](https://github.com/mikec1485/GHS/blob/main/src/scripts/GeneralisedHyperbolicStretch/lib/GHSStretch.js). No upstream source code is copied.

## Parameters and construction

The displayed stretch factor is the reference control ln(D+1), from 0 to 20; the formula receives D = expm1(factor). It has 0.001 precision. Local intensity b ranges from −5 to 15, with 0.01 precision. SP covers [0,1]. LP lies in [0,SP], HP in [SP,1]; their slider constraints update when SP changes. All three points have 0.0005 precision. The default GHS factor is 2, b is 0, SP is 0.05, LP is 0 and HP is 1. Factor zero gives identity.

The base branches are logarithmic at b=−1, integral for other negative b, exponential at b=0, and hyperbolic for positive b (including harmonic b=1). Below SP the curve is reflected with a sign change. Below LP and above HP it follows the respective tangent. The complete curve is then normalized by its values at zero and one. Calculations use float64 with log1p/expm1 to avoid cancellation at small stretch factors and near branch limits. A shared primitive scaling cancels in the final normalization.

Black and white points are a **separate optional linear adjustment after GHS**, `(value−BP)/(WP−BP)`, clipped to [0,1]. Defaults BP=0, WP=1 preserve the GHS output exactly. BP is no longer constrained by SP: that was a property of the former approximation, not the original GHS method.

The shared presentation entry point still normalizes finite image intensities before stretching. The pure GHS function itself applies no data-dependent normalization, rejects out-of-range/invalid inputs and parameters, preserves NaN masks and leaves its input untouched. The application's existing colour composition and Reveal blend remain in use. This implements the original scalar forward GHS transformation, not the full PixInsight module, its inverse, its other transformation families or its working-space modes. Old approximation parameter values do not reproduce the same image under the corrected curve.

## Validation

All **143 unittest methods pass**, with RuntimeWarnings treated as errors. New tests compare the curve against an independent numerical integral of the published derivative, across nine b values, four stretch strengths and four protection configurations. Other checks cover closed-form logarithmic/exponential/harmonic cases, derivatives at LP/SP/HP, linear protection tails, continuity as b approaches −1 and 0, identity, endpoint normalization, the full parameter limits, missing samples and rejection of invalid inputs. GUI tests cover actual displayed units, original parameter ranges, point constraints and transitions between stretch modes. Existing tests cover shared presentation and layer/export integration.

A real-image check used `Prueba.tiff`, 2750×2084 RGB uint16, SHA256 `8438909c59b29596a8f98257a4c2f20aac87f6ace62545e2ef56d8f244191f2a`. Four b branches were inspected with the same native source, colour neutralization, stretch factor, SP and protections. The actual GUI export produced a 2750×2084 RGB uint16 TIFF and companion JPEG. TIFF pixels exactly matched the independently assembled shared presentation result; native-rendered/reduced verification preview error was zero. The original source hash remained unchanged.

Artifacts are local and ignored: `.cache/ghs-reference-20261019/tests.log`, `real_validation.json`, `real_ghs_branches.png`, `gui_ghs.png`, `reference_ghs.tiff` and its JPEG. These checks validate the implementation and export consistency; no native PixInsight render comparison or photometric validation is claimed.
