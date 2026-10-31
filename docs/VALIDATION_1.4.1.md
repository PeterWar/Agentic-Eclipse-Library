# Validation of 1.4.1 (31 October 2026)

This release follows the first use of the connectors by their author on photos of other cameras and eclipses: an
astro-modified Sony A7S behind a Questar under thin cloud, and a Canon EOS 6D, both of 2024. Three artefacts of the
A7S run are cured where they are born, in the connectors' engine (`python/ael_auto.py`), in `ael.stack` and in
`ael.radial`. The dialogs of both connectors ask for less guesswork, and Photoshop now shows AEL's progress. What
changed is described in the [changelog](../CHANGELOG.md); this page says how it was checked. Everything below was
measured on the author's Mac: macOS on Apple silicon, Python 3.12, PixInsight 1.9.4, Photoshop 2026 (27.11.0).

## What the author's photos showed

The A7S run had 19 RAW frames of 0.05, 0.125 and 1 s, without darks or flats. Thin cloud changed the sky by 3.9 %
during the totality, and 16 frames were stacked. Three artefacts came out: a ring along an isophote at about 1.25
solar radii, rows of dark dots, and thin concentric halos in the NRGF. All three were already in the linear master,
before any filter, or came from the filter itself.

**The ring.** It lay where the 1 s frames give way to the shorter ones, and it had two causes, both in the stack. The
level: the short frames ran from −8 % to +37 % of the 1 s ones, depending on brightness and place, which is what thin
cloud does (it takes light away from the corona and spreads part of it around); with a smooth level field per frame
the exposures agree within 0.3 %. The grain: with weights proportional to the exposure time, a 1 s frame kept the
stack until the last tenth of its range, the grain doubled across a band 0.08 solar radii wide, and WOW and ACHF,
which normalise by the local noise, drew it as a contour even with the level matched; the gradual hand-over removes it.

How it was judged:

- **The measure:** the contour of each layer along an isophote of the master, that is, the layer within 3 px of the
  isophote minus the layer 8–24 px away.
- **Where:** along the boundary isophote and along dozens of control isophotes of the same image. The disc the Moon
  swept, plus 30 px, is left out.
- **On which angles:** all position angles together, and each of twelve 30° sectors, because a good aggregate can
  hide a local failure. A sector fails when the boundary's contour is more than 1.5 times the largest contour of that
  sector's control isophotes.

| Layer | 1.4.0: sectors failing (worst ratio) | 1.4.1 |
|---|---|---|
| ACHF | 8 of 12 (10.8×) | 0 of 12 (1.06×) |
| WOW | 9 of 12 (7.5×) | 0 of 12 (1.37×) |
| NRGF | 1 of 12 (1.5×) | 0 of 12 (1.04×) |
| Composite | 6 of 12 (8.7×) | 0 of 12 (1.0×) |

On all angles together, the boundary's contour against the largest control:

| Layer | 1.4.0 (largest control) | 1.4.1 (largest control) |
|---|---|---|
| ACHF | 0.20 (0.039) | 0.021 (0.035): below |
| Composite | 10 steps of 8 bits (2) | 2 steps (3): below |
| WOW | 0.065 (0.014) | 0.013 (0.012): level with it |

The fine level of the master (a 12 px high-pass) along the boundary went from 1.8 times the largest control to 0.35
times. At full resolution, with the contrast tripled, the ring is no longer seen in any layer or in the composite.

**The price.** In the band where the exposures hand over (65–88 % of the ceiling of the 1 s frames), the grain per
pixel rises to 0.13 %, against 0.065 % with 1.4.0: the grain the shorter exposure already had just outside the
boundary. None of these removed the ring, and they were set aside: a gain alone (0.5 % left in the master); a level
field fitted only where a frame has its full weight (3–5 % left in the transition); a lower ceiling (the contour moved
to the new boundary); fading the weights from 30 % of the range (slightly worse than from 50 %).

