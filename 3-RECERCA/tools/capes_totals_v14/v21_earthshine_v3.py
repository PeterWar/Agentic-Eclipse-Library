"""V3 de l'earthshine: neteja de vel per regions, apilat amb pesos mesurats,
Wiener per bandes. Canònic del mètode: research/127 (en curs).

La troballa que mana (29-08, tarda): el coll d'ampolla era la RESTA DEL VEL.
El polinomi ajustat fins a r<0,975 s'empassava el gradient del limbe i
contaminava tot el disc (r LROC 0,78); ajustat només dins r<0,85, cada
fotograma sol puja a 0,86-0,90 i l'apilat a 0,88.
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
R_NUCLI = 0.85        # el polinomi s'ajusta NOMÉS aquí (gradient de vel suau)
R_VORA = 0.97         # fins on arriba el model per anell de la vora
FUSIO = (0.80, 0.85)  # fosa entre els dos models
K_AZI = 2             # Fourier azimutal per anell a la vora
FR = [("vixen", "572A2982", 10), ("vixen", "572A2983", 10),
      ("vixen", "572A2984", 10), ("sony", "DSC06987", 8),
      ("sony", "DSC06984", 2), ("sony", "DSC06993", 8),
      ("sony", "DSC06996", 2), ("sony", "DSC06999", 2)]
VIX = ["572A2982", "572A2983", "572A2984"]
AP1 = ["DSC06987", "DSC06984"]
AP2 = ["DSC06993", "DSC06996", "DSC06999"]
BANDES = [(0, 4), (4, 8), (8, 16), (16, 32), (32, 64), (64, 0)]


def prepara():
    md = json.load(open(f"{CAU}/lluna_sony_meta.json"))
    x0, y0, x1, y1 = md["bbox_canvas"]
    yy = np.arange(y0, y1, dtype=np.float32)[:, None]
    xx = np.arange(x0, x1, dtype=np.float32)[None, :]
    rr = np.hypot(xx - MB[0], yy - MB[1]) / RL
    az = np.arctan2(yy - MB[1], xx - MB[0]).astype(np.float32)
    gs = np.array(json.load(open(f"{CAU}/lluna_parell.json"))["guany_sony_vixen"],
                  np.float32)
    IM, tot = {}, None
    for tren, f, e in FR:
        a = np.nan_to_num(np.load(f"{CAU}/lluna_{tren}_{f}_lineal.npy"))[..., 1]
        if tren == "vixen":
            a = a * gs[1]
        IM[f] = a
        t = np.load(f"{CAU}/lluna_{tren}_{f}_tres.npy")
        tot = t if tot is None else (tot & t)
    return IM, tot, rr, az, (x0, y0, x1, y1)


def neteja_v3(Z, tot, rr, az):
    """Vel fora, per regions: nucli (radial+poli4 ajustat a r<R_NUCLI) i vora
    (mediana + Fourier azimutal k<=K_AZI per anell), fosos a FUSIO."""
    dnu = tot & (rr < R_NUCLI)
    dvo = tot & (rr < R_VORA)
    # --- nucli ---
    NB = 160
    b = np.clip((rr / R_VORA * NB).astype(int), 0, NB - 1)
    prof = np.full(NB, np.nan)
    for k in range(NB):
        s = dvo & (b == k)
        if s.sum() > 40:
            prof[k] = np.median(Z[s])
    ok = np.isfinite(prof)
    prof = np.interp(np.arange(NB), np.arange(NB)[ok], prof[ok])
    Zr = Z - prof[b]
    ys, xs = np.where(dnu)
    u = (xs - Z.shape[1] / 2) / 500.0; v = (ys - Z.shape[0] / 2) / 500.0
    cols = [np.ones_like(u)]
    for d in range(1, 5):
        for i in range(d + 1):
            cols.append(u ** (d - i) * v ** i)
    M = np.column_stack(cols)
    c = np.linalg.lstsq(M, Zr[dnu].astype(np.float64), rcond=None)[0]
    # el polinomi s'AVALUA a tot el disc però s'ha ajustat només al nucli
    ysv, xsv = np.where(dvo)
    uv = (xsv - Z.shape[1] / 2) / 500.0; vv = (ysv - Z.shape[0] / 2) / 500.0
    colsv = [np.ones_like(uv)]
    for d in range(1, 5):
        for i in range(d + 1):
            colsv.append(uv ** (d - i) * vv ** i)
    fnu = np.zeros(Z.shape, np.float32)
    fnu[ysv, xsv] = np.column_stack(colsv) @ c
    Rnu = np.where(dvo, Zr - fnu, 0)
    # --- vora: per anell, mediana + Fourier azimutal ---
    NB2 = 80
    b2 = np.clip((rr / R_VORA * NB2).astype(int), 0, NB2 - 1)
    Rvo = np.zeros_like(Z)
    for k in range(int(0.75 * NB2), NB2):
        s = dvo & (b2 == k)
        if s.sum() < 60:
            continue
        th = az[s]; z = Zr[s].astype(np.float64)
        Ms = [np.ones_like(th)]
        for q in range(1, K_AZI + 1):
            Ms += [np.cos(q * th), np.sin(q * th)]
        Ms = np.column_stack(Ms)
        cc = np.linalg.lstsq(Ms, z, rcond=None)[0]
        Rvo[s] = (z - Ms @ cc).astype(np.float32)
    # --- fosa ---
    w = np.clip((rr - FUSIO[0]) / (FUSIO[1] - FUSIO[0]), 0, 1).astype(np.float32)
    return np.where(dvo, Rnu * (1 - w) + Rvo * w, 0), dvo


def porta_vel(Rz, tot, rr):
    """porta interna (SENSE el mapa): el residu de vel per anell ha de ser pla.
    mediana absoluta del nivell per anell, dins r<R_VORA."""
    NB = 60
    b = np.clip((rr / R_VORA * NB).astype(int), 0, NB - 1)
    nv = []
    for k in range(NB):
        s = tot & (b == k) & (rr < R_VORA)
        if s.sum() > 100:
            nv.append(abs(float(np.median(Rz[s]))))
    return float(np.max(nv)), float(np.median(nv))


def main():
    IM, tot, rr, az, bb = prepara()
    x0, y0, x1, y1 = bb
    R, dvo = {}, None
    for f in IM:
        R[f], dvo = neteja_v3(IM[f], tot, rr, az)
    prom = {"vixen": np.mean([R[f] for f in VIX], axis=0),
            "ap1": np.mean([R[f] for f in AP1], axis=0),
            "ap2": np.mean([R[f] for f in AP2], axis=0)}
    pm, pmed = porta_vel(prom["vixen"], tot, rr)
    print(f"porta interna del vel (Vixen): màx |nivell per anell| {pm:.2f} · "
          f"mediana {pmed:.2f} comptes (senyal ~4,6)")

    # pesos i SNR per banda (senyal comú per creuades, soroll per parells)
    m8 = cv2.erode((tot & (rr < R_NUCLI)).astype(np.uint8),
                   np.ones((51, 51), np.uint8)).astype(bool)
    def banda(Z, s1, s2):
        A = cv2.GaussianBlur(Z, (0, 0), s1) if s1 else Z
        return A - (cv2.GaussianBlur(Z, (0, 0), s2) if s2 else 0)
    stats = {}
    for s1, s2 in BANDES:
        Bv = {f: banda(R[f], s1, s2) for f in R}
        P = {k: np.mean([Bv[f] for f in fs], axis=0)
             for k, fs in (("vixen", VIX), ("ap1", AP1), ("ap2", AP2))}
        rc = float(np.corrcoef(P["vixen"][m8], P["ap1"][m8])[0, 1])
        sg = math.sqrt(max(rc, 0)) * math.sqrt(P["vixen"][m8].std() * P["ap1"][m8].std())
        n = {}
        for k, fs in (("vixen", VIX), ("ap1", AP1), ("ap2", AP2)):
            d = [(Bv[fs[i]] - Bv[fs[j]])[m8].std() / math.sqrt(2)
                 for i in range(len(fs)) for j in range(i + 1, len(fs))]
            n[k] = float(np.median(d)) / math.sqrt(len(fs))
        # ap2: el vel fluctuant no surt als parells; cota pel total
        sd2 = P["ap2"][m8].std()
        n["ap2"] = max(n["ap2"], math.sqrt(max(sd2 ** 2 - sg ** 2, 0)))
        stats[(s1, s2)] = (sg, n)
    print(f"\n{'banda':>8} {'senyal':>7} | {'n vix':>6} {'n a1':>6} {'n a2':>6} | "
          f"{'SNR apilat':>10}")
    for (s1, s2), (sg, n) in stats.items():
        snr = math.sqrt(sum((sg / max(n[k], 1e-9)) ** 2 for k in n))
        print(f"{s1:>3}-{s2:<4} {sg:>7.2f} | {n['vixen']:>6.2f} {n['ap1']:>6.2f} "
              f"{n['ap2']:>6.2f} | {snr:>10.1f}")
    json.dump({f"{s1}-{s2}": {"senyal": sg, "n": n}
               for (s1, s2), (sg, n) in stats.items()},
              open(f"{CAU}/v3_bandes.json", "w"), indent=1)
    np.save(f"{CAU}/v3_residus.npy",
            np.stack([R[f] for _, f, _ in FR]))
    np.save(f"{CAU}/v3_dvo.npy", dvo)
    json.dump({"fotogrames": [f for _, f, _ in FR]},
              open(f"{CAU}/v3_meta.json", "w"), indent=1)
    print("\nresidus per fotograma desats (v3_residus.npy)")


if __name__ == "__main__":
    main()
