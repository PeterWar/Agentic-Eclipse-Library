"""CapesTotalsV18 — la V17 de Pere sense halos: la Sony igualada en baixa freqüència al Vixen.

## El diagnòstic (mesurat sobre la V17 tal com Pere l'ha deixada)

Pere ha re-encès les capes 08-01 (el compost Vixen de sota és sòlid i llis: alfa
1,00, perfil 0,74 → 0,36 entre 1,75 i 6 R☉), ha corregit la capa Sony amb Camera
Raw (EL FORMAT CANÒNIC: interior neutre ~0,90 que cau a cel FOSC i BLAU, 0,28-0,41
amb B/G 1,22 al camp llunyà; ombres p0,5 ≈ 0,075-0,105) i ha mogut la màscara de
la Sony a una rampa 3,75 → 5,0 R☉. Els halos que ha pintat en vermell (9 arcs a
3,6-4,6 R☉) són EXACTAMENT la banda de transició: allà la Sony és un 8-18 % més
brillant que el Vixen de sota (0,531 vs 0,451 a 4,0 R☉) i el perfil final fa un
bony anular de +3-7 %.

## La cura

**Igualar el camp de BAIXA FREQÜÈNCIA de la Sony al del compost Vixen de sota,
per canal, a tota la zona on conviuen** — i relaxar la correcció a 1 suaument
més enllà de la cobertura Vixen perquè el camp llunyà conservi el format canònic
de Pere. ρ_c = suau(V_c)/suau(S_c) (suavitzat normalitzat amb màscara, σ≈200 px),
S' = S·ρ*. Conseqüències:

- brillantor I color igualats alhora (ρ per canal), també en azimut (ρ és 2D:
  vinyetatge descentrat i asimetries entren sols);
- el detall fi de la Sony (estrelles, corona) intacte: ρ és ultra-suau;
- **robust a QUALSEVOL màscara**: sigui on sigui la costura, els dos costats són
  idèntics en baixa freqüència — el halo no pot existir per construcció;
- la màscara de Pere NO es toca (la rampa 3,75-5,0 és seva); la capa HALOS es
  deixa INVISIBLE (és el seu diagnòstic; encesa taparia el resultat).

⛔ Regles vives: blocs globals heretats fora (trampa 8BIM/8B64), canals de màscara
i edicions a 16 bits amb round-trip, porta Photoshop abans de lliurar.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v18")
sys.path.insert(0, AQUI)
import fes_v14_pere as FP

B = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/"
V17 = B + "CapesTotalsV17.psb"
DST = B + "CapesTotalsV18.psb"
SOL = (6469.2, 6757.6)
RS = 455.5
SIGMA_RHO = 200.0        # px: la baixa freqüència que s'iguala
SIGMA_EXT = 800.0        # px: difusió per estendre ρ més enllà de la cobertura
CLAMP = (0.6, 1.4)


def suau_masc(img, w, sigma):
    """Gaussiana normalitzada amb màscara: G(img·w)/G(w), i el suport G(w)."""
    num = cv2.GaussianBlur(img * w, (0, 0), sigma)
    den = cv2.GaussianBlur(w, (0, 0), sigma)
    return num / np.maximum(den, 1e-6), den


def main():
    t0 = time.time()
    print("[1/6] càrrega dels caus de la V17 de Pere")
    sota = np.load(os.path.join(CAU, "vixen_sota_rgb16.npy"), mmap_mode="r")
    alfa = np.load(os.path.join(CAU, "vixen_sota_alfa8.npy"), mmap_mode="r")
    sony = np.load(os.path.join(CAU, "sony_pere_rgb16.npy"), mmap_mode="r")
    mskp = np.load(os.path.join(CAU, "sony_pere_mask16.npy"), mmap_mode="r")
    H, W = alfa.shape
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    rad = np.hypot(xx - SOL[0], yy - SOL[1]) / RS

    print("[2/6] el camp de correcció ρ: perfil radial × harmònics azimutals (k≤2)")
    # ⛔ La primera versió feia ρ com a camp 2D lliure (suavitzat amb màscara) i
    #    la porta dels arcs la va caçar: perseguia la costura entre apuntaments
    #    de la Sony i hi creava un bony NOU de 2 % (0,0008 → 0,0200 a az −117°),
    #    i el clamp tocava sostre (p99 = 1,400). Un model suau PER CONSTRUCCIÓ
    #    (radial × Fourier azimutal baix) iguala vinyetatge i deriva de color
    #    però no pot perseguir estructura local: la costura queda com estava
    #    (bony 0,0008, invisible), que és el correcte.
    q = 4
    radq = rad[::q, ::q]
    sonyq = np.asarray(sony[::q, ::q], np.float32) / 65535.0
    sotaq = np.asarray(sota[::q, ::q], np.float32) / 65535.0
    alfaq = np.asarray(alfa[::q, ::q], np.float32) / 255.0
    w = ((alfaq > 0.99) & (sotaq[..., 1] > 0.02) & (sonyq[..., 1] > 0.003)
         & (radq > 1.6))
    print(f"    zona on conviuen: {100*w.mean():.1f} % del llenç")
    Hq, Wq = radq.shape
    yyq = np.arange(Hq, dtype=np.float32)[:, None]
    xxq = np.arange(Wq, dtype=np.float32)[None, :]
    azq = np.arctan2(yyq * q - SOL[1], xxq * q - SOL[0])
    NB, R0, DR = 100, 1.7, 0.08          # calaixos radials 1,7 → 9,7 R☉
    NS = 24                               # sectors azimutals de 15°
    ib = np.clip(((radq - R0) / DR).astype(np.int32), -1, NB)
    isec = ((azq + np.pi) / (2 * np.pi / NS)).astype(np.int32) % NS
    K = 2                                 # harmònics
    th_s = (np.arange(NS) + 0.5) * 2 * np.pi / NS - np.pi
    base = [np.ones(NS)]
    for k in range(1, K + 1):
        base += [np.cos(k * th_s), np.sin(k * th_s)]
    Bm = np.stack(base, axis=1)           # NS × (2K+1)
    rho_pol = np.ones((NB, 720, 3), np.float32)
    sup_bin = np.zeros(NB, np.float32)
    th_d = np.linspace(-np.pi, np.pi, 720, endpoint=False)
    Bd = [np.ones(720)]
    for k in range(1, K + 1):
        Bd += [np.cos(k * th_d), np.sin(k * th_d)]
    Bd = np.stack(Bd, axis=1)
    dins = w & (ib >= 0) & (ib < NB)
    ibd, isd = ib[dins], isec[dins]
    idx = ibd * NS + isd
    for j in range(3):
        vals = np.log(np.clip(sotaq[..., j][dins] /
                              np.maximum(sonyq[..., j][dins], 1e-4), 0.5, 2.0))
        sums = np.bincount(idx, vals, NB * NS).reshape(NB, NS)
        cnts = np.bincount(idx, None, NB * NS).reshape(NB, NS)
        mitj = np.where(cnts > 30, sums / np.maximum(cnts, 1), np.nan)
        coef = np.full((NB, 2 * K + 1), np.nan, np.float32)
        for b in range(NB):
            bo = np.isfinite(mitj[b])
            if bo.sum() >= 2 * K + 2:
                coef[b], *_ = np.linalg.lstsq(Bm[bo], mitj[b][bo], rcond=None)
            if j == 0:
                sup_bin[b] = bo.mean()
        # suavitza els coeficients en r (gaussiana 1D, ignorant NaN)
        for cix in range(2 * K + 1):
            col = coef[:, cix]
            bo = np.isfinite(col)
            if bo.sum() < 3:
                coef[:, cix] = 0.0
                continue
            x = np.arange(NB, dtype=np.float32)
            colf = np.interp(x, x[bo], col[bo])
            coef[:, cix] = cv2.GaussianBlur(colf[None], (0, 0), 4.0)[0]
        rho_pol[:, :, j] = np.exp(coef @ Bd.T).astype(np.float32)
    # pes radial: 1 on hi ha suport, → 0 més enllà de la cobertura (suau, 1,5 R☉)
    supf = cv2.GaussianBlur(np.clip(sup_bin / 0.5, 0, 1)[None], (0, 0), 3.0)[0]
    quel = np.zeros(NB + 2, np.float32)
    quel[1:-1] = supf
    caual = np.clip(np.cumsum(quel[::-1])[::-1][1:-1] * 0, 0, 1)  # placeholder
    qrad = supf.copy()
    # més enllà de l'últim calaix amb suport, decau linealment en ~19 calaixos
    darrer = int(np.max(np.where(sup_bin > 0.3)[0])) if (sup_bin > 0.3).any() else 0
    for b in range(NB):
        if b > darrer:
            qrad[b] = max(0.0, 1.0 - (b - darrer) / 19.0)
    rho_pol = 1.0 + (rho_pol - 1.0) * qrad[:, None, None]
    # mostreig del camp polar al llenç (1/4)
    rb = np.clip((radq - R0) / DR - 0.5, 0.0, NB - 1.001)
    b0 = rb.astype(np.int32); fb = rb - b0
    ti = ((azq + np.pi) / (2 * np.pi) * 720).astype(np.int32) % 720
    rho = np.empty((Hq, Wq, 3), np.float32)
    for j in range(3):
        pj = rho_pol[..., j]
        rho[..., j] = (pj[b0, ti] * (1 - fb) + pj[np.minimum(b0 + 1, NB - 1), ti] * fb)
    rho[radq < R0] = rho_pol[0, :, :].mean(axis=0)[None, :]  # interior: valor pla
    # ⛔ SEGONA CAÇADA (porta de diferència): més enllà de l'últim calaix (9,7
    #    R☉) el mostreig quedava clavat al valor del calaix 99 —un ajust
    #    EXTRAPOLAT des dels sectors de cantonada— i tot el camp llunyà de Pere
    #    quedava tocat (p99 de la diferència +0,33). El camp llunyà és el seu
    #    format canònic i NO es toca: la correcció val completa fins a 5,5 R☉
    #    (la rampa de màscara de Pere és 3,75-5,0), es fon fins a 7,0, i és
    #    EXACTAMENT 1 més enllà.
    tt = np.clip((7.0 - radq) / 1.5, 0.0, 1.0).astype(np.float32)
    tt = tt * tt * (3.0 - 2.0 * tt)
    rho = 1.0 + (rho - 1.0) * tt[..., None]
    del tt
    del sonyq, sotaq, alfaq
    print(f"    ρ: G mediana {np.median(rho[..., 1]):.3f} · "
          f"p1-p99 [{np.percentile(rho[..., 1], 1):.3f}, "
          f"{np.percentile(rho[..., 1], 99):.3f}]  [{time.time()-t0:.0f}s]")
    np.save(os.path.join(CAU, "rho_q4.npy"), rho.astype(np.float32))

    print("[3/6] aplicació a resolució completa + perfil previst")
    sonyF = np.asarray(sony, np.float32) / 65535.0
    rhoF = np.dstack([cv2.resize(rho[..., j], (W, H), interpolation=cv2.INTER_LINEAR)
                      for j in range(3)])
    del rho
    sonyN = np.clip(sonyF * rhoF, 0.0, 1.0)
    # perfil final previst amb la màscara DE PERE
    mskF = np.asarray(mskp, np.float32) / 65535.0
    sotaF_G = np.asarray(sota[..., 1], np.float32) / 65535.0
    alfaF = np.asarray(alfa, np.float32) / 255.0
    print("    r · V_G · S'_G · M · FINAL_G (abans → ara)")
    perf = []
    for r0 in np.arange(3.0, 5.76, 0.25):
        z = (rad > r0 - 0.1) & (rad < r0 + 0.1)
        vg = float(np.median(sotaF_G[z]))
        sg0 = float(np.median(sonyF[..., 1][z]))
        sg = float(np.median(sonyN[..., 1][z]))
        mm = float(np.median(mskF[z]))
        f0 = sg0 * mm + vg * (1 - mm)
        f1 = sg * mm + vg * (1 - mm)
        perf.append({"r": float(r0), "V": vg, "S_nou": sg, "M": mm,
                     "final_abans": f0, "final_ara": f1})
        print(f"    {r0:4.2f} · {vg:.3f} · {sg:.3f} · {mm:.2f} · {f0:.3f} → {f1:.3f}")

    print("[4/6] verificació als 9 arcs pintats per Pere")
    blobs = json.load(open(os.path.join(CAU, "halos_blobs.json")))
    finalG_ab = sonyF[..., 1] * mskF + sotaF_G * (1 - mskF)
    finalG_ar = sonyN[..., 1] * mskF + sotaF_G * (1 - mskF)
    del sonyF
    ver = []
    for b in blobs:
        th0 = np.arctan2(b["cy"] - SOL[1], b["cx"] - SOL[0])
        az = np.arctan2(yy - SOL[1], xx - SOL[0])
        dth = np.abs(np.angle(np.exp(1j * (az - th0))))
        sec = dth < np.radians(15)
        rr = np.arange(b["r_Rsol"] - 0.8, b["r_Rsol"] + 0.85, 0.08)
        def bony(img):
            p = []
            for r0 in rr:
                z = sec & (rad > r0 - 0.04) & (rad < r0 + 0.04)
                p.append(float(np.median(img[z])) if z.sum() > 200 else np.nan)
            p = np.array(p)
            bo = np.isfinite(p)
            if bo.sum() < 8:
                return np.nan
            # bony = residu contra l'envolupant monòtona decreixent
            iso = np.minimum.accumulate(np.where(bo, p, np.inf))
            return float(np.nanmax(np.where(bo, p - iso, 0)))
        b_ab = bony(finalG_ab); b_ar = bony(finalG_ar)
        ver.append({"r": b["r_Rsol"], "az": b["az"], "bony_abans": b_ab,
                    "bony_ara": b_ar})
        print(f"    arc r {b['r_Rsol']:.2f} az {b['az']:+6.1f}°: bony "
              f"{b_ab:.4f} → {b_ar:.4f}")
    del finalG_ab, finalG_ar, sotaF_G, alfaF
    pitjor = max(v["bony_ara"] for v in ver if np.isfinite(v["bony_ara"]))
    print(f"    pitjor bony ara: {pitjor:.4f} (abans "
          f"{max(v['bony_abans'] for v in ver):.4f})")

    print("[5/6] construcció del PSB")
    from psd_tools import PSDImage
    from psd_tools.constants import ChannelID, Compression
    from psd_tools.compression import decompress
    from psd_tools.psd.image_data import ImageData
    psd = PSDImage.open(V17)
    ver_psd = psd._record.header.version
    tb = psd._record.layer_and_mask_information.tagged_blocks
    for kk in list(tb.keys()):
        kb = kk.value if hasattr(kk, "value") else kk
        if kb not in (b"Lr16", b"Mt16"):
            del tb[kk]
    print("    blocs globals heretats fora (la trampa 8BIM/8B64)")

    def reencoda(layer, cid, arr, depth=16):
        rec = layer._record
        for j, ci in enumerate(rec.channel_info):
            if int(ci.id) == cid:
                cd = layer._channels[j]
                raw = arr.astype(">u2").tobytes()
                h_, w_ = arr.shape
                cd.set_data(raw, w_, h_, depth, ver_psd)
                rec.channel_info[j] = type(ci)(ci.id, len(cd.data) + 2)
                assert decompress(cd.data, cd.compression, w_, h_, depth,
                                  ver_psd) == raw
                return
        raise KeyError(cid)

    capes = list(psd)
    l13 = next(l for l in capes if l.name.startswith("13_"))
    assert l13.bbox == (0, 0, W, H)
    s16 = np.clip(np.rint(sonyN * 65535.0), 0, 65535).astype(np.uint16)
    for j in range(3):
        reencoda(l13, j, s16[..., j])
    nom_nou = l13.name.split(" · dada")[0] + " · IGUALADA EN BAIXA FREQ AL VIXEN (V18)"
    l13.name = nom_nou
    lh = next(l for l in capes if l.name == "HALOS")
    lh.visible = False
    print("    13: contingut igualat · HALOS invisible (el diagnòstic es conserva)")

    print("    fusionada nova…", flush=True)
    compost = np.zeros((H, W, 3), np.float32)
    alfaT = np.zeros((H, W), np.float32)
    for layer in capes:
        if not layer.visible or layer is lh:
            continue
        if layer is l13:
            pix = sonyN
            al = mskF * (layer.opacity / 255.0)
        else:
            x0, y0, x1, y1 = layer.bbox
            arr = layer.numpy("color")
            pix = np.zeros((H, W, 3), np.float32)
            cob = np.zeros((H, W), np.float32)
            pix[max(0, y0):min(H, y1), max(0, x0):min(W, x1)] = arr[
                max(0, y0) - y0:min(H, y1) - y0, max(0, x0) - x0:min(W, x1) - x0]
            cob[max(0, y0):min(H, y1), max(0, x0):min(W, x1)] = 1.0
            mm, _, _ = FP._decodifica_mascara(layer, W, H)
            al = mm * cob * (layer.opacity / 255.0)
            del arr, cob, mm
        compost = compost * (1.0 - al[..., None]) + pix * al[..., None]
        alfaT = alfaT + al * (1.0 - alfaT)
        del pix, al
    rgbW = compost + (1.0 - alfaT[..., None])
    plans = [np.clip(np.rint(rgbW[..., j] * 65535.0), 0, 65535)
             .astype(">u2").tobytes() for j in range(3)]
    plans.append(np.clip(np.rint(alfaT * 65535.0), 0, 65535).astype(">u2").tobytes())
    idata = ImageData(compression=Compression.RAW)
    idata.set_data(plans, psd._record.header)
    psd._record.image_data = idata
    if getattr(psd, "_updated", False):
        psd._updated = False
    np.save(os.path.join(CAU, "compost_v18.npy"),
            np.clip(np.rint(compost * 65535.0), 0, 65535).astype(np.uint16))
    np.save(os.path.join(CAU, "alfa_v18.npy"),
            np.clip(np.rint(alfaT * 255.0), 0, 255).astype(np.uint8))
    del compost, rgbW, plans, sonyN, s16

    print("    desant…", flush=True)
    psd.save(DST)
    print(f"    {DST} · {os.path.getsize(DST)/1e9:.2f} GB · [{time.time()-t0:.0f}s]")

    print("[6/6] portes")
    p2 = PSDImage.open(DST)
    assert (p2.width, p2.height) == (W, H) and len(list(p2)) == 15
    r = subprocess.run(["sips", "-g", "pixelWidth", DST], capture_output=True, text=True)
    assert f"pixelWidth: {W}" in r.stdout + r.stderr
    r = subprocess.run([os.path.join(AQUI, "porta_photoshop.sh"), DST],
                       capture_output=True, text=True, timeout=900)
    print("    Photoshop diu:", (r.stdout + r.stderr).strip())
    rebut = {"v17_pere": V17, "desti": DST, "sol": SOL,
             "sigma_rho_px": SIGMA_RHO, "sigma_ext_px": SIGMA_EXT,
             "clamp": CLAMP, "perfil": perf, "arcs": ver,
             "pitjor_bony_ara": float(pitjor), "nom_capa": nom_nou,
             "bytes": os.path.getsize(DST)}
    json.dump(rebut, open(os.path.join(CAU, "rebut_v18.json"), "w"),
              indent=1, ensure_ascii=False)
    return rebut


if __name__ == "__main__":
    main()
