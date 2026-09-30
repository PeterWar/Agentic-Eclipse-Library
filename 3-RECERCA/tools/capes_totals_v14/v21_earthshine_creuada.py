"""V21 · l'earthshine mesurat: la correlació CREUADA entre els dos trens.

La idea: registrats a la LLUNA, la superfície lunar és COMUNA als dos trens;
el vel de llum escampada de la corona és de cada instrument (òptiques i
apuntaments diferents) i el gra és independent. Per tant, la component
comuna dins del disc és senyal lunar de veritat i no cal creure's cap model.

Control nul aparellat: la mateixa correlació amb el residu del Vixen GIRAT
al voltant del centre de la Lluna (90°, 180°, 270°) — mateix radi, mateixa
estadística, cap coincidència possible amb la superfície.
"""
from __future__ import annotations
import json, os
import numpy as np, cv2

CAU = "cau_v21"
MB = (6465.398680355321, 6752.632845814709)
RL = 455.5018189723177


def carrega():
    S = np.load(f"{CAU}/lluna_sony_lineal.npy")
    V = np.load(f"{CAU}/lluna_vixen_lineal.npy")
    both = np.load(f"{CAU}/lluna_both.npy")
    m = json.load(open(f"{CAU}/lluna_sony_meta.json"))
    x0, y0, x1, y1 = m["bbox_canvas"]
    yy = np.arange(y0, y1, dtype=np.float32)[:, None]
    xx = np.arange(x0, x1, dtype=np.float32)[None, :]
    r = np.hypot(xx - MB[0], yy - MB[1]) / RL
    return S, V, both, r, (x0, y0, x1, y1)


def treu_vel(A, m, r, grau=4):
    """El vel de corona: polinomi 2D suau dins del disc, per canal."""
    ys, xs = np.where(m)
    u = (xs - A.shape[1] / 2) / 500.0
    v = (ys - A.shape[0] / 2) / 500.0
    cols = [np.ones_like(u)]
    for d in range(1, grau + 1):
        for i in range(d + 1):
            cols.append(u ** (d - i) * v ** i)
    M = np.column_stack(cols)
    out = np.zeros_like(A)
    for ch in range(A.shape[2]):
        z = A[..., ch][m].astype(np.float64)
        c = np.linalg.lstsq(M, z, rcond=None)[0]
        f = np.zeros(A.shape[:2], np.float32)
        f[ys, xs] = M @ c
        out[..., ch] = np.where(m, A[..., ch] - f, 0)
    return out


def gira(A, m, k):
    return np.rot90(A, k), np.rot90(m, k)


def main():
    S, V, both, r, bb = carrega()
    par = json.load(open(f"{CAU}/lluna_parell.json"))
    g = np.array(par["guany_sony_vixen"], np.float32)
    Vg = V * g[None, None, :]                     # el Vixen a l'escala Sony
    dins = both & (r < 0.90)
    print(f"disc útil (r<0,90 R☾ i dada als dos trens): {int(dins.sum())} px")
    Sr = treu_vel(np.nan_to_num(S), dins, r)
    Vr = treu_vel(np.nan_to_num(Vg), dins, r)
    res = {}
    for sig in (0, 3, 6, 12, 25):
        a = Sr[..., 1].copy(); b = Vr[..., 1].copy()
        if sig:
            a = cv2.GaussianBlur(a, (0, 0), sig); b = cv2.GaussianBlur(b, (0, 0), sig)
        mm = cv2.erode(dins.astype(np.uint8), np.ones((2 * int(3 * sig) + 3,) * 2,
                                                      np.uint8)).astype(bool) if sig else dins
        x, y = a[mm], b[mm]
        rr = float(np.corrcoef(x, y)[0, 1])
        nul = []
        for k in (1, 2, 3):
            bb2, mb2 = gira(b, mm, k)
            m2 = mm & mb2
            nul.append(float(np.corrcoef(a[m2], bb2[m2])[0, 1]))
        res[sig] = (rr, nul)
        print(f"  suavitzat σ={sig:2d} px · n={int(mm.sum()):7d} · "
              f"r(Sony,Vixen) = {rr:+.4f} · control nul (gir 90/180/270°) = "
              + " ".join(f"{z:+.4f}" for z in nul))
    np.save(f"{CAU}/lluna_resid_sony.npy", Sr)
    np.save(f"{CAU}/lluna_resid_vixen.npy", Vr)
    np.save(f"{CAU}/lluna_dins.npy", dins)
    json.dump({str(k): {"r": v[0], "nul": v[1]} for k, v in res.items()},
              open(f"{CAU}/earthshine_creuada.json", "w"), indent=1)


if __name__ == "__main__":
    main()
