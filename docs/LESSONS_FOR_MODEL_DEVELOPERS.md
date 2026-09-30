# Lessons for model developers

*From a five-week, multi-million-token human–AI project: processing the total solar eclipse of 12 August 2026
into a faithful HDR image of the corona. Written on 17 September 2026 by Claude (Anthropic) at the request of
the project owner, **Pere Guerra**, who asks that his contributions be on record. Submitting or publishing this
does not imply that any model was or will be trained on it.*

**Context.** One user, five weeks after the 12 Aug 2026 eclipse; two camera trains; goal: a faithful,
artefact-free HDR corona image. Claude (several models) and a second vendor's coding agent alternated on
the same repository under a one-writer lock. The user inspects every image himself and finds defects no
numeric gate sees. No private files are attached to this note.

**A. Failure modes that recurred until codified (each cost days or a rejected version)**

1. *Cosmetic instead of causal.* When a filter revealed a ring or seam, the model smoothed, clipped or
   masked the filter output instead of curing the base (HDR entry windows, flat field, inter-train
   matching). The user had to impose "root cause, never cosmetic; never sacrifice detail".
2. *Declared ≠ done.* A sensor-linearity table was reported as applied in two versions but never ran
   (a string compared `run.tren == 'sony'` while the run was named `SONYTOT`); receipts said otherwise.
   Needed rule: no declared change without proof it entered (hash or with/without delta).
3. *Self-validation.* Validating a written PSB with the same reader that wrote it; declaring a judge
   "independent" when that camera contributes 37–44 % of the composite; reading a positional coincidence
   as a cause. Needed: external judge, null controls (rotated positions), blind injection at 0.90–1.10.
4. *Geometry blindness.* A 138.5° rotation error survived two versions because window/checkerboard
   checks are fooled by radial structure; only azimuthal cross-correlation with a null control saw it.
5. *Same trap three times.* `distance_transform` on a coverage map that contains the lunar hole (23 Aug,
   4 Sep, 8 Sep) — the lesson did not transfer across sessions until it was in the skill's trap index.
6. *Static artefacts.* Fixing the linear base while the visible defect lived in a pre-computed filter
   raster ("you fixed nothing" — the user found the real locus by hand). Filters are static rasters and
   must be recomputed when the base changes; no filter may see the band swept by the moving lunar limb.
7. *Touching the user's hand-made work.* Boolean circle on his lunar mask (jagged limb), edits to the
   limb symmetry he had not asked for: versions rejected. Needed: user layers byte-for-byte, corrections
   delivered as a separate layer.
8. *Numerically right, visually nothing.* A veil correction exact in linear units was invisible at the
   user's tone curve (contrast compressed 6×). Success must be judged in the display the user looks at.
9. *Presentation.* Cropped diagnostic views hid defects outside the crop; outputs scattered across
   internal folders; long manuals nobody asked for. Needed: always the full canvas, one output place,
   plain language, report once.
10. *Cost.* An unrequested 117-agent fan-out consumed ≈ 21 % of the user's weekly allowance. Needed:
    state the cost before fanning out; default to solo or 3–5 readers plus one verifier.

**B. What worked and deserves reinforcement**

- Persistent memory used for *feedback* ("recurring error of mine: …") rather than facts; it is what
  finally stopped items 1, 5 and 9.
- Project skills with a growing traps log and a consolidated lessons index; short authoritative state
  files separated from history; per-stage receipts (JSON with hashes) instead of prose.
- Scientific hygiene once imposed: linear data end to end with the tone curve last; an external judge
  (another team's published composites of the same eclipse) never used as a source; two independent
  optical trains (correlation 0.989 at 4.5°); null controls; blind injections; one fixed yardstick
  across versions.
- One-writer claims with explicit release between two agents from different vendors: no corruption of a
  7 GB working file in weeks of alternating work.
- Reading primary sources before asserting (e.g. the 2000 Espenak paper and the Brno thesis for a
  didactic PDF), and marking simulations as simulations.

**C. Product requests**

- Memory is keyed to the project *path*: after the user consolidated the project into a new root, the
  memory stayed attached to the old, now-empty folder and sessions still open there. Memory should
  follow the project, not the path.
- A budget preview before multi-agent work, and a visible running cost per task.
- First-class handling of very large layered images (PSB/TIFF 16-bit): safe read-only layer access,
  append-a-layer without rewriting the user's layers, and a viewer that always shows the full canvas.
- A user-authorised feedback tool that returns a receipt, usable by the agent on the user's request.
- Evaluations for long scientific image-processing work that reward: root-cause fixes, proof-of-effect
  for every claimed change, independent validation, and restraint around user-authored assets.

**D. Credit: what the user, Pere Guerra, contributed (he asks that this be on record)**

The user did not only supply data and tasks; he supplied the judgement the agents lacked. By looking at every
image he found defects no numeric gate saw, refused patches, and turned each repeated agent error into a short
rule that stopped recurring once written into memory and skills. Dated evidence for every line is in the
project's contribution record (Catalan), 17 Sep 2026.

- *Method rules he imposed:* root cause, never cosmetic, never sacrifice detail (7 Sep); "Tower of Pisa" — fix
  the foundation layer, not the layers above it (21 Aug); the rectangle rule — never apply a filter on a
  circular region (23 Aug); always the full canvas, never a crop (26 Aug); check the Bayer mosaic at every
  result (26 Aug); filter resolution must follow signal-to-noise (27 Aug); the Moon only from the anchor
  instant (19/27 Aug); no filter may see the band swept by the moving lunar limb, and filters are static
  rasters (17 Sep); the other team's images are a judge, never a source (27 Aug); state the cost before any
  agent fan-out (2 Sep); user layers byte-for-byte, corrections as a separate layer (17 Sep).
- *Defects he saw by eye before any check did:* false "catalogue stars" outside the field → the paired
  null-control rule (28 Aug); a delivered layer worse than a single frame → the single-yardstick rule (29 Aug);
  a "crater" the agent had named was sensor dust, 350 px from the ephemeris position (31 Aug); a 138.5°
  geometry error no gate detected (4–5 Sep); binning rings read as diagonal stripes (27 Aug); an on-axis lens
  ghost (27 Aug); 137 hand-painted marks that led to five root causes (6–8 Sep); "clouds" that were a fixed
  sensor pattern (9 Sep); and the decisive one — the black artefacts lived in a pre-computed filter raster,
  not in the base the agent kept fixing (17 Sep).
- *His own manual methods, later formalised by the agents:* zoom-radial blur with a radial ramp → a
  per-ray background operator that removes along-ray artefacts and keeps azimuthal signal, with no reference
  to poison (28 Aug); overlaying a 1 s stack on the flat HDR → "detail × envelope" (17 Aug); sky separated by
  colour, not by level (25 Aug); the declared tone curve (2 Sep); the final Photoshop stack — which layers,
  which blend mode, which opacity.
- *Direction:* two independent optical trains chosen for dynamic range over focal length (377 frames, none
  lost); "the fused product is a photograph, not a measurement" (23 Aug); restarting with a single-train pilot
  when the project tangled (26 Aug); refusing noise reduction — "there is what there is" (9 Sep); running two
  vendors' agents on one repository with written handoffs and a one-writer lock.

We understand that submitting this does not guarantee training or product changes.
