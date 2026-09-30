"""V21 · l'earthshine dels dos trens contra el mapa LROC de la NASA.

Cap paràmetre d'orientació no s'ajusta: la libració i el pol lunar surten de
l'efemèride i el nord del llenç, de les estrelles. L'escombrada d'angles és
NOMÉS el control nul: diu quant val la correlació quan el mapa NO hi encaixa.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np, cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
sys.path.insert(0, AQUI)
import v21_lroc as L

MB = (6465.398680355321, 6752.632845814709)
RL = 455.5018189723177


def neteja(A, m, rr, NB=180, grau=4):
    """el vel: perfil radial (mediana per anell) + polinomi 2D de grau 4."""
    out = np.zeros_like(A)
    b = np.clip((rr / 0.98 * NB).astype(int), 0, NB - 1)
    ys, xs = np.where(m)
    u = (xs - A.shape[1] / 2) / 500.0
    v = (ys - A.shape[0] / 2) / 500.0
    cols = [np.ones_like(u)]
    for d in range(1, grau + 1):
        for i in range(d + 1):
            cols.append(u ** (d - i) * v ** i)
    M = np.column_stack(cols)
    if A.ndim == 2:
        A = A[..., None]
        out = out[..., None] if out.ndim == 2 else out
        out = np.zeros_like(A)
    for ch in range(A.shape[2]):
        Z = A[..., ch].copy()
        prof = np.zeros(NB)
        for k in range(NB):
            s = m & (b == k)
            if s.sum() > 40:
                prof[k] = np.median(Z[s])
        Z = Z - prof[b]
        c = np.linalg.lstsq(M, Z[m].astype(np.float64), rcond=None)[0]
        f = np.zeros(A.shape[:2], np.float32); f[ys, xs] = M @ c
        out[..., ch] = np.where(m, Z - f, 0)
    return out.squeeze()


def main():
    geo = L.geometria_lunar(); ori = L.orientacio_del_llenc()
    Mp = L.mapa_gris()
    md = json.load(open(f"{CAU}/lluna_sony_meta.json"))
    x0, y0, x1, y1 = md["bbox_canvas"]
    forma = (y1 - y0, x1 - x0)
    centre = (MB[0] - x0, MB[1] - y0)
    yy = np.arange(y0, y1, dtype=np.float32)[:, None]
    xx = np.arange(x0, x1, dtype=np.float32)[None, :]
    rr = np.hypot(xx - MB[0], yy - MB[1]) / RL

    S = np.nan_to_num(np.load(f"{CAU}/lluna_sony_lineal.npy"))
    V = np.nan_to_num(np.load(f"{CAU}/lluna_vixen_lineal.npy"))
    par = json.load(open(f"{CAU}/lluna_parell.json"))
    V = V * np.array(par["guany_sony_vixen"], np.float32)[None, None, :]
    both = np.load(f"{CAU}/lluna_both.npy")
    dins = both & (rr < 0.90)

    # combinat dels DOS TRENS, pesat per la variància del gra de cada tren
    wS = 1.0 / max(np.var(neteja(S[..., 1], dins, rr)[dins]), 1e-9)
    wV = 1.0 / max(np.var(neteja(V[..., 1], dins, rr)[dins]), 1e-9)
    D = (S * wS + V * wV) / (wS + wV)
    print(f"pesos del combinat: Sony {wS/(wS+wV):.3f} · Vixen {wV/(wS+wV):.3f}")

    resid = {"sony": neteja(S, dins, rr), "vixen": neteja(V, dins, rr),
             "dos_trens": neteja(D, dins, rr)}
    np.save(f"{CAU}/earthshine_dos_trens_resid.npy", resid["dos_trens"])
    np.save(f"{CAU}/earthshine_dos_trens_lineal.npy", D)

    g0, disc = L.renderitza(Mp, geo, ori, forma, centre, RL, 0.0)
    Lr = neteja(g0.astype(np.float32), dins, rr)
    print(f"\nmapa LROC renderitzat · libració ({geo['libracio_lon']:+.2f}, "
          f"{geo['libracio_lat']:+.2f})° · PA pol {geo['pa_pol_lunar']:+.2f}°")

    print(f"\n{'tren':<11} {'σ':>3} {'r(LROC)':>9} {'control nul (gir)':>28} {'z':>6}")
    out = {}
    for nom in ("sony", "vixen", "dos_trens"):
        for sig in (4, 8, 16):
            a = cv2.GaussianBlur(resid[nom][..., 1], (0, 0), sig)
            b = cv2.GaussianBlur(Lr, (0, 0), sig)
            m = cv2.erode(dins.astype(np.uint8),
                          np.ones((2 * int(3 * sig) + 3,) * 2, np.uint8)).astype(bool)
            r0 = float(np.corrcoef(a[m], b[m])[0, 1])
            nul = []
            for ang in range(20, 360, 20):
                gk, _ = L.renderitza(Mp, geo, ori, forma, centre, RL, float(ang))
                bk = cv2.GaussianBlur(neteja(gk.astype(np.float32), dins, rr),
                                      (0, 0), sig)
                nul.append(float(np.corrcoef(a[m], bk[m])[0, 1]))
            nul = np.array(nul)
            z = (r0 - nul.mean()) / max(nul.std(), 1e-9)
            print(f"{nom:<11} {sig:>3} {r0:>+9.4f}   "
                  f"mitjana {nul.mean():+.4f} sd {nul.std():.4f} màx {nul.max():+.4f}"
                  f" {z:>6.1f}σ")
            out[f"{nom}_{sig}"] = {"r": r0, "nul_mitjana": float(nul.mean()),
                                   "nul_sd": float(nul.std()),
                                   "nul_max": float(nul.max()), "z": float(z),
                                   "nul": nul.tolist()}
    json.dump({"efemeride": geo, "orientacio": ori, "resultats": out,
               "pesos": {"sony": float(wS / (wS + wV)),
                         "vixen": float(wV / (wS + wV))}},
              open(f"{CAU}/earthshine_lroc.json", "w"), indent=1)


if __name__ == "__main__":
    main()
