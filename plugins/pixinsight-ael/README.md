# PixInsight bridge for Agentic Eclipse Library

This experimental connector runs the Agentic Eclipse Library (AEL) from PixInsight, with one menu entry and one dialog: the `structure` and `polar` commands on the active image, AEL's filter layers of the active image with an adjustable PixelMath composite, and a linear master from totality frames, darks and flats (experimental). It applies AEL's fixed recipes, gates and receipts; it does not make agent decisions and does not change the AEL algorithms.

The source image is never edited. Each resulting image opens in a new PixInsight window and is also written to disk.

## Requirements

- PixInsight 1.9.4 or later.
- Python 3.10 or later with AEL's dependencies: `python -m pip install numpy scipy opencv-python-headless pillow tifffile imageio`. AEL itself is not on PyPI.
- **AEL 1.4.0 or later.** The package built by `tools/build_package.py` carries it under `runtime/ael` and the connector uses it with no setting at all. In a source checkout the repository root, which holds `ael/`, is used the same way. An older AEL, or one whose version cannot be read, is refused before anything is processed: 1.4.0 measures the geometry on the image, which the dialog uses, since it asks for no geometry; 1.3.6 has the soft-log and MGN corrections that the structure image and the filter layers depend on, and 1.3.5 the edge-aware WOW and the layer names per family.

### Finding Python

The dialog has no Python field: the connector looks for one by itself, in this order: the path saved by the last successful run, `AEL_PYTHON`, `python3` and `python3.N` (newest first) in the Homebrew and system folders, the virtual environments in `~/.venvs`, `~/.virtualenvs` and `~/venvs` (and `~/venv`, `~/.venv`), pyenv, conda and Apple's `python3`. Each one is probed before it is used: Python 3.10 or later, and `import ael` works with the selected AEL folder, which needs NumPy and the rest. The first that passes is used and saved. If none does, the message says how to install the dependencies and lists every interpreter that was tried and why it failed. A Python without the dependencies is skipped, not used. To use one particular Python, set `AEL_PYTHON` to it. AEL is always the one that comes with the connector (or the repository root in a source checkout).

## Local installation

1. Keep the folder `pixinsight-ael/` together: the scripts, `python/` and `runtime/` with their relative paths.
2. In PixInsight, choose **Script > Feature Scripts…**.
3. Click **Add** (it asks for a folder), choose the folder `pixinsight-ael/`, and the dialog lists `AELBridge.js`, enabled. Click **Done**.
4. Open **Utilities > Agentic Eclipse Library**.

