# What is in this repository, what is not, and why

Published on 30 September 2026 by decision of the author, Pere Guerra Serra. Version 1.1.0 (2 October 2026) adds the runnable
package `ael`, its tests, a fourth skill and research note 179.

| Included | Files | Notes |
|---|---:|---|
| `skills/` — four Agent Skills | 33 | Snapshot of the working skills on 30 Sep 2026, with their reference files and helper scripts; `corona-visualizations` (English) is new in 1.1.0 |
| `3-RECERCA/` — research notes | 185 | 178 numbered notes plus indexes, sources, prompts and reports of consultations with other models, small data tables |
| `3-RECERCA/tools/` — processing code | 4,207 | Python, shell and Photoshop JSX scripts, and the small JSON/CSV parameter files they read |
| `ael/`, `tests/`, `examples/`, `pyproject.toml`, `README_AEL.md` — the runnable package (1.1.0) | 18 | Structure images, unrolled views and coronal motion from anyone's data; 11 tests with known truth |
| `docs/` | 2 | Lessons for model developers (English); record of the author's contributions (Catalan) |
| `AGENTS.md`, `README.md`, `LICENSE` (MIT), `CITATION.cff`, `.claude-plugin/` | — | Entry points, licence, citation and plugin manifest |

| Left out | Why |
|---|---|
| RAW frames, calibration frames, Photoshop files, the final image and its views | The author's photographs; published separately, with their own copyright |
| Data arrays (`.npy`, `.npz`), run logs, images and compiled libraries from `tools/` (about 1,500 files) | Data, not method; too large, and some are views of the image |
| The papers consulted (PDFs) | Copyright of their publishers; listed in `3-RECERCA/PAPERS_CONSULTED.md`, linked in `3-RECERCA/FONTS.md` |
| Final images of the same eclipse by other photographers, and note 177 | Their copyright; used privately as an external judge only |
| Note 81A, a transcription of a video tutorial | Not ours to publish |
| Raw answers from other AI models | Kept out for simplicity; prompts and reports are included |
| Third-party code copied during research (`umbra`, `eclipsetools`, `sunkit-image`) | Not ours; available from their authors under their own licences |

**Cleaning applied to every published text file:** absolute personal paths rewritten to `/Users/USUARI/…`;
e-mail addresses replaced by `[adreça]`; camera and lens serial numbers replaced by `[SÈRIE]`; one travel detail
removed. A scan for keys, tokens and passwords found none. No other content was edited: the notes and code are
as they were written.