**Dust and hot pixels.** The frames themselves showed 255 dust shadows (0.25 % of the sensor) and 10,330–10,890 hot
pixels per colour plane (0.35 % of a plane, the union over the three exposures). The rows of dots are gone. A first
attempt found 1,415 shadows, with false arcs: the frames moved almost only horizontally, and a horizontal line of the
sky stays still on the sensor. Looking for dust after the level fields, and accepting only compact shadows, removed
them. A thin feature of the corona is not taken for dust.

**The NRGF halos.** In fixed 15° sectors, at the radii where the frame's edge cuts the annuli, the layer's step fell
from 0.0136 to 0.0074 (median of 62 sectors), below its step at control radii (0.0137). The NRGF still shows broad
bands with no step at the cut radii: the vignetting, because there were no flats, and the corona.

**Left as they are, because they are data.** The U-shaped arcs above the lower prominence are corona: they come out
the same in the two halves of the short frames (correlation 0.95), which sat more than 50 px apart on the sensor. The
camera's magenta was not touched.

**A clear sky** (the six 2026 frames of the Vixen VSD90SS with a Canon EOS R6 Mark III, with 16 darks and 5 flats).
The same hand-over showed where the 2 s frames give way to the 0.25 s ones: with 1.4.0 the ACHF failed 5 of 12
sectors (up to 2.3×); with the gradual hand-over, 1 of 12 (1.6×). The master changes in 1.7 % of its pixels, by at
most 0.13 %. Near the limb the test cannot tell the two apart: the contours follow the edge of the excluded lunar band.

**A Canon EOS 6D (2024, cirrus).** 132 RAW frames went through the final engine without errors in 8.5 minutes, and 55
were stacked. The exposures agree within ±0.7 %, except the 1/2500 s one: +7 %, and +22 % without the level fields.
It was compared with the 0.25 s frames where those are still linear, and it has 625 times less light there: the
weakest comparison of all. Dust and hot pixels were not looked for: the frames did not move on the sensor.

## Inside the programs

**PixInsight 1.9.4 (arm64)**, in its own instances (`-n --automation-mode`). The dialog was run the way a person runs
it: **Stacked image from RAW photos**, the six Vixen frames, 16 darks and 5 flats, Run pressed: 82 of 82 gates in the
source tree and 82 of 82 in the package. Menu scripts 12 of 12; bridge validation 27 of 27. The gates new in 1.4.1:

- **The whole Console is read, from the script's first line**, and no call may be one that PixInsight calls
  deprecated. PixInsight warns once per session, at the first call; the earlier test read only the part written
  during the stack. On the first 1.4.1 package this gate fails, as it should, with two warnings
  (`getEnvironmentVariable()` and `corePlatform`).
- **No function is defined twice in the scripts.** A later definition silently replaces an earlier one; it happened
  once during this work, and no Python found `ael`.
- **The box “Agentic Eclipse Library”** with its title, the invitation, the GitHub address in blue and underlined, and
  the MIT licence line with its disclaimer.
- **Pressed through the dialog's own handlers, as a click would:** the address (the test catches the command instead
  of opening a browser) and OK in **Advanced settings…**.
- **The linear master's window is compared with its file.** With 1.4.0 that window opened black.

**Photoshop 2026 (27.11.0)**, with no document of anyone else's open; the package through the dialog, as a person
runs it, with the dialogs' buttons pressed by the test:

- Six Vixen frames, 16 darks and 5 flats: **23 of 23 gates**, 385 s. The progress window was on screen in 227 of the
  231 times the test asked the window server while AEL worked, and two pictures of it, 12 s apart, differ (its clock
  moves). Its second line said that AEL was still working during the long filters. The link is the address in blue,
  underlined, and a click asks the system to open the library's address; the link and the licence are inside the
  box. The filters chosen reach the PSB (one at 0 % as a hidden layer), the PSB is 16-bit with the hash of the
  receipt, and the connector's files do not change.
