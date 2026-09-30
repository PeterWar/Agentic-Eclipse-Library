"""V24e · els tres arcs de Pere (blau NW, lila W, lila E) — cura científica.

Mesurat (perfils radials a les tres finestres): els tres arcs són de la
FÓRMULA V24d, no de la dada — el fotograma real (u93) hi és monòton i llis:

  · BLAU NW / LILA W: vall a r≈412-424 — interferència entre la textura vella
    de la vora (E_int portava el pedestal+èmfasi de vora_b/c) i l'esglaó de
    la porta radial r>408.
  · LILA E: la dada real està SATURADA (u=0,99) de 444 px enfora, però el
    nivell d'empalme estava clavat al valor FOSC del composite just fora de
    Rllum (~0,2) — la fórmula reproduïa l'anell fosc d'ell en lloc de
    cobrir-lo. La realitat allà és glow brillant fins a la línia de llum.

Les tres cures, cadascuna per construcció:

  1. u = EXCÉS del DSC06993 sobre la LÍNIA DE BASE d'earthshine — l'apilat
     lineal validat (11 fotogrames, pesos del rebut V4) fa de baseline per
     regressió (a + b·S), i el llindar és el SOROLL mesurat (2σ MAD), no cap
     porta geomètrica. Fora l'esglaó de r=408: l'interior queda net perquè
     el flood hi ÉS zero, i el flood entra fins on la dada diu.
  2. E_int regenerat de l'apilat amb la recepta de to original (v24_capes):
     fora el pedestal i l'èmfasi de vora que ja no tenen feina.
  3. u=1 → LA LÍNIA de llum del muntatge (p85 local per sector), i a la
     banda exterior el contingut és max(meu, seu): res de Pere tapat mai, i
     el forat fosc entre el glow i la seva línia s'omple per construcció.
     El terme meu decau més enllà de Rllum+2 i la màscara mor a Rllum+3:
     el traspàs al seu contingut és exacte.
"""
from __future__ import annotations
import json, os
import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")

S22 = 453.5 / 455.5018189723177
MB_V = (6465.398680355321, 6752.632845814709)
POSV = (6257, 5969)
TO = (0.1036, 0.0983, 0.0981)
COMPS = {
    "vixen10": (["572A2982", "572A2983", "572A2984"], [10., 10., 10.], "vixen"),
    "vixen2": (["572A2979", "572A2980", "572A2981"], [2., 2., 2.], "vixen"),
    "ap1": (["DSC06987", "DSC06984"], [8., 2.], "sony"),
    "ap2": (["DSC06993", "DSC06996", "DSC06999"], [8., 2., 2.], "sony"),
}


def apilat_lineal_nou():
    """l'apilat lineal (11 fot, pesos del rebut, mota fora) al marc NOU."""
    gs = np.array(json.load(open(f"{CAU}/lluna_parell.json"))["guany_sony_vixen"],
                  np.float32)
    Wc = json.load(open(f"{CAU}/earthshine4_rebut.json"))["pesos"]
    P = {}
    for k, (fs, ts, tren) in COMPS.items():
        w = np.array(ts) / sum(ts)
        acc = None
        for f, wi in zip(fs, w):
            a = np.nan_to_num(np.load(f"{CAU}/lluna_{tren}_{f}_lineal.npy"))
            if tren == "vixen":
                a = a * gs[None, None, :]
            acc = a * wi if acc is None else acc + a * wi
        P[k] = acc
    H, W = P["ap1"].shape[:2]
    yyq, xxq = np.mgrid[0:H, 0:W].astype(np.float32)
    dmota = np.hypot(xxq - 330.0, yyq - 528.0)
    Mmota = np.clip((dmota - 14.0) / 8.0, 0, 1).astype(np.float32)
    Wm = {k: np.full((H, W), Wc[k], np.float32) for k in P}
    for k in ("vixen10", "vixen2"):
        Wm[k] *= Mmota
    tot = sum(Wm[k] for k in P)
    S = sum(P[k] * Wm[k][..., None] for k in P) / np.maximum(tot, 1e-9)[..., None]
    SL = (S[..., 0] + 2 * S[..., 1] + S[..., 2]) / 4
    # al marc nou (mateixa transformació que el re-ancoratge V22)
    yy, xx = np.mgrid[0:991, 0:991].astype(np.float32)
    cxt_v = MB_V[0] - POSV[1]; cyt_v = MB_V[1] - POSV[0]
    mx = (cxt_v + (xx - 495.8) / S22).astype(np.float32)
    my = (cyt_v + (yy - 495.8) / S22).astype(np.float32)
    return cv2.remap(SL, mx, my, cv2.INTER_LINEAR, borderValue=0)


