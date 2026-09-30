#!/usr/bin/env python3
"""Pilot de calibratge Vixen (R6 III): resta de dark en espai raw + demosaic.

Llum: 572A2983.CR3 (10,3 s, bloc fosc d'earthshine, mig de la totalitat).
Darks: 25 CR3 de 10,3 s de la biblioteca del 14-08.
Sortides al scratchpad: comparació verd/WB, comparació de píxels calents,
i TIFF lineal de 16 bits calibrat.
"""
import numpy as np
import rawpy
import tifffile
from PIL import Image, ImageDraw

LIGHT = "/Users/USUARI/Desktop/Eclipse Vixen Unfiltered/572A2983.CR3"
DARKS_DIR = "/Users/USUARI/Desktop/Darks Canon R6III Eclipse"
DARKS = ["572A3342","572A3343","572A3344","572A3454","572A3455","572A3456",
         "572A3568","572A3569","572A3570","572A4022","572A4023","572A4024",
         "572A4135","572A4136","572A4137","572A4250","572A4251","572A4252",
         "572A4817","572A5288","572A6722","572A6723","572A6724","572A6836",
         "572A6837"]
OUT = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/bd892f38-1fd3-470f-9bc5-71eb7485933a/scratchpad"

# ── 1. Master dark per mediana, en uint16 i per franges per no menjar RAM ──
stack = None
for i, name in enumerate(DARKS):
    with rawpy.imread(f"{DARKS_DIR}/{name}.CR3") as r:
        img = r.raw_image.copy()
    if stack is None:
        stack = np.empty((len(DARKS),) + img.shape, dtype=np.uint16)
    stack[i] = img
H, W = stack.shape[1:]
master = np.empty((H, W), dtype=np.float32)
for r0 in range(0, H, 512):
    r1 = min(r0 + 512, H)
    master[r0:r1] = np.median(stack[:, r0:r1, :], axis=0)
del stack

with rawpy.imread(LIGHT) as raw:
    black = np.array(raw.black_level_per_channel, dtype=np.float32)
    colors = raw.raw_colors
    white = float(raw.white_level)
    black_map = black[colors]
    dark_signal = np.clip(master - black_map, 0, None)

    med = [float(np.median(dark_signal[colors == c])) for c in range(4)]
    hot = int(np.count_nonzero(dark_signal > 50))
    print(f"mides raw: {H}x{W} · black/canal {black.tolist()} · white {white:.0f}")
    print(f"senyal fosc mediana per canal (ADU): {[f'{m:.2f}' for m in med]}")
    print(f"pixels calents (>50 ADU sobre el negre): {hot}")

    # ── 2. Calibratge en espai raw: llum − corrent fosc, pedestal intacte ──
    light_raw = raw.raw_image.astype(np.float32)
    cal = np.clip(light_raw - dark_signal, 0, white)
    raw.raw_image[:] = cal.astype(np.uint16)

    common = dict(no_auto_bright=True, output_bps=16, gamma=(1, 1),
                  demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD)
    rgb_nowb = raw.postprocess(use_camera_wb=False, use_auto_wb=False,
                               user_wb=[1, 1, 1, 1], **common)
    rgb_wb = raw.postprocess(use_camera_wb=True, **common)

# La versió SENSE calibrar, per a la comparació de píxels calents
with rawpy.imread(LIGHT) as raw2:
    rgb_uncal = raw2.postprocess(use_camera_wb=True, no_auto_bright=True,
                                 output_bps=16, gamma=(1, 1),
                                 demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD)

tifffile.imwrite(f"{OUT}/572A2983_calibrat_lineal_wb.tif", rgb_wb,
                 photometric="rgb", compression="zlib")
print("TIFF lineal 16 bits escrit")

# ── 3. Previsualitzacions amb estirament asinh comú ──────────────────────
def stretch(img16, s=0.015):
    x = img16.astype(np.float32) / 65535.0
    y = np.arcsinh(x / s) / np.arcsinh(1.0 / s)
    return (np.clip(y, 0, 1) * 255).astype(np.uint8)

def panell(parts, labels, path, scale=6):
    tiles = []
    for img, lab in zip(parts, labels):
        im = Image.fromarray(img)
        if scale > 1:
            im = im.resize((im.width // scale, im.height // scale),
                           Image.LANCZOS)
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, im.width, 34], fill=(0, 0, 0))
        d.text((10, 8), lab, fill=(255, 255, 255))
        tiles.append(im)
    total = Image.new("RGB", (sum(t.width for t in tiles) + 8 * (len(tiles) - 1),
                              max(t.height for t in tiles)), (24, 24, 24))
    x = 0
    for t in tiles:
        total.paste(t, (x, 0)); x += t.width + 8
    total.save(path)
    print("escrit", path)

panell([stretch(rgb_nowb), stretch(rgb_wb)],
       ["Calibrat, SENSE balanç de blancs — el «verd» del PixInsight",
        "El MATEIX fotograma amb el WB de càmera (Daylight)"],
       f"{OUT}/pilot_verd_vs_wb.png")

# Retall 1:1 de cel fosc per veure els píxels calents (cantonada superior dreta)
ch, cw = 900, 1400
y0, x0 = 200, rgb_wb.shape[1] - cw - 200
panell([stretch(rgb_uncal[y0:y0+ch, x0:x0+cw], s=0.004),
        stretch(rgb_wb[y0:y0+ch, x0:x0+cw], s=0.004)],
       ["SENSE calibrar (1:1) — pixels calents del sensor a 10,3 s",
        "CALIBRAT amb master de 25 darks (1:1)"],
       f"{OUT}/pilot_calibratge_hotpixels.png", scale=1)
