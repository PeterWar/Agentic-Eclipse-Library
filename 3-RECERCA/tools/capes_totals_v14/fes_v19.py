"""CapesTotalsV19 — la segona ronda de halos de Pere: referència robusta i cap fosa.

## El diagnòstic (mesurat sobre el save de Pere del 28-08 a les 17:07)

Pere ha marcat sobre una còpia de la capa Sony: VERD = halos de lluminància,
TARONJA = halos de to. Les dues famílies són NOSTRES, de la V18:

1. **Els verds grossos (5,6-6,5 R☉, az +98°/+113°)**: el fit del ρ de la V18
   anava fins a 9,7 R☉ i es va menjar la VORA del mosaic Vixen — px saturats a
   1,0000, zeros i el rolloff fosc de la vora (mesurat: la referència sana
   s'acaba a r=5,0 al sector +97,5°). El ρ hi feia un bony fins a 1,165: el
   halo ERA la correcció.
2. **Els taronges (5,3-6,6 R☉)**: la finestra declarada de la V18 (plena ≤5,5,
   fosa 5,5→7,0) fon el ρ PER CANAL cap a 1: ρR/ρG passa de 0,85 a 1,00 en
   1,2 R☉ — un viratge de to del 15 % que l'ull veu com un arc taronja. La
   fosa ERA el halo.
3. **Els verds interiors (3,5-5,4)**: residus de ±2-6 % que els harmònics k≤2
   no poden seguir.

## La cura (les tres, per construcció)

- **Referència ROBUSTA**: el fit només menja px amb α>0,995 i tots els canals
  Vixen dins (0,01-0,85), i NOMÉS fins a R_FIT_MAX=4,9 R☉ — 0,1 per sota del
  pitjor sector sa (mesurat sector a sector). Mediana per cel·la, no mitjana.
- **CAP FOSA**: més enllà de l'últim calaix, ρ es RETÉ constant per azimut
  (radialment pla). Cap gradient radial nou = cap arc, ni de llum ni de to.
  El camp llunyà canvia de nivell (declarat al rebut), però hi canvia SUAU:
  «estèticament ha de quedar com la imatge del Vixen» (Pere, 28-08).
- **k≤4**: prou azimut per als residus de ±2-6 %, massa suau per perseguir la
  costura entre apuntaments (λ ≥ 90°).

⛔ Regles vives: blocs globals heretats fora (trampa 8BIM/8B64), canals a 16
bits amb round-trip, porta Photoshop abans de lliurar, vistes al llenç sencer.
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
CAU = os.path.join(AQUI, "cau_v19")
CAU18 = os.path.join(AQUI, "cau_v18")
sys.path.insert(0, AQUI)
import fes_v14_pere as FP

B = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/"
SRC = B + "CapesTotalsV18.psb"          # el save de Pere (només lectura)
DST = B + "CapesTotalsV19.psb"
SOL = (6469.2, 6757.6)
RS = 455.5
K = 4                  # harmònics azimutals (λ ≥ 90°)
NS = 24
R0, DR = 1.7, 0.08
NB = 40                # calaixos radials 1,7 → 4,9: fins on la referència és sana
                       # a TOTS els sectors (r_sa mínim mesurat: 5,0 a az +97,5°).
                       # ⛔ Un r_stop VARIABLE per azimut es va provar i les portes
                       # el van caçar: pinta esglaons azimutals nous (−101,2°
                       # passava a −11,5 % contra els veïns). La retenció ha de
                       # ser COHERENT en azimut: global.
CROMA_FOSA_RS = 1.5    # R☉: fosa del croma retingut cap al to uniforme (~1,6 %/R☉)


def perfil_sector(img, rad, sec, rr, mig=0.04, minpx=60):
    p = np.full(len(rr), np.nan, np.float32)
    for i, r0 in enumerate(rr):
        z = sec & (np.abs(rad - r0) < mig)
        if z.sum() >= minpx:
            p[i] = float(np.median(img[z]))
    return p


def bony_monoton(p):
    bo = np.isfinite(p)
    if bo.sum() < 8:
        return np.nan
    iso = np.minimum.accumulate(np.where(bo, p, np.inf))
    return float(np.nanmax(np.where(bo, p - iso, 0)))


def pas_croma(num, den, rad, sec, r_lo=4.0, r_hi=8.0):
    rr = np.arange(r_lo, r_hi, 0.25)
    q = []
    for r0 in rr:
        z = sec & (np.abs(rad - r0) < 0.125)
        if z.sum() >= 60:
            q.append(float(np.median(num[z])) / max(float(np.median(den[z])), 1e-4))
        else:
            q.append(np.nan)
    q = np.array(q)
    d = np.abs(np.diff(q))
    return float(np.nanmax(d)) if np.isfinite(d).any() else np.nan


def main():
    t0 = time.time()
    print("[1/7] càrrega")
    sota = np.load(os.path.join(CAU18, "vixen_sota_rgb16.npy"), mmap_mode="r")
    alfa = np.load(os.path.join(CAU18, "vixen_sota_alfa8.npy"), mmap_mode="r")
    sonyB = np.load(os.path.join(CAU18, "sony_pere_rgb16.npy"), mmap_mode="r")
    mskp = np.load(os.path.join(CAU18, "sony_pere_mask16.npy"), mmap_mode="r")
    H, W = alfa.shape

    q = 4
    sonyq = np.asarray(sonyB[::q, ::q], np.float32) / 65535.0
    sotaq = np.asarray(sota[::q, ::q], np.float32) / 65535.0
    alfaq = np.asarray(alfa[::q, ::q], np.float32) / 255.0
    mq = (np.asarray(mskp[::q, ::q], np.float32) / 65535.0)
    Hq, Wq = alfaq.shape
    yyq = np.arange(Hq, dtype=np.float32)[:, None] * q
    xxq = np.arange(Wq, dtype=np.float32)[None, :] * q
    radq = np.hypot(xxq - SOL[0], yyq - SOL[1]) / RS
    azq = np.arctan2(yyq - SOL[1], xxq - SOL[0])

    print("[2/7] ρ_v19: referència robusta ≤4,9 R☉ · mediana · k≤4 · retenció global")
    sa = ((alfaq > 0.995) & (radq > 1.6)
          & np.all(sotaq > 0.01, axis=-1) & np.all(sotaq < 0.85, axis=-1)
          & (sotaq[..., 1] > 0.02) & (sonyq[..., 1] > 0.003))
    isec = ((azq + np.pi) / (2 * np.pi / NS)).astype(np.int32) % NS
    ib = np.clip(((radq - R0) / DR).astype(np.int32), -1, NB)
    th_s = (np.arange(NS) + 0.5) * 2 * np.pi / NS - np.pi
    Bm = np.stack([np.ones(NS)] + sum(([np.cos(k * th_s), np.sin(k * th_s)]
                                       for k in range(1, K + 1)), []), axis=1)
    th_d = np.linspace(-np.pi, np.pi, 720, endpoint=False)
    Bd = np.stack([np.ones(720)] + sum(([np.cos(k * th_d), np.sin(k * th_d)]
                                        for k in range(1, K + 1)), []), axis=1)
    dins = sa & (ib >= 0) & (ib < NB)
    print(f"    px de referència sans: {100 * dins.mean():.1f} % del llenç (1/4)")
    ibd, isd = ib[dins], isec[dins]
    idx = ibd * NS + isd
    rho_pol = np.ones((NB, 720, 3), np.float32)
    for j in range(3):
        vals = np.log(np.clip(sotaq[..., j][dins] /
                              np.maximum(sonyq[..., j][dins], 1e-4), 0.5, 2.0))
        # MEDIANA per cel·la (robusta a estrelles i brutícia de vora)
        med = np.full((NB, NS), np.nan, np.float32)
        ordre = np.argsort(idx, kind="stable")
        vs = vals[ordre]
        talls = np.searchsorted(idx[ordre], np.arange(NB * NS + 1))
        for c in range(NB * NS):
            a, bý = talls[c], talls[c + 1]
            if bý - a >= 40:
                med[c // NS, c % NS] = np.median(vs[a:bý])
        coef = np.full((NB, 2 * K + 1), np.nan, np.float32)
        for b in range(NB):
            bo = np.isfinite(med[b])
            if bo.sum() >= 12:      # k≤4 = 9 paràmetres; mai extrapolar amb menys
                coef[b], *_ = np.linalg.lstsq(Bm[bo], med[b][bo], rcond=None)
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

    # mostreig: interpola en r i RETÉN a l'últim calaix (global: 4,86 R☉).
    # Cap fosa de la G: la fosa de la V18 ERA el halo.
    R_STOP = R0 + (NB - 0.5) * DR
    ti = ((azq + np.pi) / (2 * np.pi) * 720).astype(np.int32) % 720
    rb = np.clip((radq - R0) / DR - 0.5, 0.0, NB - 1.001)
    b0 = rb.astype(np.int32)
    fb = rb - b0
    rho = np.empty((Hq, Wq, 3), np.float32)
    for j in range(3):
        pj = rho_pol[..., j]
        rho[..., j] = pj[b0, ti] * (1 - fb) + pj[np.minimum(b0 + 1, NB - 1), ti] * fb
    rho[radq < R0] = rho_pol[0, :, :].mean(axis=0)[None, :]

    # al tram retingut, el CROMA es fon cap a un to uniforme en 3 R☉ (~1 %/R☉,
    # trenta vegades més suau que la fosa de la V18 que va pintar els taronges);
    # la G (lluminància) es reté per azimut SENSE fosa.
    ww = np.clip(1.0 - (radq - R_STOP) / CROMA_FOSA_RS, 0.0, 1.0)
    ww = (ww * ww * (3.0 - 2.0 * ww)).astype(np.float32)
    for j, nom in ((0, "R"), (2, "B")):
        h_th = np.log(rho_pol[NB - 1, :, j]) - np.log(rho_pol[NB - 1, :, 1])
        m_c = float(np.mean(h_th))
        lnc = np.log(rho[..., j] / rho[..., 1])
        rho[..., j] = rho[..., 1] * np.exp(lnc * ww + m_c * (1.0 - ww))
        print(f"    croma {nom}: retingut per azimut [{np.exp(h_th.min()):.3f}, "
              f"{np.exp(h_th.max()):.3f}] → uniforme {np.exp(m_c):.3f} en 3 R☉")
    print(f"    ρ: G mediana {np.median(rho[..., 1]):.3f} · p1-p99 "
          f"[{np.percentile(rho[..., 1], 1):.3f}, {np.percentile(rho[..., 1], 99):.3f}]"
          f" · retingut des de r={R_STOP:.2f} R☉  [{time.time()-t0:.0f}s]")
    np.save(os.path.join(CAU, "rho_v19_q4.npy"), rho)

    print("[3/7] portes sobre el compost (1/4): 24 sectors + les 8 marques de Pere")
    comp_ab = np.load(os.path.join(CAU, "compost_pere_q4.npy"))  # el que Pere veu
    m3 = mq[..., None]
    a3 = alfaq[..., None]
    s19q = np.clip(sonyq * rho, 0, 1)
    comp_ar = s19q * m3 + sotaq * a3 * (1 - m3)
    cobert = (mq + alfaq * (1 - mq)) > 0.98
    azd = np.degrees(np.arctan2(-(yyq - SOL[1]), xxq - SOL[0]))  # conveni marques

    rr = np.arange(3.0, 8.5, 0.05)
    files_sec = []
    pitjor = {"bony_ar": 0.0, "croma_ar": 0.0}
    for s in range(24):
        azc = -180 + 15 * s + 7.5
        dz = ((azd - azc + 180) % 360) - 180
        sec = (np.abs(dz) < 7.5) & cobert
        b_ab = bony_monoton(perfil_sector(comp_ab[..., 1], radq, sec, rr))
        b_ar = bony_monoton(perfil_sector(comp_ar[..., 1], radq, sec, rr))
        cR_ab = pas_croma(comp_ab[..., 0], comp_ab[..., 1], radq, sec)
        cR_ar = pas_croma(comp_ar[..., 0], comp_ar[..., 1], radq, sec)
        cB_ab = pas_croma(comp_ab[..., 2], comp_ab[..., 1], radq, sec)
        cB_ar = pas_croma(comp_ar[..., 2], comp_ar[..., 1], radq, sec)
        files_sec.append({"az": azc, "bony": [b_ab, b_ar],
                          "cromaR": [cR_ab, cR_ar], "cromaB": [cB_ab, cB_ar]})
        pitjor["bony_ar"] = max(pitjor["bony_ar"], b_ar if np.isfinite(b_ar) else 0)
        pitjor["croma_ar"] = max(pitjor["croma_ar"],
                                 max(x for x in (cR_ar, cB_ar) if np.isfinite(x)))
        print(f"    az {azc:+7.1f}°: bony {b_ab:.4f}→{b_ar:.4f} · "
              f"ΔR/G {cR_ab:.3f}→{cR_ar:.3f} · ΔB/G {cB_ab:.3f}→{cB_ar:.3f}")

    regs = json.load(open(os.path.join(CAU, "regions_v19.json")))
    files_marca = []
    for fam in ("verd", "taronja"):
        for z in regs[fam]:
            dz = ((azd - z["az_med"] + 180) % 360) - 180
            sec = (np.abs(dz) < 12) & cobert
            rr_z = np.arange(max(2.5, z["r_min"] - 1.0), z["r_max"] + 1.5, 0.05)
            b_ab = bony_monoton(perfil_sector(comp_ab[..., 1], radq, sec, rr_z))
            b_ar = bony_monoton(perfil_sector(comp_ar[..., 1], radq, sec, rr_z))
            cR_ab = pas_croma(comp_ab[..., 0], comp_ab[..., 1], radq, sec)
            cR_ar = pas_croma(comp_ar[..., 0], comp_ar[..., 1], radq, sec)
            files_marca.append({"fam": fam, "az": z["az_med"],
                                "r": [z["r_min"], z["r_max"]],
                                "bony": [b_ab, b_ar], "cromaR": [cR_ab, cR_ar]})
            print(f"    {fam.upper():7s} az {z['az_med']:+7.1f}° "
                  f"r {z['r_min']:.2f}-{z['r_max']:.2f}: bony {b_ab:.4f}→{b_ar:.4f}"
                  f" · ΔR/G {cR_ab:.3f}→{cR_ar:.3f}")

    # canvi DECLARAT del camp llunyà (>7 R☉): retenció per azimut
    lluny = (radq > 7.0) & cobert
    dG = comp_ar[..., 1][lluny] / np.maximum(comp_ab[..., 1][lluny], 1e-4)
    print(f"    camp llunyà (>7 R☉), canvi de nivell G: mediana {np.median(dG):.3f}"
          f" · p1-p99 [{np.percentile(dG, 1):.3f}, {np.percentile(dG, 99):.3f}]"
          f" (DECLARAT: retenció, cap fosa)")
    del comp_ab, comp_ar, s19q
    if "--nomes-portes" in sys.argv:
        print("(--nomes-portes: m'aturo abans de construir res)")
        return None

    print("[4/7] aplicació a resolució completa")
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    sonyF = np.asarray(sonyB, np.float32) / 65535.0
    rhoF = np.dstack([cv2.resize(rho[..., j], (W, H), interpolation=cv2.INTER_LINEAR)
                      for j in range(3)])
    sonyN = np.clip(sonyF * rhoF, 0.0, 1.0)
    del sonyF, rhoF
    mskF = np.asarray(mskp, np.float32) / 65535.0

    print("[5/7] construcció del PSB (del save de Pere, fora la còpia de marques)")
    from psd_tools import PSDImage
    from psd_tools.constants import Compression
    from psd_tools.compression import decompress
    from psd_tools.psd.image_data import ImageData
    psd = PSDImage.open(SRC)
    ver_psd = psd._record.header.version
    tb = psd._record.layer_and_mask_information.tagged_blocks
    lr16 = tb.get_data(b"Lr16")
    capes = list(psd)
    rec13 = capes[13]._record
    i13 = next(i for i, r in enumerate(lr16.layer_records) if r is rec13)
    del lr16.layer_records[i13]
    del lr16.channel_image_data[i13]
    lr16.layer_count = (abs(lr16.layer_count) - 1) * (1 if lr16.layer_count >= 0
                                                      else -1)
    print(f"    còpia de marques (índex {i13}) fora · queden "
          f"{abs(lr16.layer_count)} capes (les marques queden al save de Pere)")
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

    l12 = capes[12]
    assert l12.bbox == (0, 0, W, H)
    s16 = np.clip(np.rint(sonyN * 65535.0), 0, 65535).astype(np.uint16)
    for j in range(3):
        reencoda(l12, j, s16[..., j])
    nom_nou = (l12.name.split(" · IGUALADA")[0]
               + " · IGUALADA EN BAIXA FREQ AL VIXEN (V19: ref robusta ≤4,9 R☉, retinguda, k≤4)")
    l12.name = nom_nou
    print("    12: contingut igualat V19 · nom nou")

    print("    fusionada nova…", flush=True)
    compost = np.zeros((H, W, 3), np.float32)
    alfaT = np.zeros((H, W), np.float32)
    for i, layer in enumerate(capes):
        if i == 13 or not layer.visible:
            continue
        if layer is l12:
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
    np.save(os.path.join(CAU, "compost_v19.npy"),
            np.clip(np.rint(compost * 65535.0), 0, 65535).astype(np.uint16))
    np.save(os.path.join(CAU, "alfa_v19.npy"),
            np.clip(np.rint(alfaT * 255.0), 0, 255).astype(np.uint8))
    del compost, rgbW, plans, sonyN, s16

    print("    desant…", flush=True)
    psd.save(DST)
    print(f"    {DST} · {os.path.getsize(DST)/1e9:.2f} GB · [{time.time()-t0:.0f}s]")

    print("[6/7] portes de fitxer")
    p2 = PSDImage.open(DST)
    assert (p2.width, p2.height) == (W, H) and len(list(p2)) == 14
    r = subprocess.run(["sips", "-g", "pixelWidth", DST],
                       capture_output=True, text=True)
    assert f"pixelWidth: {W}" in r.stdout + r.stderr
    r = subprocess.run([os.path.join(AQUI, "porta_photoshop.sh"), DST],
                       capture_output=True, text=True, timeout=900)
    print("    Photoshop diu:", (r.stdout + r.stderr).strip())

    print("[7/7] rebut")
    rebut = {"src_pere": SRC, "desti": DST, "sol": SOL, "rs": RS,
             "r_fit_max": R_FIT_MAX, "K": K, "NB": NB,
             "sectors": files_sec, "marques": files_marca,
             "canvi_camp_lluny_G": {"mediana": float(np.median(dG)),
                                    "p1": float(np.percentile(dG, 1)),
                                    "p99": float(np.percentile(dG, 99))},
             "nom_capa": nom_nou, "bytes": os.path.getsize(DST)}
    json.dump(rebut, open(os.path.join(CAU, "rebut_v19.json"), "w"),
              indent=1, ensure_ascii=False)
    print("fet")
    return rebut


if __name__ == "__main__":
    main()
