"""V21 · les dues capes finals, sense fabricar res.

EARTHSHINE: el disc mesurat pels DOS TRENS (8 fotogrames), amb el vel de
llum escampada restat. El contrast real és del 0,36 % del disc, o sigui que
per veure'l cal amplificar-lo: el factor va DECLARAT al nom de la capa i al
rebut.

ESTRELLES: ⛔ cap disc dibuixat. El contingut I la màscara surten de la llum
REALMENT enregistrada a l'apilat (excés sobre el fons local); el catàleg
només diu QUINES d'aquelles fonts són estrelles i com es diuen.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np, cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
AMPL = 30.0                      # amplificació de contrast, DECLARADA
PEDESTAL = 0.38


def capa_earthshine(W, H):
    E = np.load(f"{CAU}/earthshine_producte.npy")
    dins = np.load(f"{CAU}/earthshine_producte_dins.npy")
    reb = json.load(open(f"{CAU}/earthshine_producte_rebut.json"))
    x0, y0, x1, y1 = reb["bbox"]
    MB = reb["centre_disc"]; RL = reb["RL"]
    h, w = dins.shape
    yy = np.arange(y0, y1, dtype=np.float32)[:, None]
    xx = np.arange(x0, x1, dtype=np.float32)[None, :]
    rr = np.hypot(xx - MB[0], yy - MB[1]) / RL
    mer = cv2.erode(dins.astype(np.uint8), np.ones((41, 41), np.uint8)).astype(bool)
    sg = float(E[..., 1][mer].std())
    px = np.zeros((h, w, 3), np.uint16)
    for c in range(3):
        v = PEDESTAL + (AMPL * E[..., c] / max(sg, 1e-9)) * (0.361 / 100.0)
        px[..., c] = np.clip(np.rint(v * 65535), 0, 65535).astype(np.uint16)
    m = np.clip((0.945 - rr) / 0.045, 0, 1) * dins
    msk = np.clip(np.rint(cv2.GaussianBlur(m.astype(np.float32), (0, 0), 2.0)
                          * 65535), 0, 65535).astype(np.uint16)
    return px, msk, (int(y0), int(x0)), {"sigma_comptes": sg,
                                         "amplificacio": AMPL,
                                         "pedestal": PEDESTAL,
                                         "contrast_real_pct": reb["amplitud_pct"]}


def capa_estrelles(W, H):
    """El contingut I la màscara surten de la llum mesurada."""
    est = json.load(open(f"{CAU}/estrelles_purga.json"))
    ap = np.load(f"{CAU}/apilat_estrelles_rgb.npy", mmap_mode="r")
    G = np.asarray(ap[..., 1], np.float32)
    fons = cv2.GaussianBlur(cv2.medianBlur(G, 5), (0, 0), 10.0)
    D = G - fons
    del fons
    E16 = np.zeros((H, W, 3), np.uint16)
    S = np.zeros((H, W), np.float32)
    R = 9
    for z in est:
        xi, yi = int(round(z["x"])), int(round(z["y"]))
        if not (R < xi < W - R and R < yi < H - R):
            continue
        w = D[yi - R:yi + R + 1, xi - R:xi + R + 1]
        pic = float(w.max())
        if pic <= 0:
            continue
        # la forma és la de la llum de l'estrella, no un disc dibuixat
        oy, ox = np.mgrid[-R:R + 1, -R:R + 1]
        dins = np.hypot(oy, ox) <= R
        f = np.clip(w / pic, 0.0, 1.0) * dins
        reg = S[yi - R:yi + R + 1, xi - R:xi + R + 1]
        np.maximum(reg, f, out=reg)
    viu = S > 0.004
    for c in range(3):
        A = np.asarray(ap[..., c], np.float32)
        fl = cv2.GaussianBlur(cv2.medianBlur(A, 5), (0, 0), 10.0)
        E16[..., c] = np.where(viu, np.clip(A - fl, 0, 65535), 0).astype(np.uint16)
        del A, fl
    S16 = np.clip(np.rint(S * 65535), 0, 65535).astype(np.uint16)
    return E16, S16, len(est)


if __name__ == "__main__":
    W, H = 12415, 12095
    px, msk, pos, md = capa_earthshine(W, H)
    np.save(f"{CAU}/capa_es_px.npy", px); np.save(f"{CAU}/capa_es_msk.npy", msk)
    json.dump({"pos": pos, **md}, open(f"{CAU}/capa_es_meta.json", "w"), indent=1)
    print(f"EARTHSHINE: tessel·la {px.shape} a (y={pos[0]}, x={pos[1]}) · "
          f"σ={md['sigma_comptes']:.2f} comptes · contrast real "
          f"{md['contrast_real_pct']:.3f} % · amplificat ×{AMPL:g}")
    E16, S16, n = capa_estrelles(W, H)
    np.save(f"{CAU}/capa_est_px.npy", E16); np.save(f"{CAU}/capa_est_msk.npy", S16)
    print(f"ESTRELLES: {n} fonts · màscara i contingut = llum mesurada "
          f"(cap disc dibuixat) · px vius {int((S16>0).sum())}")
