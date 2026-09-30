"""V24d · el perímetre amb la dada REAL del DSC06993 (ordre de Pere, 01-09).

Pere: «la part del perímetre del DSC06993.psb s'adapta molt millor al contorn
real que el que has fet tu; no entenc com una sola imatge dona millor resultat
que l'agregat». La resposta mesurada: TOTES les tessel·les científiques porten
GUARDA de 8 px dins del limbe (i el sostre LDIC exclou el glow saturat del
8 s), o sigui que la capa no tenia DADA de ~447 px enfora — la banda era
pedestal+textura, i la llum del perímetre la posava l'anell additiu de la
capa REFLEX, que mor a 452 px: 5 px DINS del contorn real. El fotograma sol
sí que porta el trànsit sencer disc→glow→corona, amb la seva estructura.

La cura, en una fórmula per a tota la tessel·la (cap finestra radial):

    E′_c = E_int_c · (1 − u_c) + L_fora_c(θ) · u_c

  · E_int  = el contingut actual de la capa (interior de l'apilat, intacte);
  · u_c    = (D93_c − fons_c) / (sostre_c − fons_c), el fotograma DSC06993
             sencer compost al marc V24 amb la cadena exacta i ancorat
             SUB-PX al disc de les perles (495,877 · 495,741) — la fracció
             real de llum del trànsit, per canal (el gra i el contorn
             irregular són els del fotograma);
  · L_fora = la llum del MUNTATGE de Pere just fora d'on comença (composite
             V23, per sector de 0,5°): on u→1 el valor és el seu, i
             l'empalme és continu per construcció.

La màscara s'estén fins a la seva llum (tall = Rllum per sector, ple fins a
Rllum−2,5 i zero a Rllum+0,5) — fora el marge d'1,5 px i el suavitzat de 7
sectors que arrodonien el contorn. La capa REFLEX (anell vermell del
DSC06984, posició de Pere) NO es toca.

Sortides: capa_fosca_d93.npy · mascara_d93.npy · comp_prevista.npy · portes.
"""
from __future__ import annotations
import json, os
import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")


