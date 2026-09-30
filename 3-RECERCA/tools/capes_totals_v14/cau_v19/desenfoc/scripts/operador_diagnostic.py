# -*- coding: utf-8 -*-
"""Diagnòstic: on viu el bony màxim de cada candidat i què domina els anells.
Treballa tot en polar (compositant amb la màscara remostrejada); només imprimeix."""
import json
import warnings

import cv2
import numpy as np
from scipy.ndimage import median_filter

warnings.filterwarnings("ignore", category=RuntimeWarning)
BASE = "/Users/USUARI/Downloads/Eclipse 2026/research/tools/capes_totals_v14/cau_v19/desenfoc"
geo = json.load(open(BASE + "/geometria.json"))
W, H = geo["llenc"]; cx, cy = geo["sol_crop"]; rs = geo["rs"]
NT, NR, R0, R1 = 4080, 1200, 2.0, 11.5
LNR0 = np.log(R0); DLNR = (np.log(R1) - LNR0) / (NR - 1); DTH = 2 * np.pi / NT
MED_K = 11
c1 = np.load(BASE + "/capa1_rgb16.npy", mmap_mode="r")
c2 = np.load(BASE + "/capa2_rgb16.npy", mmap_mode="r")
mk = np.load(BASE + "/capa2_mask16.npy", mmap_mode="r")

th_g = np.arange(NT) * DTH
r_px = rs * np.exp(LNR0 + np.arange(NR) * DLNR)
MAPX = (cx + np.cos(th_g)[:, None] * r_px[None, :]).astype(np.float32)
MAPY = (cy + np.sin(th_g)[:, None] * r_px[None, :]).astype(np.float32)
IDX_R = np.arange(NR)
r_of_bin = np.exp(LNR0 + IDX_R * DLNR)


def a_polar(img):
    return cv2.remap(img, MAPX, MAPY, interpolation=cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT, borderValue=0.0)


w_pol = a_polar(np.ones((H, W), np.float32))
VALID = w_pol > 0.5


def omple(a, valid):
    idx = np.where(valid, IDX_R[None, :], 0)
    np.maximum.accumulate(idx, axis=1, out=idx)
    return np.take_along_axis(a, idx, axis=1)


def glnr(a, s):
    k = min(2 * int(3 * s) + 1, 1199)
    return cv2.GaussianBlur(a, (k, 1), sigmaX=s, sigmaY=0, borderType=cv2.BORDER_REPLICATE)


def fons(pol, sig):
    pf = omple(pol, VALID)
    pm = median_filter(pf, size=(1, MED_K), mode="nearest")
    s = sig / DLNR
    num, den = glnr(pm * w_pol, s), glnr(w_pol, s)
    return omple(num / np.maximum(den, 1e-6), den > 1e-3)


def gth(a, s):
    k = 2 * int(3 * s) + 1
    pad = int(3 * s) + 1
    ap = np.vstack([a[-pad:], a, a[:pad]])
    return cv2.GaussianBlur(ap, (1, k), sigmaX=0, sigmaY=s,
                            borderType=cv2.BORDER_REPLICATE)[pad:pad + NT]


lum1 = a_polar((c1[..., 0].astype(np.float32) + c1[..., 1] + c1[..., 2]) / 3.0)
lum2 = a_polar((c2[..., 0].astype(np.float32) + c2[..., 1] + c2[..., 2]) / 3.0)
m_pol = a_polar(mk.astype(np.float32) / 65535.0)
lum1f = a_polar(cv2.GaussianBlur((c1[..., 0].astype(np.float32) + c1[..., 1] + c1[..., 2]) / 3.0, (0, 0), 1.2))

A = fons(lum1f, 0.05)
L = fons(lum1f, 0.30)
L20 = fons(lum1f, 0.20)
HIB = L + A - np.where(gth(w_pol, 170) > 1e-3, gth(A * w_pol, 170) / np.maximum(gth(w_pol, 170), 1e-6), A)

candidats = {"F1(capa2)": lum2, "B0.05": A, "B0.20": L20, "B0.30": L, "Bhib15": HIB}


def pava(y):
    v, wt = [], []
    for yi in y:
        v.append(float(yi)); wt.append(1.0)
        while len(v) > 1 and v[-2] < v[-1]:
            vt = (v[-1] * wt[-1] + v[-2] * wt[-2]) / (wt[-1] + wt[-2])
            w2 = wt[-1] + wt[-2]
            v.pop(); wt.pop(); v[-1] = vt; wt[-1] = w2
    return np.concatenate([np.full(int(round(w_)), v_) for v_, w_ in zip(v, wt)])


sel_r = (r_of_bin >= 2.5) & (r_of_bin <= 10.0)
print("== bony per candidat (compost polar amb m): sector, radi i valor del max ==")
for nom, Bp in candidats.items():
    F = lum1 * (1 - m_pol) + Bp * m_pol
    a = np.where(VALID, F, np.nan).reshape(24, 170, NR)
    perf = np.nanmedian(a, axis=1) / 65535.0
    pitjors = []
    for s_ in range(24):
        p = perf[s_]
        ok = np.isfinite(p) & sel_r
        if ok.sum() < 50:
            continue
        fit = pava(p[ok])
        dev = (p[ok] - fit) / np.maximum(fit, 1e-3)
        i = int(np.argmax(dev))
        pitjors.append((float(dev[i]), s_, float(r_of_bin[ok][i])))
    pitjors.sort(reverse=True)
    top = ", ".join(f"s{s_:02d}({s_*15}-{s_*15+15}deg) r={r_:.2f} dev={d:.4f}" for d, s_, r_ in pitjors[:4])
    print(f"{nom:10s}: {top}")

print("\n== anells: variancia i correlacions per components ==")
for rr in (3.0, 5.0, 8.0):
    sel = np.abs(LNR0 + IDX_R * DLNR - np.log(rr)) <= 0.02
    def prof(P):
        return np.nanmedian(np.where(VALID[:, sel], P[:, sel], np.nan), axis=1)
    p1 = prof(lum1)
    ok = np.isfinite(p1)
    p1 = p1[ok]
    def lowhigh(x, s=170):
        k = 2 * int(3 * s) + 1
        pad = int(3 * s) + 1
        xp = np.concatenate([x[-pad:], x, x[:pad]])
        lo = cv2.GaussianBlur(xp.reshape(-1, 1).astype(np.float32), (1, k), sigmaX=0, sigmaY=s,
                              borderType=cv2.BORDER_REPLICATE)[pad:pad + len(x), 0]
        return lo, x - lo
    lo1, hi1 = lowhigh(p1)
    print(f"r={rr}: var total={np.var(p1):.1f} var baixa-freq(>15deg)={np.var(lo1):.1f} "
          f"var alta-freq={np.var(hi1):.1f}")
    for nom, Bp in candidats.items():
        px = prof(Bp)[ok]
        lox, hix = lowhigh(px)
        print(f"   {nom:10s} corr_tot={np.corrcoef(p1, px)[0,1]:.4f} "
              f"corr_baixa={np.corrcoef(lo1, lox)[0,1]:.4f} corr_alta={np.corrcoef(hi1, hix)[0,1]:.4f}")
