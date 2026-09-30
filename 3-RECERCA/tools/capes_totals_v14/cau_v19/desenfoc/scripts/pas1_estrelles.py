# -*- coding: utf-8 -*-
"""Pas 1: catàleg d'estrelles a capa1 (G), fora de 2,5 R☉ i amb màscara >= 60000."""
import numpy as np, cv2, json, os

BASE = "/Users/USUARI/Downloads/Eclipse 2026/research/tools/capes_totals_v14/cau_v19/desenfoc"
OUT = os.path.join(BASE, "geometria_fable")
geo = json.load(open(os.path.join(BASE, "geometria.json")))
xc, yc = geo["sol_crop"]; rs = geo["rs"]

G1 = np.asarray(np.load(os.path.join(BASE, "capa1_rgb16.npy"), mmap_mode="r")[:, :, 1], dtype=np.float32)
M2 = np.asarray(np.load(os.path.join(BASE, "capa2_mask16.npy"), mmap_mode="r"), dtype=np.uint16)
H, W = G1.shape

# fons: obertura grisa (treu estrelles fins ~12 px de radi) + gaussiana
ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
bg = cv2.morphologyEx(G1, cv2.MORPH_OPEN, ker)
bg = cv2.GaussianBlur(bg, (0, 0), 12)
res = G1 - bg
del bg

yy = np.arange(H, dtype=np.float32)[:, None]
xx = np.arange(W, dtype=np.float32)[None, :]
r_px = np.sqrt((xx - xc) ** 2 + (yy - yc) ** 2)

valid = (r_px > 2.5 * rs) & (M2 >= 60000)
# soroll robust del residu a la zona vàlida (mostrejat)
v = res[::7, ::7][valid[::7, ::7]]
med = np.median(v)
sigma = 1.4826 * np.median(np.abs(v - med))
print("residu: mediana %.1f  sigma_MAD %.1f" % (med, sigma))

thr = med + 6.0 * sigma
dil = cv2.dilate(res, cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7)))
peaks = (res >= dil - 1e-3) & (res > thr) & valid
# marge de vora
marge = 40
peaks[:marge, :] = False; peaks[-marge:, :] = False
peaks[:, :marge] = False; peaks[:, -marge:] = False
ys, xs = np.nonzero(peaks)
print("pics crus:", len(ys))

# flux: suma del residu 9x9
fluxes = np.empty(len(ys), dtype=np.float64)
for i, (y, x) in enumerate(zip(ys, xs)):
    fluxes[i] = float(res[y - 4:y + 5, x - 4:x + 5].sum())

# dedupliquem pics a < 8 px (queda el més brillant)
ordre = np.argsort(-fluxes)
tria = []
ocupat = np.zeros((H // 8 + 2, W // 8 + 2), dtype=bool)
for i in ordre:
    cy, cx = ys[i] // 8, xs[i] // 8
    if ocupat[max(cy-1,0):cy+2, max(cx-1,0):cx+2].any():
        continue
    ocupat[cy, cx] = True
    tria.append(i)
tria = np.array(tria)
print("després de deduplicar:", len(tria))

cat = []
for i in tria:
    x, y = int(xs[i]), int(ys[i])
    cat.append({
        "x": x, "y": y,
        "r_px": float(r_px[y, x]), "r_rs": float(r_px[y, x] / rs),
        "flux": float(fluxes[i]), "pic": float(res[y, x]),
    })
cat.sort(key=lambda s: -s["flux"])
# ens quedem amb un màxim de 400 per al catàleg
cat = cat[:400]

# aïllament: distància al veí detectat més proper (dins del catàleg complet de pics deduplicats)
px_all = np.array([[xs[i], ys[i]] for i in tria], dtype=np.float32)
for s in cat:
    d = np.sqrt((px_all[:, 0] - s["x"]) ** 2 + (px_all[:, 1] - s["y"]) ** 2)
    d = d[d > 0.5]
    s["vei_px"] = float(d.min()) if len(d) else 1e9

json.dump({"n": len(cat), "sigma_fons": float(sigma), "llindar": float(thr),
           "estrelles": cat}, open(os.path.join(OUT, "estrelles_capa1.json"), "w"), indent=1)
print("desat", os.path.join(OUT, "estrelles_capa1.json"))
print("flux p10 %.0f p50 %.0f p90 %.0f  | r_rs p10 %.2f p50 %.2f p90 %.2f" % (
    *np.percentile([s["flux"] for s in cat], [10, 50, 90]),
    *np.percentile([s["r_rs"] for s in cat], [10, 50, 90])))
np.save(os.path.join(OUT, "residu_capa1_G.npy"), res)
