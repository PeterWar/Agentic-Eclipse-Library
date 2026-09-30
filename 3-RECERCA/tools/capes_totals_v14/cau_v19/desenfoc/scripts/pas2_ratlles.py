# -*- coding: utf-8 -*-
"""Pas 2-3: mesura de les ratlles a capa2 (orientació, llargada, centre de convergència,
Δr/r i forma del nucli), a partir del catàleg del pas 1."""
import numpy as np, cv2, json, os

BASE = "/Users/USUARI/Downloads/Eclipse 2026/research/tools/capes_totals_v14/cau_v19/desenfoc"
OUT = os.path.join(BASE, "geometria_fable")
SCR = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/dfcda07d-fe88-40c0-8251-cd1d860283ac/scratchpad/desenfoc"
geo = json.load(open(os.path.join(BASE, "geometria.json")))
xc, yc = geo["sol_crop"]; rs = geo["rs"]

# residu de capa2 (mateixa recepta que el pas 1)
res2_path = os.path.join(SCR, "residu_capa2_G.npy")
if not os.path.exists(res2_path):
    G2 = np.asarray(np.load(os.path.join(BASE, "capa2_rgb16.npy"), mmap_mode="r")[:, :, 1], dtype=np.float32)
    ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    bg = cv2.morphologyEx(G2, cv2.MORPH_OPEN, ker)
    bg = cv2.GaussianBlur(bg, (0, 0), 12)
    np.save(res2_path, G2 - bg)
    del G2, bg
res2 = np.load(res2_path, mmap_mode="r")
H, W = res2.shape

cat = json.load(open(os.path.join(OUT, "estrelles_capa1.json")))["estrelles"]
# candidats: brillants i aïllats (com a mínim 80 px del veí) i lluny de la vora
cands = [s for s in cat if s["vei_px"] > 80]
cands.sort(key=lambda s: -s["flux"])
print("candidats aïllats:", len(cands))

