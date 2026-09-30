#!/usr/bin/env python3
"""Els filtres del detall, un per un i al LLENÇ SENCER.

⏭️ 27-08, per Pere: «vull centrar-me de moment amb el Vixen i anar filtre a
filtre per donar-te una sèrie de normes de com fer els filtres». Per parlar-ne
un per un, primer s'han de poder mirar un per un: mateix llenç, mateixa escala
de to i el mateix retall de percentils a tots, perquè comparar-los no depengui
de com s'han pintat.

    python3 vistes_filtres.py [VIXEN] [K]

⛔ Llenç sencer, mai un retall.
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image, ImageDraw

import comu

K = 6
FILTRES = [("PASSA_ALT", "passa-alt · log(camp aplanat) − gaussiana σ 24 px"),
           ("RADIAL", "radial · en coordenades polars, σ 10 px NOMÉS en radi"),
           ("NRGF", "NRGF · (dada − mitjana de l'anell) / σ de l'anell"),
           ("MGN", "MGN · cinc escales (σ 6·12·24·48·96) i arctan(3·d/σ)")]


def gris(a, m, p=99.5):
    v = np.where(m, a, np.nan)
    hi = float(np.nanpercentile(np.abs(v), p))
    g = np.clip(0.5 + 0.5 * np.nan_to_num(v) / max(hi, 1e-12), 0, 1)
    g = (g * 255).astype(np.uint8)
    out = np.dstack([g] * 3)
    out[~m] = (28, 12, 34)
    return out, hi


if __name__ == "__main__":
    tren = (sys.argv[1] if len(sys.argv) > 1 else "VIXEN").upper()
    d = comu.darrer_run(tren)
    import json
    S = json.load(open(os.path.join(d, "4-rebuts", "F1.2_sol_llenc.json")))["llenc"]
    msk = np.load(os.path.join(d, "3-filtres", "MASCARA.npy"))
    print(f"{tren}: {os.path.basename(d)}\n")
    petita = lambda a: a[::K, ::K]
    m = petita(msk)
    h, w = m.shape
    TOP = 30
    tela = Image.new("RGB", (w * 2 + 10, (h + TOP) * 2 + 10), (18, 18, 18))
    dr = ImageDraw.Draw(tela)
    for i, (nom, desc) in enumerate(FILTRES):
        f = os.path.join(d, "3-filtres", f"DETALL_{nom}.npy")
        if not os.path.exists(f):
            print(f"  ⚠️ falta {nom}"); continue
        a = petita(np.load(f))
        im, hi = gris(a, m)
        x = (i % 2) * (w + 10); y = (i // 2) * (h + TOP + 10) + TOP
        tela.paste(Image.fromarray(im), (x, y))
        dr.text((x + 4, y - 22), f"{nom}   ·   {desc}", fill=(150, 255, 150))
        rms = float(np.std(a[m]))
        print(f"  {nom:10s} rms {rms:.4f} · p99,5 |·| {hi:.4f} · "
              f"{100*np.mean(np.abs(a[m]) > hi):.2f} % per damunt del retall")
    p = os.path.join(comu.OUTPUT, "DOS_TRENS", f"FILTRES_{tren}_x{K}.png")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tela.save(p)
    print(f"\ndesat a {p}\n  llenç sencer reduït ×{K} · lila = sense dada\n"
          f"  ⚠️ tots pintats amb el MATEIX criteri (±p99,5 de cadascun): "
          f"la forma es pot comparar, el nivell no")
