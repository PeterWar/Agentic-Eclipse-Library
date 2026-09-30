"""D'on surten els halos: on el PES fa un esglao, el SOROLL en fa un altre.

Amb pocs fotogrames cada exposicio entra de cop i la seva frontera es una
ISOFOTA. Un passa-alt no veu el nivell pero si veu el SOROLL, i alla on el
soroll canvia de cop hi dibuixa una vora. Aixo no es un filtre retallat a cap
circumferencia (la norma del rectangle es compleix): es la fusio HDR.
"""
from __future__ import annotations
import json, os, sys
import numpy as np
import cv2
from astropy.io import fits
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nucli as N

K = 6
SORTIDA = os.path.expanduser("~/Desktop/Eclipse determinista/2-OUTPUT/DOS_TRENS")


def carrega(tren):
    d = N.darrer_run(tren)
    P = fits.getdata(os.path.join(d, "2-ldic", "PES_G.fits")).astype(np.float32)
    A = np.load(os.path.join(d, "3-filtres", "DETALL_PASSA_ALT.npy"))
    m = np.load(os.path.join(d, "3-filtres", "MASCARA.npy"))
    LL = json.load(open(os.path.join(d, "4-rebuts", "F1.2_sol_llenc.json")))["llenc"]
    return P, A, m, LL, os.path.basename(d)


def color(a, m, lo, hi, cmap=None):
    v = np.clip((np.nan_to_num(a) - lo) / (hi - lo), 0, 1)
    g = (v * 255).astype(np.uint8)
    rgb = cv2.applyColorMap(g, cmap) if cmap is not None else np.repeat(g[..., None], 3, 2)
    if cmap is not None:
        rgb = rgb[..., ::-1].copy()
    rgb[~m] = np.array([110, 35, 130], np.uint8)
    return rgb


if __name__ == "__main__":
    files = []
    for tren in ("VIXEN", "SONY"):
        P, A, m, LL, nom = carrega(tren)
        H, W = P.shape; h, w = H // K, W // K
        sm = lambda a: cv2.resize(a.astype(np.float32), (w, h), interpolation=cv2.INTER_AREA)
        # SOROLL local del detall: rms en finestres de 3 px de la vista
        d = A.astype(np.float32)
        s2 = sm(d * d); s1 = sm(d)
        soroll = np.sqrt(np.maximum(s2 - s1 * s1, 0))
        pes = sm(P); mk = sm(m.astype(np.float32)) > 0.5
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        rad = np.hypot(yy - h / 2., xx - w / 2.) * K / LL["R_sol_px"]; del yy, xx
        mk &= (rad > 1.02) & (rad < 9.3)
        lp = np.where(pes > 0, np.log10(np.maximum(pes, 1e-6)), np.nan)
        # quantes fronteres hi ha: el gradient del log del pes
        gp = np.hypot(*np.gradient(np.nan_to_num(lp)))
        n_front = float(np.nanmean(gp[mk] > 0.02))
        print(f"{tren}: {nom} · pes de {np.nanmin(lp[mk]):.2f} a {np.nanmax(lp[mk]):.2f} "
              f"(log10) · {100*n_front:.2f} % de la imatge és FRONTERA de pes")
        files += [(f"{tren} · log10(pes)", color(lp, mk, -1.0, 1.6, cv2.COLORMAP_TURBO)),
                  (f"{tren} · soroll del passa-alt", color(np.log10(np.maximum(soroll, 1e-9)),
                                                          mk, -4.2, -2.6, cv2.COLORMAP_TURBO))]
    h, w = files[0][1].shape[:2]
    tela = np.full((h * 2 + 12, w * 2 + 12, 3), 20, np.uint8)
    for i, (_, im) in enumerate(files):
        r_, c_ = divmod(i, 2)
        tela[r_ * (h + 12):r_ * (h + 12) + h, c_ * (w + 12):c_ * (w + 12) + w] = im
    p = os.path.join(SORTIDA, f"HALOS_pes_i_soroll_x{K}.png")
    Image.fromarray(tela).save(p)
    print(f"\n{p}")
    print("  dalt VIXEN, baix SONY · esquerra el PES, dreta el SOROLL del passa-alt")
    print("  si les vores del pes i les del soroll coincideixen, el halo és la fusió")
