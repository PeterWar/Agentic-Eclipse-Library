"""Vistes de diagnòstic de la V14. Sempre el LLENÇ SENCER, mai un retall.

⏭️ Pere troba els artefactes mirant, no llegint codi: cada etapa ha de deixar
una vista. Aquí n'hi ha dues que no es poden deduir del compost:

- **quina capa mana a cada píxel** — no és «la de dalt amb màscara oberta»
  sinó la de **pes efectiu** més gran: amb fusió Normal, el pes real d'una capa
  és la seva màscara pel que deixen passar totes les de sobre,
  `w_i = a_i · Π_{j>i} (1 − a_j)`. ⛔ Amb la regla ingènua («la de més amunt
  amb màscara > 0,5») quatre capes de la V13 no manen mai en lloc: les seves
  màscares no arriben a 0,5 enlloc, i tot i així contribueixen;
- **el perfil radial del nivell**, que és on es llegeix el defecte de la V13
  (el seu màxim cau a 2 R☉, o sigui que la corona interior hi és més fosca que
  la mitjana) i on es mesura l'ondulació de les fronteres.
"""
from __future__ import annotations
import json, os, sys
import numpy as np
import cv2
from psd_tools import PSDImage

DEST = ("/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals")

# color per capa, de la curta (calenta) a la llarga (freda)
PALETA = [(255,255,255),(120,120,255),(90,170,255),(70,220,255),(90,255,200),
          (120,255,120),(200,255,90),(255,230,80),(255,170,70),(255,110,90),
          (230,90,160),(180,90,230)]

