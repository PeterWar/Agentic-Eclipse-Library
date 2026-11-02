# Validation of 1.4.2 (2 November 2026)

1.4.2 adds three filter layers outside the defaults: `nafe`, `swap` and `larson_sekanina_1` / `larson_sekanina_0.4`
([`NAFE_SWAP_LARSON_SEKANINA.md`](NAFE_SWAP_LARSON_SEKANINA.md)). The defaults, `"all"` and every layer of 1.4.1 are
unchanged, and so are the connectors' dialogs, which do not offer the new layers.

## On the 2026 stacks, against the author's research versions

The author had a research version of each filter on his image of 12 August 2026. The library's layer was computed on
the same input, with the same domain and geometry, and compared with it. The script and its receipts are in the
author's private project, not in this repository, because they read his stacks.

**NAFE** (the green channel of the linear base, on the author's final crop with 64 px around it, in the domain of his
test layer; against that layer as written in his test file, in 16 bits):

- With his σ, 12 DN, given by hand: the same 38,658,283 pixels, correlation 0.999998, rms difference 7.9e-5, at most
  0.0055. Beyond 2 R☉ the rms is 4e-6 to 6e-6, below half a 16-bit step (7.6e-6); the differences are next to the
  limb, where the corona is brightest (6.4e-4 at 1–1.3 R☉, 2.5e-4 at 1.3–2 R☉).
- With the σ the library measures by default, 12.49 DN (12 times a pixel noise of 1.04 DN beyond 4 R☉): rms 0.0017,
  at most 0.015, ring by ring the same figures as when the filter was written on 28 October. The difference grows
  outwards (0.0021 at 8–12 R☉), where the neighbours differ by little more than the noise and a gate 4 % wider
  changes them most.

**Larson–Sekanina** (ln L of the starless fusion of both optics, the whole canvas of 10,551 × 7,506 px; against the
author's research layers made again with their own script on the same input, compared on his final crop of
7,933 × 5,021 px):

- The prominences found by `red_excess_mask` are exactly those of the research layers: 24,072 pixels, none different.
- The display scale s0 agrees within 0.25 % (1°: 0.05730 against 0.05744; 0.4°: 0.01684 against 0.01687).
- Against the research layers as they show in Overlay (their alpha applied): correlation 0.99975 for both; rms
  difference 0.00099 (1°) and 0.00094 (0.4°) in layer units; 99 % of pixels within 0.0035 (1°) and 0.0032 (0.4°). The
  largest differences are next to the limb, where the brightness falls fastest: rms 0.0087 (1°) and 0.0085 (0.4°) at
  1–1.3 R☉, 0.0026 and 0.0023 at 1.3–2 R☉, below 0.001 beyond 2 R☉. The research layers read the turned values with
  OpenCV's cubic kernel (a = −0.75), needed only the four nearest pixels observed, and kept a smoothed value only where
  half of the kernel's weight was observed; the library uses a = −0.5, needs all sixteen pixels, and keeps a smoothed
  value from 1 % of the weight. This comparison does not tell how much of the difference comes from each.
- The library's layer covers 5,927 (1°) and 5,919 (0.4°) fewer pixels of 38.6 million: those where not all sixteen
  pixels read for a turned value are observed. It has no value where there is no data.
- Its level ring by ring stays at mid grey: in the worst ring of 0.05 R☉ the median is 0.016 (1°) and 0.011 (0.4°)
  from it, within the 0.05 tolerance the author's research used for the level per ring.

**SWAP** (the same green channel, the whole canvas, 70.4 million observed pixels; against the September research
recipe, run again here with its own code on the same input):

- t0 = 488.29 in both. The same 76 observed pixels fall between the polar samples and get the median taken at their
  own radius and angle. Every observed pixel has a value; none outside the data.
- The filtered image I/(F + t0)^0.75 agrees with the research recipe: median relative difference 0, 99 % of pixels
  within 1.7e-5, at most 1.2 %. The largest differences are next to the limb (99 % within 0.104 % at 1–1.3 R☉). The
  two codes blur F differently (both with observed pixels only, but the research one cuts its Gaussian at 3σ and
  repeats the pixels at the frame's edge, and the library's cuts at 4σ and reads nothing beyond the frame); this
  comparison does not tell how much of the difference comes from that.
- What was compared is the filtered image, not the displayed layer: the September version was shown with a linear
  stretch, the library shows the paper's fourth root.

## Tests

- `python -m ael selftest`: 137 of 137 in the source tree and in the installed wheel, with network and without (124
  in 1.4.1; the 13 new tests are in `ael/_tests/test_nafe_swap_larson.py`).
- The Codex plugin 1.1.6: its ZIP passed the seventeen integration checks, with the 137 bundled tests; the Claude
  plugin folder matches it.
- The connectors' code does not change. Their checks outside the programs pass; the files of their packages differ
  from those tested inside PixInsight and Photoshop for 1.4.1 only in `runtime/ael/`, the library they carry; and
  their shared RAW engine gives, on six frames of the 2026 eclipse, the same linear master and the same three default
  layers as the engine of 1.4.1, pixel for pixel (the files differ only in the TIFF tag that names the version). They
  were not run again inside PixInsight or Photoshop.

## Limits

- These comparisons show that the library computes what the research versions computed. They do not say whether a
  layer shows corona: the Larson–Sekanina copies at ±Δθ are part of what it shows, and NAFE draws a light ring next to
  the lunar limb. A layer is judged on the image, with a null control.
- The SWAP filter's display range (0.5–2.0) is the paper's choice for EUV images; the receipt gives the share of the
  field below and above it. On the author's final crop: none below, 0.007 % above.
- Beyond about 4 R☉, where ℓ is smoothed by σ = 12 px, the 0.4° Larson–Sekanina layer turns the smoothed noise of the
  outer corona and the sky into a texture like relief; the 1° layer shows less of it. Spread about mid grey at 5–8 R☉:
  0.0083 (0.4°) and 0.0060 (1°). The research layers have the same texture there (the same spread; correlation
  0.99994 and 0.99997).
