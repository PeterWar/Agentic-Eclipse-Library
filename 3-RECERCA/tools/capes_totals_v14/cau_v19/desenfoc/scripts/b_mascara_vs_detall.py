# -*- coding: utf-8 -*-
"""1b: la mascara segueix el DETALL de capa1 o nomes el RADI?

(1-m) contra energia de detall local de capa1 (passa-alt gaussia sigma=8,
energia = mitjana local del quadrat, finestra 64 px). Ajust per separat
(1-m)~f(r) i (1-m)~g(E) i comparacio de R2. Nomes lectura; json + png a fable/.
"""
import json
import numpy as np
import cv2

BASE = "/Users/USUARI/Downloads/Eclipse 2026/research/tools/capes_totals_v14/cau_v19/desenfoc"
OUT = BASE + "/fable"
geo = json.load(open(BASE + "/geometria.json"))
W, H = geo["llenc"]; CX, CY = geo["sol_crop"]; RS = geo["rs"]

c1 = np.load(BASE + "/capa1_rgb16.npy", mmap_mode="r")
mask = np.load(BASE + "/capa2_mask16.npy", mmap_mode="r")

# lluminancia float32 0..1
lum = (np.asarray(c1[:, :, 0], np.float32) + np.asarray(c1[:, :, 1], np.float32)
       + np.asarray(c1[:, :, 2], np.float32)) / (3.0 * 65535.0)
blur = cv2.GaussianBlur(lum, (0, 0), 8, borderType=cv2.BORDER_REPLICATE)
hp = lum - blur
del blur, lum
energia = cv2.blur(hp * hp, (64, 64), borderType=cv2.BORDER_REPLICATE)
del hp

# mostreig ::4
E = energia[::4, ::4].astype(np.float64).ravel()
del energia
u = 1.0 - np.asarray(mask[::4, ::4], np.float32) / 65535.0  # 1-m
u = u.astype(np.float64).ravel()
ys, xs = np.mgrid[0:H:4, 0:W:4]
r = (np.sqrt((xs - CX) ** 2 + (ys - CY) ** 2) / RS).astype(np.float64).ravel()
del xs, ys

logE = np.log10(E + 1e-12)
res = {"n_mostres": int(u.size)}

def pearson(a, b):
    a = a - a.mean(); b = b - b.mean()
    return float((a @ b) / np.sqrt((a @ a) * (b @ b)))

def spearman(a, b):
    ra = np.argsort(np.argsort(a)).astype(np.float64)
    rb = np.argsort(np.argsort(b)).astype(np.float64)
    return pearson(ra, rb)

res["correlacions_globals"] = {
    "pearson_u_E": pearson(u, E),
    "pearson_u_logE": pearson(u, logE),
    "spearman_u_E": spearman(u, E),
    "pearson_u_r": pearson(u, r),
    "spearman_u_r": spearman(u, r),
    "pearson_logE_r": pearson(logE, r),
}

var_u = float(u.var())

# model f(r): mediana de u per calaix de 0.05 Rsol
rb = np.minimum((r / 0.05).astype(np.int64), 239)
pred_r = np.zeros(240)
ordre = np.argsort(rb, kind="stable")
rb_s = rb[ordre]; u_s = u[ordre]
limits = np.searchsorted(rb_s, np.arange(241))
for i in range(240):
    seg = u_s[limits[i]:limits[i + 1]]
    pred_r[i] = np.median(seg) if seg.size else 0.0
resid_r = u - pred_r[rb]
R2_r = 1.0 - float(resid_r.var()) / var_u

# model g(E): mediana de u per 200 calaixos de quantils de logE
qs = np.quantile(logE, np.linspace(0, 1, 201))
qs[0] -= 1; qs[-1] += 1
eb = np.clip(np.searchsorted(qs, logE, side="right") - 1, 0, 199)
pred_e = np.zeros(200)
ordre = np.argsort(eb, kind="stable")
eb_s = eb[ordre]; u_s = u[ordre]
limits = np.searchsorted(eb_s, np.arange(201))
for i in range(200):
    seg = u_s[limits[i]:limits[i + 1]]
    pred_e[i] = np.median(seg) if seg.size else 0.0
resid_e = u - pred_e[eb]
R2_e = 1.0 - float(resid_e.var()) / var_u

res["ajustos"] = {
    "R2_nomes_radi_f(r)": round(R2_r, 5),
    "R2_nomes_energia_g(E)": round(R2_e, 5),
    "corr_residu_de_f(r)_amb_logE": pearson(resid_r, logE),
    "corr_residu_de_g(E)_amb_r": pearson(resid_e, r),
}

# dins la zona de transicio (0.05 < m < 0.95): a radi fixat, u segueix E?
tz = (u > 0.05) & (u < 0.95)
res["zona_transicio"] = {"n": int(tz.sum())}
if tz.sum() > 1000:
    ut, rt, et = u[tz], r[tz], logE[tz]
    # correlacio parcial de u amb logE controlant r (residus de regressio lineal en r)
    def resid_lin(a, x):
        p = np.polyfit(x, a, 3)
        return a - np.polyval(p, x)
    res["zona_transicio"].update({
        "pearson_u_r": pearson(ut, rt),
        "pearson_u_logE": pearson(ut, et),
        "parcial_u_logE_controlant_r(poli3)": pearson(resid_lin(ut, rt), resid_lin(et, rt)),
    })

# perfil de g(E) i f(r) per al json (mostres per pintar)
res["g_E"] = {"logE_quantils": [round(float(x), 3) for x in (qs[:-1] + np.diff(qs) / 2)][::10],
              "mediana_u": [round(float(x), 4) for x in pred_e][::10]}
res["f_r"] = {"r": [round(0.05 * (i + .5), 3) for i in range(240)][::4],
              "mediana_u": [round(float(x), 4) for x in pred_r][::4]}

with open(OUT + "/b_mascara_vs_detall.json", "w") as f:
    json.dump(res, f, indent=1, ensure_ascii=False)
print(json.dumps(res["correlacions_globals"], indent=1))
print(json.dumps(res["ajustos"], indent=1))
print(json.dumps(res["zona_transicio"], indent=1))
print("fet b_mascara_vs_detall")
