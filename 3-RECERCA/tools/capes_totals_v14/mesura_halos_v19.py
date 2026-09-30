"""Mesura els halos marcats per Pere sobre el compost real de la seva V18.

1. Extreu la capa Sony [12] del seu save (RGB16) i la desa al cau_v19.
2. Compost a 1/4 = Sony·M + Vixen·α·(1−M) (el que Pere veu, sense els traços).
3. Per cada regió marcada: perfil radial al sector (G, R/G, B/G) del compost,
   del Vixen de sota i de la Sony sola, més el ρ aplicat a la V18.
"""
from __future__ import annotations

import json
import os

import numpy as np
from psd_tools import PSDImage
from psd_tools.compression import decompress

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v19")
CAU18 = os.path.join(AQUI, "cau_v18")
B = ("/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/"
     "1-Unint Capes/Capes Totals/")
PSB = B + "CapesTotalsV18.psb"
SOL = (6469.2, 6757.6)
RS = 455.5


def canal(layer, cid, depth, version):
    rec = layer._record
    for info, cd in zip(rec.channel_info, layer._channels):
        if int(info.id) == cid:
            w, h = rec.right - rec.left, rec.bottom - rec.top
            arr = decompress(cd.data, cd.compression, w, h, depth, version)
            return np.frombuffer(arr, ">u2" if depth == 16 else "u1").reshape(h, w)
    return None


def main():
    p_sony = os.path.join(CAU, "sony_v18_rgb16.npy")
    if not os.path.exists(p_sony):
        print("[1] extracció de la capa Sony [12] del save de Pere")
        psd = PSDImage.open(PSB)
        capes = list(psd)
        ly = capes[12]
        chs = [canal(ly, c, psd.depth, psd.version) for c in (0, 1, 2)]
        np.save(p_sony, np.stack(chs, -1))
        m = canal(ly, -2, psd.depth, psd.version)
        np.save(os.path.join(CAU, "mask_v18.npy"), m)
        del chs, m
    sony = np.load(p_sony, mmap_mode="r")
    mask = np.load(os.path.join(CAU, "mask_v18.npy"), mmap_mode="r")
    sota = np.load(os.path.join(CAU18, "vixen_sota_rgb16.npy"), mmap_mode="r")
    alfa = np.load(os.path.join(CAU18, "vixen_sota_alfa8.npy"), mmap_mode="r")

    # ¿la màscara de Pere és la mateixa que a la V18 nostra?
    m18 = np.load(os.path.join(CAU18, "sony_pere_mask16.npy"), mmap_mode="r")
    dif = np.abs(mask[::16, ::16].astype(np.int32) - m18[::16, ::16])
    print(f"màscara vs V18 nostra: max dif {dif.max()} (0 = idèntica al mostreig)")

    q = 4
    s4 = np.asarray(sony[::q, ::q], np.float32) / 65535.0
    v4 = np.asarray(sota[::q, ::q], np.float32) / 65535.0
    m4 = (np.asarray(mask[::q, ::q], np.float32) / 65535.0)[..., None]
    a4 = (np.asarray(alfa[::q, ::q], np.float32) / 255.0)[..., None]
    comp = s4 * m4 + v4 * a4 * (1 - m4)
    cobert = (m4[..., 0] + a4[..., 0] * (1 - m4[..., 0])) > 0.98
    np.save(os.path.join(CAU, "compost_pere_q4.npy"), comp)

    rho = np.load(os.path.join(CAU18, "rho_q4.npy"))  # (Hq,Wq,3) de la V18

    Hq, Wq = comp.shape[:2]
    yy = np.arange(Hq, dtype=np.float32)[:, None] * q
    xx = np.arange(Wq, dtype=np.float32)[None, :] * q
    rad = np.hypot(xx - SOL[0], yy - SOL[1]) / RS
    az = np.degrees(np.arctan2(-(yy - SOL[1]), xx - SOL[0]))

    regs = json.load(open(os.path.join(CAU, "regions_v19.json")))
    for fam in ("verd", "taronja"):
        for z in regs[fam]:
            a0 = z["az_med"]
            dz = ((az - a0 + 180) % 360) - 180
            sec = (np.abs(dz) < 12) & cobert
            print(f"\n=== {fam.upper()} az {a0:+.1f}° "
                  f"(marca r {z['r_min']:.2f}-{z['r_max']:.2f}) ===")
            print("  r · compG · vixG · sonyG || C:R/G B/G · V:R/G B/G · "
                  "S:R/G B/G || ρG · ρR/ρG · ρB/ρG · M")
            for rr in np.arange(max(3.0, z["r_min"] - 1.0),
                                min(9.0, z["r_max"] + 1.5), 0.25):
                mm = sec & (np.abs(rad - rr) < 0.125)
                if mm.sum() < 30:
                    continue
                C = [float(np.median(comp[..., i][mm])) for i in range(3)]
                V = [float(np.median(v4[..., i][mm])) for i in range(3)]
                S = [float(np.median(s4[..., i][mm])) for i in range(3)]
                P = [float(np.median(rho[..., i][mm])) for i in range(3)]
                M = float(np.median(m4[..., 0][mm]))
                print(f"  {rr:.2f} · {C[1]:.4f} · {V[1]:.4f} · {S[1]:.4f} || "
                      f"{C[0]/max(C[1],1e-4):.3f} {C[2]/max(C[1],1e-4):.3f} · "
                      f"{V[0]/max(V[1],1e-4):.3f} {V[2]/max(V[1],1e-4):.3f} · "
                      f"{S[0]/max(S[1],1e-4):.3f} {S[2]/max(S[1],1e-4):.3f} || "
                      f"{P[1]:.3f} · {P[0]/P[1]:.3f} · {P[2]/P[1]:.3f} · {M:.2f}")


if __name__ == "__main__":
    main()
