"""V21 · EARTHSHINE DELS DOS TRENS: el producte i la seva validació.

Entrada: els 8 fotogrames que Pere va demanar —Sony >1 s (2s×3 + 8s×2) i
Vixen >9 s (10 s×3)— apilats al MATEIX marc lunar, amb el moviment de la
Lluna i de cada muntura resolts fotograma a fotograma.

Combinació: pesos de variància INVERSA mesurats per component (Vixen,
apuntament 1 de la Sony, apuntament 2). Cap fotograma no es llença; el que
mana és la seva qualitat mesurada.

Validació (fora de mostra, res ajustat): correlació amb el mapa d'albedo
LROC WAC de la NASA a l'orientació que PREDIU l'efemèride, contra el control
nul de girar el mapa.
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
GRAU, SIG, RMAX = 4, 12, 0.90       # declarats abans de mirar el mapa
COMP = [("vixen", "", "Vixen VSD90SS + R6 III · 3 × 10 s"),
        ("sony", "_ap1", "Sony 300GM · apuntament 1 · 8 s + 2 s"),
        ("sony", "_ap2", "Sony 300GM · apuntament 2 · 8 s + 2 s + 2 s")]


def main():
    md = json.load(open(f"{CAU}/lluna_sony_meta.json"))
    x0, y0, x1, y1 = md["bbox_canvas"]
    forma = (y1 - y0, x1 - x0); centre = (MB[0] - x0, MB[1] - y0)
    yy = np.arange(y0, y1, dtype=np.float32)[:, None]
    xx = np.arange(x0, x1, dtype=np.float32)[None, :]
    rr = np.hypot(xx - MB[0], yy - MB[1]) / RL
    par = json.load(open(f"{CAU}/lluna_parell.json"))
    gs = np.array(par["guany_sony_vixen"], np.float32)

    def neteja(A, m, NB=180, grau=GRAU):
        un = A.ndim == 2
        A = A[..., None] if un else A
        out = np.zeros_like(A)
        b = np.clip((rr / 0.98 * NB).astype(int), 0, NB - 1)
        ys, xs = np.where(m)
        u = (xs - A.shape[1] / 2) / 500.0; v = (ys - A.shape[0] / 2) / 500.0
        cols = [np.ones_like(u)]
        for d in range(1, grau + 1):
            for i in range(d + 1):
                cols.append(u ** (d - i) * v ** i)
        M = np.column_stack(cols)
        for ch in range(A.shape[2]):
            Z = A[..., ch].copy(); prof = np.zeros(NB)
            for k in range(NB):
                s = m & (b == k)
                if s.sum() > 40:
                    prof[k] = np.median(Z[s])
            Z = Z - prof[b]
            c = np.linalg.lstsq(M, Z[m].astype(np.float64), rcond=None)[0]
            f = np.zeros(A.shape[:2], np.float32); f[ys, xs] = M @ c
            out[..., ch] = np.where(m, Z - f, 0)
        return out[..., 0] if un else out

    # --- càrrega, escala comuna i pesos mesurats ---
    dades, tots = {}, None
    for tren, sx, _ in COMP:
        A = np.nan_to_num(np.load(f"{CAU}/lluna_{tren}{sx}_lineal.npy"))
        if tren == "vixen":
            A = A * gs[None, None, :]           # el Vixen a l'escala Sony
        t = np.load(f"{CAU}/lluna_{tren}{sx}_tres.npy")
        dades[sx or tren] = (A, t)
        tots = t if tots is None else (tots & t)
    dins = tots & (rr < RMAX)
    print(f"disc útil (dada als 8 fotogrames, r<{RMAX} R☾): {int(dins.sum())} px")

    mer = cv2.erode(dins.astype(np.uint8),
                    np.ones((2 * int(3 * SIG) + 3,) * 2, np.uint8)).astype(bool)
    W, R, meta = {}, {}, []
    for tren, sx, etiq in COMP:
        A, _ = dades[sx or tren]
        rz = neteja(A[..., 1], dins)
        s = float(cv2.GaussianBlur(rz, (0, 0), SIG)[mer].std())
        W[sx or tren] = 1.0 / max(s * s, 1e-12)
        R[sx or tren] = rz
        meta.append((etiq, s))
    tot = sum(W.values())
    for k in W:
        W[k] /= tot
    print("\npesos de variància inversa (mesurats, cap fotograma llençat):")
    for (tren, sx, etiq), (_, s) in zip(COMP, meta):
        print(f"  {etiq:<48} rms {s:6.2f} → pes {W[sx or tren]*100:5.2f} %")

    # --- el producte: mitjana ponderada dels DOS TRENS ---
    D = np.zeros_like(dades["vixen"][0])
    for tren, sx, _ in COMP:
        D += dades[sx or tren][0] * W[sx or tren]
    E = neteja(D, dins)
    np.save(f"{CAU}/earthshine_dt_lineal.npy", D)
    np.save(f"{CAU}/earthshine_dt_resid.npy", E)
    np.save(f"{CAU}/earthshine_dt_dins.npy", dins)

    # --- validació contra el mapa de la NASA ---
    geo = L.geometria_lunar(); ori = L.orientacio_del_llenc(); Mp = L.mapa_gris()
    g0, _ = L.renderitza(Mp, geo, ori, forma, centre, RL, 0.0)
    Lr = cv2.GaussianBlur(neteja(g0.astype(np.float32), dins), (0, 0), SIG)
    m = cv2.erode(dins.astype(np.uint8),
                  np.ones((2 * int(3 * SIG) + 3,) * 2, np.uint8)).astype(bool)
    nul = []
    for ang in range(40, 325, 10):     # ⛔ |gir| < 40° NO és un nul: el mapa
        # girat poc encara se solapa amb ell mateix (a 10° dona r=0,51)
        gk, _ = L.renderitza(Mp, geo, ori, forma, centre, RL, float(ang))
        nul.append(cv2.GaussianBlur(neteja(gk.astype(np.float32), dins), (0, 0), SIG))
    print(f"\n{'producte':<34} {'r(LROC)':>9} {'nul mitjana':>12} {'nul màx':>9} {'z':>7}")
    res = {}
    provs = [("Vixen sol (3 × 10 s)", R["vixen"]),
             ("Sony apuntament 1 (2 f)", R["_ap1"]),
             ("Sony apuntament 2 (3 f)", R["_ap2"]),
             ("DOS TRENS (8 fotogrames)", E[..., 1])]
    for nom, A in provs:
        a = cv2.GaussianBlur(A, (0, 0), SIG)
        r0 = float(np.corrcoef(a[m], Lr[m])[0, 1])
        nn = np.array([float(np.corrcoef(a[m], b[m])[0, 1]) for b in nul])
        z = (r0 - nn.mean()) / max(nn.std(), 1e-9)
        print(f"{nom:<34} {r0:>+9.4f} {nn.mean():>+12.4f} {nn.max():>+9.4f} {z:>6.1f}σ")
        res[nom] = {"r": r0, "nul_mitjana": float(nn.mean()),
                    "nul_sd": float(nn.std()), "nul_max": float(nn.max()),
                    "z": float(z)}
    # amplitud física
    niv = float(np.median(D[..., 1][dins]))
    amp = float(cv2.GaussianBlur(E[..., 1], (0, 0), SIG)[m].std())
    print(f"\nnivell del disc {niv:.0f} comptes · estructura lunar rms {amp:.2f} "
          f"comptes = {100*amp/niv:.3f} % del disc")
    json.dump({"efemeride": geo, "orientacio_llenc": ori,
               "pesos": {k: float(v) for k, v in W.items()},
               "rms_per_component": {e: s for e, s in meta},
               "resultats": res, "nivell_disc": niv, "amplitud_rms": amp,
               "amplitud_pct": 100 * amp / niv,
               "model_vel": {"grau": GRAU, "radial": True, "rmax": RMAX,
                             "sigma_px": SIG},
               "control_nul": "gir del mapa 40°-320° en passos de 10°",
               "bbox": [x0, y0, x1, y1], "centre_disc": list(MB), "RL": RL,
               "mapa": "LROC WAC color poles 4k (NASA SVS 4720)"},
              open(f"{CAU}/earthshine_dt_rebut.json", "w"), indent=1,
              ensure_ascii=False)
    np.save(f"{CAU}/earthshine_lroc_render.npy", g0)


if __name__ == "__main__":
    main()
