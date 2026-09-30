"""V21, pas 2: l'ajust fi per fotograma (el plate-solve relatiu).

Model per fotograma n (coordenades RAW):
    raw_base ≈ R(θ_n)·(raw_n − sol_n) + sol_base + t_n
Ajust amb les fonts BRILLANTS (top per flux), aparellament iteratiu amb
rebuig (3 passades, radi 25 → 6 → 3 px), i el veredicte: θ, t, rms i
el desplaçament que el registre solar deixava (el «lio» de Pere).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
sys.path.insert(0, AQUI)
import fes_v15 as F15

FRAMES = ["DSC06984.ARW", "DSC06996.ARW", "DSC06999.ARW",
          "DSC06987.ARW", "DSC06993.ARW"]
BASE = "DSC06993.ARW"
TOP = 200          # fonts més brillants per fotograma


def fit_similitud(P, Q):
    """Q ≈ R(θ)·P + t (P, Q ja en el marc sol-relatiu). Tancat, sense escala."""
    Pm, Qm = P.mean(0), Q.mean(0)
    P0, Q0 = P - Pm, Q - Qm
    num = float(np.sum(P0[:, 0] * Q0[:, 1] - P0[:, 1] * Q0[:, 0]))
    den = float(np.sum(P0[:, 0] * Q0[:, 0] + P0[:, 1] * Q0[:, 1]))
    th = np.arctan2(num, den)
    ca, sa = np.cos(th), np.sin(th)

    def aplica(X):
        return np.c_[ca * X[:, 0] - sa * X[:, 1], sa * X[:, 0] + ca * X[:, 1]]

    t = Qm - aplica(Pm[None, :])[0]
    res = Q - (aplica(P) + t)
    return th, t, res, aplica


def main():
    expl = json.load(open(os.path.join(CAU, "exploracio.json")))
    S13 = {}
    comu, f2, run, ctx, S13all, K, va = F15.carrega_sony()
    for n in FRAMES:
        S13[n] = S13all[n]
    dets = {n: np.load(os.path.join(CAU, f"fonts_{n.split('.')[0]}.npy"))
            for n in FRAMES}
    vb = S13[BASE]
    solb = np.array([vb["sol_x"], vb["sol_y"]])
    Qall = dets[BASE]
    Qall = Qall[np.argsort(-Qall[:, 2])][:TOP]
    Q = Qall[:, :2] - solb

    fits = {}
    for n in FRAMES:
        if n == BASE:
            fits[n] = {"theta_deg": 0.0, "t_px": [0.0, 0.0], "n": int(len(Q)),
                       "rms_px": 0.0, "desplacament_solar_px": 0.0}
            continue
        v = S13[n]
        soln = np.array([v["sol_x"], v["sol_y"]])
        Pall = dets[n]
        Pall = Pall[np.argsort(-Pall[:, 2])][:TOP]
        P = Pall[:, :2] - soln
        th, t = 0.0, np.zeros(2)
        parelles = None
        for radi in (25.0, 6.0, 3.0):
            ca, sa = np.cos(th), np.sin(th)
            Pt = np.c_[ca * P[:, 0] - sa * P[:, 1],
                       sa * P[:, 0] + ca * P[:, 1]] + t
            tq = cKDTree(Q)
            d, j = tq.query(Pt, k=1)
            bo = d < radi
            if bo.sum() < 6:
                break
            th, t, res, _ = fit_similitud(P[bo], Q[j[bo]])
            parelles = (P[bo], Q[j[bo]], res)
        if parelles is None:
            print(f"{n}: SENSE ajust fiable")
            continue
        Pb, Qb, res = parelles
        rms = float(np.sqrt((res ** 2).sum(1).mean()))
        despl = float(np.median(np.hypot(*(Qb - Pb).T)))
        fits[n] = {"theta_deg": float(np.degrees(th)),
                   "t_px": [float(t[0]), float(t[1])],
                   "n": int(len(Pb)), "rms_px": rms,
                   "desplacament_solar_px": despl}
        print(f"{n}: {len(Pb)} parelles · θ = {np.degrees(th)*60:+.2f}′ · "
              f"t = ({t[0]:+.2f}, {t[1]:+.2f}) px · rms {rms:.2f} px · "
              f"desplaçament que deixava el registre solar: {despl:.1f} px "
              f"(mediana)")

    # el desplaçament PREDIT per la deriva sideral−solar (0,041″/s, 3,202″/px)
    tb = S13[BASE].get("t", 0.0)
    for n in FRAMES:
        if n == BASE or n not in fits:
            continue
        dt = S13[n].get("t", 0.0) - tb
        pred = abs(dt) * 0.041 / 3.202
        fits[n]["dt_s"] = float(dt)
        fits[n]["deriva_sideral_pred_px"] = float(pred)
        print(f"{n}: Δt = {dt:+.0f} s → deriva sideral−solar predita "
              f"{pred:.2f} px (la resta és muntura/rotació)")
    json.dump(fits, open(os.path.join(CAU, "fits_estrelles.json"), "w"),
              indent=1, ensure_ascii=False)
    print(f"desat a {CAU}/fits_estrelles.json")


if __name__ == "__main__":
    main()
