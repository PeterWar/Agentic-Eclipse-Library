# PSB16 writer feasibility probe

> Historical report. This document preserves its original research, measurements and implementation context. Controls, defaults, sequential processing and export behaviour described below may have changed. Use the [current technical guides](README.md) and [validation boundaries](validation.md) for the active application.

Historical step 1 report. The exporter is now integrated and tested in Photoshop; see [production PSB export](psb-export.md).

Source authorship and the exact copied/adapted or imported components are listed in [ATTRIBUTIONS.md](../ATTRIBUTIONS.md).

24 October 2026. Step 1 only: small synthetic PSB, without changing application export or project dependencies.

## Result

The candidate is **psd-tools 1.26.0**, using **AEL 1.3.3's low-level 16-bit writer**. AEL already writes the required `Lr16` section and keeps an explicitly supplied 16-bit cached composite. Its convenience wrapper does not list Color or Linear Light; the probe adds layers as Normal and assigns those two modes through `PixelLayer.blend_mode`. No AEL installation files are edited.

A normal `PixelLayer.frompil()` path is unsuitable for preserving our RGB16 input precision: the upstream API notes that the PIL image provides only 8-bit RGB precision, even in a 16-bit document. The low-level API is therefore required for this candidate. See [psd-tools layer documentation](https://psd-tools.readthedocs.io/en/stable/reference/psd_tools.api.layers.html) and [Adobe's PSD/PSB specification](https://www.adobe.com/devnet-apps/photoshop/fileformatashtml/).

Temporary packages used for the experiment: psd-tools 1.26.0 and attrs 26.1.0, installed under `/tmp/eclipse-psb-spike-deps`. Existing NumPy/Pillow and project dependencies are used. No packages were added to the application's venv, requirements or main.py metadata.

## Test document

96×64 RGB, 16 bits/channel, genuine PSB header version 2, five full-canvas layers in bottom-to-top order:

| Layer | Mode | Opacity byte | Visibility |
| --- | --- | --- | --- |
| Base | Normal | 255 | Visible |
| Fine detail | Overlay | 37 | Visible |
| Larson–Sekanina witness | Linear Light | 19 | Visible |
| RGB color witness | Color | 131 | Visible |
| Precision/Unicode witness | Normal | 53 | Hidden |

Layer names contain accents, punctuation and CJK characters. Alpha includes fully transparent holes, fractional values and opaque values. RGB witnesses include values outside the 8-bit×257 lattice, to detect silent reduction to 8-bit precision.

## Verification

1. Reopen with psd-tools through AEL.verify: no mismatches in layer names, modes, opacities, visibility, RGB or alpha.
2. Independent reader in the probe parses the PSB header, 64-bit lengths, Lr16 layer records, Unicode names, per-channel ZIP prediction and RAW cached composite. It uses struct, zlib and NumPy, not psd-tools/AEL parsing or decompression routines.
3. Every stored RGB and alpha pixel equals the original uint16 value exactly. Cached merged RGB also equals the supplied uint16 composite exactly.
4. Negative control: an 8-bit roundtrip of the reference pixels differs and is detected.

Successful artifact: `/tmp/eclipse-psb-probe/run02/probe_rgb16_layers.psb`, 180582 bytes. SHA-256: `018b5b70450bda184d4e7c49a4512b23f1ede90e8142ba4075e578f33dec361e`.

`run02/report.json` records results. `expected.npz` retains exact source arrays and merged RGB; `expected_composite.png` is an 8-bit viewing aid, not the precision authority. The failed first experiment is retained in run01; it failed before writing a PSB because the prototype initially supplied a 2D alpha to an RGB blending operation, which was corrected to broadcast RGB explicitly.

## Reproduction

From the project root, using its existing Python dependencies and psd-tools/attrs in a temporary directory:

```bash
PYTHONPATH=/path/to/temporary/dependencies .venv/bin/python scripts/research/probe_psb_writer.py \
  --ael-runtime /path/to/Agentic-Eclipse-Library/runtime \
  --out /tmp/new-psb-probe-output
```

The output directory must not already exist. The prototype imports the installed AEL writer by the explicit path; AEL is not added as an application runtime dependency. AEL's upstream MIT attribution is retained in `docs/third-party/AEL-MIT.txt`.

## What this establishes and what remains

The candidate can preserve our raster layer data and required mode identifiers in a small PSB16. It is suitable for proceeding to the next implementation stage.

This is **not yet a native Photoshop compatibility verdict**. Photoshop opening, editable-layer inspection and its recalculated composite have not been tested. The cached composite uses this application's blend equations; reading that cache back does not validate Photoshop's blend/color management.

The probe verifies **per-layer alpha**, but its cached composite is opaque RGB. A transparent merged preview for missing-data holes must be addressed before integrating the real exporter. There is no >2 GB / large-canvas stress test, memory/cancellation benchmark, ICC-profile test, or direct application export integration in this stage. Low-level private record APIs require a pinned dependency and regression tests before adoption.
