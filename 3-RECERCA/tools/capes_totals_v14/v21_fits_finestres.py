"""V21, pas 2b: ajust per CORRELACIÓ DE FASE PER FINESTRES (robust al soroll).

Per cada fotograma vs la seva referència: passa-alt de la G a mitja resolució,
finestres de 512 px repartides pel camp d'estrelles (fora de r<1,7 R☉ i del
disc lunar), correlació de fase per finestra (sub-px per paràbola), i ajust de
similitud (θ, t) sobre els desplaçaments de les finestres. El model final,
en RAW sencer:  raw_ref ≈ R(θ)·(raw_n − sol_n) + sol_ref + t.
Cadena fins a la BASE (06993): els 2 s van via el 8 s del seu apuntament.
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
import fes_v15 as F15

BASE = "DSC06993.ARW"
PARELLES = [("DSC06987.ARW", "DSC06993.ARW"),   # validació: θ esperada ≈ +8,3′
            ("DSC06984.ARW", "DSC06987.ARW"),
            ("DSC06996.ARW", "DSC06993.ARW"),
            ("DSC06999.ARW", "DSC06993.ARW")]
WIN = 512          # finestra (mitja resolució)


def passa_alt(ctx, comu, n, exp):
    plans = ctx.plans(n, exp)
    acc, wac = None, None
    for i, (pl, w) in plans.items():
        if comu.CANALS[comu.IDX_CANAL[i]] != "G":
            continue
        if acc is None:
            acc, wac = pl * w, w.copy()
        else:
            acc += pl * w
            wac += w
    img = acc / np.maximum(wac, 1e-9)
    hp = img - cv2.GaussianBlur(cv2.medianBlur(img.astype(np.float32), 5),
                                (0, 0), 10.0)
    i0 = [i for i in ctx.orig if comu.CANALS[comu.IDX_CANAL[i]] == "G"][0]
    return hp, (wac > 0).astype(np.float32), ctx.orig[i0]


def correlacio(a, b):
    """Desplaçament sub-px de b respecte d'a (correlació de fase + paràbola)."""
    win = np.hanning(a.shape[0])[:, None] * np.hanning(a.shape[1])[None, :]
    A = np.fft.rfft2(a * win)
    B = np.fft.rfft2(b * win)
    R = A * np.conj(B)
    R /= np.maximum(np.abs(R), 1e-12)
    r = np.fft.irfft2(R, s=a.shape)
    iy, ix = np.unravel_index(np.argmax(r), r.shape)
    pic = r[iy, ix]

    def par(vm, v0, vp):
        d = vm - 2 * v0 + vp
        return 0.0 if abs(d) < 1e-12 else 0.5 * (vm - vp) / d
    dy = iy + par(r[(iy - 1) % r.shape[0], ix], pic, r[(iy + 1) % r.shape[0], ix])
    dx = ix + par(r[iy, (ix - 1) % r.shape[1]], pic, r[iy, (ix + 1) % r.shape[1]])
    if dy > r.shape[0] / 2:
        dy -= r.shape[0]
    if dx > r.shape[1] / 2:
        dx -= r.shape[1]
    return dx, dy, float(pic)


def fit_sim(P, Q):
    Pm, Qm = P.mean(0), Q.mean(0)
    P0, Q0 = P - Pm, Q - Qm
    th = np.arctan2(float(np.sum(P0[:, 0] * Q0[:, 1] - P0[:, 1] * Q0[:, 0])),
                    float(np.sum(P0[:, 0] * Q0[:, 0] + P0[:, 1] * Q0[:, 1])))
    ca, sa = np.cos(th), np.sin(th)

    def ap(X):
        return np.c_[ca * X[:, 0] - sa * X[:, 1], sa * X[:, 0] + ca * X[:, 1]]
    t = Qm - ap(Pm[None, :])[0]
    return th, t, Q - (ap(P) + t)