This is a local build for testing, not a signed update repository. `tools/build_package.py --out FOLDER [--zip FILE]` assembles the folder, with `runtime/ael` copied from the checkout and checked byte by byte, `runtime/VERSION.json` (AEL version, the last commit of `ael/`, the commit of the connector and whether either had uncommitted changes, with the same keys as the Photoshop connector's) and the synthetic files of `demo/`.

## Use

The dialog is meant for people who do not know the technology: it asks only for what a person knows, and each operation shows only its own fields.

1. For the first three operations, open a monochrome or three-channel RGB image (for a floating-point TIFF with values outside 0–1, or one without data in its last sample, see **When PixInsight does not hold the file as it is stored**).
2. In **Utilities > Agentic Eclipse Library**, choose what to make (**Make**): **Structure image**, **Unrolled view of the corona** (a radius field appears: the outer radius in solar radii, 4 by default), **Filter layers and PixelMath composite**, or **Linear master from frames (experimental)**. For the first three, check the image; for the master, add the frames (and, if there are any, the darks and flats) with **Add files…**, which takes several files at once: RAW (CR2, CR3, NEF, ARW, DNG, RAF, ORF, RW2), TIFF or FITS.
3. The output folder starts at Downloads (then at the last folder used); **Browse…** chooses another. Each run creates a new timestamped subfolder, so previous runs are not overwritten.
4. Click **Run**.

There is no geometry to give. AEL measures it on the image (`ael.geometry.measure_geometry`): it finds the lunar disc, or the closed region without data that AEL stacks leave around the Moon, and places the Sun at its centre with its radius; north, parity and scale stay unknown (position angles are counted from the top of the image). A new window, `AEL_geometry_check_…`, shows the image with that circle drawn in red; the image itself is not changed. The receipt says what was measured and what was assumed. An image without a lunar disc is refused with that reason. A geometry can still be given to AEL from the terminal (`python -m ael structure --geometry FILE.json`) or to `aelBridgeRunOnView` from a script.

The bridge writes a 32-bit floating-point, interleaved TIFF in a unique temporary directory. A preflight check rejects planar RGB, unexpected shapes, incorrect sample types and missing ICC data before AEL runs. If PixInsight changes ICC header flags while writing TIFF, the helper restores the original profile and verifies that every image sample remains unchanged. The receipt records this repair. The temporary directory is removed afterwards.

The output folder contains the AEL products, `input_geometry.json` and `AEL_BRIDGE_RECEIPT.json`. The bridge receipt records the command, Python and AEL paths and versions, input TIFF SHA-256, layout, ICC information, files and gate result. `structure` also writes AEL's own `structure_RECEIPT.json`; because `polar` does not currently write an AEL receipt, the bridge receipt is the run record for that command. Receipts are printed to the Process Console.

## Validation

The tests and tools are in the repository (`plugins/pixinsight-ael/tests` and `tools`); the delivered package does not carry them.

The test launcher looks for an interpreter in the same places as the dialog (see **Finding Python**); `AEL_PYTHON` selects one explicitly. It uses only synthetic data and starts new PixInsight instances with `-n --automation-mode` and `--force-exit`, which never send a script to an instance that is already open (without `-n`, PixInsight yields the command to a running instance). A test that is stopped by its timeout stops only its own instance. On Apple silicon PixInsight 1.9.4 has only the V8 JavaScript engine: every script must start with `#engine v8`, or PixInsight refuses it (*the legacy 'sm' JavaScript engine is not available in this PixInsight build*), and in automation mode that error is never seen outside the instance. The connector's scripts and the test scripts carry the line.

```bash
PYTHONDONTWRITEBYTECODE=1 python plugins/pixinsight-ael/tests/run_tests.py \
  --output /path/to/validation-output
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python plugins/pixinsight-ael/tests/dialog_flow.py \
  --repo . --python "$(which python)" --output /path/to/dialog-output
PYTHONDONTWRITEBYTECODE=1 python plugins/pixinsight-ael/tests/entry_scripts.py \
  --repo . --output /path/to/entry-output
```

`run_tests.py` covers:

- exact float32 RGB and monochrome TIFF round trips, shape and orientation;
- negative orientation tests;
- exact ICC preservation from a source TIFF;
- identical output pixels from direct AEL and bridge executions of both commands;
- unchanged source pixels;
- clear errors for a missing executable, missing AEL, an old Python and an old AEL (1.3.3, 1.3.6 and an unreadable version are refused, 1.10.0 is accepted: versions compare as numbers);
- the interpreter detection with nothing chosen, from a clean saved-settings state and without `AEL_PYTHON`;
- paths containing spaces and accented characters;
- samples without data (NaN): the file PixInsight's writer makes has them as 1.0 (the control), the file the bridge hands to AEL has them as NaN again, and the structure image of a scene with a band, a block and a patch without data equals the one `python -m ael` makes from the file, while AEL on the file as PixInsight writes it gives three different images;
- a file with values outside 0–1 (which PixInsight rescales) and a file whose last sample is NaN (which it reads as black): the bridge runs AEL on the file itself, its structure image equals the one `python -m ael` makes from the file, and the file is left as it was;
- dialog and result images rendered by PixInsight.

`dialog_flow.py` builds the dialog in PixInsight, chooses each of its four operations, fills its few fields, presses **Run** and checks the windows and files each one leaves: the pixels against `python -m ael ... --geometry auto` and against the workflow helper run from the terminal on the same files, the PixelMath composite, and that no message box appears. The file and folder choosers are replaced by stand-ins that record how the dialog asks (several files at once; RAW, TIFF and FITS, and NPY for a master dark or flat) and answer with the files a person would pick. It also checks that the geometry is measured, the Moon of the demonstration image found within 1 px (the centre on both images, the radius on the linear one) and a check window opened; that each operation shows only its own fields; that the output folder starts at Downloads and **Browse…** sets it (the folder the dialog keeps is restored afterwards); that a file added twice is listed once; that the filter layers of an image PixInsight rescaled are made from its file; and that the master takes two darks for each exposure and three flats and equals the master the helper makes from the terminal with the same files.

`entry_scripts.py` runs `AELBridge.js`, the file that the Script menu starts, unchanged in its own new PixInsight instance, and checks that the dialog appears with its title, its Run button, its fields and four operations, an output folder that exists (or Downloads), none of the fields of earlier versions (Python, AEL folder, geometry, camera profile, one dark, one flat) and the AEL folder that comes with the connector, then closes it with Cancel. The same check on a copy whose bridge entry has lost the include of its dialog fails (`ReferenceError: AELBridgeDialog is not defined`), so a broken entry file cannot pass. For a built package: `--plugin PACKAGE/pixinsight-ael --expect-root PACKAGE/pixinsight-ael/runtime`.

`VALIDATION.json` contains the gates and exact commands. A missing PixInsight executable or a failed gate makes the complete validation fail. `--skip-pixinsight` runs only direct AEL checks and is not a complete bridge validation. `--skip-captures` omits only the visual captures.

### Size and memory

`structure` was run through the bridge on a synthetic corona of 7,506 × 10,551 pixels (80 million, the size of the 2026 composites): 49 s from the click to the three result windows on an Apple-silicon Mac with 64 GB, and the three outputs equal those of `python -m ael` on the same file bit by bit (SHA-256). The peak was **30 GB of memory** (PixInsight with the image, plus the Python process that runs AEL; the terminal run alone peaks at 29 GB), so plan on that for images of this size. The filter workflow was not run at that size.

### When PixInsight does not hold the file as it is stored

PixInsight does not always read a floating-point TIFF faithfully. A file with values outside 0–1 is rescaled to exactly 0–1, `(x − min) / (max − min)`, so the view holds numbers that are not in the file; and a file whose last sample is NaN (no data in the bottom-right corner, which a registered stack often has) is read as a completely black image, with no message. AEL does not give the same result on those numbers (its structure image depends on the scale and on the zero: a plain ×0.5 changes 30,924 of the 786,816 samples of a test image).

A view that is still its file (not processed since it was opened) is therefore compared with it before anything is exported: the size, the count of samples with and without data, the smallest and largest value and the sum of the finite values must agree, and the file must not leave 0–1. If they do not, the bridge runs AEL on the file itself, as `python -m ael` reads it. It says so in the Process Console, and the receipt records the file, its SHA-256 and the reasons (`source.ael_input`, `source.file_reasons`, `input_file`). The file is never written or removed. An AEL stack (a `linear.tif` with values far above 1 and NaN outside its coverage) can thus be opened as it is, and the result is the one `python -m ael` gives on that file, which the tests check pixel by pixel. A view that has been processed since it was opened is exported, so AEL gets what you see. Only TIFF files are compared; an image from another format is exported. The filter layers take the image in the same way. The linear master is not affected: it reads its files from Python.

### Pixels without data (NaN)

AEL marks a pixel without data as NaN, and every stack that AEL writes has them outside its coverage. PixInsight keeps a NaN in the view but writes it to a TIFF as 1.0, so AEL would read a bright area where the file has none: on a real stack of 12 million pixels with 253,851 NaN samples, every sample of the three structure images differed from those that `python -m ael` makes from the file. The bridge therefore reads the positions of the view's non-finite samples and gives them to the helper, which puts them back as NaN in the temporary TIFF before AEL runs. The bridge receipt records how many there were and that PixInsight had written them as 1.0. With this, the same stack gives three structure images equal, sample by sample, to those of `python -m ael` on the file. Infinities are put back as NaN too (AEL takes both as no data).

## Automated linear-master and filter workflow

The same dialog does both. `AELWorkflowCore.jsh` and `python/ael_workflow.py` go beside the other files.

### Filter layers of the active image — validated

Choose **Filter layers and PixelMath composite**, check the image (a linear stack: an AEL `linear.tif`, or a TIFF or FITS file from any program; an alpha channel marks the observed pixels), and click **Run**. Nothing else is asked: the PixelMath composite is always built. The image is handed to AEL as for the structure image (or AEL reads its file, when PixInsight does not hold it as stored); AEL measures the geometry on it and a window shows its circle. The helper measures a display scale from observed corona pixels and generates all sixteen portable AEL filters by default (the box **All 16 filters** unticked makes only AEL's default layers, read from `ael.filterbank.DEFAULTS`: NRGF, the edge-aware WOW and ACHF 04). From the terminal, the helper also takes an AEL `linear.npy` with `geometry.json`, `valid.npy`, `coverage.npy` and `alpha.npy` beside it. It writes:

- float NPY layers and alpha arrays from AEL;
- separate 16-bit TIFF views `AEL_L_<filter>` and `AEL_A_<filter>`;
- `AEL_DISPLAY`, the display base over black with its alpha as a 32-bit float image, which is exactly where AEL starts its own composite, and an independent `AEL_COMPOSITE` duplicate;
- `pixelmath.json` and `PIXELMATH.md` with the expressions, which name the layer and alpha views directly (PixelMath symbols accept constants only);
- AEL and workflow receipts.

The default composite applies NRGF, the edge-aware WOW and isotropic ACHF 04 with their documented opacities, rounded to 8 bits as AEL and Photoshop store them. (Up to AEL 1.3.4 the default WOW layer was the bilateral one; `wow_bilateral` is still accepted as a name for the edge-aware WOW.) The other filters remain separate for manual use. PixelMath touches only the composite, never the display base or linear master, and a PixelMath run that fails stops the workflow. The synthetic validation starts from the display base and compares the PixelMath result with AEL's own composite (`ael/display.tif`); it also checks that the two starting images differ, so a PixelMath that changes nothing cannot pass. AEL composites in floating point from the 16-bit layer images and alpha and rounds once, at the end; the replay starts from the same float32 and so differs from `display.tif` only by that final rounding: 0.50 of a 16-bit step measured, gate one step. A layer with the wrong opacity (one 8-bit step) or the wrong blend mode, built in PixInsight, differs by about 150 and about 11,000 steps and fails the gate.

### Automatic linear master — validated with synthetic data

This mode reads exposure and ISO with ExifTool (from the header for FITS frames), checks one camera/ISO, registers every frame on the Sun, writes the frozen AEL stack recipe, and can continue into filter layers.

The corona is fixed on the Sun, and during totality the Moon moves across it (28.5 px in 105 s on one 2026 train). Each frame's Moon is fitted on its own limb (a fit that leaves more than three times the reference frame's residual, and over 2 px, is refused: a veiled or saturated Moon), and it says where the Sun of that frame is, give or take how far the Moon can have moved since the reference frame. Within that window the corona of the frame is correlated with the reference's: both are band-passed in the logarithm, after a 3×3 median that removes the hot pixels fixed on the sensor, at scales that follow the Moon's size (R/55 and three times that: 4 and 12 px for a Moon of 220 px, 8 and 25 px for one of 450 px), and a masked normalised cross-correlation over every shift of the window at once, in the Fourier domain, gives the peak, placed between pixels by a parabola on each axis. Each frame leaves out its own Moon plus a margin for the blurred lunar edge (6 px or 1.5 % of the lunar radius). The corona of a frame holds when that peak reaches 0.4 and the structure score reaches 0.25: the same band-pass correlated with the frame turned 90° and 270° about the Sun, which keeps the radial statistics and loses the structure, `(c − c_turned) / (1 − c_turned)`.

When every frame records when it was taken (EXIF, or `DATE-OBS` in FITS), the lunar shifts that the frames whose corona holds give lie on a line in time, because the Moon crosses the Sun at a constant velocity. A least-squares line through the reference, leaving out the frames farther than max(1 px, 3 rms) from it, gives that velocity, and each frame's Sun is its own Moon minus the velocity times its time. The frames too short for their corona (1/3200 s) are placed that way too, and one frame's error weighs little. The run stops, naming the frame, when the velocity is faster than the Moon can cross the Sun, when a frame whose corona holds lies more than 3 px from that prediction, or when the window cuts a corona's peak (the corona would make the Moon jump). Without the times, each frame is placed by its own corona, and a frame whose corona does not hold stops the run. The window is how far the Moon can cross the Sun: 0.16 lunar radii + 2 px in a whole totality (it crosses at most twice the difference of the radii, and it never looks more than about 8 % larger than the Sun), or, with the times of both frames, at most 0.65″ a second (the Moon's motion at perigee less the Sun's; the Earth's rotation only slows it) for a Moon at least 944″ in radius, plus both exposures, how finely the times are known and 2 px. The reference frame is the one of the exposure nearest the middle of the ladder on a logarithmic scale, and of those, the one nearest the middle in time. Rotation is not supported.