def main():
    dest = sys.argv[1] if len(sys.argv) > 1 else DEST
    V = os.path.join(dest, "CapesTotalsV14_vistes")
    psd = PSDImage.open(os.path.join(dest, "CapesTotalsV14.psd"))
    W, H = psd.width, psd.height
    capes = list(psd)                      # de BAIX a DALT
    pes = np.zeros((H, W), np.float32)     # el millor pes efectiu vist fins ara
    mana = np.zeros((H, W), np.int16) - 1
    resta = np.ones((H, W), np.float32)    # el que deixen passar les de SOBRE
    for i in range(len(capes) - 1, -1, -1):   # de DALT a BAIX
        l = capes[i]
        if not l.visible:
            continue
        a = np.squeeze(np.asarray(l.mask.topil()))
        a = a.astype(np.float32) / (65535.0 if a.dtype == np.uint16 else 255.0)
        a *= (l.opacity / 255.0)
        # ⏭️ una capa en ACLARIR no tapa: guanya allà on és més clara. Aquí es
        #    compta com que mana on té màscara, que al limbe és on de fet mana.
        w = a * resta
        millor = w > pes
        mana = np.where(millor, np.int16(i), mana)
        pes = np.where(millor, w, pes)
        resta *= (1.0 - a)
        del a, w, millor
    mana = np.where(pes > 0.02, mana, np.int16(-1))
    vis = np.zeros((H, W, 3), np.uint8)
    for i in range(len(capes)):
        c = PALETA[i % len(PALETA)]
        vis[mana == i] = (c[2], c[1], c[0])
    peu = 34 * (len(capes) + 1)
    out = np.zeros((H // 8 + peu, W // 8, 3), np.uint8)
    out[:H // 8] = vis[::8, ::8]
    for i, l in enumerate(capes):
        c = PALETA[i % len(PALETA)]
        y = H // 8 + 26 + 34 * i
        cv2.rectangle(out, (14, y - 18), (52, y + 4), (c[2], c[1], c[0]), -1)
        txt = (l.name if l.visible else l.name + "   [APAGADA]").replace("R☉", "Rsol")
        if str(l.blend_mode).endswith("LIGHTEN"):
            txt += "  (ACLARIR)"
        cv2.putText(out, txt, (66, y), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (235, 235, 235), 1,
                    cv2.LINE_AA)
    cv2.putText(out, "sense capa (fora de la dada)", (66, H // 8 + 26 + 34 * len(capes)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.62, (110, 110, 110), 1, cv2.LINE_AA)
    cv2.imwrite(os.path.join(V, "V14_quina_capa_mana.png"), out)
    cob = {capes[i].name: float(100 * (mana == i).mean()) for i in range(len(capes))}
    cob["(cap)"] = float(100 * (mana < 0).mean())
    json.dump(cob, open(os.path.join(V, "V14_quina_capa_mana.json"), "w"),
              indent=1, ensure_ascii=False)
    print("  quina capa mana:")
    for k, v in cob.items():
        print(f"    {v:6.2f} %  {k}")

    # ---- perfil radial ----
    P = json.load(open(os.path.join(V, "PORTES_V14.json")))
    r = np.array(P["perfil"]["r_Rsol"]); p = np.array(P["perfil"]["nivell"])
    Wp, Hp = 1500, 900
    g = np.full((Hp, Wp, 3), 22, np.uint8)
    lo, hi = np.log10(1.0), np.log10(9.0)
    def X(rr): return int(80 + (np.log10(rr) - lo) / (hi - lo) * (Wp - 130))
    def Y(vv): return int(Hp - 70 - vv * (Hp - 120))
    for gx in (1, 1.5, 2, 3, 4, 5, 6, 8):
        cv2.line(g, (X(gx), 40), (X(gx), Hp - 70), (52, 52, 52), 1)
        cv2.putText(g, f"{gx:g}", (X(gx) - 8, Hp - 44), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (150, 150, 150), 1, cv2.LINE_AA)
    for gy in np.arange(0, 1.01, 0.1):
        cv2.line(g, (80, Y(gy)), (Wp - 50, Y(gy)), (52, 52, 52), 1)
        cv2.putText(g, f"{gy:.1f}".replace(".", ","), (24, Y(gy) + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1, cv2.LINE_AA)
    pts = np.array([[X(a), Y(b)] for a, b in zip(r, p) if np.isfinite(b)], np.int32)
    cv2.polylines(g, [pts], False, (120, 230, 255), 2, cv2.LINE_AA)
    # la V13, de research/108 §3
    v13 = [(1.09, 0.518), (1.62, 0.689), (2.15, 0.719), (2.68, 0.640),
           (3.74, 0.484), (5.33, 0.429)]
    q = np.array([[X(a), Y(b)] for a, b in v13], np.int32)
    cv2.polylines(g, [q], False, (120, 120, 255), 2, cv2.LINE_AA)
    for a, b in v13:
        cv2.circle(g, (X(a), Y(b)), 4, (120, 120, 255), -1, cv2.LINE_AA)
    mq = [(1.09, 0.631), (1.62, 0.510), (2.15, 0.404), (2.68, 0.297),
          (3.74, 0.212), (5.33, 0.175), (8.51, 0.133)]
    q2 = np.array([[X(a), Y(b)] for a, b in mq], np.int32)
    cv2.polylines(g, [q2], False, (140, 255, 150), 1, cv2.LINE_AA)
    cv2.putText(g, "nivell mostrat contra r (Rsol)", (80, 32), cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (235, 235, 235), 1, cv2.LINE_AA)
    for i, (txt, col) in enumerate([("V14 (aquest fitxer)", (120, 230, 255)),
                                    ("V13 (research/108)", (120, 120, 255)),
                                    ("maqueta de Pere (research/108)", (140, 255, 150))]):
        cv2.line(g, (Wp - 430, 60 + 28 * i), (Wp - 390, 60 + 28 * i), col, 2)
        cv2.putText(g, txt, (Wp - 380, 65 + 28 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (215, 215, 215), 1, cv2.LINE_AA)
    cv2.imwrite(os.path.join(V, "V14_perfil_radial.png"), g)
    print("  perfil radial desat")

    # ⏭️ El llenç SENCER a x2, no un retall: a x8 la Lluna fa 114 px i no s'hi pot
    #    jutjar el limbe; a x2 en fa 455. La norma de Pere és que cap sortida
    #    visual no pot ser un retall, i això no ho és: hi són les quatre vores.
    a = np.asarray(psd.numpy())[..., :3]
    cv2.imwrite(os.path.join(V, "V14_compost_x2.png"),
                (np.clip(a, 0, 1) * 255).astype(np.uint8)[::2, ::2][..., ::-1])
    print("  llenç sencer a x2 desat")

if __name__ == "__main__":
    main()