- **Cancel** marked at 150 s, inside the WOW filter (which runs for about 100 s without reporting): **11 of 11
  gates**. The window said "Stopping", Python was stopped 15 s after Cancel (the filter does not look for the stop
  file), the closing message says that nothing was opened, nothing was opened and no Python was left running.
  Photoshop left the screen and came back several times during the run (another desktop); whenever it was on screen,
  so was the progress window (71 of 71).
- The author also ran the dialog on 2026 frames of the Sony A7R III: the progress window stayed on screen while
  Photoshop was, through the filters and the saving, and the run wrote its PSB.

The programs ran the packages of the connectors as they are in this release, file for file, except
`runtime/VERSION.json`, which names the commit they were built from.

## Other checks

- `python -m ael selftest`: 117 of 117. The new test hands over from a long frame that reads 1 % high and shows which
  part of the stack it keeps.
- `tools/check_connectors.py`: 12 of 12. New: both dialogs show the same licence line and the disclaimer of their
  `LICENSE`, and both `LICENSE` files are the same. Six negative controls fail it: one word changed in the licence
  line, in the disclaimer or in a `LICENSE`, the invitation ending with a full stop, a typo in the address.
- The tests check the software; a new astronomical observation needs its own validation.

## What these checks taught

- **A gate has to look at what a person sees.** The Photoshop test of the first 1.4.1 package passed 17 of 17 with a
  progress window that never reached the screen (ScriptUI held it at 0 × 0 pixels, off screen, while the script
  waited): it read what the code wrote, not the screen. It now asks the window server and compares pictures.
- **Photoshop's ExtendScript reads a chain of conditionals differently from JavaScript.** Inside Photoshop,
  `true ? "A" : true ? "B" : "C"` gives "B". After Cancel the window said "Still working" instead of "Stopping"; the
  connector now uses `if`/`else`.
- **ScriptUI in this Photoshop draws no text with `onDraw` and `drawString`:** the underline was drawn and the
  letters were not. The link is a blue text with a one-pixel blue line under it.
- **The NRGF's halos hide in a median over all angles**, which is flat by construction: measure them in fixed sectors
  at the radii where the frame's edge cuts the annuli.

## Limits

- Tested on macOS (Apple silicon) only, by the author and by scripts that press the dialogs' buttons; not yet by other
  people. Inside the programs, the six Vixen frames of one eclipse (and, in Photoshop, one run of the Sony A7R III by
  the author); the A7S and the 6D of 2024 went through the same engine outside the programs.
- **Cancel in Photoshop and the link in either program were not clicked by hand in a test.** The tests mark Cancel
  where Photoshop's answer marks it, and call what the click calls (the system's `open` with
  `https://github.com/PeterWar/Agentic-Eclipse-Library`).
- Where the exposures hand over, the grain is up to twice that of 1.4.0. The gradual hand-over is what the connectors
  use; the library's default stays `'exposure'`.
- Without flats the vignetting stays. Dust and hot pixels are found on the frames only when the frames of an exposure
  sit at least 3 px apart on the sensor.
- While the engine writes the PSB (about two minutes for six frames), Photoshop's progress window still names the
  last filter; its second line says that writing the PSB can take minutes. The window's title is Photoshop's own.
- The Photoshop connector's linear master (a 32-bit TIFF with NaN where nothing was observed) opens black in
  PixInsight 1.9.4; for PixInsight, use the PixInsight connector, whose master is written in 0–1 with an alpha channel.
- An astro-modified camera keeps the factory colour matrix and comes out red or magenta.
- **Installing through PixInsight's Feature Scripts:** after the result message, PixInsight's "Searching for Scripts"
  window comes up over it and stays open until **Cancel** is pressed; nothing is lost. It comes from PixInsight's own
  dialog, not from the package (the folder holds one script); a script cannot add itself to the menu, and an update
  repository is accepted only if a certified developer signs it or the user allows unsigned repositories. The
  connector's README says what to press.
