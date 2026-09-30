"""V4 de l'earthshine — el pla revisat pel contrast de Codex (research/127 §6).

Canvis respecte de la V3, tots del veredicte:
  · FORA el model azimutal k≤2 de la vora (transferència 0 als modes lunars
    k=1,2): la ciència es DECLARA vàlida a r<0,85 i prou.
  · Pesos en DOS nivells: dins de component ∝ t_exp (model fotònic declarat;
    abans 8 s i 2 s entraven a mitjana igual), i UN pes per component
    (senyal/soroll² mesurat a la banda 8-64); cap pes per banda.
  · Wiener només per ATENUAR <8 px (on el g mesurat és 0,06-0,71).
  · Destripat OFF per defecte, amb porta held-out per meitats de files/columnes.
  · INJECCIÓ CEGA de textura sintètica: la transferència del pipeline a
    8-64 px ha de ser 0,90-1,10.
  · Component nou: Vixen 3×2 s (572A2979-81).
  · DECLARACIÓ: la selecció r<0,85 va ser assistida pel LROC → la r final és
    millora de producte; la significança canònica és la del research/126 (7σ).
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
R_FIT = 0.85
SIGV = 8
COMPS = {
    "vixen10": (["572A2982", "572A2983", "572A2984"], [10., 10., 10.], "vixen"),
    "vixen2": (["572A2979", "572A2980", "572A2981"], [2., 2., 2.], "vixen"),
    "ap1": (["DSC06987", "DSC06984"], [8., 2.], "sony"),
    "ap2": (["DSC06993", "DSC06996", "DSC06999"], [8., 2., 2.], "sony"),
}


def prepara():
    md = json.load(open(f"{CAU}/lluna_sony_meta.json"))
    x0, y0, x1, y1 = md["bbox_canvas"]
    yy = np.arange(y0, y1, dtype=np.float32)[:, None]
    xx = np.arange(x0, x1, dtype=np.float32)[None, :]
    rr = np.hypot(xx - MB[0], yy - MB[1]) / RL
    gs = np.array(json.load(open(f"{CAU}/lluna_parell.json"))["guany_sony_vixen"],
                  np.float32)
    IM, tot = {}, None
    for k, (fs, ts, tren) in COMPS.items():
        for f in fs:
            a = np.nan_to_num(np.load(f"{CAU}/lluna_{tren}_{f}_lineal.npy"))[..., 1]
            if tren == "vixen":
                a = a * gs[1]
            IM[f] = a
            t = np.load(f"{CAU}/lluna_{tren}_{f}_tres.npy")
            tot = t if tot is None else (tot & t)
    return IM, tot, rr, (x0, y0, x1, y1)


def fes_neteja(tot, rr, forma, r_aval=None):
    """neteja del vel: perfil radial interpolat + polinomi 2D grau 4, tot
    ajustat NOMÉS dins r<R_FIT. Sense cap model azimutal (veredicte Codex)."""
    dnu = tot & (rr < R_FIT)
    dav = tot & (rr < (r_aval or R_FIT))          # on s'AVALUA el model
    NB = 160
    b = np.clip((rr / (r_aval or R_FIT) * NB).astype(int), 0, NB - 1)
    ys, xs = np.where(dav)
    u = (xs - forma[1] / 2) / 500.0; v = (ys - forma[0] / 2) / 500.0
    cols = [np.ones_like(u)]
    for d in range(1, 5):
        for i in range(d + 1):
            cols.append(u ** (d - i) * v ** i)
    M = np.column_stack(cols)

    dfit = tot & (rr < R_FIT)

    def neteja(Z):
        prof = np.full(NB, np.nan)
        for k in range(NB):
            s = dav & (b == k)
            if s.sum() > 40:
                prof[k] = np.median(Z[s])
        ok = np.isfinite(prof)
        prof = np.interp(np.arange(NB), np.arange(NB)[ok], prof[ok])
        Zr = Z - prof[b]
        c = np.linalg.lstsq(M[dfit[ys, xs]], Zr[dfit].astype(np.float64),
                            rcond=None)[0]
        f2 = np.zeros(Z.shape, np.float32); f2[ys, xs] = M @ c
        return np.where(dav, Zr - f2, 0)
    return neteja, dav


def main():
    IM, tot, rr, bb = prepara()
    x0, y0, x1, y1 = bb
    H, W = y1 - y0, x1 - x0
    neteja, dnu = fes_neteja(tot, rr, (H, W))
    mer = cv2.erode(dnu.astype(np.uint8),
                    np.ones((2 * 3 * SIGV + 3,) * 2, np.uint8)).astype(bool)

    # --- residus per fotograma i mitjanes de component amb pes ∝ t_exp ---
    R = {f: neteja(IM[f]) for f in IM}
    P, nf = {}, {}
    for k, (fs, ts, _) in COMPS.items():
        w = np.array(ts) / sum(ts)
        P[k] = sum(R[f] * wi for f, wi in zip(fs, w)).astype(np.float32)
        # soroll del component A LA BANDA 8-64 px (la del senyal): dispersió
        # ponderada entre fotogrames — mesurar-lo al residu cru barreja el
        # gra de píxel, que el Wiener ja atenua, i falseja els pesos
        def _b(Z):
            return (cv2.GaussianBlur(Z, (0, 0), 4.0)
                    - cv2.GaussianBlur(Z, (0, 0), 32.0))
        if len(fs) > 1:
            d = [(_b(R[fs[i]]) - _b(R[fs[j]]))[mer].std() / math.sqrt(2)
                 for i in range(len(fs)) for j in range(i + 1, len(fs))]
            nf[k] = float(np.median(d)) * math.sqrt(sum(w ** 2))
        else:
            nf[k] = np.nan

    # --- porta held-out del destripat (Codex G-RATLLES) ---
    def destripa_cols(Z, files_mask):
        hp = Z - cv2.GaussianBlur(Z, (0, 0), 6.0)
        sel = np.where(files_mask[:, None] & dnu, hp, np.nan)
        col = np.nan_to_num(np.nanmedian(sel, axis=0))
        return col

    def metrica_cols(Z, files_mask):
        hp = Z - cv2.GaussianBlur(Z, (0, 0), 6.0)
        sel = np.where(files_mask[:, None] & dnu, hp, np.nan)
        return float(np.nanstd(np.nanmedian(sel, axis=0)))

    fm = np.zeros(H, bool); fm[::2] = True     # meitat A = files parelles
    Zt = P["vixen10"]
    col_A = destripa_cols(Zt, fm)
    m_B_abans = metrica_cols(Zt, ~fm)
    m_B_despres = metrica_cols(Zt - np.where(dnu, col_A[None, :], 0), ~fm)
    millora = (m_B_abans - m_B_despres) / max(m_B_abans, 1e-9)
    usa = millora >= 0.20
    print(f"porta held-out del destripat (columnes, Vixen10): "
          f"{m_B_abans:.3f} → {m_B_despres:.3f} ({100*millora:+.0f} %) → "
          f"{'ADOPTAT' if usa else 'OFF (per defecte)'}")
    def destripa(Z):
        hp = Z - cv2.GaussianBlur(Z, (0, 0), 6.0)
        col = np.nan_to_num(np.nanmedian(np.where(dnu, hp, np.nan), axis=0))
        Z = Z - np.where(dnu, col[None, :], 0)
        fil = np.nan_to_num(np.nanmedian(np.where(dnu, (Z -
              cv2.GaussianBlur(Z, (0, 0), 6.0)), np.nan), axis=1))
        return Z - np.where(dnu, fil[:, None], 0)
    if usa:
        for k in P:
            P[k] = destripa(P[k])

    # --- senyal comú i pesos per component (banda 8-64, escalars) ---
    def b864(Z):
        return cv2.GaussianBlur(Z, (0, 0), 4.0) - cv2.GaussianBlur(Z, (0, 0), 32.0)
    B = {k: b864(P[k]) for k in P}
    rc = float(np.corrcoef(B["vixen10"][mer], B["ap1"][mer])[0, 1])
    sg = math.sqrt(max(rc, 0)) * math.sqrt(B["vixen10"][mer].std()
                                           * B["ap1"][mer].std())
    # ⛔ WALKING NOISE (31-08, marcat per Pere): el patró fix del sensor
    #    camina amb la deriva lunar (12,3 px a 77°; el gra del producte surt
    #    orientat a 75°). Els PARELLS entre germans no el veuen (el patró
    #    apareix desplaçat: r fina 0,03 a Δt=13 s però 0,44 a Δt=3 s), o
    #    sigui que nf el SUBESTIMA. L'estimador bo per a TOTS els
    #    components: soroll² = potència total − senyal² (el senyal surt de
    #    la creuada entre SENSORS diferents, neta de FPN).
    W_, det = {}, {}
    for k in P:
        sd = B[k][mer].std()
        n = max(nf[k] if np.isfinite(nf[k]) else sd,
                math.sqrt(max(sd ** 2 - sg ** 2, 0.0)))
        W_[k] = sg / max(n, 1e-9) ** 2
        det[k] = (sd, n)
    T = sum(W_.values()); W_ = {k: v / T for k, v in W_.items()}
    print("\npesos per component (escalars; dins de component ∝ t_exp):")
    for k in P:
        print(f"  {k:<8} rms {det[k][0]:6.2f} · no-senyal {det[k][1]:6.2f} · "
              f"pes {100*W_[k]:5.2f} %")

    # ⛔ LA MOTA DEL SENSOR R6 (31-08, marcada per Pere com a "cràter fals"):
    #    tret fix al sensor a (3579, 2374) — al marc lunar (330, 528) —
    #    present als 6 fotogrames Vixen (+33 comptes) i ABSENT a la Sony
    #    (+5 ± 4,5). No és al flat del 22-08 (correlació 0,00: la pols es va
    #    moure en 10 dies). Cura quirúrgica: pes Vixen → 0 en un radi de
    #    22 px amb fosa; allà mana la Sony, que hi és neta. Res inventat.
    yyq, xxq = np.mgrid[0:H, 0:W].astype(np.float32)
    dmota = np.hypot(xxq - 330.0, yyq - 528.0)
    Mmota = np.clip((dmota - 14.0) / 8.0, 0, 1).astype(np.float32)
    Wm = {k: (np.full((H, W), W_[k], np.float32) * (Mmota if k in
              ("vixen10", "vixen2") else 1.0)) for k in P}
    Tm = sum(Wm.values())
    E = (sum(P[k] * Wm[k] for k in P) / np.maximum(Tm, 1e-9)).astype(np.float32)

    # Wiener en FOURIER amb bandes netes en λ (la injecció cega va caçar que
    # les diferències de gaussianes tenen cues: la "banda 4-8" DoG arriba a
    # λ~40 px i atenuar-la menjava el 17 % del senyal — transferència 0,83)
    H2, W2 = E.shape
    fy = np.fft.fftfreq(H2)[:, None]; fx = np.fft.rfftfreq(W2)[None, :]
    fr = np.hypot(fy, fx)
    lam = np.where(fr > 1e-9, 1.0 / np.maximum(fr, 1e-9), 1e9)
    # g mesurat per banda (v3_bandes/earthshine3): λ<4 0,06 · 4-8 0,71 ·
    # 8-16 0,96 · 16-32 0,995 · ≥32 1,0 — interpolat suau en log λ
    pl = np.log([2.0, 4.0, 8.0, 16.0, 32.0, 64.0])
    pg = np.array([0.06, 0.06, 0.71, 0.96, 0.995, 1.0])
    G = np.interp(np.log(np.clip(lam, 2.0, 64.0)), pl, pg).astype(np.float32)

    def wiener(Z):
        return np.fft.irfft2(np.fft.rfft2(Z) * G, s=Z.shape).astype(np.float32)
    E = wiener(E) * dnu
    np.save(f"{CAU}/earthshine4_G.npy", E)
    np.save(f"{CAU}/earthshine4_dnu.npy", dnu)

    # --- INJECCIÓ CEGA: transferència del pipeline ---
    rng = np.random.default_rng(12)
    tex = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32),
                           (0, 0), 10.0)
    tex *= 5.5 / tex[mer].std()
    Rt = {f: neteja(IM[f] + tex) for f in IM}
    Pt = {}
    for k, (fs, ts, _) in COMPS.items():
        w = np.array(ts) / sum(ts)
        Pt[k] = sum(Rt[f] * wi for f, wi in zip(fs, w)).astype(np.float32)
        if usa:
            Pt[k] = destripa(Pt[k])
    Et = wiener((sum(Pt[k] * Wm[k] for k in P)
                 / np.maximum(Tm, 1e-9)).astype(np.float32)) * dnu
    dif = Et - E
    def _b864(Z):
        return (cv2.GaussianBlur(Z, (0, 0), 4.0)
                - cv2.GaussianBlur(Z, (0, 0), 32.0))
    db, tb = _b864(dif), _b864(tex)
    g1 = float(np.dot(db[mer], tb[mer]) / np.dot(tb[mer], tb[mer]))
    print(f"\nINJECCIÓ CEGA (σ10 px, amplitud 5,5; transferència A LA BANDA "
          f"8-64): {g1:.3f} → {'PASS' if 0.90 <= g1 <= 1.10 else 'FAIL'}")

    # --- validació (r<0,85; el mapa fora de mostra per a la FORMA) ---
    geo = L.geometria_lunar(); ori = L.orientacio_del_llenc(); Mp = L.mapa_gris()
    cx, cy = MB[0] - x0, MB[1] - y0
    g0, _ = L.renderitza(Mp, geo, ori, (H, W), (cx, cy), RL, 0.0)
    Ls = cv2.GaussianBlur(neteja(g0.astype(np.float32)), (0, 0), SIGV)
    a = cv2.GaussianBlur(E, (0, 0), SIGV)
    r0 = float(np.corrcoef(a[mer], Ls[mer])[0, 1])
    nn = []
    for ang in range(40, 325, 10):
        gk, _ = L.renderitza(Mp, geo, ori, (H, W), (cx, cy), RL, float(ang))
        nn.append(float(np.corrcoef(a[mer],
                  cv2.GaussianBlur(neteja(gk.astype(np.float32)), (0, 0), SIGV)[mer])[0, 1]))
    nn = np.array(nn)
    print(f"\nPRODUCTE V4: r(LROC) = {r0:+.4f} · nul {nn.mean():+.4f}±{nn.std():.4f}")
    print("⚠️ DECLARAT: r_fit=0,85 seleccionat amb assistència del mapa → això és")
    print("   MILLORA DE PRODUCTE; la detecció canònica és la del research/126 (7,0σ).")
    fins = []
    for ang in (-4, -2, 0, 2, 4):
        gk, _ = L.renderitza(Mp, geo, ori, (H, W), (cx, cy), RL, float(ang))
        fins.append((ang, float(np.corrcoef(a[mer],
                    cv2.GaussianBlur(neteja(gk.astype(np.float32)), (0, 0), SIGV)[mer])[0, 1])))
    mx = max(fins, key=lambda t: t[1])
    print(f"escombrada fina: màxim a {mx[0]:+d}° "
          f"({' '.join(f'{aa:+d}:{rv:+.3f}' for aa, rv in fins)})")
    niv = float(np.median(np.mean([IM[f] for f in IM], axis=0)[mer]))
    amp = float(a[mer].std())
    snr = math.sqrt(sum((sg / max(det[k][1], 1e-9)) ** 2 for k in P))
    print(f"nivell {niv:.0f} · estructura {amp:.2f} = {100*amp/niv:.3f} % · "
          f"SNR proxy {snr:.1f}")
    json.dump({"r_lroc": r0, "nul_mitjana": float(nn.mean()),
               "nul_sd": float(nn.std()),
               "declaracio": "r_fit assistit pel mapa: millora de producte; "
                             "deteccio canonica = research/126 (7,0σ)",
               "maxim_orientacio_deg": mx[0], "destripat_held_out": bool(usa),
               "injeccio_transferencia": g1,
               "pesos": {k: float(W_[k]) for k in W_},
               "pes_intra_component": "proporcional a t_exp (model fotonic)",
               "snr_proxy": snr, "nivell_disc": niv, "amplitud_rms": amp,
               "amplitud_pct": 100 * amp / niv, "r_fit": R_FIT,
               "wiener": "FFT, bandes netes en lambda: <4 g=0,06 · 4-8 0,71 · 8-16 0,96 · 16-32 0,995 · >=32 1,0",
               "vora": "sense model azimutal; ciencia valida r<0,85",
               "mota_sensor_r6": {"marc_lunar": [330, 528],
                                  "sensor": [3579, 2374], "radi_px": 22,
                                  "vixen": 33.4, "sony": 5.0,
                                  "al_flat_2208": "NO (r=0,00)"}},
              open(f"{CAU}/earthshine4_rebut.json", "w"), indent=1,
              ensure_ascii=False)
    np.save(f"{CAU}/earthshine4_lroc.npy", g0)

    # --- l'extensió de DISPLAY (per a la capa): el mateix model del nucli
    #     avaluat fins a 0,975 — la ciència acaba a 0,85; això és estètica
    #     amb dada real, DECLARAT ---
    netd, dav = fes_neteja(tot, rr, (H, W), r_aval=0.975)
    Rd2 = {f: netd(IM[f]) for f in IM}
    Pd = {}
    for k, (fs, ts, _) in COMPS.items():
        w = np.array(ts) / sum(ts)
        Pd[k] = sum(Rd2[f] * wi for f, wi in zip(fs, w)).astype(np.float32)
        if usa:
            Pd[k] = destripa(Pd[k])
    Ed = (sum(Pd[k] * Wm[k] for k in P) / np.maximum(Tm, 1e-9)).astype(np.float32)
    Ed = wiener(Ed) * dav
    np.save(f"{CAU}/earthshine4_Gdisp.npy", Ed)
    np.save(f"{CAU}/earthshine4_dav.npy", dav)
    print("extensió de display (r<0,975) desada")


if __name__ == "__main__":
    main()
