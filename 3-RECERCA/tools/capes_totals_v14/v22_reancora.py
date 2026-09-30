"""V22 · re-ancoratge de les capes lunars al DISC DEL MUNTATGE.

Pere (31-08, vespre): «sobra un espai enorme al limbe dret; agafa com a
referència les capes 11 i 12». Mesurat: el disc de les seves capes (les
perles de C2) és a (6481,8 · 6758,8), R=453,5 px — el meu ancoratge era el
centre lunar del fotograma base (t=70 s), (+16,4, +6,2) px enllà i un 0,45 %
més gran. La Lluna es mou entre C2 i t=70: l'espai blau era exactament això.

Cura: les tres tessel·les (earthshine, DSC06987, LROC) i la màscara es
reescalen ×0,9956 i es re-ancoren al centre mesurat de les capes 11+12.
La validació científica (marc lunar intern) no es toca: això és l'ancoratge
de DISPLAY al muntatge.
"""
from __future__ import annotations
import json, math, os
import numpy as np, cv2

CAU = "cau_v21"
MB_VELL = (6465.398680355321, 6752.632845814709)
POS_VELLA = (6257, 5969)                     # (y0, x0) de la tessel·la
CX_NOU, CY_NOU = 6481.8, 6758.8              # el disc de les capes 11+12
S = 453.5 / 455.5018189723177                # escala limbe muntatge / meu


def transforma(A, cxt, cyt, cxn, cyn, s, interp=cv2.INTER_LINEAR):
    H, W = A.shape[:2]
    xx, yy = np.meshgrid(np.arange(W, dtype=np.float32),
                         np.arange(H, dtype=np.float32))
    mx = (cxt + (xx - cxn) / s).astype(np.float32)
    my = (cyt + (yy - cyn) / s).astype(np.float32)
    return cv2.remap(A, mx, my, interp, borderValue=0)


def main():
    left_nou = int(round(CX_NOU)) - 496      # centre de tessel·la ~ (496, 496)
    top_nou = int(round(CY_NOU)) - 496
    cxn = CX_NOU - left_nou; cyn = CY_NOU - top_nou
    cxt = MB_VELL[0] - POS_VELLA[1]; cyt = MB_VELL[1] - POS_VELLA[0]
    print(f"tessel·la: centre vell ({cxt:.2f},{cyt:.2f}) → nou ({cxn:.2f},{cyn:.2f}) "
          f"a (top,left)=({top_nou},{left_nou}) · escala {S:.4f}")
    for nom in ("capa_nat_px", "capa_6987_px", "capa_lroc_px"):
        A = np.load(f"{CAU}/{nom}.npy")
        out = transforma(A, cxt, cyt, cxn, cyn, S)
        np.save(f"{CAU}/{nom}.npy", out)
        print(f"  {nom}: transformada")
    M = np.load(f"{CAU}/capa_nat_msk.npy")
    np.save(f"{CAU}/capa_nat_msk.npy",
            transforma(M, cxt, cyt, cxn, cyn, S))
    meta = json.load(open(f"{CAU}/capa_nat_meta.json"))
    meta["pos"] = [top_nou, left_nou]
    meta["reancoratge"] = {"centre_llenc": [CX_NOU, CY_NOU],
                           "radi_px": 453.5, "escala": S,
                           "referencia": "limbe mesurat capes 11+12 de Pere "
                                         "(rms 0,8-1,1 px)"}
    json.dump(meta, open(f"{CAU}/capa_nat_meta.json", "w"), indent=1)
    print("meta actualitzat")


if __name__ == "__main__":
    main()
