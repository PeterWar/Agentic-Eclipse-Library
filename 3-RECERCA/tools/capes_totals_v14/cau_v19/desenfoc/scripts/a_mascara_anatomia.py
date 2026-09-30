# -*- coding: utf-8 -*-
"""Anatomia de capa2_mask16: rampa radial per sectors, suavitat, vistes.

Nomes lectura dels .npy (mmap). Sortides a cau_v19/desenfoc/fable/.
"""
import json
import numpy as np
import cv2

BASE = "/Users/USUARI/Downloads/Eclipse 2026/research/tools/capes_totals_v14/cau_v19/desenfoc"
OUT = BASE + "/fable"

geo = json.load(open(BASE + "/geometria.json"))
W, H = geo["llenc"]          # 8156, 5422
CX, CY = geo["sol_crop"]     # 4273.2, 2633.6
RS = geo["rs"]               # 455.5

mask = np.load(BASE + "/capa2_mask16.npy", mmap_mode="r")  # (H, W) uint16
assert mask.shape == (H, W), mask.shape

NSEC = 24
NRAD = 113  # 0.1 R_sol per calaix, fins a 11.3
res = {}

# ---------- 1a) mediana de m per calaix radial i per sector ----------
# histograma 256 nivells per (sector, radi) i 65536 nivells per radi global
hist_sec = np.zeros(NSEC * NRAD * 256, dtype=np.int64)
hist_rad = np.zeros(NRAD * 1024, dtype=np.int64)
xs = np.arange(W, dtype=np.float32) - CX
CH = 256
for y0 in range(0, H, CH):
    y1 = min(y0 + CH, H)
    ys = np.arange(y0, y1, dtype=np.float32) - CY
    dy = ys[:, None]
    r = np.sqrt(xs[None, :] ** 2 + dy ** 2) / RS
    rbin = np.minimum((r * 10).astype(np.int32), NRAD - 1)
    th = np.arctan2(dy, xs[None, :])  # -pi..pi, y avall
    sbin = ((th + np.pi) / (2 * np.pi) * NSEC).astype(np.int32) % NSEC
    mch = np.asarray(mask[y0:y1], dtype=np.uint16)
    m8 = (mch >> 8).astype(np.int32)
    m10 = (mch >> 6).astype(np.int32)
    idx = (sbin * NRAD + rbin) * 256 + m8
    hist_sec += np.bincount(idx.ravel(), minlength=hist_sec.size)
    idx2 = rbin * 1024 + m10
    hist_rad += np.bincount(idx2.ravel(), minlength=hist_rad.size)

hist_sec = hist_sec.reshape(NSEC, NRAD, 256)
hist_rad = hist_rad.reshape(NRAD, 1024)

