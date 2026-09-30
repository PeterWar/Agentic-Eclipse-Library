"""V24c2: substitueix NOMÉS la capa REFLEX per la modulada pel relleu.
Pedaç del composite per diferència additiva exacta."""
from __future__ import annotations
import os, subprocess, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "encaix_sony"))
B = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/"
F = B + "CapesTotalsV24.psb"
T0 = time.time()


def marca(t):
    print(f"[{time.time()-T0:7.1f}s] {t}", flush=True)


def main():
    from psd_tools import PSDImage
    from psd_tools.constants import Compression, BlendMode
    from psd_tools.psd.image_data import ImageData
    from psb_utils import add_pixel_layer, add_mask16, finalize_lr16
    from v21_munta import canal_cru

    psd = PSDImage.open(F)
    capes = list(psd)
    assert len(capes) == 20
    W, H = psd.width, psd.height
    hdr = psd._record.header
    l19 = capes[19]
    ry, rx = l19.top, l19.left
    Rv = np.dstack([canal_cru(l19, c, psd.depth, psd.version)
                    for c in (0, 1, 2)]).astype(np.float32)
    marca(f"reflex vell extret ({ry},{rx})")
    Rn = np.load(f"{CAU}/capa_reflex_pere.npy").astype(np.float32)
    h2, w2 = Rn.shape[:2]

    comp = psd._record.image_data.get_data(hdr)
    plans = [np.frombuffer(c, dtype=">u2").reshape(H, W).astype(np.float32)
             for c in comp]
    l19.delete_layer()
    tb = psd._record.layer_and_mask_information.tagged_blocks
    for kk in list(tb.keys()):
        kb = kk.value if hasattr(kk, "value") else kk
        if kb not in (b"Lr16", b"Mt16"):
            del tb[kk]
    cr = add_pixel_layer(psd, Rn.astype(np.uint16),
                         "REFLEX flamarada · posició de Pere · glow modulat "
                         "pel relleu real (β=0,7, declarat) · Linear Dodge (V24c2)",
                         top=ry, left=rx, blend=BlendMode.LINEAR_DODGE,
                         compression=Compression.ZIP)
    add_mask16(cr, np.full((h2, w2), 65535, np.uint16), top=ry, left=rx)
    finalize_lr16(psd)
    for c in range(3):
        reg = plans[c][ry:ry + h2, rx:rx + w2]
        reg += Rn[..., c] - Rv[..., c]
        plans[c][ry:ry + h2, rx:rx + w2] = np.clip(reg, 0, 65535)
    dades = [np.clip(p + 0.5, 0, 65535).astype(">u2").tobytes() for p in plans]
    idata = ImageData(compression=Compression.RAW)
    idata.set_data(dades, hdr)
    psd._record.image_data = idata
    if getattr(psd, "_updated", False):
        psd._updated = False
    marca("desant…")
    psd.save(F)
    marca(f"{F} · {os.path.getsize(F)/1e9:.2f} GB")
    p2 = PSDImage.open(F)
    c2 = list(p2)
    assert len(c2) == 20
    ig = sum(1 for i in range(19)
             if capes[i]._channels[1].data == c2[i]._channels[1].data)
    print(f"    fidelitat: {ig}/19 capes intactes", flush=True)
    r = subprocess.run([os.path.join(AQUI, "porta_photoshop.sh"), F],
                       capture_output=True, text=True, timeout=5400)
    print("    Photoshop diu:", (r.stdout + r.stderr).strip(), flush=True)
    marca("fet")


if __name__ == "__main__":
    main()