def main():
    comu, f2, run, ctx, S13, K, va = F15.carrega_sony()
    caches = {}

    def hp_de(n):
        if n not in caches:
            caches[n] = passa_alt(ctx, comu, n, S13[n]["exp"])
        return caches[n]

    fits = {}
    for n, ref in PARELLES:
        hpn, wn, orign = hp_de(n)
        hpr, wr, origr = hp_de(ref)
        v, vr = S13[n], S13[ref]
        H2, W2 = hpn.shape
        soln_h = ((v["sol_x"] - orign[1]) * 0.5, (v["sol_y"] - orign[0]) * 0.5)
        llun_h = ((v["sol_x"] + v["lluna_dx"] - orign[1]) * 0.5,
                  (v["sol_y"] + v["lluna_dy"] - orign[0]) * 0.5)
        yy = np.arange(H2, dtype=np.float32)[:, None]
        xx = np.arange(W2, dtype=np.float32)[None, :]
        lliure_n = ((np.hypot(xx - soln_h[0], yy - soln_h[1]) > 760)
                    & (np.hypot(xx - llun_h[0], yy - llun_h[1]) > ctx.RL * 0.5 + 40)
                    & (wn > 0.5))
        solr_h = ((vr["sol_x"] - origr[1]) * 0.5, (vr["sol_y"] - origr[0]) * 0.5)
        llur_h = ((vr["sol_x"] + vr["lluna_dx"] - origr[1]) * 0.5,
                  (vr["sol_y"] + vr["lluna_dy"] - origr[0]) * 0.5)
        lliure_r = ((np.hypot(xx - solr_h[0], yy - solr_h[1]) > 760)
                    & (np.hypot(xx - llur_h[0], yy - llur_h[1]) > ctx.RL * 0.5 + 40)
                    & (wr > 0.5))
        P, Qd, pics = [], [], []
        for y0 in range(0, H2 - WIN, WIN // 2):
            for x0 in range(0, W2 - WIN, WIN // 2):
                m = lliure_n[y0:y0 + WIN, x0:x0 + WIN]
                if m.mean() < 0.9:
                    continue
                # predicció solar: la mateixa posició sol-relativa a la ref
                cxn = x0 + WIN / 2.0
                cyn = y0 + WIN / 2.0
                rxr = (cxn - soln_h[0]) + (vr["sol_x"] - origr[1]) * 0.5
                ryr = (cyn - soln_h[1]) + (vr["sol_y"] - origr[0]) * 0.5
                x0r = int(round(rxr - WIN / 2.0))
                y0r = int(round(ryr - WIN / 2.0))
                if not (0 <= x0r and x0r + WIN <= W2 and 0 <= y0r
                        and y0r + WIN <= H2):
                    continue
                if lliure_r[y0r:y0r + WIN, x0r:x0r + WIN].mean() < 0.9:
                    continue
                a = hpr[y0r:y0r + WIN, x0r:x0r + WIN]
                b = hpn[y0:y0 + WIN, x0:x0 + WIN]
                dx, dy, pic = correlacio(a, b)
                # posició a la ref del CENTRE de la finestra de n:
                # (origen ref) + WIN/2 + desplaçament sub-px
                totx = (x0r + WIN / 2.0 + dx) - rxr
                toty = (y0r + WIN / 2.0 + dy) - ryr
                P.append([(cxn - soln_h[0]) * 2.0, (cyn - soln_h[1]) * 2.0])
                Qd.append([((cxn - soln_h[0]) + totx) * 2.0,
                           ((cyn - soln_h[1]) + toty) * 2.0])
                pics.append(pic)
        P, Qd, pics = np.array(P), np.array(Qd), np.array(pics)
        bo = pics > max(0.03, np.percentile(pics, 40))
        if bo.sum() < 4:
            print(f"{n} vs {ref}: només {bo.sum()} finestres bones")
            continue
        th, t, res = fit_sim(P[bo], Qd[bo])
        rms = float(np.sqrt((res ** 2).sum(1).mean()))
        # segona passada: fora les finestres amb residu > 3·rms
        bo2 = np.zeros(len(P), bool)
        bo2[np.where(bo)[0]] = (np.hypot(*res.T) < max(3 * rms, 2.0))
        if bo2.sum() >= 4:
            th, t, res = fit_sim(P[bo2], Qd[bo2])
            rms = float(np.sqrt((res ** 2).sum(1).mean()))
            bo = bo2
        despl = float(np.median(np.hypot(*(Qd[bo] - P[bo]).T)))
        fits[n] = {"ref": ref, "finestres": int(bo.sum()),
                   "theta_deg": float(np.degrees(th)),
                   "t_px": [float(t[0]), float(t[1])], "rms_px": rms,
                   "desplacament_solar_px": despl,
                   "pic_mediana": float(np.median(pics[bo]))}
        print(f"{n} vs {ref}: {bo.sum()} finestres · θ={np.degrees(th)*60:+.2f}′"
              f" · t=({t[0]:+.2f},{t[1]:+.2f}) px · rms {rms:.2f} px · "
              f"despl solar {despl:.1f} px · pic {np.median(pics[bo]):.3f}",
              flush=True)

    # encadena fins a la base (t en el marc sol-relatiu de la ref)
    cadena = {BASE: {"theta_deg": 0.0, "t_px": [0.0, 0.0], "via": "base"}}
    for n in fits:
        f = fits[n]
        if f["ref"] == BASE:
            cadena[n] = {"theta_deg": f["theta_deg"], "t_px": f["t_px"],
                         "via": "directa", "rms_px": f["rms_px"]}
    for n in fits:
        f = fits[n]
        if f["ref"] != BASE and f["ref"] in fits:
            g = fits[f["ref"]]
            th1 = np.radians(f["theta_deg"])
            th2 = np.radians(g["theta_deg"])
            ca, sa = np.cos(th2), np.sin(th2)
            t1 = np.array(f["t_px"])
            t2 = np.array(g["t_px"])
            tc = np.array([ca * t1[0] - sa * t1[1],
                           sa * t1[0] + ca * t1[1]]) + t2
            cadena[n] = {"theta_deg": float(np.degrees(th1 + th2)),
                         "t_px": [float(tc[0]), float(tc[1])],
                         "via": f["ref"],
                         "rms_px": float(np.hypot(f["rms_px"], g["rms_px"]))}
    json.dump({"fits": fits, "cadena_a_base": cadena, "base": BASE},
              open(os.path.join(CAU, "fits_finestres.json"), "w"), indent=1,
              ensure_ascii=False)
    print("cadena a la base:")
    for n, c in cadena.items():
        print(f"  {n}: θ={c['theta_deg']*60:+.2f}′ t=({c['t_px'][0]:+.2f},"
              f"{c['t_px'][1]:+.2f}) via {c['via']}")


if __name__ == "__main__":
    main()
