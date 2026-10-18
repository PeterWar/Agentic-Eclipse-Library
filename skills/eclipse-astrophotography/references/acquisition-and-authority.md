# Acquisition and authority decisions

Read this when the input cohort, geometry, HDR or a scientific claim changes. The ordinary goal is a usable photograph with explicit limits, not a new universal certification threshold.

## Per-camera contract

Record the camera/optical train, ISO, CFA/layout or RGB representation, exposure membership, temporal phase, reference epoch, canvas and coordinate convention. Preserve original metadata separately from interpreted clock corrections. A contact frame does not become totality-core evidence from morphology alone. Keep uncertain frames outside a qualified cohort until their admission is justified and authorized.

Matched calibration must match its acquisition conditions. Without matched darks/flats/bias, describe the consequence and assess whether a bounded photographic route remains useful. Do not invent calibration data. Measure this camera's clipping/linearity and overlap; a nominal default in an example recipe is not a measured ceiling.

Register on the intended coronal structure, not merely the moving Moon. An optimizer returning decimals does not certify a transform. Different optical trains need a calibrated distortion model each before they are combined; a free affine is not a substitute, and photographic acceptance cannot waive this. Within one train, changing scale or distortion also needs an optical model, not a convenient affine. Preserve complete reference-to-native-input mappings and qualify bridges between exposure products where required. Do not transfer thresholds, guards, centres or opacity choices from the three motivating camera cases.

The AEL stack recipe can directly combine declared exposures. If exposure-specific stacks are needed to assess intra-exposure drift and inter-exposure bridges, keep their geometry and resampling history explicit. This skill supplies neither an additional registration solver nor an HDR builder.

## Five roles

| Role | Question to answer |
|---|---|
| Analysis origin | Which centre/radius defines this operator and in what frame? |
| Physical lunar limb | What occulted boundary applies at this epoch, and what is uncertain? |
| Lunar exclusion | Which scientific or presentation rule removes a domain? |
| Input eligibility | Which observed contributors satisfy this product's phase, clipping and signal/support contract? |
| Output support | Where does the operator emit valid values, and where does the display merely have alpha? |

A retained output mask is not an undocumented replacement for a missing input mask. Label a proposed surrogate as a new diagnostic contract and seek approval; do not assert exact historical replay. Do not promote a diagnostic ellipse, circle fit or global visual impression to physical support.

## Routine checks versus escalation

Routine: identities, phase/cohort consistency, measured calibration/registration inputs, linearity, full-canvas geometry, observed support, compositing semantics, file verification and declared warnings.

Escalation: new radiometric certification, uncertain cross-camera distortion, physical limb attribution below a pixel, a causal optical model, absolute brightness/colour, lunar albedo/Earthshine or a new sky/extinction interpretation. State the scientific question and missing evidence. A separate scientific failure may remain unresolved alongside an accepted photograph.

Operational geometry acceptance has conditions: the failed scientific criterion remains failed; the user explicitly accepts the intended presentation use; observed-data support and other required contracts are intact; and it never covers fusing different optical trains without a distortion model for each. If any required parent has changed identity or is absent, STOP its dependent build rather than invoking the photographer's aesthetic permission.

## Existing AEL implementation

Use [DEVELOP.md](../../../docs/DEVELOP.md) and the actual version's templates. Paths in a recipe resolve relative to that recipe. Choose the full union or full reference canvas according to the case, not a crop of intersecting footprints. Coordinate conventions and exposure division occur exactly once.

Keep geometric coverage separate from usable support, clipping weights and alpha. No complete formal uncertainty budget is supplied by a weighting model. Filter inputs must match their intended scientific or declared presentation semantics; a stretched composite is not a linear master.

Read [PAPER_AND_LIBRARY.md](../../../docs/PAPER_AND_LIBRARY.md): AEL's portable filters differ from the original published image layers. Better synthetic performance is not automatic adoption for an accepted image.
