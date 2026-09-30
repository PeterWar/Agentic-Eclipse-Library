"""V24e: perímetre re-fet (arcs blau/lila de Pere) + reflex garbellat al
sector de la flamarada. Composite de la regió reescrit exacte (no pedaç)."""
from __future__ import annotations
import json, os, subprocess, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "encaix_sony"))
B = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/"
F = B + "CapesTotalsV24.psb"
T0 = time.time()

NOM18 = ("EARTHSHINE · interior apilat 11 fot · perímetre = flood REAL del "
         "DSC06993 (excés sobre baseline de l'apilat, corba tonal clonada "
         "del revelat de Pere, traspàs on la seva llum ARRIBA al nivell) · V24e")
NOM19 = ("REFLEX flamarada · posició de Pere · garbellat al sector de la "
         "flamarada (|az|>130°): el glow real del D93 ja posa la llum del "
         "perímetre (V24e)")


def marca(t):
    print(f"[{time.time()-T0:7.1f}s] {t}", flush=True)


def main():
    from psd_tools import PSDImage
    from psd_tools.constants import Compression, BlendMode
    from psd_tools.psd.image_data import ImageData
    from psb_utils import add_pixel_layer, add_mask16, finalize_lr16

    psd = PSDImage.open(F)
    capes = list(psd)
    assert len(capes) == 20
    W, H = psd.width, psd.height
    hdr = psd._record.header
    l18, l19 = capes[18], capes[19]
    ey, ex = l18.top, l18.left
    ry, rx = l19.top, l19.left
    marca(f"obert · earthshine ({ey},{ex}) · reflex ({ry},{rx})")

    E2 = np.load(f"{CAU}/capa_fosca_e.npy")
    M2 = np.load(f"{CAU}/mascara_e.npy")
    R2 = np.load(f"{CAU}/capa_reflex_e.npy")
    C2 = np.load(f"{CAU}/comp_prevista_e.npy")
    h2, w2 = E2.shape[:2]

    comp = psd._record.image_data.get_data(hdr)
    plans = [np.frombuffer(c, dtype=">u2").reshape(H, W).astype(np.float32)
             for c in comp]
    l19.delete_layer()
    l18.delete_layer()
    tb = psd._record.layer_and_mask_information.tagged_blocks
    for kk in list(tb.keys()):
        kb = kk.value if hasattr(kk, "value") else kk
        if kb not in (b"Lr16", b"Mt16"):
            del tb[kk]
    ce = add_pixel_layer(psd, E2, NOM18, top=ey, left=ex,
                         blend=BlendMode.NORMAL, compression=Compression.ZIP)
    add_mask16(ce, M2, top=ey, left=ex)
    cr = add_pixel_layer(psd, R2, NOM19, top=ry, left=rx,
                         blend=BlendMode.LINEAR_DODGE,
                         compression=Compression.ZIP)
    add_mask16(cr, np.full(R2.shape[:2], 65535, np.uint16), top=ry, left=rx)
    finalize_lr16(psd)
    marca("capes noves inserides")

    for c in range(3):
        plans[c][ey:ey + h2, ex:ex + w2] = C2[..., c].astype(np.float32)
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
    c2l = list(p2)
    assert len(c2l) == 20
    ig = sum(1 for i in range(18)
             if capes[i]._channels[1].data == c2l[i]._channels[1].data)
    print(f"    fidelitat: {ig}/18 capes de Pere intactes", flush=True)
    r = subprocess.run([os.path.join(AQUI, "porta_photoshop.sh"), F],
                       capture_output=True, text=True, timeout=5400)
    print("    Photoshop diu:", (r.stdout + r.stderr).strip(), flush=True)
    marca("fet")


if __name__ == "__main__":
    main()
