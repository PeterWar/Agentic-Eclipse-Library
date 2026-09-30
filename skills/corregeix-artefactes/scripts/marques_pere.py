#!/usr/bin/env python3
"""Ingestió de les marques que Pere pinta sobre un TIF de la fusionada.

    python3 marques_pere.py <Artefactes.tif> <fusionada.psb|.tif> <dir_sortida> [cx cy R_sol_px]

Escriu `marques.json` (id, x, y, mida, àrea, r en R☉, azimut, color) i
`marques_finestres.png` (per a cada marca gran: finestra del TIF de Pere al
costat de la mateixa finestra de la fusionada, contrast estirat), més
`marques_x4.png` (llenç sencer amb les marques ressaltades).
"""
import sys, os, json, numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import artefactes as art


def fusionada(path):
    if path.lower().endswith((".psb", ".psd")):
        from psd_tools import PSDImage
        p = PSDImage.open(path); W, H = p.width, p.height; hdr = p._record.header; pl = p._record.image_data.get_data(hdr)
        return np.dstack([(np.frombuffer(pl[c], ">u2").reshape(H, W) >> 8).astype(np.uint8) for c in range(3)])
    import tifffile
    A = tifffile.imread(path)[..., :3]; return (A >> 8).astype(np.uint8) if A.dtype == np.uint16 else A.astype(np.uint8)


def main():
    tif, fus, out = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(out, exist_ok=True)
    cx, cy, RS = (float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])) if len(sys.argv) > 6 else (5361.877, 3774.741, 440.603)
    rows, marca, A8 = art.marques_tif(tif, cx, cy, RS); M8 = fusionada(fus); H, W = A8.shape[:2]
    json.dump(rows, open(os.path.join(out, "marques.json"), "w"), indent=1)
    import cv2
    small = cv2.resize(A8, (W // 4, H // 4), interpolation=cv2.INTER_AREA); ms = cv2.resize(marca.astype(np.uint8) * 255, (W // 4, H // 4), interpolation=cv2.INTER_AREA) > 0
    from scipy.ndimage import binary_dilation
    small[binary_dilation(ms, iterations=2)] = [255, 0, 255]; Image.fromarray(small).save(os.path.join(out, "marques_x4.png"))
    sel = [r for r in rows if r["area"] > 5000][:12]
    try: f = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
    except Exception: f = ImageFont.load_default()
    S = 600; pan = Image.new("RGB", (2 * S + 30, max(1, len(sel)) * (S + 40) + 10), (18, 18, 20)); d = ImageDraw.Draw(pan)
    def estira(im):
        arr = im.astype(np.float32); lo, hi = np.percentile(arr, 1), np.percentile(arr, 99.5); return Image.fromarray(np.clip((arr - lo) / (hi - lo + 1e-6) * 255, 0, 255).astype(np.uint8))
    for j, r in enumerate(sel):
        x0 = int(np.clip(r["x"] - S // 2, 0, W - S)); y0 = int(np.clip(r["y"] - S // 2, 0, H - S))
        pan.paste(estira(A8[y0:y0 + S, x0:x0 + S]), (10, 10 + j * (S + 40))); pan.paste(estira(M8[y0:y0 + S, x0:x0 + S]), (S + 20, 10 + j * (S + 40)))
        d.text((10, 10 + j * (S + 40) + S + 4), f"marca {r['id']} {r['color']} · r={r['r_Rsol']} R☉ az={r['az']}° · esq: TIF de Pere · dreta: fusionada", fill=(235, 235, 230), font=f)
    pan.save(os.path.join(out, "marques_finestres.png"))
    print(f"{len(rows)} marques → {out}"); [print(" ", r) for r in rows[:20]]


if __name__ == "__main__":
    main()
