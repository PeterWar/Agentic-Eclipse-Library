#!/usr/bin/env python3
"""La capa de protuberàncies: amb els DOS contactes i amb NOMÉS C2.

⏭️ Decisió de Pere del 27-08: «no m'agrada el resultat de posar C2 i C3 i
deformar la Lluna». El motiu és geomètric: el llenç va centrat al **Sol** i la
Lluna hi llisca ~28,5 px entre C2 i C3, o sigui que unir els dos extrems deixa
com a negre la **intersecció dels dos discos**, que és una llentia i no un
cercle.

Vista: la capa sencera dels dos runs, un al costat de l'altre. ⛔ Llenç sencer.
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image, ImageDraw

import comu

SORTIDA = os.path.join(comu.OUTPUT, "DOS_TRENS")


def capa(run_dir, K=8):
    """La vista si hi és; si no, es reconstrueix del `.npy` del run.

    Els runs vells no desaven `PROTUBERANCIES_capa_x8.png`, però sí la capa
    sencera: així la comparació no depèn de quines vistes s'escrivien aquell dia.
    """
    p = os.path.join(run_dir, "lliurables", "vistes", "PROTUBERANCIES_capa_x8.png")
    if os.path.exists(p):
        return Image.open(p).convert("RGB")
    f = os.path.join(run_dir, "3-filtres", "PROTUBERANCIES_rgb.npy")
    if not os.path.exists(f):
        return None
    a = np.load(f)
    if a.dtype != np.uint8:
        a = np.clip(a * 255.0, 0, 255).astype(np.uint8)
    im = Image.fromarray(a)
    return im.resize((im.width // K, im.height // K), Image.LANCZOS)


if __name__ == "__main__":
    tren = (sys.argv[1] if len(sys.argv) > 1 else "SONYTOT").upper()
    rs = comu.runs_llista(tren, "CIENCIA")
    ims = [(os.path.basename(d), capa(d)) for d in rs]
    ims = [(n, im) for n, im in ims if im is not None][-2:]
    if len(ims) < 2:
        raise SystemExit("calen dos runs amb la vista de protuberàncies")
    w, h = ims[0][1].size
    TOP = 34
    tela = Image.new("RGB", (w * 2 + 12, h + TOP), (18, 18, 18))
    dr = ImageDraw.Draw(tela)
    ET = ["C2 + C3  ·  la Lluna és la INTERSECCIÓ dels dos discos",
          "NOMÉS C2  ·  la Lluna torna a ser rodona"]
    for i, ((n, im), et) in enumerate(zip(ims, ET)):
        tela.paste(im, (i * (w + 12), TOP))
        dr.text((i * (w + 12) + 4, 6), f"{n[:3]}  ·  {et}",
                fill=(255, 220, 120) if i == 0 else (150, 255, 150))
    os.makedirs(SORTIDA, exist_ok=True)
    p = os.path.join(SORTIDA, f"PROTUBERANCIES_C2_contra_C2C3_{tren}.png")
    tela.save(p)
    print(f"desat a {p}\n  {ims[0][0]}  →  {ims[1][0]}")
