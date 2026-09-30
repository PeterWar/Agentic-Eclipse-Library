"""V21 · EARTHSHINE DELS DOS TRENS — el producte final i el seu rebut.

Els 8 fotogrames que Pere va demanar (Sony >1 s: 2s×3 + 8s×2; Vixen >9 s:
10 s×3), apilats al mateix marc lunar amb tots els moviments resolts.

Pesos: NO els trio jo. Per a cada component es mesura
  · el soroll, amb la dispersió ENTRE els seus propis fotogrames
    (el senyal i el vel hi són comuns i es cancel·len a la diferència);
  · el senyal lunar, amb les covariàncies CREUADES entre components
    independents (s_i² = cov(i,j)·cov(i,k)/cov(j,k));
i el pes òptim és s_i / (allò que no és senyal)².  El mapa de la NASA no
entra enlloc: queda FORA DE MOSTRA per validar.
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
GRAU, SIG, RMAX = 4, 12, 0.90
COMP = {"vixen": ("vixen", ["572A2982", "572A2983", "572A2984"],
                  "Vixen VSD90SS + R6 III · 3 × 10 s"),
        "ap1": ("sony", ["DSC06987", "DSC06984"],
                "Sony 300GM · apuntament 1 · 8 s + 2 s"),
        "ap2": ("sony", ["DSC06993", "DSC06996", "DSC06999"],
                "Sony 300GM · apuntament 2 · 8 s + 2 s + 2 s")}


def main():
    md = json.load(open(f"{CAU}/lluna_sony_meta.json"))
    x0, y0, x1, y1 = md["bbox_canvas"]
    forma = (y1 - y0, x1 - x0); centre = (MB[0] - x0, MB[1] - y0)
    yy = np.arange(y0, y1, dtype=np.float32)[:, None]
    xx = np.arange(x0, x1, dtype=np.float32)[None, :]
    rr = np.hypot(xx - MB[0], yy - MB[1]) / RL
    gs = np.array(json.load(open(f"{CAU}/lluna_parell.json"))["guany_sony_vixen"],
                  np.float32)

    dat, tots = {}, None
    for k, (tren, fs, _) in COMP.items():
        for f in fs:
            a = np.nan_to_num(np.load(f"{CAU}/lluna_{tren}_{f}_lineal.npy"))
            if tren == "vixen":
                a = a * gs[None, None, :]
            t = np.load(f"{CAU}/lluna_{tren}_{f}_tres.npy")
            dat[f] = a
            tots = t if tots is None else (tots & t)
    dins = tots & (rr < RMAX)
    mer = cv2.erode(dins.astype(np.uint8),
                    np.ones((2 * int(3 * SIG) + 3,) * 2, np.uint8)).astype(bool)

    def neteja(A, NB=180, grau=GRAU):
        un = A.ndim == 2
        A = A[..., None] if un else A
        out = np.zeros_like(A)
        b = np.clip((rr / 0.98 * NB).astype(int), 0, NB - 1)
        ys, xs = np.where(dins)
        u = (xs - A.shape[1] / 2) / 500.0; v = (ys - A.shape[0] / 2) / 500.0
        cols = [np.ones_like(u)]
        for d in range(1, grau + 1):
            for i in range(d + 1):
                cols.append(u ** (d - i) * v ** i)
        M = np.column_stack(cols)
        for ch in range(A.shape[2]):
            Z = A[..., ch].copy()
            prof = np.full(NB, np.nan)
            for k in range(NB):
                s = dins & (b == k)
                if s.sum() > 40:
                    prof[k] = np.median(Z[s])
            # ⛔ els anells més interiors tenen menys de 40 px: si es deixen a
            #    zero, al centre no es resta res i hi surt un pic fabricat de
            #    250 comptes que NO és a cap fotograma (caçat el 29-08).
            ok = np.isfinite(prof)
            prof = np.interp(np.arange(NB), np.arange(NB)[ok], prof[ok])
            Z = Z - prof[b]
            c = np.linalg.lstsq(M, Z[dins].astype(np.float64), rcond=None)[0]
            f = np.zeros(A.shape[:2], np.float32); f[ys, xs] = M @ c
            out[..., ch] = np.where(dins, Z - f, 0)
        return out[..., 0] if un else out

    Z = {f: cv2.GaussianBlur(neteja(dat[f][..., 1]), (0, 0), SIG) for f in dat}
    prom = {k: np.mean([Z[f] for f in fs], axis=0)
            for k, (_, fs, _) in COMP.items()}
    sd = {k: float(prom[k][mer].std()) for k in prom}
    gra = {}
    for k, (_, fs, _) in COMP.items():
        d = [(Z[fs[i]] - Z[fs[j]])[mer].std() / math.sqrt(2)
             for i in range(len(fs)) for j in range(i + 1, len(fs))]
        gra[k] = float(np.median(d)) / math.sqrt(len(fs))
    ks = list(COMP)
    X = {}
    for i in range(3):
        for j in range(i + 1, 3):
            X[(ks[i], ks[j])] = float(np.corrcoef(prom[ks[i]][mer],
                                                  prom[ks[j]][mer])[0, 1])

    def cov(a, b):
        r = X.get((a, b), X.get((b, a)))
        return r * sd[a] * sd[b]

    sig, soroll, W = {}, {}, {}
    for k in ks:
        o = [z for z in ks if z != k]
        sig[k] = math.sqrt(max(cov(k, o[0]) * cov(k, o[1])
                               / max(cov(o[0], o[1]), 1e-12), 0.0))
        soroll[k] = math.sqrt(max(sd[k] ** 2 - sig[k] ** 2, gra[k] ** 2))
        W[k] = sig[k] / soroll[k] ** 2
    T = sum(W.values())
    W = {k: v / T for k, v in W.items()}
    print(f"{'component':<44} {'rms':>6} {'gra':>6} {'senyal':>7} "
          f"{'no-senyal':>10} {'pes':>7}")
    for k in ks:
        print(f"{COMP[k][2]:<44} {sd[k]:>6.2f} {gra[k]:>6.2f} {sig[k]:>7.2f} "
              f"{soroll[k]:>10.2f} {100*W[k]:>6.2f} %")
    print("\ncorrelacions creuades (instruments/apuntaments independents):")
    for (a, b), r in X.items():
        print(f"  {a:6s} × {b:6s} = {r:+.4f}")

    # --- el producte, RGB, al marc lunar ---
    E = np.zeros(dat[COMP["vixen"][1][0]].shape, np.float32)
    for k, (_, fs, _) in COMP.items():
        E += W[k] * neteja(np.mean([dat[f] for f in fs], axis=0))
    Elis = np.dstack([cv2.GaussianBlur(E[..., c], (0, 0), 4.0) for c in range(3)])
    np.save(f"{CAU}/earthshine_producte.npy", Elis)
    np.save(f"{CAU}/earthshine_producte_dins.npy", dins)

    # --- validació fora de mostra amb el mapa de la NASA ---
    geo = L.geometria_lunar(); ori = L.orientacio_del_llenc(); Mp = L.mapa_gris()
    g0, _ = L.renderitza(Mp, geo, ori, forma, centre, RL, 0.0)
    Lr = cv2.GaussianBlur(neteja(g0.astype(np.float32)), (0, 0), SIG)
    nuls = []
    for ang in range(40, 325, 10):
        gk, _ = L.renderitza(Mp, geo, ori, forma, centre, RL, float(ang))
        nuls.append(cv2.GaussianBlur(neteja(gk.astype(np.float32)), (0, 0), SIG))
    print(f"\n{'producte':<38} {'r(LROC)':>9} {'nul':>16} {'z':>7}")
    res = {}
    provs = [(COMP[k][2], prom[k]) for k in ks]
    provs.append(("DOS TRENS · 8 fotogrames · producte",
                  cv2.GaussianBlur(E[..., 1], (0, 0), SIG)))
    for nom, A in provs:
        r0 = float(np.corrcoef(A[mer], Lr[mer])[0, 1])
        nn = np.array([float(np.corrcoef(A[mer], b[mer])[0, 1]) for b in nuls])
        z = (r0 - nn.mean()) / max(nn.std(), 1e-9)
        print(f"{nom:<38} {r0:>+9.4f} {nn.mean():>+8.4f}±{nn.std():.4f} {z:>6.1f}σ")
        res[nom] = {"r": r0, "nul_mitjana": float(nn.mean()),
                    "nul_sd": float(nn.std()), "nul_max": float(nn.max()),
                    "z": float(z)}
    niv = float(np.median(np.mean([dat[f][..., 1] for f in dat], axis=0)[dins]))
    amp = float(cv2.GaussianBlur(E[..., 1], (0, 0), SIG)[mer].std())
    print(f"\nnivell del disc {niv:.0f} comptes · estructura lunar rms {amp:.2f} "
          f"= {100*amp/niv:.3f} % del disc")
    json.dump({"efemeride": geo, "orientacio_llenc": ori, "pesos": W,
               "rms": sd, "gra": gra, "senyal": sig, "no_senyal": soroll,
               "creuades": {f"{a}x{b}": v for (a, b), v in X.items()},
               "resultats": res, "nivell_disc": niv, "amplitud_rms": amp,
               "amplitud_pct": 100 * amp / niv,
               "model_vel": {"grau": GRAU, "radial": True, "rmax": RMAX,
                             "sigma_px": SIG},
               "control_nul": "gir del mapa 40°-320° cada 10°",
               "fotogrames": {k: COMP[k][1] for k in COMP},
               "bbox": [x0, y0, x1, y1], "centre_disc": list(MB), "RL": RL,
               "mapa": "LROC WAC color poles 4k · NASA SVS 4720"},
              open(f"{CAU}/earthshine_producte_rebut.json", "w"), indent=1,
              ensure_ascii=False)
    np.save(f"{CAU}/earthshine_lroc_render.npy", g0)


if __name__ == "__main__":
    main()
