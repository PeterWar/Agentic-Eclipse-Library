# Agentic Eclipse Library

**Skills, research notes and processing code from the total solar eclipse of 12 August 2026, organised so that
an AI agent can pick them up and work with them.**

Author and project owner: **Pere Guerra Serra**. The eclipse was photographed from Grajal de Campos (León, Spain)
with two independent optical trains — a Vixen VSD90SS refractor with a Canon EOS R6 Mark III, and a Sony α7R IIIA
with a 300 mm f/2.8 lens — both driven by [Eclipse Command](https://github.com/PeterWar/Eclipse-Command). The
images were then processed over seven weeks by AI coding agents (Claude, from Anthropic, and Codex, from OpenAI)
working under the author's direction: 123 versions of the image, 179 research notes and more than 3,000 scripts.
In October the work went on with an independent check against coronagraphs and an absolute calibration of the
corona (research notes 180 and 185).

This repository is that work, published as it is — plus, since version 1.1.0, **a runnable package, `ael`**, that
stacks declared RAW recipes, makes filter layers, and produces structure, polar and motion views.

## Start here: your own eclipse photos

**Using Codex?** Install the [AEL desktop plugin](docs/CODEX_PLUGIN.md): seven guided workflows,
the AEL processing engine, a synthetic demonstration and explicit validation limits.
The plugin can be installed from this repository's marketplace; public directory review is a separate process.

Open this folder with your coding agent (Claude Code, Codex or similar) and tell it where your photos are. It reads
[`AGENTS.md`](AGENTS.md) and the skill [`skills/eclipse-first-steps/`](skills/eclipse-first-steps/), looks at your
files and proposes the path one step at a time: calibrate (if you took darks or flats), linearise and stack, open a
layered 16-bit Photoshop project, and add the three most useful corona filters first. You choose how they look.

## Runnable tools

`ael stack` builds a linear stack with explicit calibration and registration. `ael extinction`
corrects that stack for differential atmospheric extinction when the Sun is low, after
subtracting the sky. `ael filters` adds the first three filters or sixteen portable variants
and an optional verified PSB. `ael coronagraph` checks the corona against K-Cor, SOHO/LASCO and
SDO/AIA: angular structure ring by ring with its null, and, with `ael.coronagraph`, brightness in
mean solar brightness with both published LASCO C2 calibrations and K + F for K-Cor. See [stacking and filters](docs/DEVELOP.md)
and the skill [`skills/coronagraph-comparison/`](skills/coronagraph-comparison/).

| Product | What it is |
|---|---|
| **Structure image** | The corona's fine filaments from the limb to the edge of the field (the look made famous by Druckmüller's composites): mono, cool-toned, or in the data's own measured colour |
| **Unrolled corona** | The corona in polar coordinates around the Sun or the Moon: the limb becomes a straight line and the streamers rise like curtains |
| **Coronal motion** | Epochs of one totality aligned on the Sun, displacement vectors that reject sensor-fixed and Moon-fixed "motion", a visual-check sheet and GIF/MP4 animations |

```
pip install -e ".[raw]"
python -m ael selftest                       # known-truth tests and negative controls
python -m ael structure --input composite.npy --valid valid.npy --geometry geometry.json --out out/
python -m ael polar     --input out/structure_cool.tif --geometry out/structure_geometry.json --out out/
python -m ael motion    --config motion_config.json --out out/     # see examples/motion_config_template.json
```

**From PixInsight or Photoshop (to be tested).** [`plugins/pixinsight-ael/`](plugins/pixinsight-ael/) and
[`plugins/photoshop-ael/`](plugins/photoshop-ael/) make the whole image from inside the program. You choose the RAW
photos of the totality and, if you have them, darks and flats; the connector sorts the files, calibrates, finds the
Moon in every photo, registers them on the Sun, stacks them and adds AEL's filter layers, with a receipt of what it
measured and assumed. Both run the same engine (the same file in each package): Photoshop receives one layered
16-bit PSB, PixInsight the same layers as images with the PixelMath expressions that compose them. In PixInsight they
also work on an open linear stack (structure and unrolled views, filter layers). They have been tested on the
author's Mac (their engine on five cameras of two eclipses, each connector inside its program on six frames of one),
but not yet by other people: in theory they should work, and reports are welcome. Each package carries its own copy of the AEL engine.

