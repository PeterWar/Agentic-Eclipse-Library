# Coronagraph method notes

Use the maintained `ael.coronagraph` API and its docstrings in `runtime/ael/coronagraph.py` for exact
parameters. These instructions describe comparisons; they do not supply the user's calibration or data.

## References and geometry

- K-Cor: level-2 polarised-brightness FITS from MLSO/HAO with their stated units. Display GIFs are not a
  substitute for linear pB. Reference: K-Cor Team (2013), DOI 10.5065/D69G5JV8.
- LASCO: level-0.5 FITS around the observation time, with the appropriate vignetting file and daily
  exposure-factor table for brightness. A C3 comparison also needs a justified background. Confirm which
  filters/polarisation sequences actually exist for the chosen date.
- AIA: suitable time-matched, calibrated solar images and their WCS. EUV structure and prominence
  positions can be compared; EUV intensity is not the visible-light brightness of the corona.

The observing date and instrument metadata determine the inputs. Ask before an unrequested download;
keep the files and hashes as references outside the photograph's processing inputs.

Each image needs its own `SolarFrame`. A stellar plate solution supplies solar centre and the image
offsets towards north and east. Preserve both affine axes, including their non-orthogonality. Derive the
Sun-Moon offset at the measurement time rather than treating the moving lunar centre as the Sun's centre.
For K-Cor/AIA use supported helioprojective WCS. LASCO level-0.5 headers need the appropriate map conversion;
do not silently assume an Earth observer for SOHO. Check its apparent solar radius at L1.

## Structure

Unroll the separate frames at the same physical solar radii. Bin sharp inputs where required to compare
similar resolutions. Print the frame scale and axis angle and inspect unrolled images before measuring.

Read the zero-rotation correlation, angular shift, null mean/spread/maximum and fine-detail result.
Broad streamer patterns can correlate strongly even under null rotations. Require the fine-detail result
to beat its own null. An optimum at the search boundary is not a measured orientation.

The rotation null cannot see a mirrored image: a reflection plus a rotation can fit the broad two-lobed
corona. Start from the optics (an odd number of reflections mirrors the image) and from the processing
(some software writes bottom-up frames; `ael` reads FITS rows as stored). Without stars, a landscape or an
annotated frame, scan both mirror states (`ael.coronagraph.scan_mirror`, or `"scan_mirror": true` in the
recipe), decide on the fine detail and report the scan's margin. Without shared fine detail about 1 in 5
decided answers was wrong in synthetic tests; a second, independent direction makes a decided parity surer
and is optional. The scan has been validated against LASCO C2 only.

Mask the occulter, labels, pylon and unsupported pixels; never fill them. A pylon mask follows a measured
contiguous dark region rather than globally rejecting all dark coronal structure. Exclude cells touching
the lunar-motion mixing band, gaps or prominences from a brightness analysis. Choose usable radii from
the actual validity and noise of each instrument, not fixed 2026 numbers.

## Brightness

The user's image needs a linear sky subtraction, differential-extinction treatment where needed, and
a photometric zero point with uncertainty. A fitted sky can absorb real corona or extinction. Test that
bias and declare the degeneracy; a consistent dipole is not an independent extinction measurement.

`kcor_total_msb` converts pB through a density/polarisation model and adds the declared F-corona model.
pB/p(r) alone is K, whereas a visible-light photograph sees K+F. Vary supported density choices and F
scales to report model sensitivity. Reject unreliable or negative pB regions.

For LASCO C2, the calibrated level follows `(DN-bias)/(exposure*exposure_factor) * vignetting * factor`.
Keep `colaninno_howard_2015` and `solarsoft` results distinct. The maintained code calibrates Orange-filter
data; summed pixels and polariser frames require their explicit conventions. Do not force the alternatives
to agree. Use bracketing exposures where available and retain the time mismatch as a limit.

Use `cell_medians`, `level_ratios` and `ratio_band` with the declared exclusions and uncertainties. A
fractional error band on a reference is inverted when expressed as ours/reference: use the API rather
than copying percent bounds unchanged. Report compatibility ring by ring, with the calibration named.

Deliver receipts and diagnostic views with structure and brightness as separate conclusions. A match
within a limited radial range says nothing about unsupported pixels, untested scales or absolute accuracy
outside the calibration's uncertainty.
