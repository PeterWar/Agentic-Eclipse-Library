"""L'ESTRIAT, decidit. Vixen contra Sony al llenç comú.

Tres hipòtesis i un experiment que les separa totes tres alhora, perquè els dos
sensors estan girats 33,08° i tenen escales diferents:

  CEL          → mateixa direcció i mateixa mida als dos
  SENSOR       → direcció girada 33,08°, mateixa mida
  PÍXEL SENSOR → direcció girada 33,08° i mida ×1,49 a la Sony

Es mesura a l'anell 1,4–2,6 R☉, que és on viuen els set traços que Pere va
marcar (1,56–2,43 R☉), i sobre l'estructura NORMALITZADA PER RADI.
"""
from __future__ import annotations

import json
import os

import numpy as np
from PIL import Image

import nucli as N
from estriat import normalitza_radi, espectre, pics

CAPA = "DETALL_PASSA_ALT"
R0, R1 = 1.40, 2.60
MARQUES = ("/Users/USUARI/Desktop/Eclipse determinista/2-OUTPUT/"
           "MARQUES_DE_PERE/on_has_marcat.png")


def carrega_capa(tren, capa=CAPA):
    d = N.darrer_run(tren)
    p = os.path.join(d, "3-filtres", f"{capa}.npy")
    if not os.path.exists(p):
        raise SystemExit(f"falta {p}")
    a = np.load(p)
    m = np.load(os.path.join(d, "3-filtres", "MASCARA.npy"))
    S = json.load(open(os.path.join(d, "4-rebuts", "F1.2_sol_llenc.json")))
    return a, m, S["llenc"], d


def zona_marcada(H, W):
    if not os.path.exists(MARQUES):
        return None
    a = np.asarray(Image.open(MARQUES).convert("RGB")).astype(int)
    k = (np.ptp(a, axis=2) > 25)
    f = H / k.shape[0]
    ys, xs = np.nonzero(k)
    z = np.zeros((H, W), bool)
    z[np.clip((ys * f).astype(int), 0, H - 1),
      np.clip((xs * f).astype(int), 0, W - 1)] = True
    import cv2
    return cv2.dilate(z.astype(np.uint8), np.ones((13, 13), np.uint8)).astype(bool)


if __name__ == "__main__":
    E = {}
    for tren in ("VIXEN", "SONY"):
        a, m, LL, d = carrega_capa(tren)
        H, W = a.shape
        RS = LL["R_sol_px"]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        rad = np.hypot(yy - H / 2.0, xx - W / 2.0); del yy, xx
        k = m & (rad >= R0 * RS) & (rad <= R1 * RS) & np.isfinite(a)
        z = normalitza_radi(a.astype(np.float64), k, rad)
        P = espectre(z, k)
        M, lams, angs = pics(P, LL["escala_arcsec_px"])
        E[tren] = dict(M=M, lams=lams, angs=angs, LL=LL, run=os.path.basename(d),
                       n=int(k.sum()), rad=rad, k=k, z=z, H=H, W=W)
        print(f"{tren}: run {os.path.basename(d)} · {k.sum():,} px a l'anell "
              f"{R0}–{R1} R☉ · escala sensor {LL.get('escala_sensor_arcsec_px', LL['escala_arcsec_px'])} ''/px")

    print(f"\ngir entre sensors al cel: {N.GIR_ENTRE_SENSORS:.2f}°   "
          f"·  factor d'escala Sony/Vixen: {N.ESC['SONY']/N.ESC['VIXEN']:.3f}")

    for tren in ("VIXEN", "SONY"):
        M, lams, angs = E[tren]["M"], E[tren]["lams"], E[tren]["angs"]
        Mn = M / np.nanmedian(M, axis=1, keepdims=True)     # excés sobre l'anell
        print(f"\n{tren} · els 6 pics més forts (excés sobre la mediana de la seva λ):")
        idx = np.dstack(np.unravel_index(np.argsort(np.nan_to_num(Mn).ravel())[::-1],
                                         Mn.shape))[0]
        vistos = []
        for i, j in idx:
            if any(abs(np.log(lams[i] / l)) < 0.25 and
                   min(abs(angs[j] - a_), 180 - abs(angs[j] - a_)) < 12 for l, a_ in vistos):
                continue
            vistos.append((lams[i], angs[j]))
            print(f"   λ = {lams[i]:6.1f} px de llenç  ({lams[i]*N.ESC['VIXEN']:6.1f} ″)"
                  f"   direcció {angs[j]:5.1f}°   ×{Mn[i, j]:5.2f}")
            if len(vistos) >= 6:
                break
        E[tren]["pics"] = vistos

    # ------------------------------------------------------------ el veredicte
    G = N.GIR_ENTRE_SENSORS          # 33,075
    F = N.ESC["SONY"] / N.ESC["VIXEN"]   # 1,4897
    def dang(a, b):
        d = abs(a - b) % 180.0
        return min(d, 180.0 - d)
    print("\n" + "=" * 74)
    print("VEREDICTE. Per a cada pic de la Vixen, on l'hauria de tenir la Sony:")
    print(f"  CEL          -> mateixa direccio, mateixa mida")
    print(f"  SENSOR       -> direccio -{G:.1f}deg, mateixa mida")
    print(f"  PIXEL SENSOR -> direccio -{G:.1f}deg, mida x{F:.3f}")
    print("=" * 74)
    Ms = E["SONY"]["M"] / np.nanmedian(E["SONY"]["M"], axis=1, keepdims=True)
    lams, angs = E["SONY"]["lams"], E["SONY"]["angs"]
    def llegeix(lam, ang):
        i = int(np.argmin(np.abs(np.log(lams / lam))))
        j = int(np.argmin([dang(a, ang) for a in angs]))
        return float(np.nanmax(Ms[max(i-1,0):i+2, max(j-2,0):j+3]))
    print(f"\n{'pic de la Vixen':>26s} | {'CEL':>9s} {'SENSOR':>9s} {'PIXEL':>9s}   qui guanya")
    for lam, ang in E["VIXEN"]["pics"]:
        c = llegeix(lam, ang)
        se = llegeix(lam, (ang - G) % 180.0)
        px = llegeix(lam * F, (ang - G) % 180.0)
        # argmax amb un nan retorna el nan: cal treure'ls abans de decidir
        noms = ["CEL", "SENSOR", "PIXEL"]; vals = [c, se, px]
        bo = [(v, n) for v, n in zip(vals, noms) if np.isfinite(v)]
        if not bo:
            print(f"  lam {lam:6.1f} px  {ang:5.1f}deg |  (sense dada als tres llocs)")
            continue
        bo.sort(reverse=True)
        g = bo[0][1]
        marge = bo[0][0] / max(bo[1][0] if len(bo) > 1 else 1e-9, 1e-9)
        print(f"  lam {lam:6.1f} px  {ang:5.1f}deg | {c:9.2f} {se:9.2f} {px:9.2f}   "
              f"{g} (x{marge:.2f} sobre el segon)")
    print("\n(els numeros son l'exces de potencia sobre la mediana de la seva mida;"
          "\n un pic de veritat val >3 i el fons val ~1)")
    np.savez(os.path.join(os.path.dirname(os.path.abspath(__file__)), "estriat.npz"),
             **{f"M_{t}": E[t]["M"] for t in E}, lams=E["VIXEN"]["lams"],
             angs=E["VIXEN"]["angs"])
