# Eclipse Corona Agents

**Skills, research notes and processing code from the total solar eclipse of 12 August 2026, organised so that
an AI agent can pick them up and work with them.**

Author and project owner: **Pere Guerra Serra**. The eclipse was photographed from Grajal de Campos (León, Spain)
with two independent optical trains — a Vixen VSD90SS refractor with a Canon EOS R6 Mark III, and a Sony α7R IIIA
with a 300 mm f/2.8 lens — both driven by [Eclipse Command](https://github.com/PeterWar/Eclipse-Command). The
images were then processed over seven weeks by AI coding agents (Claude, from Anthropic, and Codex, from OpenAI)
working under the author's direction: 123 versions of the image, 178 research notes and more than 3,000 scripts.

This repository is that work, published as it is.

## What is in it

| Path | What it is | Language |
|---|---|---|
| [`AGENTS.md`](AGENTS.md) | Entry point for any AI agent: what is here, where to start, the working rules that made the difference | English |
| [`skills/apilatge-imatges-eclipsi/`](skills/apilatge-imatges-eclipsi/) | Linear calibration and stacking of eclipse RAW frames: darks, flats, pedestal, saturation, linearity, noise, weights, coverage | Catalan |
| [`skills/postprocessat-corona/`](skills/postprocessat-corona/) | The post-processing method: registration by ephemeris, linear HDR fusion of the two trains, detail filters (NRGF, RHEF, MGN, WOW, ACHF and our own variants), tone curve, Photoshop layer files, external judge, gates and receipts, with a long log of traps | Catalan |
| [`skills/corregeix-artefactes/`](skills/corregeix-artefactes/) | Finding and curing recurring artefacts at their root: lens ghosts, fixed-pattern striping, coverage edges, limb fringes, radial-profile rings, marks painted by the photographer | Catalan |
| [`3-RECERCA/`](3-RECERCA/) | 177 numbered research notes, July–September 2026, with their corrections left in place: capture (camera control, exposure ladders, timing) and post-processing. Start at [`3-RECERCA/ABOUT_THESE_NOTES.md`](3-RECERCA/ABOUT_THESE_NOTES.md) | Catalan |
| [`3-RECERCA/tools/`](3-RECERCA/tools/) | The processing code: about 3,000 Python scripts, shell chains and Photoshop JSX, one folder per stage or version | Catalan comments |
| [`docs/LESSONS_FOR_MODEL_DEVELOPERS.md`](docs/LESSONS_FOR_MODEL_DEVELOPERS.md) | Recurring AI failure modes seen in this project, what fixed them, and requests for model builders | English |
| [`docs/REGISTRE_APORTACIONS_PERE_GUERRA_20260917.md`](docs/REGISTRE_APORTACIONS_PERE_GUERRA_20260917.md) | Dated record of the human contributions: method rules, defects found by eye, manual methods later formalised | Catalan |
| [`PUBLICATION_MANIFEST.md`](PUBLICATION_MANIFEST.md) | What was left out, and why | English |

## Using it with an agent

- **Claude Code:** clone the repository and open it; the three skills load from `.claude/skills/`. Or install them
  as a plugin in any project:
  ```
  /plugin marketplace add PeterWar/Eclipse-Corona-Agents
  /plugin install eclipse-corona@pere-guerra-eclipse
  ```
- **Codex and other agents:** point the agent at [`AGENTS.md`](AGENTS.md). Each skill is a plain `SKILL.md` with
  `references/` and `scripts/`.
- Most text is in Catalan. Current models read and translate it without trouble; ask your agent to answer in your
  language.

## Honest limits

- **Not turnkey software.** The RAW frames, calibration frames, Photoshop files and intermediate data arrays are not
  included, so the scripts will not run end to end as they are. Read them as a precise record of the method, and
  adapt them to your own data.
- **A snapshot of a working project.** Notes and skills cite paths of the original project (`0-RAW`, `1-PHOTOSHOP`,
  `4-RESULTATS`, `IA`, `.coordination`…). Only `3-RECERCA/` is here; the rest are references to evidence that stays
  with the author.
- Constants are specific to this equipment and this eclipse (the Sun was 9° above the horizon).
- Nothing here is peer-reviewed. The notes correct each other in the open; later notes prevail.
- No support or maintenance is promised.

## Acknowledgements

The enhancement filters come from published work by M. Druckmüller, H. Druckmüllerová, H. Morgan, S. Habbal,
F. Auchère, C. Gilly, S. Cranmer and colleagues; we implemented them ourselves from their papers
([`3-RECERCA/PAPERS_CONSULTED.md`](3-RECERCA/PAPERS_CONSULTED.md)). Their published images of the same eclipse were
used only as an external judge: no pixel of theirs is in any product, and none of their images is in this
repository.

## Credit

If you use this work — the skills, the notes or the code — or publish an image made with it, a mention in its
caption, description or references would be appreciated. This is a courtesy request, not a condition of the
licence:

    Processed with Eclipse Corona Agents by Pere Guerra — https://github.com/PeterWar/Eclipse-Corona-Agents

For papers and software, [`CITATION.cff`](CITATION.cff) gives the citation (GitHub shows it under "Cite this
repository").

## Licence

[MIT](LICENSE) © 2026 Pere Guerra Serra. You may use, copy, modify and redistribute this work freely, including
commercially; the licence only asks you to keep the copyright notice with copies of the work.