Every function reads only observed pixels; where there is no data the result is `NaN` (display files show it as
black), never a fill or a mirror.
Details, and what the 2026 data taught (correlated noise, colour in linear light, a sensor pattern that looked
like coronal motion), in [`README_AEL.md`](README_AEL.md). The agent's instructions for the three products are
the skill [`skills/corona-visualizations/`](skills/corona-visualizations/) (in English).

## Contributors

Agentic Eclipse Library was created by Pere Guerra Serra, who maintains it and decides what enters `main` and
each release. The contributors below have added to it; commits sent by contributors keep their authors' names, and every
contribution is published under the same [MIT licence](LICENSE).

[NLFotografia](https://github.com/NLFotografia) contributed a
[case study on preserving an existing edit with adjustable filters](docs/EXISTING_EDIT_CASE_STUDY.md)
in [pull request #2](https://github.com/PeterWar/Agentic-Eclipse-Library/pull/2).
It records separate checks for registration and native Photoshop saves, including the remaining failures.
Her field report in [issue #1](https://github.com/PeterWar/Agentic-Eclipse-Library/issues/1) (variable framing
without calibration frames, rings, earthshine, Photoshop, validation) is in the
[field lessons](docs/FIELD_LESSONS.md#a-field-case-contributed-by-nlfotografia-issue-1) since 1.3.1. Checking
it against the package added ring, support and detail tests for the sixteen filters and found two filter
limitations, now reported as issues.

**Chris Gilly** (NorthWest Research Associates), first author of the RHEF paper (Gilly & Cranmer 2025), reviewed
the draft of the author's paper *A Faithful Corona* and this library in October 2026. Version 1.3.2 answers his
review: an NRGF without the rings that his synthetic test, repeated on 1.3.1, still found on a steep profile; the
Upsilon curve, with an exponent for each side, for any RHEF layer; and
[how the library's filters differ from the layers of the paper's published image](docs/PAPER_AND_LIBRARY.md),
filter by filter.

**Raúl Hussein** ([@rahusga](https://github.com/rahusga)) is the lead contributor of the first skill and the first
case study with several cameras contributed from outside the project, in pull requests
[#5](https://github.com/PeterWar/Agentic-Eclipse-Library/pull/5),
[#6](https://github.com/PeterWar/Agentic-Eclipse-Library/pull/6) and
[#7](https://github.com/PeterWar/Agentic-Eclipse-Library/pull/7). His skill
[`eclipse-astrophotography`](skills/eclipse-astrophotography/SKILL.md), developed from three camera cases, takes an
agent through a whole eclipse case, from the chosen frames to an editable master the photographer accepts. It brings rules already in AEL into
one route, and adds a stage table, five geometry and support roles that one centre or one mask tends to merge, and
a case closeout in which stopping at a known limit is a valid end. His
[three-camera case study](docs/ASTRO_THREE_CAMERA_CASE_STUDY.md) follows a Sony, a Nikon and a Canon that photographed
one eclipse, and keeps in view what each could not establish. He also found that the field lessons still described the
NRGF of 1.3.1 after the 1.3.2 release, and corrected them.

**Oscar Maseda** (Sony) and **Carlos Oltra** (Nikon) photographed that eclipse and made their RAW frames available
for the case study, as Raúl Hussein did with his Canon. The frames stay private.

**Francisco Bitto** ([@fbitto](https://github.com/fbitto)) wrote the
[Eclipse Image Processor](https://github.com/fbitto/Eclipse-Image-Processor), a desktop application with adjustable
controls and a layered Photoshop export. It applies AEL's NRGF, edge-aware WOW and ACHF variants next to filters of
his own, each as an independent layer. He offered it in
[pull request #8](https://github.com/PeterWar/Agentic-Eclipse-Library/pull/8); it lives in his repository, where he
maintains it. His review of the AEL code for that work found two problems in the library: the soft logarithm of
`ael.render` returned −∞ for strongly negative values, and the MGN changed when the input was multiplied by 1e-8.
Both are corrected.

**Eduardo Piñas** ([@edu27](https://github.com/edu27)) photographed the 2026 eclipse from northern Spain with an astronomy
camera and a 300 mm lens, and tested AEL 1.3.3 on his frames. His comment on
[issue #4](https://github.com/PeterWar/Agentic-Eclipse-Library/issues/4) brought a real-data gate, with two independent
half-stacks and a reference without any filter, which showed that the default WOW bilateral layer does not follow the
fine detail; the gate is now `ael.gates.fine_detail_fidelity`. His
[issue #9](https://github.com/PeterWar/Agentic-Eclipse-Library/issues/9) found why the ACHF layers saturate next to the
limb, with a per-ring scale that cures it, and his field case in
[issue #10](https://github.com/PeterWar/Agentic-Eclipse-Library/issues/10) showed mirrored frames that a whole-profile
comparison with LASCO C2 would have accepted. Version 1.3.4 answers them; his case is in the
[field lessons](docs/FIELD_LESSONS.md#a-field-case-contributed-by-eduardo-piñas-issues-4-9-and-10).

**Claude (Anthropic)** and **Codex (OpenAI)** have contributed as AI coding agents to implementation,
documentation and validation under Pere Guerra's direction.

Contributions are welcome through public pull requests. Only [PeterWar](https://github.com/PeterWar)
can update or merge changes into `main`.

Your experience can help the next photographer: a useful measurement, a clearer instruction, a bug or an
approach that did not work. Agents using AEL are encouraged to help you prepare a short contribution and ask
before sharing it. See [how to contribute what you learned](CONTRIBUTING.md). Sharing is optional; you do not
need to publish your photos to contribute.

## What is in it

| Path | What it is | Language |
|---|---|---|
| [`AGENTS.md`](AGENTS.md) | Entry point for any AI agent: what is here, where to start, the working rules that made the difference | English |
| [`skills/eclipse-first-steps/`](skills/eclipse-first-steps/) | How an agent leads a newcomer from their own photos to a layered Photoshop project with the most useful filters | English |
| [`skills/eclipse-astrophotography/`](skills/eclipse-astrophotography/) | A whole eclipse case, from the chosen frames to an editable master the photographer accepts, with photographic acceptance kept apart from scientific claims; contributed by Raúl Hussein | English |
| [`skills/apilatge-imatges-eclipsi/`](skills/apilatge-imatges-eclipsi/) | Linear calibration and stacking of eclipse RAW frames: darks, flats, pedestal, saturation, linearity, noise, weights, coverage | Catalan |
| [`skills/postprocessat-corona/`](skills/postprocessat-corona/) | The post-processing method: registration by ephemeris, linear HDR fusion of the two trains, detail filters (NRGF, RHEF, MGN, WOW, ACHF and our own variants), tone curve, Photoshop layer files, external judge, gates and receipts, with a long log of traps | Catalan |
| [`skills/corregeix-artefactes/`](skills/corregeix-artefactes/) | Finding and curing recurring artefacts at their root: lens ghosts, fixed-pattern striping, coverage edges, limb fringes, radial-profile rings, marks painted by the photographer | Catalan |
| [`skills/corona-visualizations/`](skills/corona-visualizations/) | Structure images, unrolled views and coronal-motion analyses with the `ael` package, with their gates | English |
| [`skills/coronagraph-comparison/`](skills/coronagraph-comparison/) | Checking an eclipse image against K-Cor, SOHO/LASCO and SDO/AIA: structure, orientation and brightness in mean solar brightness, with the traps that were real | English |
| [`ael/`](ael/), [`tests/`](tests/), [`examples/`](examples/) | The runnable package (MIT), its tests with known truth and a configuration template | English |
| [`3-RECERCA/`](3-RECERCA/) | 180 numbered research notes, July–October 2026, with their corrections left in place: capture (camera control, exposure ladders, timing) and post-processing. Start at [`3-RECERCA/ABOUT_THESE_NOTES.md`](3-RECERCA/ABOUT_THESE_NOTES.md) | Catalan |
| [`3-RECERCA/tools/`](3-RECERCA/tools/) | The processing code: about 3,000 Python scripts, shell chains and Photoshop JSX, one folder per stage or version | Catalan comments |
| [`docs/LESSONS_FOR_MODEL_DEVELOPERS.md`](docs/LESSONS_FOR_MODEL_DEVELOPERS.md) | Recurring AI failure modes seen in this project, what fixed them, and requests for model builders | English |
| [`docs/REGISTRE_APORTACIONS_PERE_GUERRA_20260917.md`](docs/REGISTRE_APORTACIONS_PERE_GUERRA_20260917.md) | Dated record of the human contributions: method rules, defects found by eye, manual methods later formalised | Catalan |
| [`PUBLICATION_MANIFEST.md`](PUBLICATION_MANIFEST.md) | What was left out, and why | English |

## Using it with an agent

- **Claude Code:** clone the repository and open it; the skills load from `.claude/skills/`. Or install them
  as a plugin in any project:
  ```
  /plugin marketplace add PeterWar/Agentic-Eclipse-Library
  /plugin install agentic-eclipse-library@pere-guerra-eclipse
  ```
- **Codex:** install the [desktop plugin](docs/CODEX_PLUGIN.md) from this repository's marketplace:
  ```
  codex plugin marketplace add PeterWar/Agentic-Eclipse-Library
  codex plugin add agentic-eclipse-library@pere-guerra-eclipse
  ```
  Python and its dependencies are checked separately. The plugin runs locally and includes the maintained
  AEL 1.4.0 engine. See the guide for desktop-app installation and supported workflows.
- **Other agents:** point the agent at [`AGENTS.md`](AGENTS.md). Each skill is a plain `SKILL.md` with
  `references/` and `scripts/`.
- Most text is in Catalan. Current models read and translate it without trouble; ask your agent to answer in your
  language.

## What this plugin runs, fetches and sends

- **On your computer.** The skills run the `ael` package and the scripts in `skills/*/scripts/`. Installing `ael`
  with `pip` downloads its dependencies from PyPI: NumPy, SciPy, OpenCV, Pillow, tifffile and imageio, plus rawpy
  and Astropy with `[raw]`. The plugin has no hooks and no MCP servers.
- **Public data, after you approve it.** The skill `coronagraph-comparison` tells the agent to ask before any
  download and to say what, from where and how large: K-Cor level-2 FITS from the Mauna Loa Solar Observatory,
  SOHO/LASCO level-0.5 FITS from the Naval Research Laboratory, and SDO/AIA images from Stanford's JSOC.
- **Ephemeris.** The stacking scripts use Skyfield, which downloads the JPL ephemeris `de440s.bsp` (about 33 MB)
  if it is not already in `~/.cache/skyfield/`.
- **Research record.** `3-RECERCA/tools/astrometria/prediccio/baixa_catalegs.sh`, cited in the post-processing
  skill's astrometry notes, downloads the Hipparcos and Tycho-2 star catalogues from CDS/VizieR with `curl`.
  `3-RECERCA/tools/openrouter_client.py` is the client the project used to consult other AI models: if you run it,
  it reads your own OpenRouter key (`OPENROUTER_API_KEY` or the macOS Keychain) and sends your prompt and the files
  you pass to openrouter.ai. No skill tells an agent to run it.
- **Nothing else leaves your computer.** Nothing in this plugin sends your photos or any other data anywhere.

## Honest limits

- **The research scripts are not turnkey software.** The RAW frames, calibration frames, Photoshop files and
  intermediate data arrays are not included, so the scripts in `3-RECERCA/tools/` will not run end to end as they
  are. Read them as a precise record of the method, and adapt them to your own data. The `ael` package is the
  exception: it runs on your data and is tested on synthetic data with known truth.
- **A snapshot of a working project.** Notes and skills cite paths of the original project (`0-RAW`, `1-PHOTOSHOP`,
  `4-RESULTATS`, `IA`, `.coordination`…). Only `3-RECERCA/` is here; the rest are references to evidence that stays
  with the author.
- Constants are specific to this equipment and this eclipse (the Sun was 9° above the horizon).
- Nothing here is peer-reviewed. The notes correct each other in the open; later notes prevail.
- No support or maintenance is promised.

## Acknowledgements

The enhancement filters come from published work by M. Druckmüller, H. Druckmüllerová, H. Morgan, S. Habbal,
F. Auchère, C. Gilly, S. Cranmer, J.-L. Starck, H. Knutsson and colleagues; we implemented them ourselves from their papers
([`3-RECERCA/PAPERS_CONSULTED.md`](3-RECERCA/PAPERS_CONSULTED.md)). Their published images of the same eclipse were
used only as an external judge: no pixel of theirs is in any product, and none of their images is in this
repository.

## Credit

If you use this work — the skills, the notes or the code — or publish an image made with it, a mention in its
caption, description or references would be appreciated. This is a courtesy request, not a condition of the
licence:

    Processed with Agentic Eclipse Library by Pere Guerra — https://github.com/PeterWar/Agentic-Eclipse-Library

For papers and software, [`CITATION.cff`](CITATION.cff) gives the citation (GitHub shows it under "Cite this
repository").

## Licence

[MIT](LICENSE) © 2026 Pere Guerra Serra. You may use, copy, modify and redistribute this work freely, including
commercially; the licence only asks you to keep the copyright and permission notices with copies of the work.

## What is new in 1.4.0

Two connectors run AEL from inside PixInsight and Photoshop, from the RAW photos to a stacked image with AEL's filter
layers. **They still have to be tried by other people**, on other computers and other eclipses; on the author's Mac
their engine has been run on five cameras of two eclipses and each connector inside its program on six frames of one,
and in theory they should work elsewhere.

- **The same two choices in both:** the RAW photos of the totality, and darks and flats if you have them. Everything
  else (which photos to keep, the levels, the Moon, the registration on the Sun with the turn of the field, the light
  of each photo, the colour, the filters) is measured on the files and written in a receipt.
- **The same engine in both** ([`python/ael_auto.py`](plugins/photoshop-ael/python/ael_auto.py)): the same photos
  give the same linear master and the same filter layers in either program. Photoshop receives one layered 16-bit
  PSB, checked layer by layer; PixInsight the layers as images with their PixelMath composite, and it also works on
  an open linear stack.
- **`ael` measures the geometry on the image** (`ael.geometry.find_disc`, `python -m ael geometry`): no geometry file
  is needed to start.
- Measurements, limits and tests: [`docs/VALIDATION_1.4.0.md`](docs/VALIDATION_1.4.0.md).

## What is new in 1.3.6

Two corrections that Francisco Bitto found in his review of the AEL code (see [Contributors](#contributors)). Values
that were already right do not change.

- **`ael.render.soft_log` no longer returns −∞** for strongly negative values after sky subtraction.
- **The MGN no longer depends on the units of the input.** Multiplied by 1e-8, it changed by up to 0.40. See
  [`docs/VALIDATION_1.3.6.md`](docs/VALIDATION_1.3.6.md).
- **Contributors:** Francisco Bitto and his Eclipse Image Processor, which stays in his own repository. Eduardo Piñas
  and Codex are co-authors in the history, so GitHub lists them among the contributors, and Claude is named next to
  Codex.

## What is new in 1.3.5

- **The edge-aware WOW is the default WOW layer** (`wow_edge_aware`), by the author's decision: in his 2026 image it
  keeps the lunar limb clean and shows no rings. It is the layer called WOW bilateral in 1.3.4, and the old name still
  works. In its worst sector it inverts more faint fine detail than the plain WOW (up to 18–20 % on the author's Sony,
  over the limit of Edu's gate): see [`docs/VALIDATION_1.3.5.md`](docs/VALIDATION_1.3.5.md).
- **The plain WOW (`wow`) is optional.** Recommendation: next to a lunar limb that the data reach, use the edge-aware
  WOW; to use the plain WOW further out, blend both layers with a feathered mask.
- **The Photoshop layers take the names of the author's own files.** The number is the family (01 NRGF to 05 WOW), a
  letter tells the variants of one family apart, and the name ends with the parameter that distinguishes the layer, as
  in `05 WOW edge-aware` or `04 ACHF iso 1–16 px`. The receipt keeps the code names.

## What is new in 1.3.4

In answer to Edu's reports (see [Contributors](#contributors)):
- **A new default WOW layer.** WOW bilateral, the default Overlay layer up to 1.3.3, does not follow faint fine
  detail: with two independent half-stacks of the author's 2026 data, 38–46 % of its clear fine detail came out
  inverted, as Edu measured on his own frames. The default is now `wow`, a WOW that measures the noise of the fine
  scales in the far field (plain WOW whitened the correlated noise of a real stack into blotches) and removes, from
  8 px up, the local mean along circles around the Sun (the radial curve subtracted before it leaves residuals that
  plain WOW turned into a dark ring at 4.75 R☉). Next to the Moon and other edges of the data it averages symmetric
  pairs only. It passes Edu's gate on the author's data. At the same starting opacity it is softer than the WOW
  bilateral of 1.3.3 beyond 2 R☉.
- **WOW bilateral, rebuilt with guided range weights.** It is now the operator of the WOW bilateral layer of the
  author's own image, with the range weights of each scale taken from that scale smoothed without range weights: it
  keeps the sign of faint detail where the old range weights inverted it. It is an option and the default does not
  change: on the author's data it still inverts up to 18 % of the clear detail in its worst sector, over the limit of
  Edu's gate. Where the corona data reach the lunar limb, use it: there the default WOW draws rings and a band of
  weaker texture along the limb, which the author found applying this release to his own final image.
- **ACHF layers that do not burn next to the limb** when the sky is left in the stack: a level and a spread per ring
  instead of one for the whole image. It also evens their contrast across radius; `"achf_display": "global"` keeps the
  1.3.3 display.
- **Edu's real-data gate** in the package, optional: `ael.gates.fine_detail_fidelity`, for anyone with two
  independent stacks.
- **Mirrored frames**: `ael.coronagraph.scan_mirror` tries both mirror states against a coronagraph and decides on the
  fine detail; `ael motion` recipes now read `"mirrored"` (it was ignored without warning).
- Checks and limits: [`docs/VALIDATION_1.3.4.md`](docs/VALIDATION_1.3.4.md).

## What is new in 1.3.3

A contribution by Raúl Hussein, with RAW frames from Oscar Maseda and Carlos Oltra (see [Contributors](#contributors)):
- **A seventh skill, [`eclipse-astrophotography`](skills/eclipse-astrophotography/)**: a whole eclipse case, from
  the chosen frames to an editable master the photographer accepts, with photographic acceptance kept apart from
  scientific claims. It brings rules already in AEL into one route and adds a stage table, five geometry and support
  roles and a case closeout. It is also in both plugins.
- **[Three camera cases](docs/ASTRO_THREE_CAMERA_CASE_STUDY.md)**: a Sony, a Nikon and a Canon that photographed one
  eclipse, with what each could not establish.
- **The [field lessons](docs/FIELD_LESSONS.md) now describe the NRGF of 1.3.2**; until now they described that of
  1.3.0–1.3.1.

And a rule for all of AEL: **correct each optic before fusing**, even for a presentation
([`AGENTS.md`](AGENTS.md), rule 11). The `ael` package does not change.

## What is new in 1.3.2

In answer to the review of Chris Gilly (see [Contributors](#contributors)):
- **An NRGF without profile bias.** In 1.3.1 the ring profile was smoothed with a plain Gaussian, which biased
  steep profiles and left a concentric ripple 1.9–2.5 times the sampling floor. Each ring now gives a node with
  the profile's slope and curvature removed, joined by a local curve; in the tests the ripple stays at the
  sampling floor. It takes about five times as long. The NRGF layers of the filter bank change; with the same
  arguments, `spread_about='bin'` in `ael.filters.nrgf` gives the 1.3.1 output bit for bit.
- **Upsilon for any RHEF layer**, with an exponent for each side: `make_filter(..., upsilon_curve=(low, high))`
  from Python (the `ael filters` command does not take it).
- **[The paper and the library](docs/PAPER_AND_LIBRARY.md)**, filter by filter: input channel, rings,
  statistics, limits and blend of the published layers against the library; the algebra of blending a layer
  centred on mid grey; the sky and extinction that ring filters turn into structure.
- Fifteen new controls (84 of 84 tests). Checks and limits: [`docs/VALIDATION_1.3.2.md`](docs/VALIDATION_1.3.2.md).

## What is new in 1.3.1

- The field report of NLFotografia ([issue #1](https://github.com/PeterWar/Agentic-Eclipse-Library/issues/1))
  in [`docs/FIELD_LESSONS.md`](docs/FIELD_LESSONS.md#a-field-case-contributed-by-nlfotografia-issue-1),
  with what was checked in the package and two filter limitations it brought to light.
- Ring, support and detail tests for the sixteen filters on a synthetic scene. No output changes.

## What is new in 1.3.0

- **Coronagraph check** (`ael coronagraph`, `ael.coronagraph`, skill `coronagraph-comparison`):
  structure against K-Cor, LASCO and AIA, and brightness in mean solar brightness; on the 2026 data it
  reproduces the research results.
- **Differential extinction** (`ael extinction`, `ael.extinction`) for a low Sun, with the lesson
  that sky and extinction are degenerate.
- **Fixes prepared as 1.2.1:** continuous radial statistics in NRGF and RHEF (in the field test the
  two-pixel rings fell to about 1 % of their old amplitude), a soft highlight shoulder instead of hard
  clipping, an explicit reference canvas, and the goal-first start for a new user.
- **Field lessons** ([`docs/FIELD_LESSONS.md`](docs/FIELD_LESSONS.md)): coronagraphs, dust, a
  rotational-gradient layer, and adding layers to someone's file without rewriting theirs.
- Research notes 180 and 185, and the code behind them in `3-RECERCA/tools/`.

Existing images are not rewritten; compare a new numerical recipe before adopting it.
See the [changelog](CHANGELOG.md) and [validation](docs/VALIDATION_1.3.0.md).
