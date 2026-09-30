"""Portes fines de la V19 (iteració ràpida sobre rho_v19_q4.npy).

Mètriques:
- bony radial (G) dins la banda de CADA marca [r_min−0,5, r_max+0,5];
- croma: VARIACIÓ TOTAL EN EXCÉS de R/G i B/G (Σ|Δ| − |net|) — un perfil
  monòton dona 0; una fosa que baixa i torna (halo) dona ~2× l'oscil·lació;
- contrast local: mediana(regió marcada) vs mediana(anell control mateix r,
  azimuts veïns) — caça taques i salts que cap perfil radial no veu;
- salts azimutals: perfil de G per azimut (2°) a tres anells — caça costures
  radials (la costura entre apuntaments de la Sony).
"""
from __future__ import annotations

import json
import os

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v19")
CAU18 = os.path.join(AQUI, "cau_v18")
SOL = (6469.2, 6757.6)
RS = 455.5


def tv_exces(prof):
    p = prof[np.isfinite(prof)]
    if len(p) < 6:
        return np.nan
    return float(np.sum(np.abs(np.diff(p))) - abs(p[-1] - p[0]))


def main():
    q = 4
    sonyq = np.asarray(np.load(os.path.join(CAU18, "sony_pere_rgb16.npy"),
                               mmap_mode="r")[::q, ::q], np.float32) / 65535.0
    sotaq = np.asarray(np.load(os.path.join(CAU18, "vixen_sota_rgb16.npy"),
                               mmap_mode="r")[::q, ::q], np.float32) / 65535.0
    alfaq = np.asarray(np.load(os.path.join(CAU18, "vixen_sota_alfa8.npy"),
                               mmap_mode="r")[::q, ::q], np.float32) / 255.0
    mq = np.asarray(np.load(os.path.join(CAU18, "sony_pere_mask16.npy"),
                            mmap_mode="r")[::q, ::q], np.float32) / 65535.0
    rho = np.load(os.path.join(CAU, "rho_v19_q4.npy"))
    comp_ab = np.load(os.path.join(CAU, "compost_pere_q4.npy"))
    m3, a3 = mq[..., None], alfaq[..., None]
    comp_ar = np.clip(sonyq * rho, 0, 1) * m3 + sotaq * a3 * (1 - m3)
    Hq, Wq = mq.shape
    yy = np.arange(Hq, dtype=np.float32)[:, None] * q
    xx = np.arange(Wq, dtype=np.float32)[None, :] * q
    rad = np.hypot(xx - SOL[0], yy - SOL[1]) / RS
    azd = np.degrees(np.arctan2(-(yy - SOL[1]), xx - SOL[0]))
    cobert = (mq + alfaq * (1 - mq)) > 0.98

    def perfil(img, sec, rr, mig=0.05, minpx=60):
        p = np.full(len(rr), np.nan, np.float32)
        for i, r0 in enumerate(rr):
            z = sec & (np.abs(rad - r0) < mig)
            if z.sum() >= minpx:
                p[i] = float(np.median(img[z]))
        return p

    def bony(img, sec, rr):
        p = perfil(img, sec, rr)
        bo = np.isfinite(p)
        if bo.sum() < 6:
            return np.nan
        iso = np.minimum.accumulate(np.where(bo, p, np.inf))
        return float(np.nanmax(np.where(bo, p - iso, 0)))

    def croma_tv(comp, sec, r_lo, r_hi):
        rr = np.arange(r_lo, r_hi, 0.25)
        out = []
        for jn, jd in ((0, 1), (2, 1)):
            qs = np.full(len(rr), np.nan, np.float32)
            for i, r0 in enumerate(rr):
                z = sec & (np.abs(rad - r0) < 0.125)
                if z.sum() >= 60:
                    qs[i] = (float(np.median(comp[..., jn][z]))
                             / max(float(np.median(comp[..., jd][z])), 1e-4))
            out.append(tv_exces(qs))
        return out  # [R/G, B/G]

    print("=== LES 8 MARQUES DE PERE (abans → ara) ===")
    regs = json.load(open(os.path.join(CAU, "regions_v19.json")))
    marques = {"verd": np.load(os.path.join(CAU, "marques_verd.npy"), mmap_mode="r"),
               "taronja": np.load(os.path.join(CAU, "marques_taronja.npy"),
                                  mmap_mode="r")}
    res = []
    for fam in ("verd", "taronja"):
        mk_full = marques[fam]
        for z in regs[fam]:
            dz = ((azd - z["az_med"] + 180) % 360) - 180
            # màscara de la regió concreta (a 1/4): px marcats prop del centre
            mreg = (np.asarray(mk_full[::q, ::q]) & (np.abs(dz) < 25)
                    & (rad > z["r_min"] - 0.3) & (rad < z["r_max"] + 0.3))
            # control: mateix rang de r, azimuts veïns (10°-35° fora de la marca)
            ampl = max(8.0, (z["r_max"] - z["r_min"]) * 12)
            ctrl = (cobert & (rad > z["r_min"] - 0.35) & (rad < z["r_max"] + 0.35)
                    & (np.abs(dz) > ampl + 8) & (np.abs(dz) < ampl + 33))
            sec = (np.abs(dz) < 12) & cobert
            rr = np.arange(max(2.5, z["r_min"] - 0.5), z["r_max"] + 0.55, 0.05)
            fila = {"fam": fam, "az": z["az_med"], "r": [z["r_min"], z["r_max"]]}
            fila["bony"] = [bony(comp_ab[..., 1], sec, rr),
                            bony(comp_ar[..., 1], sec, rr)]
            lo = max(4.0, z["r_min"] - 0.7)
            hi = min(8.3, z["r_max"] + 1.3)
            fila["tvR"], fila["tvB"] = zip(croma_tv(comp_ab, sec, lo, hi),
                                           croma_tv(comp_ar, sec, lo, hi))
            # contrast amb control APARELLAT PER RADI (calaixos de 0,1 R☉):
            # sense això, part del «contrast azimutal» era perfil radial
            cl = []
            for comp in (comp_ab, comp_ar):
                dG, dRG, pes = 0.0, 0.0, 0.0
                for rb in np.arange(z["r_min"] - 0.3, z["r_max"] + 0.31, 0.1):
                    mr = mreg & (np.abs(rad - rb) < 0.05)
                    mc = ctrl & (np.abs(rad - rb) < 0.05)
                    if mr.sum() < 30 or mc.sum() < 60:
                        continue
                    gR = float(np.median(comp[..., 1][mr]))
                    gC = float(np.median(comp[..., 1][mc]))
                    rgR = float(np.median(comp[..., 0][mr])) / max(gR, 1e-4)
                    rgC = float(np.median(comp[..., 0][mc])) / max(gC, 1e-4)
                    n = mr.sum()
                    dG += (gR / gC - 1) * n
                    dRG += (rgR - rgC) * n
                    pes += n
                cl.append((dG / max(pes, 1), dRG / max(pes, 1)))
            fila["contrast_G"] = [cl[0][0], cl[1][0]]
            fila["contrast_RG"] = [cl[0][1], cl[1][1]]
            res.append(fila)
            print(f"{fam.upper():7s} az {z['az_med']:+7.1f}° r {z['r_min']:.2f}-"
                  f"{z['r_max']:.2f}:")
            print(f"    bony     {fila['bony'][0]:.4f} → {fila['bony'][1]:.4f}")
            print(f"    tvR/G    {fila['tvR'][0]:.3f} → {fila['tvR'][1]:.3f} · "
                  f"tvB/G {fila['tvB'][0]:.3f} → {fila['tvB'][1]:.3f}")
            print(f"    contrast G {cl[0][0]:+.3f} → {cl[1][0]:+.3f} · "
                  f"R/G {cl[0][1]:+.4f} → {cl[1][1]:+.4f}")

    print("\n=== SALTS AZIMUTALS (costures radials), G per anell ===")
    for r_lo, r_hi in ((4.25, 4.75), (4.75, 5.25), (5.25, 5.75), (5.75, 6.5)):
        an = cobert & (rad >= r_lo) & (rad < r_hi)
        for nom, comp in (("abans", comp_ab), ("ara  ", comp_ar)):
            g = comp[..., 1]
            binz = ((azd + 180) / 2).astype(int) % 180
            prof = np.full(180, np.nan, np.float32)
            for bz in range(180):
                z = an & (binz == bz)
                if z.sum() > 40:
                    prof[bz] = float(np.median(g[z]))
            d = np.abs(np.diff(np.concatenate([prof, prof[:1]])))
            i = int(np.nanargmax(d))
            print(f"  r {r_lo}-{r_hi} {nom}: pas màxim {np.nanmax(d):.4f} "
                  f"a az {(-180 + 2 * i + 1):+d}°")

    print("\n=== 24 SECTORS: tv croma 4,5-8 R☉ (abans → ara) ===")
    pit = [0, 0]
    for s in range(24):
        azc = -180 + 15 * s + 7.5
        dz = ((azd - azc + 180) % 360) - 180
        sec = (np.abs(dz) < 7.5) & cobert
        tab = croma_tv(comp_ab, sec, 4.5, 8.0)
        tar = croma_tv(comp_ar, sec, 4.5, 8.0)
        pit[0] = np.nanmax([pit[0], tab[0], tab[1]])
        pit[1] = np.nanmax([pit[1], tar[0], tar[1]])
        print(f"  az {azc:+7.1f}°: R/G {tab[0]:.3f}→{tar[0]:.3f} · "
              f"B/G {tab[1]:.3f}→{tar[1]:.3f}")
    print(f"  pitjor tv croma: {pit[0]:.3f} → {pit[1]:.3f}")
    json.dump(res, open(os.path.join(CAU, "portes_marques_v19.json"), "w"),
              indent=1)


if __name__ == "__main__":
    main()
