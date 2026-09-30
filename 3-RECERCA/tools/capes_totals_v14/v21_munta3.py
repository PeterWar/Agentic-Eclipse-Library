"""V21 (segona ronda): capa ESTRELLES només-catàleg + capa EARTHSHINE asimètrica.

Sobrescriu CapesTotalsV21.psb (el lliurable nostre; Pere va refusar la
primera ronda: estrelles fake i earthshine invisible).
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import time

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
CAU18 = os.path.join(AQUI, "cau_v18")
CAU19 = os.path.join(AQUI, "cau_v19")
CAUF = os.path.join(CAU19, "fons")
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "encaix_sony"))

B = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/"
SRC = B + "CapesTotalsV19.psb"
DST = B + "CapesTotalsV21.psb"
T0 = time.time()


def marca(txt):
    print(f"[{time.time()-T0:7.1f}s] {txt}", flush=True)


def main():
    from psd_tools import PSDImage
    from psd_tools.constants import Compression, BlendMode
    from psd_tools.psd.image_data import ImageData
    from psb_utils import add_pixel_layer, add_mask16, finalize_lr16
    from v21_munta import canal_cru

    psd = PSDImage.open(SRC)
    d_, v_ = psd.depth, psd.version
    capes = list(psd)
    assert len(capes) == 14
    W, H = psd.width, psd.height
    l12, lfons = capes[12], capes[13]
    m_sony = canal_cru(l12, -2, d_, v_).astype(np.float32) / 65535.0
    m_fons = canal_cru(lfons, -2, d_, v_).astype(np.float32) / 65535.0
    marca("màscares vives decodificades")

    # ---- capa ESTRELLES (només catàleg: 87 fonts amb HIP/TYC) ----
    est = np.load(os.path.join(CAU, "estrelles_v21_final.npy"))
    ap = np.load(os.path.join(CAU, "apilat_estrelles_rgb.npy"), mmap_mode="r")
    S = np.zeros((H, W), np.float32)
    for x, y, ns, _ in est:
        x, y = int(x), int(y)
        Rs_ = float(np.clip(3.5 + 0.6 * math.log1p(max(ns - 3.5, 0)) * 3.0,
                            5.0, 11.0))
        R_ = int(math.ceil(Rs_))
        oy, ox = np.mgrid[-R_:R_ + 1, -R_:R_ + 1]
        t = np.clip((Rs_ - np.hypot(oy, ox)) / 2.5, 0, 1)
        s_ = (0.5 - 0.5 * np.cos(np.pi * t)).astype(np.float32)
        reg = S[y - R_:y + R_ + 1, x - R_:x + R_ + 1]
        np.maximum(reg, s_, out=reg)
    dins = S > 0.001
    E16 = np.zeros((H, W, 3), np.uint16)
    for ch in range(3):
        A = np.asarray(ap[..., ch], np.float32)
        fl = cv2.GaussianBlur(cv2.medianBlur(A, 5), (0, 0), 10.0)
        e = np.clip(A - fl, 0, 65535)
        E16[..., ch] = np.where(dins, e, 0).astype(np.uint16)
        del A, fl, e
    S16m = np.clip(np.rint(S * 65535), 0, 65535).astype(np.uint16)
    marca(f"capa ESTRELLES ({len(est)} fonts del catàleg)")

    # ---- capa EARTHSHINE (el disc registrat a la Lluna: la DADA) ----
    meta = json.load(open(os.path.join(CAU, "apilats_meta.json")))
    ya, yb = meta["banda_lluna"]
    mx16, my16 = meta["lluna_base_canvas"]
    Rl = meta["rl_canvas"]
    apl = np.load(os.path.join(CAU, "apilat_lluna_rgb.npy"))
    trl = np.load(os.path.join(CAU, "apilat_lluna_tres.npy"))
    hL = apl.shape[0]
    yyL = np.arange(hL, dtype=np.float32)[:, None] + ya
    xxL = np.arange(W, dtype=np.float32)[None, :]
    dlq = np.hypot(xxL - mx16, yyL - my16)
    mask_d = (np.clip(((Rl - 8.0) - dlq) / 5.0, 0, 1)
              * trl.astype(np.float32)).astype(np.float32)
    x0e = max(0, int(mx16 - Rl - 30))
    x1e = min(W, int(mx16 + Rl + 30))
    Ec = np.ascontiguousarray(apl[:, x0e:x1e])
    Mc = np.ascontiguousarray(np.clip(np.rint(mask_d[:, x0e:x1e] * 65535),
                                      0, 65535).astype(np.uint16))
    marca("capa EARTHSHINE (disc registrat) retallada al seu bbox")

    # ---- PSB ----
    tb = psd._record.layer_and_mask_information.tagged_blocks
    for kk in list(tb.keys()):
        kb = kk.value if hasattr(kk, "value") else kk
        if kb not in (b"Lr16", b"Mt16"):
            del tb[kk]
    nom_e = ("EARTHSHINE+VEL · disc registrat a la LLUNA (5f, rotació "
             "compensada, base DSC06993) · superfície lunar < ~1,5 % "
             "(extinció X=6,4) — vegeu rebut (V21)")
    capa_e = add_pixel_layer(psd, Ec, nom_e, top=int(ya), left=int(x0e),
                             blend=BlendMode.NORMAL, compression=Compression.ZIP)
    add_mask16(capa_e, Mc, top=int(ya), left=int(x0e))
    nom_s = (f"ESTRELLES · {len(est)} fonts del catàleg Tycho-2/Hipparcos "
             "(plate-solve DSC06993, fotometria forçada ≥3,5σ) · "
             "Linear Dodge (V21)")
    capa_s = add_pixel_layer(psd, E16, nom_s, top=0, left=0,
                             blend=BlendMode.LINEAR_DODGE,
                             compression=Compression.ZIP)
    add_mask16(capa_s, S16m, top=0, left=0)
    finalize_lr16(psd)
    marca("capes inserides i Lr16 reconstruït")

    # fusionada
    S12r = np.load(os.path.join(CAU19, "sony_v18_rgb16.npy"), mmap_mode="r")
    V16r = np.load(os.path.join(CAU18, "vixen_sota_rgb16.npy"), mmap_mode="r")
    A8r = np.load(os.path.join(CAU18, "vixen_sota_alfa8.npy"), mmap_mode="r")
    Bf = np.load(os.path.join(CAUF, "B_v19_rgb16.npy"), mmap_mode="r")
    a_v = np.asarray(A8r, np.float32) / 255.0
    alfaT = m_sony + a_v * (1 - m_sony)
    alfaT = alfaT + m_fons * (1 - alfaT)
    Sm = S16m.astype(np.float32) / 65535.0
    me_full = np.zeros((H, W), np.float32)
    me_full[ya:yb, x0e:x1e] = Mc.astype(np.float32) / 65535.0
    plans_ = []
    for ch in range(3):
        C = (np.asarray(S12r[..., ch], np.float32) * m_sony
             + np.asarray(V16r[..., ch], np.float32) * a_v * (1 - m_sony))
        F = C * (1 - m_fons) + np.asarray(Bf[..., ch], np.float32) * m_fons
        del C
        Ef = np.zeros((H, W), np.float32)
        Ef[ya:yb, x0e:x1e] = Ec[..., ch]
        F = F * (1 - me_full) + Ef * me_full
        del Ef
        F = F + E16[..., ch].astype(np.float32) * Sm
        F = F + (1.0 - alfaT) * 65535.0
        plans_.append(np.clip(F + 0.5, 0, 65535).astype(">u2").tobytes())
        del F
        marca(f"fusionada: canal {ch}")
    if psd._record.header.channels == 4:
        plans_.append(np.clip(np.rint(alfaT * 65535.0), 0, 65535)
                      .astype(">u2").tobytes())
    idata = ImageData(compression=Compression.RAW)
    idata.set_data(plans_, psd._record.header)
    psd._record.image_data = idata
    if getattr(psd, "_updated", False):
        psd._updated = False
    del plans_
    marca("desant…")
    psd.save(DST)
    marca(f"{DST} · {os.path.getsize(DST)/1e9:.2f} GB")

    p2 = PSDImage.open(DST)
    capes2 = list(p2)
    assert (p2.width, p2.height) == (W, H) and len(capes2) == 16
    src2 = PSDImage.open(SRC)
    assert list(src2)[0]._channels[1].data == capes2[0]._channels[1].data
    print("    fidelitat: capa 0 byte a byte ✓", flush=True)
    r = subprocess.run(["sips", "-g", "pixelWidth", DST],
                       capture_output=True, text=True)
    assert f"pixelWidth: {W}" in r.stdout + r.stderr
    r = subprocess.run([os.path.join(AQUI, "porta_photoshop.sh"), DST],
                       capture_output=True, text=True, timeout=1800)
    print("    Photoshop diu:", (r.stdout + r.stderr).strip(), flush=True)
    json.dump({"capes": [ly.name for ly in capes2],
               "n_estrelles_cataleg": int(len(est)),
               "bytes": os.path.getsize(DST)},
              open(os.path.join(CAU, "rebut_v21b.json"), "w"), indent=1,
              ensure_ascii=False)
    marca("fet")


if __name__ == "__main__":
    main()
