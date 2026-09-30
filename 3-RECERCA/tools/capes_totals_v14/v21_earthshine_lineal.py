"""V21b: l'earthshine DE VERITAT — el disc lunar en LINEAL, vel restat.

El disc que ha sortit a la V21 és pla: és el VEL de llum escampada de la
corona per l'òptica, i l'earthshine (les maria) hi queda enterrat i després
la corba de render (0,17/dècada) l'acaba d'aplanar. Aquí:

1. Recomponc l'apilat registrat a la Lluna en LINEAL (mateixes àncores).
2. Ajusto el VEL com a superfície suau (polinomi 2D de grau 3 per canal,
   només dins del disc) i el resto: el residu és l'estructura de la
   superfície lunar il·luminada per la Terra (maria/terres altes).
3. Mesuro l'amplitud del residu (¿quant earthshine hi ha sobre el vel?) i
   en faig una vista estirada (diagnòstic) i el contingut de la capa nova.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
sys.path.insert(0, AQUI)
import fes_v15 as F15
import fes_v17 as F17
import v21_apilats as VA


def main():
    sv = F17.SV16()
    geo15 = F15.Geo(padx=3387.0, pady=5109.0)
    comu, f2, run, ctx, S13, K, va = F15.carrega_sony()
    fits = VA.carrega_fits()
    meta = json.load(open(os.path.join(CAU, "apilats_meta.json")))
    ya, yb = meta["banda_lluna"]
    mx16, my16 = meta["lluna_base_canvas"]
    Rl = meta["rl_canvas"]
    W = sv.W16

    C, den = VA.compon(sv, geo15, comu, f2, ctx, S13, K, fits, "lluna",
                       y0y1=(ya, yb))
    tres = np.ones(C["G"].shape, bool)
    for c in comu.CANALS:
        tres &= (den[c] > 0) & np.isfinite(C[c])
    h = C["G"].shape[0]
    yy = np.arange(h, dtype=np.float32)[:, None] + ya
    xx = np.arange(W, dtype=np.float32)[None, :]
    dl = np.hypot(xx - mx16, yy - my16)
    disc = (dl < Rl - 12) & tres
    print(f"disc: {int(disc.sum())} px", flush=True)

    # el vel: polinomi 2D de grau 3 per canal, ajustat NOMÉS dins del disc
    u = np.broadcast_to((xx - mx16) / Rl, (h, W)).astype(np.float32)
    v = np.broadcast_to((yy - my16) / Rl, (h, W)).astype(np.float32)
    def base_pol(uu, vv):
        cols = []
        for i in range(4):
            for j in range(4 - i):
                cols.append((uu ** i) * (vv ** j))
        return np.stack(cols, axis=-1)
    Bm = base_pol(u[disc], v[disc])
    residus = {}
    vels = {}
    for c in comu.CANALS:
        val = C[c][disc].astype(np.float64)
        coef, *_ = np.linalg.lstsq(Bm, val, rcond=None)
        vel = (base_pol(u, v) @ coef).astype(np.float32)
        res = np.where(disc, C[c] - vel, 0.0).astype(np.float32)
        vels[c] = vel
        residus[c] = res
        amp = np.percentile(res[disc], [1, 50, 99])
        nivell = float(np.median(vel[disc]))
        print(f"canal {c}: vel mediana {nivell:.5g} · residu p1/p50/p99 = "
              f"{amp[0]:.4g} / {amp[1]:.4g} / {amp[2]:.4g} · "
              f"amplitud/vel = {(amp[2]-amp[0])/max(nivell,1e-12)*100:.2f} %",
              flush=True)

    # estructura del residu G: mapa suavitzat una mica (les maria són amples)
    resG = cv2.GaussianBlur(residus["G"], (0, 0), 4.0)
    s = np.percentile(np.abs(resG[disc]), 98)
    print(f"escala d'estirament (p98 |residu G suau|): {s:.5g}", flush=True)

    np.save(os.path.join(CAU, "earthshine_lineal_residus.npy"),
            np.dstack([residus[c] for c in comu.CANALS]))
    np.save(os.path.join(CAU, "earthshine_lineal_vels.npy"),
            np.dstack([vels[c] for c in comu.CANALS]))
    np.save(os.path.join(CAU, "earthshine_lineal_disc.npy"), disc)
    json.dump({"banda": [int(ya), int(yb)], "escala_p98_G": float(s)},
              open(os.path.join(CAU, "earthshine_lineal_meta.json"), "w"))

    # vista diagnòstica al LLENÇ SENCER: el residu estirat ±p98 → [0,1]
    H16 = sv.H16
    vista = np.zeros(((H16 + 3) // 4, (W + 3) // 4), np.float32) + 0.5
    resq = resG[::4, ::4]
    discq = disc[::4, ::4]
    fila0 = ya // 4
    sub = vista[fila0:fila0 + resq.shape[0], :resq.shape[1]]
    m2 = discq[:sub.shape[0], :sub.shape[1]]
    sub[m2] = np.clip(resq[:sub.shape[0], :sub.shape[1]][m2] / (2 * s) + 0.5, 0, 1)
    cv2.imwrite(os.path.join(CAU, "vista_earthshine_residu_llenc.png"),
                (vista * 255).astype(np.uint8))
    print("vista al cau: vista_earthshine_residu_llenc.png", flush=True)


if __name__ == "__main__":
    main()
