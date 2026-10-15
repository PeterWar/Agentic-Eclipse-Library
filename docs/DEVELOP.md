# Stacking, extinction and filter layers

`ael stack` and `ael filters` turn a **declared recipe** into reproducible files.
They do not infer the observing site, alignment, linearity ceiling, colour calibration
or cloud transmission from a folder of RAWs. An agent measures those first and writes
them into JSON. All paths in a recipe resolve relative to that JSON, not the shell's
working directory. Every output directory must be new.

```sh
pip install ".[raw,photoshop]"
ael selftest
ael stack --config stack.json --out stack_run/
ael extinction --config extinction.json --out ext_run/   # optional: low Sun
ael filters --config filters.json --out filter_run/
```

## Stack recipe

See `examples/stack_config_template.json`. Use totality frames from **one optical
train and one ISO**, with a registration measured on coronal structure after removing
the radial gradient. A different optical train requires a calibrated distortion
model before combining it; a free affine is not a substitute.

Each frame supplies:

| Key | Meaning |
| --- | --- |
| `path`, `kind` | RAW (`raw`, default), Bayer NPY/FITS/TIFF (`bayer`), or linear native RGB array (`rgb`) |
| `pattern` | For `bayer` only: a 2x2 array of R/G/B letters with two G sites |
| `iso`, `exposure_s` | Declared ISO and positive exposure duration; exposure is divided exactly once |
| `black`, `white` | Measured native DN, scalars or native-shaped arrays; never guessed from libraw |
| `linearity_fraction` | Linear ceiling as fraction above black, default .95; **measure it for your camera** |
| `reference_to_input` | 2x3 affine, **reference pixel centres → native input pixel centres**, full resolution |
| `moon_xy`, `moon_radius_px` | Moon geometry of this exposure in its native visible sensor coordinates |
| `dark` | Optional pedestal-inclusive master dark in native DN, matched to exposure and ISO; default black |
| `flat` | Optional positive, normalised flat in native geometry; divided before resampling |
| `flux_scale` | Measured positive scalar relative throughput, default 1 |
| `transmission` | Positive native-shaped multiplicative transmission field, or scalar; default 1 |
| `background` | Native DN/s additive background **after dark/flat**, default 0 |
| `cirrus_fraction` | Measured fractional RMS of the coarse cloud structure, default 0 |

RAW reads use the visible area reported by rawpy; no automatic crop is made.
Coordinate (0,0) is the centre of the first visible pixel. For registration measured
on 2x2 superpixels, convert once with `ael.stack.full_resolution_affine`. It includes
the .5-pixel centre convention; applying another -.5 would shift the result.
`geometry.shape` is the native reference shape. Its solar centre must be independently
measured or come from ephemerides; do not silently use the Moon's current centre.

By default the canvas is the union of complete registered sensor footprints.
Set `stack.canvas: "reference"` to keep the full native reference rectangle with origin (0,0);
the output geometry retains its native centres. This does not invent coverage in gaps.
Choose the field with the owner before processing an existing image. CFA planes are
interpolated directly to it, once, without demosaicing first. The two green planes
are averaged with their own support. At each pixel, all colours use **one taper**,
set by the raw plane nearest the linear ceiling. The taper is outside the
normalised interpolation. No reconstruction is made where every exposure clips.

`stack` settings:

- `canvas`: `"union"` (default) or `"reference"`; no inferred crop or new field choice.
- `taper_start`: begin saturation taper at this fraction of the linear ceiling (.8).
- `moon_guard_px`, `limb_fade_px`: exclusion and weighting ramp outside each Moon
  (2 and 4 native pixels by default). These are data-dependent recipe choices.
- `hot_pixels`: optional `{ "enabled": true, "dithered": true, "threshold": 6,
  "persistence": .8, "read_noise_dn": 3, "gain_e_per_dn": 1 }`. Only enable for
  at least three dithered frames. Signed persistent residuals are normalised by
  local noise; a fixed star in an undithered sequence cannot be distinguished.
- `band_sigma_px`: 0 for the ordinary exposure-weighted stack; positive (e.g. 3)
  for two bands. Fine detail uses exposure weights, coarse structure uses an
  approximate inverse photon/read/cirrus variance. The split is a Gaussian low
  pass and its complementary residual, not an extra sharpening filter.
- `gain_e_per_dn`, `read_noise_dn`: measured sensor noise parameters for two bands.
- `clouds: true`: refuses a scalar-only recipe. Supply frozen **spatial** transmission
  maps, background corrections and cirrus RMS for every frame and enable two bands.
  AEL does not fit those maps or claim an automatic cirrus correction. For controls
  that change the saturation ceiling, keep the maps frozen. Independent witnesses
  must fit their corrections independently, not against a shared total stack.

