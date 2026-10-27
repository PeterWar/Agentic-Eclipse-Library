---
name: coronagraph-comparison
description: >-
  Check a total-solar-eclipse image against independent instruments that saw the same corona — the K-Cor
  coronagraph (Mauna Loa), SOHO/LASCO C2 and C3, SDO/AIA — with the Agentic Eclipse Library's
  `ael.coronagraph`: STRUCTURE (are the rays and streamers where the instrument sees them? angular profiles
  ring by ring, a null from large rotations, fine detail below 12°, orientation, mirror state, prominences) and
  BRIGHTNESS in mean solar brightness (MSB, B/B☉) against K-Cor (K + F corona, never pB/p alone) and
  LASCO C2 (both published calibrations), judged against the photograph's own asymmetric uncertainty.
  Use it for "compare with SOHO / LASCO / SDO / K-Cor", "is my processing faithful?", "validate the
  corona", "absolute calibration", "mean solar brightness", "B/B☉", "radiometric calibration", "MSB map",
  "is my image mirrored?", or to judge such a claim made by someone else.
---

# Comparing an eclipse image with coronagraphs

What this skill does: it lets an agent say, with numbers and their limits, whether a processed or calibrated
eclipse image agrees with instruments that observed the same corona from space or from another site. It was
built on the 12 August 2026 eclipse (research notes 180 and 185; code in `3-RECERCA/tools/comparacio_sdo_lasco_20261001/`
and `3-RECERCA/tools/msb_calibrat_20261011/`), and turned into tested functions in `ael/coronagraph.py`.

Read the whole file before downloading or running anything. Run `python -m ael selftest` first.

## 0 · Two questions, never mixed

1. **Structure: where are the rays?** Each image is unrolled in its *own* solar coordinates, normalised
   radius by radius, and its angular profile in a ring is correlated with the instrument's. This compares
   *angles*. A radial tone curve `a(r)·I + b(r)` passes it unchanged, so a good structure result says
   nothing about brightness, and it does not exclude local artefacts.
2. **Brightness: how bright is it, in MSB?** Only for a *linear*, sky-subtracted and photometrically
   calibrated stack. A display image, a filtered layer or a JPEG cannot be compared in brightness.

The instrument is a **judge, not a source**: no pixel of K-Cor, LASCO or AIA ever enters the photograph.

## 1 · Data (ask the user before any download)

Downloading is an action the user must approve; say what, from where and how large (in 2026 it was 30 MB
for structure and 33 MB for brightness). Keep the files with a `SHA256SUMS.txt`, never inside the product.

| Instrument | What to take | Notes |
|---|---|---|
| K-Cor (MLSO, HAO) | Level-2 pB FITS (`*_kcor_l2_pb.fts.gz`), the 15 s frames inside totality, from `https://mlso.hao.ucar.edu/hao/acos/YYYY/MM/DD/` | `BUNIT` is "Mean Solar Brightness". Cite: K-Cor Team 2013, doi:10.5065/D69G5JV8. The public GIFs are 8-bit and gamma-encoded: structure only, never brightness |
| SOHO/LASCO C2, C3 | Level 0.5 FITS just before and just after totality (NRL) | Plus `c2vig_final.fts` and the day's exposure-factor table `c2_expfactor_YYMMDD.dat` (SolarSoft, `.../solarsoft/soho/lasco/idl/expfac/data/YYMM/`). C3 needs the monthly background to be clean |
| SDO/AIA | Synoptic level 1.5 (1024 px) at 211/193/171 Å for the low corona and 304 Å for prominences (Stanford JSOC) | Structure and prominence positions only |

⚠️ LASCO C2 has made **no polarised sequences since 29 August 2025**: total brightness only.

## 2 · One solar frame per image

Everything goes through `ael.coronagraph.SolarFrame`: Sun centre, and the pixel offsets of 1 R☉ towards solar
north and solar east, as seen by *that* observer.

- **Your image.** From your plate solution (stars): `SolarFrame.from_celestial_plate(centre, R☉″, N_px_per_arcsec,
  E_px_per_arcsec, P)`, with P the solar P angle at mid-totality. From an `ael` geometry:
  `SolarFrame.from_geometry(geometry, P)` (P is required: in August it is about 15°). A plate solved under a
  low Sun is **affine** (2026: north and east
  90.43° apart); never convert with a pure rotation, which moved points 3 px at the limb and 20 px at 6 R☉.
