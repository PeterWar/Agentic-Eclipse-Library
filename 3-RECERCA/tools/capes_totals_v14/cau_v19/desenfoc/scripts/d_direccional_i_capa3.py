# -*- coding: utf-8 -*-
"""Anisotropia direccional del detall (zoom = vetes radials, gir = vetes
tangencials) per a capa1/capa2/capa0/capa3, i natura de capa3.

Metode: passa-alt gaussia (sigma=4 a q4), gradients projectats en direccio
radial/tangencial, i orientacio del tensor d'estructura respecte del radi.
"""
import json
import numpy as np
import cv2

BASE = "/Users/USUARI/Downloads/Eclipse 2026/research/tools/capes_totals_v14/cau_v19/desenfoc"
OUT = BASE + "/fable"
geo = json.load(open(BASE + "/geometria.json"))
W, H = geo["llenc"]; CX, CY = geo["sol_crop"]; RS = geo["rs"]

c1 = np.load(BASE + "/capa1_rgb16.npy", mmap_mode="r")
c2 = np.load(BASE + "/capa2_rgb16.npy", mmap_mode="r")
l1q = np.asarray(c1[::4, ::4], np.float32).mean(2)
l2q = np.asarray(c2[::4, ::4], np.float32).mean(2)
l0 = np.asarray(np.load(BASE + "/capa0_rgb16_q4.npy"), np.float32).mean(2)
l3 = np.asarray(np.load(BASE + "/capa3_rgb16_q4.npy"), np.float32).mean(2)
hq, wq = l0.shape
cxq, cyq, rsq = CX / 4, CY / 4, RS / 4
ysq, xsq = np.mgrid[0:hq, 0:wq].astype(np.float32)
rq = np.sqrt((xsq - cxq) ** 2 + (ysq - cyq) ** 2) / rsq
thq = np.arctan2(ysq - cyq, xsq - cxq)
urx, ury = np.cos(thq), np.sin(thq)

res = {}

def anisotropia(l, nom):
    hp = l - cv2.GaussianBlur(l, (0, 0), 4)
    gy, gx = np.gradient(hp)
    gr = gx * urx + gy * ury
    gt = -gx * ury + gy * urx
    # orientacio del tensor d'estructura (suavitzat 3): angle del gradient
    # respecte del radi. Vetes RADIALS (zoom) -> gradient tangencial -> angle ~90.
    # Vetes TANGENCIALS (gir) -> gradient radial -> angle ~0.
    out = []
    for r0, r1 in [(1.5, 2.5), (2.5, 3.5), (3.5, 5), (5, 7), (7, 9.5)]:
        sel = (rq >= r0) & (rq < r1)
        e_r = float((gr[sel] ** 2).mean()); e_t = float((gt[sel] ** 2).mean())
        # angle mitja ponderat per energia
        num = float((gt[sel] ** 2).sum()); den = float((gr[sel] ** 2 + gt[sel] ** 2).sum())
        out.append({"anell": [r0, r1],
                    "rms_gr_hp": round(np.sqrt(e_r), 2), "rms_gt_hp": round(np.sqrt(e_t), 2),
                    "quocient_gt2_sobre_total": round(num / den, 3) if den else None})
    res[nom] = out

for l, nom in [(l1q, "capa1_q4"), (l2q, "capa2_q4"), (l0, "capa0"), (l3, "capa3")]:
    anisotropia(l, nom)

# ---- natura de capa3: relacio amb capa1 ----
sel = (rq > 1.2) & (rq < 9)
x = l1q[sel].astype(np.float64); y = l3[sel].astype(np.float64)
A = np.polyfit(x, y, 1)
res["capa3_vs_capa1_lineal"] = {"pendent": round(float(A[0]), 4),
                                "ordenada": round(float(A[1]), 1),
                                "corr": round(float(np.corrcoef(x, y)[0, 1]), 4)}
# capa3 s'assembla mes a un passa-alt / realc de capa1?
hp1 = l1q - cv2.GaussianBlur(l1q, (0, 0), 8)
res["capa3_corr_amb_passaalt_capa1_s8"] = round(float(np.corrcoef(hp1[sel], l3[sel])[0, 1]), 4)
bp1 = cv2.GaussianBlur(l1q, (0, 0), 2) - cv2.GaussianBlur(l1q, (0, 0), 16)
res["capa3_corr_amb_bandpass_capa1_2_16"] = round(float(np.corrcoef(bp1[sel], l3[sel])[0, 1]), 4)
res["capa3_stats"] = {"min": float(l3.min()), "max": float(l3.max()),
                      "p1": float(np.percentile(l3, 1)), "p50": float(np.median(l3)),
                      "p99": float(np.percentile(l3, 99))}
res["capa0_stats"] = {"min": float(l0.min()), "max": float(l0.max()),
                      "p50": float(np.median(l0))}
# capa0 contra versions desenfocades de capa2q4 (es un zoom mes fort?)
for s in [2, 4, 8]:
    b = cv2.GaussianBlur(l2q, (0, 0), s)
    res.setdefault("capa0_corr_blur_capa2", {})["sigma_%d" % s] = round(
        float(np.corrcoef(b[sel], l0[sel])[0, 1]), 4)

# vista de capa2 sola (llenc sencer ::4) i de capa1 sola
cv2.imwrite(OUT + "/vista_capa2_x4.png",
            np.clip(np.asarray(c2[::4, ::4], np.float32) / 257.0, 0, 255).astype(np.uint8)[:, :, ::-1])
cv2.imwrite(OUT + "/vista_capa1_x4.png",
            np.clip(np.asarray(c1[::4, ::4], np.float32) / 257.0, 0, 255).astype(np.uint8)[:, :, ::-1])

with open(OUT + "/d_direccional_i_capa3.json", "w") as f:
    json.dump(res, f, indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1))
