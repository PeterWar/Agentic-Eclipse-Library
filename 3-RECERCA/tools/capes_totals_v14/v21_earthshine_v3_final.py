"""V3 final: apilat amb pesos per banda + Wiener mesurat + portes.

Cada decisió surt d'una mesura, no d'un ull:
  - pesos per component i per BANDA: w = senyal/soroll² (senyal per creuades
    entre components independents; soroll per parells del mateix component);
  - suavitzat = filtre de Wiener per bandes g = SNR²/(1+SNR²) amb l'SNR
    MESURAT de l'apilat a cada banda;
  - destripat Bayer: NOMÉS si la porta de ratlles baixa (a la v2 la pujava);
  - validació fora de mostra: r(LROC) + control nul 40-320° + escombrada
    d'orientació amb el màxim a 0°.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np, cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
sys.path.insert(0, AQUI)
import v21_lroc as L
from v21_earthshine_v3 import prepara, neteja_v3, VIX, AP1, AP2, FR

MB = (6465.398680355321, 6752.632845814709)
RL = 455.5018189723177
BANDES = [(0, 4), (4, 8), (8, 16), (16, 32), (32, 64), (64, 0)]
SIGV = 8      # escala de la validació


def banda(Z, s1, s2):
    A = cv2.GaussianBlur(Z, (0, 0), s1) if s1 else Z.copy()
    if s2:
        A -= cv2.GaussianBlur(Z, (0, 0), s2)
    return A


def ratlles(Z, m):
    hp = Z - cv2.GaussianBlur(Z, (0, 0), 6.0)
    c = np.nanstd(np.nanmedian(np.where(m, hp, np.nan), axis=0))
    f = np.nanstd(np.nanmedian(np.where(m, hp, np.nan), axis=1))
    return float(np.hypot(c, f))


def destripa(Z, m):
    hp = Z - cv2.GaussianBlur(Z, (0, 0), 6.0)
    col = np.nan_to_num(np.nanmedian(np.where(m, hp, np.nan), axis=0))
    Z2 = Z - np.where(m, col[None, :], 0)
    hp = Z2 - cv2.GaussianBlur(Z2, (0, 0), 6.0)
    fil = np.nan_to_num(np.nanmedian(np.where(m, hp, np.nan), axis=1))
    return Z2 - np.where(m, fil[:, None], 0)


def main():
    IM, tot, rr, az, bb = prepara()
    x0, y0, x1, y1 = bb
    H, W = y1 - y0, x1 - x0
    R = np.load(f"{CAU}/v3_residus.npy")
    noms = json.load(open(f"{CAU}/v3_meta.json"))["fotogrames"]
    dvo = np.load(f"{CAU}/v3_dvo.npy")
    ix = {f: noms.index(f) for f in noms}
    mer = cv2.erode((tot & (rr < 0.85)).astype(np.uint8),
                    np.ones((51, 51), np.uint8)).astype(bool)
    mvo = tot & (rr < 0.97)

    # --- destripat, amb porta ---
    m_abans = {f: ratlles(R[ix[f]], mvo) for f in noms}
    Rd = {f: destripa(R[ix[f]], mvo) for f in noms}
    m_despres = {f: ratlles(Rd[f], mvo) for f in noms}
    usa_destripat = np.median([m_despres[f] for f in noms]) < \
        np.median([m_abans[f] for f in noms])
    print(f"porta de ratlles (mediana per fotograma): "
          f"{np.median(list(m_abans.values())):.3f} → "
          f"{np.median(list(m_despres.values())):.3f} → "
          f"{'DESTRIPAT ADOPTAT' if usa_destripat else 'destripat REFUSAT'}")
    Z = Rd if usa_destripat else {f: R[ix[f]] for f in noms}

    # --- pesos i Wiener per banda ---
    comps = {"vixen": VIX, "ap1": AP1, "ap2": AP2}
    E = np.zeros((H, W), np.float32)
    taula = []
    for s1, s2 in BANDES:
        B = {f: banda(Z[f], s1, s2) for f in noms}
        P = {k: np.mean([B[f] for f in fs], axis=0) for k, fs in comps.items()}
        rc = float(np.corrcoef(P["vixen"][mer], P["ap1"][mer])[0, 1])
        sg = math.sqrt(max(rc, 0)) * math.sqrt(P["vixen"][mer].std()
                                               * P["ap1"][mer].std())
        n = {}
        for k, fs in comps.items():
            d = [(B[fs[i]] - B[fs[j]])[mer].std() / math.sqrt(2)
                 for i in range(len(fs)) for j in range(i + 1, len(fs))]
            n[k] = float(np.median(d)) / math.sqrt(len(fs))
        sd2 = P["ap2"][mer].std()
        n["ap2"] = max(n["ap2"], math.sqrt(max(sd2 ** 2 - sg ** 2, 0)))
        w = {k: sg / max(n[k], 1e-9) ** 2 for k in comps}
        T = sum(w.values()); w = {k: v / T for k, v in w.items()}
        snr2 = sum((sg / max(n[k], 1e-9)) ** 2 for k in comps)
        g = snr2 / (1.0 + snr2)
        Pb = sum(P[k] * w[k] for k in comps)
        E += Pb * g
        taula.append({"banda": f"{s1}-{s2}", "senyal": sg, "n": n,
                      "pesos": w, "snr": math.sqrt(snr2), "wiener_g": g})
        print(f"  banda {s1:>3}-{s2:<3} SNR {math.sqrt(snr2):5.1f} · g {g:.3f} · "
              f"pesos vix {100*w['vixen']:4.1f}% a1 {100*w['ap1']:4.1f}% "
              f"a2 {100*w['ap2']:4.1f}%")

    np.save(f"{CAU}/earthshine3_G.npy", E)
    np.save(f"{CAU}/earthshine3_dvo.npy", mvo)

    # --- validació fora de mostra ---
    geo = L.geometria_lunar(); ori = L.orientacio_del_llenc(); Mp = L.mapa_gris()
    cx, cy = MB[0] - x0, MB[1] - y0
    g0, _ = L.renderitza(Mp, geo, ori, (H, W), (cx, cy), RL, 0.0)
    def netm(gz):
        z, _ = neteja_v3(gz.astype(np.float32), tot, rr, az)
        return z
    Ls = cv2.GaussianBlur(netm(g0), (0, 0), SIGV)
    a = cv2.GaussianBlur(E, (0, 0), SIGV)
    r0 = float(np.corrcoef(a[mer], Ls[mer])[0, 1])
    nn = []
    for ang in range(40, 325, 10):
        gk, _ = L.renderitza(Mp, geo, ori, (H, W), (cx, cy), RL, float(ang))
        nn.append(float(np.corrcoef(a[mer],
                                    cv2.GaussianBlur(netm(gk), (0, 0), SIGV)[mer])[0, 1]))
    nn = np.array(nn)
    z = (r0 - nn.mean()) / max(nn.std(), 1e-9)
    print(f"\nPRODUCTE V3: r(LROC) = {r0:+.4f} · nul {nn.mean():+.4f}±{nn.std():.4f} "
          f"→ {z:.1f}σ")
    fins = []
    for ang in (-4, -2, 0, 2, 4):
        gk, _ = L.renderitza(Mp, geo, ori, (H, W), (cx, cy), RL, float(ang))
        fins.append((ang, float(np.corrcoef(a[mer],
                    cv2.GaussianBlur(netm(gk), (0, 0), SIGV)[mer])[0, 1])))
    mx = max(fins, key=lambda t: t[1])
    print("escombrada fina: " + " · ".join(f"{aa:+d}°:{rv:+.3f}" for aa, rv in fins)
          + f" → màxim a {mx[0]:+d}°")
    niv = float(np.median(np.mean([IM[f] for f in IM], axis=0)[mer]))
    amp = float(a[mer].std())
    print(f"nivell {niv:.0f} · estructura rms {amp:.2f} = {100*amp/niv:.3f} %")
    json.dump({"r_lroc": r0, "nul_mitjana": float(nn.mean()),
               "nul_sd": float(nn.std()), "z": float(z),
               "maxim_orientacio_deg": mx[0], "destripat": bool(usa_destripat),
               "bandes": taula, "nivell_disc": niv, "amplitud_rms": amp,
               "amplitud_pct": 100 * amp / niv, "sig_validacio": SIGV},
              open(f"{CAU}/earthshine3_rebut.json", "w"), indent=1,
              ensure_ascii=False)
    np.save(f"{CAU}/earthshine3_lroc.npy", g0)


if __name__ == "__main__":
    main()
