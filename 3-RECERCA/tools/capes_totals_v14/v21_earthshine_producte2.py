"""V21 · EARTHSHINE, segona iteració: monocrom, disc sencer, sense ratlles.

Les tres cures d'aquesta iteració (ordre de Pere del 29-08: «el disc és massa
petit; hi ha un patró de línies verticals de color brutal; repassa el projecte
d'abans, que era un bon punt de partida»):

1. ⛔ EL COLOR AMPLIFICAT ERA SOROLL: el residu R−G té 15 comptes de
   desviació amb el senyal a 5,5 — la mateixa lliçó que Earthshine_FINAL
   (15-08) ja tenia escrita («el color de gran escala NO és fiable; residu del
   halo al canal R tres vegades pitjor; no fer-lo servir»). El producte passa
   a MONOCROM del canal G, com aquell.
2. ⛔ LES LÍNIES VERTICALS són el patró de re-mostreig dels subplans Bayer
   (alineades amb les columnes del LLENÇ, no del sensor: R 0,91 comptes,
   G 0,27). Cura: restar la mediana per columna i per fila del passa-alt.
3. ⛔ EL DISC RETALLAT A 0,90 R☾ era el defecte de la capa anterior (la
   màscara d'anàlisi usada com a màscara de capa). El disc va fins a
   0,985 R☾ amb fosa; l'estructura amplificada s'esvaeix a la corona
   exterior (0,92→0,96) on el vel residual mana.
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
GRAU, SIG = 4, 12
R_FIT = 0.975          # el vel s'ajusta fins aquí (la dada arriba a ~0,98)
R_PES = 0.88           # els pesos i la validació, al disc interior net
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

    G, tots = {}, None
    for k, (tren, fs, _) in COMP.items():
        for f in fs:
            a = np.nan_to_num(np.load(f"{CAU}/lluna_{tren}_{f}_lineal.npy"))[..., 1]
            if tren == "vixen":
                a = a * gs[1]
            t = np.load(f"{CAU}/lluna_{tren}_{f}_tres.npy")
            G[f] = a
            tots = t if tots is None else (tots & t)
    fit = tots & (rr < R_FIT)
    pes = tots & (rr < R_PES)
    print(f"regió d'ajust (r<{R_FIT}): {int(fit.sum())} px · "
          f"regió de pesos (r<{R_PES}): {int(pes.sum())} px")

    def neteja(Z, NB=220):
        """vel fora: perfil radial interpolat + polinomi 2D grau 4, a r<R_FIT."""
        b = np.clip((rr / R_FIT * NB).astype(int), 0, NB - 1)
        prof = np.full(NB, np.nan)
        for k in range(NB):
            s = fit & (b == k)
            if s.sum() > 40:
                prof[k] = np.median(Z[s])
        ok = np.isfinite(prof)
        prof = np.interp(np.arange(NB), np.arange(NB)[ok], prof[ok])
        Z = Z - prof[b]
        ys, xs = np.where(fit)
        u = (xs - Z.shape[1] / 2) / 500.0; v = (ys - Z.shape[0] / 2) / 500.0
        cols = [np.ones_like(u)]
        for d in range(1, GRAU + 1):
            for i in range(d + 1):
                cols.append(u ** (d - i) * v ** i)
        M = np.column_stack(cols)
        c = np.linalg.lstsq(M, Z[fit].astype(np.float64), rcond=None)[0]
        f2 = np.zeros(Z.shape, np.float32); f2[ys, xs] = M @ c
        return np.where(fit, Z - f2, 0)

    def destripa(Z):
        """les ratlles del re-mostreig Bayer: mediana per columna i fila del
        passa-alt, només dins del disc (la mediana sobre >600 files no toca
        l'estructura lunar, que s'hi promitja)."""
        hp = Z - cv2.GaussianBlur(Z, (0, 0), 6.0)
        hpn = np.where(fit, hp, np.nan)
        col = np.nanmedian(hpn, axis=0); col = np.nan_to_num(col)
        Z = Z - np.where(fit, col[None, :], 0)
        hp = Z - cv2.GaussianBlur(Z, (0, 0), 6.0)
        hpn = np.where(fit, hp, np.nan)
        fil = np.nanmedian(hpn, axis=1); fil = np.nan_to_num(fil)
        return Z - np.where(fit, fil[:, None], 0)

    R = {}
    for k, (_, fs, _) in COMP.items():
        R[k] = destripa(neteja(np.mean([G[f] for f in fs], axis=0)))
    ind = {f: destripa(neteja(G[f])) for f in G}

    # pesos: soroll de la dispersió entre fotogrames; senyal de les creuades
    mer = cv2.erode(pes.astype(np.uint8),
                    np.ones((2 * int(3 * SIG) + 3,) * 2, np.uint8)).astype(bool)
    Zs = {f: cv2.GaussianBlur(ind[f], (0, 0), SIG) for f in ind}
    Ps = {k: cv2.GaussianBlur(R[k], (0, 0), SIG) for k in R}
    sd = {k: float(Ps[k][mer].std()) for k in R}
    gra = {}
    for k, (_, fs, _) in COMP.items():
        d = [(Zs[fs[i]] - Zs[fs[j]])[mer].std() / math.sqrt(2)
             for i in range(len(fs)) for j in range(i + 1, len(fs))]
        gra[k] = float(np.median(d)) / math.sqrt(len(fs))
    ks = list(COMP)
    X = {}
    for i in range(3):
        for j in range(i + 1, 3):
            X[(ks[i], ks[j])] = float(np.corrcoef(Ps[ks[i]][mer],
                                                  Ps[ks[j]][mer])[0, 1])

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
    T = sum(W.values()); W = {k: v / T for k, v in W.items()}
    for k in ks:
        print(f"  {COMP[k][2]:<46} rms {sd[k]:5.2f} · senyal {sig[k]:5.2f} · "
              f"pes {100*W[k]:5.2f} %")
    print("  creuades: " + " · ".join(f"{a}×{b} {v:+.3f}" for (a, b), v in X.items()))

    E = sum(W[k] * R[k] for k in ks).astype(np.float32)
    np.save(f"{CAU}/earthshine2_G.npy", E)
    np.save(f"{CAU}/earthshine2_fit.npy", fit)

    # les ratlles, abans i després (mètrica de la porta)
    hp = E - cv2.GaussianBlur(E, (0, 0), 6.0)
    colstd = float(np.nanstd(np.nanmean(np.where(pes, hp, np.nan), axis=0)))
    print(f"\nporta de ratlles: passa-alt per columna std {colstd:.3f} comptes "
          f"(abans 0,27; senyal 5,5)")

    # validació LROC (r<0.90 per comparabilitat amb el rebut anterior)
    geo = L.geometria_lunar(); ori = L.orientacio_del_llenc(); Mp = L.mapa_gris()
    g0, _ = L.renderitza(Mp, geo, ori, forma, centre, RL, 0.0)
    def netmapa(Z):
        return destripa(neteja(Z.astype(np.float32)))
    Lr = cv2.GaussianBlur(netmapa(g0), (0, 0), SIG)
    Ez = cv2.GaussianBlur(E, (0, 0), SIG)
    r0 = float(np.corrcoef(Ez[mer], Lr[mer])[0, 1])
    nul = []
    for ang in range(40, 325, 10):
        gk, _ = L.renderitza(Mp, geo, ori, forma, centre, RL, float(ang))
        nul.append(float(np.corrcoef(Ez[mer],
                                     cv2.GaussianBlur(netmapa(gk), (0, 0), SIG)[mer])[0, 1]))
    nul = np.array(nul)
    z = (r0 - nul.mean()) / max(nul.std(), 1e-9)
    print(f"validació LROC: r = {r0:+.4f} · nul {nul.mean():+.4f}±{nul.std():.4f} "
          f"→ {z:.1f}σ")
    niv = float(np.median(np.mean([G[f] for f in G], axis=0)[pes]))
    amp = float(Ez[mer].std())
    print(f"nivell del disc {niv:.0f} · estructura rms {amp:.2f} = "
          f"{100*amp/niv:.3f} %")
    json.dump({"r_lroc": r0, "nul_mitjana": float(nul.mean()),
               "nul_sd": float(nul.std()), "z": float(z),
               "pesos": {k: float(W[k]) for k in W},
               "colstd_despres": colstd, "nivell_disc": niv,
               "amplitud_rms": amp, "amplitud_pct": 100 * amp / niv,
               "monocrom": "canal G (lliçó Earthshine_FINAL: R no fiable)",
               "r_fit": R_FIT, "r_pes": R_PES},
              open(f"{CAU}/earthshine2_rebut.json", "w"), indent=1,
              ensure_ascii=False)
    np.save(f"{CAU}/earthshine2_lroc.npy", g0)


if __name__ == "__main__":
    main()
