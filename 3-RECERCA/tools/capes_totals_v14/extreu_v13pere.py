"""Extreu les 12 capes de CapesTotalsV13_Pere.psd a un cau. Només lectura del PSD.

Per capa: RGB uint16 al seu bbox (tal qual, sense re-mostrejar), màscara uint8
al llenç sencer (amb el fons de fora del bbox de màscara aplicat), i metadades.
El cau és `cau_v13pere/` i està al .gitignore, com el de la V13.
"""
from __future__ import annotations

import json
import os

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
V13P = ("/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/"
        "Capes Totals/CapesTotalsV13_Pere.psd")
CAU = os.path.join(AQUI, "cau_v13pere")


def extreu() -> dict:
    fitxa = os.path.join(CAU, "info.json")
    if os.path.exists(fitxa):
        return json.load(open(fitxa))
    from psd_tools import PSDImage
    os.makedirs(CAU, exist_ok=True)
    psd = PSDImage.open(V13P)
    W, H = psd.width, psd.height
    info = {"W": W, "H": H, "fitxer": V13P, "capes": []}
    for i, l in enumerate(psd):
        num = l.name.split("_")[0]
        a = l.numpy("color")          # float32 0-1, exacte per a 16 bits
        rgb = np.clip(np.rint(a * 65535.0), 0, 65535).astype(np.uint16)
        del a
        np.save(os.path.join(CAU, f"rgb_{num}.npy"), rgb)
        m = l.mask
        if m is None or m.size == (0, 0):
            raise SystemExit(f"la capa {num} no té màscara")
        ma = np.squeeze(np.asarray(m.topil()))
        if ma.dtype != np.uint8:
            ma = np.clip(np.rint(ma.astype(np.float32) / 257.0), 0, 255).astype(np.uint8)
        bg = int(getattr(m, "background_color", 0))
        full = np.full((H, W), bg, np.uint8)
        x0, y0, x1, y1 = m.bbox
        sx0, sy0 = max(0, x0), max(0, y0)
        sx1, sy1 = min(W, x1), min(H, y1)
        full[sy0:sy1, sx0:sx1] = ma[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0]
        np.save(os.path.join(CAU, f"mask_{num}.npy"), full)
        info["capes"].append({
            "num": num, "i": i, "nom": l.name, "bbox": list(l.bbox),
            "visible": bool(l.visible), "opacitat": int(l.opacity),
            "fusio": str(l.blend_mode), "mask_bbox": list(m.bbox), "mask_fons": bg,
            "mask_mitjana": float(full.mean() / 255.0),
            "rgb_mitjana": float(rgb.mean() / 65535.0)})
        print(f"  {num}: bbox {l.bbox} · màscara fons {bg} mitjana {full.mean()/255.0:.3f} "
              f"· «{l.name[:60]}»", flush=True)
        del rgb, full, ma
    json.dump(info, open(fitxa, "w"), indent=1, ensure_ascii=False)
    return info


if __name__ == "__main__":
    extreu()