- **The Sun's centre in your image** is not the Moon's. In 2026: the measured lunar centre minus the
  topocentric Sun–Moon offset from an ephemeris (DE421) at the instant the Moon was measured.
- **K-Cor level 2, AIA level 1.5:** `SolarFrame.from_wcs_header(header)` (helioprojective axes; R☉ from
  `RSUN_OBS`).
- **LASCO level 0.5:** the header is not helioprojective. With sunpy, take the pixels of (0, 0), (0, +1000″)
  and (+1000″, 0) in the map's frame and call `SolarFrame.from_pixel_points(c, n, w, 1000, R☉_SOHO)`, with
  **SOHO's** R☉ (`rsun_arcsec(distance_au)`; SOHO is at L1 and sees the Sun about 1.1 % larger). sunpy may
  assume an Earth observer for these files.
- Check every frame: print `rsun_px` and `axis_angle_deg`, and look at one unrolled view of each image before
  trusting a number.

## 3 · Structure

```
python -m ael coronagraph --config coronagraph.json --out new_dir/   # examples/coronagraph_config_template.json
```

or in Python:

```python
from ael import coronagraph as cg
radii = np.geomspace(1.05, 6.3, 420)
ours = cg.unroll(lum_binned, frame_ours.scaled(1/2), radii, supersample=2)   # bin a sharp image first
kcor = cg.unroll(pb_mean, frame_kcor, radii)
res_k = cg.compare_structure(ours, kcor, [(1.15, 1.30), (1.30, 1.50), (1.50, 1.75), (1.75, 1.98)])
c2 = cg.unroll(c2_dn_per_s, frame_c2, radii)              # no vignetting correction here: the pylon stays dark
pylon = cg.dark_sector(cg.nrgf_rows(c2), radii, (2.5, 6.0), seed_pa_deg=320)   # seed found by eye
res_c2 = cg.compare_structure(ours, c2, [(2.4, 2.8), (2.8, 3.3), (3.3, 4.0), (4.0, 5.0), (5.0, 6.0)], exclude_ref=pylon)
scan = cg.scan_mirror(ours, c2, [(2.4, 2.8), (2.8, 3.3), (3.3, 4.0), (4.0, 5.0)], exclude_ref=pylon,
                      frame0=frame_ours, p_angle_deg=P)   # scan["parity"]: "same", "opposite" or "undetermined"
```

- **Rings.** K-Cor from 1.15 R☉ (stay outside the lunar-motion band) to about 2; C2 from 2.4 to 6; C3 from 4,
  and beyond ~7 R☉ only with the monthly background.
- **Read** `rho_0` (no rotation), `shift_deg` (orientation), the null (`null_mean`, `null_sd`, `null_max`) and
  `fine_detail`. Whole profiles share the broad two-lobed shape of any corona: far out the whole-profile null
  reaches 0.9, and only the fine detail discriminates. Agreement = `rho_0` above `null_max`, in the fine detail.
- **Mirror state (parity) first.** The rotation null (30–330°) holds rotations only, so it cannot see a mirrored
  image: a reflection plus a rotation can fit the broad two-lobed shape and beat that null in every ring. Camera
  software can deliver bottom-up frames, so never take `mirrored=False` for granted on a new camera. Take the
  parity from stars, a landscape or an annotated frame. Without them, run `scan_mirror` against C2, or add
  `"scan_mirror": true` to the recipe (gate `parity`: "same", "opposite" or "undetermined"). It scans both mirror
  states and every rotation and picks each state's rotation on the fine detail. It keeps a state only if its best
  mean fine-detail ρ beats the other state's best by ≥ 0.15, beats its own best rotation ≥ 30° away by ≥ 0.15 (a
  corona symmetric under 180° has two peaks), and its residual rotation stays within ±2° in every ring. Otherwise it
  answers "undetermined", a frequent answer: find another direction. Never decide the parity on the whole profile.
