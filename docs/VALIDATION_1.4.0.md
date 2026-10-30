# Validation of 1.4.0 (30 October 2026)

This release adds two experimental connectors that run `ael` from inside PixInsight and Photoshop. The `ael` package
does not change (its version number only).

## What changed

1. **`plugins/pixinsight-ael/`, the PixInsight connector.** Two scripts for PixInsight 1.9. The bridge runs
   `structure` and `polar` on the active image and opens every product in a new window. The workflow makes AEL's
   filter layers from a linear stack (`linear.npy`) and writes the PixelMath expressions that compose them; it can
   also build that stack from frames (the linear master, experimental).
2. **`plugins/photoshop-ael/`, the Photoshop connector.** A script for Photoshop 2026 with the same four operations.
   The filter layers arrive as one layered 16-bit PSB, written and verified by `ael.photoshop` and then read again by
   Photoshop, which compares every layer's name, blend mode, opacity byte and visibility with what AEL wrote. A
   difference stops the run with an error; the documents stay open and the differences are written next to the
   receipt.
3. **Packages.** `tools/build_package.py` in each connector writes a self-contained folder: the scripts, the Python
   helpers, a copy of `ael/` under `runtime/ael` (checked byte by byte against the checkout), `runtime/VERSION.json`
   and synthetic demonstration files, plus a deterministic ZIP. Neither connector names an interpreter: each looks
   for a Python 3.10 or later that can import the AEL it carries and its dependencies, and says what it tried when
   none can. Both refuse an AEL older than 1.3.6.
4. **`tools/check_connectors.py`.** Each package carries its own copy of the shared parts. The check fails when the
   two copies of `python/ael_workflow.py`, `tools/make_demo.py` or `tools/build_package.py` differ in anything other
   than the program's name (and the builder's list of files), when the dialogs do not show the same experimental
   notice, when the probes refuse different AEL versions (it runs both probes against stand-in AEL packages of
   version 1.3.3 and of an unreadable version), or when a connector names a private interpreter or a home folder.

## Checks

PixInsight 1.9.4 (arm64) and Photoshop 2026 (27.11.0) on macOS, Python 3.12, AEL 1.3.6 bundled in each package.
PixInsight ran in its own instances (`-n --automation-mode`); Photoshop with no document of anyone else's open.

| | PixInsight | Photoshop |
|---|---|---|
| Every product of `structure` and `polar` against `python -m ael` on the same file | identical, file by file | identical, file by file |
| Filter layers (the three defaults and all sixteen) against `python -m ael filters` | identical | identical (35 files); the 16-bit images the connector opens are `ael.photoshop.to_u16` of AEL's arrays |
| Composite in the program against AEL's `display.tif` | PixelMath replay within 0.504 of a 16-bit step (gate: one step). A layer with one opacity step too many, or with the wrong blend mode, fails it (152 and 11,009 steps) | Photoshop's own composite of the PSB within 5 steps (99.9th percentile 4, mean 0.9). It comes from Photoshop's 15-bit arithmetic: a model of that arithmetic matches Photoshop exactly on 96 % of the pixels. A gate declared before the run (99.9th percentile ≤ 3) failed and is kept in the record |
| Layer check inside the program | — | fails with one opacity byte more or less, and with another mode; a failed check stops the run |
| A real AEL stack: 12 megapixels, values up to 1.5 × 10⁶, 253,851 samples without data (NaN) | identical to the terminal in three cases: scaled to 0–1, as it is, and with its last sample NaN | identical to the terminal; every NaN kept |
| Package folder and its ZIP, run the way a person runs them (dialog filled, Run pressed, no setting) | 26 of 26 gates; menu scripts 14 of 14; the ZIP unpacked under a folder with accents and spaces, the same | 39 of 39 gates, Python found from scratch |
| Linear master (synthetic frames with a known drift) | equal to the terminal; registration error 0.003 px | equal to the terminal; registration error ≤ 0.03 px |
| 80-megapixel synthetic image through the package | 3 of 3 products identical, 47 s, 30 GB of memory | — |

- `python -m ael selftest`: 110 of 110.
- `tools/check_connectors.py` passes. It fails on the two connectors as they were merged, before their shared parts
  were made equal (three checks), and on a Photoshop core that put a private interpreter first.
- The tests check the software; a new astronomical observation needs its own validation.

## What these checks taught

- **The demonstration files were too clean.** A real AEL stack has values far above 1 and NaN outside its coverage;
  the synthetic files had neither. PixInsight rescales a floating-point TIFF with values outside 0–1 when it opens it,
  writes NaN as 1.0 and reads a whole TIFF as black when its last sample is NaN, so every product of the PixInsight
  bridge differed from AEL's on such a stack. The bridge now compares the view with its file and, when PixInsight
  does not hold the file as stored, has AEL read the file itself. The demonstration images that are opened in the
  program are inside 0–1, and both connectors carry the same ones.
- **Rounding twice.** The PixelMath replay started from the display base already rounded to 16 bits and rounded again
  at the end: 1.0039 steps against a gate of one. It now starts from the same floating-point values AEL starts from,
  and the gate did not change.
- **A check that only reports.** A read-only review by Codex found that a failed layer check in Photoshop was written
  next to the receipt while the run still ended as completed, and that the check of the AEL floor read a constant
  instead of running the probes (with the Photoshop refusal switched off, it still passed). A failed layer check now
  stops the run, and `tools/check_connectors.py` runs both probes; with the refusal switched off, it fails.

## Limits

- **The linear master is not valid on real eclipse frames.** It registers every frame on the Sun; on real frames that
  registration lands 0.07–2.2 px from the reference registration, and the cause has not been found. Both dialogs say
  so. Its tests use synthetic frames.
- Tested on macOS only, with the programs driven by scripts: no installation through PixInsight's Feature Scripts
  dialog and no mouse clicks. The filter workflow was not run at 80 megapixels.
- The Photoshop PSB carries no colour profile; Photoshop assigns its working profile when it opens it.
- Where there is no data, the display files of `structure` and `polar` hold black (0), as those of `python -m ael`
  do: the connectors keep every NaN up to AEL, and AEL's display writers turn them into 0. Which samples hold data is
  in the valid mask the products are made from, not in the display file.
