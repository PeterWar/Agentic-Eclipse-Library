"""Les quatre feines obertes del 27-08, en quatre panells que es poden mirar.

Un full amb el que decideix cada una: el flat mesurat pel dither i la seva
validacio fora de mostra, el blau descompost en camera / composicio / cel, la
deriva fotometrica entre trens abans i despres, i la familia fina canal a
canal. Els numeros son els de `research/116`.
"""
from __future__ import annotations

import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
SORTIDA = os.path.expanduser("~/Desktop/Eclipse determinista/2-OUTPUT/DOS_TRENS")
FLAT = os.path.join(AQUI, "..", "sony_entrada", "flat_dither.json")

# ---- mesures (research/116). Tot ve dels scripts d'aquesta carpeta.
ANELLS = ["1,05-1,30", "1,30-1,70", "1,80-2,20", "2,50-3,20"]
CRUS = [np.nan, -2.69, -3.57, np.nan]
LDIC = [-5.03, -5.06, -1.97, -2.52]
CORONA = [-6.09, -6.02, -5.32, -10.92]

RAD = [1.150, 1.255, 1.369, 1.494, 1.631, 1.780, 1.942, 2.119, 2.313, 2.524,
       2.754, 3.005, 3.279, 3.579, 3.905]
RHO_ABANS = [1.0549, 1.0278, 1.0273, 1.0328, 1.0298, 1.0269, 1.0231, 0.9951,
             0.9888, 0.9847, 0.9985, 1.0007, 0.9993, 0.9785, 0.9624]
RHO_DESPRES = [1.0462, 1.0178, 1.0203, 1.0299, 1.0159, 1.0194, 1.0130, 0.9900,
               0.9860, 0.9778, 0.9969, 0.9978, 1.0024, 0.9864, 0.9929]

CANALS = ["R", "G", "B"]
FINA_V = [7.49, 7.85, 6.57]
FINA_S = [6.13, 4.59, 5.53]


def main():
    os.makedirs(SORTIDA, exist_ok=True)
    fig, ax = plt.subplots(2, 2, figsize=(15.5, 10.5))
    fig.patch.set_facecolor("white")

    # ---------------------------------------------------------------- 1. flat
    d = json.load(open(FLAT))
    r = np.array(d["r_sensor_px"])
    a = ax[0, 0]
    for c, col in zip(("R", "G1", "B", "G2"), ("#c0392b", "#27ae60", "#2980b9", "#16a085")):
        a.plot(r, 100 * (np.exp(np.array(d["lnF"][c])) - 1), label=c, color=col, lw=2)
    a.axhline(0, color="k", lw=0.8)
    a.set_xlabel("radi al SENSOR (px)"); a.set_ylabel("error del flat (%)")
    a.set_title("1 · el flat de la Sony, mesurat pel salt de muntura\n"
                "amplitud 7,1-9,1 % · valida fora de mostra (100 % del guany esperat)",
                fontsize=11)
    a.legend(fontsize=9); a.grid(alpha=.3)

    # ---------------------------------------------------------------- 2. blau
    a = ax[0, 1]
    x = np.arange(len(ANELLS)); w = 0.26
    a.bar(x - w, CRUS, w, label="fotogrames CRUS (les càmeres)", color="#7f8c8d")
    a.bar(x, LDIC, w, label="+ composició LDIC", color="#e67e22")
    a.bar(x + w, CORONA, w, label="+ resta del cel", color="#2980b9")
    a.axhline(0, color="k", lw=0.8)
    a.set_xticks(x); a.set_xticklabels(ANELLS)
    a.set_xlabel("anell (R☉)"); a.set_ylabel("B/G de la Sony sobre la Vixen (%)")
    a.set_title("2 · el blau: ~3 punts són les càmeres,\nla resta la posa la cadena "
                "(i creix cap enfora amb el cel)", fontsize=11)
    a.legend(fontsize=9); a.grid(alpha=.3, axis="y")

    # ------------------------------------------------------------- 3. deriva
    a = ax[1, 0]
    a.semilogx(RAD, RHO_ABANS, "o-", color="#c0392b", label="flat de cel (13,51 %)")
    a.semilogx(RAD, RHO_DESPRES, "o-", color="#27ae60",
               label="flat corregit pel dither (7,43 %)")
    a.axhline(1.0, color="k", lw=0.8)
    a.set_xlabel("R☉"); a.set_ylabel("G Vixen / G Sony (normalitzat)")
    a.set_title("3 · la deriva fotomètrica entre trens\n"
                "el flat n'era la meitat; el que queda no és el nivell del cel",
                fontsize=11)
    a.legend(fontsize=9); a.grid(alpha=.3, which="both")
    a.set_xticks([1.2, 1.5, 2, 2.5, 3, 4]); a.set_xticklabels(["1,2", "1,5", "2", "2,5", "3", "4"])

    # -------------------------------------------------------------- 4. estriat
    a = ax[1, 1]
    x = np.arange(3); w = 0.35
    a.bar(x - w / 2, FINA_V, w, label="Vixen", color="#8e44ad")
    a.bar(x + w / 2, FINA_S, w, label="Sony", color="#f39c12")
    a.axhline(1.0, color="k", lw=0.8, ls="--")
    a.set_xticks(x); a.set_xticklabels(CANALS)
    a.set_ylabel("excés de la família fina (× sobre el fons de la seva λ)")
    a.set_title("4 · la família fina (λ 6-10 px) canal a canal\n"
                "el verd no destaca (G/(R,B) = 1,12): NO és la quincunx del Bayer",
                fontsize=11)
    a.legend(fontsize=9); a.grid(alpha=.3, axis="y")

    fig.suptitle("Les quatre feines obertes del 27 d'agost — research/116",
                 fontsize=14, y=0.985)
    fig.tight_layout(rect=[0, 0, 1, 0.965])
    p = os.path.join(SORTIDA, "QUATRE_DEUTES_27-08.png")
    fig.savefig(p, dpi=110)
    print("desat a", p)


if __name__ == "__main__":
    main()
