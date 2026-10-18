# What is in this repository, what is not, and why

Published on 30 September 2026 by decision of the author, Pere Guerra Serra. Version 1.1.0 (2 October 2026) adds the runnable
package `ael`, its tests, a fourth skill and research note 179. Version 1.1.1 (same day) adds the skill
`eclipse-first-steps`, which tells an agent how to lead a newcomer through their own photos, and `ael.photoshop`.
Version 1.2.0 (3 October) adds `ael stack` and `ael filters`. Version 1.3.0 (13 October) adds `ael.extinction`,
`ael.coronagraph`, the skill `coronagraph-comparison`, research notes 180 and 185 and the code of five new
research folders, and releases the fixes prepared as 1.2.1. Version 1.3.1 (same day) adds the field report of
issue #1 to the field lessons and two tests. Version 1.3.2 (16 October) answers Chris Gilly's review of the
draft of the paper *A Faithful Corona*: a new NRGF, Upsilon for any RHEF layer, `docs/PAPER_AND_LIBRARY.md` and fifteen controls.
Version 1.3.3 (18 October) adds the contribution of Raúl Hussein (the skill `eclipse-astrophotography`, a
three-camera case study and a correction to the field lessons) and rule 11 of `AGENTS.md`; the `ael` code does not change.

| Included | Files | Notes |
|---|---:|---|
| `skills/` — seven Agent Skills | 39 | Snapshot of the working skills on 30 Sep 2026 (`eclipse-first-steps` revised and `coronagraph-comparison` added on 13 Oct), with their reference files and helper scripts; `corona-visualizations` (English) is new in 1.1.0, `eclipse-first-steps` (English) in 1.1.1, `coronagraph-comparison` (English) in 1.3.0; `eclipse-astrophotography` (English), contributed by Raúl Hussein, in 1.3.3 |
| `3-RECERCA/` — research notes | 187 | 180 numbered notes plus indexes, sources, prompts and reports of consultations with other models, small data tables |
| `3-RECERCA/tools/` — processing code | 4,352 | Python, shell and Photoshop JSX scripts, and the small JSON/CSV parameter files they read |
| `ael/`, `tests/`, `examples/`, `pyproject.toml`, `README_AEL.md` — the runnable package | 39 | Stacking, extinction, filter layers, structure images, unrolled views, coronal motion, coronagraph checks and layered Photoshop files from anyone's data; 84 tests with known truth (1.3.3; the code is that of 1.3.2) |
| `docs/` | 17 | Recipes, field lessons, validation records, two community case studies, the plugin guide, privacy and terms, and the paper's layers against the library (English); lessons for model developers (English); record of the author's contributions (Catalan) |
| `AGENTS.md`, `README.md`, `LICENSE` (MIT), `CITATION.cff`, `.claude-plugin/` | — | Entry points, licence, citation and plugin manifest |

| Left out | Why |
|---|---|
| RAW frames, calibration frames, Photoshop files, the final image and its views | The author's photographs; published separately, with their own copyright |
| Data arrays (`.npy`, `.npz`), run logs, images and compiled libraries from `tools/` (about 1,500 files) | Data, not method; too large, and some are views of the image |
| The papers consulted (PDFs) | Copyright of their publishers; listed in `3-RECERCA/PAPERS_CONSULTED.md`, linked in `3-RECERCA/FONTS.md` |
| Final images of the same eclipse by other photographers, notes 177 and 181–184 (they start from or build on those images and presentations), and the research folders built on them (`moviment_estrobo_desplegada_20261002`, `capa_alineada_20261006`, `cronologia_vixen_20261007`) | Their copyright; used privately as an external judge only |
| Data downloaded from K-Cor, SOHO/LASCO and SDO/AIA | Public, and not redistributed here; the skill `coronagraph-comparison` says where to get them and how to cite K-Cor |
| Note 81A, a transcription of a video tutorial | Not ours to publish |
| Raw answers from other AI models | Kept out for simplicity; prompts and reports are included |
| The reviewer's letter and synthetic test scripts (October 2026) | Private correspondence; the changes they led to are in the changelog |
| Third-party code copied during research (`umbra`, `eclipsetools`, `sunkit-image`) | Not ours; available from their authors under their own licences |

**Cleaning applied to every published text file:** absolute personal paths rewritten to `/Users/USUARI/…`;
e-mail addresses replaced by `[adreça]`; camera and lens serial numbers replaced by `[SÈRIE]`; one travel detail
removed. A scan for keys, tokens and passwords found none. No other content was edited: the notes and code are
as they were written. Since 1.3.0 one exception is recorded: in three passages of note 180, one of note 185 and
a few lines of the code behind them, the names of private persons, the words of a private message and a private
link were removed, and note 185 gained one closing line about this release. Each edit in a note is marked in its
text; the author's build log (not published) lists every replacement.
