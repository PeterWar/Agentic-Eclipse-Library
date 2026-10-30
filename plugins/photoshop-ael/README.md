# Adobe Photoshop connector for Agentic Eclipse Library

Choose the RAW photos of a total solar eclipse, and optionally their darks and flats. AEL stacks them into one image and opens it in Photoshop as a layered 16-bit PSB: the display base and AEL's default filter layers (NRGF, WOW edge-aware and isotropic ACHF 04), each with its blend mode and opacity, ready to adjust.

There is nothing else to set. Everything else is measured on the files and written in a receipt.

## Use

1. In Photoshop, choose **File > Scripts > Browse…** and select `AELPhotoshop.jsx`.
2. **Totality RAW photos — Choose…**: select every RAW photo of the totality (all exposures together). Photos of the partial phases, darks or flats among them are recognised and left out.
3. **Darks and flats (optional) — Choose…**: select the dark and flat frames of the same camera, if you have them, mixed as they are.
4. Press **Make the image**. A progress window shows what AEL is doing. **Stop** asks AEL to stop at its next step (whether Photoshop delivers the click while a script runs has not been tested automatically).

When it finishes, the layered image opens and a message says how many photos were stacked, which were left out and why, and where everything was saved: a new folder in `Pictures/AEL Photoshop/` with the PSB, the linear master (32-bit float TIFF, no data = NaN), a preview, `AEL receipt.json` and the recipes in `details/`.

## What AEL works out by itself

