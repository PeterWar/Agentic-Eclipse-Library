"""V21, pas 4: les dues capes noves i el PSB.

[0] Auditoria del retoc de Pere a la V19: es decodifiquen les màscares vives
    (Sony i FONS) i es comparen amb les nostres; el flatten fa servir LES
    SEVES. Mostreig de contingut per detectar retocs de píxels.
[1] CAPA ESTRELLES: detecció sobre l'apilat registrat (net i afinat), discos
    suaus, contingut = excés sobre el fons local, mode Linear Dodge.
    Mètrica de qualitat: elongació de les estrelles abans (capa 12) i ara.
[2] CAPA EARTHSHINE: el disc de l'apilat lunar, màscara suau dins del limbe.
[3] PSB: la V19 de Pere + les dues capes; fusionada nova; portes; Photoshop.
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
import fes_v14_pere as FP

B = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/"
SRC = B + "CapesTotalsV19.psb"          # el re-save de Pere (només lectura)
DST = B + "CapesTotalsV21.psb"
SOL = (6469.2, 6757.6)
RS = 455.5
T0 = time.time()


def marca(txt):
    print(f"[{time.time()-T0:7.1f}s] {txt}", flush=True)


def canal_cru(layer, cid, depth, version):
    from psd_tools.compression import decompress
    rec = layer._record
    for info, cd in zip(rec.channel_info, layer._channels):
        if int(info.id) == cid:
            w, h = rec.right - rec.left, rec.bottom - rec.top
            if cid == -2 and rec.mask_data is not None:
                ms = rec.mask_data
                w, h = ms.right - ms.left, ms.bottom - ms.top
            arr = decompress(cd.data, cd.compression, w, h, depth, version)
            return np.frombuffer(arr, ">u2" if depth == 16 else "u1").reshape(h, w)
    return None


def main():
    from psd_tools import PSDImage
    from psd_tools.constants import Compression, BlendMode
    from psd_tools.psd.image_data import ImageData
    from psb_utils import add_pixel_layer, add_mask16, finalize_lr16

    psd = PSDImage.open(SRC)
    d_, v_ = psd.depth, psd.version
    capes = list(psd)
    assert len(capes) == 14, f"esperava 14 capes, n'hi ha {len(capes)}"
    W, H = psd.width, psd.height
    l12 = capes[12]
    lfons = capes[13]
    assert lfons.name.startswith("FONS_PER_RAIG")

    marca("[0] auditoria del retoc de Pere")
    m_sony = canal_cru(l12, -2, d_, v_)
    m_fons = canal_cru(lfons, -2, d_, v_)
    m_sony_o = np.load(os.path.join(CAU19, "mask_v18.npy"), mmap_mode="r")
    m_fons_o = np.load(os.path.join(CAUF, "mask_rampa16.npy"), mmap_mode="r")
    for nom, a, o in (("màscara Sony", m_sony, m_sony_o),
                      ("màscara FONS", m_fons, m_fons_o)):
        dif = np.abs(a[::8, ::8].astype(np.int32) - o[::8, ::8])
        print(f"    {nom}: dif max {dif.max()} · frac>1% {float((dif>655).mean()):.5f}")
    s12G = canal_cru(l12, 1, d_, v_)
    s12G_o = np.load(os.path.join(CAU19, "sony_v18_rgb16.npy"), mmap_mode="r")
    dif = np.abs(s12G[::16, ::16].astype(np.int32) - s12G_o[::16, ::16, 1])
    print(f"    contingut Sony (G ::16): dif max {dif.max()} · "
          f"frac>1% {float((dif>655).mean()):.5f}")
    fonsG = canal_cru(lfons, 1, d_, v_)
    fonsG_o = np.load(os.path.join(CAUF, "B_v19_rgb16.npy"), mmap_mode="r")
    dif = np.abs(fonsG[::16, ::16].astype(np.int32) - fonsG_o[::16, ::16, 1])
    print(f"    contingut FONS (G ::16): dif max {dif.max()} · "
          f"frac>1% {float((dif>655).mean()):.5f}")
    del s12G, fonsG, dif

    marca("[1] capa ESTRELLES de l'apilat registrat")
    ap = np.load(os.path.join(CAU, "apilat_estrelles_rgb.npy"), mmap_mode="r")
    tres = np.load(os.path.join(CAU, "apilat_estrelles_tres.npy"), mmap_mode="r")
    meta = json.load(open(os.path.join(CAU, "apilats_meta.json")))
    G = np.asarray(ap[..., 1], np.float32)
    fons = cv2.GaussianBlur(cv2.medianBlur(G, 5), (0, 0), 10.0)
    D = G - fons
    del fons
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    rad = np.hypot(xx - SOL[0], yy - SOL[1]) / RS
    NBb, lg0, lg1 = 48, np.log(1.8), np.log(20.0)
    bidx = np.clip(((np.log(np.maximum(rad, 1e-3)) - lg0)
                    / ((lg1 - lg0) / NBb)).astype(np.int16), 0, NBb - 1)
    med_b = np.zeros(NBb, np.float32)
    sig_b = np.full(NBb, 1e9, np.float32)
    tr = np.asarray(tres)
    Ds, bs, ts = D[::3, ::3], bidx[::3, ::3], tr[::3, ::3]
    for bb in range(NBb):
        v = Ds[(bs == bb) & ts]
        if v.size > 300:
            md = np.median(v)
            med_b[bb], sig_b[bb] = md, 1.4826 * np.median(np.abs(v - md))
    del Ds, bs, ts
    cand = (D > (med_b + 4.0 * sig_b)[bidx]) & tr & (rad > 1.9)
    ncc, lab, st, cen = cv2.connectedComponentsWithStats(
        cand.astype(np.uint8), 8)
    del cand
    est = []
    for i in range(1, ncc):
        x0, y0, wc, hc, area = st[i]
        if area < 3 or area > 200 or wc > 22 or hc > 22:
            continue
        if max(wc, hc) > 3 * max(min(wc, hc), 1):
            continue
        sub = np.where(lab[y0:y0 + hc, x0:x0 + wc] == i,
                       D[y0:y0 + hc, x0:x0 + wc], -1e9)
        iy, ix = np.unravel_index(np.argmax(sub), sub.shape)
        py, px = y0 + iy, x0 + ix
        if not (16 <= px < W - 16 and 16 <= py < H - 16):
            continue
        bb = int(bidx[py, px])
        if D[py, px] < med_b[bb] + 5.0 * sig_b[bb]:
            continue
        est.append((px, py, float(D[py, px] - med_b[bb]), int(area)))
    del lab
    est = np.array(est, np.float32) if est else np.zeros((0, 4), np.float32)
    marca(f"    estrelles a l'apilat registrat: {len(est)} (de {ncc-1} comp.)")

    # elongació: l'apilat registrat vs la capa 12 (el «lio» quantificat)
    def elong(img, xs, ys, R=7):
        e = []
        for x, y in zip(xs, ys):
            x, y = int(x), int(y)
            wdw = img[y - R:y + R + 1, x - R:x + R + 1].astype(np.float64)
            wdw = wdw - np.median(wdw)
            wdw[wdw < 0] = 0
            tot = wdw.sum()
            if tot <= 0:
                continue
            oy, ox = np.mgrid[-R:R + 1, -R:R + 1]
            mx = (wdw * ox).sum() / tot
            my = (wdw * oy).sum() / tot
            vxx = (wdw * (ox - mx) ** 2).sum() / tot
            vyy = (wdw * (oy - my) ** 2).sum() / tot
            vxy = (wdw * (ox - mx) * (oy - my)).sum() / tot
            tr_ = vxx + vyy
            dd = math.sqrt(max((vxx - vyy) ** 2 + 4 * vxy ** 2, 0))
            l1 = (tr_ + dd) / 2
            l2 = max((tr_ - dd) / 2, 1e-6)
            e.append(math.sqrt(l1 / l2))
        return np.array(e)
    top = est[np.argsort(-est[:, 2])][:120]
    S12full = np.asarray(np.load(os.path.join(CAU19, "sony_v18_rgb16.npy"),
                                 mmap_mode="r")[..., 1], np.float32)
    e_ara = elong(G, top[:, 0], top[:, 1])
    e_abans = elong(S12full, top[:, 0], top[:, 1])
    print(f"    elongació (mediana, 120 brillants): capa 12 {np.median(e_abans):.2f}"
          f" → apilat registrat {np.median(e_ara):.2f}")
    del S12full

    # discos + contingut additiu
    S = np.zeros((H, W), np.float32)
    for x, y, c0, area in est:
        x, y = int(x), int(y)
        Rs_ = float(np.clip(2.0 * math.sqrt(area / math.pi) + 3.0, 5.0, 12.0))
        R_ = int(math.ceil(Rs_))
        oy, ox = np.mgrid[-R_:R_ + 1, -R_:R_ + 1]
        t = np.clip((Rs_ - np.hypot(oy, ox)) / 2.5, 0, 1)
        s_ = (0.5 - 0.5 * np.cos(np.pi * t)).astype(np.float32)
        reg = S[y - R_:y + R_ + 1, x - R_:x + R_ + 1]
        np.maximum(reg, s_, out=reg)
    E16 = np.zeros((H, W, 3), np.uint16)
    dins = S > 0.001
    for ch in range(3):
        A = np.asarray(ap[..., ch], np.float32)
        fl = cv2.GaussianBlur(cv2.medianBlur(A, 5), (0, 0), 10.0)
        e = np.clip(A - fl, 0, 65535)
        E16[..., ch] = np.where(dins, e, 0).astype(np.uint16)
        del A, fl, e
    np.save(os.path.join(CAU, "capa_estrelles_E16.npy"), E16)
    np.save(os.path.join(CAU, "capa_estrelles_mask.npy"),
            np.clip(np.rint(S * 65535), 0, 65535).astype(np.uint16))
    np.save(os.path.join(CAU, "estrelles_v21.npy"), est)
    del G, D, ap
    marca("[1] capa ESTRELLES construïda")

    marca("[2] capa EARTHSHINE")
    apl = np.load(os.path.join(CAU, "apilat_lluna_rgb.npy"))
    trl = np.load(os.path.join(CAU, "apilat_lluna_tres.npy"))
    ya, yb_ = meta["banda_lluna"]
    mx16, my16 = meta["lluna_base_canvas"]
    Rl = meta["rl_canvas"]
    hL = apl.shape[0]
    yyL = np.arange(hL, dtype=np.float32)[:, None] + ya
    xxL = np.arange(W, dtype=np.float32)[None, :]
    dl = np.hypot(xxL - mx16, yyL - my16)
    mask_d = (np.clip(((Rl - 8.0) - dl) / 5.0, 0, 1)
              * trl.astype(np.float32)).astype(np.float32)
    x0e = max(0, int(mx16 - Rl - 40)); x1e = min(W, int(mx16 + Rl + 40))
    Ec = apl[:, x0e:x1e]
    Mc = np.clip(np.rint(mask_d[:, x0e:x1e] * 65535), 0, 65535).astype(np.uint16)
    disc = mask_d[:, x0e:x1e] > 0.5
    med = [round(float(np.median(Ec[..., j][disc])), 4) for j in range(3)] \
        if disc.sum() > 500 else None
    print(f"    earthshine: bbox x[{x0e},{x1e}) y[{ya},{yb_}) · disc {int(disc.sum())} px"
          f" · mediana RGB (16b/65535) {med}")
    marca("[2] capa EARTHSHINE construïda")

    marca("[3] el PSB")
    tb = psd._record.layer_and_mask_information.tagged_blocks
    for kk in list(tb.keys()):
        kb = kk.value if hasattr(kk, "value") else kk
        if kb not in (b"Lr16", b"Mt16"):
            del tb[kk]
    print("    blocs globals heretats fora (la trampa 8BIM/8B64)", flush=True)
    nom_e = ("EARTHSHINE · apilat 5f registrat a la LLUNA (base DSC06993, "
             "rotació de camp compensada) (V21)")
    capa_e = add_pixel_layer(psd, np.ascontiguousarray(Ec), nom_e,
                             top=int(ya), left=int(x0e),
                             blend=BlendMode.NORMAL,
                             compression=Compression.ZIP)
    add_mask16(capa_e, np.ascontiguousarray(Mc), top=int(ya), left=int(x0e))
    nom_s = (f"ESTRELLES · {len(est)} fonts de l'apilat registrat a les "
             "estrelles (plate-solve, base DSC06993) · Linear Dodge (V21)")
    capa_s = add_pixel_layer(psd, E16, nom_s, top=0, left=0,
                             blend=BlendMode.LINEAR_DODGE,
                             compression=Compression.ZIP)
    add_mask16(capa_s, np.load(os.path.join(CAU, "capa_estrelles_mask.npy")),
               top=0, left=0)
    finalize_lr16(psd)
    marca("    capes inserides i Lr16 reconstruït")

    # fusionada: flatten de la V19 (amb LES SEVES màscares vives) + les noves
    mF = m_fons.astype(np.float32) / 65535.0
    mS_ = m_sony.astype(np.float32) / 65535.0
    S12r = np.load(os.path.join(CAU19, "sony_v18_rgb16.npy"), mmap_mode="r")
    V16r = np.load(os.path.join(CAU18, "vixen_sota_rgb16.npy"), mmap_mode="r")
    A8r = np.load(os.path.join(CAU18, "vixen_sota_alfa8.npy"), mmap_mode="r")
    Bf = np.load(os.path.join(CAUF, "B_v19_rgb16.npy"), mmap_mode="r")
    a_v = np.asarray(A8r, np.float32) / 255.0
    Sm = np.zeros((H, W), np.float32)
    Sm[:] = np.load(os.path.join(CAU, "capa_estrelles_mask.npy")
                    ).astype(np.float32) / 65535.0
    plans_ = []
    alfaT = mS_ + a_v * (1 - mS_)
    alfaT = alfaT + mF * (1 - alfaT)
    mask_e_full = np.zeros((H, W), np.float32)
    mask_e_full[ya:yb_, x0e:x1e] = Mc.astype(np.float32) / 65535.0
    for ch in range(3):
        C = (np.asarray(S12r[..., ch], np.float32) * mS_
             + np.asarray(V16r[..., ch], np.float32) * a_v * (1 - mS_))
        F = C * (1 - mF) + np.asarray(Bf[..., ch], np.float32) * mF
        del C
        Efull = np.zeros((H, W), np.float32)
        Efull[ya:yb_, x0e:x1e] = Ec[..., ch]
        F = F * (1 - mask_e_full) + Efull * mask_e_full
        del Efull
        F = F + E16[..., ch].astype(np.float32) * Sm
        F = F + (1.0 - alfaT) * 65535.0
        plans_.append(np.clip(F + 0.5, 0, 65535).astype(">u2").tobytes())
        del F
        marca(f"    fusionada: canal {ch}")
    n_can = psd._record.header.channels
    if n_can == 4:
        plans_.append(np.clip(np.rint(alfaT * 65535.0), 0, 65535)
                      .astype(">u2").tobytes())
    idata = ImageData(compression=Compression.RAW)
    idata.set_data(plans_, psd._record.header)
    psd._record.image_data = idata
    if getattr(psd, "_updated", False):
        psd._updated = False
    del plans_
    marca("    desant…")
    psd.save(DST)
    marca(f"    {DST} · {os.path.getsize(DST)/1e9:.2f} GB")

    p2 = PSDImage.open(DST)
    capes2 = list(p2)
    assert (p2.width, p2.height) == (W, H) and len(capes2) == 16, len(capes2)
    src2 = PSDImage.open(SRC)
    assert list(src2)[0]._channels[1].data == capes2[0]._channels[1].data
    print("    fidelitat: canal R de la capa 0 byte a byte ✓", flush=True)
    r = subprocess.run(["sips", "-g", "pixelWidth", DST],
                       capture_output=True, text=True)
    assert f"pixelWidth: {W}" in r.stdout + r.stderr
    r = subprocess.run([os.path.join(AQUI, "porta_photoshop.sh"), DST],
                       capture_output=True, text=True, timeout=1800)
    print("    Photoshop diu:", (r.stdout + r.stderr).strip(), flush=True)

    rebut = {"src": SRC, "desti": DST,
             "n_estrelles": int(len(est)),
             "elongacio_mediana": {"capa12_abans": float(np.median(e_abans)),
                                   "apilat_ara": float(np.median(e_ara))},
             "earthshine": {"bbox": [int(x0e), int(ya), int(x1e), int(yb_)],
                            "lluna_canvas": [mx16, my16], "rl_canvas": Rl,
                            "mediana_rgb": med},
             "fits": meta["fits_deg_t"],
             "capes": [ly.name for ly in capes2],
             "bytes": os.path.getsize(DST)}
    json.dump(rebut, open(os.path.join(CAU, "rebut_v21.json"), "w"),
              indent=1, ensure_ascii=False)
    marca("rebut desat; fet")


if __name__ == "__main__":
    main()