Outputs: `linear.npy` and float32 `linear.tif` (DN/s sensor RGB); `valid.npy`;
`support.npy` (sum of usable interpolation support, without exposure/limb taper);
`coverage.npy` (geometric sensor coverage, independent of saturation);
`weight.npy`; `alpha.npy`; shifted `geometry.json`; and a hashed `receipt.json`.
There is no formal uncertainty map: the two-band variance is a weighting model,
not a propagated absolute-photometry uncertainty budget.

## Extinction recipe (optional)

With a low Sun the air mass changes across the field and the corona carries a dipole of
atmospheric origin (in 2026, about ±9 % at 1.5 R☉ and ±23 % at 4 R☉ around the Sun's own
line of sight). `ael extinction` corrects it on the **linear stack, after subtracting the
sky**: `(I − sky)·10^(0.4·k·(X − x_ref))`. Run it between `stack` and `filters`, and rebuild
every filter layer from its output; a correction applied to a finished image is a patch.
See `examples/extinction_config_template.json`.

| Key | Meaning |
| --- | --- |
| `input`, `geometry`, `valid` | The linear stack, its geometry (with `arcsec_per_px` and `north_deg` when the air mass is computed) and its valid mask |
| `sky` | Exactly one of `{"fit": {"r_min_rsun": 8, "order": 1}}` (robust polynomial per channel, far from the Sun), `{"array": "sky.npy"}`, or `{"value": number or one per channel}` (0 if already subtracted) |
| `airmass` | `{"site": {...}, "time_utc": "..."}` (astropy), or `{"sun_altitude_deg": h, "zenith_pa_deg": q}` / `{"sun_altitude_deg": h, "zenith_image_deg": a}`, or `{"array": "airmass.npy"}`. Optional `north_px`/`east_px` (image pixels per arcsecond towards north and east, from a plate solution) or `arcsec_per_px` |
| `site` | `lat_deg`, `lon_deg` (east positive), `height_m`, `pressure_hpa` (null: standard atmosphere at that height), `temperature_c`, `relative_humidity`, `wavelength_um` |
| `k` | Extinction coefficient in mag per air mass: one value (achromatic) or one per channel. **Measured, never assumed** |
| `x_ref` | Reference air mass: a number (e.g. where the photometric zero point was evaluated) or `"sun"` |
| `keep_sky` | Also write `corrected_with_sky.npy`: the corrected corona plus the same sky model, for `ael filters` |

The top-level keys `sky`, `airmass`, `k` and `x_ref` are required and have no default.
Sub-keys that do default (`sky.fit.order` = 1; the site's height 0 m, standard-atmosphere
pressure, 10 °C, 0 % humidity and 0.55 µm) are recorded in the receipt; give measured values
where you have them. A sky array may be (H, W) or (H, W, C); a sky value is one number or one
per channel. Every input is checked and every output computed before the output directory is
created, and an existing directory is refused. Outputs: `corrected_net.npy` (sky-subtracted, NaN outside data), optionally
`corrected_with_sky.npy`, `airmass.npy`, `factor.npy`, `sky.npy` and a hashed `receipt.json`
with the air-mass and factor ranges, the factor at 1.5–4 R☉ and the sky-fit details.
Pixels whose line of sight is below the horizon have no air mass and stay NaN.

Conventions: `zenith_pa_deg` is measured on the sky from celestial north through east
(`ael.extinction.solar_horizontal` gives it, with ICRS north); `zenith_image_deg` on the
image, clockwise from up. The image is treated as a gnomonic projection of the apparent sky
centred on the Sun; with a plate solution fitted on stars (`airmass_map_from_wcs`), pixels
map to true positions and refraction is applied point by point. The two routes differ by
the differential refraction (about 0.8 % of the vertical offset at 9° altitude).

Measuring `k`: `ael.extinction.dimming_k` on pairs of registered frames with the same
exposure and ISO, far apart in time. It refuses air-mass differences below 0.02. Quote the
scatter between pairs, not the fit error. It reads any change of transparency as extinction.

Sky and extinction are degenerate. Fit the sky where the corona is negligible; check the
result against a reference without atmosphere with `ring_dipole`, `k_nulling_dipole` and
the gate `k_consistency` (one `k` for every ring, no radial trend). A pass is consistency,
not a measurement of `k`, and says nothing about the absolute level: estimate the corona
left in the sky region by passing a corona model through the same sky fit, and declare it.
See `docs/FIELD_LESSONS.md`.

## Filters recipe

