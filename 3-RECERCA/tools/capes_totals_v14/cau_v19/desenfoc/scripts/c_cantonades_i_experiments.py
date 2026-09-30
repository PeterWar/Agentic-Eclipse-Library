# -*- coding: utf-8 -*-
"""2: cantonades pintades de capa2. 3: experiments apagats capa0/capa3 (q4).

Nomes lectura; json + png (llenc sencer) a fable/.
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
mask = np.load(BASE + "/capa2_mask16.npy", mmap_mode="r")
res = {}

# ---------- 2) cantonades ----------
# finestres de 1200x1200 a resolucio plena, mostrejades ::2 -> 600x600
def finestra(arr, cant, mida=1200, pas=2):
    if cant == "NW": sl = (slice(0, mida, pas), slice(0, mida, pas))
    elif cant == "NE": sl = (slice(0, mida, pas), slice(W - mida, W, pas))
    elif cant == "SW": sl = (slice(H - mida, H, pas), slice(0, mida, pas))
    else: sl = (slice(H - mida, H, pas), slice(W - mida, W, pas))
    return np.asarray(arr[sl], np.float32)

cantons = {"NW": (0, 0), "NE": (W - 1, 0), "SW": (0, H - 1), "SE": (W - 1, H - 1)}
res["cantonades"] = {}
for nom, (px, py) in cantons.items():
    w1 = finestra(c1, nom); w2 = finestra(c2, nom); wm = finestra(mask, nom) / 65535.0
    d = {}
    d["mediana_RGB_capa1"] = [int(np.median(w1[:, :, k])) for k in range(3)]
    d["mediana_RGB_capa2"] = [int(np.median(w2[:, :, k])) for k in range(3)]
    d["std_RGB_capa1"] = [round(float(w1[:, :, k].std()), 1) for k in range(3)]
    d["std_RGB_capa2"] = [round(float(w2[:, :, k].std()), 1) for k in range(3)]
    d["mediana_m"] = round(float(np.median(wm)), 5)
    # variacio local (passa-alt 15 px) de capa2 vs capa1, lluminancia
    l1 = w1.mean(axis=2); l2 = w2.mean(axis=2)
    hp1 = l1 - cv2.blur(l1, (15, 15)); hp2 = l2 - cv2.blur(l2, (15, 15))
    d["std_passaalt15_capa1"] = round(float(hp1.std()), 2)
    d["std_passaalt15_capa2"] = round(float(hp2.std()), 2)
    res["cantonades"][nom] = d

# extensio de la zona coberta: finestres grans 2400x2400 ::2, anells de 60 px (::2)
res["extensio_pintat"] = {}
for nom, (px, py) in cantons.items():
    wg1 = finestra(c1, nom, 2400); wg2 = finestra(c2, nom, 2400)
    l1 = wg1.mean(axis=2); l2 = wg2.mean(axis=2)
    hp2 = l2 - cv2.blur(l2, (15, 15))
    n = l1.shape[0]
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    # distancia (en px de resolucio plena = *2) des de la cantonada de la finestra
    if nom == "NW": dd = np.sqrt(xx ** 2 + yy ** 2) * 2
    elif nom == "NE": dd = np.sqrt((n - 1 - xx) ** 2 + yy ** 2) * 2
    elif nom == "SW": dd = np.sqrt(xx ** 2 + (n - 1 - yy) ** 2) * 2
    else: dd = np.sqrt((n - 1 - xx) ** 2 + (n - 1 - yy) ** 2) * 2
    perfil = []
    for r0 in range(0, 2400, 100):
        sel = (dd >= r0) & (dd < r0 + 100)
        if sel.sum() < 50: continue
        perfil.append({
            "dist_px": r0 + 50,
            "std_hp15_capa2": round(float(hp2[sel].std()), 2),
            "med_abs_dif_l2_l1": round(float(np.median(np.abs(l2[sel] - l1[sel]))), 1),
            "med_l1": round(float(np.median(l1[sel])), 1),
            "med_l2": round(float(np.median(l2[sel])), 1),
        })
    res["extensio_pintat"][nom] = perfil

# color exacte del pintat: mediana RGB de capa2 al disc de 300 px de cada cantonada
res["color_pintat_RGB16"] = {}
for nom in cantons:
    w2 = finestra(c2, nom, 600, 1)
    n = w2.shape[0]
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    if nom == "NW": dd = np.sqrt(xx**2 + yy**2)
    elif nom == "NE": dd = np.sqrt((n-1-xx)**2 + yy**2)
    elif nom == "SW": dd = np.sqrt(xx**2 + (n-1-yy)**2)
    else: dd = np.sqrt((n-1-xx)**2 + (n-1-yy)**2)
    sel = dd < 300
    med = [int(np.median(w2[:, :, k][sel])) for k in range(3)]
    p5 = [int(np.percentile(w2[:, :, k][sel], 5)) for k in range(3)]
    p95 = [int(np.percentile(w2[:, :, k][sel], 95)) for k in range(3)]
    res["color_pintat_RGB16"][nom] = {"mediana": med, "p5": p5, "p95": p95}

# cel de capa1 a r = 8-10 Rsol (mostreig ::4)
a1 = np.asarray(c1[::4, ::4], np.float32)
ys, xs = np.mgrid[0:H:4, 0:W:4]
r4 = np.sqrt((xs - CX) ** 2 + (ys - CY) ** 2) / RS
sel = (r4 >= 8) & (r4 <= 10)
res["cel_capa1_r8_10"] = {
    "mediana_RGB": [int(np.median(a1[:, :, k][sel])) for k in range(3)],
    "p25_RGB": [int(np.percentile(a1[:, :, k][sel], 25)) for k in range(3)],
    "p75_RGB": [int(np.percentile(a1[:, :, k][sel], 75)) for k in range(3)],
    "n_px": int(sel.sum()),
}
sel2 = (r4 >= 6) & (r4 <= 8)
res["cel_capa1_r6_8"] = {
    "mediana_RGB": [int(np.median(a1[:, :, k][sel2])) for k in range(3)]}

# vista de les diferencies |capa2-capa1| al llenc sencer ::4 (on treballa el pintat+zoom)
a2 = np.asarray(c2[::4, ::4], np.float32)
dif = np.abs(a2 - a1).mean(axis=2)
d8 = np.clip(dif / dif.max() * 255 * 4, 0, 255).astype(np.uint8)  # x4 de guany
cv2.imwrite(OUT + "/vista_dif_capa2_capa1_x4_guany4.png", d8)
res["dif_c2_c1"] = {"max_lum": float(dif.max()), "p50": float(np.median(dif)),
                    "p99": float(np.percentile(dif, 99))}

# ---------- 3) experiments apagats q4 ----------
c0 = np.asarray(np.load(BASE + "/capa0_rgb16_q4.npy"), np.float32)
m0 = np.asarray(np.load(BASE + "/capa0_mask16_q4.npy"), np.float32) / 65535.0
c3 = np.asarray(np.load(BASE + "/capa3_rgb16_q4.npy"), np.float32)
m3 = np.asarray(np.load(BASE + "/capa3_mask16_q4.npy"), np.float32) / 65535.0
c1q = np.asarray(c1[::4, ::4], np.float32)
c2q = np.asarray(c2[::4, ::4], np.float32)
mq = np.asarray(mask[::4, ::4], np.float32) / 65535.0
hq, wq = c0.shape[:2]
res["q4"] = {"forma": [int(hq), int(wq)],
             "forma_c1_q4": [int(c1q.shape[0]), int(c1q.shape[1])]}

def pearson(a, b):
    a = a.ravel().astype(np.float64); b = b.ravel().astype(np.float64)
    a = a - a.mean(); b = b - b.mean()
    return float((a @ b) / np.sqrt((a @ a) * (b @ b)))

l0 = c0.mean(2); l3 = c3.mean(2); l1q = c1q.mean(2); l2q = c2q.mean(2)
res["q4"]["identitat"] = {
    "c0_vs_c3_max_absdif": float(np.abs(c0 - c3).max()),
    "c0_vs_c1q_corr": pearson(l0, l1q), "c0_vs_c2q_corr": pearson(l0, l2q),
    "c3_vs_c1q_corr": pearson(l3, l1q), "c3_vs_c2q_corr": pearson(l3, l2q),
    "c0_vs_c1q_rms": float(np.sqrt(((l0 - l1q) ** 2).mean())),
    "c0_vs_c2q_rms": float(np.sqrt(((l0 - l2q) ** 2).mean())),
    "c3_vs_c1q_rms": float(np.sqrt(((l3 - l1q) ** 2).mean())),
    "c3_vs_c2q_rms": float(np.sqrt(((l3 - l2q) ** 2).mean())),
    "m0_vs_m3_max_absdif": float(np.abs(m0 - m3).max()),
    "m0_vs_mq_rms": float(np.sqrt(((m0 - mq) ** 2).mean())),
    "m3_vs_mq_rms": float(np.sqrt(((m3 - mq) ** 2).mean())),
}
res["q4"]["mascares"] = {
    "mitjana_m0": round(float(m0.mean()), 5), "mitjana_m3": round(float(m3.mean()), 5),
    "mitjana_mq_capa2": round(float(mq.mean()), 5),
    "frac_m0_0": round(float((m0 < 1/1024).mean()), 5),
    "frac_m0_1": round(float((m0 > 1023/1024).mean()), 5),
    "frac_m3_0": round(float((m3 < 1/1024).mean()), 5),
    "frac_m3_1": round(float((m3 > 1023/1024).mean()), 5),
}

# geometria a q4
cxq, cyq, rsq = CX / 4, CY / 4, RS / 4
ysq, xsq = np.mgrid[0:hq, 0:wq].astype(np.float32)
rq = np.sqrt((xsq - cxq) ** 2 + (ysq - cyq) ** 2) / rsq
thq = np.arctan2(ysq - cyq, xsq - cxq)
urx, ury = np.cos(thq), np.sin(thq)  # radial unitari

def perfil_mascara(m, nom):
    prof = []
    for i in range(0, 45):
        sel = (rq >= i * 0.25) & (rq < (i + 1) * 0.25)
        if sel.sum() < 100: continue
        prof.append([round(0.25 * i + 0.125, 3), round(float(np.median(m[sel])), 4)])
    res["q4"].setdefault("perfil_mascara", {})[nom] = prof

perfil_mascara(m0, "capa0"); perfil_mascara(m3, "capa3"); perfil_mascara(mq, "capa2_q4")

# rugositat radial i direccional: energia del gradient radial vs tangencial per anell
def rugositat(l, nom):
    gy, gx = np.gradient(l)
    gr = gx * urx + gy * ury          # component radial
    gt = -gx * ury + gy * urx         # component tangencial
    hp = l - cv2.GaussianBlur(l, (0, 0), 4)
    prof = []
    for r0, r1 in [(1.2, 2), (2, 3), (3, 4.5), (4.5, 6.5), (6.5, 9)]:
        sel = (rq >= r0) & (rq < r1)
        prof.append({
            "anell_Rsol": [r0, r1],
            "rms_grad_radial": round(float(np.sqrt((gr[sel] ** 2).mean())), 2),
            "rms_grad_tangencial": round(float(np.sqrt((gt[sel] ** 2).mean())), 2),
            "rms_passaalt_s4": round(float(np.sqrt((hp[sel] ** 2).mean())), 2),
        })
    res["q4"].setdefault("rugositat", {})[nom] = prof

for l, nom in [(l1q, "capa1_q4"), (l2q, "capa2_q4"), (l0, "capa0"), (l3, "capa3")]:
    rugositat(l, nom)

# vistes q4 dels experiments (llenc sencer, ja son 1/4)
for arr, nom in [(c0, "capa0_rgb"), (c3, "capa3_rgb")]:
    cv2.imwrite(OUT + "/vista_%s_q4.png" % nom,
                np.clip(arr / 257.0, 0, 255).astype(np.uint8)[:, :, ::-1])
for arr, nom in [(m0, "capa0_mask"), (m3, "capa3_mask")]:
    cv2.imwrite(OUT + "/vista_%s_q4.png" % nom, (arr * 255).astype(np.uint8))
# diferencia capa0 - capa1q4 (que ha canviat en l'experiment apagat)
d0 = np.abs(l0 - l1q); d3 = np.abs(l3 - l1q)
esc = max(d0.max(), d3.max(), 1)
cv2.imwrite(OUT + "/vista_dif_capa0_capa1_q4.png", np.clip(d0 / esc * 255 * 4, 0, 255).astype(np.uint8))
cv2.imwrite(OUT + "/vista_dif_capa3_capa1_q4.png", np.clip(d3 / esc * 255 * 4, 0, 255).astype(np.uint8))

with open(OUT + "/c_cantonades_i_experiments.json", "w") as f:
    json.dump(res, f, indent=1, ensure_ascii=False)
print(json.dumps(res["cantonades"], indent=1))
print(json.dumps(res["color_pintat_RGB16"], indent=1))
print(json.dumps(res["cel_capa1_r8_10"], indent=1))
print(json.dumps(res["q4"]["identitat"], indent=1))
print(json.dumps(res["q4"]["mascares"], indent=1))
print("fet c_cantonades_i_experiments")