def mesura_ratlla(s):
    x0, y0, r = s["x"], s["y"], s["r_px"]
    wh = int(max(80, min(600, 0.16 * r)))
    xlo, xhi = x0 - wh, x0 + wh + 1
    ylo, yhi = y0 - wh, y0 + wh + 1
    if xlo < 0 or ylo < 0 or xhi > W or yhi > H:
        return None
    win = np.asarray(res2[ylo:yhi, xlo:xhi], dtype=np.float32)
    med = np.median(win)
    sig = 1.4826 * np.median(np.abs(win - med))
    thr = med + 3.5 * sig
    bw = (win > thr).astype(np.uint8)
    bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, lab, stats, cent = cv2.connectedComponentsWithStats(bw, 8)
    if n < 2:
        return None
    # component més proper a la posició de l'estrella (dins de 25 px)
    best, bestd = -1, 1e9
    for k in range(1, n):
        if stats[k, cv2.CC_STAT_AREA] < 25:
            continue
        # distància del punt (wh, wh) al bounding box del component
        bx, by, bw_, bh_ = stats[k, 0], stats[k, 1], stats[k, 2], stats[k, 3]
        dx = max(bx - wh, 0, wh - (bx + bw_ - 1))
        dy = max(by - wh, 0, wh - (by + bh_ - 1))
        d = np.hypot(dx, dy)
        if d < bestd:
            bestd, best = d, k
    if best < 0 or bestd > 25:
        return None
    k = best
    # si el component toca la vora de la finestra, la ratlla no hi cap: fora
    bx, by, bw_, bh_ = stats[k, 0], stats[k, 1], stats[k, 2], stats[k, 3]
    if bx <= 1 or by <= 1 or bx + bw_ >= 2 * wh - 1 or by + bh_ >= 2 * wh - 1:
        return None
    mm = lab == k
    ys, xs = np.nonzero(mm)
    wgt = win[ys, xs] - med
    wgt = np.clip(wgt, 0, None)
    Wt = wgt.sum()
    mx = (xs * wgt).sum() / Wt
    my = (ys * wgt).sum() / Wt
    ux, uy = xs - mx, ys - my
    c20 = (ux * ux * wgt).sum() / Wt
    c02 = (uy * uy * wgt).sum() / Wt
    c11 = (ux * uy * wgt).sum() / Wt
    theta = 0.5 * np.arctan2(2 * c11, c20 - c02)   # eix principal
    ex, ey = np.cos(theta), np.sin(theta)
    t = ux * ex + uy * ey                            # projecció eix major
    q = -ux * ey + uy * ex                           # eix menor
    t1, t99 = np.percentile(t, [1, 99])
    L = float(t99 - t1)
    ampl = float(np.percentile(np.abs(q), 95) * 2)
    # valors propis per a l'elongació
    tr, det = c20 + c02, c20 * c02 - c11 * c11
    disc = max(tr * tr / 4 - det, 0)
    l1 = tr / 2 + np.sqrt(disc); l2 = tr / 2 - np.sqrt(disc)
    elong = float(np.sqrt(l1 / max(l2, 1e-6)))
    # perfil al llarg de l'eix major (bins de 2 px) per la forma del nucli
    nb = max(int(L // 2), 8)
    bins = np.linspace(t1, t99, nb + 1)
    idx = np.clip(np.digitize(t, bins) - 1, 0, nb - 1)
    prof = np.zeros(nb)
    for i in range(len(t)):
        prof[idx[i]] += wgt[i]
    pmax = prof.max()
    centre60 = prof[int(nb * 0.2):int(nb * 0.8)]
    flat = float(np.median(centre60) / pmax) if pmax > 0 else 0.0
    # posició de l'estrella original al llarg de la ratlla (0 = extrem interior)
    sx, sy = x0 - (xlo + mx), y0 - (ylo + my)
    t_star = sx * ex + sy * ey
    # signe radial: eix cap enfora
    rx, ry = (x0 - xc) / r, (y0 - yc) / r
    if ex * rx + ey * ry < 0:
        ex, ey, theta = -ex, -ey, theta + np.pi
        t_star = -t_star
    pos_norm = float((t_star - t1) / (t99 - t1))     # ~1 => estrella a l'extrem EXTERIOR
    ang_raig = np.arctan2(ry, rx)
    dang = (theta - ang_raig + np.pi / 2) % np.pi - np.pi / 2
    return {
        "x": x0, "y": y0, "r_px": r, "r_rs": s["r_rs"], "flux": s["flux"],
        "cx": float(xlo + mx), "cy": float(ylo + my),
        "theta_deg": float(np.degrees(theta) % 360), "ang_raig_deg": float(np.degrees(ang_raig) % 360),
        "dang_deg": float(np.degrees(dang)),
        "L_px": L, "ampl_px": ampl, "elong": elong, "area": int(mm.sum()),
        "flat": flat, "pos_estrella": pos_norm, "n_bins": nb,
        "perfil": [float(p) for p in prof],
    }

ratlles = []
for s in cands:
    m = mesura_ratlla(s)
    if m is None:
        continue
    if m["elong"] < 2.0 or m["L_px"] < 12:
        continue
    ratlles.append(m)
    if len(ratlles) >= 40:
        break
print("ratlles bones:", len(ratlles))

# ajust del centre de convergència: minimitza sum (n_i · (C - p_i))^2
A = np.zeros((2, 2)); b = np.zeros(2)
for m in ratlles:
    th = np.radians(m["theta_deg"])
    nx, ny = -np.sin(th), np.cos(th)
    p = np.array([m["cx"], m["cy"]])
    nn = np.outer([nx, ny], [nx, ny])
    A += nn; b += nn @ p
C = np.linalg.solve(A, b)

def rms_dist(cx_, cy_):
    d = []
    for m in ratlles:
        th = np.radians(m["theta_deg"])
        nx, ny = -np.sin(th), np.cos(th)
        d.append((nx * (cx_ - m["cx"]) + ny * (cy_ - m["cy"])) ** 2)
    return float(np.sqrt(np.mean(d)))

geoC = (8156 / 2.0, 5422 / 2.0)
resultat = {
    "n_ratlles": len(ratlles),
    "centre_ajustat": [float(C[0]), float(C[1])],
    "rms_perp_px": {"ajustat": rms_dist(*C), "sol": rms_dist(xc, yc), "geometric": rms_dist(*geoC)},
    "dist_centre_ajustat_a_sol_px": float(np.hypot(C[0] - xc, C[1] - yc)),
    "dist_centre_ajustat_a_geometric_px": float(np.hypot(C[0] - geoC[0], C[1] - geoC[1])),
    "sol": [xc, yc], "centre_geometric": list(geoC),
}
# Δr/r: ajust L = a·r + b
rr = np.array([m["r_px"] for m in ratlles])
LL = np.array([m["L_px"] for m in ratlles])
a1, b1 = np.polyfit(rr, LL, 1)
resultat["fit_L_vs_r"] = {"pendent_a": float(a1), "intercept_b_px": float(b1),
                          "mediana_L_sobre_r": float(np.median(LL / rr)),
                          "corr_L_r": float(np.corrcoef(rr, LL)[0, 1])}
resultat["dang_deg"] = {"mediana": float(np.median([m["dang_deg"] for m in ratlles])),
                        "rms": float(np.sqrt(np.mean(np.array([m["dang_deg"] for m in ratlles]) ** 2)))}
resultat["pos_estrella"] = {"mediana": float(np.median([m["pos_estrella"] for m in ratlles])),
                            "p10": float(np.percentile([m["pos_estrella"] for m in ratlles], 10)),
                            "p90": float(np.percentile([m["pos_estrella"] for m in ratlles], 90))}
resultat["flat"] = {"mediana": float(np.median([m["flat"] for m in ratlles])),
                    "p10": float(np.percentile([m["flat"] for m in ratlles], 10)),
                    "p90": float(np.percentile([m["flat"] for m in ratlles], 90))}
resultat["ratlles"] = ratlles
json.dump(resultat, open(os.path.join(OUT, "ratlles_capa2.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in resultat.items() if k != "ratlles"}, indent=1))
