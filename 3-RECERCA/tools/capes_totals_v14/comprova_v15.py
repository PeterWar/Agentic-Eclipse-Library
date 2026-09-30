"""Portes de la V15, totes sobre el fitxer escrit.

A · fidelitat   les 12 capes de la V14 (amb l'edició de Pere) van BYTE A BYTE
                dins de la V15: tots els canals (píxels, transparència i
                màscara) idèntics, rectangles = original + pad, noms/opacitat/
                visibilitat iguals; i la capa Sony és a BAIX de tot.
B · alineació   el residual Sony↔V14 mesurat al construir (rebut) ≤ 0,35 px.
C · llenç       el llenç conté la V14 sencera (pad ≥ 0) i tota la dada Sony
                (la màscara de la capa nova no toca cap vora del llenç).
D · obrible     psd-tools i ImageIO (sips) llegeixen el PSB.
E · Photoshop   ⛔ LA PORTA DEFINITIVA: l'obre el Photoshop DE VERITAT
                (porta_photoshop.sh, ExtendScript sense diàlegs). Lliçó del
                28-08: psd-tools + sips + ImageMagick van donar per bo un PSB
                que Photoshop refusava (signatures 8BIM/8B64 dels blocs
                globals). Si Photoshop no hi és, la porta queda NO EXECUTADA
                i el fitxer NO es pot declarar lliurable.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v15")
import fes_v15 as F


def porta(nom, ok, detall):
    print(f"  {nom}: {'PASSA' if ok else '⛔ FALLA'} — {detall}")
    return ok


def main():
    from psd_tools import PSDImage
    rebut = json.load(open(os.path.join(CAU, "rebut_v15.json")))
    padx, pady = rebut["pad"]
    W, H = rebut["llenc"]
    tot_ok = True

    a = PSDImage.open(F.V14)
    b = PSDImage.open(F.DST)
    la, lb = list(a), list(b)

    # ---- A
    print("[A] fidelitat")
    ok = len(lb) == 13 and lb[0].name.startswith("13_8s_DSC06987")
    detalls = [] if ok else ["la capa Sony no és a baix de tot"]
    for x, y in zip(la, lb[1:]):
        num = x.name.split("_")[0]
        if x.name != y.name or x.visible != y.visible or x.opacity != y.opacity:
            ok = False; detalls.append(f"{num}: metadades")
        rx, ry = x._record, y._record
        if not (ry.top == rx.top + pady and ry.left == rx.left + padx
                and ry.bottom == rx.bottom + pady and ry.right == rx.right + padx):
            ok = False; detalls.append(f"{num}: rect de capa")
        if not (ry.mask_data.top == rx.mask_data.top + pady
                and ry.mask_data.left == rx.mask_data.left + padx):
            ok = False; detalls.append(f"{num}: rect de màscara")
        for j in range(len(rx.channel_info)):
            ha = hashlib.sha256(x._channels[j].data).hexdigest()
            hb = hashlib.sha256(y._channels[j].data).hexdigest()
            if ha != hb:
                ok = False
                detalls.append(f"{num}: canal {int(rx.channel_info[j].id)}")
    tot_ok &= porta("A", ok, "; ".join(detalls) if detalls else
                    "13 capes; les 12 de la V14 byte a byte amb rect = original+pad; "
                    "la Sony a baix de tot")

    # ---- B
    res = rebut["residual_v14_px"]
    d = max(abs(res[0]), abs(res[1]))
    tot_ok &= porta("B", d <= 0.35,
                    f"residual Sony↔V14 ({res[0]:+.2f}, {res[1]:+.2f}) px "
                    f"(correcció aplicada {rebut['correccio_raw_sony_px']})")

    # ---- C
    ok = padx >= 0 and pady >= 0 and W > 7648 + padx and H > 5353 + pady
    sony = lb[0]
    x0, y0, x1, y1 = sony.bbox
    m = sony.mask
    detall = (f"llenç {W}×{H}, pad ({padx}, {pady}); capa Sony bbox "
              f"({x0}, {y0})-({x1}, {y1})")
    tot_ok &= porta("C", ok, detall)

    # ---- D
    r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", F.DST],
                       capture_output=True, text=True)
    txt = r.stdout + r.stderr
    okD = f"pixelWidth: {W}" in txt and f"pixelHeight: {H}" in txt
    tot_ok &= porta("D", okD, "psd-tools i ImageIO llegeixen el PSB "
                    f"({os.path.getsize(F.DST)/1e9:.2f} GB, versió "
                    f"{b._record.header.version})")

    # ---- E · el Photoshop de veritat
    r = subprocess.run([os.path.join(AQUI, "porta_photoshop.sh"), F.DST],
                       capture_output=True, text=True, timeout=600)
    resp = (r.stdout + r.stderr).strip()
    tot_ok &= porta("E", resp.startswith("OBRE"), f"Photoshop diu: «{resp}»")

    print("\nVEREDICTE:", "TOTES LES PORTES PASSEN" if tot_ok else "⛔ HI HA FALLES")
    json.dump({"passa": bool(tot_ok)},
              open(os.path.join(CAU, "portes_v15.json"), "w"))
    return tot_ok


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