- **Evidence for the parity.** Field case, Edu (@edu27), 2026, frames from an astro camera that came out mirrored:
  against C2 the whole profile preferred the unmirrored image at north 91° (ρ 0.83), and `compare_structure` there
  gave `rho_0` 0.73–0.87 with a null fraction of 0.000 in every ring. Its fine detail was 0.36–0.40, with a
  residual rotation drifting from −3° to +6°; the mirrored solution gave 0.68–0.81 at 0.0–0.5°. On the 2026 MSB
  map the whole profile chose the right parity with the `dark_sector` pylon mask (0.94 against 0.69; 0.77 against
  0.65 without the extinction correction). With a narrow pylon mask (±6°) and no extinction correction it chose
  the mirror, 0.67 against 0.50, above its rotation null in all four rings (2.4–5 R☉). There the mirror's fine
  detail was 0.43 / 0.25 / 0.19 / 0.30, with a residual rotation from +1° to +9°; the right parity gave 0.90 /
  0.84 / 0.76 / 0.56 at −0.5° to +0.5°. The scan kept the parity of the star plate against both C2 images with
  both masks, with and without the extinction correction (margin 0.41–0.53), and found the mirror when the map
  was flipped (0.41–0.54).
- **The scan can be wrong.** In synthetic nulls without shared fine detail (asymmetric corona, ±20 % uncorrected
  extinction dipole) it chose the wrong parity once in 60 cases in an independent check, with a margin of 0.161,
  just above the 0.15 threshold, and once in 60 more of the same kind (0.156). In 160 nulls of two other models it
  never did. Count on an error of the order of 1–3 % when the fine detail is not shared, and confirm a decided
  parity with a second, independent direction (stars, landscape, the contacts below, an annotated frame). In those
  nulls the decisions with the right parity came from the broad shape, with the rotation up to 8° off: take the
  orientation from the declared frame, and the scan's rotation as a hint.
- **After a scan the rotation null is no longer a null.** The best rotation is chosen among the very rotations the
  null is made of, so its fine detail beats that null almost by construction. The scan compares the two mirror
  states with each other instead: each is the best of the same rotations.
- **The fine detail is not only fine.** The 12° high-pass keeps 8 % of the m = 2 harmonic, 18 % of m = 3 and 42 %
  of m = 5. On a synthetic corona without rays the right state still reached a median ρ of 0.97. Keep 12° for the
  parity: narrower high-passes (6°, 4°) decided more often but chose the wrong parity in up to 2 of 40 synthetic
  cases with weak shared detail.
- **The Moon as a cross-check.** The lunar track gives one direction, the Moon's motion. With the Sun's position on
  the sensor free, any constant offset of the track goes into it, and the track is straight (to 0.012″ during the
  2026 totality), so a fit of the track alone cannot tell the parity. The contacts can, away from the central
  line: at second and third contact the chromosphere appears on the side of the track where the Sun's centre
  lies, 13.9° from the axis of the Moon's motion at the site of the 2026 map (impact parameter 7.8″, totality 107 s)
  and 0.017° on the central line (110 s). A mirror puts it on the other side. Near the central line neither the
  track nor the contacts tell the parity. These angles come from the DE421 ephemeris; the test has not been tried
  on frames.
- **The sky as a cross-check.** With the Sun low, the extinction dipole and the sky gradient point along the
  vertical. In 2026 the zenith lay 70° from the Moon's motion (celestial PA 48° and 118°), so the two directions
  together fix the parity: a mirror would put the zenith 139° from where the ephemeris puts it. This is geometry
  only and has not been tested with data as a parity check. On the 2026 map, already oriented by stars, the
  uncorrected ratio to C2 had its dipole towards solar PA 30–37° and the sky gradient towards 25°, with the zenith
  at 33° (research note 185).
- **Pylon.** Only the contiguous dark run that contains the seed; a global threshold would remove real coronal
  holes. Labels and occulter edges: mask them, never fill them.
- **Prominences.** Overlay AIA 304 Å contours (outside the disc and the Moon) and say where they match *by eye*.
- **2026, for orientation.** Display image vs K-Cor NRGF: 0.90–0.95 up to 1.75 R☉; vs C2 0.82 falling to 0.42
  (2.4–6 R☉), fine detail 0.88 to 0.58; vs AIA 211 Å 0.87–0.89. Linear MSB map vs K-Cor pB: 0.96–0.98
  (1.15–1.75 R☉); vs C2 0.97 falling to 0.78, fine detail 0.97 to 0.69. Orientation −0.5° to +0.8°. The whole C2
  profile at 5–6 R☉ prefers +9° to +10°, the edge of the ±10° search (`at_search_edge`): that is the broad shape,
  not the orientation.

