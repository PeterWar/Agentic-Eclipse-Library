# -*- coding: utf-8 -*-
"""Pas 5: simulació endavant. Aplico zoom sintètic a capa1 (G) amb nuclis candidats
i comparo l'empremta (rms del passa-alt per anell) amb la capa2 real.
"""
import numpy as np, cv2, json, os, sys

BASE = "/Users/USUARI/Downloads/Eclipse 2026/research/tools/capes_totals_v14/cau_v19/desenfoc"
SCR = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/dfcda07d-fe88-40c0-8251-cd1d860283ac/scratchpad/desenfoc"
geo = json.load(open(os.path.join(BASE, "geometria.json")))
xc, yc = geo["sol_crop"]; rs = geo["rs"]

G1 = np.array(np.load(os.path.join(BASE, "capa1_rgb16.npy"), mmap_mode="r")[:, :, 1], np.float32)
H, W = G1.shape
M2 = np.asarray(np.load(os.path.join(BASE, "capa2_mask16.npy"), mmap_mode="r")) >= 60000

def zoom_sintetic(img, pesos):
    """pesos: llista (s, w). output(p) = sum w * img(s*(p-c)+c)"""
    out = np.zeros_like(img, np.float32)
    wtot = sum(w for _, w in pesos)
    for s, w in pesos:
        M = np.float32([[s, 0, (1 - s) * xc], [0, s, (1 - s) * yc]])
        out += (w / wtot) * cv2.warpAffine(img, M, (W, H), flags=cv2.WARP_INVERSE_MAP | cv2.INTER_LINEAR,
                                           borderMode=cv2.BORDER_REPLICATE)
    return out

def empremta(img):
    hp = img - cv2.GaussianBlur(img, (0, 0), 8)
    B = 128
    nby, nbx = H // B, W // B
    em = np.zeros((nby, nbx), np.float32)
    for by in range(nby):
        fila = hp[by * B:(by + 1) * B, :nbx * B]
        for bx in range(nbx):
            x = fila[:, bx * B:(bx + 1) * B]
            em[by, bx] = np.sqrt(((x - x.mean()) ** 2).mean())
    return em

ybc = (np.arange(H // 128) + 0.5) * 128; xbc = (np.arange(W // 128) + 0.5) * 128
rb = np.sqrt((xbc[None, :] - xc) ** 2 + (ybc[:, None] - yc) ** 2) / rs
ANELLS = [(3.2, 3.6), (3.6, 4.0), (4.0, 4.4), (4.4, 4.8), (4.8, 5.2), (5.2, 5.6), (5.6, 6.0)]

def perfil(em):
    fila = []
    for lo, hi in ANELLS:
        sel = (rb >= lo) & (rb < hi)
        fila.append(float(np.median(em[sel])))
    return fila

em2 = np.load(os.path.join(SCR, "rms_hp2_blocs.npy"))
print("mesurat capa2:", ["%.2f" % v for v in perfil(em2)])

def uniforme(a, b, n=41):
    return [(s, 1.0) for s in np.linspace(1 - a, 1 + b, n)]
def triangular(a, n=41):
    return [(s, 1 - abs(s - 1) / a + 1e-9) for s in np.linspace(1 - a, 1 + a, n)]
def expo(tau, vmax, n=61):
    return [(np.exp(v), np.exp(-abs(v) / tau)) for v in np.linspace(-vmax, vmax, n)]

candidats = {
    "uniforme ±10%": uniforme(0.10, 0.10),
    "uniforme ±5%": uniforme(0.05, 0.05),
    "uniforme ±2.5%": uniforme(0.025, 0.025),
    "uniforme -10..0 (endins)": uniforme(0.10, 0.0),
    "triangular ±10%": triangular(0.10),
    "triangular ±5%": triangular(0.05),
    "expo tau=0.03 fins ±0.12": expo(0.03, 0.12),
    "expo tau=0.05 fins ±0.20": expo(0.05, 0.20),
}
resultats = {"mesurat_capa2": perfil(em2), "anells": ANELLS}
for nom, pesos in candidats.items():
    sim = zoom_sintetic(G1, pesos)
    p = perfil(empremta(sim))
    resultats[nom] = p
    print("%-28s" % nom, ["%.2f" % v for v in p])
json.dump(resultats, open(os.path.join(BASE, "geometria_fable", "simulacio_empremta.json"), "w"), indent=1)
