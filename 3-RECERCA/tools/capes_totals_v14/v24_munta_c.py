"""V24c: la vora viva, muntada SOBRE la V24 desada per Pere.

Es conserven byte a byte les seves 18 capes (inclòs el seu retoc d'1 px a la
[11]) i el seu REFLEX a la posició que ell ha triat (left 4862). Només se
substitueix el contingut de la capa EARTHSHINE (vora amb el residu viu) i la
fusionada es pedaça per diferència exacta: comp' = comp + (E_nova−E_vella)·m.
"""
from __future__ import annotations
import json, os, subprocess, sys, time
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "encaix_sony"))
B = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/"
SRC = B + "CapesTotalsV24.psb"
DST = B + "CapesTotalsV24.psb"
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
    assert len(capes) == 20
    W, H = psd.width, psd.height
    hdr = psd._record.header
    l18, l19 = capes[18], capes[19]
    ty, tx = l18.top, l18.left
    ry, rx = l19.top, l19.left
    marca(f"V24 de Pere: earthshine a ({ty},{tx}) · reflex a ({ry},{rx})")

    comp = psd._record.image_data.get_data(hdr)
    plans = [np.frombuffer(c, dtype=">u2").reshape(H, W).astype(np.float32)
             for c in comp]
    marca("composite de Pere llegit")

    Ev = np.load(f"{CAU}/capa_fosca_VELLA.npy").astype(np.float32)
    En = np.load(f"{CAU}/capa_fosca_px.npy")
    Em = np.load(f"{CAU}/capa_nat_msk.npy")
    Rp = np.load(f"{CAU}/capa_reflex_pere.npy")
    h2, w2 = Em.shape

    # treu les capes [18] i [19] del registre i re-afegeix-les
    lml = psd._record.layer_and_mask_information.layer_info
    # psd-tools: més segur reconstruir via psb_utils després d'esborrar amb API
    for l in (capes[19], capes[18]):
        l.delete_layer()
    marca("capes velles retirades")
    tb = psd._record.layer_and_mask_information.tagged_blocks
    for kk in list(tb.keys()):
        kb = kk.value if hasattr(kk, "value") else kk
        if kb not in (b"Lr16", b"Mt16"):
            del tb[kk]
    ce = add_pixel_layer(psd, En,
                         "EARTHSHINE al to DSC06984 · vora amb el residu viu "
                         "(Wiener suau ×2,2 int) · r=0,885 LROC (V24c)",
                         top=ty, left=tx, blend=BlendMode.NORMAL,
                         compression=Compression.ZIP)
    add_mask16(ce, Em, top=ty, left=tx)
    cr = add_pixel_layer(psd, Rp,
                         "REFLEX flamarada · posició afinada per Pere (−4 px) "
                         "· Linear Dodge (V24c)",
                         top=ry, left=rx, blend=BlendMode.LINEAR_DODGE,
                         compression=Compression.ZIP)
    add_mask16(cr, np.full((h2, w2), 65535, np.uint16), top=ry, left=rx)
    finalize_lr16(psd)
    marca("capes noves inserides")

    m = Em.astype(np.float32) / 65535.0
    for c in range(3):
        reg = plans[c][ty:ty + h2, tx:tx + w2]
        reg += (En[..., c].astype(np.float32) - Ev[..., c]) * m
        plans[c][ty:ty + h2, tx:tx + w2] = np.clip(reg, 0, 65535)
    dades = [np.clip(p + 0.5, 0, 65535).astype(">u2").tobytes() for p in plans]
    idata = ImageData(compression=Compression.RAW)
    idata.set_data(dades, hdr)
    psd._record.image_data = idata
    if getattr(psd, "_updated", False):
        psd._updated = False
    marca("fusionada pedaçada · desant…")
    psd.save(DST)
    marca(f"{DST} · {os.path.getsize(DST)/1e9:.2f} GB")

    p2 = PSDImage.open(DST)
    c2 = list(p2)
    assert len(c2) == 20
    ig = sum(1 for i in range(18)
             if capes[i]._channels[1].data == c2[i]._channels[1].data)
    print(f"    fidelitat: {ig}/18 capes de Pere byte a byte", flush=True)
    r = subprocess.run([os.path.join(AQUI, "porta_photoshop.sh"), DST],
                       capture_output=True, text=True, timeout=5400)
    print("    Photoshop diu:", (r.stdout + r.stderr).strip(), flush=True)
    marca("fet")


if __name__ == "__main__":
    main()