See `examples/filters_config_template.json`. Input must be linear. Supply the
stack's geometry, valid mask, **geometric** coverage and base alpha. Optional
`exclude` masks remove stars or known defects from the filter **input**, never
fill their pixels. `min_coverage` is a threshold on geometric coverage; never feed
an unsaturated-frame count into it.

`white_balance` contains three linear ratios. `camera_to_linear_rgb` is an optional
3x3 colour matrix applied after those ratios. Default identity leaves sensor colour;
it must not be called calibrated sRGB. Optional `icc` embeds a matching profile in
the PSB. `display.scale` (positive luminance scale in input units) and `display.asinh`
(positive, default 10) declare the display stretch. `display.highlight_ceiling` is positive and at most `1 - 1/65535`,
default .9, retaining at least one 16-bit code of headroom. After the per-channel asinh, a shared factor maps the RGB maximum `m` to
`ceiling * (1-exp(-m/ceiling))`. This prevents positive hard clipping while preserving
the asinh RGB ratios. It never changes the linear input. The receipt records effective
parameters, negative RGB counts, clipping checks and the separate linear-reference scale.
This changes the 1.2.0 display recipe: compare full canvases before adopting it for an existing image.

The default visible layers are NRGF (Multiply, .39), bilateral WOW (Overlay, .37),
and isotropic ACHF 04 (Overlay, .08). These opacities are starting points. Override
`visible` and `opacities`, or request `"filters": "all"` for sixteen layers:

| Family | Identifiers |
| --- | --- |
| Radial normalisation | `nrgf`, `nrgf_log` |
| Radial histogram equalisation | `rhef`, `rhef_upsilon`, `rhef_local60`, `rhef_local30` (any of them with `upsilon_curve=(low, high)` since 1.3.2) |
| Angular high-pass | `achf_angular`, `achf_angular4`, `achf_angular8` |
| Isotropic multi-scale high-pass | `achf_iso_01`, `achf_iso_04`, `achf_iso_05`, `achf_iso_06` |
| Local/wavelet normalisation | `mgn`, `wow`, `wow_bilateral` |

These are portable parameterisations, **not a byte-identical reproduction** of the
historical sixteen-layer project. In particular `nrgf_log` uses only measured log
luminance rather than extrapolating the historical inward radial statistics; local
RHEF interpolates measured log-intensity quantile functions in radius and angle before inversion; bilateral WOW has paired observed taps and a
noise floor. The general recipes do not include the historical per-image resolution
map or hand-made layer finishing. Ordit/Trama need independent registered witnesses
and are not included in this single-stack command.

NRGF (since 1.3.2) measures each annulus about a continuous profile: a node at the mean
radius of the annulus' pixels with the local slope and curvature removed, a cubic spline
between nodes, and the spread interpolated without overshoot; see `docs/VALIDATION_1.3.2.md`. RHEF uses 257 quantiles per populated radial/sector cell, with
constant distributions at .5 and no output outside positive observed data. Sparse
annuli do not become valid by borrowing a neighbouring cell. These statistical
interpolations do not smooth the image. See `docs/FIELD_LESSONS.md` for the ring
negative controls, injection limits and the rejected alternative.

Before isotropic filtering, a **smooth cubic spline in ln radius** is fitted to log
luminance and subtracted. This prevents the one-sided lunar-edge kernel from turning
the radial brightness slope into a false ring or a dipole when the Moon is off-centre.
Ring medians are fit observations, not a staircase subtracted from the image.
Multiply layers use the **same geometric alpha ramp as the base** on observed data,
preventing the earlier disappearance of darkening from making a bright rim.

Outputs: float layers with NaN outside observed data, their alpha arrays, a full
canvas preview, display TIFF, and a receipt of actual operator/display parameters.
`photoshop: true` adds a new layered 16-bit `corona.psb` and pixel-by-pixel verification.
The hidden linear-reference layer has its own recorded scale, with the positive
observed maximum at .98. Negative colour-matrix values are clipped only for 16-bit
representation; the signed float input remains the HDR authority. The application is **never opened automatically**. The
receipt distinguishes file roundtrip from a native Photoshop check.

No lunar texture, saturated corona or stars are invented. A missing region remains
empty/black in the preview. Review the full field and the limb at native resolution
before choosing the presentation. A passing software test is not independent
scientific validation of an image or a guarantee of no artefacts.

Field guidance on astromodified colour, exposure metadata, earthshine candidates and
partial dust-response estimates is in `docs/FIELD_LESSONS.md`. AEL does not infer
a universal white balance or automatically remove dust or recover lunar relief.

For a preferred existing Photoshop edit with independently adjustable filters, see
the [existing-edit case study](EXISTING_EDIT_CASE_STUDY.md). It separates appearance,
measured registration and native-save integrity. Its image-specific settings are
not additions to the default linear recipe.
