"""V21, pas 1: exploració — quin 8 s té la Lluna centrada, instants, i el
desplaçament REAL de les estrelles entre fotogrames (la mesura del «lio»).

Per fotograma: imatge G a mitja resolució del RAW, detecció de fonts puntuals
fora de la corona i del disc lunar, i ajust de TRANSLACIÓ + ROTACIÓ (similitud
sense escala) de cada fotograma contra la base, sobre les estrelles aparellades
via la predicció solar (el registre solar ja posa les estrelles a pocs px).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "encaix_sony"))
import fes_v15 as F15

FRAMES = ["DSC06984.ARW", "DSC06996.ARW", "DSC06999.ARW",
          "DSC06987.ARW", "DSC06993.ARW"]


def imatge_G(ctx, comu, n, exp):
    """G a mitja resolució del RAW (mitjana dels dos plans G), i el seu pes."""
    plans = ctx.plans(n, exp)
    acc, wac = None, None
    for i, (pl, w) in plans.items():
        if comu.CANALS[comu.IDX_CANAL[i]] != "G":
            continue
        if acc is None:
            acc, wac = pl * w, w.copy()
        else:
            acc = acc + pl * w
            wac = wac + w
    return acc / np.maximum(wac, 1e-9), wac


def detecta(img, w, sol_half, lluna_half, RL_half):
    """Fonts puntuals: màxims locals sobre fons local, fora de r<1,6 R☉ del Sol
    i del disc lunar; llindar 5σ local (MAD en anells amples)."""
    H, W = img.shape
    fons = cv2.medianBlur(img.astype(np.float32), 5)
    fons = cv2.GaussianBlur(fons, (0, 0), 12.0)
    D = img - fons
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    rs = np.hypot(xx - sol_half[0], yy - sol_half[1])
    rl = np.hypot(xx - lluna_half[0], yy - lluna_half[1])
    lliure = (rs > 720.0) & (rl > RL_half + 30) & (w > 0.5)  # 720 half-px ≈ 1,63 R☉
    v = D[lliure][::7]
    md = np.median(v)
    sig = 1.4826 * np.median(np.abs(v - md))
    cand = lliure & (D > md + 4.0 * sig)
    ncc, lab, st, cen = cv2.connectedComponentsWithStats(cand.astype(np.uint8), 8)
    out = []
    for k in range(1, ncc):
        x0, y0, wc, hc, area = st[k]
        if area < 2 or area > 60 or wc > 12 or hc > 12:
            continue
        sub = np.where(lab[y0:y0+hc, x0:x0+wc] == k, D[y0:y0+hc, x0:x0+wc], 0)
        tot = sub.sum()
        if tot <= 0:
            continue
        iy, ix = np.mgrid[y0:y0+hc, x0:x0+wc]
        cx = float((sub * ix).sum() / tot)
        cy = float((sub * iy).sum() / tot)
        pic = float(sub.max())
        if pic < md + 5.0 * sig:
            continue
        out.append((cx, cy, float(tot), pic))
    return np.array(out, np.float64) if out else np.zeros((0, 4)), float(sig)


def ajusta_similitud(P, Q):
    """Q ≈ R(θ)·P + t (sense escala). Retorna θ (rad), t, residus."""
    Pm, Qm = P.mean(0), Q.mean(0)
    P0, Q0 = P - Pm, Q - Qm
    num = np.sum(P0[:, 0] * Q0[:, 1] - P0[:, 1] * Q0[:, 0])
    den = np.sum(P0[:, 0] * Q0[:, 0] + P0[:, 1] * Q0[:, 1])
    th = np.arctan2(num, den)
    ca, sa = np.cos(th), np.sin(th)
    Pr = np.c_[ca * P0[:, 0] - sa * P0[:, 1], sa * P0[:, 0] + ca * P0[:, 1]]
    t = Qm - Pm + (Pm - (Pm))  # t tal que Q = R(P−Pm)+Pm + t
    res = Q0 - Pr
    return th, Qm - Pm, res


def main():
    os.makedirs(CAU, exist_ok=True)
    comu, f2, run, ctx, S13, K, va = F15.carrega_sony()
    print(f"RL (radi lunar al RAW) = {ctx.RL:.2f} px")
    g = ctx.g
    cx_sensor, cy_sensor = g.ample / 2.0, g.alt / 2.0
    print(f"sensor {g.ample}x{g.alt} · centre ({cx_sensor:.0f}, {cy_sensor:.0f})")

    # instants de captura (de l'EXIF del run, si hi és al registre)
    try:
        reg = run.llegeix_rebut("F1.3_registre.json")["fotogrames"]
    except Exception:
        reg = S13
    info = {}
    for n in FRAMES:
        v = S13[n]
        mlx, mly = v["sol_x"] + v["lluna_dx"], v["sol_y"] + v["lluna_dy"]
        dc = float(np.hypot(mlx - cx_sensor, mly - cy_sensor))
        extra = {k: v[k] for k in v if k in ("t_c2", "instant", "hora", "t")}
        info[n] = {"exp": v["exp"], "sol": [v["sol_x"], v["sol_y"]],
                   "lluna": [mlx, mly], "lluna_a_centre_px": round(dc, 1),
                   "extra": extra}
        print(f"{n}: exp {v['exp']:5.2f} s · sol ({v['sol_x']:7.1f},{v['sol_y']:7.1f})"
              f" · lluna ({mlx:7.1f},{mly:7.1f}) · |lluna−centre| {dc:7.1f} px"
              f" · extra {extra}")
    base = min(F15.FRAMES_8S, key=lambda n: info[n]["lluna_a_centre_px"])
    print(f"\nBASE (8 s amb la Lluna més centrada): {base}")

    # detecció per fotograma (coordenades en MITJA resolució del RAW)
    dets = {}
    for n in FRAMES:
        v = S13[n]
        img, w = imatge_G(ctx, comu, n, v["exp"])
        sol_h = (v["sol_x"] * 0.5, v["sol_y"] * 0.5)
        llu_h = (info[n]["lluna"][0] * 0.5, info[n]["lluna"][1] * 0.5)
        # ⚠️ els plans van amb 'orig': la coordenada half = (raw − orig)/2; per
        # a G n'hi ha dos amb origs diferents — aquí fem servir el pla combinat
        # sobre la graella del primer pla G (origs difereixen ≤1 px raw)
        i0 = [i for i in ctx.orig if comu.CANALS[comu.IDX_CANAL[i]] == "G"][0]
        oy, ox = ctx.orig[i0]
        sol_h = ((v["sol_x"] - ox) * 0.5, (v["sol_y"] - oy) * 0.5)
        llu_h = ((info[n]["lluna"][0] - ox) * 0.5, (info[n]["lluna"][1] - oy) * 0.5)
        est, sig = detecta(img, w, sol_h, llu_h, ctx.RL * 0.5)
        # a coordenades RAW senceres
        if len(est):
            est[:, 0] = est[:, 0] * 2.0 + ox
            est[:, 1] = est[:, 1] * 2.0 + oy
        dets[n] = est
        print(f"{n}: {len(est)} fonts (σ_local {sig:.4g})")
        del img, w

    # aparellament contra la base via la predicció SOLAR i ajust de similitud
    vb = S13[base]
    res_fits = {}
    for n in FRAMES:
        if n == base or len(dets[n]) < 3 or len(dets[base]) < 3:
            continue
        v = S13[n]
        # predicció: mateixa posició relativa al Sol
        P = dets[n][:, :2] - np.array([v["sol_x"], v["sol_y"]])
        Q = dets[base][:, :2] - np.array([vb["sol_x"], vb["sol_y"]])
        from scipy.spatial import cKDTree
        t = cKDTree(Q)
        d, j = t.query(P, k=1)
        bo = d < 25.0
        if bo.sum() < 3:
            print(f"{n}: només {bo.sum()} parelles a <25 px — no ajusto")
            continue
        Pm_, Qm_ = P[bo], Q[j[bo]]
        th, tvec, res = ajusta_similitud(Pm_, Qm_)
        rms = float(np.sqrt((res ** 2).sum(1).mean()))
        # segona passada amb el fit aplicat (aparellament més fi)
        ca, sa = np.cos(th), np.sin(th)
        P2 = np.c_[ca * (P[:, 0] - P[:, 0].mean()) - sa * (P[:, 1] - P[:, 1].mean()),
                   sa * (P[:, 0] - P[:, 0].mean()) + ca * (P[:, 1] - P[:, 1].mean())]
        res_fits[n] = {"n_parelles": int(bo.sum()), "theta_deg": float(np.degrees(th)),
                       "t_px": [float(tvec[0]), float(tvec[1])], "rms_px": rms,
                       "desplacament_tipic_px": float(np.median(d[bo]))}
        print(f"{n} vs {base}: {bo.sum()} parelles · desplaçament mediana "
              f"{np.median(d[bo]):.2f} px · fit θ={np.degrees(th)*60:.2f}′ "
              f"t=({tvec[0]:+.2f},{tvec[1]:+.2f}) px · rms {rms:.2f} px")

    json.dump({"base": base, "RL": float(ctx.RL), "info": info,
               "fits_vs_base": res_fits,
               "n_fonts": {n: int(len(dets[n])) for n in FRAMES}},
              open(os.path.join(CAU, "exploracio.json"), "w"), indent=1,
              ensure_ascii=False)
    for n in FRAMES:
        np.save(os.path.join(CAU, f"fonts_{n.split('.')[0]}.npy"), dets[n])
    print(f"\ndesat a {CAU}")


if __name__ == "__main__":
    main()
