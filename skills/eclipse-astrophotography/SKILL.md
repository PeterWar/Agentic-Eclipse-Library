---
name: eclipse-astrophotography
description: Guide an explicit ASTRO or eclipse astrophotography case workflow, operational-versus-scientific qualification, editable-master acceptance and closeout. Use existing AEL skills for a single calibration, filter or diagnosis task; use eclipse-first-steps when the goal is unspecified.
---

# Eclipse astrophotography

Deliver an editable photograph with an honest case record. This is a workflow skill built on Agentic Eclipse Library (AEL), not another numerical engine. Respond in the photographer's language.

Use the already stated goal and authorizations. Approval may cover a bounded group of stages; do not ask again for that same scope. Ask at a material change of inputs, geometry, scientific claim or photographic version. A design/review request authorizes no processing.

Processing approval is not publication permission. Do not add publication or submission to the case plan unless the user requests it. Before any upload, public issue/PR or publication, show the exact text/files, destination and attribution and obtain explicit permission for that material and destination. Existing exact publication approval remains valid within its scope; otherwise keep drafts local and STOP the publication branch. This applies at every stage, including scientific escalation and closeout.

## Enter at the right point

- For an unclear goal or a first look at eclipse photos, route to [AEL first steps](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/8ade9c7d04f7ef46191ec71c6aa1a9dc50004fd0/skills/eclipse-first-steps/SKILL.md).
- Keep a single-stage request with its existing specialist. In the Codex plugin use `eclipse-calibration-stacking`, `corona-filter-layers` or `eclipse-artefact-diagnosis`; in a source checkout the corresponding skills are `apilatge-imatges-eclipsi`, `postprocessat-corona` and `corregeix-artefactes`. Read their actual local entrypoints when present. This skill coordinates case decisions across stages; it does not replace those procedures.
- For Earthshine, absolute brightness or another physical claim, identify the required evidence and limits first. Route supported sky/extinction and coronagraph comparisons to AEL's existing documentation and `coronagraph-comparison`; that skill is not an Earthshine certification method. Do not run a physical investigation under photographic approval.
- For a preferred existing edit, establish whether the user wants detail recomputed on that edit or separately aligned existing layers. Read the [existing-edit case](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/8ade9c7d04f7ef46191ec71c6aa1a9dc50004fd0/docs/EXISTING_EDIT_CASE_STUDY.md). Do not call a finished RGB image linear RAW data.
- For an already accepted master, preserve its identity and closeout. A new library release or better local metric does not authorize another version or reopen acceptance.
- Use the supplied case's acquisition contract. Read [acquisition and authority decisions](references/acquisition-and-authority.md) when eligibility, scientific versus operational geometry or exposure fusion is at issue. Read [examples and receipt fields](references/examples-and-receipts.md) for a concrete handoff.

## Decision workflow

Enter at the earliest unverified dependency, retaining prior accepted stages.

| Stage | Routine operational check and next action | Material human checkpoint |
|---|---|---|
| 1. Goal and inventory | Identify selected inputs, target phenomenon, camera/optical train, existing edits and desired editable endpoint | Agree scope when not already explicit |
| 2. Integrity and phase | Record identities; curate totality/contact/uncertain phases; keep original and interpreted times separate | Approve a changed cohort or unresolved phase admission |
| 3. Calibration and linearity | Use matched calibration if available; measure usable response and clipping for this camera; declare missing calibration | Agree proceeding with stated limits; do not fabricate flats or transfer another camera's ceiling |
| 4. Registration and exposure stacks | Qualify registration on the intended scene; preserve full reference canvas and measured reference-to-input mapping | Approve geometry/canvas; failed certification is retained, even if explicitly accepted for bounded presentation |
| 5. Operational HDR | Use a declared AEL stack recipe; retain eligibility, coverage, weights and radiometric/extrapolation limits | Agree any material combination or relative-radiometry assumption |
| 6. Base and colour | Separate observed RGB, measured luminance, propagated presentation chroma and display stretch | Let the photographer select a usable base; a neutral display is not measured colour |
| 7. Editable AEL layers | Use a qualified linear parent/support with existing AEL filters; keep RGB/alpha, modes and opacity independent | Review requested layer choices; known filter limitations remain visible |
| 8. Master and verification | New full-canvas editable file; reopen and check actual channels/metadata/cache; inspect limb, edges and overview | Record actual native Photoshop review if performed; do not infer it from a software PASS |
| 9. Decision and closeout | Accept, reject or STOP; bind outcome to artifact identity and retain warnings, failures, dependencies and reproduction limits | Photographer makes final photographic decision; no automatic scientific closure |

