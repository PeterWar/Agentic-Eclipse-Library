# About these research notes

These are the working notes of the project, written between July and October 2026, mostly in **Catalan**, by the
AI agents (Claude, Codex) at the request and under the direction of **Pere Guerra**. They are published as they
are: numbered in the order they were written, with later notes correcting earlier ones in the open
("rectificació", "errata"). That trail of corrections is part of the value; nothing has been tidied after the fact.

- `README.md` is the Catalan index. Notes `00`–`70` cover the capture side (camera control, exposure ladders,
  timing); `71` onwards the post-processing (calibration, registration, linear HDR fusion, filters, artefacts,
  earthshine, stars, the lunar limb). `179` describes the runnable package `ael` (structure images, unrolled
  views, coronal motion) and what it found in the 2026 data. `180` compares the final image with SDO/AIA,
  SOHO/LASCO and K-Cor; `185` corrects the absolute calibration in mean solar brightness that `180` began, and
  adds the differential extinction under a low Sun (the code is `ael.coronagraph` and `ael.extinction`).
- `tools/` holds the processing code, one folder per stage or image version. Only text files are published: the
  data arrays, logs and images they read and write are not.
- `FONTS.md` lists sources with links. `PAPERS_CONSULTED.md` lists the papers read; the PDFs are **not** included
  because they belong to their publishers.
- Six notes are not published: `81A` (a private transcription of a video tutorial), and `177` and `181`–`184`
  (studies that start from other photographers' images, which may only be used privately).
- From version 1.3.0, two notes had a sentence edited for publication, to remove the names and words of private
  correspondents and a private link (`180`, `185`); each edit is marked in the text. The same names were removed
  from a few lines of `tools/comparacio_sdo_lasco_20261001/` and `tools/msb_calibrat_20261011/`.
- None of this is peer-reviewed. Numbers come with their receipts in the original project; here they stand as
  claims with a method attached. Build on them, check them, and say so if they are wrong.
