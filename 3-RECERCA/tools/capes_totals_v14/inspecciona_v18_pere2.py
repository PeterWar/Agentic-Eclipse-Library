"""Segona passada: quina de les capes [12]/[13] és la de marques de Pere."""
from __future__ import annotations

import os

import numpy as np
from psd_tools import PSDImage
from psd_tools.compression import decompress

B = ("/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/"
     "1-Unint Capes/Capes Totals/")
PSB = B + "CapesTotalsV18.psb"


def canal(layer, cid, depth, version):
    rec = layer._record
    for info, cd in zip(rec.channel_info, layer._channels):
        if int(info.id) == cid:
            w = rec.right - rec.left
            h = rec.bottom - rec.top
            if cid == -2:  # màscara: dimensions pròpies
                ms = rec.mask_data
                w = ms.right - ms.left
                h = ms.bottom - ms.top
            arr = decompress(cd.data, cd.compression, w, h, depth, version)
            a = np.frombuffer(arr, ">u2" if depth == 16 else "u1")
            return a.reshape(h, w)
    return None


def main():
    psd = PSDImage.open(PSB)
    depth, version = psd.depth, psd.version
    for i, ly in enumerate(psd):
        if i not in (12, 13):
            continue
        rec = ly._record
        cids = [int(c.id) for c in rec.channel_info]
        clens = [len(cd.data) for cd in ly._channels]
        print(f"[{i}] '{ly.name}'")
        print(f"    canals ids={cids} bytes={clens} "
              f"clip={rec.clipping} flags={rec.flags} blend={rec.blend_mode}")
        a = canal(ly, -1, depth, version)
        if a is not None:
            a8 = a[::8, ::8]
            cob = float((a8 > 0).mean())
            print(f"    alfa: cobertura {cob:.4f} · mitjana {a8.mean()/655.35:.1f}%")
            op = a8 > 32768
            print(f"    alfa>50%: {float(op.mean()):.4f}")
            if 0 < op.sum() and cob < 0.5:
                r = canal(ly, 0, depth, version)[::8, ::8].astype(np.float32) / 65535
                g = canal(ly, 1, depth, version)[::8, ::8].astype(np.float32) / 65535
                b = canal(ly, 2, depth, version)[::8, ::8].astype(np.float32) / 65535
                rr, gg, bb = r[op], g[op], b[op]
                print(f"    RGB al pintat: R {rr.mean():.3f} G {gg.mean():.3f} "
                      f"B {bb.mean():.3f}")
        m = canal(ly, -2, depth, version)
        if m is not None:
            print(f"    màscara: {m.shape} · mitjana {m.mean()/655.35:.1f}%")
        else:
            print("    sense màscara")


if __name__ == "__main__":
    main()
