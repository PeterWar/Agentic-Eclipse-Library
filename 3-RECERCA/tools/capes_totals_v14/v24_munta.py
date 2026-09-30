"""V24 = la V23 de Pere (18 capes byte a byte) + la Lluna al to del
DSC06984.psb + el reflex vermell de la flamarada (geometria exacta del run).
Canònic: research/128 (en curs). Fitxer NOU: CapesTotalsV24.psb.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "encaix_sony"))
B = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/"
SRC, DST = B + "CapesTotalsV23.psb", B + "CapesTotalsV24.psb"
POS = (3279, 4866)          # (top, left) del disc a la V23 (mesurat)
T0 = time.time()


def marca(t):
    print(f"[{time.time()-T0:7.1f}s] {t}", flush=True)


def main():
    from psd_tools import PSDImage
    from psd_tools.constants import Compression, BlendMode
    from psd_tools.psd.image_data import ImageData
    from psb_utils import add_pixel_layer, add_mask16, finalize_lr16

    psd = PSDImage.open(SRC)
    capes = list(psd)
    assert len(capes) == 18, len(capes)
    W, H = psd.width, psd.height
    hdr = psd._record.header
    marca(f"V23 oberta: {W}x{H} · {len(capes)} capes · {hdr.channels} canals")

    # el composite de la V23 (el va escriure el Photoshop de Pere)
    comp = psd._record.image_data.get_data(hdr)
    plans = [np.frombuffer(c, dtype=">u2").reshape(H, W).astype(np.float32)
             for c in comp]
    marca(f"composite llegit ({len(plans)} plans)")

    Ep = np.load(f"{CAU}/capa_fosca_px.npy")
    Em = np.load(f"{CAU}/capa_nat_msk.npy")
    Rp = np.load(f"{CAU}/capa_reflex_px.npy")
    ty, tx = POS
    h2, w2 = Em.shape

    tb = psd._record.layer_and_mask_information.tagged_blocks
    for kk in list(tb.keys()):
        kb = kk.value if hasattr(kk, "value") else kk
        if kb not in (b"Lr16", b"Mt16"):
            del tb[kk]
    ce = add_pixel_layer(psd, Ep,
                         "EARTHSHINE al to DSC06984 · mediana 0,104/0,098/0,098 "
                         "com el teu revelat · estructura validada r=0,885 (V24)",
                         top=ty, left=tx, blend=BlendMode.NORMAL,
                         compression=Compression.ZIP)
    add_mask16(ce, Em, top=ty, left=tx)
    cr = add_pixel_layer(psd, Rp,
                         "REFLEX flamarada · llum vermella del DSC06984 sobre el "
                         "limbe W · geometria exacta del run · Linear Dodge (V24)",
                         top=ty, left=tx, blend=BlendMode.LINEAR_DODGE,
                         compression=Compression.ZIP)
    add_mask16(cr, np.full((h2, w2), 65535, np.uint16), top=ty, left=tx)
    finalize_lr16(psd)
    marca("capes inserides")

    # fusionada: composite V23 + earthshine (màscara) + reflex (additiu)
    m = Em.astype(np.float32) / 65535.0
    for c in range(3):
        reg = plans[c][ty:ty + h2, tx:tx + w2]
        reg = reg * (1 - m) + Ep[..., c].astype(np.float32) * m
        reg = np.clip(reg + Rp[..., c].astype(np.float32), 0, 65535)
        plans[c][ty:ty + h2, tx:tx + w2] = reg
    dades = [np.clip(p + 0.5, 0, 65535).astype(">u2").tobytes() for p in plans]
    idata = ImageData(compression=Compression.RAW)
    idata.set_data(dades, hdr)
    psd._record.image_data = idata
    if getattr(psd, "_updated", False):
        psd._updated = False
    marca("fusionada refeta · desant…")
    psd.save(DST)
    marca(f"{DST} · {os.path.getsize(DST)/1e9:.2f} GB")

    p2 = PSDImage.open(DST)
    c2 = list(p2)
    assert (p2.width, p2.height) == (W, H) and len(c2) == 20
    src2 = PSDImage.open(SRC)
    ig = sum(1 for i in range(18)
             if list(src2)[i]._channels[1].data == c2[i]._channels[1].data)
    print(f"    fidelitat: {ig}/18 capes de la V23 byte a byte", flush=True)
    r = subprocess.run([os.path.join(AQUI, "porta_photoshop.sh"), DST],
                       capture_output=True, text=True, timeout=5400)
    print("    Photoshop diu:", (r.stdout + r.stderr).strip(), flush=True)
    json.dump({"capes": [ly.name[:80] for ly in c2],
               "bytes": os.path.getsize(DST)},
              open(f"{CAU}/rebut_v24.json", "w"), indent=1, ensure_ascii=False)
    marca("fet")


if __name__ == "__main__":
    main()
