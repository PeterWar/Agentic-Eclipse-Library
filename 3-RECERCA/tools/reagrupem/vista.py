#!/usr/bin/env python3
"""Vistes del llenç. ⛔ NORMA: SEMPRE el llenç sencer, mai un retall."""
from __future__ import annotations
import os, sys, numpy as np
from astropy.io import fits
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu  # noqa: E402


def redueix(a, k):
    h, w = a.shape
    a = a[:h//k*k, :w//k*k].reshape(h//k, k, w//k, k)
    return np.nanmean(a, axis=(1, 3))


def corba(x, rad, RS, pend=0.17, ancora=0.68, terra=0.045):
    """Corba de to DECLARADA (research/108), no derivada de percentils.

    y = ancora + pend * log10(v / v_ancora)

    - **pendent 0,17 per dècada** de B/B☉ (la maqueta de Pere; `estira_log`
      en feia 0,503 i cremava 1,67 dècades);
    - **àncora 0,68 a 1,05–1,15 R☉**, mediana de l'anell;
    - **terra 0,045**;
    - ⛔ el sostre surt del **màxim de la dada**, mai d'un percentil.
    """
    v = np.where(np.isfinite(x) & (x > 0), x, np.nan)
    anell = (rad >= 1.05*RS) & (rad <= 1.15*RS) & np.isfinite(v)
    va = np.nanmedian(v[anell])
    y = ancora + pend*np.log10(np.maximum(v, va*1e-9)/va)
    return np.clip(np.where(np.isfinite(y), y, terra), terra, 1.0)


def desa_png(rgb, ruta, titol=""):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    h, w = rgb.shape[:2]
    fig, ax = plt.subplots(figsize=(w/110, h/110 + 0.6), facecolor="#0b0b0b")
    ax.imshow(np.clip(rgb, 0, 1)); ax.set_xticks([]); ax.set_yticks([])
    if titol: ax.set_title(titol, color="#eeeeee", fontsize=13)
    fig.tight_layout(); fig.savefig(ruta, dpi=110, facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    red = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    C = {c: fits.getdata(os.path.join(comu.F2, f"LDIC_{c}.fits")).astype(np.float64)
         for c in ("R", "G", "B")}
    P = fits.getdata(os.path.join(comu.F2, "LDIC_pes_G.fits")).astype(np.float64)
    pass
    small = {c: redueix(C[c], red) for c in C}
    G = small["G"]
    print("G: finit", f"{100*np.isfinite(G).mean():.1f}%",
          "min", f"{np.nanmin(G):.4g}", "màx", f"{np.nanmax(G):.4g}",
          "mediana", f"{np.nanmedian(G):.4g}")
    H_, W_ = G.shape
    yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float64)
    rad = np.hypot(yy - H_/2.0, xx - W_/2.0)
    RS = 440.60/red
    print("  anella d'àncora 1,05-1,15 R☉ ->",
          f"{np.nanmedian(G[(rad>=1.05*RS)&(rad<=1.15*RS)]):.4g}")
    rgb = np.dstack([corba(small["R"], rad, RS), corba(small["G"], rad, RS),
                     corba(small["B"], rad, RS)])
    rgb = np.where(np.isfinite(rgb), rgb, 0.0)
    p = comu.vista(f"LDIC_llenc_sencer_x{red}.png")
    desa_png(rgb, p, f"LDIC · LLENÇ SENCER {C['G'].shape[1]}x{C['G'].shape[0]} "
                     f"(reduït {red}x) · corba de to declarada 0,17/dècada")
    print(p)
    pw = redueix(P, red); pw = pw/np.nanmax(pw)
    desa_png(np.dstack([pw, pw, pw]),
             comu.vista(f"LDIC_pes_x{red}.png"),
             "Mapa de PES (denominador) · llenç sencer")
    print(comu.vista(f"LDIC_pes_x{red}.png"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