The dialog asks only for the frames, the output folder and, for this operation only, optional darks and flats; its experimental notice also shows only here. Neither a geometry nor a camera profile is asked for. Without a geometry, AEL measures the lunar limb on the reference frame (the first one; when its lunar disc cannot be measured, for example because a long exposure saturated it, the first frame where it can becomes the reference, and the receipt says so). Without a camera profile, each RAW file gives its levels: the black is measured on the sensor's covered border when it has one (LibRaw declares 0–96 for a Canon EOS R6 Mark III whose border reads 512), the white is the level LibRaw declares, and 85 % of the range from black to white counts as linear, as in AEL's own chain. A calibrated TIFF or FITS frame is measured: black 0, and saturation where many samples of a channel share its highest value (none when no value is shared). Either can still be given to the helper from a script or the terminal (`"geometry"` and `"camera"` in its configuration), a camera profile such as:

```json
{
  "black": 512,
  "white": 16000,
  "linearity_fraction": 0.95,
  "train": "camera and optics identifier"
}
```

A camera profile that is given holds for every frame.

**Darks and flats.** One file is taken as the master; several make the masters, in `calibration/` of the output. AEL subtracts the dark before dividing by each frame's exposure, so a dark matches one exposure and ISO: darks are grouped by the exposure their metadata record, one master dark for each exposure the frames use (the per-pixel median of up to 25 files; from more, the mean without the values beyond 3 standard deviations, in two passes that read one file at a time), and each frame takes the master of its own exposure. A frame whose exposure has no dark, a dark at another ISO or of another camera, a master dark that records no exposure for frames of several exposures, and RAW darks for TIFF frames stop the run before anything is written. A RAW master dark should read the black level: one that reads far above it is not a dark, and one kept in 0–1 (raw values divided by 65535) is brought back to the raw levels. Several RAW flats make the master flat with `ael.calibrate.master_flat` (each colour plane normalised on the central annulus, a weighted mean with rejection, the black measured on the covered border); TIFF or FITS flats are normalised in the same way and combined with the per-pixel median. Where the flat has no value (a pixel saturated or rejected in every flat, a dead pixel, under 10 % of the centre, or the last row or column of a sensor with odd sides), the master leaves that pixel without data. The frames are registered calibrated, as they are stacked. The masters must match the optical train and the native geometry (the visible sensor area of a RAW file). Cloud transmission, colour calibration and mixed-optics distortion are not inferred.