def main():
    lv = json.load(open(f"{CAU}/limbe_v23.json"))
    TCX, TCY = lv["cx"] - 4866, lv["cy"] - 3279
    yy, xx = np.mgrid[0:991, 0:991].astype(np.float32)
    rr = np.hypot(xx - TCX, yy - TCY)
    az = np.arctan2(yy - TCY, xx - TCX)
    NA = 720
    ai = np.clip(((az + np.pi) / (2 * np.pi) * NA).astype(int), 0, NA - 1)

    # ── u per canal, del fotograma sencer ────────────────────────────────
    C = np.nan_to_num(np.load(f"{CAU}/d93_disp_lineal.npy"))
    meta = json.load(open(f"{CAU}/d93_disp_meta.json"))
    # u ÚNIC de luminància: amb un u per canal el G satura abans (sostre més
    # baix) i el trànsit sortia tenyit de verd — el croma del glow el posa
    # L_fora, no la fracció
    L93 = (C[..., 0] + 2 * C[..., 1] + C[..., 2]) / 4
    fL = (meta["fons"][0] + 2 * meta["fons"][1] + meta["fons"][2]) / 4
    sL = (meta["sostre"][0] + 2 * meta["sostre"][1] + meta["sostre"][2]) / 4
    u1 = np.clip((L93 - fL) / (sL - fL), 0, 1)
    # porta radial: el terme de glow només al trànsit (r>408) — sense això
    # les terres altes brillants de l'earthshine (u~0,3) es contaminarien
    u1 *= np.clip((rr - 408.0) / 17.0, 0, 1)
    u = u1[..., None]

    # ── la llum del muntatge per sector (composite V23) ──────────────────
    und = np.load(f"{CAU}/v23_comp_regio.npy").astype(np.float32) / 65535.0
    Rllum = np.load(f"{CAU}/Rllum_v23.npy")
    # la llum d'ell AL RADI D'EMPALME (no la mediana més enfora: la llum
    # puja i sobrevalorar-la crea un salt positiu a tot el contorn)
    Lout = np.zeros((NA, 3), np.float32)
    for a in range(NA):
        an = (ai == a) & (rr > Rllum[a] + 0.5) & (rr < Rllum[a] + 2.5)
        if an.sum():
            for c in range(3):
                Lout[a, c] = np.median(und[an, c])
        else:
            Lout[a] = np.nan
    # forats i suavitzat azimutal curt (5 sectors = 2,5°)
    for c in range(3):
        v = Lout[:, c]
        bad = ~np.isfinite(v)
        if bad.any():
            v[bad] = np.interp(np.flatnonzero(bad), np.flatnonzero(~bad),
                               v[~bad], period=NA)
        Lout[:, c] = np.convolve(np.r_[v[-5:], v, v[:5]],
                                 np.ones(5) / 5, "same")[5:-5]
    np.save(f"{CAU}/Lout_v23.npy", Lout)

    # ── la fórmula (Lout interpolat CONTINU en azimut: cap graó de sector) ─
    Ei = np.load(f"{CAU}/v24_l18_content.npy").astype(np.float32) / 65535.0
    afrac = (az + np.pi) / (2 * np.pi) * NA - 0.5
    Lpx = np.dstack([np.interp(afrac.ravel(), np.arange(NA), Lout[:, c],
                               period=NA).reshape(991, 991)
                     for c in range(3)]).astype(np.float32)
    E2 = Ei * (1 - u) + Lpx * u
    np.save(f"{CAU}/capa_fosca_d93.npy",
            np.clip(np.rint(np.clip(E2, 0, 1) * 65535), 0, 65535)
            .astype(np.uint16))

    # ── màscara: fins a la seva llum, sense arrodonir el contorn ─────────
    Rl = np.convolve(np.r_[Rllum[-3:], Rllum, Rllum[:3]],
                     np.ones(3) / 3, "same")[3:-3]
    Rlc = np.interp(afrac.ravel(), np.arange(NA), Rl,
                    period=NA).reshape(991, 991).astype(np.float32)
    m = np.clip((Rlc + 0.5 - rr) / 3.0, 0, 1).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 0.8)
    np.save(f"{CAU}/mascara_d93.npy",
            np.clip(np.rint(m * 65535), 0, 65535).astype(np.uint16))

    # ── composite previst i portes ───────────────────────────────────────
    R19 = np.load(f"{CAU}/v24_l19_content.npy").astype(np.float32) / 65535.0
    Rr = np.zeros_like(R19); Rr[:, :987] = R19[:, 4:]
    comp0 = np.load(f"{CAU}/v24_comp_regio.npy").astype(np.float32) / 65535.0
    comp2 = np.clip(und * (1 - m[..., None]) + E2 * m[..., None] + Rr, 0, 1)
    np.save(f"{CAU}/comp_prevista.npy",
            np.clip(np.rint(comp2 * 65535), 0, 65535).astype(np.uint16))

    # porta 1: interior intacte (r<390)
    dint = np.abs(comp2 - comp0)[rr < 390].max()
    # porta 2: empalme continu — salt a través del tall de màscara
    salt, salt0 = [], []
    for a in range(NA):
        an1 = (ai == a) & (rr > Rl[a] - 1.5) & (rr < Rl[a] - 0.5)
        an2 = (ai == a) & (rr > Rl[a] + 1.0) & (rr < Rl[a] + 2.0)
        if an1.sum() and an2.sum():
            salt.append(np.median(comp2[an1, 1]) - np.median(comp2[an2, 1]))
            salt0.append(np.median(comp0[an1, 1]) - np.median(comp0[an2, 1]))
    salt = np.array(salt); salt0 = np.array(salt0)
    # porta 3: el forat fosc de 452-456 (l'espai que Pere marcava) ha marxat:
    # mínim radial entre 445 i Rllum+3, abans i ara
    def forat(cc):
        mins = []
        for a in range(0, NA, 4):
            an = (ai == a) & (rr > 445) & (rr < Rllum[a] + 3)
            if an.sum() > 4:
                prof = cc[an, 1]
                mins.append(prof.min())
        return np.array(mins)
    f0, f2_ = forat(comp0), forat(comp2)
    print(f"porta interior (r<390): max|Δ| {dint:.4f}")
    print(f"porta empalme: salt mediana {np.median(salt):+.4f} · "
          f"p95 |salt| {np.percentile(np.abs(salt), 95):.4f} "
          f"(el muntatge ACTUAL al mateix lloc: mediana {np.median(salt0):+.4f} · "
          f"p95 {np.percentile(np.abs(salt0), 95):.4f})")
    print(f"forat fosc 445→llum (mínim G per sector): abans mediana "
          f"{np.median(f0):.3f} · ara {np.median(f2_):.3f}")
    json.dump({"porta_interior_maxdif": float(dint),
               "salt_empalme_mediana": float(np.median(salt)),
               "salt_empalme_p95abs": float(np.percentile(np.abs(salt), 95)),
               "forat_fosc_abans": float(np.median(f0)),
               "forat_fosc_ara": float(np.median(f2_))},
              open(f"{CAU}/portes_d93.json", "w"), indent=1)


if __name__ == "__main__":
    main()
