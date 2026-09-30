"""Inspecció del save de Pere de la V18 (28-08 17:07): estructura i marques.

Només lectura del PSB. Escriu al cau_v19: la màscara de marques VERDES
(lluminància) i TARONGES (to), i un resum JSON.
"""
from __future__ import annotations

import json
import os

import numpy as np
from psd_tools import PSDImage
from psd_tools.compression import decompress

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v19")
B = ("/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/"
     "1-Unint Capes/Capes Totals/")
PSB = B + "CapesTotalsV18.psb"


def canal(layer, cid, W, H, depth, version):
    rec = layer._record
    for info, cd in zip(rec.channel_info, layer._channels):
        if int(info.id) == cid:
            w = rec.right - rec.left
            h = rec.bottom - rec.top
            arr = decompress(cd.data, cd.compression, w, h, depth, version)
            a = np.frombuffer(arr, ">u2" if depth == 16 else "u1")
            return a.reshape(h, w), (rec.top, rec.left, rec.bottom, rec.right)
    return None, None


def main():
    os.makedirs(CAU, exist_ok=True)
    psd = PSDImage.open(PSB)
    W, H = psd.width, psd.height
    depth, version = psd.depth, psd.version
    print(f"llenç {W}x{H} · {depth} bits · v{version} · {len(list(psd))} capes")
    halos = None
    for i, ly in enumerate(psd):
        rec = ly._record
        nch = len(rec.channel_info)
        print(f"  [{i:02d}] '{ly.name}' vis={ly.visible} bbox={ly.bbox} "
              f"canals={nch} opacitat={rec.opacity}")
        if "HALO" in ly.name.upper():
            halos = ly
    if halos is None:
        print("⛔ cap capa HALOS")
        return

    r, bb = canal(halos, 0, W, H, depth, version)
    g, _ = canal(halos, 1, W, H, depth, version)
    b, _ = canal(halos, 2, W, H, depth, version)
    a, _ = canal(halos, -1, W, H, depth, version)
    top, left, bot, right = bb
    print(f"\nHALOS: bbox top={top} left={left} bot={bot} right={right}")
    esc = 65535.0 if depth == 16 else 255.0
    rf = r.astype(np.float32) / esc
    gf = g.astype(np.float32) / esc
    bf = b.astype(np.float32) / esc
    if a is not None:
        af = a.astype(np.float32) / esc
    else:
        af = np.ones_like(rf)
    pintat = af > 0.5
    print(f"px pintats: {pintat.sum()}")
    # classificació per color dins del pintat
    rr, gg, bbv = rf[pintat], gf[pintat], bf[pintat]
    # mostres de colors dominants
    from collections import Counter
    q = (np.round(rr * 8).astype(int) * 100 + np.round(gg * 8).astype(int) * 10
         + np.round(bbv * 8).astype(int))
    cnt = Counter(q.tolist()).most_common(12)
    print("colors dominants (R·8,G·8,B·8 → recompte):")
    for k, n in cnt:
        print(f"  R{k // 100} G{(k // 10) % 10} B{k % 10}: {n}")

    # verd: G clarament per sobre de R i B; taronja: R alt, G mitjà, B baix
    verd = pintat & (gf > rf + 0.15) & (gf > bf + 0.15)
    taronja = pintat & (rf > bf + 0.25) & (rf > 0.5) & (gf > bf) & (gf < rf)
    vermell = pintat & (rf > gf + 0.25) & (rf > bf + 0.25) & (gf < 0.35)
    print(f"\nverds: {verd.sum()} · taronges: {taronja.sum()} "
          f"· vermells (ronda 1?): {vermell.sum()} "
          f"· sense classificar: {(pintat & ~verd & ~taronja & ~vermell).sum()}")

    # desa màscares al llenç sencer (u1)
    for nom, m in (("marques_verd", verd), ("marques_taronja", taronja),
                   ("marques_vermell", vermell), ("marques_totes", pintat)):
        full = np.zeros((H, W), np.uint8)
        full[top:bot, left:right] = m.astype(np.uint8) * 255
        np.save(os.path.join(CAU, nom + ".npy"), full)
    json.dump({
        "psb_mtime": os.path.getmtime(PSB), "psb_bytes": os.path.getsize(PSB),
        "capes": [ly.name for ly in psd],
        "halos_bbox": [int(x) for x in (top, left, bot, right)],
        "px_verd": int(verd.sum()), "px_taronja": int(taronja.sum()),
        "px_vermell": int(vermell.sum()), "px_pintat": int(pintat.sum()),
    }, open(os.path.join(CAU, "inspeccio_v18_pere.json"), "w"), indent=1)
    print(f"\nmàscares desades a {CAU}")


if __name__ == "__main__":
    main()