def main():
    lv = json.load(open(f"{CAU}/limbe_v23.json"))
    TCX, TCY = lv["cx"] - 4866, lv["cy"] - 3279
    yy, xx = np.mgrid[0:991, 0:991].astype(np.float32)
    rr = np.hypot(xx - TCX, yy - TCY)
    az = np.arctan2(yy - TCY, xx - TCX)
    NA = 720
    afrac = (az + np.pi) / (2 * np.pi) * NA - 0.5
    ai = np.clip(((az + np.pi) / (2 * np.pi) * NA).astype(int), 0, NA - 1)

    # ── 1) el flood per excés sobre la baseline d'earthshine ─────────────
    C = np.nan_to_num(np.load(f"{CAU}/d93_disp_lineal.npy"))
    meta = json.load(open(f"{CAU}/d93_disp_meta.json"))
    L93 = (C[..., 0] + 2 * C[..., 1] + C[..., 2]) / 4
    fL = (meta["fons"][0] + 2 * meta["fons"][1] + meta["fons"][2]) / 4
    sL = (meta["sostre"][0] + 2 * meta["sostre"][1] + meta["sostre"][2]) / 4
    SL = apilat_lineal_nou()
    # ⛔ l'apilat porta les ONZE vores de guarda desplaçades (clots per trams
    # a r>430): el baseline s'estén llis des de dins — físicament és el
    # nivell d'earthshine del disc, que és suau
    def _bn(Z, mk, s):
        return (cv2.GaussianBlur(Z * mk, (0, 0), s)
                / np.maximum(cv2.GaussianBlur(mk, (0, 0), s), 1e-6))
    mkS = ((rr < 428) & (SL > 0)).astype(np.float32)
    SLe = _bn(SL, mkS, 8.0)
    wS = np.clip((rr - 424.0) / 4.0, 0, 1)
    SL = SL * (1 - wS) + SLe * wS
    dins = (rr < 400) & (SL > 0)
    A = np.c_[SL[dins], np.ones(int(dins.sum()))]
    (b, a), *_ = np.linalg.lstsq(A, L93[dins], rcond=None)
    flood = L93 - (a + b * SL)
    res = flood[rr < 380]
    sig = 1.4826 * np.median(np.abs(res - np.median(res)))
    t = 2.0 * sig
    print(f"baseline: L93 ≈ {a:.1f} + {b:.3f}·S (r<400) · σ_MAD {sig:.1f} · "
          f"llindar 2σ = {t:.1f} comptes")
    u = np.clip((flood - t) / (sL - fL), 0, 1).astype(np.float32)
    # el fotograma sol porta píxels calents/raigs: mediana 3×3 (mata pics
    # d'1-2 px que l'apilat no té; el flood real és llis i no se'n ressent)
    u = cv2.medianBlur(u, 3)
    # el flood de display és llum escampada del limbe: NOMÉS es queda el que
    # hi està CONNECTAT (component connex que toca r>440). Una taca aïllada
    # dins del disc (llum que només té el fotograma sol i l'apilat no
    # confirma: fantasma/reflex) mor sola — cap porta geomètrica.
    Mb = (u > 0.02).astype(np.uint8)
    nlab, lab = cv2.connectedComponents(Mb, connectivity=8)
    toca = np.unique(lab[(rr > 440) & (Mb > 0)])
    keep = np.isin(lab, toca[toca > 0])
    u = np.where(keep | (u <= 0.02), u, 0.0).astype(np.float32)
    # suau σ1: la corba tonal del revelat és brusca i amplificaria variacions
    # de 2-3 px del contorn en dents; la PSF real ja és ≥1 px
    u = cv2.GaussianBlur(u, (0, 0), 1.2)
    # decaïment del terme meu més enllà de la llum d'ell (el muntatge allà
    # és SEU): u → 0 entre Rllum+2 i Rllum+5
    Rllum = np.load(f"{CAU}/Rllum_v23.npy")
    Rlc = np.interp(afrac.ravel(), np.arange(NA), Rllum,
                    period=NA).reshape(991, 991).astype(np.float32)
    # (el decaïment fi es fa més avall, quan R_hand ja està calculat)
    print(f"u interior (r<380): mediana {np.median(u[rr<380]):.4f} · "
          f"p99 {np.percentile(u[rr<380],99):.4f}")

    # ── 2) E_int net: la recepta de to original sobre l'apilat ───────────
    E = np.load(f"{CAU}/capa_nat_px.npy").astype(np.float32) / 65535.0
    g = E[..., 0]
    dins9 = rr < 453.5 * 0.9
    med = float(np.median(g[dins9]))
    p10, p90 = np.percentile(g[dins9], 10), np.percentile(g[dins9], 90)
    k = 0.045 / max(p90 - p10, 1e-9)
    Ei = np.zeros_like(E)
    for c in range(3):
        Ei[..., c] = np.clip(TO[c] + (g - med) * k, 0, 1)
    # ⛔ capa_nat porta les ONZE vores de guarda desplaçades (cada fotograma
    # acaba el seu cercle a ±2 px): a r>428 la barreja cau a zero per trams i
    # surten arcs foscos discontinus. El TO del disc s'estén llis des de
    # dins; l'estructura de la vora la posa el flood real (hu).
    def blur_norm(Z, mk, s):
        return (cv2.GaussianBlur(Z * mk, (0, 0), s)
                / np.maximum(cv2.GaussianBlur(mk, (0, 0), s), 1e-6))
    mk_in = (rr < 426).astype(np.float32)
    wext = np.clip((rr - 424.0) / 4.0, 0, 1)[..., None]
    Eext = np.dstack([blur_norm(Ei[..., c], mk_in, 8.0) for c in range(3)])
    Ei = Ei * (1 - wext) + Eext * wext

    # ── 3) el nivell de la LÍNIA de llum d'ell, per sector ───────────────
    und = np.load(f"{CAU}/v23_comp_regio.npy").astype(np.float32) / 65535.0
    Lline = np.zeros((NA, 3), np.float32)
    for s in range(NA):
        an = (ai == s) & (rr > Rllum[s]) & (rr < Rllum[s] + 14)
        if an.sum() >= 4:
            for c in range(3):
                Lline[s, c] = np.percentile(und[an, c], 85)
        else:
            Lline[s] = np.nan
    for c in range(3):
        v = Lline[:, c]
        bad = ~np.isfinite(v)
        if bad.any():
            v[bad] = np.interp(np.flatnonzero(bad), np.flatnonzero(~bad),
                               v[~bad], period=NA)
        Lline[:, c] = np.convolve(np.r_[v[-5:], v, v[:5]],
                                  np.ones(5) / 5, "same")[5:-5]
    Lpx = np.dstack([np.interp(afrac.ravel(), np.arange(NA), Lline[:, c],
                               period=NA).reshape(991, 991)
                     for c in range(3)]).astype(np.float32)
    # el TRASPÀS es fa on el contingut d'ell ARRIBA al nivell (0,8·Lline),
    # no on comença la seva llum: a l'E la seva pujada és lenta i tallar a
    # Rllum deixava un fossat fosc entre el meu halo i la seva corona
    thA = (np.arange(NA) + 0.5) / NA * 2 * np.pi - np.pi
    rsA = np.arange(440, 494, 0.5, dtype=np.float32)
    xsA = (TCX + rsA[None, :] * np.cos(thA)[:, None]).astype(np.float32)
    ysA = (TCY + rsA[None, :] * np.sin(thA)[:, None]).astype(np.float32)
    PuG = cv2.remap(und[..., 1].astype(np.float32), xsA, ysA,
                    cv2.INTER_LINEAR, borderValue=np.nan)
    # el nivell estable de la SEVA corona (més enllà del llavi i del seu
    # solc): l'objectiu del traspàs surt d'aquí, no del pic del llavi
    Lstab = np.zeros(NA, np.float32)
    for s in range(NA):
        fi = (rsA >= Rllum[s] + 8) & (rsA <= Rllum[s] + 30)
        Lstab[s] = np.nanpercentile(PuG[s, fi], 90) if fi.sum() else np.nan
    bad = ~np.isfinite(Lstab)
    if bad.any():
        Lstab[bad] = np.interp(np.flatnonzero(bad), np.flatnonzero(~bad),
                               Lstab[~bad], period=NA)
    # traspàs on el seu perfil S'HI QUEDA (mínim rodant de 8 px ≥ 0,85·estable),
    # no on el creua un pic: el llavi brillant amb solc darrere ja no enganya
    Rhand = np.zeros(NA, np.float32)
    W8 = 16                                    # 8 px a passos de 0,5
    for s in range(NA):
        v = PuG[s]
        obj = 0.98 * Lstab[s]
        jj = None
        for j in np.flatnonzero(rsA >= Rllum[s]):
            seg = v[j:j + W8]
            if np.all(np.isfinite(seg)) and np.min(seg) >= obj:
                jj = j
                break
        Rhand[s] = min(rsA[jj] if jj is not None else Rllum[s] + 26,
                       Rllum[s] + 26)
    Rhand = np.convolve(np.r_[Rhand[-15:], Rhand, Rhand[:15]],
                        np.ones(15) / 15, "same")[15:-15]
    # fre de derivada azimutal: cap salt entre arcs (la costura del S).
    # ALÇANT les valls, mai escapçant els pics: escapçar tornava a posar el
    # traspàs del braç NW abans del solc de darrere el llavi
    for _ in range(40):
        Rhand = np.maximum(Rhand, np.maximum(np.roll(Rhand, 1),
                                             np.roll(Rhand, -1)) - 0.4)
    Rhc = np.interp(afrac.ravel(), np.arange(NA), Rhand,
                    period=NA).reshape(991, 991).astype(np.float32)
    print(f"R_hand − Rllum: mediana {np.median(Rhand - Rllum):.1f} px · "
          f"p90 {np.percentile(Rhand - Rllum, 90):.1f}")
    # el nivell de l'altiplà = el SEU valor a R_hand (empalme exacte; p85
    # només serveix per situar R_hand)
    Ltar = np.zeros((NA, 3), np.float32)
    for s in range(NA):
        an = (ai == s) & (rr > Rhand[s] - 1.0) & (rr < Rhand[s] + 8.0)
        if an.sum() >= 3:
            for c in range(3):
                Ltar[s, c] = np.percentile(und[an, c], 90)
        else:
            Ltar[s] = np.nan
    for c in range(3):
        v = Ltar[:, c]
        bad = ~np.isfinite(v)
        if bad.any():
            v[bad] = np.interp(np.flatnonzero(bad), np.flatnonzero(~bad),
                               v[~bad], period=NA)
        Ltar[:, c] = np.convolve(np.r_[v[-7:], v, v[:7]],
                                 np.ones(7) / 7, "same")[7:-7]
    Lpx = np.dstack([np.interp(afrac.ravel(), np.arange(NA), Ltar[:, c],
                               period=NA).reshape(991, 991)
                     for c in range(3)]).astype(np.float32)
    print(f"objectiu d'altiplà (el SEU nivell a R_hand): G mediana "
          f"{np.median(Ltar[:,1]):.3f}")
    print(f"línia de llum: G mediana {np.median(Lline[:,1]):.3f} · "
          f"p10 {np.percentile(Lline[:,1],10):.3f} · "
          f"p90 {np.percentile(Lline[:,1],90):.3f}")

    # ── transferència no lineal: γ ajustada CONTRA el revelat de Pere ────
    # el mapa lineal u→línia fa un vel marró ample (mig flood ja brillant);
    # la realitat concentra la llum vora el limbe. γ es tria maximitzant la
    # correlació de forma (per azimut, 412→Rllum−2) amb el perfil radial del
    # revelat de Pere (d93_pere_tile) — derivada de la referència.
    # la corba tonal del trànsit, CLONADA del revelat de Pere: h_c(u) es
    # mesura aparellant píxel a píxel la fracció de flood amb el seu render
    # (banda 410..Rllum+2), es normalitza disc→blanc i es força monòtona.
    # El camí cromàtic (marró-taronja del seu gust) queda mesurat, no imitat;
    # el blanc d'ell es re-ancora al nivell de LÍNIA del muntatge.
    ref = np.load(f"{CAU}/d93_pere_tile.npy")
    band = (rr > 410) & (rr < Rlc + 2) & (ref[..., 1] > 0)
    ub = u[band]
    nb = 40
    ibin = np.clip((ub * nb).astype(int), 0, nb - 1)
    h = np.zeros((nb, 3), np.float32)
    for c in range(3):
        vals = ref[..., c][band]
        for j in range(nb):
            s = ibin == j
            h[j, c] = np.median(vals[s]) if s.sum() >= 20 else np.nan
        v = h[:, c]
        bad = ~np.isfinite(v)
        if bad.any():
            v[bad] = np.interp(np.flatnonzero(bad), np.flatnonzero(~bad), v[~bad])
        v = np.maximum.accumulate(v)                      # monòtona
        v = np.convolve(np.r_[v[:1].repeat(2), v, v[-1:].repeat(2)],
                        np.ones(5) / 5, "same")[2:-2]       # genoll suau
        h[:, c] = (v - v[0]) / max(v[-1] - v[0], 1e-6)     # disc→blanc = 0→1
    for uu in (0.05, 0.1, 0.2, 0.3, 0.5):
        j = int(uu*nb)
        print(f"  h({uu}) = " + " ".join(f"{h[j,c]:.2f}" for c in range(3)))

    u_tap = (u * np.clip(((Rhc + 9.0) - rr) / 5.0, 0, 1)).astype(np.float32)
    uc = np.clip(u_tap * nb - 0.5, 0, nb - 1)
    j0 = np.floor(uc).astype(int); fj = (uc - j0)[..., None]
    j1 = np.minimum(j0 + 1, nb - 1)
    hu = h[j0] * (1 - fj) + h[j1] * fj
    for c in range(3):
        hu[..., c] = cv2.GaussianBlur(hu[..., c], (0, 0), 1.5)

    # ── la fórmula + max-blend a la banda ────────────────────────────────
    E2 = Ei * (1 - hu) + Lpx * hu
    wb = np.clip((rr - 443.0) / 3.0, 0, 1)[..., None]
    E2 = (1 - wb) * E2 + wb * np.maximum(E2, und)
    np.save(f"{CAU}/capa_fosca_e.npy",
            np.clip(np.rint(np.clip(E2, 0, 1) * 65535), 0, 65535)
            .astype(np.uint16))

    # màscara: plena fins a Rllum+1, morta a Rllum+3
    m = np.clip(((Rhc + 7.0) - rr) / 4.0, 0, 1).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 0.8)
    np.save(f"{CAU}/mascara_e.npy",
            np.clip(np.rint(m * 65535), 0, 65535).astype(np.uint16))

    # ── composite previst i portes ───────────────────────────────────────
    # REFLEX restringit al sector de la FLAMARADA (|az|>145°, finestra suau):
    # amb el glow real a la capa, l'anell sintètic de l'E duplicava la llum i
    # feia el bony-i-caiguda que la realitat no té (marca LILA E). El vermell
    # de la flamarada (W, on és real i on Pere el va col·locar) es conserva.
    R19 = np.load(f"{CAU}/v24_l19_content.npy").astype(np.float32) / 65535.0
    yy4, xx4 = np.mgrid[0:991, 0:991].astype(np.float32)
    az4 = np.degrees(np.arctan2(yy4 - (lv["cy"] - 3279),
                                xx4 - (lv["cx"] - 4862)))
    wfl = np.clip((np.abs(az4) - 130.0) / 15.0, 0, 1).astype(np.float32)
    R19e = R19 * wfl[..., None]
    np.save(f"{CAU}/capa_reflex_e.npy",
            np.clip(np.rint(R19e * 65535), 0, 65535).astype(np.uint16))
    Rr = np.zeros_like(R19e); Rr[:, :987] = R19e[:, 4:]
    compd = np.load(f"{CAU}/comp_prevista.npy").astype(np.float32) / 65535.0
    comp2 = np.clip(und * (1 - m[..., None]) + E2 * m[..., None] + Rr, 0, 1)
    np.save(f"{CAU}/comp_prevista_e.npy",
            np.clip(np.rint(comp2 * 65535), 0, 65535).astype(np.uint16))

    # porta 1: interior (r<390) — contra el LLIURAT (V24d)
    d = np.abs(comp2 - compd)[rr < 390]
    print(f"porta interior (r<390) vs V24d: max {d.max():.4f} · p99 {np.percentile(d,99):.4f}")
    # porta 2: valls — profunditat màxima d'un mínim local radial 400→Rllum−2
    th = (np.arange(NA) + 0.5) / NA * 2 * np.pi - np.pi
    rs = np.arange(398, 452, 0.5, dtype=np.float32)
    xs = (TCX + rs[None, :] * np.cos(th)[:, None]).astype(np.float32)
    ys = (TCY + rs[None, :] * np.sin(th)[:, None]).astype(np.float32)
    def valls(cc):
        P = cv2.remap(cc[..., 1].astype(np.float32), xs, ys,
                      cv2.INTER_LINEAR, borderValue=np.nan)
        K = np.ones(5, np.float32) / 5
        out = np.zeros(NA)
        for i in range(NA):
            fi = rs < Rllum[i] - 2
            v = np.convolve(P[i, fi], K, "same")[2:-2]
            if len(v) > 4:
                cmax = np.maximum.accumulate(v)
                out[i] = np.max(cmax - v)
        return out
    v0, v2 = valls(compd), valls(comp2)
    print(f"porta valls (profunditat màxima, mediana): V24d {np.median(v0):.4f} → "
          f"V24e {np.median(v2):.4f} · p95: {np.percentile(v0,95):.4f} → "
          f"{np.percentile(v2,95):.4f}")
    # porta 3: el forat fosc 445→Rllum+3
    def forat(cc):
        P = cv2.remap(cc[..., 1].astype(np.float32), xs, ys,
                      cv2.INTER_LINEAR, borderValue=np.nan)
        mins = []
        for i in range(NA):
            fi = (rs > 445) & (rs < Rllum[i] + 3)
            if fi.sum() > 4:
                mins.append(np.nanmin(P[i, fi]))
        return np.array(mins)
    f0, f2 = forat(compd), forat(comp2)
    print(f"porta forat fosc (mínim G, mediana): V24d {np.median(f0):.3f} → "
          f"V24e {np.median(f2):.3f}")
    # porta 4: traspàs exacte al seu contingut més enllà de la màscara
    fora = (rr > Rhc + 8) & (rr < Rhc + 14)
    dt = np.abs(comp2 - np.clip(und + Rr, 0, 1))[fora]
    print(f"porta traspàs (Rllum+4..+10): max|comp−(seu+reflex)| {dt.max():.4f}")
    json.dump({"interior_p99": float(np.percentile(d, 99)),
               "baseline_a": float(a), "baseline_b": float(b),
               "sigma_mad": float(sig), "llindar": float(t),
               "interior_max": float(d.max()),
               "valls_mediana_d": float(np.median(v0)),
               "valls_mediana_e": float(np.median(v2)),
               "valls_p95_d": float(np.percentile(v0, 95)),
               "valls_p95_e": float(np.percentile(v2, 95)),
               "forat_mediana_d": float(np.median(f0)),
               "forat_mediana_e": float(np.median(f2)),
               "traspas_max": float(dt.max())},
              open(f"{CAU}/portes_e.json", "w"), indent=1)


if __name__ == "__main__":
    main()
