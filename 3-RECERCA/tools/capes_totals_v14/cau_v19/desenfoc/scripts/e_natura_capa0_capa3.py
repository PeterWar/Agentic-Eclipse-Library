# -*- coding: utf-8 -*-
"""Natura fina dels experiments apagats:
 - capa0: quina sigma de desenfoc gaussia equival (contra capa1_q4 i capa2_q4)
 - capa3: colors i radis dels tracos de retolador; fraccio de negre; el fons
   fora dels tracos es identic a capa1_q4?
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
r1q = np.asarray(c1[::4, ::4], np.float32)
r2q = np.asarray(c2[::4, ::4], np.float32)
l1q = r1q.mean(2); l2q = r2q.mean(2)
c0 = np.asarray(np.load(BASE + "/capa0_rgb16_q4.npy"), np.float32)
c3 = np.asarray(np.load(BASE + "/capa3_rgb16_q4.npy"), np.float32)
l0 = c0.mean(2); l3 = c3.mean(2)
hq, wq = l0.shape
cxq, cyq, rsq = CX / 4, CY / 4, RS / 4
ysq, xsq = np.mgrid[0:hq, 0:wq].astype(np.float32)
rq = np.sqrt((xsq - cxq) ** 2 + (ysq - cyq) ** 2) / rsq
res = {}

# --- capa0: millor sigma equivalent (a escala q4; x4 per a res. plena) ---
sel = (rq > 1.0) & (rq < 9.5)
for font, lf in [("capa1_q4", l1q), ("capa2_q4", l2q)]:
    fila = {}
    for s in [4, 8, 12, 16, 24, 32, 48, 64, 96]:
        b = cv2.GaussianBlur(lf, (0, 0), s)
        d = l0[sel] - b[sel]
        fila["sigma_%d" % s] = {"rms": round(float(np.sqrt((d ** 2).mean())), 1),
                                "corr": round(float(np.corrcoef(l0[sel], b[sel])[0, 1]), 5)}
    res["capa0_gauss_de_" + font] = fila

# --- capa3 ---
# tracos: colors saturats fora de la gamma del cel. Croma = distancia al gris
mx = c3.max(2); mn = c3.min(2)
croma = (mx - mn) / (mx + 1)
negre = mx < 500
verd = (c3[:, :, 1] > c3[:, :, 0] * 1.15) & (c3[:, :, 1] > c3[:, :, 2] * 1.15) & ~negre
taronja = (c3[:, :, 0] > c3[:, :, 2] * 1.3) & (c3[:, :, 0] > 20000) & ~negre
res["capa3"] = {
    "frac_negre_sota500": round(float(negre.mean()), 5),
    "frac_verd": round(float(verd.mean()), 5),
    "frac_taronja": round(float(taronja.mean()), 5),
    "r_negre_p50_p99_Rsol": [round(float(np.percentile(rq[negre], q)), 2) for q in (50, 99)],
}
for nom, selm in [("verd", verd), ("taronja", taronja)]:
    if selm.sum() > 100:
        res["capa3"]["traç_" + nom] = {
            "RGB16_mediana": [int(np.median(c3[:, :, k][selm])) for k in range(3)],
            "r_Rsol_p5_p50_p95": [round(float(np.percentile(rq[selm], q)), 2) for q in (5, 50, 95)],
            "n_px_q4": int(selm.sum()),
        }
# fons fora de tracos i negre: identic a capa1_q4? a capa2_q4?
resta = ~(negre | verd | taronja) & (rq > 1.0)
d1 = np.abs(l3 - l1q)[resta]; d2 = np.abs(l3 - l2q)[resta]
res["capa3"]["fons_vs_capa1q4"] = {"med_absdif": round(float(np.median(d1)), 1),
                                   "p95_absdif": round(float(np.percentile(d1, 95)), 1)}
res["capa3"]["fons_vs_capa2q4"] = {"med_absdif": round(float(np.median(d2)), 1),
                                   "p95_absdif": round(float(np.percentile(d2, 95)), 1)}
# el fons de capa3 esta desenfocat? passa-alt s4 fora dels tracos
hp3 = l3 - cv2.GaussianBlur(l3, (0, 0), 4)
hp1 = l1q - cv2.GaussianBlur(l1q, (0, 0), 4)
lluny = resta & (rq > 3) & (rq < 8) & (cv2.dilate((negre | verd | taronja).astype(np.uint8), np.ones((25, 25), np.uint8)) == 0)
res["capa3"]["fons_rms_hp_s4"] = round(float(np.sqrt((hp3[lluny] ** 2).mean())), 2)
res["capa3"]["capa1q4_rms_hp_s4_mateixa_zona"] = round(float(np.sqrt((hp1[lluny] ** 2).mean())), 2)

with open(OUT + "/e_natura_capa0_capa3.json", "w") as f:
    json.dump(res, f, indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
