# Validation of 1.4.0 (30 October 2026)

This release adds two experimental connectors that run `ael` from inside PixInsight and Photoshop. In the `ael`
package, the geometry can be measured on the image (`ael.geometry.find_disc` and `measure_geometry`), and a flat may
mark with NaN a pixel it has no value for (`ael.stack`); nothing else changes.

## What changed

1. **`plugins/pixinsight-ael/`, the PixInsight connector.** One script for PixInsight 1.9 with one dialog. It runs
   `structure` and `polar` on the active image, makes AEL's filter layers from the active image with the PixelMath
   expressions that compose them, or builds a linear master from frames, darks and flats (experimental), and opens
   every product in a new window.
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

- **The linear master's registration has not been compared frame by frame with an independent one.** It places
  every frame's Sun from its own Moon and the corona (see below). Its synthetic tests hold to 0.035 px.
- Tested on macOS only, with the programs driven by scripts: no installation through PixInsight's Feature Scripts
  dialog and no mouse clicks. The filter workflow was not run at 80 megapixels.
- The Photoshop PSB carries no colour profile; Photoshop assigns its working profile when it opens it.
- Where there is no data, the display files of `structure` and `polar` hold black (0), as those of `python -m ael`
  do: the connectors keep every NaN up to AEL, and AEL's display writers turn them into 0. Which samples hold data is
  in the valid mask the products are made from, not in the display file.

## Later on 30 October: one dialog, darks and flats

After testing the package, the author asked for one menu entry instead of two, file lists that take several files and
RAW files, an output folder that starts somewhere (Downloads) with a **Browse…** button, and darks and flats that make
their masters or are taken as masters.

- **Calibration, synthetic** (`plugins/pixinsight-ael/tests/workflow_calibration.py`): three frames written as a
  sensor records them (a flat field with vignetting and a dust shadow, and a dark signal with hot pixels that grows
  with the exposure), three darks per exposure, three flats with a dead pixel. One master dark per exposure, equal to
  the median of its files; the master flat equal to the median of the normalised flats, without a value at the dead
  pixel; the master equal, bit for bit, to the stack of the frames calibrated by hand with the same registration; the
  same frames uncalibrated differ by up to 7.9 times the median. Refused before anything is written: a frame whose
  exposure has no dark, a dark at another ISO, a master dark without an exposure for frames of several exposures, a
  RAW dark for TIFF frames, a flat of another camera.
- **Calibration, real:** two Vixen R6 III totality frames (1/30 s and 2 s) with 39 RAW darks of those exposures and
  10 RAW flats: two master darks (median 512, the black of the covered border), a master flat without a value only on
  the last row and column (the sensor's sides are odd, 4639 × 6959), and the second frame registered with the Moon
  crossing 3.6 px in 15 s against 6.7 px allowed. 4.5 minutes, 14 GB of memory at the peak.
- **The time between frames:** in `tests/workflow_lunar_motion.py` the same moving Moon (3.2 px) is refused in frames
  taken 1 s apart and passes in frames taken 100 s apart (0.008 px against the Sun).
- **The frames were registered uncalibrated**: a dark signal that does not grow with the exposure made the registration
  on the logarithm fail to converge in the synthetic test. The frames are now registered calibrated, as they are stacked.
- **The registration, rewritten.** Judge: with the time of every frame, the Moon's shift relative to the Sun must lie
  on a straight line, because the Moon crosses the Sun at a constant velocity. The Gauss-Newton fit of the logarithm put it 4–6 px (rms) off
  that line on 15 Canon EOS 6D frames of 2024, up to 12 px, with the same result started only at full resolution. The
  corona correlated within the window the Moon allows, band-passed at the Moon's scale, puts the frames whose corona
  holds within 0.45 px of the line on 15 Vixen R6 III frames of 2026 (velocity 0.2713 px/s; the ephemeris gives
  0.271), 0.9 px on the 6D frames and 0.55 px on 13 Sony α7 III frames of 2024. The 1/3200 s frames have too little
  corona to correlate (peak 0.01–0.03) and are placed by their Moon and the velocity. With the times of the 6D frames
  shuffled, the run is refused. The Sony frames of 0.4 s, whose Moon is veiled by cirrus, leave 13–14 px in their limb
  fit against 0.6–0.8 px and are refused. The three CR2 frames that stopped earlier in the evening now make a master.