Use AEL 1.3.2 as the reference for this skill; record the actual source version and environment before an authorized run. [Declared stack/filter recipes](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/8ade9c7d04f7ef46191ec71c6aa1a9dc50004fd0/docs/DEVELOP.md) execute measured inputs; they do not estimate registration, infer calibration or discover a reliable HDR recipe automatically. A supported stack can combine the declared exposure ladder; per-exposure stacks are a diagnostic/qualification route when the acquisition contract requires them, not a compulsory extra resampling.

In a source installation, the existing commands are ael stack and ael filters; the relevant functions are ael.stack.stack_from_config and ael.develop.filters_from_config. In a plugin, read `../../docs/USAGE.md` relative to this skill's directory and use that package's bundled launcher instead of assuming the shell working directory or another installed AEL. In a source checkout use the source installation instructions if that plugin-local guide is absent. Read exact help/schema before constructing a recipe. Do not install or upgrade without authorization.

## Boundaries that change the decision

Keep RAWs, manual edits and accepted masters immutable; write derived outputs to new destinations. Invalid or missing observations remain invalid, never mirrored, generated or silently filled. Keep five roles explicit: analysis origin, physical lunar limb, lunar exclusion, input eligibility and output support. A finite filter result or opaque display is not new observational authority.

Stop the affected branch for missing/changed required identities, unsupported input semantics, unresolved required geometry, invalid support or a failed file contract. Preserve unrelated accepted domains. A photographer may accept operational geometry after scientific certification fails only within an explicit presentation scope with usable observed support; this never bypasses corruption, identity failures or missing inputs.

Escalate only the question requiring new physical evidence: distortion, uncertain phase, causal artifact correction, lunar attribution, calibrated brightness/colour or extinction. Define its evidence and controls before a separately authorized investigation. Do not force every photograph through a complete scientific research programme.

For artifacts, route to [AEL diagnosis](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/8ade9c7d04f7ef46191ec71c6aa1a9dc50004fd0/skills/corregeix-artefactes/SKILL.md). ACHF/WOW boundary bands and bilateral WOW sign inversion remain [documented limits](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/8ade9c7d04f7ef46191ec71c6aa1a9dc50004fd0/docs/FIELD_LESSONS.md); do not cure them by hiding the evidence.

Retain a negative result when a measured local improvement yields no demonstrated useful photographic gain. Distinguish agent assessment from photographer judgement. Close photographic, scientific, lunar, reproduction and conservation dimensions separately; never infer complete SCIENTIFIC acceptance, Earthshine or RAW-to-final replay from an accepted Photoshop file.

Built on Agentic Eclipse Library by Pere Guerra Serra and its credited method authors. General gates, numerical algorithms and human review are prior AEL work.

ASTROPHOTOGRAPHY workflow and skill, developed from three camera case studies and built on Agentic Eclipse Library.

Raúl Hussein ([@rahusga](https://github.com/rahusga)) is the creator and lead contributor of the proposed `eclipse-astrophotography` workflow/skill. Observational acquisition and private RAW dataset contributors are credited separately in the repository README. Dataset contribution does not imply skill authorship or manuscript coauthorship.

No original RAW files, photographs or editable masters are distributed with this contribution.

Pere Guerra Serra is the original author of Agentic Eclipse Library. Credit the original numerical methods according to [AEL's method documentation](https://github.com/PeterWar/Agentic-Eclipse-Library/blob/8ade9c7d04f7ef46191ec71c6aa1a9dc50004fd0/docs/PAPER_AND_LIBRARY.md). This contribution assigns no ownership of AEL, maintainer privilege or manuscript coauthorship.