- **Which photos are totality frames.** A photo is a totality frame when AEL finds the dark lunar disc with a bright ring around it, or, in a long exposure whose lunar disc is saturated by scattered light, when its corona registers on the reference. Partial phases are left out. Photos where the photosphere shows (Baily's beads, the diamond ring) are left out too: they saturate beside the lunar limb, within 90° of position angle, at exposures so short that it takes more than twice the brightest light any clean photo shows there. So are photos whose light does not follow the others (a photometric gain beyond 2×, or more than 20 % scatter around the common corona): sunlight scattered near a contact, or a cloud.
- **One camera, one ISO.** If photos of several cameras or ISO values are chosen, the camera and ISO with the most photos are used and the others are listed as left out. Each optic needs its own distortion model before images of two optics can be fused, so they are never mixed.
- **Darks and flats.** Each calibration file is classified as a dark or a flat from its preview, then checked on its raw data. Darks are combined by exposure (median, up to 32 per exposure) and each photo gets the dark of its exposure and ISO; a photo without one is calibrated with the black level. Flats are combined with AEL's master flat (each Bayer plane normalised, up to 48 frames).
- **Black and saturation levels.** The black level is the mean level of the masked border of the sensor when the file has one (LibRaw does not know every camera: for the Canon EOS R6 Mark III it declares 0–97 where the sensor reads 512.2), otherwise LibRaw's. The saturation level is the plateau where the sensor clips. The top 15 % of each RAW range is not used, because some sensors stop being linear well before they clip; the shorter exposures cover it.
- **The registration on the Sun.** The corona is fixed on the Sun and the Moon moves across it. Each photo is registered on the corona of a reference photo: a band-pass of the logarithm of the corona between 1.36 and 3 solar radii (saturated pixels, the photo's own Moon and pixels without data left out), first by cross-correlation and then by Gauss-Newton for a shift and a turn of the field about the Sun (a mount that does not follow the sky turns the field during the totality). Two checks: the result must not depend on its starting point, and the coronal structure must match better than the same photo turned by 90° and 270°. A long focal length is registered at a reduced scale, where the Sun is about 240 pixels across its radius. The lunar limb of every photo is measured to about a tenth of a pixel. Over a totality the Moon's motion against the Sun is a straight line in time, so that line is fitted on the photos registered on the corona, the turn of the field is fitted as a straight line in time too, and every photo is placed by its own lunar limb minus the line. A photo that the corona places far from the line is left out. When the Moon and the corona disagree by more than a pixel on that line, the data cannot tell which is biased: each photo registered on the corona keeps its own registration, a photo between two of them follows the lunar track measured on its neighbours, and a photo before the first or after the last stays out. Without capture times, or with fewer than three photos on the corona, the corona registration is used as it is.
- **One sky for all photos.** Thin clouds or haze can change the light during a totality, and exposure times are not exact. AEL measures one photometric gain per photo where it and the others have good unsaturated data (a coarse grid of radius and position angle around the Sun, through each photo's final placement, fitted by alternating medians with the reference fixed). What the gains leave unexplained is the sky's consistency. Above 3 %, the sky changed: the gains go to the stack (`flux_scale`), each photo's weight fades over the top half of its range instead of the top fifth, so that the edge where an exposure saturates leaves no step, and the closing message says so. Under a clear sky the nominal exposure times are kept: there the gain fit carries more bias of its own (the blur of the inner corona, the faint sky of the long exposures) than the shutter carries error.
- **The Sun.** The Sun's centre is the Moon's centre at the middle of the photos, on the fitted lunar motion. That is exact when the photos span the totality symmetrically and the site is on the central line; elsewhere the true centre is off by up to the difference of the radii, sideways to the Moon's motion. The Sun's radius is the lunar radius over the eclipse's ratio of apparent diameters (a table of total eclipses from 2008 to 2035); when the camera's date matches no eclipse of the table, the lunar radius is used. North, parity and plate scale are not known.
- **Colour.** The camera's daylight white balance and its camera-to-sRGB matrix, derived from the colour matrix LibRaw holds for the camera. The corona keeps the colour that a camera set to daylight records: nothing is neutralised. The matrix is the one of the camera as it left the factory: a camera modified for astronomy (its infrared filter replaced) comes out reddish, and its colour has to be set by hand in Photoshop.
- **The filters.** AEL's default layers with AEL's default opacities, over a display base scaled on the corona between 1.1 and 2 solar radii. The band that the Moon swept across the corona during the photos enters no filter: there the stack mixes different photos.

## Requirements

- macOS with Adobe Photoshop 2026 (tested with 27.11.0).
- Python 3.10 or later with these packages, installed once from the Terminal:

```bash
python3 -m pip install numpy scipy opencv-python-headless pillow tifffile imageio psd-tools rawpy exifread
```

  `exifread` is optional: without it, AEL cannot name the camera or read fractions of a second in the capture times.
- The connector finds Python by itself: the Python that worked last time, `AEL_PYTHON`, `python3` and `python3.N` in `/opt/homebrew/bin` and `/usr/local/bin`, virtual environments in `~/.venvs`, `~/.virtualenvs`, `~/venvs`, `~/venv` and `~/.venv`, pyenv, conda, and `/usr/bin/python3`. The first one that runs AEL and has the packages above is used. If none does, the message lists every Python tried and why it failed. No external program is needed: exposure, ISO and capture time come from LibRaw (rawpy) and the EXIF.
- Memory: a run keeps one photo at a time, plus the stack. With 24–42 megapixel cameras, plan for 8–16 GB of free memory and 1–3 minutes per 10 photos.

## Folder

Keep `AELPhotoshop.jsx`, `AELPhotoshopCore.jsx`, `AELPhotoshopDialog.jsx`, `python/` and `runtime/` together. `tools/build_package.py --out NEW_FOLDER --no-demo [--zip FILE]` writes such a folder with the AEL engine of this checkout under `runtime/ael`, checked byte by byte, and `runtime/VERSION.json`.

## Tests

- `tests/run_photoshop_raw.py --plugin photoshop-ael --raw RAWS.txt [--calibration CALIBRATION.txt] --output NEW_FOLDER` runs the connector in Photoshop the way a person does: the entry script and the dialog as they are, with the dialog window, the file chooser and `alert()` replaced by test doubles that press the dialog's own buttons and keep the messages. The progress window, the Python run, opening the PSB and Photoshop's own reading of its layers are the real ones. It checks the closing message, that exactly one PSB opened with the layers AEL wrote, 16 bits per channel, the PSB's SHA-256 against the receipt, and that the connector's folder is unchanged. Only documents the test opened are closed.
- The older bridge tests (`run_tests.py`, `run_package_tests.py` and the workflow tests) cover the functions the dialog no longer offers: filters, structure and polar from an open document, and the experimental master of `ael_workflow.py`.

## Limitations

- Tested on macOS only. Windows is untested.
- One camera and one ISO per run. Each photo is placed by a shift and a turn of the field: optical distortion, which changes as the image drifts across the sensor, is not corrected.
- Without darks, hot pixels stay in the stack.
- The Sun's centre and radius are estimates (see above); the receipt says how each was obtained.
- The connector has not been signed, packaged for automatic updates or published.
