"""Troba les marques de Pere: diferència entre les dues còpies de la Sony.

[13] (a sobre) = còpia amb els traços pintats; [12] = la Sony de la V18.
Els px on difereixen són els traços; el color del traç ve de [13].
Desa al cau_v19: màscares verd/taronja al llenç sencer + colors.
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


def canal(layer, cid, depth, version):
    rec = layer._record
    for info, cd in zip(rec.channel_info, layer._channels):
        if int(info.id) == cid:
            w = rec.right - rec.left
            h = rec.bottom - rec.top
            arr = decompress(cd.data, cd.compression, w, h, depth, version)
            return np.frombuffer(arr, ">u2" if depth == 16 else "u1").reshape(h, w)
    return None


def main():
    os.makedirs(CAU, exist_ok=True)
    psd = PSDImage.open(PSB)
    depth, version = psd.depth, psd.version
    capes = list(psd)
    base, marc = capes[12], capes[13]
    dif_tot = None
    rgb_marc = []
    for cid in (0, 1, 2):
        a = canal(base, cid, depth, version).astype(np.int32)
        b = canal(marc, cid, depth, version).astype(np.int32)
        d = np.abs(b - a)
        dif_tot = d if dif_tot is None else np.maximum(dif_tot, d)
        rgb_marc.append(b)
        print(f"canal {cid}: px que difereixen >1%: {(d > 655).sum()}")
    tra = dif_tot > 655  # >1 % de diferència = traç
    print(f"\ntraç total: {tra.sum()} px "
          f"({100 * tra.mean():.3f} % del llenç)")
    r = rgb_marc[0].astype(np.float32) / 65535
    g = rgb_marc[1].astype(np.float32) / 65535
    bch = rgb_marc[2].astype(np.float32) / 65535

    from collections import Counter
    rr, gg, bb = r[tra], g[tra], bch[tra]
    q = (np.round(rr * 8).astype(int) * 100 + np.round(gg * 8).astype(int) * 10
         + np.round(bb * 8).astype(int))
    print("colors dominants del traç (R·8,G·8,B·8 → recompte):")
    for k, n in Counter(q.tolist()).most_common(10):
        print(f"  R{k // 100} G{(k // 10) % 10} B{k % 10}: {n}")

    verd = tra & (g > r + 0.10) & (g > bch + 0.10)
    taronja = tra & (r > bch + 0.15) & (g < r) & (g > 0.75 * bch)
    resta = tra & ~verd & ~taronja
    print(f"\nverd: {verd.sum()} · taronja: {taronja.sum()} "
          f"· sense classificar: {resta.sum()}")
    if resta.sum():
        rr, gg, bb = r[resta], g[resta], bch[resta]
        q = (np.round(rr * 8).astype(int) * 100
             + np.round(gg * 8).astype(int) * 10 + np.round(bb * 8).astype(int))
        print("  colors del sense classificar:")
        for k, n in Counter(q.tolist()).most_common(6):
            print(f"    R{k // 100} G{(k // 10) % 10} B{k % 10}: {n}")

    np.save(os.path.join(CAU, "marques_verd.npy"), verd)
    np.save(os.path.join(CAU, "marques_taronja.npy"), taronja)
    np.save(os.path.join(CAU, "marques_totes.npy"), tra)
    json.dump({"px_verd": int(verd.sum()), "px_taronja": int(taronja.sum()),
               "px_resta": int(resta.sum())},
              open(os.path.join(CAU, "marques_v19.json"), "w"), indent=1)
    print(f"desat a {CAU}")


if __name__ == "__main__":
    main()