`tests/workflow_lunar_motion.py` is the gate for this registration. Between three frames the telescope drifts and the Moon moves another 1.6 and 3.2 px across the Sun (0.07 lunar radii, about one totality), always covering it. With a still Moon, a moving Moon, and a moving Moon with photon and read noise and a saturated inner corona, the worst error against the Sun is 0.035 px (gate 0.1 px), and 0.018 px with the frames 100 s apart, placed by the lunar velocity. Another corona with the Moon in the same place is refused, and the same moving Moon in frames 1 s apart too. An earlier version registered on the lunar limb and failed this test with errors equal to the lunar motion.

`tests/workflow_lunar_noise.py` is a second, separately written judge with shorter exposures (0.01–0.04 s), where the outer corona of the reference is close to the read noise, a Moon moving 4 px, and a frame of an unrelated corona with other streamers and orientation. Its noisy gate is three times the noise floor measured in the same run. The structure check of an earlier version (high-pass correlation of the fine structure ≥ 0.25) refused every good frame of this test, even frames that did not move, because at these exposures the fine structure is mostly noise; the turned-frame score passes them and still refuses the unrelated corona.

`tests/workflow_calibration.py` checks the darks and flats: one master dark for each exposure, equal to the median of its files, a master flat without a value at a dead pixel, a master equal bit for bit to the stack of the frames calibrated by hand with the same registration (and, uncalibrated, different by up to 7.9 times the median), and the five refusals. `tests/workflow_lunar_motion.py` also checks the time between frames: the same moving Moon is refused in frames taken 1 s apart and passes in frames taken 100 s apart.

