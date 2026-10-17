# ASTROPHOTOGRAPHY: Lessons from Three Eclipse Camera Cases

## 1. Context and relation to AEL

Three separate Sony, Nikon and Canon camera datasets and processing cases from the same eclipse reached photographer-accepted editable presentations using Agentic Eclipse Library (AEL) methodology and case-specific downstream scripts. They are not independent observations of solar physics. This account adds their different stopping decisions, support failures and retained qualifications to AEL's existing field lessons. It introduces no numerical algorithm or universal processing recipe.

Measured registration, negative controls, separate lunar support and native-file checks are already part of [AEL's field lessons](FIELD_LESSONS.md). The [existing-edit case study](EXISTING_EDIT_CASE_STUDY.md) already distinguishes a filter mask from a measured edge and good disk agreement from coronal alignment. Those are prior work, not discoveries claimed here.

The historical Canon workflow used AEL 1.2.0, commit `91431acea491b1e00653db2625a56ec79202ac22`. This documentation was reviewed against [public main at 5629b37](https://github.com/PeterWar/Agentic-Eclipse-Library/tree/5629b37071ec87a32f3cf37b5ce6dfcc8b02ada1). The case-specific scripts and astronomical inputs are private; this is not a demonstration that current public AEL reproduces the three masters.

## 2. Three camera cases and acquisition characteristics

These are aggregate historical inventory and processing-cohort records, not new measurements or a release of capture metadata. Exposure membership and usable support were qualified separately for each phenomenon.

| Case | Acquisition characteristics | Accepted canvas |
| --- | --- | --- |
| Sony ILCE-7CM2 | Initial inventory of 63 distinct RAW captures; this inventory count is not the selected exposure membership of the final accepted products. A later expansion experiment was a separate branch, not automatic membership of the accepted stack. | 7028 × 4688 |
| Nikon Z 6 | 81 captures: 54 classified as totality core, 9 as contact and 18 as uncertain. Contact/uncertain captures were not automatically admitted as totality science inputs. | 6064 × 4040 |
| Canon EOS 60D | 112 captures in the inventory; the selected core used 13 captures per exposure level, 39 in total. Acquisition groups were not all qualified processing bursts. | 5202 × 3464 |

Matched dark/flat/bias calibration was not available for these cases. Camera colour, relative radiometry, background and optical-response uncertainties therefore remain explicit. No camera-to-solar-colour calibration or absolute brightness qualification follows from these presentations.

## 3. Photographic ASTRO workflow and accepted endpoints

The practical sequence was to identify the selected inputs, freeze geometry and support, preserve the linear authorities, build separately adjustable presentation layers, check the written document and obtain the photographer's decision. Changing a filter or a display curve did not silently redefine the scientific inputs.

| Case | Photographer-reported endpoint | Qualifications retained |
| --- | --- | --- |
| Sony | V4 accepted and closed; no V5 promoted. | No qualified lunar layer; interpolation, limb, inner-corona and background warnings remain. |
| Nikon | V6 accepted and closed after photographer-reported Adobe Photoshop inspection. | Measured colour/luminance, propagated presentation colour and observed detector response retain separate meanings. |
| Canon | CLEAN accepted and closed with 26 retained warnings. | Operational geometry/radiometry, invalid support, blue/violet fringe and partly unresolved limb gradient remain. |

These are photographic decisions. No complete SCIENTIFIC workflow was accepted or closed. Earlier pending-review reports describe their original stage; explicit later accepted closeouts govern current photographic status. A historical word such as “candidate” in an artifact name does not undo acceptance.

## 4. Five separate geometry/support roles

The cross-case distinction is useful because similar-looking edges had different causes. A single centre, radius or mask could not safely stand in for all five roles.

| Role | Case-specific distinction |
| --- | --- |
| Analysis origin | Sony's diagnosed analysis/lunar-centre offset was not reproduced in Canon; Nikon also kept analysis and physical lunar geometry separate. |
| Physical lunar limb | The occulting boundary depends on epoch and observed optical response. Canon's better-fitting diagnostic ellipse was not promoted to a production mask. |
| Lunar exclusion | The declared excluded region is a processing/support decision, not a new measurement of the Moon. It must not silently move with an analysis-origin change. |
| Per-input eligibility | Geometric coverage, saturation, contributor count and common colour support answer different questions. Canon's full-count eligibility rejected samples that were nevertheless finite. |
| Final output support | A finite or opaque display does not extend measured support. A retained Sony output mask could support a bounded later diagnostic, but could not recover its missing historical input-mask domain. |

The Canon limb moved relative to the coronal reference across the selected sequence. A mask fitted to the first epoch therefore did not certify pure-coronal support for all contributors. None of these distinctions supplies a centre, guard width or threshold for another camera.

## 5. Operational acceptance versus scientific qualification

Canon provides the concrete separation: a frozen inter-exposure translation was accepted by human review for presentation after automatic geometric certification had failed. Operational acceptance remained true while geometric certification remained false. The failed checks were retained; decimal precision of the transform was not an accuracy bound.

Input identity failures or genuinely missing required parents still stop the affected operation. A photographic acceptance does not authorize inventing calibration, filling unobserved pixels or relabelling a failed scientific gate. Conversely, an unresolved physical interpretation need not reopen an already accepted photographic master.

## 6. Sony negative experiment and stopping decision

A later bounded outer-corona witness measured a 1.89× reduction in a local green-channel noise proxy (paired spatial-block 95% interval, 1.80–1.96). The diagnostic window covered 0.59% of the canvas. These rounded figures describe that proxy and window; they are not a calibrated whole-image SNR gain, resolution gain or general benefit from more exposures.

Broad/coarse structure repeated across disjoint subsets, but fine-scale repeatability failed the experiment's declared criterion. The agent's common-display comparison found no useful additional photographic gain over accepted V4. That assessment was not a blinded photographer preference test. The recorded stopping decision preserved V4 without promoting V5; it does not imply that additional capture or stacking is generally unhelpful.

## 7. Nikon observed signal versus presentation semantics

The Nikon authority records distinguish measured RGB from measured green luminance where colour was unavailable, and both from propagated presentation chroma. Propagation made a presentation possible; it did not turn unavailable red/blue measurements into observed RGB.

The accepted chromosphere presentation used observed detector response with source-specific support and some mixed occulted/exterior pixel footprints. It did not qualify pure exterior chromosphere radiance or independently establish a physical chromosphere boundary from the presentation layer. The photographer's native Photoshop acceptance confirmed the practical endpoint, not that unresolved physical attribution.

A later, separate lunar feasibility experiment stopped with attribution unresolved and did not reopen V6. Broad signal inside a disk is not sufficient to isolate Earthshine from background and scattered exterior light; a black presentation disk is likewise not evidence that the RAW signal was zero.

## 8. Canon geometry, invalid support and accepted CLEAN endpoint

The earlier Canon account ended at a moderate three-layer AEL50 presentation. Its frozen controls were NRGF Multiply 50/255, bilateral WOW Overlay 47/255 and ACHF ISO04 Overlay 10/255. Earlier percentage labels were nominal; these opacity bytes identify that historical preset, not calibrated strengths or recommended defaults.

The later CLEAN endpoint was a distinct, explicitly accepted presentation, with all 16 AEL variants still editable. MGN and ISO06 were hidden together; active angular ACHF and plain WOW used Overlay at 13/255 and 8/255. This combined photographer preference did not establish each filter's individual causal contribution. The historical AEL50 product was preserved separately. The clarification extends the earlier account rather than replacing it.

The frozen HDR eligibility rule required 13 contributors separately in each green phase. Exactly 34 pixels failed that rule because of count-12 support; they remain invalid and unfilled. Finite observations under a different count rule did not qualify them under the accepted contract.

Common CFA contributors addressed one downstream colour-membership mismatch, not every chromatic defect. The retained test showed partial blue-fringe reduction and no material prominence-median improvement on shared support; one red/green edge scalar worsened. Native wavelength-dependent edge response and temporal support remained relevant. This was not a demonstrated defect in AEL's public stack implementation or a complete colour repair.

The blue/violet fringe and limb gradient remain partly unresolved. The grey disk was traced to opaque, nonzero presentation BASE amplified by display adjustments, not certified lunar illumination. Diagnostic shape fits, presentation changes and CLEAN acceptance introduced no new scientific authority. The later closeout supersedes the earlier pending-review label without claiming a newly inspected Adobe session.

## 9. Reusable practical lessons

- Record the geometry/support role before proposing a mask change: Sony's offset, Nikon's mixed footprints and Canon's changing boundary did not justify the same correction.
- Keep numerical improvement and deliverable benefit separate: Sony's local proxy improved while the proposed photographic gain remained unconvincing.
- Preserve support semantics in colour: Nikon's propagated chroma was a display aid; Canon's common-contributor change was a partial, case-specific correction.
- Keep the rejected contract visible: Canon's operational bridge and 34 invalid pixels did not become scientific passes through human preference.
- Hand over reversible presentation choices once an accepted editable endpoint exists. A later metric or software version alone is not authorization to replace it.

## 10. Validation and reproducibility limitations

| Evidence type | What this account relies on | What it does not establish |
| --- | --- | --- |
| Direct observational measurements | Historical private input/cohort records, support and native-response diagnostics, and Sony's bounded noise-proxy experiment. | Publicly reproducible astronomical measurements or a complete uncertainty budget. |
| Photographer-reported acceptance | Explicit Sony, Nikon and Canon decisions; Nikon reports native Photoshop inspection. | Independent scientific certification or a new Adobe inspection in this documentation review. |
| Agent assessments | Sony's common-display comparison and the case synthesis. | A blinded preference experiment or independent instrumentation. |
| Synthetic/software tests | Historical known-shift, mask/support and file-contract controls. | Validation of the photographed scene, all filters or physical radiance. |
| Published AEL results | Existing field lessons, existing-edit case and method documentation, credited as prior work. | Independent confirmation of public issue measurements by this case study. |
| Unresolved hypotheses | Optical/background contributions, pure chromosphere attribution and lunar illumination. | Qualified Earthshine, calibrated solar radiance or universal camera colour. |

This preparation reviewed existing documents and receipts; it performed no new RAW decoding, image measurement, scientific processing or native Photoshop test. Complete RAW-to-PSB reproduction is not established. Missing or intentionally retired historical parents, machine-specific paths and external dependencies block some reconstruction and validators. Packaging replay from retained products establishes a narrower result than rebuilding from RAW; byte identity and provenance do not restore missing parents. Some Sony retirements are individually documented; broader retention intent does not prove every Nikon/Canon deletion cause or date.

Readers cannot independently reproduce the private cohort qualifications, astronomical measurements, support counts, Sony experiment, accepted image appearance or preferences from this public text. The aggregate values are reported case evidence, not portable test fixtures. No universal filter validation or new algorithm benchmark is claimed. Complete SCIENTIFIC acceptance remains independent of all three photographic closures.

## 11. Contributor attribution and references

**Raúl Hussein (@rahusga)** is the creator and lead contributor of the contributed ASTROPHOTOGRAPHY workflow/skill and author of this case-study synthesis. Observational contributions are separate:

- **Oscar Maseda:** original Sony acquisition and private RAW dataset contribution.
- **Carlos Oltra:** original Nikon acquisition and private RAW dataset contribution.
- **Raúl Hussein:** original Canon acquisition and private RAW dataset contribution.

Observational dataset contribution does not imply skill authorship or whitepaper coauthorship. The contributors consented to public naming and their stated roles, not distribution of the underlying files.

**Pere Guerra Serra** is the original author of Agentic Eclipse Library. Original numerical-method credit remains with the authors identified in [AEL's method documentation](PAPER_AND_LIBRARY.md); no ownership of AEL, maintainer privileges or manuscript coauthorship is assigned here. This proposed documentation contribution follows the repository's [MIT licence](../LICENSE) and [contribution guide](../CONTRIBUTING.md).

No original RAW files, photographs or editable masters are distributed with this contribution.

Image derivatives, arrays, masks, exact capture metadata and private scientific evidence are also excluded. No dataset release is planned. This account stands independently of any future whitepaper and does not depend on whether the skill integration is pending or merged.

Processed with Agentic Eclipse Library by Pere Guerra — https://github.com/PeterWar/Agentic-Eclipse-Library