## 4 · Brightness in MSB

**a. Your map.** Linear stack → sky fitted where the corona is negligible (r ≥ 8 R☉) → differential extinction
(`ael extinction`, referred to the air mass at which the zero point was measured) → photometric zero point
(stars in the same frames) → MSB. Give the factor's uncertainty from a bootstrap of the stars: in 2026 it
was −17 %/+2 %, not the ±10 % first assumed. Declare the one-sided bias of the sky: pass a model corona
(`k_corona_van_de_hulst_1950` + `f_corona_van_de_hulst_1950`) through the same sky fit.

**b. K-Cor.** pB/p(r) is the **K** corona only. A photograph sees K + F:

```python
model = cg.kcor_total_msb(pb_mean, r_kcor, density="baumbach_allen", f_scale=1.0)
ours_cells = cg.cell_medians(msb, frame_ours, rings, drop_touching=band | gap | prominences)
ratios = cg.level_ratios(ours_cells, cg.cell_medians(model, frame_kcor, rings))
```

Vary the density (`baumbach_allen`, `saito_equator`) and the F scale (0.5–1.5) and report the range. Use
K-Cor only where its pB is reliable (2026: negative beyond ~1.95 R☉, so it was used to 1.7 R☉).

**c. LASCO C2.** `(DN − bias) / (exposure time × exposure factor) × vignetting × factor`, with
`lasco_c2_msb_per_dn(date, "colaninno_howard_2015")` and `(…, "solarsoft")`. They differ by 13.5 % in level for
August 2026, a difference already present in 2013. Give both. Only the Orange filter is calibrated; a summed
image divides the factor (`summing=lasco_c2_summing(header)`), and a polariser image is calibrated only by
SolarSoft (factor / 0.25256). Average the images before and after totality; exclude the pylon by PA.

**d. Judge.** `ratio_band(σ_lo, σ_hi)` gives the 1σ band of ours/reference: for −20 %/+11 %, **0.90–1.25**
(not 0.80–1.11). Say "compatible" only inside the band, ring by ring.

**2026 result, for orientation:** K-Cor 1.06/1.06/1.12 at 1.15–1.70 R☉ (compatible); C2 1.14→1.40 with
Colaninno & Howard (inside 1σ at every ring) and 1.32→1.62 with SolarSoft; cause of the C2 level not
separated (stray light, sky, the second camera, the C2 calibration). `ael.coronagraph` reproduces those
numbers within 0.003 (C2) and 0.009 (K-Cor) from the research's calibrated map, which is not distributed
(`docs/VALIDATION_1.3.0.md`).

## 5 · Traps that were real

- K-Cor **pB/p without the F corona** gave a false +13–15 % excess; the K-Cor GIF overestimated pB by 2–3 %.
- A ring inside the **lunar-motion band** (the Moon moves during totality) was compared as if it were corona.
  Drop every cell that touches the band, the 1–2 px gap at the limb or a prominence (`drop_touching`).
- **R☉** taken from another day or observer (959″ instead of 946.66″) put the brightness 6 % low.
- **The sky swallowed corona.** A constant sky measured 7 R☉ out contains K + F: the corona came out 4/9/16 %
  low at 3/4/5 R☉. A sky plane fitted on uncorrected data absorbed the extinction dipole. Sky and `k` are
  degenerate: the C2 dipole is a consistency test conditional on the sky plane, not a measurement of `k`.
- **Colour.** The sky is blue: a sky level in luminance is not the level in camera green.
- **Two cameras** calibrated through each other: give the second camera's own zero point, or say it is missing.
- **NRGF on LASCO level 0.5** keeps the F corona's flattened shape; for display, remove angular harmonics
  m ≤ 3 (`subtract_low_harmonics`) after the vignetting correction.
- The **K-Cor GIF photosphere circles** have different radii in the NRGF and pB products: never take R☉ from them.

## 6 · What to hand over

A JSON receipt (the command writes one) and a short text that keeps the two questions apart: structure per ring
with its null and fine detail, and what fixed the mirror state; brightness per ring with both C2 calibrations, the
K-Cor model range and the band; what was excluded and why; what was *not* tested. Never write "validated" for a
brightness that only agrees in structure, and never present a ratio without its band.

Credit line for anything you produce with this: `Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library` (a courtesy, not a condition).