`tests/workflow_synthetic.py` passes all gates: 0.025 px worst translation error (gate 0.1 px), 0.0203% median relative master difference (gate 0.1%), sixteen filters and alpha maps, and a PixelMath composite within one 16-bit step of AEL's composite (gate `1/65535`; 0.50 steps measured). The unrelated-image registration control is rejected. `tests/workflow_dark_guard.py` checks that one master dark without an exposure is refused for frames of two exposures. On real frames the corona correlation of one frame takes about 1 s for a Canon EOS 6D frame (20 megapixels, Moon of 220 px) and 5–7 s for a Sony α7 III or Canon EOS R6 Mark III frame with a Moon of 450–480 px (Apple silicon). Windows and Linux remain untested.

## Limitations

- **The registration on the Sun has not been checked frame by frame against an independent registration.** On real frames it places every frame's Sun from its own Moon and the lunar velocity. On 15 Vixen R6 III frames of 2026 (1/3200 s to 10 s) the frames whose corona holds lie within 0.45 px (rms) of the Moon's straight path, and the velocity, 0.2713 px/s, is the one the ephemeris gives (28.5 px in 105 s, 0.271 px/s). On 15 Canon EOS 6D frames of 2024 (3.5 minutes) they lie within 0.9 px, at 0.42 lunar radii per 1,000 s, close to what the duration of totality at Mazatlán implies (about 0.41). On 13 Sony α7 III frames of 2024, which span only 26 s, they lie within 0.55 px. The same 6D frames with their times shuffled are refused. The registration this replaces, a Gauss-Newton fit of the logarithm of the corona, put the Moon up to 12 px off its path on those 6D frames and 13 and 33 px off on three of them, with frames that passed its structure check.
- The geometry measured on the image places the Sun at the centre of the measured circle, with its radius. On a single frame that circle is the Moon, and the true Sun can be off by up to the difference of the radii (29 px on the 2026 frames); its radius is the Moon's, 3–8 % larger than the Sun's. Type the Sun's values when you know them. The detection was measured on real stacks and RAW frames of 2024 and 2026 and on 660 synthetic eclipses; it misses some Moons of 25 px radius (wide-angle frames) and every frame whose lunar disc is saturated. Measure it on the linear image when you can: on an image stretched for display the limb comes out inside the true one (62.1 px instead of 63.6 px on the demonstration image, against 63.35 px on its linear version), while the centre stays within 0.02 px.
- Tested only on macOS (Apple silicon) with PixInsight 1.9.4 and AEL 1.4.0. Windows and Linux have not been tested; the interpreter search lists Unix-style folders.
- Python must be installed separately (the package carries AEL, not Python or its dependencies); this is not a native C++ module.
- `structure` and `polar` are covered by the original bridge. The complete master/filter workflow is validated with synthetic data only; real eclipse data require separate validation.
- The automatic master holds every frame's luminance in memory at once: plan on several gigabytes for dozens of full-size RAW frames (two Canon EOS R6 Mark III frames with 39 darks and 10 flats peaked at 14 GB, in 4.5 minutes).
- ICC profiles are read from the source file and copied unchanged to the temporary TIFF. An unsaved image, or a profile assigned only in memory after reading the file, cannot be verified or preserved reliably by this prototype. The receipt records the ICC origin and byte counts.
- `polar` expects display-range data in [0, 1]. `structure` expects a linear composite with valid geometry and enough outer field for its sky model.
- The connector has not been signed or packaged for automatic updates.
