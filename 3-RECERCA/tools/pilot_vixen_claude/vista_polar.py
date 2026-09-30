"""⛔ L'ULL BO: la corona desenrotllada a coordenades polars.

## Per què això i no una altra vista

En coordenades cartesianes un **arc concèntric amb el Sol** i un **plomall
radial** se semblen prou perquè un s'hi equivoqui, i el 24-08-2026 m'hi vaig
equivocar quatre vegades. Desenrotllada a (azimut, log r) la confusió és
impossible:

| a l'espai | a la vista polar |
|---|---|
| arc concèntric amb el Sol | **ratlla HORITZONTAL** que travessa els 360° |
| costura de fusió (isofota) | ratlla horitzontal **ondulada**, que segueix la corona |
| plomall, nansa, estria radial | ratlla **VERTICAL** |
| gra i soroll | textura sense direcció |

I encara hi ha una segona cosa que la vista polar dona de franc: **el perfil
mitjà per columna** (la mitjana sobre azimut a cada radi) és exactament
l'estadístic de la porta H1, i **el perfil per fila** ensenya si l'artefacte és
local en azimut, que és el que la mediana global amagava.

⚠️ El mostreig és **log r**, no r: la corona interior és on hi ha el detall i on
totes les costures s'apilen, i amb r uniforme se'n perd la meitat.

Eina: `skimage.transform.warp_polar`. Sobre ella, matplotlib per als eixos, que
és el que permet llegir un radi directament de la imatge sense comptar píxels.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comu as C  # noqa: E402


def desenrotlla(d, w, r0, r1, n_r=900, n_a=1440):
    """(azimut, log r) → array (n_r, n_a). ⛔ mostreig uniforme en LOG r."""
    from scipy.ndimage import map_coordinates
    H, W = d.shape
    lr = np.linspace(np.log(r0), np.log(r1), n_r)
    az = np.linspace(0.0, 2.0 * np.pi, n_a, endpoint=False)
    R = np.exp(lr)[:, None] * C.R_SOL_PX
    A = az[None, :]
    yy = H / 2.0 - R * np.cos(A)
    xx = W / 2.0 + R * np.sin(A)
    v = map_coordinates(np.nan_to_num(d), [yy, xx], order=1, mode="constant", cval=0.0)
    m = map_coordinates(w.astype(np.float32), [yy, xx], order=1, mode="constant", cval=0.0)
    return np.where(m > 0.5, v, np.nan), np.exp(lr), np.degrees(az)


def desenrotlla_per_nivell(d, w, g, n_niv=700, n_a=1440, r0=1.09, r1=3.2):
    """(azimut, log NIVELL) → array. ⛔ **És la coordenada natural de les costures.**

    Una frontera de fusió HDR és una isofota per construcció —el pes d'un
    fotograma només depèn del seu valor cru—, o sigui que **al pla del nivell és
    una recta horitzontal**, per molt que serpentegi en radi. Igual que la vista
    polar separa els arcs concèntrics dels plomalls, aquesta separa les costures
    de la corona: el que surti horitzontal aquí és de la fusió.
    """
    from scipy.ndimage import map_coordinates
    H, W = d.shape
    az = np.linspace(0.0, 2.0 * np.pi, n_a, endpoint=False)
    n_r = 1600
    R = np.exp(np.linspace(np.log(r0), np.log(r1), n_r))[:, None] * C.R_SOL_PX
    A = az[None, :]
    yy = H / 2.0 - R * np.cos(A)
    xx = W / 2.0 + R * np.sin(A)
    V = map_coordinates(np.nan_to_num(d), [yy, xx], order=1, mode="constant", cval=0.0)
    M = map_coordinates(w.astype(np.float32), [yy, xx], order=1, mode="constant", cval=0.0)
    G = map_coordinates(np.nan_to_num(g), [yy, xx], order=1, mode="constant", cval=0.0)
    V = np.where(M > 0.5, V, np.nan)
    G = np.where((M > 0.5) & (G > 0), G, np.nan)
    lg = np.log(G)
    bo = np.isfinite(lg)
    lo, hi = np.nanpercentile(lg[bo], [0.5, 99.5])
    graella = np.linspace(hi, lo, n_niv)          # de brillant a fosc
    out = np.full((n_niv, n_a), np.nan)
    for j in range(n_a):
        c = lg[:, j]; v = V[:, j]
        k = np.isfinite(c) & np.isfinite(v)
        if k.sum() < 20:
            continue
        # el nivell baixa cap enfora: cal ordre creixent per a np.interp
        cc, vv = c[k][::-1], v[k][::-1]
        o = np.argsort(cc)
        out[:, j] = np.interp(graella, cc[o], vv[o], left=np.nan, right=np.nan)
    return out, np.exp(graella), np.degrees(az)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("detall", type=Path)
    ap.add_argument("-o", "--sortida", type=Path, required=True)
    ap.add_argument("--comp", type=Path, default=None)
    ap.add_argument("--sostre", type=float, default=None)
    ap.add_argument("--exposicions", type=float, nargs="+", default=None)
    ap.add_argument("--fb", type=float, default=None)
    ap.add_argument("--r0", type=float, default=1.09)
    ap.add_argument("--r1", type=float, default=3.0)
    ap.add_argument("--titol", default="")
    ap.add_argument("--eix", choices=["radi", "nivell"], default="radi")
    a = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d = np.load(a.detall / "DETALL_ln.npy")
    w = np.load(a.detall / "PES.npy")
    if a.eix == "nivell":
        g = np.load(a.comp, mmap_mode="r")
        g = np.asarray(g[..., 1] if g.ndim == 3 else g, np.float32)
        if a.fb:
            g = g / np.float32(a.fb)
        P, r, az = desenrotlla_per_nivell(d, w, g, r0=a.r0, r1=a.r1)
    else:
        P, r, az = desenrotlla(d, w, a.r0, a.r1)
    # ⛔ realçat per FILA (= per radi): si no, la corona interior satura la vista
    sd = np.nanstd(P, axis=1, keepdims=True)
    Q = P / np.maximum(sd, 1e-12)

    fig = plt.figure(figsize=(16, 9))
    gs = fig.add_gridspec(2, 2, width_ratios=[5, 1], height_ratios=[4, 1],
                          hspace=0.06, wspace=0.03)
    ax = fig.add_subplot(gs[0, 0])
    y0, y1 = np.log(r[0]), np.log(r[-1])
    ax.imshow(Q, origin="lower", aspect="auto", cmap="gray", vmin=-2.5, vmax=2.5,
              extent=[0, 360, y0, y1])
    if a.eix == "nivell":
        ax.set_ylabel("nivell del compost (ADU/s, log)")
        tics = [x for x in r[::max(len(r)//8, 1)]]
        ax.set_yticks(np.log(tics)); ax.set_yticklabels([f"{x:.0f}" for x in tics])
        cap = "HORITZONTAL = COSTURA DE FUSIÓ  ·  la corona no té motiu de ser horitzontal aquí"
    else:
        ax.set_ylabel("radi (R☉, escala log)")
        tics = [x for x in (1.1, 1.2, 1.3, 1.5, 1.7, 2.0, 2.5, 3.0) if a.r0 <= x <= a.r1]
        ax.set_yticks(np.log(tics)); ax.set_yticklabels([f"{x:g}" for x in tics])
        cap = "HORITZONTAL = arc concèntric  ·  VERTICAL = plomall radial"
    ax.set_xticklabels([])
    ax.set_title((a.titol or a.detall.name) + "  ·  " + cap, fontsize=11)

    # les fronteres de fusió, desenrotllades
    if a.eix == "radi" and a.comp and a.sostre and a.exposicions:
        g = np.load(a.comp, mmap_mode="r")
        g = np.asarray(g[..., 1] if g.ndim == 3 else g, np.float32)
        if a.fb:
            g = g / np.float32(a.fb)
        G, _, _ = desenrotlla(g, w, a.r0, a.r1)
        lr = np.linspace(np.log(a.r0), np.log(a.r1), G.shape[0])
        for t in sorted(a.exposicions):
            for niv, col in ((a.sostre / t, "#ff4040"), (0.2 * a.sostre / t, "#40c0ff")):
                y = []
                for j in range(G.shape[1]):
                    c = G[:, j]
                    k = np.flatnonzero(np.isfinite(c) & (c < niv))
                    y.append(lr[k[0]] if k.size and k[0] > 0 else np.nan)
                y = np.array(y)
                if np.isfinite(y).sum() > 100:
                    ax.plot(az, y, color=col, lw=0.7, alpha=0.85)

    # perfil per RADI: l'estadístic de la porta H1, dibuixat
    axr = fig.add_subplot(gs[0, 1], sharey=ax)
    axr.plot(100 * np.nanmedian(P, axis=1), np.log(r), color="#b1552b", lw=1.0)
    if a.eix == "nivell" and a.sostre and a.exposicions:
        for t in sorted(a.exposicions):
            for niv, col in ((a.sostre/t, "#ff4040"), (0.2*a.sostre/t, "#40c0ff")):
                if r.min() < niv < r.max():
                    ax.axhline(np.log(niv), color=col, lw=0.6, alpha=0.8)
                    axr.axhline(np.log(niv), color=col, lw=0.6, alpha=0.5)
    axr.axvline(0, color="0.7", lw=0.8, ls="--")
    axr.set_xlabel("mediana\nazimutal (%)", fontsize=8)
    axr.tick_params(labelleft=False, labelsize=8)
    axr.grid(alpha=0.25)

    # perfil per AZIMUT: si l'artefacte és local, aquí es veu
    axa = fig.add_subplot(gs[1, 0], sharex=ax)
    axa.plot(az, 100 * np.nanstd(P, axis=0), color="#2b6cb1", lw=0.9)
    axa.set_xlabel("azimut (graus, 0 = amunt a la imatge, cap a l'est)")
    axa.set_ylabel("rms (%)", fontsize=9)
    axa.set_xlim(0, 360); axa.grid(alpha=0.25)
    a.sortida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.sortida, dpi=130, bbox_inches="tight")
    print(f"→ {a.sortida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