def mediana_hist(h, nivells):
    """mediana (en unitats m 0..1) d'un histograma h de `nivells` calaixos."""
    n = h.sum()
    if n == 0:
        return np.nan
    c = np.cumsum(h)
    i = int(np.searchsorted(c, (n + 1) // 2))
    return (i + 0.5) / nivells

med_rad = np.array([mediana_hist(hist_rad[i], 1024) for i in range(NRAD)])
med_sec = np.full((NSEC, NRAD), np.nan)
for s in range(NSEC):
    for i in range(NRAD):
        med_sec[s, i] = mediana_hist(hist_sec[s, i], 256)

cnt_rad = hist_rad.sum(axis=1)
radis = (np.arange(NRAD) + 0.5) * 0.1

# on comenca a pujar i on arriba a 1 (perfil global)
def primer_radi(cond):
    ii = np.where(cond & (cnt_rad > 1000))[0]
    return float(radis[ii[0]]) if ii.size else None

res["perfil_radial"] = {
    "radis_Rsol": radis.tolist(),
    "mediana_m": [None if np.isnan(v) else round(float(v), 5) for v in med_rad],
    "n_px": cnt_rad.tolist(),
    "primer_radi_m_sup_0p01": primer_radi(med_rad > 0.01),
    "primer_radi_m_sup_0p05": primer_radi(med_rad > 0.05),
    "primer_radi_m_sup_0p50": primer_radi(med_rad > 0.50),
    "primer_radi_m_sup_0p95": primer_radi(med_rad > 0.95),
    "primer_radi_m_sup_0p99": primer_radi(med_rad > 0.99),
    "primer_radi_m_sup_0p999": primer_radi(med_rad > 0.999),
}

# variacio azimutal: per cada radi, min/max/rang de les medianes de sector
valid = cnt_rad > 1000
rang_sec = np.nanmax(med_sec, axis=0) - np.nanmin(med_sec, axis=0)
res["variacio_azimutal"] = {
    "rang_max_entre_sectors": round(float(np.nanmax(rang_sec[valid])), 5),
    "radi_del_rang_max": float(radis[valid][int(np.nanargmax(rang_sec[valid]))]),
    "rang_mitja_entre_sectors": round(float(np.nanmean(rang_sec[valid])), 5),
}
# radi on cada sector creua m=0.5 i m=0.95
creua = {}
for s in range(NSEC):
    prof = med_sec[s]
    def cr(th):
        ii = np.where((prof > th) & (cnt_rad > 200))[0]
        return float(radis[ii[0]]) if ii.size else None
    ang0 = -180 + s * 15
    creua["sector_%02d_(%d..%ddeg)" % (s, ang0, ang0 + 15)] = {
        "r_m05": cr(0.5), "r_m095": cr(0.95)}
res["creuament_per_sector"] = creua

# estadistics globals de la mascara
tot = hist_rad.sum(axis=0)
res["global"] = {
    "mitjana_m": round(float((np.arange(1024) + 0.5) @ tot / tot.sum() / 1024), 5),
    "frac_m_0_exacte": round(float(tot[0] / tot.sum()), 5),
    "frac_m_1_calaix_maxim": round(float(tot[-1] / tot.sum()), 5),
}

# ---------- 1c) suavitat: gradient de m ----------
m = np.asarray(mask, dtype=np.float32) / 65535.0
gy, gx = np.gradient(m)
gmag = np.sqrt(gx * gx + gy * gy)
del gx, gy

hbins = np.concatenate([[0], np.logspace(-6, 0, 61)])
hh, _ = np.histogram(gmag, bins=hbins)
res["gradient"] = {
    "bins": hbins.tolist(),
    "histograma": hh.tolist(),
    "p50": float(np.median(gmag)),
    "p90": float(np.percentile(gmag, 90)),
    "p99": float(np.percentile(gmag, 99)),
    "p999": float(np.percentile(gmag, 99.9)),
    "max": float(gmag.max()),
}
trans = (m > 0.05) & (m < 0.95)
gt = gmag[trans]
gt = gt[gt > 1e-6]
amplada = 1.0 / gt  # px per recorrer 0->1 al pendent local
res["transicions"] = {
    "n_px_transicio": int(trans.sum()),
    "frac_px_transicio": round(float(trans.mean()), 5),
    "amplada_px_p10": float(np.percentile(amplada, 10)),
    "amplada_px_p50": float(np.percentile(amplada, 50)),
    "amplada_px_p90": float(np.percentile(amplada, 90)),
}
# vores dures: pas > 0.5 en < 4 px  <=>  |grad m| > 0.125 /px
dures = gmag > 0.125
n_dures = int(dures.sum())
res["vores_dures"] = {"criteri": "|grad m| > 0.125 per px", "n_px": n_dures}
if n_dures:
    yy, xx = np.where(dures)
    rr = np.sqrt((xx - CX) ** 2 + (yy - CY) ** 2) / RS
    res["vores_dures"].update({
        "r_min_Rsol": float(rr.min()), "r_p50_Rsol": float(np.median(rr)),
        "r_max_Rsol": float(rr.max()),
        "bbox_xyxy": [int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())],
    })
del gmag, trans

# ---------- 1d) vistes (llenc sencer, ::4) ----------
m4 = m[::4, ::4]
cv2.imwrite(OUT + "/vista_mascara_m_x4.png", (m4 * 255).astype(np.uint8))

c1 = np.load(BASE + "/capa1_rgb16.npy", mmap_mode="r")
c2 = np.load(BASE + "/capa2_rgb16.npy", mmap_mode="r")
a1 = np.asarray(c1[::4, ::4], dtype=np.float32)
a2 = np.asarray(c2[::4, ::4], dtype=np.float32)
comp = a1 * (1 - m4[..., None]) + a2 * m4[..., None]
comp8 = np.clip(comp / 257.0, 0, 255).astype(np.uint8)
cv2.imwrite(OUT + "/vista_compost_x4.png", comp8[:, :, ::-1])

# sobreposicio: compost + tinta JET de m al 35% + contorns 0.1/0.5/0.9
tinta = cv2.applyColorMap((m4 * 255).astype(np.uint8), cv2.COLORMAP_JET)
over = (comp8[:, :, ::-1].astype(np.float32) * 0.65 + tinta.astype(np.float32) * 0.35)
over = np.clip(over, 0, 255).astype(np.uint8)
for niv, col in [(0.1, (255, 255, 255)), (0.5, (0, 255, 255)), (0.9, (0, 0, 255))]:
    bw = (m4 >= niv).astype(np.uint8)
    cs, _ = cv2.findContours(bw, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(over, cs, -1, col, 2)
cv2.imwrite(OUT + "/vista_mascara_sobre_compost_x4.png", over)

with open(OUT + "/a_mascara_anatomia.json", "w") as f:
    json.dump(res, f, indent=1, ensure_ascii=False)
print("fet a_mascara_anatomia")
print(json.dumps({k: res[k] for k in ["global", "variacio_azimutal", "transicions", "vores_dures"]},
                 indent=1, ensure_ascii=False))
print("perfil radial (r, mediana m):")
for i in range(0, NRAD, 5):
    print(" %5.2f  %s" % (radis[i], res["perfil_radial"]["mediana_m"][i]))
